import os
import sys
import time
import json
import random
import hashlib
import gc
from pathlib import Path
from typing import Dict, List, Tuple, Set, Any

import numpy as np
from PIL import Image
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
import torchvision.transforms as T
import torchvision.models as models

# Set reproducibility seeds
torch.manual_seed(42)
np.random.seed(42)
random.seed(42)

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_MODEL_PATH = BASE_DIR / "model" / "civic_validator.pt"
CHECKPOINT_PATH = BASE_DIR / "model" / "civic_validator_checkpoint.pt"
METRICS_PATH = BASE_DIR / "model" / "civic_validator_metrics.json"

# Dataset Directories
if os.path.exists(r"D:\NAGARSETU\random images"):
    RANDOM_DIR = r"D:\NAGARSETU\random images"
elif os.path.exists(r"D:\NAGARSETU\random iamges"):
    RANDOM_DIR = r"D:\NAGARSETU\random iamges"
else:
    RANDOM_DIR = str(BASE_DIR / "tests" / "fixtures")

ROAD_DIR = r"D:\NAGARSETU\road"
DRAINAGE_DIR = r"D:\NAGARSETU\drainage images"
LEAK_DIR = r"D:\NAGARSETU\leaking pipes"
NORMAL_PIPE_DIR = r"D:\NAGARSETU\normal pipe images"
GARBAGE_DIR = r"D:\NAGARSETU\garbage waste"
DRAINAGE_CATALOG = BASE_DIR / "data" / "drainage_catalog.json"

# Independent held-out test images specification (STRICTLY EXCLUDED FROM TRAINING & VALIDATION)
HELD_OUT_SPEC = [
    # (path, class_idx, name)
    (r"D:\NAGARSETU\road\Pothole_01.jpg", 2, "GENUINE_CIVIC_ISSUE (Road Pothole)"),
    (r"D:\NAGARSETU\drainage images\images (1).jpg", 2, "GENUINE_CIVIC_ISSUE (Damaged Drain)"),
    (r"D:\NAGARSETU\leaking pipes\water-leaking-hole-industrial-hose-260nw-2609724773.jpg", 2, "GENUINE_CIVIC_ISSUE (Pipe Leak)"),
    (r"D:\NAGARSETU\garbage waste\images.jpg", 2, "GENUINE_CIVIC_ISSUE (Garbage Accumulation)"),
    (r"D:\NAGARSETU\road\16tvsbg03-City-17TVTV_ROAD.jpg.jpg", 1, "CIVIC_INFRASTRUCTURE_NO_ISSUE (Clean Road)"),
    (r"D:\NAGARSETU\drainage images\images (10).jpg", 1, "CIVIC_INFRASTRUCTURE_NO_ISSUE (Normal Drain)"),
    (str(BASE_DIR / "tests" / "fixtures" / "test_animal_cat.jpg"), 0, "NON_CIVIC_IMAGE (Cat Animal)"),
    (str(BASE_DIR / "tests" / "fixtures" / "test_unrelated_vehicle.jpg"), 0, "NON_CIVIC_IMAGE (Vehicle)"),
    (os.path.join(RANDOM_DIR, "WhatsApp Image 2026-11-04 at 5.40.49 AM (1).jpeg"), 0, "NON_CIVIC_IMAGE (Random Household 1)"),
    (os.path.join(RANDOM_DIR, "WhatsApp Image 2026-11-04 at 5.46.41 AM (1).jpeg"), 0, "NON_CIVIC_IMAGE (Random Household 2)"),
    (os.path.join(RANDOM_DIR, "WhatsApp Image 2026-11-04 at 5.47.10 AM.jpeg"), 0, "NON_CIVIC_IMAGE (Random Household 3)")
]


def compute_file_hash(filepath: str) -> str:
    with open(filepath, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()


class CivicImageDataset(Dataset):
    def __init__(self, samples: List[Tuple[str, int]], transform=None):
        self.cached_samples = []
        for file_path, label in samples:
            try:
                with Image.open(file_path) as raw:
                    img = raw.convert("RGB").resize((256, 256), Image.Resampling.BILINEAR)
                self.cached_samples.append((img, label, file_path))
            except Exception as e:
                print(f"Warning: could not cache {file_path}: {e}")
        self.transform = transform

    def __len__(self):
        return len(self.cached_samples)

    def __getitem__(self, idx):
        img, label, file_path = self.cached_samples[idx]
        if self.transform:
            img = self.transform(img)
        return img, label, file_path


class CivicValidator(nn.Module):
    """
    Lightweight, high-accuracy transfer-learning model based on MobileNetV3-Small
    for pre-filtering and validating civic complaint images.
    Classes:
    0: NON_CIVIC_IMAGE (indoor scenes, furniture, domestic objects, tiles, laptops, animals, unrelated vehicles)
    1: CIVIC_INFRASTRUCTURE_NO_ISSUE (clean undamaged road, clean normal pipe, normal functional drain)
    2: GENUINE_CIVIC_ISSUE (pothole, road damage, leaking/broken pipe, blocked/damaged drain, garbage accumulation)
    """
    def __init__(self, num_classes=3, pretrained=True):
        super(CivicValidator, self).__init__()
        cache_file = Path.home() / ".cache" / "torch" / "hub" / "checkpoints" / "mobilenet_v3_small-047dcff4.pth"
        if pretrained and cache_file.exists():
            self.backbone = models.mobilenet_v3_small(weights=None)
            state = torch.load(str(cache_file), map_location="cpu")
            self.backbone.load_state_dict(state)
        elif pretrained:
            weights = models.MobileNet_V3_Small_Weights.DEFAULT
            self.backbone = models.mobilenet_v3_small(weights=weights)
        else:
            self.backbone = models.mobilenet_v3_small(weights=None)

        in_features = self.backbone.classifier[3].in_features
        self.backbone.classifier[3] = nn.Linear(in_features, num_classes)

    def forward(self, x):
        return self.backbone(x)


def prepare_datasets() -> Tuple[List[Tuple[str, int]], List[Tuple[str, int]], Set[str]]:
    # 1. Identify all held-out hashes to strictly prevent data leakage
    held_out_hashes = set()
    held_out_paths = set()
    for item in HELD_OUT_SPEC:
        p = os.path.normpath(item[0])
        if os.path.exists(p):
            h = compute_file_hash(p)
            held_out_hashes.add(h)
            held_out_paths.add(p)

    seen_hashes = set(held_out_hashes)

    def collect_unique_images(dir_path: str, exclude_names: Set[str] = None) -> List[str]:
        if not os.path.exists(dir_path):
            return []
        res = []
        for f in sorted(os.listdir(dir_path)):
            if not f.lower().endswith((".jpg", ".jpeg", ".png", ".webp")):
                continue
            if exclude_names and f in exclude_names:
                continue
            p = os.path.normpath(os.path.join(dir_path, f))
            if p in held_out_paths:
                continue
            h = compute_file_hash(p)
            if h in seen_hashes:
                continue
            seen_hashes.add(h)
            res.append(p)
        return res

    # Class 0: NON_CIVIC_IMAGE (random images from household, indoor, animal, domestic objects)
    non_civic_files = collect_unique_images(RANDOM_DIR)

    # Class 1: CIVIC_INFRASTRUCTURE_NO_ISSUE (clean pipes, clean drains, clean undamaged road)
    clean_infra_files = []
    # Normal pipes
    clean_infra_files.extend(collect_unique_images(NORMAL_PIPE_DIR))
    # Normal drains from catalog
    if os.path.exists(DRAINAGE_CATALOG):
        with open(DRAINAGE_CATALOG, "r") as fp:
            dcat = json.load(fp).get("catalog", {})
        for fname, lbl in sorted(dcat.items()):
            if lbl == "NORMAL_DRAIN":
                p = os.path.normpath(os.path.join(DRAINAGE_DIR, fname))
                if os.path.exists(p) and p not in held_out_paths:
                    h = compute_file_hash(p)
                    if h not in seen_hashes:
                        seen_hashes.add(h)
                        clean_infra_files.append(p)
    # Clean roads
    good_road_dir = os.path.join(ROAD_DIR, "good road")
    if os.path.exists(good_road_dir):
        clean_infra_files.extend(collect_unique_images(good_road_dir))
    clean_road_screenshot = os.path.normpath(os.path.join(ROAD_DIR, "Screenshot 2026-10-10 013251.png"))
    if os.path.exists(clean_road_screenshot) and clean_road_screenshot not in held_out_paths:
        h = compute_file_hash(clean_road_screenshot)
        if h not in seen_hashes:
            seen_hashes.add(h)
            clean_infra_files.append(clean_road_screenshot)

    # Class 2: GENUINE_CIVIC_ISSUE (road pothole/damage, leaking pipes, blocked drains, garbage)
    civic_defect_files = []
    # Road damage (exclude clean road screenshot and good road folder)
    road_excludes = {"Screenshot 2026-10-10 013251.png", "good road"}
    civic_defect_files.extend(collect_unique_images(ROAD_DIR, exclude_names=road_excludes))
    # Leaking pipes
    civic_defect_files.extend(collect_unique_images(LEAK_DIR))
    # Garbage waste
    civic_defect_files.extend(collect_unique_images(GARBAGE_DIR))
    # Drainage defects
    if os.path.exists(DRAINAGE_CATALOG):
        with open(DRAINAGE_CATALOG, "r") as fp:
            dcat = json.load(fp).get("catalog", {})
        for fname, lbl in sorted(dcat.items()):
            if lbl != "NORMAL_DRAIN":
                p = os.path.normpath(os.path.join(DRAINAGE_DIR, fname))
                if os.path.exists(p) and p not in held_out_paths:
                    h = compute_file_hash(p)
                    if h not in seen_hashes:
                        seen_hashes.add(h)
                        civic_defect_files.append(p)

    print("Dataset Composition (excluding all duplicates and held-out test images):")
    print(f"  Class 0 (NON_CIVIC_IMAGE):               {len(non_civic_files)}")
    print(f"  Class 1 (CIVIC_INFRASTRUCTURE_NO_ISSUE): {len(clean_infra_files)}")
    print(f"  Class 2 (GENUINE_CIVIC_ISSUE):            {len(civic_defect_files)}")
    print(f"  Held-out Test Images:                    {len(HELD_OUT_SPEC)}")

    # Split train and validation (85% train, 15% validation)
    random.seed(42)
    random.shuffle(non_civic_files)
    random.shuffle(clean_infra_files)
    random.shuffle(civic_defect_files)

    n0_train = int(len(non_civic_files) * 0.85)
    n1_train = int(len(clean_infra_files) * 0.85)
    n2_train = int(len(civic_defect_files) * 0.85)

    train_samples = (
        [(p, 0) for p in non_civic_files[:n0_train]] +
        [(p, 1) for p in clean_infra_files[:n1_train]] +
        [(p, 2) for p in civic_defect_files[:n2_train]]
    )

    val_samples = (
        [(p, 0) for p in non_civic_files[n0_train:]] +
        [(p, 1) for p in clean_infra_files[n1_train:]] +
        [(p, 2) for p in civic_defect_files[n2_train:]]
    )

    random.shuffle(train_samples)
    print(f"  Train split size: {len(train_samples)} (C0: {n0_train}, C1: {n1_train}, C2: {n2_train})")
    print(f"  Val split size:   {len(val_samples)} (C0: {len(non_civic_files) - n0_train}, C1: {len(clean_infra_files) - n1_train}, C2: {len(civic_defect_files) - n2_train})")

    return train_samples, val_samples, held_out_paths


def evaluate_held_out(model: nn.Module, device: torch.device) -> Dict[str, Any]:
    eval_transform = T.Compose([
        T.Resize((224, 224)),
        T.ToTensor(),
        T.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])

    classes = {0: "NON_CIVIC_IMAGE", 1: "CIVIC_INFRASTRUCTURE_NO_ISSUE", 2: "GENUINE_CIVIC_ISSUE"}
    model.eval()

    total = 0
    correct = 0
    false_accepts = 0  # Non-civic (0) or Clean infra (1) predicted as Genuine defect (2)
    false_rejects = 0  # Genuine defect (2) predicted as Non-civic (0) or Clean infra (1)

    # Per-class counts: [TP, FP, FN]
    class_stats = {0: {"tp": 0, "fp": 0, "fn": 0}, 1: {"tp": 0, "fp": 0, "fn": 0}, 2: {"tp": 0, "fp": 0, "fn": 0}}
    results_detail = []

    with torch.no_grad():
        for path, expected, name in HELD_OUT_SPEC:
            if not os.path.exists(path):
                print(f"Warning: Held-out image missing: {path}")
                continue
            with Image.open(path) as raw:
                img = raw.convert("RGB")
            tensor = eval_transform(img).unsqueeze(0).to(device)
            out = model(tensor)
            probs = torch.softmax(out, dim=1)[0]
            pred = int(probs.argmax().item())
            conf = float(probs[pred].item())

            total += 1
            is_match = (pred == expected)
            if is_match:
                correct += 1
                class_stats[expected]["tp"] += 1
            else:
                class_stats[expected]["fn"] += 1
                class_stats[pred]["fp"] += 1

            # Decision Gate False Accept / False Reject definitions
            if expected in (0, 1) and pred == 2:
                false_accepts += 1
            elif expected == 2 and pred in (0, 1):
                false_rejects += 1

            results_detail.append({
                "name": name,
                "path": path,
                "expected": classes[expected],
                "predicted": classes[pred],
                "confidence": round(conf, 4),
                "passed": is_match
            })

    accuracy = correct / total if total > 0 else 0.0

    # Calculate Macro Precision and Recall
    precisions = []
    recalls = []
    for c in (0, 1, 2):
        tp = class_stats[c]["tp"]
        fp = class_stats[c]["fp"]
        fn = class_stats[c]["fn"]
        p = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        r = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        precisions.append(p)
        recalls.append(r)

    macro_precision = float(np.mean(precisions))
    macro_recall = float(np.mean(recalls))

    return {
        "total_held_out": total,
        "correct": correct,
        "accuracy": round(accuracy, 4),
        "false_accepts": false_accepts,
        "false_rejects": false_rejects,
        "macro_precision": round(macro_precision, 4),
        "macro_recall": round(macro_recall, 4),
        "class_stats": class_stats,
        "details": results_detail
    }


def train_civic_validator(additional_epochs: int = 6, batch_size: int = 8, lr: float = 1.0e-4):
    device = torch.device("cpu")
    print("\nPreparing datasets and caching samples in RAM for fast, reliable execution...")
    train_samples, val_samples, held_out_paths = prepare_datasets()

    train_transform = T.Compose([
        T.Resize((224, 224)),
        T.RandomHorizontalFlip(),
        T.RandomRotation(10),
        T.ColorJitter(brightness=0.15, contrast=0.15, saturation=0.15),
        T.ToTensor(),
        T.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])

    eval_transform = T.Compose([
        T.Resize((224, 224)),
        T.ToTensor(),
        T.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])

    train_dataset = CivicImageDataset(train_samples, train_transform)
    val_dataset = CivicImageDataset(val_samples, eval_transform)

    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False)

    model = CivicValidator(num_classes=3, pretrained=False)

    best_val_acc = 0.0
    prior_epochs = 0

    # Resume from existing checkpoint if available
    if OUTPUT_MODEL_PATH.exists():
        print(f"\n[AI] Resuming CivicValidator from existing checkpoint: {OUTPUT_MODEL_PATH}")
        try:
            state = torch.load(OUTPUT_MODEL_PATH, map_location="cpu")
            model.load_state_dict(state)
            if METRICS_PATH.exists():
                with open(METRICS_PATH, "r") as mf:
                    old_m = json.load(mf)
                    prior_epochs = old_m.get("epochs", 10)
                    best_val_acc = old_m.get("best_val_accuracy", 0.9091)
            print(f"[AI] Successfully loaded weights (Prior Epochs: {prior_epochs}, Prior Best Val Acc: {best_val_acc:.4f})")
        except Exception as e:
            print(f"[AI] Error loading checkpoint: {e}. Starting fresh.")
            model = CivicValidator(num_classes=3, pretrained=True)
    else:
        model = CivicValidator(num_classes=3, pretrained=True)

    model.to(device)

    # Class weighting to balance classes: Class 0 (33), Class 1 (43), Class 2 (212)
    class_weights = torch.tensor([2.5, 2.2, 1.0]).float().to(device)
    criterion = nn.CrossEntropyLoss(weight=class_weights)
    optimizer = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=1e-3)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=additional_epochs)

    best_state = model.state_dict().copy()
    start_time = time.time()
    total_planned_epochs = prior_epochs + additional_epochs

    print(f"\nStarting Civic AI Training Resumption ({additional_epochs} additional epochs, target {total_planned_epochs} total)...")

    for ep in range(1, additional_epochs + 1):
        curr_total_epoch = prior_epochs + ep
        model.train()
        total_loss = 0.0
        correct = 0
        total = 0

        for imgs, labels, _ in train_loader:
            imgs, labels = imgs.to(device), labels.to(device)
            optimizer.zero_grad()
            outputs = model(imgs)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()

            total_loss += loss.item() * len(labels)
            preds = outputs.argmax(dim=1)
            correct += (preds == labels).sum().item()
            total += len(labels)

        scheduler.step()
        train_loss = total_loss / total
        train_acc = correct / total

        # Validation
        model.eval()
        val_loss = 0.0
        val_correct = 0
        val_total = 0

        with torch.no_grad():
            for imgs, labels, _ in val_loader:
                imgs, labels = imgs.to(device), labels.to(device)
                outputs = model(imgs)
                loss = criterion(outputs, labels)
                val_loss += loss.item() * len(labels)
                preds = outputs.argmax(dim=1)
                val_correct += (preds == labels).sum().item()
                val_total += len(labels)

        val_loss = val_loss / val_total
        val_acc = val_correct / val_total

        print(f"Epoch {curr_total_epoch:02d}/{total_planned_epochs:02d} (+{ep}) | Train Loss: {train_loss:.4f} Acc: {train_acc:.4f} | Val Loss: {val_loss:.4f} Acc: {val_acc:.4f}")

        if val_acc >= best_val_acc:
            best_val_acc = val_acc
            best_state = {k: v.cpu().clone() for k, v in model.state_dict().items()}

        gc.collect()

    elapsed = time.time() - start_time
    print(f"\nResumed training completed in {elapsed:.1f}s. Best Val Accuracy: {best_val_acc:.4f}")

    # Load best weights into model
    model.load_state_dict(best_state)

    # Evaluate on independent held-out test images
    print("\n--- Evaluating on Independent Held-Out Test Images ---")
    held_out_metrics = evaluate_held_out(model, device)
    print(f"Held-Out Test Accuracy: {held_out_metrics['accuracy']*100:.2f}% ({held_out_metrics['correct']}/{held_out_metrics['total_held_out']})")
    print(f"False Accepts (Non-civic/clean -> Defect): {held_out_metrics['false_accepts']}")
    print(f"False Rejects (Genuine defect -> Clean/Invalid): {held_out_metrics['false_rejects']}")
    print(f"Macro Precision: {held_out_metrics['macro_precision']:.4f} | Macro Recall: {held_out_metrics['macro_recall']:.4f}")

    for d in held_out_metrics["details"]:
        status = "PASS" if d["passed"] else "FAIL"
        print(f"  [{status}] {d['name']}: expected={d['expected']}, predicted={d['predicted']} (conf={d['confidence']:.3f})")

    # Save best production model (pure state_dict)
    os.makedirs(os.path.dirname(OUTPUT_MODEL_PATH), exist_ok=True)
    torch.save(best_state, OUTPUT_MODEL_PATH)
    print(f"\nSaved production CivicValidator model to: {OUTPUT_MODEL_PATH}")

    # Save complete checkpoint
    torch.save({
        "epoch": total_planned_epochs,
        "completed_epochs": total_planned_epochs,
        "model_state_dict": best_state,
        "best_val_accuracy": best_val_acc,
        "held_out_accuracy": held_out_metrics["accuracy"],
        "classes": {0: "NON_CIVIC_IMAGE", 1: "CIVIC_INFRASTRUCTURE_NO_ISSUE", 2: "GENUINE_CIVIC_ISSUE"}
    }, CHECKPOINT_PATH)
    print(f"Saved checkpoint with metadata to: {CHECKPOINT_PATH}")

    # Save metrics JSON
    metrics = {
        "model_name": "CivicValidator (MobileNetV3-Small)",
        "training_completed_percentage": "100%",
        "epochs_planned": total_planned_epochs,
        "epochs_completed": total_planned_epochs,
        "train_samples": len(train_samples),
        "val_samples": len(val_samples),
        "total_images_used": len(train_samples) + len(val_samples),
        "best_val_accuracy": round(best_val_acc, 4),
        "held_out_test_accuracy": held_out_metrics["accuracy"],
        "false_accepts": held_out_metrics["false_accepts"],
        "false_rejects": held_out_metrics["false_rejects"],
        "macro_precision": held_out_metrics["macro_precision"],
        "macro_recall": held_out_metrics["macro_recall"],
        "training_time_seconds": round(elapsed, 1),
        "held_out_evaluation": held_out_metrics,
        "classes": {
            "0": "NON_CIVIC_IMAGE",
            "1": "CIVIC_INFRASTRUCTURE_NO_ISSUE",
            "2": "GENUINE_CIVIC_ISSUE"
        }
    }
    with open(METRICS_PATH, "w") as f:
        json.dump(metrics, f, indent=2)
    print(f"Saved metrics to: {METRICS_PATH}")

    return model, metrics


if __name__ == "__main__":
    train_civic_validator(additional_epochs=6, batch_size=8, lr=1.0e-4)
