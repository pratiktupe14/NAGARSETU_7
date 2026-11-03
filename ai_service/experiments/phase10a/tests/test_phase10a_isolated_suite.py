r"""
Phase 10A: Isolated Unit & Regression Test Suite
Tests:
1. test_dataset_provenance_manifest
2. test_model_evaluation_metrics
3. test_promotion_gates_audit
4. test_shadow_audit_metrics
5. test_staging_adapter_predict
6. test_circuit_breaker_tripping
7. test_production_model_hashes
"""

import os
import sys
import json
import hashlib
import pytest
from PIL import Image

PROV_MANIFEST = r"ai_service\experiments\phase10a\provenance\water_phase10a_verified_manifest.json"
EVAL_JSON = r"ai_service\experiments\phase10a\evaluation\water_phase10a_evaluation_results.json"
GATES_JSON = r"ai_service\experiments\phase10a\gates\promotion_gates_audit.json"
SHADOW_JSON = r"ai_service\experiments\phase10a\shadow_audit\shadow_evaluation_forensic_audit.json"
STAGING_JSON = r"ai_service\experiments\phase10a\staging\staging_test_results.json"

PROD_MODELS = {
    "civicmodel.pt": "1067a09d37e4e9081164e6d6da337ad66d8ec7a884a6a194e58703beee804aa2",
    "best.pt": "0965dfbb16320981abeab3ed50cefe90bef8dede1453407aed2d952898a765e6",
    "water_pipe_model.pt": "f1bc766c569d1053b4e252247e37edfcc0fe76d3ce594e8b1ae9020aa52aac86",
    "drainage_model.pt": "70821c225a90dd769f097c5d212ebce89a21aaf83667ada4a950d54e9d96e75f"
}

def get_file_sha256(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

def test_dataset_provenance_manifest():
    assert os.path.exists(PROV_MANIFEST)
    with open(PROV_MANIFEST, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert len(data["samples"]) == 150
    assert data["provenance_summary"]["unique_parent_source_photos"] == 78
    assert data["provenance_summary"]["recycled_parent_crops"] == 66

def test_model_evaluation_metrics():
    assert os.path.exists(EVAL_JSON)
    with open(EVAL_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)
    base_acc = data["overall_metrics"]["production_baseline"]["accuracy"]
    cand_acc = data["overall_metrics"]["candidate_v5_fp32"]["accuracy"]
    assert base_acc == 0.96
    assert cand_acc == 0.94
    assert cand_acc < base_acc # Acc regressed by 2 percentage points

def test_promotion_gates_audit():
    assert os.path.exists(GATES_JSON)
    with open(GATES_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data["P1_statistical_performance"]["status"] == "FAIL"
    assert data["P2_multi_scenario_coverage"]["status"] == "FAIL"
    assert data["P3_deterministic_latency"]["status"] == "PASS"
    assert data["P4_memory_and_stability"]["status"] == "PASS"
    assert data["P5_shadow_evaluation"]["status"] == "PASS"
    assert data["P6_fault_tolerance"]["status"] == "PASS"
    assert "FAIL" in data["P7_governance_and_rollback"]["status"]

def test_shadow_audit_metrics():
    assert os.path.exists(SHADOW_JSON)
    with open(SHADOW_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data["total_shadow_requests"] == 500
    assert data["agreement_metrics"]["agreement_rate_pct"] == 98.6
    assert data["safety_and_isolation_audit"]["candidate_crashes"] == 0
    assert data["safety_and_isolation_audit"]["database_write_attempts"] == 0

def test_staging_adapter_predict():
    staging_path = r"ai_service\experiments\phase10a\staging"
    sys.path.insert(0, os.path.abspath(staging_path))
    from staging_water_adapter import StagingWaterAIAdapter

    adapter = StagingWaterAIAdapter(
        baseline_path=r"ai_service\model\water_pipe_model.pt",
        candidate_path=r"ai_service\experiments\phase5\water_training\water_pipe_candidate_v5.pt",
        mode="PASSIVE_SHADOW"
    )
    img = Image.new("RGB", (256, 256), color=(100, 150, 200))
    resp = adapter.predict(img)
    assert resp["status"] == "success"
    assert resp["authoritative_model"] == "baseline"
    assert resp["prediction"] in ("leak", "normal")

def test_circuit_breaker_tripping():
    staging_path = r"ai_service\experiments\phase10a\staging"
    sys.path.insert(0, os.path.abspath(staging_path))
    from staging_water_adapter import StagingCircuitBreaker

    cb = StagingCircuitBreaker(failure_threshold=5, recovery_timeout_sec=30.0)
    for _ in range(4):
        cb.record_failure()
    assert cb.state == "CLOSED"
    cb.record_failure()
    assert cb.state == "OPEN"
    assert not cb.is_available()

def test_production_model_hashes():
    for name, exp_sha in PROD_MODELS.items():
        p = os.path.join("ai_service", "model", name)
        assert os.path.exists(p)
        sha = get_file_sha256(p)
        assert sha == exp_sha, f"Hash mismatch on {name}: {sha} vs {exp_sha}"
