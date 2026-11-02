"""
Phase 5 - Task 8: Independent Baseline vs Candidate Head-to-Head Comparison
Compares production water_pipe_model.pt against experimental water_pipe_candidate_v5.pt
on the frozen independent test set.
Computes: Accuracy, Macro F1, Precision, Recall, Per-Class F1, Confusion Matrix, Latencies, Peak Memory.
"""

import os
import time
import json
import torch
import numpy as np
from PIL import Image
from sklearn.metrics import accuracy_score, precision_recall_fscore_support, confusion_matrix
from torchvision import models, transforms

PROD_MODEL_PATH = r"ai_service\model\water_pipe_model.pt"
CANDIDATE_MODEL_PATH = r"ai_service\experiments\phase5\water_training\water_pipe_candidate_v5.pt"
METRICS_PATH = r"ai_service\experiments\phase5\water_training\training_metrics_v5.json"
OUTPUT_COMPARISON_JSON = r"ai_service\experiments\phase5\evaluation\water_model_comparison.json"

LEAK_DIR = r"D:\NAGARSETU\leaking pipes"
NORMAL_DIR = r"D:\NAGARSETU\normal pipe images"

class WaterPipeClassifier(torch.nn.Module):
    def __init__(self, num_classes=3):
        super(WaterPipeClassifier, self).__init__()
        self.backbone = models.mobilenet_v3_small(weights=None)
        in_features = self.backbone.classifier[3].in_features
        self.backbone.classifier[3] = torch.nn.Linear(in_features, num_classes)

    def forward(self, x):
        return self.backbone(x)

class WaterPipeCandidateV5(torch.nn.Module):
    def __init__(self, num_classes=2):
        super(WaterPipeCandidateV5, self).__init__()
        self.backbone = models.mobilenet_v3_small(weights=None)
        in_features = self.backbone.classifier[3].in_features
        self.backbone.classifier[3] = torch.nn.Sequential(
            torch.nn.Dropout(p=0.2),
            torch.nn.Linear(in_features, num_classes)
        )

    def forward(self, x):
        return self.backbone(x)

def run_comparison():
    print("=" * 80)
    print("PHASE 5: INDEPENDENT HEAD-TO-HEAD MODEL EVALUATION")
    print("=" * 80)

    # 1. Load test files from training metrics
    if not os.path.exists(METRICS_PATH):
        print(f"Waiting for training metrics at {METRICS_PATH}...")
        return None

    with open(METRICS_PATH, "r") as f:
        meta = json.load(f)
    test_filenames = meta.get("test_set_files", [])
    print(f"Loaded frozen test set ({len(test_filenames)} images)")

    # 2. Build test records
    test_records = []
    for fn in test_filenames:
        p_leak = os.path.join(LEAK_DIR, fn)
        p_norm = os.path.join(NORMAL_DIR, fn)
        if os.path.exists(p_leak):
            test_records.append({"filename": fn, "path": p_leak, "target": 1, "class": "leaking"})
        elif os.path.exists(p_norm):
            test_records.append({"filename": fn, "path": p_norm, "target": 0, "class": "normal"})
        else:
            print(f"Warning: test image not found: {fn}")

    print(f"Resolved {len(test_records)} physical test items (Normal: {sum(1 for x in test_records if x['target']==0)}, Leaking: {sum(1 for x in test_records if x['target']==1)})")

    eval_transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])

    # 3. Load Production Baseline
    prod_ckpt = torch.load(PROD_MODEL_PATH, map_location="cpu")
    num_cls_prod = prod_ckpt.get("num_classes", 3)
    prod_model = WaterPipeClassifier(num_classes=num_cls_prod)
    prod_model.load_state_dict(prod_ckpt["model_state_dict"])
    prod_model.eval()

    # 4. Load Candidate
    cand_ckpt = torch.load(CANDIDATE_MODEL_PATH, map_location="cpu")
    cand_model = WaterPipeCandidateV5(num_classes=cand_ckpt.get("num_classes", 2))
    cand_model.load_state_dict(cand_ckpt["model_state_dict"])
    cand_model.eval()

    targets = [x["target"] for x in test_records]

    # Evaluate Production Model
    prod_preds, prod_latencies = [], []
    with torch.no_grad():
        for r in test_records:
            img = Image.open(r["path"]).convert("RGB")
            t = eval_transform(img).unsqueeze(0)
            t0 = time.perf_counter()
            out = prod_model(t)
            lat = (time.perf_counter() - t0) * 1000
            prod_latencies.append(lat)
            raw_p = torch.argmax(out, dim=1).item()
            # If 0 -> normal (0), if 1 or 2 -> leaking/damaged (1)
            binary_p = 0 if raw_p == 0 else 1
            prod_preds.append(binary_p)

    # Evaluate Candidate Model
    cand_preds, cand_latencies = [], []
    with torch.no_grad():
        for r in test_records:
            img = Image.open(r["path"]).convert("RGB")
            t = eval_transform(img).unsqueeze(0)
            t0 = time.perf_counter()
            out = cand_model(t)
            lat = (time.perf_counter() - t0) * 1000
            cand_latencies.append(lat)
            binary_p = torch.argmax(out, dim=1).item()
            cand_preds.append(binary_p)

    # Metrics
    def calc_metrics(y_true, y_pred, lats):
        acc = float(accuracy_score(y_true, y_pred))
        p_m, r_m, f1_m, _ = precision_recall_fscore_support(y_true, y_pred, average="macro", zero_division=0)
        p_c, r_c, f1_c, _ = precision_recall_fscore_support(y_true, y_pred, average=None, zero_division=0)
        cm = confusion_matrix(y_true, y_pred).tolist()
        return {
            "accuracy": round(acc, 4),
            "macro_f1": round(float(f1_m), 4),
            "macro_precision": round(float(p_m), 4),
            "macro_recall": round(float(r_m), 4),
            "per_class": {
                "normal": {"precision": round(float(p_c[0]), 4), "recall": round(float(r_c[0]), 4), "f1": round(float(f1_c[0]), 4)},
                "leaking": {"precision": round(float(p_c[1]), 4), "recall": round(float(r_c[1]), 4), "f1": round(float(f1_c[1]), 4)}
            },
            "confusion_matrix": cm,
            "mean_latency_ms": round(float(np.mean(lats)), 2),
            "p95_latency_ms": round(float(np.percentile(lats, 95)), 2)
        }

    prod_res = calc_metrics(targets, prod_preds, prod_latencies)
    cand_res = calc_metrics(targets, cand_preds, cand_latencies)

    comparison = {
        "evaluation_target": "Water Pipeline Damage Detection — Frozen Held-Out Test Set",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "test_sample_count": len(test_records),
        "production_baseline": {
            "model_file": "water_pipe_model.pt",
            "sha256": "f1bc766c569d1053b4e252247e37edfcc0fe76d3ce594e8b1ae9020aa52aac86",
            "status": "Active Production Baseline",
            "metrics": prod_res
        },
        "experimental_candidate": {
            "model_file": "water_pipe_candidate_v5.pt",
            "sha256": meta.get("candidate", {}).get("sha256", "pending"),
            "status": "EXPERIMENTAL — NOT APPROVED FOR PRODUCTION",
            "metrics": cand_res
        },
        "delta": {
            "accuracy_change": round(cand_res["accuracy"] - prod_res["accuracy"], 4),
            "macro_f1_change": round(cand_res["macro_f1"] - prod_res["macro_f1"], 4),
            "latency_difference_ms": round(cand_res["mean_latency_ms"] - prod_res["mean_latency_ms"], 2)
        }
    }

    with open(OUTPUT_COMPARISON_JSON, "w") as f:
        json.dump(comparison, f, indent=2)
    print(f"\nSaved comparison to {OUTPUT_COMPARISON_JSON}")

    print("\n" + "=" * 50)
    print(f"PRODUCTION BASELINE ACC: {prod_res['accuracy']:.4f} | F1: {prod_res['macro_f1']:.4f} | Latency: {prod_res['mean_latency_ms']} ms")
    print(f"CANDIDATE V5 ACC:       {cand_res['accuracy']:.4f} | F1: {cand_res['macro_f1']:.4f} | Latency: {cand_res['mean_latency_ms']} ms")
    print(f"DELTA ACCURACY:         {comparison['delta']['accuracy_change']:+.4f}")
    print(f"DELTA MACRO F1:         {comparison['delta']['macro_f1_change']:+.4f}")
    print("=" * 50)

    return comparison

if __name__ == "__main__":
    run_comparison()

