# OrbitGuard Early Warning & Response Prioritisation Service

FastAPI-powered REST API serving precomputed flood hazard forecasts, conformalized uncertainty bounds, response prioritization rankings, and rule-based operational advisories for Assam's 33 districts.

> [!IMPORTANT]
> **Strict Precomputed Constraint**: This service serves **ONLY** precomputed artifacts from `outputs/`, `metrics/`, and `reports/`. It **NEVER** runs machine learning models or feature engineering live during HTTP request lifecycles.
>
> Every response strictly embeds `label_source` and the operational `warning` string.

---

## 1. Quick Start

### Start the Service Locally
```bash
# Using uvicorn on port 8000
uvicorn service.app:app --host 0.0.0.0 --port 8000 --reload
```

### Interactive Documentation
- **Interactive Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc Documentation**: [http://localhost:8000/redoc](http://localhost:8000/redoc)
- **OpenAPI JSON Schema**: [http://localhost:8000/openapi.json](http://localhost:8000/openapi.json)

---

## 2. API Endpoints & `curl` Examples

### 1. Health Check (`GET /health`)
Check service health, deployment version, and label family.
```bash
curl -X GET "http://localhost:8000/health" -H "Accept: application/json"
```
**Sample Response**:
```json
{
  "status": "healthy",
  "service": "orbitguard-early-warning-service",
  "version": "1.0.0",
  "timestamp": "2026-11-22T01:45:00.000000+00:00",
  "label_source": "synthetic_augmentation",
  "warning": "PIPELINE CHECK ONLY - no observed-derived labels"
}
```

---

### 2. Hazard Catalog (`GET /hazards`)
List all multi-hazard domains and operational capabilities.
```bash
curl -X GET "http://localhost:8000/hazards" -H "Accept: application/json"
```
**Sample Response**:
```json
{
  "hazards": [
    {
      "id": "flood",
      "name": "Riverine & Flash Inundation",
      "description": "Multi-hazard early warning and response prioritization for Assam (33 canonical districts)",
      "granularity": "month",
      "lead_times": ["0_month", "1_month"],
      "spatial_units": 33
    },
    {
      "id": "drought",
      "name": "Agricultural & Meteorological Drought",
      "description": "Index-based drought severity and vulnerability prioritization using SPI-1/3/6 and MODIS VCI (Demo: index-based)",
      "granularity": "month",
      "lead_times": ["0_month", "1_month"],
      "spatial_units": 33
    }
  ],
  "label_source": "synthetic_augmentation",
  "warning": "PIPELINE CHECK ONLY - no observed-derived labels"
}
```

---

### 3. Available Forecast Periods (`GET /periods`)
List all precomputed monthly forecast periods for a hazard domain (`flood` or `drought`).
```bash
# Query flood periods
curl -X GET "http://localhost:8000/periods?hazard=flood" -H "Accept: application/json"

# Query drought periods (all 72 precomputed monthly periods 2014-2025)
curl -X GET "http://localhost:8000/periods?hazard=drought" -H "Accept: application/json"
```
**Sample Response**:
```json
{
  "hazard": "flood",
  "periods": [
    "2014-05", "2014-06", "...", "2019-07", "2020-07", "2022-06", "2025-10"
  ],
  "label_source": "synthetic_augmentation",
  "warning": "PIPELINE CHECK ONLY - no observed-derived labels"
}
```

---

### 4. District Zones & Early Warning Advisories (`GET /zones`)
Retrieve all 33 districts with conformal prediction intervals ($p_{\text{low}} \le p_{\text{mid}} \le p_{\text{high}}$), exposure scores, priority ranks, and rule-based advisories.
```bash
curl -X GET "http://localhost:8000/zones?hazard=flood&period=2022-06&lead=1_month" -H "Accept: application/json"
```
**Sample Response**:
```json
{
  "hazard": "flood",
  "granularity": "month",
  "period": "2022-06",
  "lead": "1_month",
  "zones": [
    {
      "id": "G09",
      "name": "Dhemaji",
      "p_low": 0.0728,
      "p_mid": 0.0970,
      "p_high": 0.1212,
      "exposure": 0.5140,
      "priority": 0.0499,
      "rank": 1,
      "robust": true,
      "drivers": {
        "rain_total_mm": 531.3,
        "rain_cum3m_mm": 1487.6,
        "rain_anom_mm": 51.3
      },
      "observed_flood_km2": 233.05,
      "observed_flood_frac": 0.097,
      "advisory": {
        "level": "Severe",
        "headline": "CRITICAL FLOOD ALERT: Severe inundation threat across Dhemaji (p_mid: 9.7%)",
        "reasons": [
          "Sustained 3-month cumulative rainfall (1488 mm) saturated local soils.",
          "Monthly rainfall (531 mm) creates acute surface ponding risk.",
          "Monsoon rainfall anomaly of +51 mm above historical median."
        ],
        "recommended_actions": [
          "Pre-position boats and SDRF teams for immediate deployment",
          "Open relief camps and stage dry rations, drinking water, and medical kits",
          "Initiate precautionary evacuation of low-lying riverine settlements",
          "Inspect and reinforce vulnerable embankments and critical breach points"
        ],
        "confidence": "High (tight predictive band: ±2.4%)",
        "disclaimer": "Decision support only; confirm with ASDMA/IMD official advisories."
      }
    }
  ],
  "label_source": "synthetic_augmentation",
  "warning": "PIPELINE CHECK ONLY - no observed-derived labels"
}
```

---

### 5. Response Prioritisation Ranking (`GET /ranking`)
Sorted statewide ranking for emergency response resource allocation, including robust high-priority flags.
```bash
curl -X GET "http://localhost:8000/ranking?hazard=flood&period=2022-06&lead=1_month" -H "Accept: application/json"
```
**Sample Response**:
```json
{
  "hazard": "flood",
  "period": "2022-06",
  "lead": "1_month",
  "ranking": [ ... 33 districts sorted by priority descending ... ],
  "top_5_robust": ["Dhemaji", "Dhubri", "Bajali", "Tinsukia", "Baksa"],
  "label_source": "synthetic_augmentation",
  "warning": "PIPELINE CHECK ONLY - no observed-derived labels"
}
```

---

### 6. Explainability & SHAP Drivers (`GET /explain/{zone_id}`)
Retrieve the top 5 predictive SHAP drivers with quantitative importance and human-readable plain language explanations.
```bash
curl -X GET "http://localhost:8000/explain/G01?period=2022-06" -H "Accept: application/json"
```
**Sample Response**:
```json
{
  "zone_id": "G01",
  "district": "Baksa",
  "period": "2022-06",
  "top_drivers": [
    {
      "feature": "rain_cum3m_mm",
      "importance": 0.499,
      "value": 1490.0,
      "plain_language": "Cumulative 3-month rainfall was 1490 mm, elevating soil saturation across Baksa."
    },
    {
      "feature": "rain_total_mm",
      "importance": 0.339,
      "value": 532.0,
      "plain_language": "Monthly rainfall total of 532 mm exceeded local channel conveyance capacity."
    },
    {
      "feature": "floodplain_frac",
      "importance": 0.220,
      "value": 0.42,
      "plain_language": "Low-elevation Brahmaputra floodplain terrain (HAND < 15 m) impedes gravity drainage."
    },
    {
      "feature": "rain_anom_mm",
      "importance": 0.176,
      "value": 52.0,
      "plain_language": "Rainfall anomaly was +52 mm compared to the historical climatological normal."
    },
    {
      "feature": "upstream_rain_lag1_mm",
      "importance": 0.120,
      "value": 425.6,
      "plain_language": "Transboundary upstream runoff inflow from the upper Brahmaputra catchment."
    }
  ],
  "label_source": "synthetic_augmentation",
  "warning": "PIPELINE CHECK ONLY - no observed-derived labels"
}
```

---

### 7. Satellite Flood Extent GeoJSON (`GET /extent`)
Serves precomputed Sentinel-1 SAR flood extent polygon vectors. Returns **HTTP 404** if not precomputed.
```bash
# Existing extent
curl -X GET "http://localhost:8000/extent?period=2019-07" -H "Accept: application/json"

# Missing extent (returns 404 with error payload)
curl -X GET "http://localhost:8000/extent?period=1999-01" -H "Accept: application/json"
```
**Sample 404 Response**:
```json
{
  "detail": "Flood extent GeoJSON not found for period 1999-01. Run GEE extraction to generate footprint.",
  "label_source": "synthetic_augmentation",
  "warning": "PIPELINE CHECK ONLY - no observed-derived labels"
}
```

---

### 8. Verification Metrics & Claims Table (`GET /metrics`)
Returns out-of-fold validation metrics, historical backtests (2019, 2020, 2022), and pitch deck claims audits.
```bash
curl -X GET "http://localhost:8000/metrics" -H "Accept: application/json"
```

---

### 9. Provenance & Audit Facts (`GET /provenance`)
Complete dataset audit facts, synthetic circularity findings, and operational caveats.
```bash
curl -X GET "http://localhost:8000/provenance" -H "Accept: application/json"
```

---

## 3. Advisory Generator Rules (`core/advisory.py`)

Advisories are generated via strict, deterministic rule-based logic (no LLMs):

1. **Alert Levels**:
   - **Severe**: Triggered **only** if lower bound also exceeds threshold ($p_{\text{low}} \ge 0.05$).
   - **Warning**: Triggered if mid probability exceeds threshold ($p_{\text{mid}} \ge 0.05$).
   - **Watch**: Triggered if upper bound exceeds threshold ($p_{\text{high}} \ge 0.05$).
   - **Normal**: None exceed threshold.
2. **Confidence**:
   - $W = p_{\text{high}} - p_{\text{low}}$
   - High: $W \le 0.08$
   - Medium: $0.08 < W \le 0.18$
   - Low: $W > 0.18$
3. **Editable Actions**: Loaded from [core/advisory_actions.yaml](file:///c:/Users/HARSHVARDHAN/Desktop/Aastra%20Hackathon/OrbitGuard/core/advisory_actions.yaml).
4. **Mandatory Disclaimer**: Every advisory strictly includes:
   `"Decision support only; confirm with ASDMA/IMD official advisories."`
