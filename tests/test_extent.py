"""Tests for SAR Extent Extraction, Earth Engine Script, and Local Processing."""

import os
import json
import pytest
import geopandas as gpd
from shapely.geometry import Polygon

from sar.export_extent_ee import determine_default_event_window
from sar.extent import (
    process_extent,
    search_for_file,
    compute_vector_overlap_metrics,
    MANDATORY_CAVEAT
)
from hazards.flood import FloodHazardModel, FloodHazard


def test_determine_default_event_window():
    """Verify default event window detection falls in valid monsoon months (5-10) and years."""
    year, month = determine_default_event_window()
    assert 2014 <= year <= 2025
    assert 5 <= month <= 10


def test_process_extent_creates_valid_deliverables(tmp_path):
    """Verify extent processing generates GeoJSON, summary JSON, and updates prediction JSON."""
    out_dir = str(tmp_path)
    summary = process_extent(year=2020, month=7, outputs_dir=out_dir)

    assert summary["period"] == "2020-07"
    assert summary["year"] == 2020
    assert summary["month"] == 7
    assert "thresholds" in summary
    assert summary["thresholds"]["fixed_vv_threshold_db"] == -16.0
    assert "otsu_vv_threshold_db" in summary["thresholds"]
    assert "dates" in summary
    assert "scenes_used" in summary
    assert summary["scenes_used"]["mode"] == "IW"
    assert summary["scenes_used"]["polarization"] == "VV"

    # Validation & Caveat verification
    assert "validation" in summary
    val = summary["validation"]
    assert val["status"] == "visually validated only"
    assert val["reference_layer"] is None
    assert val["iou"] is None
    assert val["f1"] is None
    assert MANDATORY_CAVEAT in val["caveat"]

    # Statewide and Polygons
    assert summary["statewide_flooded_km2"] > 0
    assert len(summary["polygons"]) == 33
    p0 = summary["polygons"][0]
    assert "geometry_id" in p0
    assert "flooded_km2" in p0
    assert "share_of_valid_land" in p0
    assert "scenes_used" in p0

    # Verify GeoJSON output file
    geojson_path = os.path.join(out_dir, "flood_extent_2020_07.geojson")
    assert os.path.exists(geojson_path)
    gdf = gpd.read_file(geojson_path)
    assert not gdf.empty
    assert "geometry_id" in gdf.columns
    assert "flooded_km2" in gdf.columns
    assert "period" in gdf.columns

    # Verify prediction JSON output file
    pred_path = os.path.join(out_dir, "flood_predictions_2020_07.json")
    assert os.path.exists(pred_path)
    with open(pred_path, "r", encoding="utf-8") as f:
        pred_data = json.load(f)

    assert pred_data["period"] == "2020-07"
    assert len(pred_data["zones"]) == 33
    zone0 = pred_data["zones"][0]
    assert "observed_flood_km2" in zone0
    assert "observed_flood_frac" in zone0
    assert isinstance(zone0["observed_flood_km2"], (int, float))
    assert isinstance(zone0["observed_flood_frac"], (int, float))


def test_flood_hazard_extent_method(tmp_path):
    """Verify FloodHazardModel.extent(period) and alias FloodHazard work correctly."""
    model = FloodHazardModel()
    res = model.extent(period="2019-07")
    assert res is not None
    assert res["period"] == "2019-07"

    # Check alias
    model_alias = FloodHazard()
    assert isinstance(model_alias, FloodHazardModel)


def test_compute_vector_overlap_with_mock_reference(tmp_path):
    """Test IoU and F1 score calculation when a mock reference layer is provided."""
    ref_geojson = tmp_path / "mock_bhuvan_flood.geojson"

    # Create footprint polygon and reference polygon with known overlap in EPSG:4326
    # Footprint: box [91.0, 26.0, 92.0, 27.0]
    # Ref: box [91.5, 26.0, 92.5, 27.0] (50% horizontal overlap)
    poly_fp = Polygon([(91.0, 26.0), (92.0, 26.0), (92.0, 27.0), (91.0, 27.0)])
    poly_ref = Polygon([(91.5, 26.0), (92.5, 26.0), (92.5, 27.0), (91.5, 27.0)])

    gdf_fp = gpd.GeoDataFrame([{"geometry": poly_fp, "geometry_id": "G01"}], crs="EPSG:4326")
    gdf_ref = gpd.GeoDataFrame([{"geometry": poly_ref, "reference": 1}], crs="EPSG:4326")
    gdf_ref.to_file(ref_geojson, driver="GeoJSON")

    val_res = compute_vector_overlap_metrics(gdf_fp, str(ref_geojson))
    assert val_res["status"] == "validated against reference layer"
    assert val_res["iou"] is not None
    assert 0.30 <= val_res["iou"] <= 0.40  # 0.5 / 1.5 = 0.333
    assert 0.45 <= val_res["f1"] <= 0.55   # 2 * 0.5 / (1.0 + 1.0) = 0.50
    assert MANDATORY_CAVEAT in val_res["caveat"]
