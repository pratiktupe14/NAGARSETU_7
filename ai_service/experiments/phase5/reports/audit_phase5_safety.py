"""
Phase 5 - Task 10: Production Compatibility and Safety Audit
Verifies:
1. Four original production models remain cryptographically bit-identical.
2. Production model paths in model_manager.py are untouched.
3. No experimental code/models leak into production modules.
4. Working tree tracked files have zero uncommitted changes (clean git status).
5. Reports full inventory of Phase 5 created files.
"""

import os
import sys
import hashlib
import subprocess
import json

ORIGINAL_MODEL_HASHES = {
    "civicmodel.pt": "1067a09d37e4e9081164e6d6da337ad66d8ec7a884a6a194e58703beee804aa2",
    "best.pt": "0965dfbb16320981abeab3ed50cefe90bef8dede1453407aed2d952898a765e6",
    "water_pipe_model.pt": "f1bc766c569d1053b4e252247e37edfcc0fe76d3ce594e8b1ae9020aa52aac86",
    "drainage_model.pt": "70821c225a90dd769f097c5d212ebce89a21aaf83667ada4a950d54e9d96e75f"
}

MODEL_DIR = r"ai_service\model"
AUDIT_OUTPUT_PATH = r"ai_service\experiments\phase5\reports\phase5_safety_audit.json"

def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

def run_safety_audit():
    print("=" * 80)
    print("PHASE 5 TASK 10: PRODUCTION COMPATIBILITY & SAFETY AUDIT")
    print("=" * 80)

    # 1. Model Hashes
    model_audit = {}
    all_models_intact = True
    for model_name, expected_hash in ORIGINAL_MODEL_HASHES.items():
        p = os.path.join(MODEL_DIR, model_name)
        if not os.path.exists(p):
            model_audit[model_name] = {"status": "MISSING", "expected": expected_hash}
            all_models_intact = False
            continue
        actual_hash = sha256_file(p)
        matches = (actual_hash == expected_hash)
        if not matches:
            all_models_intact = False
        model_audit[model_name] = {
            "status": "VERIFIED_INTACT" if matches else "CORRUPTED",
            "actual_sha256": actual_hash,
            "expected_sha256": expected_hash,
            "matches": matches,
            "size_bytes": os.path.getsize(p)
        }
        print(f"[{'PASS' if matches else 'FAIL'}] {model_name}: {actual_hash[:16]}... matches baseline: {matches}")

    # 2. Check Git status for tracked file modifications
    git_status = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True)
    lines = git_status.stdout.strip().split("\n") if git_status.stdout.strip() else []
    tracked_modifications = [l for l in lines if l and not l.startswith("??")]
    untracked_files = [l for l in lines if l.startswith("??")]

    print(f"\nTracked file modifications: {len(tracked_modifications)}")
    if tracked_modifications:
        for m in tracked_modifications:
            print(f"  WARNING: {m}")
    else:
        print("  PASS: Zero tracked source files modified.")

    # 3. Verify model_manager.py references default models
    with open(r"ai_service\model_manager.py", "r", encoding="utf-8") as f:
        mm_content = f.read()

    mm_checks = {
        "civicmodel_default": 'POTHOLE_MODEL_PATH = os.getenv("POTHOLE_MODEL_PATH", str(DEFAULT_MODEL_DIR / "civicmodel.pt"))' in mm_content,
        "best_default": 'WASTE_MODEL_PATH = os.getenv("WASTE_MODEL_PATH", str(DEFAULT_MODEL_DIR / "best.pt"))' in mm_content,
        "water_pipe_default": 'WATER_PIPE_MODEL_PATH = os.getenv("WATER_PIPE_MODEL_PATH", str(DEFAULT_MODEL_DIR / "water_pipe_model.pt"))' in mm_content,
        "drainage_default": 'DRAINAGE_MODEL_PATH = os.getenv("DRAINAGE_MODEL_PATH", str(DEFAULT_MODEL_DIR / "drainage_model.pt"))' in mm_content,
        "no_phase5_candidate_import": "water_pipe_candidate_v5" not in mm_content
    }

    print("\nModel Manager Safety Verification:")
    for k, v in mm_checks.items():
        print(f"  [{'PASS' if v else 'FAIL'}] {k}: {v}")

    # 4. Inventory Phase 5 files
    phase5_dir = r"ai_service\experiments\phase5"
    p5_files = []
    if os.path.exists(phase5_dir):
        for root, dirs, files in os.walk(phase5_dir):
            for file in files:
                rel = os.path.relpath(os.path.join(root, file), phase5_dir)
                sz = os.path.getsize(os.path.join(root, file))
                p5_files.append({"path": rel, "size_bytes": sz})

    audit_summary = {
        "timestamp": json.loads(json.dumps(os.environ.get("TIMESTAMP", "2026-11-02T23:45:00"))),
        "overall_status": "COMPLIANT" if (all_models_intact and not tracked_modifications and all(mm_checks.values())) else "VIOLATION",
        "production_models_audit": model_audit,
        "tracked_files_modified_count": len(tracked_modifications),
        "tracked_modifications": tracked_modifications,
        "model_manager_configuration": mm_checks,
        "phase5_isolated_files_count": len(p5_files),
        "phase5_file_inventory": p5_files
    }

    with open(AUDIT_OUTPUT_PATH, "w") as f:
        json.dump(audit_summary, f, indent=2)
    print(f"\nAudit report saved to: {AUDIT_OUTPUT_PATH}")

    return audit_summary

if __name__ == "__main__":
    res = run_safety_audit()
    if res["overall_status"] != "COMPLIANT":
        sys.exit(1)

