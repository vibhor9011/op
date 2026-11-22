# OrbitGuard: Operational Limitations, Defensibility & Next Steps Roadmap

> **Author**: OrbitGuard Engineering & Applied Science Team  
> **Status**: Technical Reference & Operational Roadmap  
> **Target Audience**: Disaster Management Authorities (ASDMA / NDMA / CWC), Technical Judges, and Research Collaborators

---

## 1. Executive Summary

OrbitGuard is designed around an unwavering principle of **Methodological Honesty**. In early warning systems, uncalibrated overclaims cost lives and destroy trust with incident commanders. This document outlines the explicit operational boundaries of the current prototype and details the architectural roadmap for transitioning from hackathon verification to operational deployment in Assam's District Emergency Operations Centers (DEOCs).

---

## 2. Six Core Operational Limitations & Strategic Next Steps

### 2.1 Daily Labels & 1–3 Day Operational Warnings

#### The Current Limitation
- The historical training records available in the prototype operate strictly at **monthly aggregation** (monsoon months May through October, 2014–2025).
- Daily flood inundation labels do not exist in the training archive. Consequently, any claim of a validated "1–3 day operational forecast" on this dataset is mathematically impossible without label fabrication.
- At monthly resolution, OrbitGuard validates a **1-month-ahead outlook**, successfully flagging **84.29%** (295 of 350) of flooded polygon-months in out-of-fold historical backtests.

#### The Next Step: Transition to Daily Horizon
1. **Dynamic Daily Slicing**: OrbitGuard's lag engine (`core/ingest.py`) is already engineered to compute rolling windows (3-day maximum precipitation, 7-day cumulative rainfall).
2. **CWC Stage Feeds**: Integrate Central Water Commission (CWC) daily river gauge stations along the Brahmaputra (e.g. Dibrugarh, Tezpur, Guwahati, Goalpara, Dhubri) as daily hydraulic boundary conditions.
3. **Daily Inundation Tracking**: Ingest daily MODIS/VIIRS NRT flood water fraction products alongside Sentinel-1 passes to supervise daily transition probabilities ($t-1 \to t+1, t+2, t+3$).

---

### 2.2 Official District-Level Ground Truth & Synthetic Circularity

#### The Current Limitation
- As audited in `reports/data_audit_v2.md`, the synthetic district-month affected population in the input archive tracks the official statewide annual disaster anchors at a near-constant ratio of **0.911 to 0.960** every single year.
- This constancy proves that the synthetic dataset was derived top-down from the anchors. Validating an ML model trained on synthetic data against those same anchors is mathematically circular.
- Furthermore, the synthetic binary flood flag exhibits a **93.37% positive rate**, rendering raw accuracy metrics meaningless.

#### The Next Step: Direct ASDMA / DDMA Integration
1. **DEOC Daily Flood Situation Reports**: Digitize ASDMA's daily Flood Situation Reports (SITREPs), which report revenue circle-level inundated villages, crop damage hectares, and relief camp enrollments.
2. **Independent Ground Truth Repository**: Replace synthetic target allocations with empirical circle-level data, breaking the circular link to statewide anchors.
3. **Partitioned Evaluation**: Maintain a permanent holdout of ground-truth field records strictly isolated from feature engineering.

---

### 2.3 Satellite Sourcing: Open Data vs. ISRO MOSDAC / INSAT Swap-In

#### The Current Limitation
- The prototype currently runs on open global satellite feeds: CHIRPS (0.05° resolution precipitation) and ERA5/GPM-equivalent variables.
- Direct API integration with ISRO's Meteorological and Oceanographic Satellite Data Archival Centre (MOSDAC) was not active within the sandbox environment.

#### The Next Step: Zero-Code MOSDAC Connector
1. **INSAT-3D / 3DR Imager**: Connect the MOSDAC API to ingest 30-minute Hydro-Estimator precipitation rain rates and cloud-top brightness temperatures.
2. **Standardized Sensor Interface**: The `BaseHazardModel` feature extraction interface (`core/hazard.py`) abstracts the sensor source. Swapping CHIRPS for INSAT-3DR requires updating only the geospatial raster parser; the downstream feature engineering, calibration, and ranking pipelines remain 100% identical.
3. **Kalpana-1 Reanalysis**: Ingest 2002–2015 historical Indian geostationary archives to extend the local climatological baseline to 25+ years.

---

### 2.4 Uncertainty Quantification: Conformal Quantile Regression to Bayesian BNNs

#### The Current Limitation
- OrbitGuard currently quantifies uncertainty using LightGBM pinball loss quantile regressors ($\alpha \in \{0.10, 0.50, 0.90\}$) calibrated via **Split Conformalized Quantile Regression (CQR)**.
- While CQR provides distribution-free, finite-sample coverage guarantees (achieving **90.7% empirical coverage** on held-out test data), it estimates aleatoric uncertainty from residuals rather than maintaining an explicit distribution over model weights.

#### The Next Step: Variational Bayesian Neural Network
1. **Epistemic Uncertainty Separation**: Implement a Bayesian Neural Network (BNN) with Monte Carlo Dropout or Variational Inference to explicitly separate data noise (aleatoric) from lack of knowledge during extreme out-of-distribution monsoons (epistemic).
2. **Hybrid Conformal Bayes**: Wrap the BNN predictive posterior in conformal prediction intervals, combining the Bayesian posterior distribution with finite-sample frequentist coverage guarantees.
3. **Risk Communication**: Directly communicate epistemic uncertainty to ASDMA directors: *"Model uncertainty is high because this rainfall pattern has never been observed in the 30-year record."*

---

### 2.5 Multi-Hazard Architecture Expansion

#### The Current State
- **Flood Module**: Fully implemented (LightGBM classifier, isotonic calibration, quantile regression, CQR, SHAP attributions, exposure ranking).
- **Drought Module**: Functional demo implemented (`hazards/drought.py`, `Demo: index-based`) using SPI-1/3/6 and MODIS VCI with shared exposure ranking.
- **Landslide & Heatwave**: Defined as abstract polymorphic interfaces under `BaseHazardModel`.

#### The Next Step: Landslide and Heatwave Modules
1. **Rainfall-Induced Landslide Hazard**:
   - Target Regions: Karbi Anglong, Dima Hasao, and Cachar hill districts.
   - Features: MERIT Hydro slope gradient, curvature, geological lithology, and the Antecedent Rainfall Index (ARI) over 3, 7, and 14 days.
   - Interface: Inherits `BaseHazardModel` and outputs $[p_{\text{low}}, p_{\text{mid}}, p_{\text{high}}]$ into the same `/ranking` endpoint.
2. **Extreme Heat & Humidity (Wet-Bulb Temperature)**:
   - Target Regions: Urban centers (Guwahati Metropolitan, Silchar, Dibrugarh).
   - Features: MODIS/VIIRS Land Surface Temperature (LST), IMD relative humidity, and simplified wet-bulb temperature ($T_w$) exceedance.
   - Priority: Multiplied by population density and built-up fraction for cooling center prioritization.

---

### 2.6 Orbital Sensor Module: The Multi-Constellation Roadmap

#### The Current State
- Sentinel-1 C-band Synthetic Aperture Radar (SAR) with a 6-to-12 day revisit period.
- Pipeline contains complete cloud-native Earth Engine extraction (`sar/export_extent_ee.py`) and local post-processing (`sar/extent.py`), with offline vector proxy demonstrated for July 2019.

#### The Next Step: Multi-Constellation Radar Fusion
1. **NISAR Integration (NASA-ISRO SAR)**:
   - NISAR's dual L-band (24 cm) and S-band (12 cm) polarimetric radar will penetrate dense tree canopies in Assam's flooded riparian forests, where C-band backscatter saturates.
   - Joint 12-day repeat orbit combined with Sentinel-1 will slash radar revisit intervals over the Brahmaputra valley to 3–4 days.
2. **Optical Gap Filling (Sentinel-2 & PlanetScope)**:
   - Automated cloud masking using s2cloudless.
   - When cloud breaks occur, high-resolution optical imagery (3m PlanetScope / 10m Sentinel-2 MNDWI) immediately supplements radar footprints.
3. **Micro-SAR Constellations (Capella / Umbra / ICEYE)**:
   - Commercial tasking API hook for sub-meter flood breach inspection on critical Brahmaputra embankments during active disaster declarations.

---

## 3. Operational Integration Summary

```
                      [ Raw Earth Observation & Gauge Data ]
                                         │
                 ┌───────────────────────┴───────────────────────┐
                 ▼                                               ▼
     [ Sentinel-1 & NISAR SAR ]                     [ IMD / CWC / MOSDAC ]
     Cloud-penetrating 30m Water                     Daily Rain & River Stage
                 │                                               │
                 └───────────────────────┬───────────────────────┘
                                         ▼
                        [ OrbitGuard Multi-Hazard Core ]
                             - Strict In-Fold Isolation
                             - Conformal Quantile Bounds
                             - Shared Response Prioritization
                                         │
                 ┌───────────────────────┴───────────────────────┐
                 ▼                                               ▼
     [ FastAPI REST Service ]                      [ ASDMA DEOC GIS Portal ]
      Precomputed JSON & GeoJSON                    Interactive Map & Alert Feeds
                 │                                               │
                 └───────────────────────┬───────────────────────┘
                                         ▼
                        [ Operational Decision Support ]
                         - Robust High-Priority Zones
                         - Boat & SDRF Pre-Positioning
                         - ASDMA Official Disclaimer
```

By maintaining methodological honesty, publishing exact empirical bounds, and designing polymorphic hazard interfaces, OrbitGuard bridges the gap between academic machine learning and real-world disaster management.
