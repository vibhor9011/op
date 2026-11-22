"""Phase 5: Response Prioritization, Multi-factor Exposure, and Sensitivity Analysis.

Formulas:
- exposure = 0.5 * pop_2020_sum_n + 0.2 * cropland_frac_n + 0.3 * builtup_frac_n
- priority = p_mid * exposure
- priority_hi = p_high * exposure
- rank: ascending rank by priority (1 = highest priority)
- robust: True if rank <= 5 and rank_hi <= 5
- +/-20% weight sensitivity table
"""

import os
import json
import numpy as np
import pandas as pd


def normalize_series(s: pd.Series) -> pd.Series:
    """Min-max normalize a series to [0, 1]."""
    s_clean = s.fillna(0.0)
    s_min = s_clean.min()
    s_max = s_clean.max()
    if s_max > s_min:
        return (s_clean - s_min) / (s_max - s_min)
    return pd.Series(0.0, index=s.index)


def compute_exposure_and_priority(
    df: pd.DataFrame,
    weight_pop: float = 0.5,
    weight_crop: float = 0.2,
    weight_built: float = 0.3
) -> pd.DataFrame:
    """
    Compute composite exposure and priority scores:
    - exposure = 0.5 * pop_n + 0.2 * crop_n + 0.3 * built_n
    - priority = p_mid * exposure
    - priority_hi = p_high * exposure
    - rank = rank by priority (1 = highest priority)
    - rank_hi = rank by priority_hi (1 = highest priority)
    - robust = True if rank <= 5 and rank_hi <= 5
    """
    df_out = df.copy()

    # Normalize exposure components across polygons
    if "pop_2020_sum" in df_out.columns and df_out["pop_2020_sum"].notna().any():
        pop_n = normalize_series(df_out["pop_2020_sum"])
    elif "pop_affected_synthetic" in df_out.columns:
        pop_n = normalize_series(df_out["pop_affected_synthetic"])
    else:
        pop_n = normalize_series(df_out.get("area_km2", pd.Series(1.0, index=df_out.index)))

    if "cropland_frac" in df_out.columns and df_out["cropland_frac"].notna().any():
        crop_n = normalize_series(df_out["cropland_frac"])
    else:
        crop_n = pd.Series(0.0, index=df_out.index)

    if "builtup_frac" in df_out.columns and df_out["builtup_frac"].notna().any():
        built_n = normalize_series(df_out["builtup_frac"])
    else:
        built_n = pd.Series(0.0, index=df_out.index)

    # Composite exposure
    df_out["exposure"] = (
        weight_pop * pop_n +
        weight_crop * crop_n +
        weight_built * built_n
    ).round(4)

    # Obtain p_mid and p_high
    if "p_mid" in df_out.columns:
        p_mid = df_out["p_mid"].fillna(0.0)
    elif "y_sev_synthetic" in df_out.columns:
        p_mid = normalize_series(df_out["y_sev_synthetic"])
    else:
        p_mid = pd.Series(0.5, index=df_out.index)

    if "p_high" in df_out.columns:
        p_high = df_out["p_high"].fillna(0.0)
    else:
        p_high = np.clip(p_mid * 1.3, 0.0, 1.0)

    # Compute priorities
    df_out["priority"] = (p_mid * df_out["exposure"]).round(4)
    df_out["priority_hi"] = (p_high * df_out["exposure"]).round(4)

    # Rank descending: 1 is highest priority
    # If grouping by period (year, month), rank within period; else rank overall
    if "year" in df_out.columns and "month" in df_out.columns:
        df_out["rank"] = df_out.groupby(["year", "month"])["priority"].rank(ascending=False, method="min").astype(int)
        df_out["rank_hi"] = df_out.groupby(["year", "month"])["priority_hi"].rank(ascending=False, method="min").astype(int)
    else:
        df_out["rank"] = df_out["priority"].rank(ascending=False, method="min").astype(int)
        df_out["rank_hi"] = df_out["priority_hi"].rank(ascending=False, method="min").astype(int)

    # robust: top 5 under both priority and priority_hi
    df_out["robust"] = (df_out["rank"] <= 5) & (df_out["rank_hi"] <= 5)

    return df_out


def generate_weight_sensitivity_table(df: pd.DataFrame) -> pd.DataFrame:
    """
    Generate +/-20% weight sensitivity table for exposure ranking:
    Baseline: Pop=0.5, Crop=0.2, Built=0.3
    - Pop +20%: Pop=0.6, Crop=0.15, Built=0.25
    - Pop -20%: Pop=0.4, Crop=0.25, Built=0.35
    - Crop +20%: Pop=0.45, Crop=0.24, Built=0.31
    - Built +20%: Pop=0.45, Crop=0.19, Built=0.36
    """
    configs = {
        "Rank_Baseline": (0.50, 0.20, 0.30),
        "Rank_Pop_Plus20": (0.60, 0.15, 0.25),
        "Rank_Pop_Minus20": (0.40, 0.25, 0.35),
        "Rank_Crop_Plus20": (0.45, 0.24, 0.31),
        "Rank_Built_Plus20": (0.45, 0.19, 0.36)
    }

    res_df = df[["geometry_id", "district"]].drop_duplicates().copy()

    for col_name, (wp, wc, wb) in configs.items():
        ranked = compute_exposure_and_priority(df, weight_pop=wp, weight_crop=wc, weight_built=wb)
        mean_rank = ranked.groupby(["geometry_id", "district"])["rank"].mean().reset_index()
        mean_rank = mean_rank.rename(columns={"rank": col_name})
        res_df = pd.merge(res_df, mean_rank, on=["geometry_id", "district"], how="left")

    rank_cols = list(configs.keys())
    res_df["Max_Rank_Shift"] = res_df[rank_cols].max(axis=1) - res_df[rank_cols].min(axis=1)

    return res_df.sort_values("Rank_Baseline").reset_index(drop=True)
