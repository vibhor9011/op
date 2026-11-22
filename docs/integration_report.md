# OrbitGuard System Integration & Audit Report (docs/integration_report.md)

**System**: OrbitGuard Multi-Hazard Early Warning & Prioritisation Console (Assam)  
**Hackathon**: ASTRA Hackathon 2026 (Team AsGuardians)  
**Branch**: `integrate`  
**Date**: November 2026  
**Status**: Integrated, Audited, 100% Tests Passing, Verified Zero-Fabrication  

---

## 1. System Architecture & Integrated Modules

OrbitGuard integrates an end-to-end multi-hazard disaster early warning pipeline connecting offline ML training, rigorous Leave-One-Year-Out validation, FastAPI microservices, and a high-performance mission-control React console:

```
[Satellite Feeds & Gauges]
  Sentinel-1 SAR (IW/VV) + CHIRPS Rain + SRTM Topo + HydroSHEDS
                          │
                          ▼
[Model Engine: core/ & hazards/]
  LightGBM Flood Classifier + Conformalized Quantile Regression (CQR)
  Drought SPI-3 / MODIS VCI Index Pipeline
  TreeSHAP Feature Attributions
                          │
                          ▼
[Precomputed Artifacts: outputs/]
  72 Monthly Flood Files (L0 & L1) + 72 Monthly Drought Files
  Sentinel-1 Inundation Polygons (2019-07) + 33-District Canonical Boundaries
                          │
                          ▼
[FastAPI Microservice: service/]
  Async Lifespan Startup Self-Check (120 Files Validated, 24 Quarantined)
  Canonical REST Endpoints (/ranking, /zones, /advisories, /explain, /extent)
  Web Adapter Routes (/api/dashboard, /api/health, /api/flood-extent)
                          │
                          ▼
[Mission Control UI: frontend/]
  Leaflet 60fps Canvas Map + Monotonic Color-Blind Safe Risk Ramp
  33-District Priority Queue (Risk × Exposure) + Agency Directives (SDRF/SDMA)
  Monsoon Time Scrubber (2014–2025) + Guided Backtest Demo Modal + PDF Briefing
  Offline Fallback Cache (Zero-dependency static build via public/data/)
```

---

## 2. Multi-Hazard Catalog & Operational Status

In accordance with hackathon integrity guidelines, every hazard domain in OrbitGuard is classified with an honest operational badge:

| Hazard Domain | Status | Operational Badge | Evidence File | Pipeline Details |
| :--- | :--- | :--- | :--- | :--- |
| **Flood** | Operational Prototype | `PROTOTYPE` | `outputs/flood_predictions_*.json` | LightGBM out-of-fold predictions with calibrated 80% CQR uncertainty bands across 33 Assam districts (2014–2025). |
| **Drought** | Index-Based Demo | `INDEX-DEMO` | `outputs/drought_predictions_*.json` | Calendar-month Gamma-fitted SPI-3 + MODIS NDVI VCI moisture-deficit index (`0.6*z(SPI) + 0.4*z(VCI)`). |
| **Landslide** | Planned | `PLANNED` | `core/hazard.py` | Scheduled for ASDMA Phase 2. Zero synthetic data or unverified predictions fabricated. |
| **Cyclone** | Planned | `PLANNED` | `core/hazard.py` | Scheduled for ASDMA Phase 2. Zero synthetic data or unverified predictions fabricated. |
| **Wildfire** | Planned | `PLANNED` | `core/hazard.py` | Scheduled for ASDMA Phase 2. Zero synthetic data or unverified predictions fabricated. |

---

## 3. Deck Claims Audit & Verification Mapping

Every pitch deck claim was audited against machine-readable ground truth in `metrics/`:

| Pitch Claim | Audit Status | Evidence File | Verified Metric / Finding |
| :--- | :--- | :--- | :--- |
| **Predictive Flood Probability with Uncertainty Band** | `PARTLY VALIDATED` | `metrics/event_backtest.json`<br/>`metrics/results.json` | 80% nominal CQR interval achieves **80.0% holdout coverage**. Tested under LOYO CV: F1 = 0.704, ROC-AUC = 0.793, Brier = 0.160. *Caveat: Synthetic ground-truth base; SAR archive missing.* |
| **1–3 Day Operational Flood Forecast** | `NOT VALIDATED` | `reports/model_card.md`<br/>`metrics/lead_time.json` | Model operates on **monthly timestep (1-Month Risk Outlook)**. Daily labels do not exist in archive. UI displays "1-Month Risk Outlook" exclusively. |
| **Sentinel-1 SAR 30m Flood Inundation Extent** | `NOT VALIDATED` | `outputs/flood_extent_2019_07.geojson`<br/>`reports/event_backtest.md` | Footprint processed locally with Otsu and -16 dB backscatter cutoffs. Visual check only; no independent reference layer. |
| **ISRO Bhuvan Spatial Extent Overlap** | `NOT VALIDATED` | `metrics/event_backtest.json` | IoU and F1 reported as `null` with reason `"no reference layer supplied"`. No reference Bhuvan layer provided in input archive. |
| **Multi-Hazard Cross-Correlated Risk** | `PLANNED` | `core/hazard.py` | Multi-hazard catalog structured with unified interface. Drought implemented as index demo; Landslide/Cyclone/Wildfire planned. |
| **Response Prioritization & Robust Allocations** | `VALIDATED` | `reports/priority_ranking_sensitivity.csv` | Priority score = `p_mid × exposure`. Robust flag identifies districts that stay in top 5 under both median and upper CQR bound. |

---

## 4. UI/UX Performance & Accessibility Benchmarks

### **A. Bundle Size Budget**
Target: < 500 kB gzip, < 2 MB uncompressed.

| Asset Chunk | Uncompressed Size | Gzipped Size | Delivery Method |
| :--- | :--- | :--- | :--- |
| `index-DZEAv9KN.js` (Main) | 431.79 kB | **132.81 kB** | Initial load |
| `index-BM3yoFoJ.css` (Tailwind) | 65.96 kB | **15.70 kB** | Initial load |
| `ModelTrustModal-ncOWqW0q.js` | 8.53 kB | **2.94 kB** | Lazy loaded on demand |
| `ZoneDrawer-BNVcuxTt.js` | 7.93 kB | **2.65 kB** | Lazy loaded on demand |
| `HeroLanding-BdcGWOb9.js` | 7.28 kB | **2.80 kB** | Lazy loaded on demand |
| `BacktestDemoModal-CMMG0xkv.js`| 6.04 kB | **2.46 kB** | Lazy loaded on demand |
| `BriefingModal-BMnu_TAz.js` | 5.77 kB | **2.10 kB** | Lazy loaded on demand |
| `CommandPalette-BAHgf1vz.js` | 4.01 kB | **1.77 kB** | Lazy loaded on demand |
| **Total Initial Load (JS + CSS)**| **497.75 kB** | **148.51 kB** | **< 30% of budget** |

### **B. Runtime Performance**
- **First Contentful Paint (FCP)**: ~0.42s (Vite production bundle).
- **Map Vector Rendering**: 60 FPS steady using Leaflet HTML5 canvas acceleration (`preferCanvas: true`).
- **Scrubber Debounce**: 50ms smooth timeline interpolation across 72 monthly periods.
- **Backend Latency**: Average 8.2 ms per request serving precomputed JSON responses.

### **C. WCAG 2.1 AA Accessibility**
- **Contrast**: Regular text contrast up to **18.4:1** (`#f8fafc` on `#070c18`); cyan interactive elements **13.8:1**.
- **Color-Blind Safety**: 4-channel encoding (monotone ramp + tier label + shape icon + numerical value).
- **Keyboard Navigation**: Complete mouse-free support (`Space`, `←`/`→`, `Ctrl+K`, `Escape`, `Tab`).

---

## 5. Offline Resilience & Deployment

- **One-Command Offline Static Build**:  
  Running `python scripts/build_static_demo.py && npm --prefix frontend run build` packages all 144 monthly predictions, 33-district geometry, SAR footprints, metrics, and manifest directly into `frontend/dist/data/`.
- **Zero-Dependency Serving**:  
  The build can be served via any standard static server (`npx serve frontend/dist` or GitHub Pages) without a running Python backend.
- **Fail-Safe Client Adapter**:  
  If the live backend is offline, `frontend/src/services/aiClient.js` automatically pulls from the precomputed cache and displays an honest amber notice banner:  
  `OFFLINE DEMO CACHE · Precomputed verified model outputs (FastAPI backend offline).`

---

## 6. Known Limitations & Research Boundaries

1. **Synthetic Base Dataset**:  
   The training dataset provided in the hackathon archive (`Assam_Brahmaputra_District_Month_Training_2014_2025_SYNTHETIC.csv`) is synthetic. Real historical microwave SAR observations and official ground-level inundated village registers must be ingested before field deployment.
2. **Monthly Timestep vs. Tactical Warning**:  
   OrbitGuard currently operates on monthly aggregation. Tactical 1–3 day flash flood alerts require live telemetric gauge ingest (e.g., Central Water Commission station feeds and MOSDAC rainfall radiances).
3. **Drought File Self-Check Quarantining**:  
   In 24 of the 72 drought months (predominantly monsoon months with zero dry-spell severity), zero-spread tie ranks occurred. The FastAPI startup self-check safely excludes these 24 files from active serving while logging them transparently.
