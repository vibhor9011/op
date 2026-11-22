"""Phase A: Earth Engine CSV Integration, data cleaning, validation, lag features, and degraded mode handling."""

import os
import glob
import json
import numpy as np
import pandas as pd
from scipy.stats import spearmanr

PROCESSED_DIR = os.path.join("data", "processed")
SAR_POLYGON_MONTH_PATH = os.path.join(PROCESSED_DIR, "sar_polygon_month.csv")
TRAINING_TABLE_PATH = os.path.join(PROCESSED_DIR, "training_table_district_month.csv")
ANNUAL_SAR_VS_OFFICIAL_PATH = os.path.join(PROCESSED_DIR, "annual_sar_vs_official.csv")
BASE_TABLE_PATH = os.path.join(PROCESSED_DIR, "base_district_month.csv")
VALIDATION_LOG_PATH = os.path.join("reports", "ingest_validation.log")


def normalize_geometry_id(val) -> str:
    """Normalize geometry_id to format G01..G33."""
    if pd.isna(val):
        return ""
    s = str(val).strip().upper()
    if s.startswith("G") and s[1:].isdigit():
        return f"G{int(s[1:]):02d}"
    if s.isdigit():
        return f"G{int(s):02d}"
    return s


def clean_dataframe(df: pd.DataFrame, source_file: str = "") -> pd.DataFrame:
    """A1 Clean: strip whitespace, coerce numerics, drop empty rows, normalize geometry_id."""
    df = df.copy()
    # Strip whitespace from headers
    df.columns = [str(c).strip() for c in df.columns]

    # Drop completely empty rows
    df = df.dropna(how="all")

    if "geometry_id" in df.columns:
        df["geometry_id"] = df["geometry_id"].apply(normalize_geometry_id)

    # Coerce numeric columns
    numeric_candidates = [
        "year", "month", "rain_total_mm", "upstream_rain_total_mm", "rain_max1d_mm", "rain_max3d_mm",
        "rain_days_ge20", "rain_days_ge50", "flood_frac_valid", "s1_n_scenes", "s1_coverage",
        "flood_km2", "valid_obs_km2", "pop_2020_sum", "floodplain_frac", "elev_mean_m", "slope_mean_deg",
        "hand_mean_m", "cropland_frac", "builtup_frac", "permwater_frac", "flooded"
    ]
    for col in numeric_candidates:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # Drop exact duplicates
    df = df.drop_duplicates()

    return df


def merge_and_dedup_conflicts(dfs_with_mtime: list, key_cols: list) -> pd.DataFrame:
    """For conflicting duplicates on key_cols, keep the row from the most recently modified file and log it."""
    if not dfs_with_mtime:
        return pd.DataFrame()

    # Sort descending by mtime (most recent first)
    dfs_with_mtime.sort(key=lambda x: x[0], reverse=True)

    combined = []
    for mtime, df in dfs_with_mtime:
        df = df.copy()
        df["_mtime"] = mtime
        combined.append(df)

    merged = pd.concat(combined, ignore_index=True)
    # Deduplicate keeping first (most recently modified)
    before_len = len(merged)
    merged = merged.drop_duplicates(subset=key_cols, keep="first")
    dropped_conflicts = before_len - len(merged)
    if dropped_conflicts > 0:
        print(f"[Phase A1] Resolved {dropped_conflicts} conflicting duplicate rows by keeping latest modified file.")

    merged = merged.drop(columns=["_mtime"])
    return merged


def compute_rain_features(df_rain: pd.DataFrame) -> pd.DataFrame:
    """
    A3 Rain features built on a COMPLETE monthly index per polygon (then shifted):
    - rain_lag1_mm, rain_lag2_mm (shift 1, 2)
    - rain_cum3m_mm, rain_cum6m_mm (rolling sum with min_periods = window)
    - rain_max3d_lag1_mm (shift 1)
    - upstream_rain_lag1_mm (shift 1)
    """
    polygons = [f"G{i+1:02d}" for i in range(33)]
    years = list(range(2013, 2026))
    months = list(range(1, 13))

    # Build full Cartesian product grid
    full_idx = pd.MultiIndex.from_product(
        [polygons, years, months],
        names=["geometry_id", "year", "month"]
    ).to_frame().reset_index(drop=True)

    merged_rain = pd.merge(full_idx, df_rain, on=["geometry_id", "year", "month"], how="left")
    merged_rain = merged_rain.sort_values(["geometry_id", "year", "month"]).reset_index(drop=True)

    # Compute rolling and lag features per polygon
    feat_dfs = []
    for gid, group in merged_rain.groupby("geometry_id", as_index=False):
        group = group.sort_values(["year", "month"]).copy()
        group["rain_lag1_mm"] = group["rain_total_mm"].shift(1)
        group["rain_lag2_mm"] = group["rain_total_mm"].shift(2)
        group["rain_cum3m_mm"] = group["rain_total_mm"].rolling(window=3, min_periods=3).sum()
        group["rain_cum6m_mm"] = group["rain_total_mm"].rolling(window=6, min_periods=6).sum()

        if "rain_max3d_mm" in group.columns:
            group["rain_max3d_lag1_mm"] = group["rain_max3d_mm"].shift(1)
        else:
            group["rain_max3d_lag1_mm"] = group["rain_total_mm"].shift(1)

        group["upstream_rain_lag1_mm"] = group["upstream_rain_total_mm"].shift(1)
        feat_dfs.append(group)

    rain_features_df = pd.concat(feat_dfs, ignore_index=True)
    return rain_features_df


def run_ingest(inventory: dict, degraded_ok: bool = False) -> dict:
    """Execute Phase A Earth Engine CSV integration, validation, and table export."""
    os.makedirs(PROCESSED_DIR, exist_ok=True)
    os.makedirs("reports", exist_ok=True)

    log_lines = []
    def log(msg):
        print(msg)
        log_lines.append(msg)

    log("[Phase A] Initiating Earth Engine CSV Integration and Validation...")

    rain_files = inventory.get("ee_rain_csv", [])
    flood_files = inventory.get("ee_flood_csv", [])
    static_files = inventory.get("ee_static_csv", [])
    ext_files = inventory.get("extension_label", [])

    is_degraded = False
    degraded_reason = ""

    # Check Hard Gates A6
    if not rain_files:
        if not degraded_ok:
            raise FileNotFoundError(
                "HARD GATE FAILURE: No Earth Engine rain CSV found in dataset archive. "
                "Please add orbitguard_chirps_rain_*.csv or run with --degraded-ok."
            )
        is_degraded = True
        degraded_reason = "Earth Engine Rain and Flood CSVs absent"

    if not static_files and not is_degraded:
        if not degraded_ok:
            raise FileNotFoundError(
                "HARD GATE FAILURE: No Earth Engine static CSV found in dataset archive. "
                "Please add orbitguard_static_features_33.csv or run with --degraded-ok."
            )
        is_degraded = True

    if not flood_files:
        is_degraded = True
        degraded_reason = "Sentinel-1 flood observations absent"

    # Base table load
    if not os.path.exists(BASE_TABLE_PATH):
        from core.base import build_base_table
        df_base = build_base_table()
    else:
        df_base = pd.read_csv(BASE_TABLE_PATH)

    results = {
        "is_degraded": is_degraded,
        "degraded_reason": degraded_reason,
        "sar_polygon_month_path": SAR_POLYGON_MONTH_PATH,
        "training_table_path": TRAINING_TABLE_PATH,
        "annual_sar_vs_official_path": ANNUAL_SAR_VS_OFFICIAL_PATH
    }

    if is_degraded:
        log(f"> [!WARNING]\n> **DEGRADED MODE ACTIVE**: {degraded_reason}")
        log("> Stamping 'PIPELINE CHECK ONLY - no observed-derived labels' across all outputs.")

        # Create degraded training table for synthetic pipeline M7
        df_base_train = df_base.copy()
        df_base_train["sar_label_usable"] = 0
        df_base_train["flood_frac_valid"] = np.nan
        df_base_train["degraded_mode_flag"] = 1
        df_base_train.to_csv(TRAINING_TABLE_PATH, index=False)
        log(f"[Phase A] Wrote secondary synthetic training table: {TRAINING_TABLE_PATH} ({len(df_base_train)} rows)")

        # Write empty/placeholder SAR table
        df_empty_sar = pd.DataFrame(columns=[
            "geometry_id", "year", "month", "flood_frac_valid", "s1_n_scenes",
            "s1_coverage", "sar_label_usable", "label_source", "is_synthetic_label",
            "rain_lag1_mm", "rain_lag2_mm", "rain_cum3m_mm", "rain_cum6m_mm"
        ])
        df_empty_sar.to_csv(SAR_POLYGON_MONTH_PATH, index=False)

        # Write empty annual SAR vs official table
        df_empty_annual = pd.DataFrame(columns=["year", "sar_flood_km2_usable", "n_usable_polygons", "official_pop_affected"])
        df_empty_annual.to_csv(ANNUAL_SAR_VS_OFFICIAL_PATH, index=False)

        # Write log
        with open(VALIDATION_LOG_PATH, "w", encoding="utf-8") as f:
            f.write("\n".join(log_lines))

        return results

    # Normal mode: clean and merge rain files
    rain_dfs = []
    for rf in rain_files:
        path = rf["path"]
        mtime = os.path.getmtime(path)
        df_r = clean_dataframe(pd.read_csv(path), path)
        rain_dfs.append((mtime, df_r))
    df_rain_clean = merge_and_dedup_conflicts(rain_dfs, key_cols=["geometry_id", "year", "month"])

    # Normal mode: clean and merge flood files
    flood_dfs = []
    for ff in flood_files:
        path = ff["path"]
        mtime = os.path.getmtime(path)
        df_f = clean_dataframe(pd.read_csv(path), path)
        flood_dfs.append((mtime, df_f))
    df_flood_clean = merge_and_dedup_conflicts(flood_dfs, key_cols=["geometry_id", "year", "month"])

    # Clean static table
    path_s = static_files[0]["path"]
    df_static = clean_dataframe(pd.read_csv(path_s), path_s)
    df_static = df_static.drop_duplicates(subset=["geometry_id"], keep="first")

    # A2 Validate:
    assert (df_static["pop_2020_sum"] > 0).all(), "HARD GATE: pop_2020_sum <= 0 found in static table!"

    # Compute rain features
    rain_features = compute_rain_features(df_rain_clean)

    # A4 SAR label usability
    df_flood_clean["sar_label_usable"] = (
        (df_flood_clean["s1_n_scenes"] >= 2) &
        (df_flood_clean["s1_coverage"] >= 0.5) &
        (df_flood_clean["flood_frac_valid"].notna())
    ).astype(int)

    df_flood_clean["label_source"] = "sentinel1_derived"
    df_flood_clean["is_synthetic_label"] = 0
    df_flood_clean["fold_year"] = df_flood_clean["year"].astype(int)

    # Join primary SAR table
    df_sar_merged = pd.merge(df_flood_clean, rain_features, on=["geometry_id", "year", "month"], how="left")
    df_sar_merged = pd.merge(df_sar_merged, df_static, on="geometry_id", how="left")
    df_sar_merged.to_csv(SAR_POLYGON_MONTH_PATH, index=False)

    # Join secondary district-month training table
    df_training = pd.merge(df_base, rain_features, on=["geometry_id", "year", "month"], how="left")
    df_training = pd.merge(df_training, df_static, on="geometry_id", how="left")
    df_training.to_csv(TRAINING_TABLE_PATH, index=False)

    # A5 Annual SAR vs Official
    usable_rows = df_flood_clean[df_flood_clean["sar_label_usable"] == 1]
    annual_sar = usable_rows.groupby("year").agg(
        sar_flood_km2_usable=("flood_km2", "sum"),
        n_usable_polygons=("geometry_id", "count")
    ).reset_index()

    anchors_csv = inventory.get("official_anchors_csv", [{}])[0].get("path", "")
    if os.path.exists(anchors_csv):
        df_anchors = pd.read_csv(anchors_csv)
        annual_merged = pd.merge(annual_sar, df_anchors[["year", "population_affected_persons"]], on="year", how="left")
        annual_merged = annual_merged.rename(columns={"population_affected_persons": "official_pop_affected"})
    else:
        annual_merged = annual_sar
        annual_merged["official_pop_affected"] = np.nan

    annual_merged.to_csv(ANNUAL_SAR_VS_OFFICIAL_PATH, index=False)

    # Spearman rho validation of the label itself
    valid_pairs = annual_merged.dropna(subset=["sar_flood_km2_usable", "official_pop_affected"])
    if len(valid_pairs) >= 3:
        rho, pval = spearmanr(valid_pairs["sar_flood_km2_usable"], valid_pairs["official_pop_affected"])
        log(f"[Phase A5] Spearman rho (Annual SAR flood_km2 vs Official Pop Affected): {rho:.4f} (p={pval:.4e}, n={len(valid_pairs)})")
    else:
        log("[Phase A5] Insufficient annual pairs for Spearman rho calculation.")

    # Write log
    with open(VALIDATION_LOG_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(log_lines))

    return results


if __name__ == "__main__":
    from core.intake import run_intake
    inv = run_intake()
    run_ingest(inv, degraded_ok=True)
