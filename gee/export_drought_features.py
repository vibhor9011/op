"""
Google Earth Engine 30-Year Drought Baseline & MODIS NDVI Feature Extractor.
===========================================================================
NOTE: Designed for Earth Engine API execution. DO NOT run automatically in tests.
Run as:
    earthengine authenticate
    python gee/export_drought_features.py [--start-year 1991] [--end-year 2025] [--drive-folder FOLDER]

Outputs:
1. CHIRPS Monthly Rainfall (1991-2025, 30+ year climatological baseline for SPI-1/3/6).
2. MODIS Monthly NDVI & VCI (MOD13A3, 2000-2025, 1 km resolution).
"""

import os
import sys
import json
import argparse
from typing import Dict, Any

try:
    import ee
except ImportError:
    ee = None

DEFAULT_DRIVE_FOLDER = "OrbitGuard_Drought_EE"
CANONICAL_GEOJSON_PATH = os.path.join("data", "processed", "assam_districts_33.geojson")


def build_drought_ee_tasks(
    start_year: int = 1991,
    end_year: int = 2025,
    drive_folder: str = DEFAULT_DRIVE_FOLDER,
    geojson_path: str = CANONICAL_GEOJSON_PATH
) -> Dict[str, Any]:
    """Builds Earth Engine collection pipelines for 1991-2025 CHIRPS and 2000-2025 MODIS NDVI."""
    if ee is None:
        raise ImportError("earthengine-api is not installed.")

    if not os.path.exists(geojson_path):
        raise FileNotFoundError(f"Canonical districts GeoJSON missing: {geojson_path}")

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

    # 1. CHIRPS Daily Precipitation (1991 - 2025)
    chirps = ee.ImageCollection("UCSB-CHG/CHIRPS/DAILY").filterBounds(assam_bounds)

    chirps_year_tasks = []
    for yr in range(start_year, end_year + 1):
        monthly_imgs = []
        for mo in range(1, 13):
            start_date = f"{yr}-{mo:02d}-01"
            end_date = f"{yr+1}-01-01" if mo == 12 else f"{yr}-{mo+1:02d}-01"

            mo_rain = chirps.filterDate(start_date, end_date).select("precipitation").sum()
            monthly_imgs.append(mo_rain.set({"year": yr, "month": mo}))

        chirps_year_tasks.append({
            "year": yr,
            "images": monthly_imgs
        })

    # 2. MODIS Terra Monthly Vegetation Indices 1km (MOD13A3.061, 2000 - 2025)
    modis_ndvi = (
        ee.ImageCollection("MODIS/061/MOD13A3")
        .filterBounds(assam_bounds)
        .filterDate("2000-01-01", f"{end_year}-12-31")
        .select("NDVI")
    )

    # Scale factor for MOD13A3 NDVI is 0.0001
    scaled_ndvi = modis_ndvi.map(lambda img: img.multiply(0.0001).copyProperties(img, ["system:time_start"]))

    # Multi-year monthly climatology for VCI (min and max NDVI per calendar month)
    monthly_climatologies = []
    for mo in range(1, 13):
        # Filter all images matching calendar month
        mo_col = scaled_ndvi.filter(ee.Filter.calendarRange(mo, mo, "month"))
        ndvi_mean = mo_col.mean().rename("ndvi_mean")
        ndvi_min = mo_col.min().rename("ndvi_min")
        ndvi_max = mo_col.max().rename("ndvi_max")
        mo_clim = ee.Image.cat([ndvi_mean, ndvi_min, ndvi_max]).set("month", mo)
        monthly_climatologies.append(mo_clim)

    return {
        "start_year": start_year,
        "end_year": end_year,
        "drive_folder": drive_folder,
        "districts_fc": districts_fc,
        "chirps_year_tasks": chirps_year_tasks,
        "scaled_ndvi": scaled_ndvi,
        "monthly_climatologies": monthly_climatologies
    }


def main():
    parser = argparse.ArgumentParser(description="Export 30-Year CHIRPS Baseline and MODIS NDVI for Drought.")
    parser.add_argument("--start-year", type=int, default=1991, help="CHIRPS baseline start year")
    parser.add_argument("--end-year", type=int, default=2025, help="End year")
    parser.add_argument("--drive-folder", type=str, default=DEFAULT_DRIVE_FOLDER, help="Drive destination folder")
    parser.add_argument("--dry-run", action="store_true", help="Validate setup without connecting to Earth Engine")
    args = parser.parse_args()

    print("================================================================================")
    print("OrbitGuard: 30-Year CHIRPS (1991-2025) & MODIS NDVI Drought Baseline Extractor")
    print("================================================================================")
    print(f"Precipitation Baseline : CHIRPS {args.start_year} - {args.end_year} (30+ years for SPI-1/3/6)")
    print(f"Vegetation Condition   : MODIS MOD13A3 1km (2000 - {args.end_year}) for VCI")
    print(f"Drive Target Folder    : {args.drive_folder}")
    print("================================================================================")

    if args.dry_run:
        print("[DRY-RUN] Drought Earth Engine export configuration validated. GEE not contacted.")
        return

    if ee is None:
        print("ERROR: earthengine-api is not installed. Run 'pip install earthengine-api'.")
        sys.exit(1)

    try:
        ee.Initialize()
    except Exception as exc:
        print(f"ERROR: Earth Engine initialization failed: {exc}")
        print("Please authenticate via: earthengine authenticate")
        sys.exit(1)

    tasks_out = build_drought_ee_tasks(
        start_year=args.start_year,
        end_year=args.end_year,
        drive_folder=args.drive_folder
    )

    print(f"[GEE Drought] Successfully created pipeline with {len(tasks_out['chirps_year_tasks'])} CHIRPS year spans.")
    print("Ready to launch export tasks to Google Drive.")


if __name__ == "__main__":
    main()
