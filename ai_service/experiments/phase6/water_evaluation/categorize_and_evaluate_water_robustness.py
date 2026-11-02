"""
Phase 6 - Task 2: Water Pipeline Robustness Validation
Evaluates production baseline water_pipe_model.pt against candidate water_pipe_candidate_v5.pt
across fine-grained test scenarios:
Category A: Leaks (thin spray, hairline cracks, slow leak, large leak, joint leaks, poorly lit)
Category B: Normal pipes (rusted intact, wet surfaces, old functional, clean concrete/metal, stained)
Category C: Difficult conditions (low-res, motion blur/shadows, wide-angle, partial pipe, angle)
Outputs: water_robustness_evaluation.json
"""

import os
import time
import json
import torch
import torch.nn.functional as F
import numpy as np
from PIL import Image
from torchvision import models, transforms
from sklearn.metrics import accuracy_score, precision_recall_fscore_support, confusion_matrix

PROD_MODEL_PATH = r"ai_service\model\water_pipe_model.pt"
CAND_MODEL_PATH = r"ai_service\experiments\phase5\water_training\water_pipe_candidate_v5.pt"
OUTPUT_JSON = r"ai_service\experiments\phase6\water_evaluation\water_robustness_evaluation.json"

LEAK_DIR = r"D:\NAGARSETU\leaking pipes"
NORMAL_DIR = r"D:\NAGARSETU\normal pipe images"

# Production Model Architecture
class WaterPipeClassifier(torch.nn.Module):
    def __init__(self, num_classes=3):
        super(WaterPipeClassifier, self).__init__()
        self.backbone = models.mobilenet_v3_small(weights=None)
        in_features = self.backbone.classifier[3].in_features
        self.backbone.classifier[3] = torch.nn.Linear(in_features, num_classes)

    def forward(self, x):
        return self.backbone(x)

# Candidate Architecture
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

def run_robustness_validation():
    print("=" * 80)
    print("PHASE 6 TASK 2: WATER PIPELINE ROBUSTNESS & EDGE-CASE VALIDATION")
    print("=" * 80)

    # 1. Load models
    prod_ckpt = torch.load(PROD_MODEL_PATH, map_location="cpu")
    prod_model = WaterPipeClassifier(num_classes=prod_ckpt.get("num_classes", 3))
    prod_model.load_state_dict(prod_ckpt["model_state_dict"])
    prod_model.eval()

    cand_ckpt = torch.load(CAND_MODEL_PATH, map_location="cpu")
    cand_model = WaterPipeCandidateV5(num_classes=cand_ckpt.get("num_classes", 2))
    cand_model.load_state_dict(cand_ckpt["model_state_dict"])
    cand_model.eval()

    eval_transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])

    # 2. Curate Scenario Test Set with Verified Files
    scenario_map = {
        # Category A: Leaks
        "WhatsApp Image 2026-10-09 at 12.19.20 AM (1).jpeg": {"category": "A_LEAK", "scenario": "thin_vertical_water_spray", "gt": 1, "dir": LEAK_DIR},
        "WhatsApp Image 2026-10-09 at 12.19.19 AM (2).jpeg": {"category": "A_LEAK", "scenario": "hairline_cracks_leak", "gt": 1, "dir": LEAK_DIR},
        "WhatsApp Image 2026-10-09 at 12.19.19 AM (1).jpeg": {"category": "A_LEAK", "scenario": "slow_leakage_trickle", "gt": 1, "dir": LEAK_DIR},
        "WhatsApp Image 2026-10-09 at 12.19.19 AM.jpeg":     {"category": "A_LEAK", "scenario": "large_water_burst", "gt": 1, "dir": LEAK_DIR},
        "burst-water-pipe.jpg":                             {"category": "A_LEAK", "scenario": "large_street_rupture", "gt": 1, "dir": LEAK_DIR},
        "broken-water-pipe-leaking-out-soil-underground-leak-274565016.webp": {"category": "A_LEAK", "scenario": "subsurface_soil_leak", "gt": 1, "dir": LEAK_DIR},
        "images (2).jpg":                                   {"category": "A_LEAK", "scenario": "pipe_joint_leakage", "gt": 1, "dir": LEAK_DIR},
        "images (3).jpg":                                   {"category": "A_LEAK", "scenario": "joint_collar_fracture", "gt": 1, "dir": LEAK_DIR},
        "images (4).jpg":                                   {"category": "A_LEAK", "scenario": "poorly_lit_indoor_leak", "gt": 1, "dir": LEAK_DIR},
        "images (5).jpg":                                   {"category": "A_LEAK", "scenario": "spraying_lateral_leak", "gt": 1, "dir": LEAK_DIR},

        # Category B: Normal Pipes
        "blue-industrial-water-pipe-system-with-visible-rust-near-a-corrugated-metal-wall-in-an-outdoor-setting-photo.jpg": {"category": "B_NORMAL", "scenario": "rusted_intact_metal_pipe", "gt": 0, "dir": NORMAL_DIR},
        "pipa-hdpe-1-1568x882.webp":                        {"category": "B_NORMAL", "scenario": "clean_hdpe_water_pipe", "gt": 0, "dir": NORMAL_DIR},
        "4412.webp":                                        {"category": "B_NORMAL", "scenario": "wet_pipe_surface_intact", "gt": 0, "dir": NORMAL_DIR},
        "WhatsApp Image 2026-10-09 at 1.24.00 AM.jpeg":     {"category": "B_NORMAL", "scenario": "old_functional_pvc_pipe", "gt": 0, "dir": NORMAL_DIR},
        "Screenshot 2026-10-09 011506.png":                 {"category": "B_NORMAL", "scenario": "clean_concrete_water_main", "gt": 0, "dir": NORMAL_DIR},
        "Screenshot 2026-10-09 011519.png":                 {"category": "B_NORMAL", "scenario": "clean_metal_pipeline", "gt": 0, "dir": NORMAL_DIR},
        "Screenshot 2026-10-09 011533.png":                 {"category": "B_NORMAL", "scenario": "stained_discolored_pipe_intact", "gt": 0, "dir": NORMAL_DIR},
        "Screenshot 2026-10-09 011541.png":                 {"category": "B_NORMAL", "scenario": "weathered_exterior_pipe", "gt": 0, "dir": NORMAL_DIR},

        # Category C: Difficult Conditions
        "images (8).jpg":                                   {"category": "C_DIFFICULT", "scenario": "low_resolution_blurry_leak", "gt": 1, "dir": LEAK_DIR},
        "images (9).jpg":                                   {"category": "C_DIFFICULT", "scenario": "harsh_shadows_and_glare_leak", "gt": 1, "dir": LEAK_DIR},
        "images (13).jpg":                                  {"category": "C_DIFFICULT", "scenario": "wide_angle_distant_pipe_leak", "gt": 1, "dir": LEAK_DIR},
        "images (16).jpg":                                  {"category": "C_DIFFICULT", "scenario": "partial_pipe_occlusion_leak", "gt": 1, "dir": LEAK_DIR},
        "Screenshot 2026-10-09 011809.png":                 {"category": "C_DIFFICULT", "scenario": "extreme_camera_tilt_angle_normal", "gt": 0, "dir": NORMAL_DIR},
        "Screenshot 2026-10-09 011821.png":                 {"category": "C_DIFFICULT", "scenario": "uneven_lighting_normal_pipe", "gt": 0, "dir": NORMAL_DIR}
    }

    test_samples = []
    for fn, info in scenario_map.items():
        fp = os.path.join(info["dir"], fn)
        if os.path.exists(fp):
            test_samples.append({
                "sample_id": f"SMP-{len(test_samples)+1:03d}",
                "filename": fn,
                "filepath": fp,
                "category": info["category"],
                "scenario": info["scenario"],
                "ground_truth": info["gt"],
                "gt_label": "leaking" if info["gt"] == 1 else "normal"
            })
        else:
            print(f"Warning: sample file not found: {fp}")

    print(f"Loaded {len(test_samples)} verified robustness test samples across A/B/C categories.")

    # 3. Execute inference
    evaluation_records = []
    high_conf_errors = []

    for s in test_samples:
        img = Image.open(s["filepath"]).convert("RGB")
        tensor = eval_transform(img).unsqueeze(0)

        # Baseline inference
        t0 = time.perf_counter()
        with torch.no_grad():
            prod_out = prod_model(tensor)
            prod_probs = F.softmax(prod_out, dim=1)[0].numpy()
        prod_lat = (time.perf_counter() - t0) * 1000

        # Baseline: class 0 is normal, 1 and 2 are leak/damage
        prod_raw_pred = int(np.argmax(prod_probs))
        prod_binary_pred = 0 if prod_raw_pred == 0 else 1
        prod_conf = float(prod_probs[prod_raw_pred])
        prod_correct = (prod_binary_pred == s["ground_truth"])

        # Candidate inference
        t0 = time.perf_counter()
        with torch.no_grad():
            cand_out = cand_model(tensor)
            cand_probs = F.softmax(cand_out, dim=1)[0].numpy()
        cand_lat = (time.perf_counter() - t0) * 1000

        cand_pred = int(np.argmax(cand_probs))
        cand_conf = float(cand_probs[cand_pred])
        cand_correct = (cand_pred == s["ground_truth"])

        rec = {
            "sample_id": s["sample_id"],
            "category": s["category"],
            "scenario": s["scenario"],
            "ground_truth": s["gt_label"],
            "baseline": {
                "predicted": "leaking" if prod_binary_pred == 1 else "normal",
                "raw_class": prod_raw_pred,
                "confidence": round(prod_conf, 4),
                "correct": prod_correct,
                "latency_ms": round(prod_lat, 2)
            },
            "candidate": {
                "predicted": "leaking" if cand_pred == 1 else "normal",
                "confidence": round(cand_conf, 4),
                "correct": cand_correct,
                "latency_ms": round(cand_lat, 2)
            }
        }
        evaluation_records.append(rec)

        # Flag high-confidence errors
        if not prod_correct and prod_conf > 0.70:
            high_conf_errors.append({"model": "production", "sample_id": s["sample_id"], "scenario": s["scenario"], "conf": prod_conf, "pred": rec["baseline"]["predicted"], "gt": s["gt_label"]})
        if not cand_correct and cand_conf > 0.70:
            high_conf_errors.append({"model": "candidate", "sample_id": s["sample_id"], "scenario": s["scenario"], "conf": cand_conf, "pred": rec["candidate"]["predicted"], "gt": s["gt_label"]})

    # 4. Compute per-category & overall metrics
    def summarize_group(records):
        if not records:
            return {"sample_count": 0}
        gt = [1 if r["ground_truth"] == "leaking" else 0 for r in records]
        b_pred = [1 if r["baseline"]["predicted"] == "leaking" else 0 for r in records]
        c_pred = [1 if r["candidate"]["predicted"] == "leaking" else 0 for r in records]

        def get_stat(y_true, y_pred):
            acc = float(accuracy_score(y_true, y_pred))
            p, r, f1, _ = precision_recall_fscore_support(y_true, y_pred, average="macro", zero_division=0)
            cm = confusion_matrix(y_true, y_pred, labels=[0, 1]).tolist()
            return {"accuracy": round(acc, 4), "macro_f1": round(float(f1), 4), "precision": round(float(p), 4), "recall": round(float(r), 4), "confusion_matrix": cm}

        return {
            "sample_count": len(records),
            "baseline": get_stat(gt, b_pred),
            "candidate": get_stat(gt, c_pred)
        }

    cat_a = [r for r in evaluation_records if r["category"] == "A_LEAK"]
    cat_b = [r for r in evaluation_records if r["category"] == "B_NORMAL"]
    cat_c = [r for r in evaluation_records if r["category"] == "C_DIFFICULT"]

    summary = {
        "evaluation_name": "Phase 6 Water Pipeline Robustness Validation",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "total_samples": len(evaluation_records),
        "overall_performance": summarize_group(evaluation_records),
        "category_a_leaks": summarize_group(cat_a),
        "category_b_normal_pipes": summarize_group(cat_b),
        "category_c_difficult_conditions": summarize_group(cat_c),
        "high_confidence_incorrect_predictions": high_conf_errors,
        "sample_evaluations": evaluation_records
    }

    with open(OUTPUT_JSON, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"\nSaved water robustness evaluation to: {OUTPUT_JSON}")

    print("\nOVERALL METRICS:")
    print(f"  Production Baseline: Acc={summary['overall_performance']['baseline']['accuracy']:.3f} | F1={summary['overall_performance']['baseline']['macro_f1']:.3f}")
    print(f"  Candidate V5:       Acc={summary['overall_performance']['candidate']['accuracy']:.3f} | F1={summary['overall_performance']['candidate']['macro_f1']:.3f}")
    print(f"\nCategory A (Leaks) Accuracy & F1:")
    print(f"  Baseline:  Acc={summary['category_a_leaks']['baseline']['accuracy']:.3f} | F1={summary['category_a_leaks']['baseline']['macro_f1']:.3f}")
    print(f"  Candidate: Acc={summary['category_a_leaks']['candidate']['accuracy']:.3f} | F1={summary['category_a_leaks']['candidate']['macro_f1']:.3f}")
    print(f"\nCategory B (Normal) Accuracy & F1:")
    print(f"  Baseline:  Acc={summary['category_b_normal_pipes']['baseline']['accuracy']:.3f} | F1={summary['category_b_normal_pipes']['baseline']['macro_f1']:.3f}")
    print(f"  Candidate: Acc={summary['category_b_normal_pipes']['candidate']['accuracy']:.3f} | F1={summary['category_b_normal_pipes']['candidate']['macro_f1']:.3f}")
    print(f"\nCategory C (Difficult Conditions) Accuracy:")
    print(f"  Baseline:  Acc={summary['category_c_difficult_conditions']['baseline']['accuracy']:.3f}")
    print(f"  Candidate: Acc={summary['category_c_difficult_conditions']['candidate']['accuracy']:.3f}")

    return summary

if __name__ == "__main__":
    run_robustness_validation()
