# OrbitGuard Flood Hazard Model Card

- **Model Version**: 1.0.0 (Hackathon Prototype, Assam)
- **Hazard Category**: Riverine & Flash Inundation
- **Operational Mode**: DEGRADED MODE (Secondary synthetic verification)

---

> [!WARNING]
> **PIPELINE CHECK ONLY - NO OBSERVED-DERIVED LABELS**
> Earth Engine Sentinel-1 SAR flood observations were absent in the raw input archive.
> In accordance with strict Honesty Rules:
> - **NO headline flood metrics** are reported.
> - **NO operational flood predictions JSON** are generated for operational deployment.
> - The secondary model (M7) was executed strictly for end-to-end pipeline and interface testing on synthetic data.

## 1. Intended Use & Scope

- **Primary Purpose**: Early warning and humanitarian relief prioritization across Assam's 33 administrative districts.
- **Target Users**: Assam State Disaster Management Authority (ASDMA), NDRF, and humanitarian emergency responders.
- **Decision Support Level**: Pre-disaster stage-allocation and resource prepositioning.

## 2. Model Architecture & Pipeline Components

- **M1 Classifier**: LightGBM gradient boosted tree predicting flood threshold occurrence ($T_{cls}: \text{flood\_frac} \ge 0.02$).
- **M2 Calibration**: Nested out-of-fold Isotonic Regression mapping raw margin scores to calibrated probabilities.
- **M3 Quantile Regressors**: LightGBM quantile regression optimizing pinball loss at $\alpha \in \{0.10, 0.50, 0.90\}$.
- **M4 Conformal Prediction (CQR)**: Conformalized Quantile Regression producing valid finite-sample coverage intervals.
- **M5 Risk Tiers & Quantile Probability**: $p_{mid}$ mapped to calibrated probability; $p_{low}$ / $p_{high}$ mapped to probability that CQR lower/upper quantiles exceed the 2% threshold.
- **M6 Explainability**: Global SHAP feature importances and local per-district contribution waterfalls for top-5 high risk predictions.
- **M7 Secondary Pipeline Check**: Synthetic log-severity regressor for system-level verification.

## 3. Training & Cross-Validation Strategy

- **Evaluation Framework**: Leave-One-Year-Out (LOYO) cross-validation across all 12 monsoon seasons (2014–2025).
- **Zero Leakage**: All anomalies, percent ranks, and climatological normalizations are computed strictly inside training folds.
- **Spatial Deduplication**: Barpeta/Bajali and Baksa/Tamulpur share physical geometries; all evaluations operate at polygon level (geometry_id) to avoid double counting.

## 4. What is Explicitly NOT Validated & Known Limitations

1. **1–3 Day Lead Forecasts are NOT Validated**: The presentation deck's claim of 1–3 day early warning forecasts is NOT validated by this monthly prototype pipeline.
2. **Synthetic Data Circularity**: As demonstrated in `reports/data_audit_v2.md`, the synthetic district-month population figures are a constant ~91-96% fraction of official state anchors every year, proving they were derived top-down. Validating synthetic models against official anchors is circular.
3. **Synthetic Flag Imbalance**: The synthetic `flood_affected_status` flag has an active rate of 93.37%. An all-ones model trivially achieves 93.37% accuracy, rendering this flag unsuitable as a target.
4. **Satellite-Derived Labels**: Sentinel-1 SAR observations represent satellite-detected surface water extent, NOT ground-truth damage or flood victim counts.
5. **Vegetation & SAR Penetration Limits**: C-band SAR (Sentinel-1) suffers from signal attenuation and under-detection in densely vegetated or forested floodplains.
6. **Boundary Vintage & Proxy Districts**: 2016-vintage boundaries require Bajali to proxy to Barpeta and Tamulpur to Baksa.
7. **CHIRPS vs. INSAT**: CHIRPS precipitation has a 1–2 day latency and coarse 0.05-degree resolution, unlike operational real-time INSAT geostationary radar feeds.
8. **12-Year Span**: A 12-year historical sample (2014–2025) provides limited statistical power for extreme 100-year return period hydrologic anomalies.

## 5. Secondary Synthetic Model Verification Metrics (M7)

- **Cross-Validation**: Leave-One-Year-Out (2014-2025, 12 folds)
- **Out-of-Fold RMSE**: `2.6312`
- **Out-of-Fold MAE**: `1.7587`
- **Out-of-Fold R²**: `-0.0774`

*(Verification scatter plot saved to `reports/m7_synthetic_loyo_evaluation.png`)*
