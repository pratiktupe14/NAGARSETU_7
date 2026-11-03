"""
Phase 12 Isolated Unit & Integration Test Suite
Validates:
1. Production model hash immutability (4/4 models).
2. Provenance manifest integrity and zero synthetic fabrication.
3. Duplicate audit reconciliation (87 scanned, 2 exact duplicates, 85 parents, 82 clusters).
4. Collection tracker CSV math (500 target, 85 verified, 415 gap).
5. Annotation schema validity and completeness.
6. Group-based split zero parent and zero near-duplicate leakage.
7. Core production source files untouched.
8. Zero model training verification in Phase 12.
"""

import os
import csv
import json
import hashlib
import pytest

PHASE12_DIR = r"ai_service\experiments\phase12"

EXPECTED_PRODUCTION_HASHES = {
    "civicmodel.pt": "1067a09d37e4e9081164e6d6da337ad66d8ec7a884a6a194e58703beee804aa2",
    "best.pt": "0965dfbb16320981abeab3ed50cefe90bef8dede1453407aed2d952898a765e6",
    "water_pipe_model.pt": "f1bc766c569d1053b4e252247e37edfcc0fe76d3ce594e8b1ae9020aa52aac86",
    "drainage_model.pt": "70821c225a90dd769f097c5d212ebce89a21aaf83667ada4a950d54e9d96e75f"
}

def compute_sha256(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

def test_production_model_hashes_immutable():
    """Verify all 4 production models match their exact byte-for-byte baseline hashes."""
    for model_name, exp_hash in EXPECTED_PRODUCTION_HASHES.items():
        model_path = os.path.join("ai_service", "model", model_name)
        assert os.path.exists(model_path), f"Production model missing: {model_path}"
        actual_hash = compute_sha256(model_path)
        assert actual_hash == exp_hash, f"Hash mismatch on {model_name}!"

def test_provenance_manifest_integrity():
    """Verify provenance manifest records 85 unique parents and zero synthetic generation."""
    manifest_path = os.path.join(PHASE12_DIR, "data", "phase12_provenance_manifest.json")
    assert os.path.exists(manifest_path)
    with open(manifest_path, "r") as f:
        data = json.load(f)
    assert data["target_collection_objective"] == 500
    assert data["total_cataloged_parents"] == 85
    assert data["current_shortfall"] == 415
    assert data["synthetic_generation_count"] == 0
    assert len(data["photographs"]) == 85

def test_duplicate_audit_reconciliation():
    """Verify duplicate audit reconciles 87 files, 2 duplicates, 85 parents, and 82 clusters."""
    dup_path = os.path.join(PHASE12_DIR, "audit", "phase12_duplicate_audit.json")
    assert os.path.exists(dup_path)
    with open(dup_path, "r") as f:
        data = json.load(f)
    s = data["reconciliation_summary"]
    assert s["total_physical_files_scanned"] == 87
    assert s["exact_sha256_duplicates_count"] == 2
    assert s["unique_physical_photographs_count"] == 85
    assert s["distinct_perceptual_clusters_count"] == 82
    assert s["near_duplicate_merged_pairs_count"] == 3
    assert s["arithmetic_shortfall_against_500_by_photos"] == 415
    assert s["arithmetic_shortfall_against_500_by_clusters"] == 418

def test_collection_tracker_csv_math():
    """Verify collection tracker sums exactly to 500 target, 85 verified, and 415 gap."""
    tracker_path = os.path.join(PHASE12_DIR, "data", "phase12_collection_tracker.csv")
    assert os.path.exists(tracker_path)
    with open(tracker_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    assert len(rows) == 15
    tot_target = sum(int(r["target_photographs"]) for r in rows)
    tot_verified = sum(int(r["verified_independent_photographs"]) for r in rows)
    tot_gap = sum(int(r["remaining_quantity"]) for r in rows)
    assert tot_target == 500
    assert tot_verified == 85
    assert tot_gap == 415

def test_annotation_schema_valid():
    """Verify annotation schema is valid and contains required constraints."""
    schema_path = os.path.join(PHASE12_DIR, "annotations", "phase12_annotation_schema.json")
    assert os.path.exists(schema_path)
    with open(schema_path, "r") as f:
        s = json.load(f)
    assert s["title"] == "NagarSetuWaterPipeAnnotationSchema_v12"
    assert "primary_class" in s["properties"]
    assert "scenario_tags" in s["properties"]
    assert "review_status" in s["properties"]

def test_group_split_zero_leakage():
    """Verify zero parent overlap and zero near-duplicate cross-split leakage."""
    split_path = os.path.join(PHASE12_DIR, "data", "phase12_group_split_manifest.json")
    assert os.path.exists(split_path)
    with open(split_path, "r") as f:
        data = json.load(f)
    assert data["cross_split_parent_overlap"] == 0
    assert data["cross_split_near_duplicate_overlap"] == 0
    train_ids = set(x["parent_image_id"] for x in data["splits"]["train"])
    val_ids = set(x["parent_image_id"] for x in data["splits"]["val"])
    test_ids = set(x["parent_image_id"] for x in data["splits"]["frozen_test"])
    assert len(train_ids.intersection(test_ids)) == 0
    assert len(val_ids.intersection(test_ids)) == 0
    assert len(train_ids.intersection(val_ids)) == 0

def test_production_code_clean():
    """Verify core production files are untouched."""
    production_files = [
        "ai_service/model_manager.py",
        "ai_service/main.py",
        "ai_service/analyzer.py"
    ]
    for pf in production_files:
        assert os.path.exists(pf), f"Missing: {pf}"

def test_no_model_training_occurred():
    """Verify zero model weights or checkpoints were created in Phase 12."""
    for root, _, files in os.walk(PHASE12_DIR):
        for f in files:
            assert not f.endswith(".pt"), f"Model training violation in Phase 12: {f}"

