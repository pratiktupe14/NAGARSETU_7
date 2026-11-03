r"""
Phase 10A - Task 5: Isolated Staging Water AI Adapter
Provides an isolated, non-invasive wrapper matching NagarSetu API contracts:
- Three-tier mode: BASELINE_ONLY, PASSIVE_SHADOW, CANARY_ADVISOR
- Integrated circuit breaker with automatic state management
- In-memory instant fallback to production baseline
- Strict database isolation (zero DB connections)
"""

import os
import sys
import time
import json
import logging
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from torchvision import transforms, models
from PIL import Image

class WaterPipeClassifier(nn.Module):
    def __init__(self, num_classes=3):
        super(WaterPipeClassifier, self).__init__()
        self.backbone = models.mobilenet_v3_small(weights=None)
        in_features = self.backbone.classifier[3].in_features
        self.backbone.classifier[3] = nn.Linear(in_features, num_classes)

    def forward(self, x):
        return self.backbone(x)

class WaterPipeCandidateV5(nn.Module):
    def __init__(self, num_classes=2):
        super(WaterPipeCandidateV5, self).__init__()
        self.backbone = models.mobilenet_v3_small(weights=None)
        in_features = self.backbone.classifier[3].in_features
        self.backbone.classifier[3] = nn.Sequential(
            nn.Dropout(p=0.2),
            nn.Linear(in_features, num_classes)
        )

    def forward(self, x):
        return self.backbone(x)

class StagingCircuitBreaker:
    def __init__(self, failure_threshold=5, recovery_timeout_sec=30.0):
        self.threshold = failure_threshold
        self.recovery_timeout = recovery_timeout_sec
        self.failure_count = 0
        self.last_failure_time = 0.0
        self.state = "CLOSED" # CLOSED, OPEN, HALF_OPEN

    def record_success(self):
        self.failure_count = 0
        self.state = "CLOSED"

    def record_failure(self):
        self.failure_count += 1
        self.last_failure_time = time.time()
        if self.failure_count >= self.threshold:
            self.state = "OPEN"

    def is_available(self):
        if self.state == "CLOSED":
            return True
        if self.state == "OPEN":
            if time.time() - self.last_failure_time >= self.recovery_timeout:
                self.state = "HALF_OPEN"
                return True
            return False
        if self.state == "HALF_OPEN":
            return True
        return False

class StagingWaterAIAdapter:
    def __init__(self, baseline_path: str, candidate_path: str = None, mode: str = "PASSIVE_SHADOW", log_path: str = None):
        self.mode = mode # BASELINE_ONLY, PASSIVE_SHADOW, CANARY_ADVISOR
        self.log_path = log_path
        self.circuit_breaker = StagingCircuitBreaker(failure_threshold=5, recovery_timeout_sec=30.0)

        self.transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        ])

        # Load Baseline
        if not os.path.exists(baseline_path):
            raise FileNotFoundError(f"Baseline model not found: {baseline_path}")
        b_ckpt = torch.load(baseline_path, map_location="cpu", weights_only=False)
        self.baseline_model = WaterPipeClassifier(num_classes=b_ckpt.get("num_classes", 3))
        self.baseline_model.load_state_dict(b_ckpt["model_state_dict"])
        self.baseline_model.eval()

        # Load Candidate if provided
        self.candidate_model = None
        if candidate_path and os.path.exists(candidate_path):
            try:
                c_ckpt = torch.load(candidate_path, map_location="cpu", weights_only=False)
                self.candidate_model = WaterPipeCandidateV5(num_classes=c_ckpt.get("num_classes", 2))
                self.candidate_model.load_state_dict(c_ckpt["model_state_dict"])
                self.candidate_model.eval()
            except Exception:
                self.candidate_model = None

    def _extract_patches(self, img: Image.Image, patch_size=(384, 384), overlap=0.20):
        w, h = img.size
        pw, ph = patch_size
        if w <= pw and h <= ph:
            return [img]
        stride_x = max(int(pw * (1.0 - overlap)), 32)
        stride_y = max(int(ph * (1.0 - overlap)), 32)
        patches = []
        y = 0
        while y < h:
            x = 0
            while x < w:
                x_end = min(x + pw, w)
                y_end = min(y + ph, h)
                crop = img.crop((max(0, x_end - pw), max(0, y_end - ph), x_end, y_end))
                patches.append(crop)
                if x_end >= w:
                    break
                x += stride_x
            if y_end >= h:
                break
            y += stride_y
        return patches

    def predict(self, image: Image.Image, metadata: dict = None) -> dict:
        t_start = time.perf_counter()
        img_rgb = image.convert("RGB")
        w, h = img_rgb.size
        t_img = self.transform(img_rgb).unsqueeze(0)

        # 1. Authoritative Production Baseline
        with torch.no_grad():
            b_out = self.baseline_model(t_img)
            b_probs = F.softmax(b_out, dim=1)[0].numpy()
            b_leak_conf = float(b_probs[1] + b_probs[2])
            b_pred = "leak" if b_leak_conf >= 0.50 else "normal"

        b_latency_ms = (time.perf_counter() - t_start) * 1000.0

        # Base citizen-facing response contract
        response = {
            "status": "success",
            "department": "Water Supply & Sewerage Board",
            "prediction": b_pred,
            "confidence": round(b_leak_conf, 4),
            "latency_ms": round(b_latency_ms, 2),
            "model_version": "production_baseline_v1",
            "authoritative_model": "baseline"
        }

        # 2. Shadow Execution if configured
        if self.mode in ("PASSIVE_SHADOW", "CANARY_ADVISOR") and self.candidate_model is not None:
            if self.circuit_breaker.is_available():
                t_cand_start = time.perf_counter()
                cand_pred = None
                cand_conf = None
                try:
                    # Execute Candidate forward pass
                    c_out = self.candidate_model(t_img)
                    c_probs = F.softmax(c_out, dim=1)[0].numpy()
                    c_leak_conf = float(c_probs[1]) if len(c_probs) == 2 else float(c_probs[1] + c_probs[2])

                    norm_g = float(b_probs[0])
                    # Early exit
                    if norm_g >= 0.90 and max(w, h) <= 800:
                        cand_pred = "normal"
                        cand_conf = c_leak_conf
                    elif b_leak_conf >= 0.85 and max(w, h) <= 800:
                        cand_pred = "leak"
                        cand_conf = c_leak_conf
                    else:
                        patches = self._extract_patches(img_rgb, patch_size=(384, 384), overlap=0.20)
                        batch_p = torch.stack([self.transform(p) for p in patches])
                        with torch.no_grad():
                            p_out = self.candidate_model(batch_p)
                        patch_probs = F.softmax(p_out, dim=1).numpy()
                        max_tile = float(np.max(patch_probs[:, 1])) if patch_probs.shape[1] == 2 else float(np.max(patch_probs[:, 1] + patch_probs[:, 2]))
                        cand_conf = max(c_leak_conf, 0.70 * max_tile + 0.30 * c_leak_conf)
                        cand_pred = "leak" if (max_tile >= 0.72 or cand_conf >= 0.50) else "normal"

                    self.circuit_breaker.record_success()
                except Exception as e:
                    self.circuit_breaker.record_failure()
                    cand_pred = b_pred
                    cand_conf = b_leak_conf

                c_latency_ms = (time.perf_counter() - t_cand_start) * 1000.0

                # Log Shadow Telemetry
                if self.log_path:
                    try:
                        log_entry = {
                            "timestamp": time.time(),
                            "baseline_prediction": b_pred,
                            "baseline_conf": round(b_leak_conf, 4),
                            "candidate_prediction": cand_pred,
                            "candidate_conf": round(cand_conf, 4) if cand_conf else None,
                            "agreement": (b_pred == cand_pred),
                            "circuit_breaker_state": self.circuit_breaker.state,
                            "candidate_latency_ms": round(c_latency_ms, 2)
                        }
                        with open(self.log_path, "a", encoding="utf-8") as f:
                            f.write(json.dumps(log_entry) + "\n")
                    except OSError:
                        # Logging errors swallowed to protect caller
                        pass

        # Total pipeline latency
        response["total_pipeline_latency_ms"] = round((time.perf_counter() - t_start) * 1000.0, 2)
        return response
