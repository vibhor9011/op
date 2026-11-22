# OrbitGuard Outputs & API Contract Specification

> **Status**: Frozen Production Contract (v1.0)  
> **Service Architecture**: FastAPI serving ONLY precomputed artifacts from `outputs/`, `metrics/`, and `reports/`.  
> **Strict Operational Rule**: Models are NEVER executed live during HTTP request lifecycles. Every single response embeds `label_source` and the operational `warning` string.

---

## 1. Precomputed Files Specification (`outputs/`)

| File Pattern / Artifact | Format | Description | Constraints & Provenance |
| :--- | :---: | :--- | :--- |
| `outputs/flood_zones.geojson` | GeoJSON FeatureCollection | 33 canonical administrative district polygons with priority ranks and risk tiers. | Simplified to 0.004° tolerance in EPSG:4326; area computed in EPSG:7755. Stamped with `degraded_mode`. |
| `outputs/flood_predictions_{YYYY}_{MM}.json` | JSON | Monthly flood hazard predictions for all 33 districts across 72 periods (2014–2025). | Conformal bounds $p_{\text{low}} \le p_{\text{mid}} \le p_{\text{high}}$, composite exposure, descending priority rank, robust flags, SHAP drivers. |
| `outputs/drought_predictions_{YYYY}_{MM}.json` | JSON | Monthly index-based drought predictions for all 33 districts across 72 periods (2014–2025). | Label source: `index_derived`, warning: `Demo: index-based - Agricultural & Meteorological Drought Index (SPI-3 + VCI)`. |
| `outputs/flood_extent_{YYYY}_{MM}.geojson` | GeoJSON FeatureCollection | High-resolution Sentinel-1 SAR flood inundation footprint vector polygons. | IW VV polarization, Otsu & -16 dB threshold, slope $< 5^\circ$, HAND $< 15\text{ m}$, 5 ha MMU. |
| `outputs/extent_summary.json` | JSON | Quantitative spatial extent summary for the target monsoon event. | Flooded km², share of valid land, scenes used, non-independence caveat. |
| `outputs/shap_explanations.json` | JSON | Precomputed top-5 SHAP feature drivers and plain-language attributions for all districts. | Quantitative attributions and operational explanations. |
| `outputs/provenance.json` | JSON | Global metadata, synthetic circularity audit proof, and ASDMA disclaimer. | Embedded into all API error and metadata responses. |

---

## 2. Standard Monthly Prediction JSON Contract

Every `outputs/{hazard}_predictions_{YYYY}_{MM}.json` strictly complies with the following schema:

```json
{
  "hazard": "flood",
  "granularity": "month",
  "period": "2022-06",
  "label_source": "synthetic_augmentation",
  "warning": "PIPELINE CHECK ONLY - no observed-derived labels",
  "zones": [
    {
      "id": "G09",
      "name": "Dhemaji",
      "p_low": 0.0728,
      "p_mid": 0.0970,
      "p_high": 0.1212,
      "exposure": 0.5140,
      "priority": 0.0499,
      "rank": 1,
      "robust": true,
      "drivers": {
        "rain_total_mm": 531.3,
        "rain_cum3m_mm": 1487.6,
        "rain_anom_mm": 51.3
      },
      "observed_flood_km2": 233.05,
      "observed_flood_frac": 0.0970
    }
  ]
}
```

### Strict Field Requirements
1. `hazard`: Must be `"flood"` or `"drought"`.
2. `granularity`: Fixed to `"month"`.
3. `zones`: Must contain exactly **33 canonical districts** (`G01` to `G33`).
4. **Non-Crossing Invariant**: $0.0 \le p_{\text{low}} \le p_{\text{mid}} \le p_{\text{high}} \le 1.0$.
5. `exposure`: Composite vulnerability in $[0.0, 1.0]$.
6. `priority`: $p_{\text{mid}} \times \text{exposure}$.
7. `rank`: Ascending priority rank from 1 (highest priority) to 33 (lowest priority).
8. `robust`: Boolean flag; `true` if and only if district ranks $\le 5$ under both $p_{\text{mid}}$ and $p_{\text{high}}$.

---

## 3. FastAPI REST Endpoints Contract

All endpoints return JSON with CORS headers enabled (`*`) and automatically embed `label_source` and `warning`.

| Method | Endpoint | Query Parameters | Description | Status Codes |
| :--- | :--- | :--- | :--- | :---: |
| `GET` | `/health` | *None* | Health status, deployment version, and label provenance. | `200` |
| `GET` | `/hazards` | *None* | Catalog of active hazard domains (`flood`, `drought`). | `200` |
| `GET` | `/periods` | `hazard` (default: `flood`) | All available precomputed periods (YYYY-MM). | `200` |
| `GET` | `/zones` | `hazard`, `period`, `lead` | District zones with CQR bounds, exposure, and rule-based advisories. | `200`, `404` |
| `GET` | `/ranking` | `hazard`, `period`, `lead` | Districts sorted descending by priority rank; includes top-5 robust list. | `200`, `404` |
| `GET` | `/explain/{zone_id}` | `period` | Top 5 SHAP feature drivers with quantitative and plain-language text. | `200` |
| `GET` | `/extent` | `period` | Precomputed Sentinel-1 SAR flood extent GeoJSON footprint. | `200`, `404` |
| `GET` | `/metrics` | *None* | CV metrics, historical event backtest, and pitch deck claims audit. | `200` |
| `GET` | `/provenance` | *None* | Audit findings, synthetic circularity proof, and ASDMA disclaimer. | `200` |

---

## 4. Operational Advisory Object Schema

When queried via `/zones`, each zone dynamically embeds an operational advisory generated by the deterministic rule engine (`core/advisory.py`):

```json
{
  "level": "Severe",
  "headline": "CRITICAL FLOOD ALERT: Severe inundation threat across Dhemaji (p_mid: 9.7%)",
  "reasons": [
    "Sustained 3-month cumulative rainfall (1488 mm) saturated local soils.",
    "Monsoon rainfall anomaly of +51 mm above historical median."
  ],
  "recommended_actions": [
    "Pre-position boats and SDRF teams in high-risk circles",
    "Open relief camps and stage dry rations and water purification kits",
    "Initiate precautionary evacuation of low-lying riverine settlements"
  ],
  "confidence": "High (tight predictive band: ±2.4%)",
  "disclaimer": "Decision support only; confirm with ASDMA/IMD official advisories."
}
```

### Advisory Threshold Rules
- **Severe**: Triggered ONLY if $p_{\text{low}} \ge \tau$ (lower bound exceeds threshold).
- **Warning**: Triggered if $p_{\text{mid}} \ge \tau$ (median forecast exceeds threshold).
- **Watch**: Triggered if only $p_{\text{high}} \ge \tau$ (upper bound exceeds threshold).
- **Normal**: None exceed threshold.
