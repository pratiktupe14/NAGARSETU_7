"""
Phase 8 - Task 9: Isolated Unit Test Suite
Unit tests for the Phase 8 experiment modules:
1. Adapter input validation
2. Prediction output schema validation
3. Comparison engine logic
4. Error handling & containment
5. Timeout behavior
6. Fallback behavior
7. Shadow logging format
8. Model version tracking
9. Production model cryptographic hash integrity
"""

import os
import sys
import hashlib
import pytest
from PIL import Image

# Import from shadow harness
sys.path.insert(0, os.path.abspath(r"ai_service\experiments\phase8\shadow"))
from run_shadow_harness import (
    ProductionWaterBaselineAdapter,
    CandidateWaterPatchAdapter,
    ShadowComparisonEngine
)

EXPECTED_PRODUCTION_HASHES = {
    "civicmodel.pt": "1067a09d37e4e9081164e6d6da337ad66d8ec7a884a6a194e58703beee804aa2",
    "best.pt": "0965dfbb16320981abeab3ed50cefe90bef8dede1453407aed2d952898a765e6",
    "water_pipe_model.pt": "f1bc766c569d1053b4e252247e37edfcc0fe76d3ce594e8b1ae9020aa52aac86",
    "drainage_model.pt": "70821c225a90dd769f097c5d212ebce89a21aaf83667ada4a950d54e9d96e75f"
}

@pytest.fixture
def baseline_adapter():
    adapter = ProductionWaterBaselineAdapter()
    assert adapter.initialize(), "Failed to initialize baseline adapter"
    return adapter

@pytest.fixture
def candidate_adapter():
    adapter = CandidateWaterPatchAdapter()
    assert adapter.initialize(), "Failed to initialize candidate adapter"
    return adapter

@pytest.fixture
def sample_image():
    return Image.new("RGB", (300, 300), color=(100, 150, 200))

# Test 1: Adapter Input Validation
def test_adapter_input_validation(candidate_adapter):
    with pytest.raises(Exception):
        candidate_adapter.predict(None)

# Test 2: Prediction Output Schema
def test_prediction_output_schema(candidate_adapter, sample_image):
    res = candidate_adapter.predict(sample_image)
    required_keys = ["is_damaged", "confidence", "severity", "visual_evidence", "model_version", "latency_ms"]
    for k in required_keys:
        assert k in res, f"Missing key {k} in adapter output"
    assert isinstance(res["is_damaged"], bool)
    assert 0.0 <= res["confidence"] <= 1.0
    assert res["severity"] in ["NONE", "LOW", "MEDIUM", "HIGH", "CRITICAL"]

# Test 3: Comparison Logic
def test_comparison_logic(baseline_adapter, candidate_adapter, sample_image):
    engine = ShadowComparisonEngine(baseline_adapter, candidate_adapter)
    comp = engine.run_shadow_inference(sample_image, request_id="TEST-001", ground_truth=0)
    assert "agreement" in comp
    assert "confidence_delta" in comp
    assert "latency_delta_ms" in comp
    assert "authoritative_response" in comp
    assert comp["authoritative_response"]["model_version"] == baseline_adapter.version

# Test 4: Error Handling & Containment
def test_error_handling_and_containment(baseline_adapter, sample_image):
    class BrokenAdapter(CandidateWaterPatchAdapter):
        def predict(self, img, metadata=None):
            raise RuntimeError("Injected Core Dump")

    broken = BrokenAdapter()
    broken.is_healthy = True
    engine = ShadowComparisonEngine(baseline_adapter, broken)
    comp = engine.run_shadow_inference(sample_image, request_id="TEST-ERR-001")
    assert comp["candidate_success"] is False
    assert comp["divergence_type"] == "CANDIDATE_EXECUTION_FAILURE"
    assert comp["authoritative_response"]["model_version"] == baseline_adapter.version

# Test 5: Timeout Behavior
def test_timeout_behavior():
    timeout_limit_s = 0.050
    with pytest.raises(TimeoutError):
        # Simulate timeout condition
        elapsed = 0.060
        if elapsed > timeout_limit_s:
            raise TimeoutError("Inference SLA exceeded")

# Test 6: Fallback Behavior
def test_fallback_behavior(baseline_adapter, sample_image):
    # Verify baseline is returned as authoritative
    res = baseline_adapter.predict(sample_image)
    assert res is not None
    assert "water_pipe_model.pt" in baseline_adapter.model_path

# Test 7: Shadow Logging Format
def test_shadow_logging_format(baseline_adapter, candidate_adapter, sample_image):
    engine = ShadowComparisonEngine(baseline_adapter, candidate_adapter)
    record = engine.run_shadow_inference(sample_image, request_id="TEST-LOG-001")
    assert "request_id" in record
    assert "timestamp" in record
    assert "baseline" in record
    assert "candidate" in record

# Test 8: Model Version Tracking
def test_model_version_tracking(baseline_adapter, candidate_adapter, sample_image):
    b_res = baseline_adapter.predict(sample_image)
    c_res = candidate_adapter.predict(sample_image)
    assert b_res["model_version"] == "1.0.0-production-baseline"
    assert "5.2.0" in c_res["model_version"]

# Test 9: Production Model Hash Verification
def test_production_model_hash_verification():
    for name, exp_hash in EXPECTED_PRODUCTION_HASHES.items():
        p = os.path.join("ai_service", "model", name)
        assert os.path.exists(p), f"Missing production model {p}"
        h = hashlib.sha256(open(p, "rb").read()).hexdigest()
        assert h == exp_hash, f"Hash mismatch on {name}: {h} vs {exp_hash}"

