"""
Phase 11 - Task 5 & 6: Independent Evaluation and Architecture Comparison
Evaluates 4 architectures on the exact same test datasets:
  A. Original Production Baseline (water_pipe_model.pt)
  B. Candidate v5 (water_pipe_candidate_v5.pt)
  C. Candidate v6 3-Class (water_pipe_candidate_v6_3class.pt)
  D. Candidate Multi-Stage (water_pipe_multistage_v1.pt)

Evaluates on:
  1. Frozen Independent Test Set (17 parents, zero leakage)
  2. Standard 150-Image Benchmark Set (from Phase 10A verified manifest)
"""

import os
import sys
import time
import json
import math
import numpy as np
from PIL import Image
from collections import defaultdict, Counter

import torch
import torch.nn as nn
from torchvision import models, transforms

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# Model Definitions
class BaselineWaterPipeClassifier(nn.Module):
    def __init__(self, num_classes=3):
        super(BaselineWaterPipeClassifier, self).__init__()
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

class WaterPipeCandidateV6_3Class(nn.Module):
    def __init__(self, num_classes=3):
        super(WaterPipeCandidateV6_3Class, self).__init__()
        self.backbone = models.mobilenet_v3_small(weights=None)
        in_features = self.backbone.classifier[3].in_features
        self.backbone.classifier[3] = nn.Sequential(
            nn.Dropout(p=0.25),
            nn.Linear(in_features, 256),
            nn.Hardswish(),
            nn.Dropout(p=0.15),
            nn.Linear(256, num_classes)
        )

    def forward(self, x):
        return self.backbone(x)

class WaterPipeMultiStageV1(nn.Module):
    def __init__(self):
        super(WaterPipeMultiStageV1, self).__init__()
        base = models.mobilenet_v3_small(weights=None)
        self.features = base.features
        self.avgpool = base.avgpool
        self.stage1_head = nn.Sequential(
            nn.Linear(576, 128),
            nn.Hardswish(),
            nn.Dropout(p=0.2),
            nn.Linear(128, 2)
        )
        self.stage2_head = nn.Sequential(
            nn.Linear(576, 128),
            nn.Hardswish(),
            nn.Dropout(p=0.2),
            nn.Linear(128, 2)
        )

    def forward(self, x):
        feat = self.features(x)
        feat = self.avgpool(feat)
        feat = torch.flatten(feat, 1)
        return self.stage1_head(feat), self.stage2_head(feat)

# Loaders
def load_all_models():
    models_dict = {}
    
    # 1. Baseline
    base_path = r"ai_service\model\water_pipe_model.pt"
    ckpt_base = torch.load(base_path, map_location="cpu", weights_only=False)
    num_cls = ckpt_base.get("num_classes", 3)
    base_model = BaselineWaterPipeClassifier(num_classes=num_cls)
    base_model.load_state_dict(ckpt_base["model_state_dict"])
    base_model.eval().to(DEVICE)
    models_dict["Baseline"] = base_model
    
    # 2. Candidate v5
    v5_path = r"ai_service\experiments\phase5\water_training\water_pipe_candidate_v5.pt"
    ckpt_v5 = torch.load(v5_path, map_location="cpu", weights_only=False)
    v5_model = WaterPipeCandidateV5(num_classes=2)
    v5_model.load_state_dict(ckpt_v5["model_state_dict"])
    v5_model.eval().to(DEVICE)
    models_dict["Candidate_v5"] = v5_model
    
    # 3. Candidate v6 3-Class
    v6_path = r"ai_service\experiments\phase11\models\water_pipe_candidate_v6_3class.pt"
    if os.path.exists(v6_path):
        ckpt_v6 = torch.load(v6_path, map_location="cpu", weights_only=False)
        v6_model = WaterPipeCandidateV6_3Class(num_classes=3)
        v6_model.load_state_dict(ckpt_v6["model_state_dict"])
        v6_model.eval().to(DEVICE)
        models_dict["Candidate_v6_3Class"] = v6_model
    else:
        print(f"Warning: {v6_path} not found yet.")
        
    # 4. Candidate Multi-Stage
    ms_path = r"ai_service\experiments\phase11\models\water_pipe_multistage_v1.pt"
    if os.path.exists(ms_path):
        ckpt_ms = torch.load(ms_path, map_location="cpu", weights_only=False)
        ms_model = WaterPipeMultiStageV1()
        ms_model.load_state_dict(ckpt_ms["model_state_dict"])
        ms_model.eval().to(DEVICE)
        models_dict["Candidate_MultiStage"] = ms_model
    else:
        print(f"Warning: {ms_path} not found yet.")
        
    return models_dict

# Predict functions
def predict_baseline(model, tensor_img):
    with torch.no_grad():
        outputs = model(tensor_img)
        probs = torch.softmax(outputs, dim=1)[0]
        leak_p = float(probs[1] + probs[2])
        is_leak = (leak_p >= 0.50)
        pred_class = "pipe_leak" if is_leak else ("rusted_pipe" if probs[2] > probs[0] else "normal_pipe")
    return {
        "pred_class": pred_class,
        "is_leak": is_leak,
        "probs": probs.tolist(),
        "confidence": max(probs.tolist())
    }

def predict_cand_v5(model, tensor_img):
    with torch.no_grad():
        outputs = model(tensor_img)
        probs = torch.softmax(outputs, dim=1)[0]
        pred_idx = int(torch.argmax(probs).item())
        is_leak = (pred_idx == 1)
        pred_class = "pipe_leak" if is_leak else "normal_pipe"
    return {
        "pred_class": pred_class,
        "is_leak": is_leak,
        "probs": probs.tolist(),
        "confidence": float(probs[pred_idx])
    }

def predict_cand_v6(model, tensor_img):
    with torch.no_grad():
        outputs = model(tensor_img)
        probs = torch.softmax(outputs, dim=1)[0]
        pred_idx = int(torch.argmax(probs).item())
        cls_map = {0: "normal_pipe", 1: "pipe_leak", 2: "rusted_pipe"}
        pred_class = cls_map[pred_idx]
        is_leak = (pred_class == "pipe_leak")
    return {
        "pred_class": pred_class,
        "is_leak": is_leak,
        "probs": probs.tolist(),
        "confidence": float(probs[pred_idx])
    }

def predict_multistage(model, tensor_img):
    with torch.no_grad():
        logits_s1, logits_s2 = model(tensor_img)
        p_s1 = torch.softmax(logits_s1, dim=1)[0]
        p_s2 = torch.softmax(logits_s2, dim=1)[0]
        
        # Stage 1: 0 is clean normal, 1 is anomaly
        is_anomaly = (p_s1[1].item() > 0.50)
        if not is_anomaly:
            pred_class = "normal_pipe"
            is_leak = False
            conf = p_s1[0].item()
        else:
            # Stage 2: 0 is rust/condensation, 1 is active leak
            if p_s2[1].item() > 0.50:
                pred_class = "pipe_leak"
                is_leak = True
                conf = p_s2[1].item()
            else:
                pred_class = "rusted_pipe"
                is_leak = False
                conf = p_s2[0].item()
    return {
        "pred_class": pred_class,
        "is_leak": is_leak,
        "probs": [p_s1.tolist(), p_s2.tolist()],
        "confidence": conf
    }

def evaluate_on_dataset(models_dict, dataset_items, dataset_name):
    print(f"\nEvaluating on {dataset_name} ({len(dataset_items)} samples)...")
    eval_transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
    ])
    
    results = {}
    
    for m_name, model in models_dict.items():
        correct = 0
        total = len(dataset_items)
        y_true_binary = []
        y_pred_binary = []
        y_true_3c = []
        y_pred_3c = []
        scenario_results = defaultdict(lambda: {"correct": 0, "total": 0})
        latencies = []
        
        for it in dataset_items:
            img_path = it.get("filepath") or it.get("path") or it.get("image_path")
            
            # Ground truth determination
            if "ground_truth" in it:
                gt_is_leak = (it["ground_truth"] == 1)
            elif "is_leak" in it:
                gt_is_leak = bool(it["is_leak"])
            elif "ground_truth_label" in it:
                gt_is_leak = (it["ground_truth_label"] == "leaking")
            elif "class_id_binary" in it:
                gt_is_leak = (it["class_id_binary"] == 1)
            else:
                gt_is_leak = False
                
            if "3class_label" in it:
                gt_3c = it["3class_label"]
            elif gt_is_leak:
                gt_3c = "pipe_leak"
            elif "rust" in it.get("scenario", "").lower():
                gt_3c = "rusted_pipe"
            else:
                gt_3c = "normal_pipe"
                    
            scenario = it.get("scenario") or it.get("subscenario") or "standard"
            
            img = Image.open(img_path).convert("RGB")
            t_img = eval_transform(img).unsqueeze(0).to(DEVICE)
            
            t0 = time.perf_counter()
            if m_name == "Baseline":
                pred = predict_baseline(model, t_img)
            elif m_name == "Candidate_v5":
                pred = predict_cand_v5(model, t_img)
            elif m_name == "Candidate_v6_3Class":
                pred = predict_cand_v6(model, t_img)
            elif m_name == "Candidate_MultiStage":
                pred = predict_multistage(model, t_img)
            t1 = time.perf_counter()
            latencies.append((t1 - t0) * 1000.0)
            
            pred_is_leak = pred["is_leak"]
            pred_3c = pred["pred_class"]
            
            # Binary accuracy match
            is_correct_bin = (pred_is_leak == gt_is_leak)
            if is_correct_bin:
                correct += 1
                
            y_true_binary.append(1 if gt_is_leak else 0)
            y_pred_binary.append(1 if pred_is_leak else 0)
            
            y_true_3c.append(gt_3c)
            y_pred_3c.append(pred_3c)
            
            scenario_results[scenario]["total"] += 1
            if is_correct_bin:
                scenario_results[scenario]["correct"] += 1
                
        # Metrics
        acc = correct / total
        tp = sum(1 for yt, yp in zip(y_true_binary, y_pred_binary) if yt == 1 and yp == 1)
        tn = sum(1 for yt, yp in zip(y_true_binary, y_pred_binary) if yt == 0 and yp == 0)
        fp = sum(1 for yt, yp in zip(y_true_binary, y_pred_binary) if yt == 0 and yp == 1)
        fn = sum(1 for yt, yp in zip(y_true_binary, y_pred_binary) if yt == 1 and yp == 0)
        
        leak_recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        leak_precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        leak_fnr = fn / (tp + fn) if (tp + fn) > 0 else 0.0
        normal_fpr = fp / (tn + fp) if (tn + fp) > 0 else 0.0
        specificity = tn / (tn + fp) if (tn + fp) > 0 else 0.0
        f1_leak = 2 * leak_precision * leak_recall / (leak_precision + leak_recall) if (leak_precision + leak_recall) > 0 else 0.0
        
        # Macro F1 across 2 binary classes
        norm_rec = specificity
        norm_prec = tn / (tn + fn) if (tn + fn) > 0 else 0.0
        f1_norm = 2 * norm_prec * norm_rec / (norm_prec + norm_rec) if (norm_prec + norm_rec) > 0 else 0.0
        macro_f1 = (f1_leak + f1_norm) / 2.0
        
        # Per-scenario accuracy
        scenario_acc = {}
        for sc, stats in scenario_results.items():
            scenario_acc[sc] = {
                "correct": stats["correct"],
                "total": stats["total"],
                "accuracy": stats["correct"] / stats["total"] if stats["total"] > 0 else 0.0
            }
            
        results[m_name] = {
            "model_name": m_name,
            "total_samples": total,
            "accuracy": round(acc, 4),
            "correct_count": correct,
            "confusion_matrix": {"TP": tp, "TN": tn, "FP": fp, "FN": fn},
            "leak_recall": round(leak_recall, 4),
            "leak_precision": round(leak_precision, 4),
            "leak_fnr": round(leak_fnr, 4),
            "normal_fpr": round(normal_fpr, 4),
            "specificity": round(specificity, 4),
            "macro_f1": round(macro_f1, 4),
            "latency_p95_ms": round(float(np.percentile(latencies, 95)), 2),
            "latency_mean_ms": round(float(np.mean(latencies)), 2),
            "scenarios": scenario_acc,
            "y_true_binary": y_true_binary,
            "y_pred_binary": y_pred_binary
        }
        
    return results

def compute_mcnemar_test(res_a, res_b):
    y_true = res_a["y_true_binary"]
    y_a = res_a["y_pred_binary"]
    y_b = res_b["y_pred_binary"]
    
    # b: A correct, B wrong
    b = sum(1 for yt, ya, yb in zip(y_true, y_a, y_b) if ya == yt and yb != yt)
    # c: A wrong, B correct
    c = sum(1 for yt, ya, yb in zip(y_true, y_a, y_b) if ya != yt and yb == yt)
    
    if (b + c) == 0:
        chi2 = 0.0
        p_val = 1.0
    else:
        chi2 = ((abs(b - c) - 1.0) ** 2) / (b + c)
        # Approximate p-value from chi2 with 1 dof using survival function
        # sf(x) ~ erfc(sqrt(x/2))
        p_val = math.erfc(math.sqrt(max(0.0, chi2) / 2.0))
        
    return {
        "b_baseline_correct_candidate_wrong": b,
        "c_baseline_wrong_candidate_correct": c,
        "chi2": round(chi2, 4),
        "p_value": round(p_val, 4),
        "significant_p_lt_05": p_val < 0.05
    }

def main():
    print("=" * 80)
    print("PHASE 11: WATER AI INDEPENDENT MULTI-ARCHITECTURE EVALUATION")
    print("=" * 80)
    
    # 1. Load models
    models_dict = load_all_models()
    print(f"Loaded {len(models_dict)} models for evaluation: {list(models_dict.keys())}")
    
    # 2. Ingest Datasets
    # A. Frozen Test Set
    split_manifest_path = r"ai_service\experiments\phase11\dataset\water_phase11_group_split_manifest.json"
    with open(split_manifest_path, "r") as f:
        split_data = json.load(f)
    frozen_test_items = split_data["splits"]["frozen_test"]
    
    # B. 150-Image Benchmark Set
    manifest_150_path = r"water_phase10a_verified_manifest.json"
    with open(manifest_150_path, "r") as f:
        bench_data = json.load(f)
    bench_150_items = bench_data["samples"]
    
    # 3. Run Evaluations
    results_frozen = evaluate_on_dataset(models_dict, frozen_test_items, "Frozen Independent Test Set (17 Parents)")
    results_150 = evaluate_on_dataset(models_dict, bench_150_items, "Standard 150-Image Benchmark Set")
    
    # 4. Statistical Tests (Baseline vs Candidates)
    statistical_comparisons = {}
    for cand_name in ["Candidate_v5", "Candidate_v6_3Class", "Candidate_MultiStage"]:
        if cand_name in results_150:
            mcnemar = compute_mcnemar_test(results_150["Baseline"], results_150[cand_name])
            statistical_comparisons[f"Baseline_vs_{cand_name}_150bench"] = mcnemar
            
    output_payload = {
        "timestamp": "2026-11-03",
        "phase": "11",
        "frozen_test_results": results_frozen,
        "benchmark_150_results": results_150,
        "statistical_tests": statistical_comparisons
    }
    
    out_dir = r"ai_service\experiments\phase11\evaluation"
    os.makedirs(out_dir, exist_ok=True)
    out_json = os.path.join(out_dir, "water_phase11_evaluation_results.json")
    with open(out_json, "w") as f:
        json.dump(output_payload, f, indent=2)
    with open("water_phase11_evaluation_results.json", "w") as f:
        json.dump(output_payload, f, indent=2)
    print(f"\nSaved evaluation results to: {out_json}")
    
    # Print Summary Table
    print("\n" + "=" * 80)
    print("EVALUATION SUMMARY ON 150-IMAGE BENCHMARK SET")
    print("=" * 80)
    print(f"{'Model':24s} | {'Acc':7s} | {'Leak Rec':9s} | {'Spec':7s} | {'Macro F1':9s} | {'FPR':6s} | {'P95 (ms)':8s}")
    print("-" * 80)
    for m_name, res in results_150.items():
        print(f"{m_name:24s} | {res['accuracy']*100:5.2f}% | {res['leak_recall']*100:7.2f}% | {res['specificity']*100:5.2f}% | {res['macro_f1']*100:7.2f}% | {res['normal_fpr']*100:5.2f}% | {res['latency_p95_ms']:6.2f} ms")

if __name__ == "__main__":
    main()
