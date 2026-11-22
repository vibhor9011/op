# OrbitGuard Integration Inventory & Discovery Report
**Phase 0 Deliverable — Team AsGuardians // ASTRA Hackathon 2026**
**Timestamp**: 2026-11-22T03:09:00+05:30
**Git Branch**: `integrate`

---

## 1. Executive Summary

OrbitGuard represents an operational-grade flood early warning and disaster response prioritisation framework for the 33 administrative districts of Assam. A thorough discovery audit of the repository was conducted across model code (`core/`, `hazards/`), precomputed artifacts (`outputs/`), empirical validation benchmarks (`metrics/`), audit reports (`reports/`), the backend service (`service/`), and the web application (`frontend/`).

Existing tests (46 unit and contract tests) pass with 100% compliance. The frontend builds cleanly via Vite in 2.07s. However, critical contract mismatches were uncovered between the model outputs (33 real administrative districts, 72 monthly periods, conformal intervals, SHAP drivers) and the prototype frontend (which relied on an 8-district toy schematic generator). 

This inventory specifies the architectural baseline, records what works and what is broken, documents every contract mismatch, and establishes the phase-by-phase integration strategy.

---

## 2. Inventory of Repository Components

| Component / Path | Current State | Verification / Artifacts | Integration Action |
|---|---|---|---|
| **`core/` & `hazards/`** | Production-ready ML pipeline & hazard models | `hazards/flood.py` (M1–M7 LightGBM + CQR + SHAP), `hazards/drought.py` (SPI-3 + VCI index) | **Keep unmodified** (strict constraint: never edit model code). |
| **`outputs/`** | 148 verified precomputed artifacts | 72 flood JSONs, 72 drought JSONs, `flood_zones.geojson`, `flood_extent_2019_07.geojson`, `shap_explanations.json`, `extent_summary.json` | **Keep unmodified**; backend serves strictly from these files. |
| **`metrics/`** | Audited empirical benchmark results | `results.json`, `lead_time.json`, `event_backtest.json`, `claims_table.json`, `reliability_audit.json`, `run_info.json` | **Keep unmodified**; status badges and claim texts derived dynamically. |
| **`service/`** | FastAPI decision support API | 9 working endpoints, CORS enabled, Pydantic schemas, 46 passing tests | **Upgrade**: Add `/advisories`, `/geometry`, `/timeline`, `/overview`, startup self-check, and `DATA_MODE=live\|mock`. |
| **`frontend/`** | React 19 + Vite 8 + Tailwind v4 + Leaflet | Standalone UI shell with mock/local engine; builds in 2.07s | **Upgrade**: Replace 8-district toy engine with real-data adapter for 33 districts; implement mission-control design system. |
| **`reports/`** | 6 technical audit reports & visualizations | `reliability_audit.md`, `event_backtest.md`, `data_audit_v2.md`, `model_card.md`, LOYO evaluation curves | **Reference**: Surface findings in Model Trust panel. |
| **`tests/`** | 46 passing unit/contract tests | `pytest tests -q` passes in 14.78s | **Extend**: Add Phase 1 real-data endpoint contract tests and frontend unit tests. |

---

## 3. Existing Test & Build Baseline

1. **Backend Test Suite**:
   - `python -m pytest tests -q`
   - **Result**: `46 passed, 2 warnings in 14.78s` (100% pass rate).
   - Warnings: Deprecation alias in `anyio`, CPU core detection warning in Windows `loky` (silenced by `LOKY_MAX_CPU_COUNT=4`).
2. **Frontend Build & Dependency Audit**:
   - `npm --prefix frontend install` -> 79 packages audited, 0 vulnerabilities.
   - `npm --prefix frontend run build` -> Vite v8.3.8 built `dist/` in 2.07s without errors.
3. **Documentation Consistency Audit**:
   - `python scripts/check_metrics_consistency.py` -> 963 verified numeric citations, zero orphan numbers.

---

## 4. Contract Mismatches & Adapter Strategy

| Contract Dimension | Real Model Deliverables (`outputs/`, `metrics/`) | Frontend Expectation (`spec.json`, `orbitguardEngine.js`) | Consumer-Side Resolution (`service/` & `frontend/`) |
|---|---|---|---|
| **District Set** | **33 canonical districts** (`G01` to `G33`) with official Assam names and accurate coordinates. | Only 8 hardcoded districts (`dhemaji`, `lakhimpur`, `golaghat`, `nagaon`, `morigaon`, `nalbari`, `barpeta`, `dhubri`). | Backend serves canonical GeoJSON (`/geometry`). Frontend dynamically renders all 33 districts across map, rankings, and drawers. |
| **Zone Identifiers** | `id: "G01"` .. `"G33"` (alphanumeric geometry IDs). | `id: "dhemaji"` (lowercase district name strings). | Standardize on canonical `G01`..`G33` IDs. Maintain reverse lookup map (`name <-> id`) for compatibility. |
| **Time Granularity** | **Monthly timestep** (`2014-05` to `2025-10`, 72 periods). Lead times: `1_month` (forecast) vs `same_month` (nowcast). | Hardcoded `day = 1, 2, 3` and `rainBoost = 0..30`. | Time scrubber operates over real monsoon periods with play/scrub controls. Lead selector toggles `1_month` vs `same_month`. |
| **Lead Wording Rule** | Monthly lead time flagged 84.3% of severe events 1 month ahead. **Daily 1–3 day lead time is NOT validated**. | Showed "Day 1, Day 2, Day 3" forecast horizons. | In accordance with Honesty Rules: UI explicitly states **"1-Month Risk Outlook"** for `1_month` lead and **"Same-Month Risk Assessment"** for nowcast. Never use "1–3 day forecast". |
| **Hazards Supported** | **Flood** (LightGBM LOYO + CQR + SHAP) and **Drought** (`Demo: index-based` SPI-3 + VCI). | Flood active; "Orbital" planned modal; other hazards as static tags. | Dynamic hazard tabs: Flood (Operational Prototype), Drought (Demo: Index-Based), Landslide/Cyclone/Heatwave ("Planned - no data yet" with NO fake numbers). |
| **Advisory Format** | Rule-based engine (`core/advisory.py` + `core/advisory_actions.yaml`) outputs levels `Watch`, `Warning`, `Severe` with ASDMA disclaimer. | Hardcoded per-agency actions (`SDRF`, `SDMA`, `DISTRICT`, `NGO`) in `spec.json`. | Integrate real advisory generator: exposes `/advisories` endpoint, returning calibrated advisory levels, empirical triggers, and mandatory ASDMA advisory disclaimer. |
| **Data Mode & Fallback** | `DATA_MODE=live|mock`. Live mode strictly serves real precomputed files without falling back. | Silently caught network errors and defaulted to `localDashboard(day, rainBoost)`. | Strict mode enforcement: `live` mode surfaces network or parsing errors clearly. `mock` mode displays an unmissable banner: *"MOCK DATA - not model output"*. |

---

## 5. Architectural Decision Log

1. **Keep Existing Model Code & Precomputed Outputs Untouched**:
   - Zero changes to `core/`, `hazards/`, `outputs/`, or `metrics/`.
   - All contract reconciliation is handled by consumer adapters in `service/` and `frontend/src/services/`.
2. **Offline-Safe Resilience**:
   - The frontend will bundle all necessary geometry (`assam_districts_33.geojson`) and precomputed baseline states so the prototype operates smoothly even on flaky conference/hackathon venue Wi-Fi.
3. **Pydantic Contract & Schema Validation**:
   - Add `/advisories`, `/geometry`, `/timeline`, and `/overview` endpoints with strict Pydantic schemas.
   - Run a startup integrity check that verifies all 72 prediction files have 33 unique zones, monotonic ranks, and valid intervals ($p_{\text{low}} \le p_{\text{mid}} \le p_{\text{high}}$).

---

## 6. Phase 0 Verification Checkpoint
- [x] Full codebase inspection completed.
- [x] All 46 backend tests verified passing.
- [x] Frontend dependencies installed and production build verified.
- [x] All contract mismatches cataloged and mapped to adapter solutions.
- [x] Git branch `integrate` active.
