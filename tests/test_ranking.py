"""Unit tests for Phase 5 response prioritization and sensitivity analysis."""

import pytest
import numpy as np
import pandas as pd
from core.ranking import compute_exposure_and_priority, generate_weight_sensitivity_table


def test_exposure_and_priority_calculation():
    """Verify priority score weighting and integer ranking properties."""
    df = pd.DataFrame({
        "geometry_id": ["G01", "G02", "G03"],
        "district": ["DistA", "DistB", "DistC"],
        "p_mid": [0.8, 0.5, 0.1],
        "p_high": [0.9, 0.6, 0.2],
        "pop_2020_sum": [100000, 500000, 200000],
        "builtup_frac": [0.05, 0.20, 0.02],
        "cropland_frac": [0.30, 0.40, 0.10]
    })

    ranked = compute_exposure_and_priority(df)

    assert "exposure" in ranked.columns
    assert "priority" in ranked.columns
    assert "priority_hi" in ranked.columns
    assert "rank" in ranked.columns
    assert "rank_hi" in ranked.columns
    assert "robust" in ranked.columns

    # Exposure score must be in [0, 1]
    assert (ranked["exposure"] >= 0.0).all() and (ranked["exposure"] <= 1.0).all()

    # Priority score = p_mid * exposure
    expected_pri = (ranked["p_mid"] * ranked["exposure"]).round(4)
    assert np.allclose(ranked["priority"], expected_pri)

    # Ranks must be 1, 2, 3
    ranks = sorted(ranked["rank"].tolist())
    assert ranks == [1, 2, 3]


def test_ranking_sensitivity_table():
    """Verify +/-20% weight sensitivity table."""
    df = pd.DataFrame({
        "geometry_id": ["G01", "G02"],
        "district": ["Baksa", "Barpeta"],
        "p_mid": [0.7, 0.4],
        "p_high": [0.85, 0.55],
        "pop_2020_sum": [200000, 800000],
        "builtup_frac": [0.02, 0.15],
        "cropland_frac": [0.45, 0.20]
    })

    sens_table = generate_weight_sensitivity_table(df)

    assert "Rank_Baseline" in sens_table.columns
    assert "Rank_Pop_Plus20" in sens_table.columns
    assert "Rank_Pop_Minus20" in sens_table.columns
    assert "Rank_Crop_Plus20" in sens_table.columns
    assert "Rank_Built_Plus20" in sens_table.columns
    assert "Max_Rank_Shift" in sens_table.columns

    assert not sens_table.isna().any().any()
