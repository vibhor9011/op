"""Unit tests for Hazard Baselines (B0-B3) and Machine Learning Models (M1-M7)."""

import pytest
import numpy as np
import pandas as pd
from hazards.flood import FloodBaselines, FloodHazardModel, compute_ece


def create_dummy_dataset(n_samples: int = 150):
    """Create synthetic test dataset for model unit testing."""
    np.random.seed(42)
    polys = ["G01", "G02", "G03"]
    years = [2018, 2019, 2020]
    months = [6, 7, 8]

    records = []
    for i in range(n_samples):
        gid = np.random.choice(polys)
        yr = np.random.choice(years)
        m = np.random.choice(months)
        rain = np.random.uniform(50, 600)
        flood_frac = np.clip((rain - 100) / 1000.0 + np.random.normal(0, 0.01), 0, 0.15)
        records.append({
            "geometry_id": gid,
            "year": yr,
            "month": m,
            "rain_total_mm": rain,
            "rain_lag1_mm": rain * 0.9,
            "rain_cum3m_mm": rain * 2.5,
            "month_sin": np.sin(2 * np.pi * m / 12.0),
            "month_cos": np.cos(2 * np.pi * m / 12.0),
            "geom_code": int(gid[1:]),
            "flood_frac_valid": flood_frac,
            "sar_label_usable": 1
        })
    df = pd.DataFrame(records)
    return df


def test_flood_baselines_b0_b3():
    """Verify B0-B3 baseline models fit and output valid probabilities."""
    df = create_dummy_dataset(120)
    y_cls = (df["flood_frac_valid"] >= 0.02).astype(int)

    base_model = FloodBaselines()
    base_model.fit(df, y_cls)
    preds = base_model.predict(df)

    assert "B0_climatology" in preds
    assert "B1_month_mean" in preds
    assert "B2_logistic" in preds
    assert "B3_persistence" in preds

    for name, p in preds.items():
        assert len(p) == len(df)
        assert (p >= 0.0).all() and (p <= 1.0).all(), f"Baseline {name} produced out-of-bounds probs!"


def test_flood_hazard_model_m1_m5():
    """Verify LightGBM classifier M1, Isotonic calibration M2, Quantiles M3, CQR M4, and predict [p_low, p_mid, p_high]."""
    df = create_dummy_dataset(150)
    y_cls = (df["flood_frac_valid"] >= 0.02).astype(int)
    y_reg = df["flood_frac_valid"]

    model = FloodHazardModel()
    model.fit(df, y_cls, y_reg)

    # Test predict() returning DataFrame[p_low, p_mid, p_high]
    pred_df = model.predict(df)
    assert isinstance(pred_df, pd.DataFrame)
    assert set(pred_df.columns) == {"p_low", "p_mid", "p_high"}
    assert len(pred_df) == len(df)

    # Bounds: 0 <= p_low <= p_mid <= p_high <= 1
    assert (pred_df["p_low"] >= 0.0).all() and (pred_df["p_low"] <= 1.0).all()
    assert (pred_df["p_mid"] >= 0.0).all() and (pred_df["p_mid"] <= 1.0).all()
    assert (pred_df["p_high"] >= 0.0).all() and (pred_df["p_high"] <= 1.0).all()
    assert (pred_df["p_low"] <= pred_df["p_mid"] + 1e-6).all()
    assert (pred_df["p_mid"] <= pred_df["p_high"] + 1e-6).all()

    # ECE should be finite and non-negative
    ece = compute_ece(y_cls.values, pred_df["p_mid"].values)
    assert ece >= 0.0 and ece <= 1.0

    # Predict Quantiles & CQR
    q_df = model.predict_quantiles(df)
    assert "q10" in q_df.columns and "q90" in q_df.columns
    assert "cqr_low" in q_df.columns and "cqr_high" in q_df.columns

    # CQR ordering
    assert (q_df["cqr_low"] <= q_df["cqr_high"]).all()

    # Empirical CQR Coverage target >= 80% on training residuals
    covered = (y_reg.values >= q_df["cqr_low"].values) & (y_reg.values <= q_df["cqr_high"].values)
    coverage_rate = np.mean(covered)
    assert coverage_rate >= 0.80, f"Expected CQR coverage >= 80%, got {coverage_rate*100:.2f}%"

    # Risk tier mapping
    assert model.map_risk_tier(0.10) == "low"
    assert model.map_risk_tier(0.40) == "mid"
    assert model.map_risk_tier(0.85) == "high"
