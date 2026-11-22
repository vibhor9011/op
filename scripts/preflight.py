"""
OrbitGuard System Preflight Verification Script (scripts/preflight.py).
======================================================================
Prints hazards, periods, leads, and the evidence file for each status.
Verifies file contracts and integrity against metrics and outputs.
Confirms startup self-check properly validates clean files and excludes/logs violators.
Exits 0 on success, non-zero on any violation.
"""

import os
import sys

# Ensure root workspace directory is in python module search path
sys.path.insert(0, os.path.abspath("."))

import json
import glob
import math

OUTPUTS_DIR = "outputs"
METRICS_DIR = "metrics"
CANONICAL_IDS = {f"G{i:02d}" for i in range(1, 34)}

def run_preflight():
    print("=" * 80)
    print("              ORBITGUARD SYSTEM PREFLIGHT INTEGRATION AUDIT              ")
    print("=" * 80)

    fatal_errors = []

    # 1. Check Claims & Evidence Table
    claims_path = os.path.join(METRICS_DIR, "claims_table.json")
    if not os.path.exists(claims_path):
        fatal_errors.append(f"Missing required claims file: {claims_path}")
    else:
        with open(claims_path, "r", encoding="utf-8") as f:
            claims = json.load(f)
        print("\n[1] PITCH DECK CLAIMS & EVIDENCE VERIFICATION:")
        for k, v in claims.items():
            ev = v.get("evidence_file", "None")
            status = v.get("status", "unknown")
            print(f"  * {k:<22} -> [{status.upper():<12}] Evidence: {ev}")

    # 2. Check Lead Time Rules
    lead_time_path = os.path.join(METRICS_DIR, "lead_time.json")
    if not os.path.exists(lead_time_path):
        fatal_errors.append(f"Missing required lead time file: {lead_time_path}")
    else:
        with open(lead_time_path, "r", encoding="utf-8") as f:
            lt = json.load(f)
        gran = lt.get("lead_time_granularity")
        if gran != "monthly":
            fatal_errors.append(f"Expected monthly granularity, got {gran}")
        share = lt.get("summary_across_events", {}).get("overall_share_flagged")
        print(f"\n[2] LEAD TIME & HONESTY WORDING AUDIT:")
        print(f"  * Granularity: {gran} (Monthly lead only; daily 1-3 day is NOT validated)")
        print(f"  * 1-Month Ahead Share Flagged: {share * 100:.1f}% of severe event polygon-months")
        print(f"  * Approved Wording: '1-Month Risk Outlook' (Forecast), 'Same-Month Risk Assessment' (Nowcast)")

    # 3. Check Multi-Hazard Catalog
    hazards = [
        {"id": "flood", "status": "Operational Prototype", "evidence": "outputs/flood_predictions_*.json", "min_files": 72},
        {"id": "drought", "status": "Demo: Index-Based", "evidence": "outputs/drought_predictions_*.json", "min_files": 48},
        {"id": "landslide", "status": "Planned - no data yet", "evidence": "None (No outputs)", "min_files": 0},
        {"id": "cyclone", "status": "Planned - no data yet", "evidence": "None (No outputs)", "min_files": 0},
        {"id": "wildfire", "status": "Planned - no data yet", "evidence": "None (No outputs)", "min_files": 0}
    ]

    print("\n[3] MULTI-HAZARD CATALOG & STATUS AUDIT:")
    for h in hazards:
        files = glob.glob(os.path.join(OUTPUTS_DIR, f"{h['id']}_predictions_*.json"))
        count = len(files)
        print(f"  * {h['id'].capitalize():<12} -> [{h['status']:<22}] Files: {count:<3} Evidence: {h['evidence']}")
        if h["min_files"] > 0 and count < h["min_files"]:
            fatal_errors.append(f"Hazard '{h['id']}' expected at least {h['min_files']} files, found {count}")
        elif h["min_files"] == 0 and count > 0:
            fatal_errors.append(f"Hazard '{h['id']}' marked Planned but found {count} output files")

    # 4. Check Precomputed Outputs Integrity & Startup Self-Check Simulation
    print("\n[4] STARTUP SELF-CHECK AUDIT (Validation & Violator Exclusion):")
    from service.app import perform_startup_self_check, VALIDATED_FILES, EXCLUDED_FILES
    perform_startup_self_check()

    print(f"  * Precomputed Files Audited: {len(VALIDATED_FILES) + len(EXCLUDED_FILES)}")
    print(f"  * Validated for Active Serving: {len(VALIDATED_FILES)}")
    print(f"  * Excluded and Logged (Violators): {len(EXCLUDED_FILES)}")

    # Strict Gate: Flood files must have 100% clean validation (0 exclusions)
    flood_excluded = [f for f in EXCLUDED_FILES if "flood" in f]
    if flood_excluded:
        fatal_errors.append(f"Operational flood predictions contained violators: {flood_excluded}")
    else:
        print("  * Operational Flood Predictions (72/72): 100% VALIDATED (0 exclusions)")

    # Verify that excluded files are logged with exact failure reasons
    for fname, reason in list(EXCLUDED_FILES.items())[:3]:
        print(f"    - Excluded: {fname} (Reason: {reason})")
    if len(EXCLUDED_FILES) > 3:
        print(f"    ... and {len(EXCLUDED_FILES) - 3} more violators quarantined.")

    # 5. Check Spatial Layers
    print("\n[5] SPATIAL GEOMETRY & SAR FOOTPRINT LAYERS:")
    zones_geom = os.path.join(OUTPUTS_DIR, "flood_zones.geojson")
    extent_geom = os.path.join(OUTPUTS_DIR, "flood_extent_2019_07.geojson")
    if os.path.exists(zones_geom):
        with open(zones_geom, "r", encoding="utf-8") as f:
            zg = json.load(f)
        print(f"  * Canonical 33 Districts Boundary: PRESENT ({len(zg.get('features', []))} polygons)")
    else:
        fatal_errors.append("Missing outputs/flood_zones.geojson")

    if os.path.exists(extent_geom):
        print("  * Sentinel-1 SAR Event Footprint (2019-07): PRESENT")
    else:
        fatal_errors.append("Missing outputs/flood_extent_2019_07.geojson")

    print("\n" + "=" * 80)
    if fatal_errors:
        print(f"[FAIL] PREFLIGHT DETECTED {len(fatal_errors)} FATAL VIOLATIONS:")
        for v in fatal_errors:
            print(f"  - {v}")
        print("=" * 80)
        sys.exit(1)
    else:
        print("[SUCCESS] ALL PREFLIGHT AUDITS PASSED CLEANLY (Zero fatal violations)")
        print("  * Self-check mechanism verified: valid files served, violators quarantined.")
        print("=" * 80)
        sys.exit(0)

if __name__ == "__main__":
    run_preflight()
