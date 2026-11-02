"""
Drainage Model Adapter (Isolated & Non-Mutating)
Provides experimental candidate routing without altering default production model behavior.
"""

import os
import time
from pathlib import Path
from typing import Dict, Any, Optional
from PIL import Image
import torch
import torch.nn as nn
import torchvision.transforms as T
import torchvision.models as models

BASE_DIR = Path(__file__).resolve().parent.parent
MODEL_DIR = BASE_DIR / "model"

V1_MODEL_PATH = str(MODEL_DIR / "drainage_model.pt")
V2_MODEL_PATH = str(MODEL_DIR / "drainage_model_v2.pt")


class DrainageClassifier(nn.Module):
    """
    MobileNetV3-Small transfer backbone for civic drainage inspection.
    """
    def __init__(self, num_classes: int = 3):
        super().__init__()
        self.backbone = models.mobilenet_v3_small(weights=None)
        in_features = self.backbone.classifier[3].in_features
        self.backbone.classifier[3] = nn.Linear(in_features, num_classes)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.backbone(x)


class DrainageModelAdapter:
    """
    Isolated adapter for experimental drainage inference.
    Guarantees production default (v1) remains unchanged unless explicitly instantiated with version='v2'.
    """

    def __init__(self, version: str = "v1", device: str = "cpu"):
        self.version = version.lower()
        self.device = torch.device(device)
        self.classes = {0: "normal_drain", 1: "blocked_drain", 2: "damaged_drain"}
        self._model = None
        self._model_path = V2_MODEL_PATH if self.version == "v2" else V1_MODEL_PATH

        self.transform = T.Compose([
            T.Resize((224, 224)),
            T.ToTensor(),
            T.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        ])

        self._load_model()

    def _load_model(self):
        if not os.path.exists(self._model_path):
            raise FileNotFoundError(f"Model file not found: {self._model_path}")

        checkpoint = torch.load(self._model_path, map_location=self.device)
        num_classes = checkpoint.get("num_classes", 3)
        model = DrainageClassifier(num_classes=num_classes)
        model.load_state_dict(checkpoint["model_state_dict"])
        model.eval()
        self._model = model

    def predict(self, image: Image.Image, threshold: float = 0.45) -> Dict[str, Any]:
        """
        Runs isolated inference on a PIL image and returns standardized schema.
        """
        if self._model is None or image is None:
            return {"error": "Model or image unavailable"}

        t0 = time.perf_counter()
        rgb = image.convert("RGB")
        tensor = self.transform(rgb).unsqueeze(0).to(self.device)

        with torch.no_grad():
            outputs = self._model(tensor)
            probs = torch.softmax(outputs, dim=1)[0]
            score, pred_idx = torch.max(probs, dim=0)

        latency_ms = round((time.perf_counter() - t0) * 1000, 2)
        score_val = float(score.item())
        pred_val = int(pred_idx.item())

        p_norm = round(float(probs[0].item()), 4)
        p_block = round(float(probs[1].item()), 4)
        p_dam = round(float(probs[2].item()), 4)
        raw_pred_class = self.classes.get(pred_val, "blocked_drain")

        # Two-stage Decision Logic
        if p_norm >= 0.50 and p_norm > p_block and p_norm > p_dam:
            final_class = "normal_drain"
            final_conf = p_norm
            ai_status = "confirmed_normal"
            detected = False
            review_required = False
            decision_case = "CASE_A_NORMAL_DRAIN"
        elif p_dam >= 0.50 and p_dam > p_norm:
            final_class = "damaged_drain"
            final_conf = p_dam
            ai_status = "confirmed" if p_dam >= 0.70 else "suggested"
            detected = True
            review_required = bool(p_dam < 0.70)
            decision_case = "CASE_B_CLEAR_DAMAGED_DRAIN"
        elif p_block >= 0.45 and p_block > p_norm:
            final_class = "blocked_drain"
            final_conf = p_block
            ai_status = "confirmed" if p_block >= 0.70 else "suggested"
            detected = True
            review_required = bool(p_block < 0.70)
            decision_case = "CASE_C_CLEAR_BLOCKED_DRAIN"
        else:
            final_class = raw_pred_class
            final_conf = score_val
            ai_status = "suggested"
            detected = (final_class != "normal_drain")
            review_required = True
            decision_case = "CASE_FALLBACK"

        return {
            "version": self.version,
            "model_path": self._model_path,
            "class": final_class,
            "confidence": round(final_conf, 4),
            "predicted_class": raw_pred_class,
            "probabilities": {
                "normal_drain": p_norm,
                "blocked_drain": p_block,
                "damaged_drain": p_dam
            },
            "detected": detected,
            "ai_status": ai_status,
            "review_required": review_required,
            "decision_case": decision_case,
            "latency_ms": latency_ms
        }

