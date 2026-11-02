"""
PHASE 3 — TASK 1: DRAINAGE EVALUATION REPRODUCIBILITY & INCONSISTENCY RESOLUTION
Runs identical frozen test samples and identical preprocessing on both drainage_model.pt
and drainage_model_v2.pt, evaluating simultaneously against:
  1. drainage_catalog.json (Ground Truth Source A — Phase 2 baseline)
  2. drainage_annotations_reviewed.json (Ground Truth Source B — Phase 1 baseline)
"""

import os
import json
import time
from typing import Dict, Any, List
import torch
import torch.nn as nn
from PIL import Image
import torchvision.transforms as T
import torchvision.models as models

class DrainageClassifier(nn.Module):
    def __init__(self, num_classes: int = 3):
        super().__init__()
        self.backbone = models.mobilenet_v3_small(weights=None)
        in_features = self.backbone.classifier[3].in_features
        self.backbone.classifier[3] = nn.Linear(in_features, num_classes)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.backbone(x)

def load_model(path: str) -> nn.Module:
    cp = torch.load(path, map_location="cpu")
    num_cls = cp.get("num_classes", 3)
    m = DrainageClassifier(num_classes=num_cls)
    m.load_state_dict(cp["model_state_dict"])
    m.eval()
    return m

def compute_metrics(y_true: List[int], y_pred: List[int], class_names: List[str]) -> Dict[str, Any]:
    n_classes = len(class_names)
    cm = [[0] * n_classes for _ in range(n_classes)]
    for yt, yp in zip(y_true, y_pred):
        cm[yt][yp] += 1

    per_class = {}
    for c in range(n_classes):
        tp = cm[c][c]
        fp = sum(cm[r][c] for r in range(n_classes) if r != c)
        fn = sum(cm[c][col] for col in range(n_classes) if col != c)
        p = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        r = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = 2 * p * r / (p + r) if (p + r) > 0 else 0.0
        per_class[class_names[c]] = {
            "precision": round(p, 4),
            "recall": round(r, 4),
            "f1": round(f1, 4),
            "support": tp + fn,
            "tp": tp, "fp": fp, "fn": fn
        }

    total = len(y_true)
    correct = sum(1 for yt, yp in zip(y_true, y_pred) if yt == yp)
    accuracy = round(correct / total, 4) if total > 0 else 0.0
    macro_f1 = round(sum(v["f1"] for v in per_class.values()) / n_classes, 4)

    return {
        "accuracy": accuracy,
        "correct": correct,
        "total": total,
        "macro_f1": macro_f1,
        "confusion_matrix": cm,
        "per_class": per_class
    }

def run_investigation():
    base_dir = r"d:\NAGARSETU\NAGARSETU 3.1\ai_service"
    m1_path = os.path.join(base_dir, "model", "drainage_model.pt")
    m2_path = os.path.join(base_dir, "model", "drainage_model_v2.pt")
    splits_path = os.path.join(base_dir, "training", "drainage_v2", "frozen_splits.json")
    catalog_path = os.path.join(base_dir, "data", "drainage_catalog.json")
    reviewed_path = os.path.join(base_dir, "training", "drainage_v2", "drainage_annotations_reviewed.json")

    with open(splits_path, "r") as f:
        test_files = json.load(f)["test"]

    with open(catalog_path, "r", encoding="utf-8") as f:
        catalog_dict = json.load(f)["catalog"]

    with open(reviewed_path, "r", encoding="utf-8") as f:
        reviewed_dict = {item["filename"]: item for item in json.load(f)["images"]}

    class_names = ["normal_drain", "blocked_drain", "damaged_drain"]
    c2i = {name: i for i, name in enumerate(class_names)}

    eval_tf = T.Compose([
        T.Resize((224, 224)),
        T.ToTensor(),
        T.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])

    m_orig = load_model(m1_path)
    m_v2 = load_model(m2_path)

    sample_results = []
    y_cat_true = []
    y_rev_true = []
    y_orig_pred = []
    y_v2_pred = []

    for fp in test_files:
        fname = os.path.basename(fp)
        # 1. Source A: Catalog
        raw_cat = catalog_dict.get(fname, "DAMAGED_DRAIN").lower()
        if raw_cat == "drain_overflow":
            raw_cat = "blocked_drain"
        cat_idx = c2i.get(raw_cat, 2)

        # 2. Source B: Reviewed
        raw_rev = reviewed_dict.get(fname, {}).get("assigned_label", "damaged_drain").lower()
        rev_idx = c2i.get(raw_rev, 2)

        real_p = os.path.join(r"D:\NAGARSETU\drainage images", fname)
        if not os.path.exists(real_p):
            real_p = os.path.join(base_dir, "training", "drainage_v2", "images", fname)

        img = Image.open(real_p).convert("RGB")
        tensor = eval_tf(img).unsqueeze(0)

        with torch.no_grad():
            out_orig = m_orig(tensor)
            probs_orig = torch.softmax(out_orig, 1)[0].tolist()
            pred_orig = int(torch.argmax(out_orig, 1).item())

            out_v2 = m_v2(tensor)
            probs_v2 = torch.softmax(out_v2, 1)[0].tolist()
            pred_v2 = int(torch.argmax(out_v2, 1).item())

        y_cat_true.append(cat_idx)
        y_rev_true.append(rev_idx)
        y_orig_pred.append(pred_orig)
        y_v2_pred.append(pred_v2)

        sample_results.append({
            "filename": fname,
            "path": real_p,
            "catalog_label": raw_cat,
            "reviewed_label": raw_rev,
            "label_conflict": (raw_cat != raw_rev),
            "orig_prediction": class_names[pred_orig],
            "orig_probs": [round(x, 4) for x in probs_orig],
            "orig_matches_catalog": (pred_orig == cat_idx),
            "orig_matches_reviewed": (pred_orig == rev_idx),
            "v2_prediction": class_names[pred_v2],
            "v2_probs": [round(x, 4) for x in probs_v2],
            "v2_matches_catalog": (pred_v2 == cat_idx),
            "v2_matches_reviewed": (pred_v2 == rev_idx)
        })

    metrics_orig_vs_cat = compute_metrics(y_cat_true, y_orig_pred, class_names)
    metrics_v2_vs_cat = compute_metrics(y_cat_true, y_v2_pred, class_names)
    metrics_orig_vs_rev = compute_metrics(y_rev_true, y_orig_pred, class_names)
    metrics_v2_vs_rev = compute_metrics(y_rev_true, y_v2_pred, class_names)

    output = {
        "investigation": "Phase 1 vs Phase 2 Inconsistency Resolution",
        "held_out_test_set_size": len(test_files),
        "source_a_catalog_evaluation": {
            "ground_truth_file": "drainage_catalog.json",
            "original_model_metrics": metrics_orig_vs_cat,
            "candidate_v2_metrics": metrics_v2_vs_cat
        },
        "source_b_reviewed_evaluation": {
            "ground_truth_file": "drainage_annotations_reviewed.json",
            "original_model_metrics": metrics_orig_vs_rev,
            "candidate_v2_metrics": metrics_v2_vs_rev
        },
        "samples": sample_results
    }

    out_file = os.path.join(base_dir, "experiments", "phase3", "drainage_inconsistency_resolution.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2)

    print("Investigation complete. Output written to:", out_file)
    print(f"Against Catalog Ground Truth (Phase 2):")
    print(f"  drainage_model.pt    : {metrics_orig_vs_cat['accuracy']*100}% ({metrics_orig_vs_cat['correct']}/16)")
    print(f"  drainage_model_v2.pt : {metrics_v2_vs_cat['accuracy']*100}% ({metrics_v2_vs_cat['correct']}/16)")
    print(f"Against Reviewed Ground Truth (Phase 1):")
    print(f"  drainage_model.pt    : {metrics_orig_vs_rev['accuracy']*100}% ({metrics_orig_vs_rev['correct']}/16)")
    print(f"  drainage_model_v2.pt : {metrics_v2_vs_rev['accuracy']*100}% ({metrics_v2_vs_rev['correct']}/16)")

if __name__ == "__main__":
    run_investigation()

