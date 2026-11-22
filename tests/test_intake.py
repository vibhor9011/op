"""Unit tests for Phase Z intake, path traversal protection, and content classification."""

import os
import io
import zipfile
import pytest
import pandas as pd
from core.intake import safe_extract, classify_file, compute_sha256, SecurityError
from core.ingest import merge_and_dedup_conflicts, clean_dataframe


def test_path_traversal_guard(tmp_path):
    """Verify that safe_extract raises SecurityError if zip contains traversal paths."""
    zip_dest = tmp_path / "malicious.zip"
    extract_dest = tmp_path / "extract_dir"
    extract_dest.mkdir()

    # Create malicious zip with traversal path
    with zipfile.ZipFile(zip_dest, "w") as zf:
        zf.writestr("../../etc/passwd", "evil content")

    with pytest.raises(SecurityError):
        safe_extract(str(zip_dest), str(extract_dest))


def test_content_classification_renamed_files(tmp_path):
    """Verify that file classification succeeds by content signature even if filename is obfuscated."""
    # 1. Synthetic CSV disguised as random name
    synth_file = tmp_path / "random_file_xyz_999.dat"
    df_synth = pd.DataFrame({
        "district": ["Baksa", "Barpeta"],
        "year": [2020, 2020],
        "month": [6, 6],
        "population_affected": [100, 200],
        "flood_affected_status": [1, 1],
        "record_type": ["SYNTHETIC_AUGMENTED", "SYNTHETIC_AUGMENTED"]
    })
    df_synth.to_csv(synth_file, index=False)
    res_synth = classify_file(str(synth_file))
    assert res_synth["type"] == "synthetic_base_csv"

    # 2. Official anchors disguised as random text
    anchor_file = tmp_path / "report_temp_123.tmp"
    df_anchor = pd.DataFrame({
        "year": [2018, 2019],
        "population_affected_persons": [1000000, 2000000],
        "record_type": ["OFFICIAL_STATE_ANNUAL", "OFFICIAL_STATE_ANNUAL"]
    })
    df_anchor.to_csv(anchor_file, index=False)
    res_anchor = classify_file(str(anchor_file))
    assert res_anchor["type"] == "official_anchors_csv"

    # 3. EE Rain CSV disguised
    rain_file = tmp_path / "unknown_climate.bin"
    df_rain = pd.DataFrame({
        "geometry_id": ["G01", "G02"],
        "year": [2021, 2021],
        "month": [7, 7],
        "rain_total_mm": [350.5, 420.0],
        "upstream_rain_total_mm": [500.0, 520.0]
    })
    df_rain.to_csv(rain_file, index=False)
    res_rain = classify_file(str(rain_file))
    assert res_rain["type"] == "ee_rain_csv"


def test_conflicting_duplicate_resolution():
    """Verify that conflicting duplicates on (geometry_id, year, month) keep the latest modified file row."""
    df1 = pd.DataFrame({
        "geometry_id": ["G01", "G02"],
        "year": [2020, 2020],
        "month": [7, 7],
        "rain_total_mm": [100.0, 200.0]
    })
    # Older file (mtime = 100)
    # Newer file (mtime = 200) with conflict on G01
    df2 = pd.DataFrame({
        "geometry_id": ["G01", "G03"],
        "year": [2020, 2020],
        "month": [7, 7],
        "rain_total_mm": [999.0, 300.0]  # updated G01
    })

    dfs_with_mtime = [(100, df1), (200, df2)]
    merged = merge_and_dedup_conflicts(dfs_with_mtime, key_cols=["geometry_id", "year", "month"])

    assert len(merged) == 3
    g01_val = merged[merged["geometry_id"] == "G01"]["rain_total_mm"].iloc[0]
    assert g01_val == 999.0, f"Expected 999.0 from newer file, got {g01_val}"
