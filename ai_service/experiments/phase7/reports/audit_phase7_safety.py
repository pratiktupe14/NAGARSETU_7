"""
Phase 7 - Task 9 & 11: Comprehensive Production Safety Audit
Conducts an automated cryptographic verification of all original model weights,
verifies git working tree status, and executes the 31-test safe test suite.
Outputs:
- phase7_safety_audit.json (phase7/reports)
"""

import os
import sys
import json
import hashlib
import subprocess

REPORTS_DIR = r"ai_service\experiments\phase7\reports"
OUTPUT_JSON = os.path.join(REPORTS_DIR, "phase7_safety_audit.json")

EXPECTED_PRODUCTION_HASHES = {
    "civicmodel.pt": "1067a09d37e4e9081164e6d6da337ad66d8ec7a884a6a194e58703beee804aa2",
    "best.pt": "0965dfbb16320981abeab3ed50cefe90bef8dede1453407aed2d952898a765e6",
    "water_pipe_model.pt": "f1bc766c569d1053b4e252247e37edfcc0fe76d3ce594e8b1ae9020aa52aac86",
    "drainage_model.pt": "70821c225a90dd769f097c5d212ebce89a21aaf83667ada4a950d54e9d96e75f"
}

MODEL_PATHS = {
    "civicmodel.pt": r"ai_service\model\civicmodel.pt",
    "best.pt": r"ai_service\model\best.pt",
    "water_pipe_model.pt": r"ai_service\model\water_pipe_model.pt",
    "drainage_model.pt": r"ai_service\model\drainage_model.pt"
}

def get_file_hash(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

def main():
    print("=" * 80)
    print("PHASE 7 TASK 9 & 11: FINAL PRODUCTION SAFETY AUDIT")
    print("=" * 80)
    os.makedirs(REPORTS_DIR, exist_ok=True)

    # 1. Cryptographic Model Hash Check
    print("\n--- 1. Cryptographic Hash Audit of Production Models ---")
    hash_results = {}
    all_hashes_valid = True
    for model_name, path in MODEL_PATHS.items():
        if not os.path.exists(path):
            hash_results[model_name] = {"status": "MISSING", "valid": False}
            all_hashes_valid = False
            continue

        actual_hash = get_file_hash(path)
        expected_hash = EXPECTED_PRODUCTION_HASHES[model_name]
        is_match = (actual_hash == expected_hash)
        if not is_match:
            all_hashes_valid = False

        hash_results[model_name] = {
            "path": path,
            "expected_sha256": expected_hash,
            "actual_sha256": actual_hash,
            "valid": is_match,
            "size_bytes": os.path.getsize(path)
        }
        print(f"  {model_name}: {'MATCH' if is_match else 'MISMATCH'}")
        print(f"    Expected: {expected_hash}")
        print(f"    Actual:   {actual_hash}")

    # 2. Git Status Check (Tracked Files Protection)
    print("\n--- 2. Git Status Audit (Tracked Files Protection) ---")
    git_proc = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True)
    git_output = git_proc.stdout.strip().splitlines()

    tracked_modifications = []
    untracked_files = []
    for line in git_output:
        status_code = line[:2]
        filepath = line[3:]
        if status_code.strip() == "??":
            untracked_files.append(filepath)
        else:
            tracked_modifications.append(line)

    zero_tracked_modifications = (len(tracked_modifications) == 0)
    print(f"  Tracked modifications count: {len(tracked_modifications)}")
    print(f"  Zero tracked modifications: {zero_tracked_modifications}")
    if not zero_tracked_modifications:
        for mod in tracked_modifications:
            print(f"    WARNING: {mod}")

    # 3. Safe Test Suite Execution
    print("\n--- 3. Safe Test Suite Execution ---")
    test_cmd = [
        sys.executable, "-m", "pytest",
        "ai_service/tests/test_clean_road_verification.py",
        "ai_service/tests/test_nodes.py",
        "ai_service/tests/test_pipe_ai.py",
        "-v"
    ]
    test_proc = subprocess.run(test_cmd, capture_output=True, text=True)
    test_output = test_proc.stdout
    test_exit_code = test_proc.returncode

    passed_count = 0
    failed_count = 0
    for line in test_output.splitlines():
        if "passed in" in line:
            print(f"  {line.strip()}")
        if "PASSED" in line:
            passed_count += 1
        if "FAILED" in line:
            failed_count += 1

    all_tests_passed = (test_exit_code == 0 and failed_count == 0)
    print(f"  Tests passed: {passed_count}, Tests failed: {failed_count}")
    print(f"  Overall test suite passed: {all_tests_passed}")

    # 4. Final Safety Verdict
    final_verdict = (
        all_hashes_valid and
        zero_tracked_modifications and
        all_tests_passed
    )

    audit_payload = {
        "audit_name": "Phase 7 Final Production Safety Audit",
        "timestamp": "2026-11-03",
        "verdict": "PASSED" if final_verdict else "FAILED",
        "cryptographic_integrity": {
            "all_valid": all_hashes_valid,
            "models": hash_results
        },
        "git_working_tree": {
            "clean_tracked_files": zero_tracked_modifications,
            "tracked_modifications": tracked_modifications,
            "untracked_count": len(untracked_files)
        },
        "test_suite": {
            "exit_code": test_exit_code,
            "all_passed": all_tests_passed,
            "passed_tests": passed_count,
            "failed_tests": failed_count
        }
    }

    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(audit_payload, f, indent=2)
    print(f"\nSaved safety audit payload to {OUTPUT_JSON}")
    print(f"FINAL AUDIT VERDICT: {'PASSED - 100% SAFE' if final_verdict else 'FAILED - SAFETY VIOLATION'}")

    return 0 if final_verdict else 1

if __name__ == "__main__":
    sys.exit(main())

