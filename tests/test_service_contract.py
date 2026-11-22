"""Contract and integration tests for OrbitGuard Early Warning FastAPI service."""

import os
import glob
import json
import pytest
from fastapi import HTTPException

from service.app import (
    app,
    get_health,
    get_hazards,
    get_periods,
    get_zones,
    get_ranking,
    get_advisories,
    get_explain,
    get_extent,
    get_geometry,
    get_timeline,
    get_overview,
    get_metrics,
    get_provenance,
    api_health,
    api_dashboard,
    api_flood_extent
)
from core.advisory import determine_advisory_level, determine_confidence, generate_zone_advisory

OUTPUTS_DIR = "outputs"


def test_json_contract_on_all_precomputed_prediction_files():
    """
    Contract test that fails if ANY precomputed file in outputs/ violates the JSON contract:
    - zones have id, name, p_low <= p_mid <= p_high, exposure, priority, rank, robust
    - label_source and warning string present
    - 33 canonical zones per file
    """
    pred_files = glob.glob(os.path.join(OUTPUTS_DIR, "flood_predictions_*.json"))
    assert len(pred_files) > 0, "No precomputed prediction files found in outputs/"

    for f_path in pred_files:
        with open(f_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        assert data.get("hazard") == "flood", f"{f_path}: hazard must be 'flood'"
        assert data.get("granularity") == "month", f"{f_path}: granularity must be 'month'"
        assert "period" in data, f"{f_path}: missing period"
        assert "label_source" in data and len(data["label_source"]) > 0, f"{f_path}: missing label_source"
        assert "warning" in data and len(data["warning"]) > 0, f"{f_path}: missing warning string"

        zones = data.get("zones", [])
        assert len(zones) == 33, f"{f_path}: expected 33 zones, got {len(zones)}"

        seen_ids = set()
        seen_ranks = set()

        for z in zones:
            # 1. Identity
            zid = z.get("id")
            name = z.get("name")
            assert zid and zid.startswith("G"), f"{f_path}: invalid zone id {zid}"
            assert name and len(name) > 0, f"{f_path}: empty district name for {zid}"
            seen_ids.add(zid)

            # 2. Probability bounds: 0 <= p_low <= p_mid <= p_high <= 1
            p_low = z.get("p_low")
            p_mid = z.get("p_mid")
            p_high = z.get("p_high")

            assert isinstance(p_low, (int, float)), f"{f_path}: {zid} p_low not numeric"
            assert isinstance(p_mid, (int, float)), f"{f_path}: {zid} p_mid not numeric"
            assert isinstance(p_high, (int, float)), f"{f_path}: {zid} p_high not numeric"

            assert 0.0 <= p_low <= 1.0, f"{f_path}: {zid} p_low out of range: {p_low}"
            assert 0.0 <= p_mid <= 1.0, f"{f_path}: {zid} p_mid out of range: {p_mid}"
            assert 0.0 <= p_high <= 1.0, f"{f_path}: {zid} p_high out of range: {p_high}"

            # Strict non-crossing contract
            assert p_low <= p_mid + 1e-6, f"{f_path}: {zid} p_low ({p_low}) > p_mid ({p_mid})"
            assert p_mid <= p_high + 1e-6, f"{f_path}: {zid} p_mid ({p_mid}) > p_high ({p_high})"

            # 3. Exposure, Priority, Rank, Robust
            exposure = z.get("exposure")
            priority = z.get("priority")
            rank = z.get("rank")
            robust = z.get("robust")

            assert isinstance(exposure, (int, float)) and 0.0 <= exposure <= 1.0, f"{f_path}: {zid} invalid exposure {exposure}"
            assert isinstance(priority, (int, float)) and priority >= 0.0, f"{f_path}: {zid} invalid priority {priority}"
            assert isinstance(rank, int) and 1 <= rank <= 33, f"{f_path}: {zid} invalid rank {rank}"
            assert isinstance(robust, bool), f"{f_path}: {zid} robust must be boolean"
            seen_ranks.add(rank)

            # 4. Drivers structure
            assert "drivers" in z, f"{f_path}: {zid} missing drivers object"

        assert len(seen_ids) == 33, f"{f_path}: duplicate zone IDs found"
        assert len(seen_ranks) == 33, f"{f_path}: duplicate ranks found"


def test_fastapi_route_declarations():
    """Verify all 9 required endpoints are registered on the FastAPI app with CORS."""
    routes = {r.path for r in app.routes if hasattr(r, "path")}
    required_routes = {
        "/health",
        "/hazards",
        "/periods",
        "/zones",
        "/ranking",
        "/explain/{zone_id}",
        "/extent",
        "/metrics",
        "/provenance"
    }
    assert required_routes.issubset(routes), f"Missing routes: {required_routes - routes}"

    # Verify CORS middleware installed
    cors_installed = any("CORSMiddleware" in str(m) for m in app.user_middleware)
    assert cors_installed, "CORSMiddleware not configured on FastAPI app"


def test_endpoint_health():
    """GET /health returns healthy status, version, and embeds provenance."""
    resp = get_health()
    assert resp.status == "healthy"
    assert resp.service == "orbitguard-early-warning-service"
    assert resp.version == "1.0.0"
    assert len(resp.timestamp) > 10
    assert len(resp.label_source) > 0
    assert len(resp.warning) > 0


def test_endpoint_hazards():
    """GET /hazards returns multi-hazard catalog and embeds provenance."""
    resp = get_hazards()
    assert len(resp.hazards) > 0
    h = resp.hazards[0]
    assert h.id == "flood"
    assert h.spatial_units == 33
    assert "1_month" in h.lead_times
    assert len(resp.label_source) > 0
    assert len(resp.warning) > 0


def test_endpoint_periods():
    """GET /periods returns precomputed forecast periods."""
    resp = get_periods(hazard="flood")
    assert resp.hazard == "flood"
    assert "2022-06" in resp.periods
    assert "2019-07" in resp.periods
    assert len(resp.periods) >= 72
    assert len(resp.label_source) > 0
    assert len(resp.warning) > 0


def test_endpoint_zones_with_advisory():
    """GET /zones returns 33 zones with non-crossing bounds, exposure, and advisories."""
    resp = get_zones(hazard="flood", period="2022-06", lead="1_month")
    assert resp.hazard == "flood"
    assert resp.period == "2022-06"
    assert resp.lead == "1_month"
    assert len(resp.zones) == 33
    assert len(resp.label_source) > 0
    assert len(resp.warning) > 0

    for z in resp.zones:
        # Non-crossing bounds
        assert z.p_low <= z.p_mid <= z.p_high
        assert 0.0 <= z.exposure <= 1.0
        assert z.priority >= 0.0
        assert 1 <= z.rank <= 33

        # Advisory verification
        adv = z.advisory
        assert adv.level in ["Severe", "Warning", "Watch", "Normal"]
        assert len(adv.headline) > 5
        assert len(adv.reasons) > 0
        assert len(adv.recommended_actions) > 0
        assert "confidence" in adv.model_dump()
        assert "Decision support only; confirm with ASDMA/IMD official advisories." in adv.disclaimer


def test_endpoint_ranking_includes_robust_flag():
    """GET /ranking returns sorted prioritization with robust flag and top 5 robust list."""
    resp = get_ranking(hazard="flood", period="2022-06", lead="1_month")
    assert resp.hazard == "flood"
    assert resp.period == "2022-06"
    assert len(resp.ranking) == 33
    assert len(resp.top_5_robust) == 5
    assert len(resp.label_source) > 0
    assert len(resp.warning) > 0

    # Verify descending sort order by priority
    priorities = [z.priority for z in resp.ranking]
    assert priorities == sorted(priorities, reverse=True)

    # Check rank order
    ranks = [z.rank for z in resp.ranking]
    assert ranks == list(range(1, 34))


def test_endpoint_explain():
    """GET /explain/{zone_id} returns top 5 SHAP drivers with plain-language text."""
    resp = get_explain(zone_id="G01", period="2022-06")
    assert resp.zone_id == "G01"
    assert len(resp.top_drivers) == 5
    assert len(resp.label_source) > 0
    assert len(resp.warning) > 0

    for drv in resp.top_drivers:
        assert drv.feature is not None
        assert drv.importance > 0.0
        assert len(drv.plain_language) > 15


def test_endpoint_extent_success_and_404():
    """GET /extent serves precomputed GeoJSON or raises 404 with error message."""
    # 1. Existing extent (2019-07)
    ext_data = get_extent(period="2019-07")
    assert ext_data["type"] == "FeatureCollection"
    assert "label_source" in ext_data
    assert "warning" in ext_data

    # 2. Non-existent extent returns 404
    with pytest.raises(HTTPException) as exc_info:
        get_extent(period="1999-01")
    assert exc_info.value.status_code == 404
    assert "not found" in exc_info.value.detail.lower()


def test_endpoint_metrics():
    """GET /metrics returns results, event_backtest, and claims_table."""
    resp = get_metrics()
    assert len(resp.results) > 0
    assert len(resp.event_backtest) > 0
    assert len(resp.claims_table) > 0
    assert len(resp.label_source) > 0
    assert len(resp.warning) > 0


def test_endpoint_provenance():
    """GET /provenance returns audit provenance, synthetic circularity findings, and caveats."""
    resp = get_provenance()
    assert resp.mode in ["DEGRADED_MODE", "OPERATIONAL"]
    assert resp.spatial_units == 33
    assert "2014-2025" in resp.vintage
    assert "synthetic_flag_positive_rate" in resp.data_audit_summary
    assert len(resp.sar_independence_caveat) > 20
    assert "1-3 day" in resp.lead_time_limitation
    assert "Decision support only" in resp.asdma_disclaimer
    assert len(resp.label_source) > 0
    assert len(resp.warning) > 0


def test_advisory_rule_levels():
    """Verify rule-based advisory level mapping."""
    # Severe: only if p_low exceeds threshold
    assert determine_advisory_level(p_low=0.08, p_mid=0.15, p_high=0.22, threshold=0.05) == "Severe"

    # Warning: p_mid exceeds threshold, but p_low does not
    assert determine_advisory_level(p_low=0.02, p_mid=0.09, p_high=0.18, threshold=0.05) == "Warning"

    # Watch: only p_high exceeds threshold
    assert determine_advisory_level(p_low=0.01, p_mid=0.03, p_high=0.08, threshold=0.05) == "Watch"

    # Normal: none exceed threshold
    assert determine_advisory_level(p_low=0.005, p_mid=0.02, p_high=0.04, threshold=0.05) == "Normal"


def test_endpoint_advisories():
    """GET /advisories returns all 33 zone advisories with mandatory disclaimer."""
    resp = get_advisories(hazard="flood", period="2022-06", lead="1_month")
    assert resp.hazard == "flood"
    assert resp.period == "2022-06"
    assert len(resp.advisories) == 33
    for item in resp.advisories:
        assert item.zone_id.startswith("G")
        assert item.advisory.level in ("Severe", "Warning", "Watch", "Normal")
        assert "Decision support only" in item.advisory.disclaimer
        assert len(item.advisory.recommended_actions) >= 1
    assert len(resp.label_source) > 0
    assert len(resp.warning) > 0


def test_endpoint_geometry():
    """GET /geometry serves canonical 33-district polygon GeoJSON."""
    geom = get_geometry(hazard="flood")
    assert geom["type"] == "FeatureCollection"
    features = geom.get("features", [])
    assert len(features) == 33
    for f in features:
        assert "geometry" in f
        assert "properties" in f
        assert "geometry_id" in f["properties"] or "district" in f["properties"]
    assert "label_source" in geom
    assert "warning" in geom


def test_endpoint_timeline():
    """GET /timeline serves historical progression across periods."""
    # 1. District timeline
    tl_district = get_timeline(zone_id="G09", hazard="flood")
    assert tl_district.zone_id == "G09"
    assert tl_district.district_name == "Dhemaji"
    assert len(tl_district.timeline) >= 12
    for item in tl_district.timeline:
        assert item.p_low <= item.p_mid <= item.p_high
        assert item.priority >= 0.0

    # 2. Statewide timeline
    tl_state = get_timeline(zone_id=None, hazard="flood")
    assert "Statewide" in tl_state.district_name
    assert len(tl_state.timeline) >= 12


def test_endpoint_overview():
    """GET /overview returns active alerts count and summary exposure."""
    resp = get_overview(hazard="flood", period="2022-06", lead="1_month")
    assert resp.hazard == "flood"
    assert resp.period == "2022-06"
    assert resp.active_alerts_total >= 0
    assert resp.severe_alerts_count + resp.warning_alerts_count + resp.watch_alerts_count + resp.normal_count == 33
    assert len(resp.top_priority_district) > 0
    assert resp.statewide_mean_risk >= 0.0
    assert len(resp.top_5_robust) <= 5
    assert len(resp.label_source) > 0
    assert len(resp.warning) > 0


def test_frontend_compatibility_endpoints():
    """Verify /api/* adapter endpoints work seamlessly for web frontend."""
    # Health
    h = api_health()
    assert h["status"] == "ok"
    assert h["engine"] == "fastapi-lgbm"

    # Dashboard
    dash = api_dashboard(period="2022-06", lead="1_month")
    assert dash["engine"] == "fastapi-lgbm"
    assert len(dash["districts"]) == 33
    assert dash["geojson"]["type"] == "FeatureCollection"
    assert dash["summary"]["alerts"] >= 0

    # Flood Extent
    ext = api_flood_extent(period="2019-07")
    assert ext["type"] == "FeatureCollection"

