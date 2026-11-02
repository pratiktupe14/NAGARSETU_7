"""
Phase 8 - Task 13: Comprehensive Final Safety Audit
Performs an exhaustive cryptographic, source code, and regression safety audit:
1. Cryptographic hashes of all 4 original production models against Phase 0 baselines
2. Git working tree audit (verifies zero tracked file modifications)
3. Audit of all untracked Phase 8 experiment files
4. Execution and pass verification of the 31 existing production AI tests
Outputs:
- phase8_final_safety_audit.json (root and phase8/audit)
"""

import os
import sys
import json
import hashlib
import subprocess

AUDIT_DIR = r"ai_service\experiments\phase8\audit"
ROOT_JSON = r"phase8_final_safety_audit.json"
PHASE8_JSON = os.path.join(AUDIT_DIR, "phase8_final_safety_audit.json")

EXPECTED_PRODUCTION_HASHES = {
    "civicmodel.pt": {
        "path": r"ai_service\model\civicmodel.pt",
        "expected_sha256": "1067a09d37e4e9081164e6d6da337ad66d8ec7a884a6a194e58703beee804aa2",
        "expected_size": 22519594
    },
    "best.pt": {
        "path": r"ai_service\model\best.pt",
        "expected_sha256": "0965dfbb16320981abeab3ed50cefe90bef8dede1453407aed2d952898a765e6",
        "expected_size": 22543854
    },
    "water_pipe_model.pt": {
        "path": r"ai_service\model\water_pipe_model.pt",
        "expected_sha256": "f1bc766c569d1053b4e252247e37edfcc0fe76d3ce594e8b1ae9020aa52aac86",
        "expected_size": 6221217
    },
    "drainage_model.pt": {
        "path": r"ai_service\model\drainage_model.pt",
        "expected_sha256": "70821c225a90dd769f097c5d212ebce89a21aaf83667ada4a950d54e9d96e75f",
        "expected_size": 6220717
    }
}

def get_sha256(filepath):
    if not os.path.exists(filepath):
        return None
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

def main():
    print("=" * 80)
    print("PHASE 8 TASK 13: COMPREHENSIVE FINAL SAFETY AUDIT")
    print("=" * 80)
    os.makedirs(AUDIT_DIR, exist_ok=True)

    # 1. Cryptographic Model Hash Verification
    print("\n--- 1. Cryptographic Hash Audit of Production Models ---")
    model_audit = {}
    all_models_valid = True
    for name, meta in EXPECTED_PRODUCTION_HASHES.items():
        p = meta["path"]
        exists = os.path.exists(p)
        actual_sha = get_sha256(p) if exists else None
        actual_size = os.path.getsize(p) if exists else 0
        match = (actual_sha == meta["expected_sha256"])
        if not match:
            all_models_valid = False

        model_audit[name] = {
            "path": p,
            "exists": exists,
            "expected_sha256": meta["expected_sha256"],
            "actual_sha256": actual_sha,
            "actual_size_bytes": actual_size,
            "valid": match
        }
        print(f"  {name}: {'MATCH' if match else 'FAIL'} (SHA-256: {actual_sha[:16]}...)")

    # 2. Git Working Tree Status
    print("\n--- 2. Git Status Audit ---")
    git_proc = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True)
    git_lines = git_proc.stdout.strip().splitlines()

    tracked_modifications = []
    untracked_files = []
    for line in git_lines:
        code = line[:2].strip()
        fpath = line[3:].strip()
        if code == "??":
            untracked_files.append(fpath)
        else:
            tracked_modifications.append(line)

    clean_tracked = (len(tracked_modifications) == 0)
    print(f"  Tracked Modifications: {len(tracked_modifications)} (Clean: {clean_tracked})")
    print(f"  Untracked Experiment/Report Files: {len(untracked_files)}")

    # 3. Existing Production Test Suite Execution
    print("\n--- 3. Safe AI Production Unit Tests (31 Baseline Tests) ---")
    test_cmd = [
        sys.executable, "-m", "pytest",
        "ai_service/tests/test_clean_road_verification.py",
        "ai_service/tests/test_nodes.py",
        "ai_service/tests/test_pipe_ai.py",
        "-v"
    ]
    test_proc = subprocess.run(test_cmd, capture_output=True, text=True)
    test_out = test_proc.stdout
    test_code = test_proc.returncode

    passed_count = sum(1 for line in test_out.splitlines() if "PASSED" in line)
    failed_count = sum(1 for line in test_out.splitlines() if "FAILED" in line)
    tests_valid = (test_code == 0 and passed_count == 31 and failed_count == 0)

    print(f"  Tests Passed: {passed_count} / 31 | Failed: {failed_count} | Exit Code: {test_code}")
    print(f"  Test Suite Valid: {tests_valid}")

    # Overall Verdict
    overall_safe = (all_models_valid and clean_tracked and tests_valid)

    audit_payload = {
        "timestamp": "2026-11-03",
        "phase": 8,
        "task": "Task 13 - Final Production Safety Audit",
        "verdict": "PASSED - 100% PRODUCTION SAFE" if overall_safe else "FAILED",
        "all_production_models_intact": all_models_valid,
        "models": model_audit,
        "git_status": {
            "clean_tracked_working_tree": clean_tracked,
            "tracked_modifications_count": len(tracked_modifications),
            "tracked_modifications": tracked_modifications,
            "untracked_files_count": len(untracked_files),
            "untracked_files": untracked_files
        },
        "test_suite": {
            "baseline_tests_expected": 31,
            "tests_passed": passed_count,
            "tests_failed": failed_count,
            "exit_code": test_code,
            "passed": tests_valid
        }
    }

    with open(PHASE8_JSON, "w", encoding="utf-8") as f:
        json.dump(audit_payload, f, indent=2)
    with open(ROOT_JSON, "w", encoding="utf-8") as f:
        json.dump(audit_payload, f, indent=2)

    print(f"\nSaved safety audit payload to {PHASE8_JSON} and {ROOT_JSON}")
    print(f"OVERALL SAFETY AUDIT VERDICT: {'PASSED' if overall_safe else 'FAILED'}")
    return 0 if overall_safe else 1

if __name__ == "__main__":
    sys.exit(main())

