# OrbitGuard Mission Demo Script & Live Walkthrough Guide (docs/demo_walkthrough.md)

**Target Duration**: 75–90 Seconds  
**Audience**: ASTRA Hackathon 2026 Evaluation Panel & ASDMA Technical Observers  
**Presenter**: Lead Integration Engineer / Product Designer (Team AsGuardians)  
**Strict Honesty Protocol**: Every number spoken aloud is pulled directly from verified holdout metrics in `metrics/event_backtest.json`, `metrics/lead_time.json`, and `metrics/results.json`.

---

## 1. Quick Setup & Fallback Readiness Checklist

- [x] Backend running on `http://localhost:8000` (or offline static demo cache verified via `npm run build`).
- [x] Browser opened to `http://localhost:5173` (or static `dist/index.html`).
- [x] Initial view: Flood Hazard Module, `2022-06`, `1-Month Risk Outlook`, Agency: `ALL`.
- [x] Keyboard ready: `Space` (Play/Pause), `Ctrl+K` (Command Palette), `←`/`→` (Scrub).

---

## 2. Timed 80-Second Live Walkthrough Script

### **[00:00 - 00:15] Hook & Mission Context**
*Action*: Start on the mission control overview screen (`2022-06`).
> **Speak**:
> "Esteemed judges, annual monsoon floods in Assam displace millions across the Brahmaputra basin, but emergency managers often face fragmented data or single-point predictions that hide forecast volatility. 
> This is **OrbitGuard**—an operational multi-hazard early warning and response prioritization system built for the Assam State Disaster Management Authority (ASDMA)."

---

### **[00:15 - 00:35] Antecedent Catchment Build-up & 1-Month Risk Outlook**
*Action*: Press `←` to scrub back to `2022-05`, then press `→` forward to `2022-06`. Point cursor to **Dhemaji (#1)** and **Dhubri (#2)** on the left Priority Sidebar.
> **Speak**:
> "Look at May 2022: antecedent catchment saturation was mounting, with statewide risk at 3.0%. 
> Scrubbing forward into June 2022, OrbitGuard's 1-month risk outlook flags an impending catastrophe: statewide predicted severe risk surges to **77.3%** (`p_mid = 0.7725`, 80% conformal prediction interval `[54.1% – 84.1%]`). 
> Dhemaji and Dhubri are immediately escalated to **High Tier (Priority 0.329 and 0.318)**. 
> Notice the **ROBUST** badge: their priority holds in the top-5 whether evaluated at the median or upper 80% conformal bound."

---

### **[00:35 - 00:50] Ground-Truth Extent & Physical Attribution**
*Action*: Toggle **Sentinel-1 SAR** layer in the bottom-right HUD. Adjust the SAR opacity slider to 85%. Click on **Dhemaji (G09)** to slide open the `ZoneDrawer`.
> **Speak**:
> "Here in the Brahmaputra corridor, we overlay the 30-meter Sentinel-1 SAR microwave radar footprint. 
> Clicking into Dhemaji opens our operational explainability drawer: the top drivers are **antecedent catchment precipitation** (+0.142 TreeSHAP attribution) and **river channel proximity** (-0.065), coupled with flat slope drainage constraints.
> Below, OrbitGuard instantly generates ASDMA action directives: pre-positioning SDRF boat teams in Subansiri lowlands and opening relief camps 10 days before peak cresting."

---

### **[00:50 - 01:05] Multi-Hazard Toggle & Honest Engineering Boundaries**
*Action*: In the TopBar, click the **DROUGHT [INDEX-DEMO]** tab, then hover over **LANDSLIDE [PLANNED]**. Click **MODEL TRUST** in the TopBar.
> **Speak**:
> "OrbitGuard is designed as a unified disaster cockpit. Under the Drought tab, we evaluate a 30-year SPI-3 and MODIS VCI moisture-deficit index. 
> Crucially, for Landslide, Cyclone, and Wildfire, we display an honest **PLANNED** status—zero synthetic predictions or unverified numbers are fabricated.
> Clicking our **Model Trust** console reveals our complete Leave-One-Year-Out cross-validation results: our LightGBM classifier achieves an out-of-fold **F1 of 0.704**, **ROC-AUC of 0.793**, an exact **80.0% empirical coverage** on nominal 80% CQR intervals, and a rigorous label-permutation test p-value of **p = 0.0476**."

---

### **[01:05 - 01:20] Closing & Operational Handover**
*Action*: Click the **PRINT BRIEFING** button inside Dhemaji's drawer (or press `Escape` back to main console).
> **Speak**:
> "With a single click, emergency district officers can generate this 1-page printable ASDMA briefing sheet for district field magistrates.
> OrbitGuard moves disaster management from reactive rescue to calibrated, proactive response. Thank you."

---

## 3. The 8 Toughest Judge Questions & Bulletproof Honest Answers

### **Q1: "Your pitch mentioned a 1–3 day forecast. Is that what is running here?"**
> **Answer**:  
> "No, and we document that transparently in our Model Card and Trust Console. The available historical open radar and gauge archive operates on monthly aggregations. OrbitGuard provides a **1-Month Risk Outlook** (and same-month nowcast) with out-of-fold Leave-One-Year-Out validation. 
> A daily 1–3 day operational forecast requires real-time automated daily ingest from MOSDAC or IMD AWS stations, which is marked as **Planned (Not Validated)** in our claims audit."

### **Q2: "What is your actual validation score on historical floods? Did you train on the same data you tested on?"**
> **Answer**:  
> "We used strict **Leave-One-Year-Out (LOYO) cross-validation** across all 12 years (2014–2025). When evaluating 2022, no 2022 data was seen during training. 
> Under LOYO CV, our forecast model achieves:
> - **Macro F1**: 0.704 (In-fold tuned threshold = 0.4155)
> - **ROC-AUC**: 0.793
> - **PR-AUC**: 0.771
> - **Brier Score**: 0.160
> Furthermore, in our 20-run permutation test where labels were shuffled within polygons across years, the empirical p-value was **p = 0.0476**, confirming statistically significant predictive signal beyond seasonal climatology."

### **Q3: "How do you handle forecast uncertainty? Why not just give a single probability?"**
> **Answer**:  
> "Single-point estimates are dangerous in disaster response because a 40% probability with wide uncertainty (e.g., [10%–80%]) requires a very different emergency staging strategy than 40% with narrow uncertainty ([35%–45%]).
> We use **Conformalized Quantile Regression (CQR)** to construct distribution-free 80% prediction intervals. On held-out test data, our nominal 80% band achieves **exactly 80.0% empirical coverage**."

### **Q4: "What does the 'ROBUST' tag in the priority sidebar mean?"**
> **Answer**:  
> "Priority is defined as Exceedance Risk multiplied by District Exposure (`p_mid × exposure`). 
> A district is flagged as **ROBUST** if its allocation priority remains in the statewide Top 5 regardless of whether we rank by the median probability (`p_mid`) or the upper conformal bound (`p_high`). This prevents resource misallocation for borderline volatile districts."

### **Q5: "Why did your top 10 ranked districts miss some observed flooded districts in 2019 and 2020?"**
> **Answer**:  
> "In 2019, our top 10 predicted hit 4 of the top 10 observed (with 6 false alarms and 6 misses); in 2020, it hit 3 of 10; and in 2022, it hit 6 of 10. 
> In 2019 and 2020, localized embankment breaches occurred in districts with moderate rainfall that our macro basin precipitation features did not capture without live river gauge data. That is why OrbitGuard outputs uncertainty bounds and embeds the mandatory notice that outputs must be confirmed with ASDMA ground telemetry."

### **Q6: "Where does the SAR flood footprint come from? Is it validated against ISRO Bhuvan?"**
> **Answer**:  
> "The flood extent is extracted from Sentinel-1 GRD SAR backscatter composites (IW mode, VV polarization, < -16 dB threshold with Otsu refinement, permanent water masked via JRC, and slope < 5°).
> In the hackathon input archive, no independent reference Bhuvan GeoJSON was provided. Therefore, we report IoU and F1 as `null` with reason `'no reference layer supplied'` and visually cross-check the footprint."

### **Q7: "Can this system run offline if internet connectivity drops in a cyclone or flood?"**
> **Answer**:  
> "Yes. We built a zero-dependency static offline demo build (`scripts/build_static_demo.py` and `npm run build`). 
> All 144 precomputed 33-district monthly prediction JSONs, GeoJSON boundaries, and SHAP drivers are packaged into `frontend/dist/data/`. If the live FastAPI backend is unreachable, the client automatically switches to static cache mode with an honest amber offline ribbon."

### **Q8: "How does the Drought module work compared to the Flood module?"**
> **Answer**:  
> "The flood module is an ML-trained LightGBM classifier with conformal intervals. The drought module is explicitly labeled **'Demo: Index-Based'**. 
> It computes a standardized precipitation index (SPI-3) via a calendar-month gamma fit alongside a MODIS NDVI Vegetation Condition Index (VCI), combined via a documented weighting of `0.6*z(SPI-3) + 0.4*z(VCI)`."

---

## 4. Quick Emergency Hotkey Sheet

- `Space`: Play / Pause timeline replay
- `Ctrl + K`: Open Command Search (districts, periods, layer toggles)
- `←` / `→`: Step backward / forward one month
- `Escape`: Close active drawer or modal
- `1` / `2`: Toggle between 1-Month Outlook and Same-Month Risk
