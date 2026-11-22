"""Unit tests for Phase 1 temporal leakage prevention and in-fold transformation isolation."""

import pytest
import numpy as np
import pandas as pd
from core.features import compute_infold_features, assert_no_temporal_leakage


def test_infold_climatology_isolation():
    """Verify that climatology and anomalies are fit strictly on training folds."""
    # Training data: 2 years (2018, 2019) for polygon G01 in month 6
    df_train = pd.DataFrame({
        "geometry_id": ["G01", "G01"],
        "year": [2018, 2019],
        "month": [6, 6],
        "rain_total_mm": [100.0, 200.0],
        "rain_cum3m_mm": [300.0, 400.0]
    })
    # Mean in train is 150.0

    # Test data: year 2020 with extreme value 1000.0
    df_test = pd.DataFrame({
        "geometry_id": ["G01"],
        "year": [2020],
        "month": [6],
        "rain_total_mm": [1000.0],
        "rain_cum3m_mm": [1200.0]
    })

    df_tr_feat, df_te_feat = compute_infold_features(df_train, df_test)

    # In training, anomalies relative to 150: 100 - 150 = -50, 200 - 150 = +50
    assert np.isclose(df_tr_feat["rain_anom"].iloc[0], -50.0)
    assert np.isclose(df_tr_feat["rain_anom"].iloc[1], 50.0)

    # In test, anomaly MUST be relative to training mean (150.0), NOT including test value
    # If leakage occurred, mean would be (100+200+1000)/3 = 433.33
    assert np.isclose(df_te_feat["rain_anom"].iloc[0], 1000.0 - 150.0)  # 850.0


def test_percentile_rank_in_fold():
    """Verify percentile rank is bounded in [0, 1] and derived strictly from training distribution."""
    df_train = pd.DataFrame({
        "geometry_id": ["G01", "G01", "G01"],
        "year": [2015, 2016, 2017],
        "month": [7, 7, 7],
        "rain_total_mm": [100.0, 200.0, 300.0]
    })
    df_test = pd.DataFrame({
        "geometry_id": ["G01", "G01"],
        "year": [2018, 2018],
        "month": [7, 7],
        "rain_total_mm": [50.0, 500.0]  # One below min, one above max
    })

    _, df_te_feat = compute_infold_features(df_train, df_test)

    assert df_te_feat["rain_pct_rank"].iloc[0] == 0.0  # 50 is <= 100
    assert df_te_feat["rain_pct_rank"].iloc[1] == 1.0  # 500 is > 300


def test_temporal_leakage_assertion():
    """Verify that assert_no_temporal_leakage flags forward-looking features."""
    safe_features = ["rain_lag1_mm", "rain_lag2_mm", "rain_cum3m_mm", "month_sin"]
    assert_no_temporal_leakage(None, safe_features)

    with pytest.raises(AssertionError):
        assert_no_temporal_leakage(None, ["rain_lag1_mm", "lead_rain_mm"])

    with pytest.raises(AssertionError):
        assert_no_temporal_leakage(None, ["future_flood_flag", "month_cos"])
