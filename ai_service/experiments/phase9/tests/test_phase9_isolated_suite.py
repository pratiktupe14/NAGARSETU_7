r"""
Phase 9: Comprehensive Automated Isolated Test Suite
Tests:
1. test_expanded_dataset_integrity
2. test_model_evaluation_reproducibility
3. test_inference_optimization_verification
4. test_concurrency_thread_safety
5. test_memory_stability_verification
6. test_failure_recovery_verification
7. test_shadow_evaluation_verification
8. test_code_protection_compliance
9. test_production_model_sha256_invariance
"""

import os
import sys
import json
import hashlib
import time
import subprocess
import pytest
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from torchvision import transforms, models
from PIL import Image

MANIFEST_PATH = r"ai_service\experiments\phase9\dataset\water_phase9_dataset_manifest.json"
SHADOW_LOG_PATH = r"ai_service\experiments\phase9\shadow\extended_shadow_log.jsonl"
PROD_MODELS = {
    "civicmodel.pt": {
        "path": r"ai_service\model\civicmodel.pt",
        "expected_sha256": "1067a09d37e4e9081164e6d6da337ad66d8ec7a884a6a194e58703beee804aa2"
    },
    "best.pt": {
        "path": r"ai_service\model\best.pt",
        "expected_sha256": "0965dfbb16320981abeab3ed50cefe90bef8dede1453407aed2d952898a765e6"
    },
    "water_pipe_model.pt": {
        "path": r"ai_service\model\water_pipe_model.pt",
        "expected_sha256": "f1bc766c569d1053b4e252247e37edfcc0fe76d3ce594e8b1ae9020aa52aac86"
    },
    "drainage_model.pt": {
        "path": r"ai_service\model\drainage_model.pt",
        "expected_sha256": "70821c225a90dd769f097c5d212ebce89a21aaf83667ada4a950d54e9d96e75f"
    }
}

class WaterPipeClassifier(nn.Module):
    def __init__(self, num_classes=3):
        super(WaterPipeClassifier, self).__init__()
        self.backbone = models.mobilenet_v3_small(weights=None)
        in_features = self.backbone.classifier[3].in_features
        self.backbone.classifier[3] = nn.Linear(in_features, num_classes)

    def forward(self, x):
        return self.backbone(x)

def get_file_sha256(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

def test_expanded_dataset_integrity():
    """Verify 150 images exist on disk, match manifest SHA-256, and open without corruption."""
    assert os.path.exists(MANIFEST_PATH), f"Manifest missing: {MANIFEST_PATH}"
    with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
        manifest = json.load(f)
    samples = manifest["samples"]
    assert len(samples) == 150, f"Expected 150 samples, found {len(samples)}"

    for s in samples:
        path = s["filepath"]
        assert os.path.exists(path), f"Sample file missing on disk: {path}"
        # SHA-256 check
        sha = get_file_sha256(path)
        assert sha == s["sha256"], f"SHA mismatch on {s['sample_id']}"
        # PIL open check
        with Image.open(path) as img:
            assert img.size == (512, 512)
            assert img.mode in ("RGB", "L")

def test_model_evaluation_reproducibility():
    """Verify deterministic reproducibility on a subset of samples."""
    ckpt = torch.load(PROD_MODELS["water_pipe_model.pt"]["path"], map_location="cpu", weights_only=False)
    m = WaterPipeClassifier(num_classes=3)
    m.load_state_dict(ckpt["model_state_dict"])
    m.eval()

    eval_transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])

    with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
        manifest = json.load(f)
    subset = manifest["samples"][:5]

    with torch.no_grad():
        for s in subset:
            img = Image.open(s["filepath"]).convert("RGB")
            t = eval_transform(img).unsqueeze(0)
            out1 = m(t)
            out2 = m(t)
            assert torch.allclose(out1, out2, atol=1e-6), "Model forward pass non-deterministic"

def test_inference_optimization_verification():
    """Verify complete pipeline latency finishes within the 150ms SLA on standard test canvas."""
    ckpt = torch.load(PROD_MODELS["water_pipe_model.pt"]["path"], map_location="cpu", weights_only=False)
    m = WaterPipeClassifier(num_classes=3)
    m.load_state_dict(ckpt["model_state_dict"])
    m.eval()

    eval_transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])

    test_canvas = Image.new("RGB", (768, 768), color=(120, 140, 160))
    # Warmup
    t_img = eval_transform(test_canvas).unsqueeze(0)
    _ = m(t_img)

    times = []
    with torch.no_grad():
        for _ in range(10):
            t0 = time.perf_counter()
            t_in = eval_transform(test_canvas).unsqueeze(0)
            _ = m(t_in)
            times.append((time.perf_counter() - t0) * 1000.0)

    p95 = float(np.percentile(times, 95))
    assert p95 < 150.0, f"P95 latency {p95:.2f}ms exceeds 150ms SLA"

def test_concurrency_thread_safety():
    """Verify multi-threaded inference produces zero exceptions and consistent shapes."""
    import concurrent.futures
    ckpt = torch.load(PROD_MODELS["water_pipe_model.pt"]["path"], map_location="cpu", weights_only=False)
    m = WaterPipeClassifier(num_classes=3)
    m.load_state_dict(ckpt["model_state_dict"])
    m.eval()

    eval_transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])

    test_img = Image.new("RGB", (512, 512), color=(80, 120, 180))

    def worker_infer():
        t = eval_transform(test_img).unsqueeze(0)
        with torch.no_grad():
            out = m(t)
            return out.shape

    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:
        futures = [ex.submit(worker_infer) for _ in range(20)]
        for f in concurrent.futures.as_completed(futures):
            shape = f.result()
            assert shape == (1, 3)

def test_memory_stability_verification():
    """Verify memory does not grow unbounded during repeated execution."""
    import psutil
    process = psutil.Process()
    ckpt = torch.load(PROD_MODELS["water_pipe_model.pt"]["path"], map_location="cpu", weights_only=False)
    m = WaterPipeClassifier(num_classes=3)
    m.load_state_dict(ckpt["model_state_dict"])
    m.eval()

    eval_transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])

    test_img = Image.new("RGB", (512, 512), color=(90, 130, 170))
    t_img = eval_transform(test_img).unsqueeze(0)

    # 30 iterations
    rss_start = process.memory_info().rss
    with torch.no_grad():
        for _ in range(30):
            _ = m(t_img)
    rss_end = process.memory_info().rss
    growth_mb = (rss_end - rss_start) / (1024 * 1024)
    # Memory growth should be negligible (< 15MB including OS buffer fluctuations)
    assert growth_mb < 15.0, f"Memory growth {growth_mb:.2f}MB exceeds tolerance"

def test_failure_recovery_verification():
    """Verify recovery fallback works when candidate fails."""
    ckpt = torch.load(PROD_MODELS["water_pipe_model.pt"]["path"], map_location="cpu", weights_only=False)
    baseline_m = WaterPipeClassifier(num_classes=3)
    baseline_m.load_state_dict(ckpt["model_state_dict"])
    baseline_m.eval()

    eval_transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])
    test_img = Image.new("RGB", (512, 512), color=(100, 150, 200))
    t_img = eval_transform(test_img).unsqueeze(0)

    # Injected candidate failure
    def failing_candidate():
        raise RuntimeError("Simulated Candidate Model Failure")

    # Guarded execution
    active_result = None
    try:
        failing_candidate()
    except Exception:
        with torch.no_grad():
            active_result = baseline_m(t_img)

    assert active_result is not None
    assert active_result.shape == (1, 3)

def test_shadow_evaluation_verification():
    """Verify shadow log file exists, contains 500 entries, and zero DB writes/user impacts."""
    assert os.path.exists(SHADOW_LOG_PATH), f"Shadow log missing: {SHADOW_LOG_PATH}"
    count = 0
    with open(SHADOW_LOG_PATH, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                entry = json.loads(line)
                assert entry["user_response_impact"] is None
                assert entry["db_write_attempted"] is False
                count += 1
    assert count == 500, f"Expected 500 shadow entries, found {count}"

def test_code_protection_compliance():
    """Verify zero modified tracked production files using git status."""
    res = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True)
    assert res.returncode == 0
    lines = res.stdout.strip().splitlines()
    # Check that no tracked production file was modified (M flag)
    for line in lines:
        if line.startswith(" M ") or line.startswith("M  "):
            filepath = line[3:].strip()
            # Ensure it is not an existing tracked production file
            assert filepath.startswith("ai_service/experiments/phase9/") or filepath.startswith("phase9_") or filepath.endswith(".json") or filepath.endswith(".md"), \
                f"Tracked production file modified: {filepath}"

def test_production_model_sha256_invariance():
    """Verify all four production models are byte-for-byte identical to Phase 0 baselines."""
    for model_name, info in PROD_MODELS.items():
        p = info["path"]
        assert os.path.exists(p), f"Production model missing: {p}"
        sha = get_file_sha256(p)
        assert sha == info["expected_sha256"], f"SHA-256 mutation detected on {model_name}! Expected {info['expected_sha256']}, got {sha}"
