# OrbitGuard Phase Z: Intake & Data Classification Report

- **Primary Archive Source**: `C:\Users\HARSHVARDHAN\Desktop\Aastra Hackathon\OrbitGuard\orbitguard_flood_data.zip`
- **Extraction Destination**: `data\raw\_unzipped`
- **XLSX Fallback Activated**: No

## 1. Content-Based Classification Inventory

| Category | Found Count | File Path(s) | Status |
|---|---|---|---|
| synthetic_base_csv | 1 | `Assam_Brahmaputra_District_Month_Training_2014_2025_SYNTHETIC.csv` | Available |
| official_anchors_csv | 1 | `Assam_Official_Annual_Flood_Anchors_2014_2025.csv` | Available |
| xlsx_workbook | 1 | `Assam_Flood_Training_Dataset_2014_2025.xlsx` | Available |
| district_geojson_geometry_id | 0 | None | Missing |
| district_geojson_raw | 1 | `assam_raw_districts.geojson` | Available |
| ee_rain_csv | 0 | None | Missing |
| ee_flood_csv | 0 | None | Missing |
| ee_static_csv | 0 | None | Missing |
| extension_label | 0 | None | Missing |

## 2. Hard Gates & Operational Assessment

- **Earth Engine Rain CSV**: ABSENT (Degraded Mode Active)
- **Earth Engine Flood CSV**: ABSENT (Degraded Mode Active)
- **Earth Engine Static CSV**: ABSENT (Degraded Mode Active)
- **Synthetic Base Dataset**: Valid (35 districts x 6 months x 12 years)
- **Official Annual Anchors**: Valid (2014-2025)
- **District Boundary GeoJSON**: Available (33 districts)

## 3. Unrecognised Files

- None. All files identified and classified.

## 4. Pipeline Execution Mode Decision

> [!WARNING]
> **DEGRADED MODE ACTIVATED**: Earth Engine Sentinel-1 SAR flood observations are absent in raw input archive.
> Operating in **Degraded Mode**: Executing secondary synthetic pipeline (M7) for full end-to-end pipeline verification.
> Headline metrics and observed SAR predictions are omitted per Honesty Rules.