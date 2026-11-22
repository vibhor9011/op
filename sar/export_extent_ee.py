"""
Google Earth Engine Sentinel-1 Flood Extent Extraction Script.
==============================================================
NOTE: This script is designed for manual execution via Google Earth Engine API.
DO NOT run automatically inside sandboxed unit test runners.
Run as:
    earthengine authenticate
    python sar/export_extent_ee.py [--year YYYY] [--month MM] [--drive-folder FOLDER]

Algorithm:
1. Sentinel-1 GRD, IW mode, VV polarization.
2. Identical orbit pass (ASCENDING or DESCENDING) for pre-event and event.
3. Pre-event baseline: Jan 1 - Feb 28 median composite of the same calendar year.
4. Event composite: 1st of month to end of month.
5. Smoothing: Focal median 30m filter.
6. Water thresholding: Fixed threshold (-16 dB) and Otsu thresholding on event image; both reported.
7. Terrain and permanent water masking:
   - JRC Global Surface Water occurrence < 50%
   - SRTM elevation slope < 5 degrees
   - MERIT Hydro Height Above Nearest Drainage (HAND) < 15 m
   - Event water AND NOT Pre-event water
8. Minimum Mapping Unit (MMU): Connected flood patches < 5 ha removed.
9. Exports to Google Drive:
   - GeoJSON of simplified flood polygons (100 m tolerance).
   - CSV of flooded km2 per canonical geometry_id (G01..G33).
"""

import os
import sys
import json
import calendar
import argparse
from typing import Tuple, Dict, Any

try:
    import ee
except ImportError:
    ee = None


DEFAULT_DRIVE_FOLDER = "OrbitGuard_SAR_Extent"
CANONICAL_GEOJSON_PATH = os.path.join("data", "processed", "assam_districts_33.geojson")
SAR_DATA_PATH = os.path.join("data", "processed", "sar_polygon_month.csv")
BASE_DATA_PATH = os.path.join("data", "processed", "base_district_month.csv")


def determine_default_event_window() -> Tuple[int, int]:
    """
    Determine default event window (year, month).
    Prioritizes:
    1. Single most flooded month by SAR if sar_polygon_month.csv has usable rows.
    2. Peak month from base_district_month.csv.
    3. Fallback to July 2020 (2020, 7).
    """
    # 1. Check SAR table
    if os.path.exists(SAR_DATA_PATH):
        try:
            import pandas as pd
            df_sar = pd.read_csv(SAR_DATA_PATH)
            if not df_sar.empty and "flood_frac_valid" in df_sar.columns and "sar_label_usable" in df_sar.columns:
                df_usable = df_sar[df_sar["sar_label_usable"] == 1]
                if not df_usable.empty:
                    top_sar = df_usable.groupby(["year", "month"])["flood_frac_valid"].sum().idxmax()
                    return int(top_sar[0]), int(top_sar[1])
        except Exception:
            pass

    # 2. Check base table
    if os.path.exists(BASE_DATA_PATH):
        try:
            import pandas as pd
            df_base = pd.read_csv(BASE_DATA_PATH)
            if not df_base.empty and "pop_affected_synthetic" in df_base.columns:
                top_base = df_base.groupby(["year", "month"])["pop_affected_synthetic"].sum().idxmax()
                return int(top_base[0]), int(top_base[1])
        except Exception:
            pass

    # 3. Canonical peak default
    return 2020, 7


def compute_otsu_threshold_ee(image, region, scale: int = 100):
    """
    Computes Otsu threshold on a single-band Earth Engine image within a region.
    Maximizes between-class variance over the backscatter histogram.
    """
    histogram = image.reduceRegion(
        reducer=ee.Reducer.histogram(numBins=120, minBucketWidth=0.25, maxBuckets=120),
        geometry=region,
        scale=scale,
        maxPixels=1e9
    )

    hist_dict = ee.Dictionary(histogram.get("VV"))
    counts = ee.Array(hist_dict.get("histogram"))
    means = ee.Array(hist_dict.get("bucketMeans"))
    size = counts.length().get([0])
    total = counts.reduce(ee.Reducer.sum(), [0]).get([0])
    sum_all = means.multiply(counts).reduce(ee.Reducer.sum(), [0]).get([0])
    global_mean = sum_all.divide(total)

    indices = ee.List.sequence(1, size)

    def calc_bss(i):
        a_counts = counts.slice(0, 0, i)
        a_count = a_counts.reduce(ee.Reducer.sum(), [0]).get([0])
        a_means = means.slice(0, 0, i)
        a_mean = a_means.multiply(a_counts).reduce(ee.Reducer.sum(), [0]).get([0]).divide(a_count)
        b_count = total.subtract(a_count)
        b_mean = sum_all.subtract(a_count.multiply(a_mean)).divide(b_count)
        return a_count.multiply(a_mean.subtract(global_mean).pow(2)).add(
            b_count.multiply(b_mean.subtract(global_mean).pow(2))
        )

    bss = indices.map(calc_bss)
    max_bss = ee.List(bss).reduce(ee.Reducer.max())
    max_idx = ee.List(bss).indexOf(max_bss)
    otsu_threshold = ee.Number(means.get([max_idx]))
    return otsu_threshold


def build_sar_flood_pipeline(
    year: int,
    month: int,
    orbit_pass: str = "DESCENDING",
    mmu_ha: float = 5.0,
    geojson_path: str = CANONICAL_GEOJSON_PATH
) -> Dict[str, Any]:
    """
    Constructs the Earth Engine computational graph for Sentinel-1 flood extent.
    """
    if ee is None:
        raise ImportError("earthengine-api is not installed. Install via 'pip install earthengine-api'.")

    # 1. Load Assam district boundaries
    if not os.path.exists(geojson_path):
        raise FileNotFoundError(f"Canonical districts GeoJSON not found at: {geojson_path}")

    with open(geojson_path, "r", encoding="utf-8") as f:
        geojson_data = json.load(f)

    features = []
    for feat in geojson_data["features"]:
        geom = ee.Geometry(feat["geometry"])
        props = {
            "geometry_id": feat["properties"]["geometry_id"],
            "district": feat["properties"]["district"],
            "area_km2": float(feat["properties"].get("area_km2", 0.0))
        }
        features.append(ee.Feature(geom, props))

    districts_fc = ee.FeatureCollection(features)
    assam_bounds = districts_fc.geometry().dissolve().bounds()

    # 2. Date windows
    _, last_day = calendar.monthrange(year, month)
    event_start = f"{year}-{month:02d}-01"
    event_end = f"{year}-{month:02d}-{last_day:02d}"

    # Pre-event: Jan-Feb of same calendar year
    pre_start = f"{year}-01-01"
    pre_end = f"{year}-03-01"

    # 3. Filter Sentinel-1 GRD IW VV
    s1_base = (
        ee.ImageCollection("COPERNICUS/S1_GRD")
        .filterBounds(assam_bounds)
        .filter(ee.Filter.eq("instrumentMode", "IW"))
        .filter(ee.Filter.listContains("transmitterReceiverPolarisation", "VV"))
        .filter(ee.Filter.eq("orbitProperties_pass", orbit_pass))
    )

    s1_event = s1_base.filterDate(event_start, event_end).select("VV")
    s1_pre = s1_base.filterDate(pre_start, pre_end).select("VV")

    event_scene_count = s1_event.size()
    pre_scene_count = s1_pre.size()

    # 4. Focal Median 30m Smoothing
    event_vv = s1_event.median()
    pre_vv = s1_pre.median()

    event_smooth = event_vv.focalMedian(30, "circle", "meters")
    pre_smooth = pre_vv.focalMedian(30, "circle", "meters")

    # 5. Thresholds: Fixed (-16 dB) and Otsu
    fixed_thresh = -16.0
    otsu_thresh = compute_otsu_threshold_ee(event_smooth, assam_bounds, scale=100)

    # Initial water masks
    event_water = event_smooth.lt(fixed_thresh)
    pre_water = pre_smooth.lt(fixed_thresh)

    # 6. Environmental and Terrain Masks
    # JRC surface water occurrence >= 50%
    jrc = ee.Image("JRC/GSW1_4/GlobalSurfaceWater")
    jrc_occurrence = jrc.select("occurrence").unmask(0)
    perm_water_mask = jrc_occurrence.gte(50)

    # SRTM slope < 5 deg
    srtm = ee.Image("USGS/SRTMGL1_003")
    slope = ee.Terrain.slope(srtm.select("elevation"))
    slope_mask = slope.lt(5.0)

    # MERIT Hydro HAND < 15 m
    merit = ee.Image("MERIT/Hydro/v1_0_1")
    hand = merit.select("hnd")
    hand_mask = hand.lt(15.0)

    # Combined flood condition:
    # event water AND NOT pre-event water AND NOT JRC occurrence>=50 AND slope<5 deg AND MERIT hnd<15 m
    flood_raw = (
        event_water
        .And(pre_water.Not())
        .And(perm_water_mask.Not())
        .And(slope_mask)
        .And(hand_mask)
    )

    # 7. Minimum Mapping Unit (MMU) Filter (< 5 ha)
    # 5 ha = 50,000 m2. At 30m resolution, 1 pixel = 900 m2 -> 50,000 / 900 ~= 56 pixels
    min_pixels = int(round((mmu_ha * 10000.0) / 900.0))
    connected = flood_raw.connectedPixelCount(maxPixels=min_pixels + 20, eightConnected=True)
    flood_clean = flood_raw.updateMask(connected.gte(min_pixels))

    # 8. Vector Flood Polygons (simplified to 100 m)
    flood_vectors = flood_clean.selfMask().reduceToVectors(
        geometry=assam_bounds,
        scale=30,
        geometryType="polygon",
        eightConnected=True,
        labelProperty="flood",
        maxPixels=1e9
    )
    simplified_vectors = flood_vectors.map(lambda feat: feat.simplify(maxError=100))

    # 9. Zonal Statistics per Geometry ID (G01..G33)
    pixel_area_km2 = ee.Image.pixelArea().divide(1e6)
    flood_km2_img = flood_clean.multiply(pixel_area_km2).rename("flooded_km2")
    valid_land_img = ee.Image(1).clip(districts_fc).multiply(pixel_area_km2).rename("valid_land_km2")

    stats_img = flood_km2_img.addBands(valid_land_img)
    stats_fc = stats_img.reduceRegions(
        collection=districts_fc,
        reducer=ee.Reducer.sum(),
        scale=30
    )

    return {
        "year": year,
        "month": month,
        "orbit_pass": orbit_pass,
        "mmu_ha": mmu_ha,
        "fixed_threshold_db": fixed_thresh,
        "otsu_threshold_ee": otsu_thresh,
        "event_window": (event_start, event_end),
        "pre_window": (pre_start, pre_end),
        "event_scene_count": event_scene_count,
        "pre_scene_count": pre_scene_count,
        "simplified_vectors": simplified_vectors,
        "stats_fc": stats_fc,
        "districts_fc": districts_fc
    }


def export_to_drive(pipeline_out: Dict[str, Any], folder: str = DEFAULT_DRIVE_FOLDER):
    """Start Earth Engine export tasks to Google Drive."""
    year = pipeline_out["year"]
    month = pipeline_out["month"]

    prefix_geojson = f"flood_extent_{year}_{month:02d}"
    prefix_csv = f"flood_extent_stats_{year}_{month:02d}"

    print(f"\n[GEE SAR Extent] Initiating Drive export tasks to folder: '{folder}'")
    print(f"  - Vector GeoJSON: {prefix_geojson}.geojson")
    print(f"  - Statistics CSV: {prefix_csv}.csv")

    task_geojson = ee.batch.Export.table.toDrive(
        collection=pipeline_out["simplified_vectors"],
        description=prefix_geojson,
        folder=folder,
        fileNamePrefix=prefix_geojson,
        fileFormat="GeoJSON"
    )

    task_csv = ee.batch.Export.table.toDrive(
        collection=pipeline_out["stats_fc"],
        description=prefix_csv,
        folder=folder,
        fileNamePrefix=prefix_csv,
        fileFormat="CSV"
    )

    task_geojson.start()
    task_csv.start()

    print("[GEE SAR Extent] Tasks successfully submitted to Earth Engine task queue:")
    print(f"  Task GeoJSON ID: {task_geojson.id}")
    print(f"  Task CSV ID:     {task_csv.id}")


def main():
    parser = argparse.ArgumentParser(description="Export Sentinel-1 Flood Extent using Earth Engine API.")
    parser.add_argument("--year", type=int, default=None, help="Event year (e.g., 2020)")
    parser.add_argument("--month", type=int, default=None, help="Event month (1-12, e.g., 7)")
    parser.add_argument("--drive-folder", type=str, default=DEFAULT_DRIVE_FOLDER, help="Destination Google Drive folder")
    parser.add_argument("--orbit-pass", type=str, choices=["DESCENDING", "ASCENDING"], default="DESCENDING", help="Orbit pass")
    parser.add_argument("--mmu-ha", type=float, default=5.0, help="Minimum mapping unit in hectares")
    parser.add_argument("--geojson-path", type=str, default=CANONICAL_GEOJSON_PATH, help="Path to canonical 33 districts GeoJSON")
    parser.add_argument("--dry-run", action="store_true", help="Print configuration without contacting Earth Engine")

    args = parser.parse_args()

    # Determine event window
    if args.year is None or args.month is None:
        def_yr, def_mo = determine_default_event_window()
        year = args.year or def_yr
        month = args.month or def_mo
    else:
        year = args.year
        month = args.month

    print("================================================================================")
    print("OrbitGuard: Sentinel-1 Earth Engine Flood Extent Extraction")
    print("================================================================================")
    print(f"Target Event Period : {year}-{month:02d}")
    print(f"Orbit Pass          : {args.orbit_pass} (IW VV)")
    print(f"Drive Target Folder : {args.drive_folder}")
    print(f"Minimum Mapping Unit: {args.mmu_ha} ha")
    print(f"Fixed VV Threshold  : -16.0 dB")
    print("Dynamic Threshold   : Otsu inter-class variance optimization")
    print("Terrain Filters     : SRTM slope < 5 deg, MERIT HAND < 15 m, JRC perm water < 50%")
    print("================================================================================")

    if args.dry_run:
        print("[DRY-RUN] Script configuration verified. Earth Engine not initialized.")
        return

    if ee is None:
        print("ERROR: earthengine-api is not installed.")
        print("Please run: pip install earthengine-api && earthengine authenticate")
        sys.exit(1)

    try:
        ee.Initialize()
    except Exception as exc:
        print(f"ERROR: Earth Engine initialization failed: {exc}")
        print("Please authenticate via: earthengine authenticate")
        sys.exit(1)

    pipeline_out = build_sar_flood_pipeline(
        year=year,
        month=month,
        orbit_pass=args.orbit_pass,
        mmu_ha=args.mmu_ha,
        geojson_path=args.geojson_path
    )

    try:
        otsu_val = pipeline_out["otsu_threshold_ee"].getInfo()
        print(f"Computed Otsu Threshold: {otsu_val:.2f} dB (vs fixed -16.00 dB)")
        print(f"Event Sentinel-1 Scenes: {pipeline_out['event_scene_count'].getInfo()}")
        print(f"Pre-event S1 Scenes    : {pipeline_out['pre_scene_count'].getInfo()}")
    except Exception as info_err:
        print(f"Note: Could not query threshold info synchronously: {info_err}")

    export_to_drive(pipeline_out, folder=args.drive_folder)


if __name__ == "__main__":
    main()
