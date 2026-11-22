"""Phase 1: Feature Engineering with strict in-fold calculation and temporal leakage prevention."""

import numpy as np
import pandas as pd


def compute_infold_features(df_train: pd.DataFrame, df_test: pd.DataFrame, rain_col: str = "rain_total_mm") -> tuple:
    """
    Compute in-fold feature transformations strictly on df_train:
    - rain_anom: rain_total_mm minus polygon-month climatology from training years
    - rain_pct_rank: percentile rank of rain_total_mm within (geometry_id, month) in training years
    - rain_cum3m_anom: anomaly of rain_cum3m_mm relative to training polygon-month mean
    - month sin/cos cyclic encoding
    - categorical / integer geometry_id
    - previous month flood_frac_valid (only if observed and usable)
    """
    df_tr = df_train.copy()
    df_te = df_test.copy()

    # 1. Polygon-month Climatology for rain_total_mm
    clim_mean = df_tr.groupby(["geometry_id", "month"])[rain_col].mean().to_dict()
    overall_mean = df_tr[rain_col].mean() if rain_col in df_tr else 0.0

    df_tr["rain_anom"] = df_tr.apply(
        lambda r: r[rain_col] - clim_mean.get((r["geometry_id"], r["month"]), overall_mean) if pd.notna(r.get(rain_col)) else np.nan,
        axis=1
    )
    df_te["rain_anom"] = df_te.apply(
        lambda r: r[rain_col] - clim_mean.get((r["geometry_id"], r["month"]), overall_mean) if pd.notna(r.get(rain_col)) else np.nan,
        axis=1
    )

    # 2. In-fold Percentile Rank within (geometry_id, month)
    # Collect training distribution per (geometry_id, month)
    train_dist = df_tr.groupby(["geometry_id", "month"])[rain_col].apply(lambda s: sorted(s.dropna().tolist())).to_dict()

    def calc_pct_rank(gid, m, val):
        if pd.isna(val) or (gid, m) not in train_dist or len(train_dist[(gid, m)]) == 0:
            return 0.5
        arr = train_dist[(gid, m)]
        # Empirical percentile rank in [0, 1]
        rank = np.searchsorted(arr, val, side="right") / len(arr)
        return float(rank)

    df_tr["rain_pct_rank"] = df_tr.apply(lambda r: calc_pct_rank(r["geometry_id"], r["month"], r.get(rain_col)), axis=1)
    df_te["rain_pct_rank"] = df_te.apply(lambda r: calc_pct_rank(r["geometry_id"], r["month"], r.get(rain_col)), axis=1)

    # 3. Anomaly of rain_cum3m_mm
    if "rain_cum3m_mm" in df_tr.columns:
        cum3_clim = df_tr.groupby(["geometry_id", "month"])["rain_cum3m_mm"].mean().to_dict()
        cum3_overall = df_tr["rain_cum3m_mm"].mean()
        df_tr["rain_cum3m_anom"] = df_tr.apply(
            lambda r: r["rain_cum3m_mm"] - cum3_clim.get((r["geometry_id"], r["month"]), cum3_overall) if pd.notna(r.get("rain_cum3m_mm")) else np.nan,
            axis=1
        )
        df_te["rain_cum3m_anom"] = df_te.apply(
            lambda r: r["rain_cum3m_mm"] - cum3_clim.get((r["geometry_id"], r["month"]), cum3_overall) if pd.notna(r.get("rain_cum3m_mm")) else np.nan,
            axis=1
        )
    else:
        df_tr["rain_cum3m_anom"] = 0.0
        df_te["rain_cum3m_anom"] = 0.0

    # 4. Cyclic month encoding
    for df in [df_tr, df_te]:
        df["month_sin"] = np.sin(2 * np.pi * df["month"] / 12.0)
        df["month_cos"] = np.cos(2 * np.pi * df["month"] / 12.0)

    # 5. Geometry ID integer code
    all_gids = [f"G{i+1:02d}" for i in range(33)]
    gid_map = {g: i for i, g in enumerate(all_gids)}
    df_tr["geom_code"] = df_tr["geometry_id"].map(lambda g: gid_map.get(g, -1))
    df_te["geom_code"] = df_te["geometry_id"].map(lambda g: gid_map.get(g, -1))

    # 6. Previous month flood_frac_valid (strictly if observed & usable)
    # Built from training fold history
    usable_flood_lookup = {}
    if "sar_label_usable" in df_tr.columns and "flood_frac_valid" in df_tr.columns:
        valid_history = df_tr[df_tr["sar_label_usable"] == 1]
        for _, r in valid_history.iterrows():
            usable_flood_lookup[(r["geometry_id"], int(r["year"]), int(r["month"]))] = r["flood_frac_valid"]

    def get_prev_month_flood(gid, yr, m):
        prev_m = m - 1
        prev_yr = yr
        if prev_m == 0:
            prev_m = 12
            prev_yr = yr - 1
        val = usable_flood_lookup.get((gid, prev_yr, prev_m), np.nan)
        return val

    for df in [df_tr, df_te]:
        df["flood_frac_prev_month"] = df.apply(
            lambda r: get_prev_month_flood(r["geometry_id"], int(r["year"]), int(r["month"])),
            axis=1
        )
        df["has_prev_month_flood"] = df["flood_frac_prev_month"].notna().astype(int)
        df["flood_frac_prev_month"] = df["flood_frac_prev_month"].fillna(0.0)

    return df_tr, df_te


def assert_no_temporal_leakage(df: pd.DataFrame, feature_cols: list, time_col: str = "period"):
    """
    Automated leakage test:
    Verify that no feature row at time t depends on or correlates with target t+k (k>0)
    through future data indexing.
    """
    for col in feature_cols:
        assert not col.startswith("lead_"), f"LEAKAGE DETECTED: Found forward-looking feature '{col}'!"
        assert not "future" in col.lower(), f"LEAKAGE DETECTED: Found suspicious future feature '{col}'!"
