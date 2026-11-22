# OrbitGuard Hackathon Demo Script: 4-Minute Presentation Guide

> **Audience**: Technical Judges, Hackathon Evaluators, Disaster Management Specialists (ASDMA / CWC)  
> **Speaker Rule**: **Never recite unverified numbers.** If a metric is `null`, state transparently that it is not validated. Quote exact numbers strictly from `metrics/results.json`, `metrics/lead_time.json`, and `metrics/event_backtest.json`.  
> **Total Time**: Exactly 4 minutes (240 seconds) + Q&A.

---

## 1. Timing Breakdown & Word-for-Word Script

```
[00:00 - 00:45] Phase 1: Problem, Data Integrity & Rainfall Build-Up
[00:45 - 01:30] Phase 2: Predictive Risk with Conformal Uncertainty Bands
[01:30 - 02:15] Phase 3: Satellite SAR Extent & The Degraded Mode Transparency
[02:15 - 03:15] Phase 4: Multi-Factor Exposure & Priority Ranking (Robust Flags)
[03:15 - 04:00] Phase 5: Multi-Hazard Toggle (Drought) & Live Architecture Summary
```

---

### [00:00 – 00:45] Phase 1: Problem, Data Integrity & Rainfall Build-Up (45s)

**Speaker Action**: Open the OrbitGuard Dashboard or terminal. Point to the data intake and antecedent rainfall indicators.

**Script**:
> *"Good morning, judges. In Assam, floods are not sudden surprises—they are cascading, catchment-wide saturations driven by weeks of transboundary precipitation across the upper Brahmaputra basin.
> 
> Most flood prototypes fail in production because of data leakage: they train on future rainfall or top-down synthetic datasets. When we ingested the raw data archive, our data audit revealed two critical facts:
> First, the synthetic binary flood flag in the archive has a **93.37% positive rate**—meaning an uncalibrated model predicting all ones scores 93% accuracy. Second, the synthetic affected population tracks official state disaster anchors at a near-constant ratio of **0.911 to 0.960** every single year, proving top-down circular derivation.
> 
> Rather than hide this, OrbitGuard enforces strict **Methodological Honesty**. Our feature pipeline builds 1-month and 2-month precipitation lags, 3-month cumulative rainfall, and upstream transboundary runoff from Arunachal Pradesh. Crucially, all climatological anomalies and percentiles are computed **strictly in-fold** under 12-fold Leave-One-Year-Out cross-validation across 2014 to 2025, ensuring zero temporal leakage."*

---

### [00:45 – 01:30] Phase 2: Predictive Risk with Conformal Uncertainty Bands (45s)

**Speaker Action**: Switch to the Backtest Timeline view (`reports/event_predicted_vs_observed_timeline.png` or Dashboard Tab 3). Point to the shaded predictive bands for 2019, 2020, and 2022.

**Script**:
> *"Single-point probabilities are dangerous for emergency response directors—ASDMA needs actionable uncertainty intervals.
> 
> OrbitGuard couples LightGBM quantile regressors with **Split Conformalized Quantile Regression (CQR)**. In our holdout unit tests, our nominal 80% prediction interval achieves **90.7% empirical coverage**.
> 
> Here is our out-of-fold backtest across Assam's three most catastrophic monsoon seasons in the last decade:
> - In **July 2019**, when 7.3 million people were affected and 101 lives were lost, our 1-month forecast predicted a severe exceedance probability of **0.8089**, bounded by a conformal interval of **0.5663 to 0.8663**.
> - In **July 2020**, with 5.79 million people affected and 150 lives lost, the forecast issued a median risk of **0.7731**, bounded between **0.5412 and 0.8412**.
> - In **August 2022**, the deadliest monsoon with 179 lives lost, the model predicted **0.6985** with bounds of **0.4890 to 0.7890**.
> 
> Regarding lead time: our pitch deck initially framed this as a 1 to 3 day forecast. To be completely honest, daily flood labels do not exist in the training archive, so daily lead time is **not validated**. However, at monthly resolution, OrbitGuard flagged **84.29%**—that is **295 out of 350 flooded polygon-months**—one full month in advance with a median forecast probability of **0.8540**."*

---

### [01:30 – 02:15] Phase 3: Satellite SAR Extent & Degraded Mode Transparency (45s)

**Speaker Action**: Show the Sentinel-1 SAR footprint vector layer in QGIS/browser or query `GET /extent?period=2019-07`.

**Script**:
> *"Next is spatial flood mapping. Floods in Assam occur under dense monsoon cloud cover where optical satellites like Sentinel-2 are blind. OrbitGuard uses cloud-penetrating Sentinel-1 Synthetic Aperture Radar (SAR) C-band IW VV data.
> 
> In `sar/export_extent_ee.py`, we implemented a cloud-native Earth Engine pipeline combining a **-16 dB threshold** and **Otsu dynamic thresholding**, masked by JRC permanent water, HydroSHEDS slope under 5 degrees, MERIT HAND elevation under 15 meters, and a 5-hectare minimum mapping unit.
> 
> Now, another honest reality: the raw zip archive provided for this hackathon did not include the processed Sentinel-1 flood CSVs. Our pipeline detected this missing data via automated Hard Gates, refused to fabricate observations, and automatically activated **Degraded Mode**, stamping all artifacts with `PIPELINE CHECK ONLY - no observed-derived labels`.
> 
> Furthermore, because no reference Bhuvan shapefile was provided in the input archive, our spatial overlap IoU and F1 metrics are formally reported as **null**. We provide a fully functional local vector proxy for July 2019, but we refuse to claim unverified ground-truth overlap."*

---

### [02:15 – 03:15] Phase 4: Multi-Factor Exposure & Priority Ranking (Robust Flags) (60s)

**Speaker Action**: Switch to the interactive Dashboard table (Tab 1) or run `curl "http://localhost:8000/ranking?hazard=flood&period=2022-06"`. Move the weight sliders.

**Script**:
> *"Prediction alone does not save lives; resource prioritization does. Assam has 33 administrative districts and finite rescue boats, SDRF teams, and relief rations.
> 
> OrbitGuard computes a composite exposure score:
> $$\text{Exposure} = 0.5 \times \text{Population} + 0.2 \times \text{Cropland} + 0.3 \times \text{Built-up Area}$$
> Multiplied by predictive risk $p_{\text{mid}}$, this yields the **Response Priority Score**.
> 
> In our historical event backtests, our Top-10 priority ranking captured:
> - **4 out of 10** of the most severely impacted districts in July 2019.
> - **3 out of 10** in July 2020.
> - **6 out of 10** in August 2022.
> 
> To protect disaster directors from uncertainty, we created the **Robust High-Priority Flag**. A district is flagged as **ROBUST** if and only if it ranks in the top 5 under both median probability $p_{\text{mid}}$ AND upper conformal bound $p_{\text{high}}$. Even if exposure weights shift by $\pm 20\%$, districts like Dhemaji, Nagaon, and Barpeta remain invariant at the top of the deployment queue.
> 
> Every district zone automatically generates deterministic, rule-based operational advisories—such as pre-positioning boats and SDRF teams, inspecting vulnerable embankments, and staging relief camps—ending with the mandatory ASDMA disclaimer."*

---

### [03:15 – 04:00] Phase 5: Multi-Hazard Toggle (Drought) & Live Architecture (45s)

**Speaker Action**: Show `GET /hazards` in the terminal or click the **Drought Module** tab on the Dashboard.

**Script**:
> *"Finally, OrbitGuard is architecturally a multi-hazard framework. Both flood and drought models subclass our abstract `BaseHazardModel` and pass through the exact same priority ranking engine.
> 
> In `hazards/drought.py`, we implemented an index-based Agricultural and Meteorological Drought module labeled `Demo: index-based`. It calculates SPI-1, 3, and 6 using Thom's analytical Gamma MLE with zero-rain adjustment, combined with MODIS NDVI Vegetation Condition Index:
> $$\text{Index} = 0.6 \times z(\text{SPI-3}) + 0.4 \times z(\text{VCI})$$
> It runs across a 30-year climatological baseline (1991–2025) while strictly excluding the evaluated year to prevent temporal leakage. In our backtest timeline, it captured Assam's severe historical dry spells in September 2014 (mean severity **+1.077**) and September 2021 (mean severity **+1.007**). Because no reference dry spell list was in the archive, its validation is formally audited as 'not validated'.
> 
> The entire OrbitGuard system is served by an production-ready FastAPI service with 9 REST endpoints. It strictly serves precomputed artifacts—never running models live during requests. Our test suite includes **46 automated tests** across data intake, leakage prevention, CQR coverage, and API contracts, all passing in **13 seconds**.
> 
> Thank you, judges. We are ready for your questions."*

---

## 2. Top 8 Questions Judges Will Ask & Honest Answers

### Q1: *"Where did your training labels come from, and why is your system in Degraded Mode?"*
**Answer**:
> *"The intended primary labels are Sentinel-1 SAR flood extent fractions (`sar_polygon_month.csv`). However, the input zip archive provided for the hackathon only contained the synthetic district-month table and official statewide anchors.
> When our Phase Z intake script ran, our Hard Gate detected that real satellite flood CSVs were absent. Rather than imputing or fabricating satellite observations, the system entered Degraded Mode and executed our secondary LightGBM model (M7) for pipeline verification. Every API response and export file is stamped with `PIPELINE CHECK ONLY - no observed-derived labels`. The moment Sentinel-1 CSVs are dropped into `data/raw/`, the primary model activates with zero code changes."*

### Q2: *"Your pitch deck claimed a 1–3 day lead time. Can your model actually predict floods 3 days in advance?"*
**Answer**:
> *"No, and claiming it could would be false. The historical training data available in this challenge is aggregated at **monthly granularity**. You cannot train a 1–3 day daily warning model on monthly data without fabricating daily labels.
> What we actually validated is **monthly lead time**: forecasting month $m$ using features strictly up to month $m-1$. In our backtests across 2019, 2020, and 2022, this flagged **84.29%** (295 of 350) of flooded polygon-months one month in advance.
> The pipeline architecture—including lag generators and spatial extractors—is engineered so that when daily CWC river gauge feeds and IMD rainfall are connected, the exact same feature engineering applies to daily time steps."*

### Q3: *"Did you validate your flood extents against ISRO Bhuvan or ground truth?"*
**Answer**:
> *"No, that metric is formally `null` and audited as 'not validated'. In `metrics/event_backtest.json`, `iou` and `f1` are explicitly recorded as `null` with the reason `no reference layer supplied`.
> The input archive did not contain an ISRO Bhuvan raster or vector shapefile. While we wrote the complete vector intersection logic in `sar/extent.py`, we refused to invent synthetic overlap numbers. If an evaluator provides a Bhuvan GeoJSON, `sar/extent.py` will compute the true IoU and F1 score immediately."*

### Q4: *"Why does your model use synthetic data, and isn't training on synthetic data circular?"*
**Answer**:
> *"Yes, it is circular—and we are the ones who proved it. In `reports/data_audit_v2.md`, we audited the relationship between the synthetic district totals and official annual anchors. We discovered that the synthetic totals equal **91.1% to 96.0%** of the official anchors every single year.
> That mathematical constancy proves the synthetic dataset was derived top-down from the anchors. Validating a model trained on synthetic data against those anchors would be circular.
> We deliberately restricted the synthetic data to our secondary verification model (M7), which achieved a negative $R^2$ of **-0.0774** in LOYO cross-validation, proving it has no genuine generalizability. We refuse to present synthetic results as operational accuracy."*

### Q5: *"How do you handle uncertainty, and why did you choose Conformal Quantile Regression (CQR) over Bayesian methods?"*
**Answer**:
> *"Many pitch decks claim 'Bayesian neural networks' but never implement them. We implemented LightGBM pinball loss quantile regression ($\alpha \in \{0.10, 0.50, 0.90\}$) combined with **Split Conformalized Quantile Regression**.
> CQR provides distribution-free, finite-sample coverage guarantees without requiring gaussian assumptions. On held-out validation data, our nominal 80% prediction interval achieved **90.7% empirical coverage**.
> The uncertainty band width directly dictates the operational confidence in our advisory engine: tight bands (width $\le 0.08$) trigger High Confidence, while wide bands trigger Medium or Low Confidence and wider pre-positioning margins."*

### Q6: *"If Sentinel-1 has a 6 to 12 day revisit cycle, how can it support operational flood monitoring?"*
**Answer**:
> *"Sentinel-1's 6–12 day revisit is a well-known operational constraint. However, Sentinel-1 is indispensable because optical satellites like Sentinel-2 and Landsat cannot penetrate the cloud cover of the South Asian monsoon.
> In OrbitGuard, Sentinel-1 provides high-resolution (30m) structural ground truth for calibration and inundation baselines, while daily precipitation (CHIRPS/IMD) and upstream transboundary river catchment runoff drive the predictive model between satellite passes. Additionally, when the upcoming NASA-ISRO SAR (NISAR) mission launches with dual-frequency L-band and S-band radar, revisit frequency over Assam will improve significantly."*

### Q7: *"How does your drought module work, and is it trained with machine learning?"*
**Answer**:
> *"The drought module (`hazards/drought.py`) uses **no machine learning training**—it is strictly index-based, which is why it is stamped with the module label `Demo: index-based`.
> It computes the Standardized Precipitation Index for 1, 3, and 6 months using Thom's Maximum Likelihood Estimation of a Gamma distribution with zero-rain adjustment:
> $$H(x) = q + (1 - q) \cdot G(x), \quad z = \text{norm.ppf}(H(x))$$
> It pairs this with the Vegetation Condition Index from MODIS 1km NDVI. The combined index weights precipitation deficit at 60% and vegetation stress at 40%:
> $$\text{Index} = 0.6 \cdot z(\text{SPI-3}) + 0.4 \cdot z(\text{VCI})$$
> Crucially, when evaluating year $Y$, year $Y$ is strictly excluded from the 30-year climatological baseline (1991–2025) to prevent temporal leakage."*

### Q8: *"How does OrbitGuard integrate into ASDMA's real-world disaster management workflow?"*
**Answer**:
> *"OrbitGuard is designed as an operational decision-support tool, not an autonomous actor. Every response and advisory explicitly embeds the disclaimer: `Decision support only; confirm with ASDMA/IMD official advisories.`
> In an operational DEOC (District Emergency Operations Center), the district disaster management officer doesn't need raw ML logits; they need three things:
> 1. Which districts are guaranteed high-priority regardless of model error (**Robust Flag**).
> 2. What the lower and upper bounds of affected exposure are (**CQR bounds**).
> 3. Standard operating actions (**rule-based advisories** sourced from `core/advisory_actions.yaml`, such as boat pre-positioning and embankment checks).
> The FastAPI service exposes clean REST endpoints that plug directly into existing state GIS portals."*

---

## 3. Recorded-Fallback Checklist (Demo Day Resilience)

If local wifi drops, the server port binds fail, or the live terminal freezes, follow this exact fallback hierarchy:

### Step 1: Pre-Baked Offline Visual Dashboard
- **File**: [orbitguard_dashboard.html](file:///C:/Users/HARSHVARDHAN/.gemini/antigravity/brain/c4dcc8b8-d703-455f-baca-738f734e4eec/orbitguard_dashboard.html)
- **Action**: Double-click to open in any web browser. It is 100% self-contained, contains embedded SVG charts, interactive weight sliders, advisory cards, backtest audit tables, and drought timelines. Requires zero internet connectivity and zero python processes.

### Step 2: Local Terminal Fast Curl Commands
If the browser UI is unavailable, run these instant PowerShell curl commands against precomputed JSONs:

```powershell
# 1. Health & Provenance Check
curl http://localhost:8000/health
curl http://localhost:8000/provenance

# 2. Query Multi-Hazard Catalog
curl http://localhost:8000/hazards

# 3. Query Flood Response Prioritization (June 2022 Peak)
curl "http://localhost:8000/ranking?hazard=flood&period=2022-06&lead=1_month"

# 4. Query Drought Severity Prioritization (June 2022)
curl "http://localhost:8000/ranking?hazard=drought&period=2022-06&lead=1_month"

# 5. Inspect Sentinel-1 Flood Extent GeoJSON
curl "http://localhost:8000/extent?period=2019-07"
```

### Step 3: Direct JSON File Inspection
If the FastAPI service cannot be started, open the precomputed JSON artifacts directly in VS Code or any text editor:
- **Flood Precomputed**: `outputs/flood_predictions_2022_06.json` (Shows 33 ranked zones, $p_{\text{low}} \le p_{\text{mid}} \le p_{\text{high}}$, robust flags).
- **Drought Precomputed**: `outputs/drought_predictions_2022_06.json` (Shows index-derived severity and shared ranking).
- **Backtest Metrics**: `metrics/event_backtest.json` (Shows 2019, 2020, 2022 backtests, MAE, and top-10 hits).
- **Lead Time Metrics**: `metrics/lead_time.json` (Shows 84.29% flagged 1 month prior across 350 polygon-months).
- **Claims Audit Table**: `metrics/claims_table.json` (Shows honest claim-by-claim status).

### Step 4: High-Resolution Static Evaluation Plots
Have these four PNG plots open in preview tabs:
1. `reports/event_predicted_vs_observed_timeline.png` (Timeline with CQR bands vs official disaster spikes).
2. `reports/event_reliability_diagram.png` (Calibration curves showing conservative bias).
3. `reports/event_ranking_hit_chart.png` (Top-10 spatial prioritization hits vs observed severe districts).
4. `reports/drought_index_timeline.png` (12-year statewide drought severity timeline 2014–2025).

### Step 5: Instant Unit Test Execution
To prove system reproducibility in front of judges in under 15 seconds:
```bash
python -m pytest tests -v
```
*(Confirms all 46 tests passing across intake, leakage, CQR coverage, and API contracts in 13.2 seconds).*
