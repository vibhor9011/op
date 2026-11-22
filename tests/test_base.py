"""Unit tests for Phase B boundary harmonization and base table construction."""

import os
import pytest
import pandas as pd
import geopandas as gpd
from core.base import build_base_table, build_canonical_boundaries, DISTRICT_NAME_MAPPING


def test_boundary_geojson_33_districts():
    """Verify that canonical boundaries exist with exactly 33 districts and valid geometry_id."""
    gdf = build_canonical_boundaries()
    assert len(gdf) == 33
    assert "geometry_id" in gdf.columns
    assert list(gdf["geometry_id"].values[:5]) == ["G01", "G02", "G03", "G04", "G05"]
    assert (gdf["area_km2"] > 0).all()
    assert (gdf["centroid_lat"] > 20).all()
    assert (gdf["centroid_lon"] > 88).all()


def test_district_35_to_33_mapping():
    """Verify all 35 synthetic districts map cleanly to boundary polygons."""
    df_base = build_base_table()
    unique_districts = df_base["district"].unique()
    assert len(unique_districts) == 35, f"Expected 35 districts, found {len(unique_districts)}"

    # Check proxies
    bajali = df_base[df_base["district"] == "Bajali"]
    tamulpur = df_base[df_base["district"] == "Tamulpur"]

    assert (bajali["geometry_is_proxy"] == 1).all()
    assert (bajali["polygon_district"] == "Barpeta").all()
    assert (tamulpur["geometry_is_proxy"] == 1).all()
    assert (tamulpur["polygon_district"] == "Baksa").all()

    # Others proxy == 0
    non_proxies = df_base[~df_base["district"].isin(["Bajali", "Tamulpur"])]
    assert (non_proxies["geometry_is_proxy"] == 0).all()


def test_base_table_dimensions_and_prior_year():
    """Verify exact 2,520 rows, prior year pop logic, and anchor merges."""
    df_base = build_base_table()

    # Exact rows
    assert len(df_base) == 2520, f"Expected 2520 rows, got {len(df_base)}"

    # Check 12 years (2014-2025) and 6 months (5-10)
    assert set(df_base["year"].unique()) == set(range(2014, 2026))
    assert set(df_base["month"].unique()) == set(range(5, 11))

    # Prior year pop null for 2014 (35 * 6 = 210 rows)
    rows_2014 = df_base[df_base["year"] == 2014]
    assert len(rows_2014) == 210
    assert rows_2014["prior_year_dist_pop_synthetic"].isna().all()

    # Prior year pop non-null for 2015-2025
    rows_after = df_base[df_base["year"] > 2014]
    assert rows_after["prior_year_dist_pop_synthetic"].notna().all()

    # Check 2024 official anchor is unavailable
    rows_2024 = df_base[df_base["year"] == 2024]
    assert (rows_2024["official_anchor_available"] == 0).all()
