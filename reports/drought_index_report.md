# OrbitGuard Drought Hazard Module: Index-Based Audit

- **Module Label**: `Demo: index-based`
- **Warning String**: `DEMO: INDEX-BASED - Agricultural & Meteorological Drought Index (SPI-3 + VCI)`
- **Validation Status**: `not validated`
- **Evidence Note**: No reference dry spell list in input zip; generated 2014-2025 index timeline.

## 1. Methodology & Assumptions

- **Baseline**: 30-year monthly precipitation climatology (1991–2025).
- **Zero-Rain Handling**: H(x) = q + (1 - q) * G(x), z = norm.ppf(H(x)).
- **Zero Temporal Leakage**: Evaluated year excluded from Gamma reference period.
- **Vegetation Condition Index (VCI)**: Scaled from multi-year MODIS NDVI min-max.
- **Combined Index Weights**: `Combined index assumption: 0.6 * z(SPI-3) + 0.4 * z(VCI), weighting 3-month seasonal precipitation deficit at 60% and satellite vegetative moisture stress at 40%.`
- **Uncertainty Bounds**: Spread among SPI-1/3/6 timescales combined with 20-fold bootstrap of Gamma fit.

## 2. Statewide Severe Dry Months (2014–2025)

| Period | Mean Drought Severity | Mean p_mid | Risk Classification |
| :--- | :---: | :---: | :--- |
| 2014-09 | 1.077 | 0.6834 | Moderate |
| 2021-09 | 1.007 | 0.6628 | Moderate |
| 2018-09 | 0.893 | 0.6281 | Moderate |
| 2014-10 | 0.763 | 0.5868 | Mild |
| 2021-10 | 0.704 | 0.5677 | Mild |
| 2014-05 | 0.628 | 0.5427 | Mild |
| 2018-10 | 0.612 | 0.5374 | Mild |
| 2019-09 | 0.543 | 0.5144 | Mild |

*(Full timeline visualization saved to `reports/drought_index_timeline.png`)*
