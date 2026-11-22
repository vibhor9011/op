"""
OrbitGuard Rule-Based Advisory Generator (core/advisory.py).
============================================================
Rule-based templates generating operational flood advisories without an LLM.
Produces for each zone:
{
    "level": "Severe" | "Warning" | "Watch" | "Normal",
    "headline": str,
    "reasons": list[str],
    "recommended_actions": list[str],
    "confidence": str,
    "disclaimer": "Decision support only; confirm with ASDMA/IMD official advisories."
}

Rules:
- Level from p_mid and p_high:
  - Severe: ONLY if p_low also exceeds the threshold (p_low >= threshold)
  - Warning: if p_mid exceeds the threshold (p_mid >= threshold)
  - Watch: if only p_high exceeds the threshold (p_high >= threshold)
  - Normal: if none exceed the threshold
- Reasons: Sourced deterministically from top SHAP drivers, rainfall, and terrain metrics.
- Actions: Sourced from editable YAML (core/advisory_actions.yaml).
- Confidence: Categorized from prediction band width (p_high - p_low).
- Mandatory line: "Decision support only; confirm with ASDMA/IMD official advisories."
"""

import os
import yaml
from typing import Dict, Any, List, Optional

CONFIG_YAML_PATH = os.path.join(os.path.dirname(__file__), "advisory_actions.yaml")

DEFAULT_DISCLAIMER = "Decision support only; confirm with ASDMA/IMD official advisories."

DEFAULT_ACTIONS = {
    "Severe": [
        "Pre-position boats and SDRF teams for immediate deployment",
        "Open relief camps and stage dry rations, drinking water, and medical kits",
        "Initiate precautionary evacuation of low-lying riverine settlements",
        "Inspect and reinforce vulnerable embankments and critical breach points"
    ],
    "Warning": [
        "Pre-position boats and SDRF teams in high-risk revenue circles",
        "Issue community alerts and activate 24/7 District Emergency Operation Centers (DEOC)",
        "Check embankments, sluice gates, and vulnerable drainage culverts",
        "Identify flood shelters and ensure standby power and clean water supplies"
    ],
    "Watch": [
        "Issue community alerts and advisories to riverine populations",
        "Monitor IMD local weather radar and CWC river gauge feeds",
        "Check embankments and clear blocked municipal/rural drainage channels",
        "Place disaster response volunteers and circle quick response teams on standby"
    ],
    "Normal": [
        "Routine seasonal monitoring of hydro-meteorological indicators",
        "Maintain standard readiness protocols across district emergency cells"
    ]
}


def load_advisory_config() -> Dict[str, Any]:
    """Load configuration from advisory_actions.yaml with safe fallbacks."""
    if os.path.exists(CONFIG_YAML_PATH):
        try:
            with open(CONFIG_YAML_PATH, "r", encoding="utf-8") as f:
                cfg = yaml.safe_load(f)
                if isinstance(cfg, dict):
                    return cfg
        except Exception:
            pass

    return {
        "threshold": 0.05,
        "disclaimer": DEFAULT_DISCLAIMER,
        "confidence_bands": {
            "high_max_width": 0.08,
            "medium_max_width": 0.18
        },
        "actions": DEFAULT_ACTIONS
    }


def determine_advisory_level(
    p_low: float,
    p_mid: float,
    p_high: float,
    threshold: float = 0.05
) -> str:
    """
    Determine advisory level according to strict rule:
    - Severe only if p_low also exceeds the threshold;
    - Warning if p_mid does;
    - Watch if only p_high does.
    - Normal otherwise.
    """
    if p_low >= threshold:
        return "Severe"
    elif p_mid >= threshold:
        return "Warning"
    elif p_high >= threshold:
        return "Watch"
    else:
        return "Normal"


def determine_confidence(p_low: float, p_high: float, conf_cfg: Dict[str, float] = None) -> str:
    """Confidence categorized from uncertainty band width (p_high - p_low)."""
    if conf_cfg is None:
        conf_cfg = {"high_max_width": 0.08, "medium_max_width": 0.18}

    width = max(0.0, float(p_high - p_low))
    high_cut = conf_cfg.get("high_max_width", 0.08)
    med_cut = conf_cfg.get("medium_max_width", 0.18)

    if width <= high_cut:
        return f"High (tight predictive band: ±{width/2.0:.1%})"
    elif width <= med_cut:
        return f"Medium (moderate predictive band: ±{width/2.0:.1%})"
    else:
        return f"Low (wide predictive band: ±{width/2.0:.1%})"


def generate_reasons(
    drivers: Optional[Dict[str, Any]] = None,
    p_mid: float = 0.0,
    top_shap_features: Optional[List[Dict[str, Any]]] = None
) -> List[str]:
    """Extract deterministic, human-readable reasons from rainfall drivers and top SHAP features."""
    reasons = []
    drivers = drivers or {}

    # 1. Evaluate top SHAP features if provided
    if top_shap_features:
        for feat in top_shap_features[:3]:
            fname = feat.get("feature", "")
            fval = feat.get("value")
            plain = feat.get("plain_language")
            if plain:
                reasons.append(plain)
            elif "rain_cum3m" in fname and fval is not None:
                reasons.append(f"Cumulative 3-month rainfall ({fval:.0f} mm) elevated catchment saturation.")
            elif "rain_total" in fname and fval is not None:
                reasons.append(f"High monthly precipitation total ({fval:.0f} mm) exceeding drainage capacity.")
            elif "rain_anom" in fname and fval is not None:
                reasons.append(f"Significant positive rainfall anomaly (+{fval:.0f} mm above climatology).")
            elif "floodplain" in fname:
                reasons.append("Extensive low-lying riverine floodplain geometry (HAND < 15 m).")
            elif "upstream" in fname and fval is not None:
                reasons.append(f"Elevated upstream transboundary runoff inflow ({fval:.0f} mm).")

    # 2. Driver rainfall checks if reasons list is still short
    rain_cum = drivers.get("rain_cum3m_mm")
    if rain_cum is not None and pd_valid_num(rain_cum) and len(reasons) < 3:
        if float(rain_cum) > 600.0:
            reasons.append(f"Sustained 3-month cumulative rainfall ({float(rain_cum):.0f} mm) saturated local soils.")

    rain_tot = drivers.get("rain_total_mm")
    if rain_tot is not None and pd_valid_num(rain_tot) and len(reasons) < 3:
        if float(rain_tot) > 200.0:
            reasons.append(f"Monthly rainfall ({float(rain_tot):.0f} mm) creates acute surface ponding risk.")

    rain_anom = drivers.get("rain_anom_mm")
    if rain_anom is not None and pd_valid_num(rain_anom) and len(reasons) < 3:
        if float(rain_anom) > 30.0:
            reasons.append(f"Monsoon rainfall anomaly of +{float(rain_anom):.0f} mm above historical median.")

    # 3. Default contextual reason if none triggered
    if not reasons:
        if p_mid >= 0.05:
            reasons.append(f"Calibrated flood exceedance probability is {p_mid:.1%} under active monsoon regime.")
            reasons.append("Low-lying floodplain elevation and proximity to Brahmaputra river channels.")
        else:
            reasons.append("Precipitation and soil moisture indicators remain within manageable seasonal baseline.")

    return reasons[:4]


def pd_valid_num(val) -> bool:
    """Helper to verify numerical validity."""
    try:
        f = float(val)
        return not (f != f)  # Not NaN
    except (ValueError, TypeError):
        return False


def generate_headline(level: str, district_name: str, p_mid: float) -> str:
    """Generate concise, standardized headline for early warning broadcasts."""
    if level == "Severe":
        return f"CRITICAL FLOOD ALERT: Severe inundation threat across {district_name} (p_mid: {p_mid:.1%})"
    elif level == "Warning":
        return f"FLOOD WARNING: Elevated inundation risk in {district_name} (p_mid: {p_mid:.1%})"
    elif level == "Watch":
        return f"FLOOD WATCH: Potential flooding conditions monitored for {district_name}"
    else:
        return f"MONSOON ADVISORY: Normal monitoring active for {district_name}"


def generate_zone_advisory(
    zone_data: Dict[str, Any],
    top_shap_features: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """
    Generate advisory for a single zone dictionary.
    zone_data must contain: name, p_low, p_mid, p_high, and optionally drivers.
    """
    cfg = load_advisory_config()
    threshold = float(cfg.get("threshold", 0.05))
    disclaimer = cfg.get("disclaimer", DEFAULT_DISCLAIMER)
    actions_map = cfg.get("actions", DEFAULT_ACTIONS)
    conf_cfg = cfg.get("confidence_bands", {"high_max_width": 0.08, "medium_max_width": 0.18})

    name = zone_data.get("name", zone_data.get("district", "Unknown District"))
    p_low = float(zone_data.get("p_low", 0.0))
    p_mid = float(zone_data.get("p_mid", 0.0))
    p_high = float(zone_data.get("p_high", 0.0))
    drivers = zone_data.get("drivers", {})

    level = determine_advisory_level(p_low, p_mid, p_high, threshold=threshold)
    confidence = determine_confidence(p_low, p_high, conf_cfg)
    headline = generate_headline(level, name, p_mid)
    reasons = generate_reasons(drivers=drivers, p_mid=p_mid, top_shap_features=top_shap_features)
    recommended_actions = list(actions_map.get(level, actions_map.get("Watch", [])))

    return {
        "level": level,
        "headline": headline,
        "reasons": reasons,
        "recommended_actions": recommended_actions,
        "confidence": confidence,
        "disclaimer": disclaimer
    }
