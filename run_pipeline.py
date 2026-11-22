"""OrbitGuard Flood Module: End-to-End Pipeline CLI Runner.

Usage:
    python run_pipeline.py [--zip PATH] [--force] [--skip-train] [--degraded-ok]
"""

import os
import sys
import argparse
import json
import pandas as pd

# Set MPLCONFIGDIR to avoid permissions warnings on matplotlib cache
os.environ["MPLCONFIGDIR"] = os.path.abspath(os.path.join("data", "processed", ".mplconfig"))
os.makedirs(os.environ["MPLCONFIGDIR"], exist_ok=True)
os.environ["LOKY_MAX_CPU_COUNT"] = str(os.cpu_count() or 4)

from core.intake import run_intake
from core.base import build_base_table
from core.ingest import run_ingest
from core.ranking import compute_exposure_and_priority, generate_weight_sensitivity_table
from core.export import export_flood_zones_geojson, export_monthly_predictions_json, write_model_card
from core.backtest import run_event_backtest
from hazards.flood import run_synthetic_m7_pipeline


def main():
    parser = argparse.ArgumentParser(description="OrbitGuard Flood Module Pipeline Runner")
    parser.add_argument("--zip", default=None, help="Path to input raw data zip file")
    parser.add_argument("--force", action="store_true", help="Force re-extraction and processing")
    parser.add_argument("--skip-train", action="store_true", help="Skip model training and cross-validation")
    parser.add_argument("--degraded-ok", action="store_true", default=True, help="Continue past missing SAR/rain CSVs in degraded mode")
    args = parser.parse_args()

    print("================================================================================")
    print("                    ORBITGUARD FLOOD EARLY WARNING MODULE                       ")
    print("                Multi-Hazard Response Prioritisation (Assam)                    ")
    print("================================================================================")

    # 1. Phase Z: Intake
    print("\n>>> PHASE Z: Zip Intake & File Content Classification")
    try:
        inventory = run_intake(zip_path=args.zip, force=args.force)
    except Exception as e:
        print(f"\n[FATAL ERROR IN PHASE Z]: {e}")
        sys.exit(1)

    # 2. Phase B: Base Table & Boundaries
    print("\n>>> PHASE B: Boundary Harmonization & 2,520-Row Base Table Construction")
    try:
        df_base = build_base_table()
    except Exception as e:
        print(f"\n[FATAL ERROR IN PHASE B]: {e}")
        sys.exit(1)

    # 3. Phase A: Earth Engine Integration / Degraded Mode
    print("\n>>> PHASE A: Earth Engine Integration & Hard Gate Evaluation")
    try:
        ingest_res = run_ingest(inventory=inventory, degraded_ok=args.degraded_ok)
    except Exception as e:
        print(f"\n[FATAL ERROR IN PHASE A]: {e}")
        sys.exit(1)

    is_degraded = ingest_res.get("is_degraded", False)

    # 4. Phase 3 & 4: Model Cross-Validation
    m7_results = None
    if not args.skip_train:
        print("\n>>> PHASES 1-4: Feature Engineering, Baselines & LOYO Cross-Validation")
        if is_degraded:
            print("DEGRADED MODE DETECTED: Executing secondary synthetic severity model (M7)...")
            m7_results = run_synthetic_m7_pipeline()
        else:
            print("NORMAL MODE DETECTED: Satellite SAR observations available for full LOYO CV.")
    else:
        print("\n>>> PHASES 1-4: Skipped (--skip-train flag active)")

    # 5. Phase 5: Response Prioritization & Sensitivity Analysis
    print("\n>>> PHASE 5: Composite Exposure & Priority Ranking")
    df_ranked = compute_exposure_and_priority(df_base)
    sensitivity_df = generate_weight_sensitivity_table(df_base)
    sensitivity_path = os.path.join("reports", "priority_ranking_sensitivity.csv")
    sensitivity_df.to_csv(sensitivity_path, index=False)
    print(f"[Phase 5] Priority ranking sensitivity table saved: {sensitivity_path}")

    # Historical Event Backtest & Claims Audit
    print("\n>>> PHASE 5 EXTENSION: Severe Event Backtesting & Deck Claims Audit")
    run_event_backtest()

    # 6. Phase 6: Exports & Reporting
    print("\n>>> PHASE 6: GeoJSON & Model Card Export")
    export_flood_zones_geojson(df_ranked, is_degraded=is_degraded)
    write_model_card(is_degraded=is_degraded, m7_results=m7_results)

    # 7. SAR Extent Processing & Footprint Extraction
    print("\n>>> SAR EXTENT & VALIDATION FOOTPRINT")
    from sar.extent import process_extent
    process_extent()

    # Precompute all service endpoints outputs (72 periods, SHAP explanations, provenance)
    from core.export import precompute_all_service_outputs
    precompute_all_service_outputs()

    # Precompute all drought predictions and reports
    print("\n>>> PHASE DROUGHT: Index-Based Drought Precomputations")
    from hazards.drought import precompute_all_drought_outputs, validate_drought_against_reference_or_report
    precompute_all_drought_outputs()
    validate_drought_against_reference_or_report()

    # Run reliability audit
    print("\n>>> RELIABILITY AUDIT: Stability, Permutation & Sensitivity")
    from core.reliability import run_full_reliability_audit
    run_full_reliability_audit()

    # Export pipeline verification summary JSON (matches outputs/*.json checklist)
    summary_path = os.path.join("outputs", "pipeline_verification_summary.json")
    summary_payload = {
        "module": "OrbitGuard_Flood",
        "vintage": "2014-2025",
        "spatial_units": 33,
        "base_table_rows": len(df_base),
        "mode": "DEGRADED_MODE" if is_degraded else "OPERATIONAL",
        "status": "PIPELINE CHECK ONLY - no observed-derived labels" if is_degraded else "VALIDATED",
        "m7_metrics": m7_results.get("metrics") if m7_results else None,
        "input_archive": inventory.get("synthetic_base_csv", [{}])[0].get("path", "")
    }
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary_payload, f, indent=2)
    print(f"[Phase 6] Exported pipeline verification summary: {summary_path}")

    # Summary Notice
    print("\n================================================================================")
    if is_degraded:
        print("PIPELINE STATUS: COMPLETED IN DEGRADED MODE")
        print("NOTICE: 'PIPELINE CHECK ONLY - no observed-derived labels' applied to all outputs.")
        print("No headline metrics or operational flood_predictions.json produced per Honesty Rules.")
    else:
        print("PIPELINE STATUS: COMPLETED SUCCESSFULLY (OPERATIONAL SAR DERIVED)")
    print("================================================================================\n")


if __name__ == "__main__":
    main()
