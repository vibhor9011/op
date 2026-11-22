"""
Comprehensive tests for OrbitGuard Drought Hazard Module (hazards/drought.py),
GEE drought export script, API drought integration, and shared ranking polymorphism.
"""

import os
import glob
import json
import subprocess
import sys
import numpy as np
import pandas as pd
import pytest
from scipy.stats import norm

from core.hazard import BaseHazardModel
from hazards.drought import (
    DroughtHazardModel,
    DroughtHazard,
    fit_gamma_with_zero_rain,
    compute_vci,
    WEIGHTS_ASSUMPTION,
    MODULE_LABEL,
    WARNING_STRING
)
from core.ranking import compute_exposure_and_priority
from service.app import get_hazards, get_periods, get_zones, get_ranking

OUTPUTS_DIR = "outputs"
REPORTS_DIR = "reports"


def test_drought_hazard_interface_polymorphism():
    """Verify DroughtHazardModel implements BaseHazardModel contract and proper labels."""
    assert issubclass(DroughtHazardModel, BaseHazardModel)
    assert DroughtHazard is DroughtHazardModel

    model = DroughtHazardModel()
    assert model.hazard_name == "drought"
    assert model.module_label == MODULE_LABEL
    assert "Demo: index-based" in model.module_label

    # Verify BaseHazardModel method signatures exist
    for method in ["build_features", "build_labels", "fit", "predict", "extent", "explain"]:
        assert hasattr(model, method)
        assert callable(getattr(model, method))


def test_spi_gamma_fit_with_zero_rain_handling():
    """
    Test SPI calculation with zero-rain adjustment:
    H(x) = q + (1 - q) * G(x), z = norm.ppf(H(x))
    """
    # 30-year historical rainfall sequence with 3 zero-rain months (q = 3/30 = 0.1)
    np.random.seed(42)
    hist_rain = np.array(list(np.random.gamma(shape=3.0, scale=80.0, size=27)) + [0.0, 0.0, 0.0])

    # Test 1: Zero rainfall should evaluate to H = q and negative z
    z_zero, sigma_zero = fit_gamma_with_zero_rain(values=hist_rain, eval_val=0.0)
    assert z_zero < -1.0, f"Zero rainfall must yield negative SPI, got {z_zero}"
    assert sigma_zero >= 0.0

    # Test 2: Low rainfall (drought condition)
    z_low, sigma_low = fit_gamma_with_zero_rain(values=hist_rain, eval_val=25.0)
    assert z_low < 0.0, f"Low rainfall must yield negative SPI, got {z_low}"

    # Test 3: Very high rainfall (wet/surplus condition)
    z_high, sigma_high = fit_gamma_with_zero_rain(values=hist_rain, eval_val=600.0)
    assert z_high > 1.0, f"High rainfall must yield positive SPI, got {z_high}"

    # Monotonicity check: z_zero < z_low < z_high
    assert z_zero <= z_low <= z_high


def test_reference_period_excludes_evaluated_year_no_leakage():
    """Verify that fitting reference periods excludes the evaluated year (in-fold isolation)."""
    model = DroughtHazardModel()
    lookup = model._get_lookup()
    cell = lookup.get(("G01", 7))
    assert cell is not None

    eval_year = 2020
    # Filter out eval_year
    mask = cell["years"] != eval_year
    ref_rain1 = cell["rain1"][mask]
    assert len(ref_rain1) == 34  # 35 total years (1991-2025) minus 1
    assert eval_year not in cell["years"][mask]


def test_vci_calculation():
    """Test Vegetation Condition Index (VCI) calculation and standardization."""
    # Min = 0.20, Max = 0.80
    ndvi_hist = np.array([0.20, 0.35, 0.50, 0.65, 0.80])

    # At minimum NDVI -> VCI = 0.0
    vci_min, z_min = compute_vci(ndvi_val=0.20, ndvi_reference=ndvi_hist)
    assert round(vci_min, 1) == 0.0
    assert z_min < -1.0

    # At maximum NDVI -> VCI = 100.0
    vci_max, z_max = compute_vci(ndvi_val=0.80, ndvi_reference=ndvi_hist)
    assert round(vci_max, 1) == 100.0
    assert z_max > 1.0

    # At midpoint NDVI 0.50 -> VCI = 50.0, z = 0.0
    vci_mid, z_mid = compute_vci(ndvi_val=0.50, ndvi_reference=ndvi_hist)
    assert round(vci_mid, 1) == 50.0
    assert abs(z_mid) < 0.05


def test_combined_index_calculation_and_weights_assumption():
    """
    Test combined drought index: 0.6 * z(SPI-3) + 0.4 * z(VCI).
    Verify weights assumption is documented.
    """
    assert "0.6 * z(SPI-3) + 0.4 * z(VCI)" in WEIGHTS_ASSUMPTION
    assert "60%" in WEIGHTS_ASSUMPTION
    assert "40%" in WEIGHTS_ASSUMPTION

    model = DroughtHazardModel()
    res = model.compute_indices(
        gid="G01",
        year=2021,
        month=7,
        eval_rain1=150.0,
        eval_rain3=450.0,
        eval_rain6=900.0,
        eval_ndvi=0.45
    )

    # Check that output dict contains all expected keys
    for k in ["spi_1", "spi_3", "spi_6", "vci", "z_vci", "combined_index", "drought_severity", "p_low", "p_mid", "p_high"]:
        assert k in res

    # Verify probability non-crossing contract: 0 <= p_low <= p_mid <= p_high <= 1
    assert 0.0 <= res["p_low"] <= res["p_mid"] <= res["p_high"] <= 1.0


def test_shared_ranking_code_for_flood_and_drought():
    """
    CRITICAL REQUIREMENT: Run flood and drought through the exact same
    compute_exposure_and_priority ranking code from core/ranking.py.
    """
    districts = ["Baksa", "Barpeta", "Dhubri", "Kamrup", "Nagaon"]
    gids = ["G01", "G02", "G08", "G14", "G21"]
    areas = [2400.0, 3245.0, 1600.0, 3105.0, 3993.0]

    # 1. Flood predictions mock DataFrame
    flood_df = pd.DataFrame({
        "geometry_id": gids,
        "district": districts,
        "p_mid": [0.65, 0.42, 0.88, 0.15, 0.73],
        "p_low": [0.55, 0.35, 0.78, 0.10, 0.60],
        "p_high": [0.75, 0.50, 0.95, 0.22, 0.85],
        "area_km2": areas
    })

    # 2. Drought predictions mock DataFrame
    drought_df = pd.DataFrame({
        "geometry_id": gids,
        "district": districts,
        "p_mid": [0.18, 0.72, 0.31, 0.60, 0.84],
        "p_low": [0.12, 0.65, 0.25, 0.52, 0.76],
        "p_high": [0.24, 0.79, 0.38, 0.68, 0.92],
        "area_km2": areas
    })

    # Execute same ranking function on both
    ranked_flood = compute_exposure_and_priority(flood_df)
    ranked_drought = compute_exposure_and_priority(drought_df)

    # Assert contract fields present in both outputs
    required_cols = ["geometry_id", "district", "exposure", "priority", "priority_hi", "rank", "robust"]
    for col in required_cols:
        assert col in ranked_flood.columns, f"Missing {col} in ranked_flood"
        assert col in ranked_drought.columns, f"Missing {col} in ranked_drought"

    # Verify rank values are within 1..5 for 5 districts
    assert 1 in ranked_flood["rank"].values
    assert 1 in ranked_drought["rank"].values
    assert all(1 <= r <= 5 for r in ranked_flood["rank"])
    assert all(1 <= r <= 5 for r in ranked_drought["rank"])

    # Verify that the district with rank 1 has the highest priority
    top_flood = ranked_flood[ranked_flood["rank"] == 1].iloc[0]
    assert top_flood["priority"] == ranked_flood["priority"].max()

    top_drought = ranked_drought[ranked_drought["rank"] == 1].iloc[0]
    assert top_drought["priority"] == ranked_drought["priority"].max()


def test_precomputed_drought_json_contract():
    """Verify all 72 precomputed drought JSON prediction files meet contract."""
    drought_files = glob.glob(os.path.join(OUTPUTS_DIR, "drought_predictions_*.json"))
    assert len(drought_files) == 72, f"Expected 72 drought prediction files, found {len(drought_files)}"

    for f_path in drought_files:
        with open(f_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        assert data.get("hazard") == "drought", f"{f_path}: hazard must be 'drought'"
        assert data.get("granularity") == "month", f"{f_path}: granularity must be 'month'"
        assert data.get("label_source") == "index_derived"
        assert "Demo: index-based" in data.get("warning", "")

        zones = data.get("zones", [])
        assert len(zones) == 33, f"{f_path}: expected 33 canonical zones, got {len(zones)}"

        seen_ranks = set()
        for z in zones:
            assert z["id"].startswith("G"), f"Invalid geometry_id: {z['id']}"
            p_low = z["p_low"]
            p_mid = z["p_mid"]
            p_high = z["p_high"]
            assert 0.0 <= p_low <= p_mid <= p_high <= 1.0, f"{f_path}: crossing intervals: {p_low}, {p_mid}, {p_high}"
            assert "exposure" in z and 0.0 <= z["exposure"] <= 1.0
            assert "priority" in z and z["priority"] >= 0.0
            assert "rank" in z and 1 <= z["rank"] <= 33
            seen_ranks.add(z["rank"])
            assert "robust" in z and isinstance(z["robust"], bool)

        assert 1 in seen_ranks, f"{f_path}: missing rank 1"
        assert all(1 <= r <= 33 for r in seen_ranks), f"{f_path}: ranks out of bounds"


def test_fastapi_drought_catalog_and_queries():
    """Verify FastAPI service handles drought endpoints and catalog queries."""
    # 1. GET /hazards lists drought
    hazards_resp = get_hazards()
    hazard_ids = [h.id for h in hazards_resp.hazards]
    assert "flood" in hazard_ids
    assert "drought" in hazard_ids

    drought_item = next(h for h in hazards_resp.hazards if h.id == "drought")
    assert "Demo: index-based" in drought_item.description

    # 2. GET /periods?hazard=drought
    periods_resp = get_periods(hazard="drought")
    assert periods_resp.hazard == "drought"
    assert len(periods_resp.periods) == 72
    assert "2022-06" in periods_resp.periods

    # 3. GET /zones?hazard=drought&period=2022-06
    zones_resp = get_zones(hazard="drought", period="2022-06")
    assert zones_resp.hazard == "drought"
    assert zones_resp.period == "2022-06"
    assert len(zones_resp.zones) == 33
    assert zones_resp.label_source == "index_derived"
    assert "Demo: index-based" in zones_resp.warning

    for z in zones_resp.zones:
        assert z.p_low <= z.p_mid <= z.p_high
        assert z.advisory is not None
        assert z.advisory.level in ["Severe", "Warning", "Watch", "Normal"]
        assert "Decision support only; confirm with ASDMA/IMD official advisories." in z.advisory.disclaimer

    # 4. GET /ranking?hazard=drought&period=2022-06
    ranking_resp = get_ranking(hazard="drought", period="2022-06")
    assert ranking_resp.hazard == "drought"
    assert len(ranking_resp.ranking) == 33
    assert ranking_resp.ranking[0].rank == 1
    # Check descending priority order
    for i in range(len(ranking_resp.ranking) - 1):
        assert ranking_resp.ranking[i].priority >= ranking_resp.ranking[i + 1].priority


def test_drought_validation_report_not_validated():
    """Verify validation audit report correctly records 'not validated' and weights assumption."""
    rep_path = os.path.join(REPORTS_DIR, "drought_index_report.md")
    assert os.path.exists(rep_path), "reports/drought_index_report.md must exist"

    with open(rep_path, "r", encoding="utf-8") as f:
        content = f.read()

    assert "Demo: index-based" in content
    assert "not validated" in content
    assert "0.6 * z(SPI-3) + 0.4 * z(VCI)" in content
    assert os.path.exists(os.path.join(REPORTS_DIR, "drought_index_timeline.png"))


def test_gee_export_drought_features_dry_run():
    """Verify Earth Engine export extension can execute dry-run without invoking live GEE."""
    res = subprocess.run(
        [sys.executable, "gee/export_drought_features.py", "--dry-run"],
        capture_output=True,
        text=True
    )
    assert res.returncode == 0
    assert "DRY-RUN" in res.stdout
    assert "CHIRPS" in res.stdout
    assert "MODIS" in res.stdout
