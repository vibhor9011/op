"""Unit tests for Historical Event Backtesting and Deck Claims Audit."""

import os
import json
import pytest
import pandas as pd
from core.backtest import run_event_backtest


def test_event_backtest_execution():
    """Verify that event backtest produces expected reports, metrics JSON, and plots."""
    res = run_event_backtest()

    # 1. Events selected
    assert res["severe_events_selected"] == [2019, 2020, 2022]

    # 2. Extent overlap placeholder
    assert res["extent_overlap"]["status"] is None
    assert res["extent_overlap"]["reason"] == "no reference layer supplied"

    # 3. Check event metrics
    for yr_str in ["2019", "2020", "2022"]:
        ev = res["events"][yr_str]
        assert ev["mae_l1"] >= 0.0 and ev["mae_l1"] <= 1.0
        assert -1.0 <= ev["cal_in_large_l1"] <= 1.0
        hits = ev["top10_peak"]["hits"]
        misses = ev["top10_peak"]["misses"]
        fa = ev["top10_peak"]["false_alarms"]
        assert hits + misses == 10
        assert hits + fa == 10
        assert 0.0 <= ev["monthly_lead_time"]["share_flagged"] <= 1.0

    # 4. Check generated plot files
    for plot_name in [
        "event_predicted_vs_observed_timeline.png",
        "event_reliability_diagram.png",
        "event_ranking_hit_chart.png"
    ]:
        p = os.path.join("reports", plot_name)
        assert os.path.exists(p) and os.path.getsize(p) > 1000


def test_claims_table_structure():
    """Verify metrics/claims_table.json structure and coverage."""
    claims_path = os.path.join("metrics", "claims_table.json")
    assert os.path.exists(claims_path)

    with open(claims_path, "r", encoding="utf-8") as f:
        claims = json.load(f)

    expected_claims = [
        "probability_with_band",
        "1_to_3_day_forecast",
        "sar_extent",
        "bhuvan_overlap",
        "ranking",
        "multi_hazard"
    ]
    for c in expected_claims:
        assert c in claims
        assert "status" in claims[c]
        assert "evidence_file" in claims[c]
        assert claims[c]["status"] in ["validated", "partly", "not_validated", "planned"]

    # 1-3 day forecast MUST be not_validated
    assert claims["1_to_3_day_forecast"]["status"] == "not_validated"
    assert claims["bhuvan_overlap"]["status"] == "not_validated"
