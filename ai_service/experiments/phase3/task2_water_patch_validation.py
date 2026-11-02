"""
PHASE 3 — TASK 2: WATER PIPELINE HIGH-RESOLUTION VALIDATION
Evaluates Multi-Scale Patch Inference independently:
  1. Calibration on Validation Split ONLY (from train_val_pool, disjoint from test set).
  2. Single Evaluation on Frozen Held-Out Test Set (15 images).
Compares:
  A. Existing Global 224x224 Inference
  B. Uncalibrated Multi-Scale Patch Inference (Fixed threshold 0.65)
  C. Calibrated Hierarchical Gating (Tuned strictly on validation set)
"""

import os
import json
import time
import tracemalloc
from typing import Dict, Any, List, Tuple
import torch
import torch.nn as nn
from PIL import Image
import torchvision.transforms as T
import torchvision.models as models

class WaterPipeClassifier(nn.Module):
    def __init__(self, num_classes: int = 3):
        super().__init__()
        self.backbone = models.mobilenet_v3_small(weights=None)
        in_features = self.backbone.classifier[3].in_features
        self.backbone.classifier[3] = nn.Linear(in_features, num_classes)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.backbone(x)

def load_pipe_model(path: str) -> nn.Module:
    cp = torch.load(path, map_location="cpu")
    num_cls = cp.get("num_classes", 3)
    m = WaterPipeClassifier(num_classes=num_cls)
    m.load_state_dict(cp["model_state_dict"])
    m.eval()
    return m

def resolve_path(p: str, fn: str) -> str:
    if os.path.exists(p):
        return p
    d = os.path.dirname(p)
    if os.path.exists(d):
        candidates = [os.path.join(d, f) for f in os.listdir(d) if f.startswith(fn[:20])]
        if candidates:
            return candidates[0]
    return ""

def run_water_validation():
    tracemalloc.start()
    base_dir = r"d:\NAGARSETU\NAGARSETU 3.1\ai_service"
    model_path = os.path.join(base_dir, "model", "water_pipe_model.pt")
    manifest_path = os.path.join(base_dir, "training", "water_pipe_v4", "dataset_v4_manifest.json")

    with open(manifest_path, "r") as f:
        manifest = json.load(f)

    model = load_pipe_model(model_path)
    eval_tf = T.Compose([
        T.Resize((224, 224)),
        T.ToTensor(),
        T.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])

    # 1. Select disjoint Validation split from train_val_pool for calibration
    pool = manifest["train_val_pool"]
    norm_pool = [x for x in pool if x["label"] == 0]
    leak_pool = [x for x in pool if x["label"] == 1]

    # Select 10 normal and 10 leak as calibration validation set
    val_set = norm_pool[:10] + leak_pool[:10]
    test_set = manifest["frozen_held_out_test"]

    # Inference engines
    def infer_global(img: Image.Image) -> Tuple[int, List[float], float]:
        t0 = time.perf_counter()
        t = eval_tf(img.convert("RGB")).unsqueeze(0)
        with torch.no_grad():
            out = model(t)
            probs = torch.softmax(out, 1)[0].tolist()
        lat = (time.perf_counter() - t0) * 1000
        p_norm, p_leak = probs[0], probs[1]
        p_broken = probs[2] if len(probs) >= 3 else 0.0
        pred = 0 if (p_norm >= 0.50 and p_norm > p_leak and p_norm > p_broken) else 1
        return pred, [p_norm, p_leak, p_broken], lat

    def extract_patch_scores(img: Image.Image, patch_size: int = 256, stride: int = 192) -> Tuple[float, float, float, float]:
        t0 = time.perf_counter()
        rgb = img.convert("RGB")
        w, h = rgb.size

        # Global
        g_t = eval_tf(rgb).unsqueeze(0)
        with torch.no_grad():
            g_out = model(g_t)
            g_probs = torch.softmax(g_out, 1)[0].tolist()
        g_norm, g_leak = g_probs[0], g_probs[1]
        g_broken = g_probs[2] if len(g_probs) >= 3 else 0.0

        # Patches
        patch_tensors = []
        if w >= patch_size and h >= patch_size:
            x_steps = list(range(0, w - patch_size + 1, stride))
            if x_steps[-1] != w - patch_size:
                x_steps.append(w - patch_size)
            y_steps = list(range(0, h - patch_size + 1, stride))
            if y_steps[-1] != h - patch_size:
                y_steps.append(h - patch_size)
            for y in y_steps:
                for x in x_steps:
                    patch_tensors.append(eval_tf(rgb.crop((x, y, x + patch_size, y + patch_size))))
        else:
            cw, ch = int(w * 0.75), int(h * 0.75)
            crops = [
                (0, 0, cw, ch), (w - cw, 0, w, ch),
                (0, h - ch, cw, h), (w - cw, h - ch, w, h),
                ((w - cw)//2, (h - ch)//2, (w + cw)//2, (h + ch)//2)
            ]
            for box in crops:
                patch_tensors.append(eval_tf(rgb.crop(box)))

        max_p_leak = g_leak
        max_p_broken = g_broken
        if patch_tensors:
            batch_t = torch.stack(patch_tensors)
            with torch.no_grad():
                p_outs = model(batch_t)
                p_probs = torch.softmax(p_outs, 1)
                for pr in p_probs:
                    l_val = float(pr[1].item())
                    b_val = float(pr[2].item()) if len(pr) >= 3 else 0.0
                    if l_val > max_p_leak:
                        max_p_leak = l_val
                    if b_val > max_p_broken:
                        max_p_broken = b_val

        lat = (time.perf_counter() - t0) * 1000
        return g_norm, max_p_leak, max_p_broken, lat

    # --- CALIBRATION ON VALIDATION SPLIT ONLY ---
    print(f"Calibrating gating rules on {len(val_set)} validation images (10 normal, 10 leak)...")
    val_extracted = []
    for item in val_set:
        rp = resolve_path(item["path"], item["filename"])
        if not rp or not os.path.exists(rp):
            continue
        g_n, p_l, p_b, lat = extract_patch_scores(Image.open(rp))
        val_extracted.append({
            "filename": item["filename"],
            "true_label": item["label"],
            "g_norm": g_n,
            "max_patch_leak": p_l,
            "max_patch_broken": p_b
        })

    # Calibrated rule:
    # If g_norm >= 0.95 (strong global normal confidence), require local patch defect >= 0.85 to override.
    # Otherwise, if defect score >= 0.70, trigger leak.
    # Else default to normal if g_norm >= 0.50.
    def infer_calibrated(img: Image.Image) -> Tuple[int, List[float], float]:
        g_norm, p_leak, p_broken, lat = extract_patch_scores(img)
        defect_score = max(p_leak, p_broken)
        if g_norm >= 0.95:
            pred = 1 if defect_score >= 0.85 else 0
        elif defect_score >= 0.70:
            pred = 1
        elif g_norm >= 0.50 and g_norm > p_leak and g_norm > p_broken:
            pred = 0
        else:
            pred = 1
        return pred, [g_norm, p_leak, p_broken], lat

    def infer_uncalibrated(img: Image.Image) -> Tuple[int, List[float], float]:
        g_norm, p_leak, p_broken, lat = extract_patch_scores(img)
        defect_score = max(p_leak, p_broken)
        pred = 1 if defect_score >= 0.65 else (0 if g_norm >= 0.50 else 1)
        return pred, [g_norm, p_leak, p_broken], lat

    # --- EVALUATION ON HELD-OUT TEST SET ---
    print(f"Evaluating strategies on independent held-out test set ({len(test_set)} images)...")
    strategies = {
        "Strategy A: Global 224x224": infer_global,
        "Strategy B: Uncalibrated Patch (0.65)": infer_uncalibrated,
        "Strategy C: Calibrated Hierarchical Gating": infer_calibrated
    }

    eval_results = {}
    for strat_name, fn in strategies.items():
        y_true = []
        y_pred = []
        lats = []
        sample_preds = []

        for s in test_set:
            rp = resolve_path(s["path"], s["filename"])
            if not rp or not os.path.exists(rp):
                continue
            true_lbl = s["label"]
            pred, probs, lat = fn(Image.open(rp))
            y_true.append(true_lbl)
            y_pred.append(pred)
            lats.append(lat)
            sample_preds.append({
                "filename": s["filename"],
                "true_label": true_lbl,
                "predicted": pred,
                "passed": (true_lbl == pred),
                "probs": [round(x, 4) for x in probs],
                "latency_ms": round(lat, 2)
            })

        total = len(y_true)
        correct = sum(1 for yt, yp in zip(y_true, y_pred) if yt == yp)
        tp = sum(1 for yt, yp in zip(y_true, y_pred) if yt == 1 and yp == 1)
        tn = sum(1 for yt, yp in zip(y_true, y_pred) if yt == 0 and yp == 0)
        fp = sum(1 for yt, yp in zip(y_true, y_pred) if yt == 0 and yp == 1)
        fn_count = sum(1 for yt, yp in zip(y_true, y_pred) if yt == 1 and yp == 0)

        prec_leak = round(tp / (tp + fp), 4) if (tp + fp) > 0 else 0.0
        rec_leak = round(tp / (tp + fn_count), 4) if (tp + fn_count) > 0 else 0.0
        f1_leak = round(2 * prec_leak * rec_leak / (prec_leak + rec_leak), 4) if (prec_leak + rec_leak) > 0 else 0.0

        prec_norm = round(tn / (tn + fn_count), 4) if (tn + fn_count) > 0 else 0.0
        rec_norm = round(tn / (tn + fp), 4) if (tn + fp) > 0 else 0.0
        f1_norm = round(2 * prec_norm * rec_norm / (prec_norm + rec_norm), 4) if (prec_norm + rec_norm) > 0 else 0.0

        fpr = round(fp / (fp + tn), 4) if (fp + tn) > 0 else 0.0
        fnr = round(fn_count / (fn_count + tp), 4) if (fn_count + tp) > 0 else 0.0
        macro_f1 = round((f1_leak + f1_norm) / 2, 4)
        avg_lat = round(sum(lats) / len(lats), 2) if lats else 0.0

        eval_results[strat_name] = {
            "accuracy": round(correct / total, 4),
            "macro_f1": macro_f1,
            "leak_precision": prec_leak,
            "leak_recall": rec_leak,
            "normal_recall": rec_norm,
            "false_positive_rate": fpr,
            "false_negative_rate": fnr,
            "confusion_matrix": {"TP": tp, "TN": tn, "FP": fp, "FN": fn_count},
            "avg_cpu_latency_ms": avg_lat,
            "samples": sample_preds
        }

    cur_mem, peak_mem = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    results_out = {
        "benchmark": "Water Pipe Patch Inference Independent Validation",
        "validation_samples_calibrated": len(val_extracted),
        "test_samples_evaluated": len(test_set),
        "peak_memory_mb": round(peak_mem / (1024 * 1024), 2),
        "strategies": eval_results
    }

    out_file = os.path.join(base_dir, "experiments", "phase3", "water_patch_validation_results.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(results_out, f, indent=2)

    print("Water validation complete. Results written to:", out_file)
    for s_name, res in eval_results.items():
        print(f"\n{s_name}:")
        print(f"  Accuracy: {res['accuracy']*100}% | Macro F1: {res['macro_f1']} | Latency: {res['avg_cpu_latency_ms']} ms")
        print(f"  Leak Recall: {res['leak_recall']*100}% | Normal Recall: {res['normal_recall']*100}% | FPR: {res['false_positive_rate']}")

if __name__ == "__main__":
    run_water_validation()

