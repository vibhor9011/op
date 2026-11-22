"""
Google Earth Engine feature extraction script.
To execute:
    earthengine authenticate
    python gee/export_flood_features.py
"""

# pyrefly: ignore[missing-import]
import sys
from IPython.core import async_helpers
# pyrefly: ignore[missing-import]
import ee
import json
import os

# Initialize Earth Engine
try:
    ee.Initialize()
except Exception as e:
    print("Earth Engine initialization failed. Run 'earthengine authenticate' first.")
    print(f"Error: {e}")
    sys.exit(1)

DRIVE_FOLDER = "OrbitGuard_Assam_GEE"

# 1. Load canonical 33 district polygons
geojson_path = os.path.join("data", "processed", "assam_districts_33.geojson")
if not os.path.exists(geojson_path):
    geojson_path = "assam_districts_33.geojson"

with open(geojson_path, "r") as f:
    geojson_data = json.load(f)

features = []
for feat in geojson_data["features"]:
    geom = ee.Geometry(feat["geometry"])
    props = {"geometry_id": feat["properties"]["geometry_id"], "district": feat["properties"]["district"]}
    features.append(ee.Feature(geom, props))

districts_fc = ee.FeatureCollection(features)
assam_bounds = districts_fc.geometry().bounds()

# Upstream Brahmaputra bounding box [91.5, 26.8, 97.5, 29.5]
upstream_bbox = ee.Geometry.BBox(91.5, 26.8, 97.5, 29.5)

# 2. Static Datasets
srtm = ee.Image("USGS/SRTMGL1_003")
elevation = srtm.select("elevation")
slope = ee.Terrain.slope(elevation)

merit = ee.Image("MERIT/Hydro/v1_0_1")
hand = merit.select("hnd")

jrc = ee.Image("JRC/GSW1_4/GlobalSurfaceWater")
occurrence = jrc.select("occurrence")

worldcover = ee.ImageCollection("ESA/WorldCover/v100").first()
cropland = worldcover.eq(40)
builtup = worldcover.eq(50)
perm_water = worldcover.eq(80).Or(occurrence.gt(80))
floodplain = hand.lt(15).And(slope.lt(5))

worldpop = ee.ImageCollection("WorldPop/GP/100m/pop").filter(ee.Filter.date("2020-01-01", "2020-12-31")).first()

# Reduce static features over 33 districts
static_image = ee.Image.cat([
    elevation.rename("elev_mean_m"),
    slope.rename("slope_mean_deg"),
    hand.rename("hand_mean_m"),
    cropland.rename("cropland_frac"),
    builtup.rename("builtup_frac"),
    floodplain.rename("floodplain_frac"),
    perm_water.rename("permwater_frac"),
    worldpop.rename("pop_2020_sum")
])

static_reduced = static_image.reduceRegions(
    collection=districts_fc,
    reducer=ee.Reducer.mean().combine(
        reducer2=ee.Reducer.sum(),
        sharedInputs=True
    ),
    scale=100
)

task_static = ee.batch.Export.table.toDrive(
    collection=static_reduced,
    description="orbitguard_static_features_33",
    folder=DRIVE_FOLDER,
    fileNamePrefix="orbitguard_static_features_33",
    fileFormat="CSV"
)
task_static.start()
print("Started Static features export task.")

# 3. CHIRPS Daily Precipitation (2013 - 2025)
chirps = ee.ImageCollection("UCSB-CHG/CHIRPS/DAILY")

for year in range(2013, 2026):
    year_features = []
    for month in range(1, 13):
        start_date = f"{year}-{month:02d}-01"
        if month == 12:
            end_date = f"{year+1}-01-01"
        else:
            end_date = f"{year}-{month+1:02d}-01"

        monthly_rain = chirps.filterDate(start_date, end_date)
        rain_total = monthly_rain.select("precipitation").sum().rename("rain_total_mm")
        rain_max1d = monthly_rain.select("precipitation").max().rename("rain_max1d_mm")
        
        # Days ge 20mm and 50mm
        days_ge20 = monthly_rain.map(lambda img: img.gte(20)).sum().rename("rain_days_ge20")
        days_ge50 = monthly_rain.map(lambda img: img.gte(50)).sum().rename("rain_days_ge50")

        # Upstream mean
        upstream_mean = rain_total.reduceRegion(
            reducer=ee.Reducer.mean(),
            geometry=upstream_bbox,
            scale=5000
        ).get("rain_total_mm")

        combined_rain = ee.Image.cat([rain_total, rain_max1d, days_ge20, days_ge50])
        
        reduced = combined_rain.reduceRegions(
            collection=districts_fc,
            reducer=ee.Reducer.mean(),
            scale=5000
        ).map(lambda f: f.set({
            "year": year,
            "month": month,
            "upstream_rain_total_mm": upstream_mean
        }))
        year_features.append(reduced)

    year_fc = ee.FeatureCollection(year_features).flatten()
    task_rain = ee.batch.Export.table.toDrive(
        collection=year_fc,
        description=f"orbitguard_chirps_rain_{year}",
        folder=DRIVE_FOLDER,
        fileNamePrefix=f"orbitguard_chirps_rain_{year}",
        fileFormat="CSV"
    )
    task_rain.start()
    print(f"Started CHIRPS export task for year {year}")

# 4. Sentinel-1 SAR GRD Flood Extent (Months 5-10, 2014-2025)
s1 = ee.ImageCollection("COPERNICUS/S1_GRD") \
    .filter(ee.Filter.listContains("transmitterReceiverPolarisation", "VV")) \
    .filter(ee.Filter.eq("instrumentMode", "IW")) \
    .filterBounds(assam_bounds)

for year in range(2014, 2026):
    s1_monthly_records = []
    for month in range(5, 11):
        start_date = f"{year}-{month:02d}-01"
        if month == 12:
            end_date = f"{year+1}-01-01"
        else:
            end_date = f"{year}-{month+1:02d}-01"

        s1_month = s1.filterDate(start_date, end_date)
        n_scenes = s1_month.size()

        # Water detection: focal median 30m, VV < -16 dB
        def detect_water(img):
            vv = img.select("VV")
            smooth = vv.focalMedian(30, "circle", "meters")
            water = smooth.lt(-16).rename("water")
            valid = smooth.isFinite().rename("valid")
            return water.addBands(valid)

        water_col = s1_month.map(detect_water)
        water_freq = water_col.select("water").mean()
        valid_freq = water_col.select("valid").mean()

        # Flooded condition: freq >= 0.33, slope < 5 deg, hand < 15m, occurrence < 50
        flood_mask = water_freq.gte(0.33) \
            .And(slope.lt(5)) \
            .And(hand.lt(15)) \
            .And(occurrence.unmask(0).lt(50))

        pixel_area_km2 = ee.Image.pixelArea().divide(1e6)
        flood_area_img = flood_mask.multiply(pixel_area_km2).rename("flood_km2")
        valid_area_img = valid_freq.gt(0).multiply(pixel_area_km2).rename("valid_obs_km2")

        reduced_s1 = ee.Image.cat([flood_area_img, valid_area_img]).reduceRegions(
            collection=districts_fc,
            reducer=ee.Reducer.sum(),
            scale=30
        ).map(lambda f: f.set({
            "year": year,
            "month": month,
            "s1_n_scenes": n_scenes,
            "s1_coverage": ee.Number(f.get("valid_obs_km2")).divide(ee.Number(f.geometry().area().divide(1e6))),
            "flood_frac_valid": ee.Number(f.get("flood_km2")).divide(ee.Number(f.get("valid_obs_km2")))
        }))
        s1_monthly_records.append(reduced_s1)

    year_s1_fc = ee.FeatureCollection(s1_monthly_records).flatten()
    task_s1 = ee.batch.Export.table.toDrive(
        collection=year_s1_fc,
        description=f"orbitguard_sentinel1_flood_{year}",
        folder=DRIVE_FOLDER,
        fileNamePrefix=f"orbitguard_sentinel1_flood_{year}",
        fileFormat="CSV"
    )
    task_s1.start()
    print(f"Started Sentinel-1 export task for year {year}")

print("\nAll export tasks submitted to Google Earth Engine!")
print(f"Monitor tasks in the GEE Task Manager or Earth Engine Python API.")
print(f"When finished, download the CSV files from Google Drive folder: '{DRIVE_FOLDER}'")
