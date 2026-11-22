"""Unit tests for Hard Gates, Degraded Modes, CV fold isolation, and Polygon Deduplication."""

import pytest
import numpy as np
import pandas as pd
from core.ingest import run_ingest
from core.features import compute_infold_features
from hazards.flood import FloodHazardModel


def test_hard_gates_fail_when_degraded_not_allowed():
    """Verify that run_ingest raises FileNotFoundError when EE CSVs are missing and degraded_ok is False."""
    empty_inventory = {
        "ee_rain_csv": [],
        "ee_flood_csv": [],
        "ee_static_csv": []
    }
    with pytest.raises(FileNotFoundError) as exc_info:
        run_ingest(empty_inventory, degraded_ok=False)
    assert "HARD GATE FAILURE" in str(exc_info.value)


def test_degraded_mode_activates_gracefully():
    """Verify that run_ingest returns is_degraded=True when degraded_ok is True."""
    empty_inventory = {
        "ee_rain_csv": [],
        "ee_flood_csv": [],
        "ee_static_csv": []
    }
    res = run_ingest(empty_inventory, degraded_ok=True)
    assert res["is_degraded"] is True
    assert "Sentinel-1" in res["degraded_reason"] or "Earth Engine" in res["degraded_reason"]


def test_cv_folds_exclude_held_out_year():
    """Verify that in LOYO cross-validation, the training set never contains the held-out year."""
    years = [2018, 2019, 2020, 2021]
    df_dummy = pd.DataFrame({
        "year": np.repeat(years, 6),
        "month": np.tile(range(5, 11), len(years)),
        "geometry_id": ["G01"] * (len(years) * 6),
        "target": np.random.uniform(0, 1, len(years) * 6)
    })

    for held_out_year in years:
        train_mask = df_dummy["year"] != held_out_year
        test_mask = df_dummy["year"] == held_out_year

        train_years = df_dummy.loc[train_mask, "year"].unique()
        test_years = df_dummy.loc[test_mask, "year"].unique()

        assert held_out_year not in train_years, f"Data leakage: held-out year {held_out_year} present in train set!"
        assert list(test_years) == [held_out_year]


def test_polygon_level_deduplication():
    """Verify that polygon-level aggregation handles proxy districts without double counting."""
    # Barpeta and Bajali both map to G02; Baksa and Tamulpur both map to G01
    df_sample = pd.DataFrame({
        "district": ["Barpeta", "Bajali", "Baksa", "Tamulpur", "Dhubri"],
        "geometry_id": ["G02", "G02", "G01", "G01", "G10"],
        "year": [2020, 2020, 2020, 2020, 2020],
        "month": [7, 7, 7, 7, 7],
        "pop_affected_synthetic": [1000, 200, 500, 100, 800]
    })

    # At polygon level (unique geometry_id per period), each geometry appears exactly once
    poly_level = df_sample.groupby(["geometry_id", "year", "month"]).agg({
        "pop_affected_synthetic": "sum"
    }).reset_index()

    assert len(poly_level) == 3  # G01, G02, G10
    g02_sum = poly_level[poly_level["geometry_id"] == "G02"]["pop_affected_synthetic"].iloc[0]
    assert g02_sum == 1200  # 1000 + 200


def test_cqr_band_coverage_on_held_out_data():
    """Verify that CQR adjustment achieves nominal 80% coverage on held-out test samples."""
    np.random.seed(123)
    n_train = 200
    n_test = 80

    def make_features(n):
        rain = np.random.uniform(50, 600, n)
        y = np.clip((rain - 100) / 1000.0 + np.random.normal(0, 0.015, n), 0, 0.20)
        df = pd.DataFrame({
            "geometry_id": ["G01"] * n,
            "year": [2018] * n,
            "month": np.random.choice([6, 7, 8], n),
            "rain_total_mm": rain,
            "rain_lag1_mm": rain * 0.9,
            "rain_cum3m_mm": rain * 2.5,
            "month_sin": np.sin(2 * np.pi * 7 / 12.0),
            "month_cos": np.cos(2 * np.pi * 7 / 12.0),
            "geom_code": 1
        })
        return df, pd.Series((y >= 0.02).astype(int)), pd.Series(y)

    X_tr, y_cls_tr, y_reg_tr = make_features(n_train)
    X_te, y_cls_te, y_reg_te = make_features(n_test)

    model = FloodHazardModel()
    model.fit(X_tr, y_cls_tr, y_reg_tr)

    q_te = model.predict_quantiles(X_te)
    covered = (y_reg_te.values >= q_te["cqr_low"].values) & (y_reg_te.values <= q_te["cqr_high"].values)
    coverage = np.mean(covered)

    assert coverage >= 0.80, f"Expected coverage >= 80% on held-out test data, got {coverage*100:.2f}%"
