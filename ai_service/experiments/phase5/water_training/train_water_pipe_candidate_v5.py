"""
Phase 5 - Task 7 & 8: Water Pipeline Experimental Candidate Training & Evaluation
Architecture: MobileNetV3-Small Transfer Learning
Dataset: 83 deduplicated physical water pipe images (Stratified 70/15/15 split)
Candidate Checkpoint: ai_service/experiments/phase5/water_training/water_pipe_candidate_v5.pt
Status: EXPERIMENTAL — NOT APPROVED FOR PRODUCTION
"""

import os
import time
import json
import random
import hashlib
import platform
import numpy as np
from PIL import Image
from collections import Counter

import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from torchvision import models, transforms

# 1. Reproducibility Configuration
SEED = 42
random.seed(SEED)
np.random.seed(SEED)
torch.manual_seed(SEED)
if torch.cuda.is_available():
    torch.cuda.manual_seed_all(SEED)

LEAK_DIR = r"D:\NAGARSETU\leaking pipes"
NORMAL_DIR = r"D:\NAGARSETU\normal pipe images"
OUTPUT_DIR = r"ai_service\experiments\phase5\water_training"
CANDIDATE_MODEL_PATH = os.path.join(OUTPUT_DIR, "water_pipe_candidate_v5.pt")
METRICS_PATH = os.path.join(OUTPUT_DIR, "training_metrics_v5.json")

def compute_sha256(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

# 2. Dataset Definition
class WaterPipeDataset(Dataset):
    def __init__(self, items, transform=None):
        self.items = items
        self.transform = transform

    def __len__(self):
        return len(self.items)

    def __getitem__(self, idx):
        item = self.items[idx]
        img = Image.open(item["path"]).convert("RGB")
        if self.transform:
            img = self.transform(img)
        return img, item["class_id"], item["filename"]

# 3. Model Architecture (Matching MobileNetV3-Small structure)
class WaterPipeCandidateV5(nn.Module):
    def __init__(self, num_classes=2):
        super(WaterPipeCandidateV5, self).__init__()
        weights = models.MobileNet_V3_Small_Weights.DEFAULT
        self.backbone = models.mobilenet_v3_small(weights=weights)
        in_features = self.backbone.classifier[3].in_features
        self.backbone.classifier[3] = nn.Sequential(
            nn.Dropout(p=0.2),
            nn.Linear(in_features, num_classes)
        )

    def forward(self, x):
        return self.backbone(x)

def train_and_evaluate():
    print("=" * 80)
    print("PHASE 5: WATER PIPELINE EXPERIMENTAL CANDIDATE TRAINING")
    print("=" * 80)

    start_time = time.time()
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Execution Device: {device} ({torch.cuda.get_device_name(0) if torch.cuda.is_available() else platform.processor()})")

    # 4. Ingest and Deduplicate Images
    raw_items = []
    seen_hashes = {}
    duplicates = []

    # Class 0: normal (perfect_pipe), Class 1: leaking (water_leakage)
    for class_id, class_name, folder in [(0, "normal", NORMAL_DIR), (1, "leaking", LEAK_DIR)]:
        if not os.path.exists(folder):
            raise FileNotFoundError(f"Missing folder: {folder}")
        for fn in sorted(os.listdir(folder)):
            fp = os.path.join(folder, fn)
            if not os.path.isfile(fp) or not fn.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):
                continue
            h = compute_sha256(fp)
            if h in seen_hashes:
                duplicates.append({"file": fn, "dup_of": seen_hashes[h], "sha256": h})
                continue
            seen_hashes[h] = fn
            raw_items.append({
                "filename": fn,
                "path": fp,
                "class_id": class_id,
                "class_name": class_name,
                "sha256": h
            })

    print(f"Total Unique Images Ingested: {len(raw_items)} (Excluded {len(duplicates)} exact duplicates)")
    counts = Counter(x["class_name"] for x in raw_items)
    print(f"Class Breakdown: Normal={counts['normal']}, Leaking={counts['leaking']}")

    # 5. Stratified Split (70% Train, 15% Val, 15% Test)
    normals = [x for x in raw_items if x["class_id"] == 0]
    leakings = [x for x in raw_items if x["class_id"] == 1]

    random.seed(SEED)
    random.shuffle(normals)
    random.shuffle(leakings)

    n_train = int(len(normals) * 0.70)
    n_val = int(len(normals) * 0.15)
    train_normals = normals[:n_train]
    val_normals = normals[n_train:n_train + n_val]
    test_normals = normals[n_train + n_val:]

    l_train = int(len(leakings) * 0.70)
    l_val = int(len(leakings) * 0.15)
    train_leakings = leakings[:l_train]
    val_leakings = leakings[l_train:l_train + l_val]
    test_leakings = leakings[l_train + l_val:]

    train_set = train_normals + train_leakings
    val_set = val_normals + val_leakings
    test_set = test_normals + test_leakings

    random.shuffle(train_set)

    print(f"Splits Created: Train={len(train_set)}, Val={len(val_set)}, Test={len(test_set)}")

    # 6. Transforms & Augmentations
    train_transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.RandomHorizontalFlip(p=0.5),
        transforms.RandomVerticalFlip(p=0.2),
        transforms.RandomRotation(degrees=15),
        transforms.ColorJitter(brightness=0.15, contrast=0.15),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])

    eval_transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])

    train_loader = DataLoader(WaterPipeDataset(train_set, transform=train_transform), batch_size=8, shuffle=True)
    val_loader = DataLoader(WaterPipeDataset(val_set, transform=eval_transform), batch_size=8, shuffle=False)
    test_loader = DataLoader(WaterPipeDataset(test_set, transform=eval_transform), batch_size=8, shuffle=False)

    # 7. Model, Optimizer, Loss with class weighting
    model = WaterPipeCandidateV5(num_classes=2).to(device)

    # Calculate class weights for imbalance (leaking is ~2x normal)
    weight_normal = len(train_set) / (2.0 * len(train_normals))
    weight_leaking = len(train_set) / (2.0 * len(train_leakings))
    class_weights = torch.tensor([weight_normal, weight_leaking], dtype=torch.float).to(device)
    criterion = nn.CrossEntropyLoss(weight=class_weights)

    optimizer = torch.optim.AdamW(model.parameters(), lr=1e-3, weight_decay=1e-4)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=15)

    epochs = 15
    best_val_f1 = 0.0
    best_state_dict = None
    history = []

    print(f"\nTraining WaterPipeCandidateV5 for {epochs} epochs...")
    for epoch in range(1, epochs + 1):
        model.train()
        train_loss = 0.0
        train_correct = 0
        total_train = 0

        for imgs, labels, _ in train_loader:
            imgs, labels = imgs.to(device), labels.to(device)
            optimizer.zero_grad()
            outputs = model(imgs)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()

            train_loss += loss.item() * imgs.size(0)
            preds = torch.argmax(outputs, dim=1)
            train_correct += (preds == labels).sum().item()
            total_train += imgs.size(0)

        scheduler.step()
        epoch_train_loss = train_loss / total_train
        epoch_train_acc = train_correct / total_train

        # Validation phase
        model.eval()
        val_loss = 0.0
        val_correct = 0
        total_val = 0
        val_preds, val_targets = [], []

        with torch.no_grad():
            for imgs, labels, _ in val_loader:
                imgs, labels = imgs.to(device), labels.to(device)
                outputs = model(imgs)
                loss = criterion(outputs, labels)
                val_loss += loss.item() * imgs.size(0)
                preds = torch.argmax(outputs, dim=1)
                val_correct += (preds == labels).sum().item()
                total_val += imgs.size(0)
                val_preds.extend(preds.cpu().numpy())
                val_targets.extend(labels.cpu().numpy())

        epoch_val_loss = val_loss / total_val
        epoch_val_acc = val_correct / total_val

        # Calculate macro F1 for validation
        from sklearn.metrics import f1_score
        val_f1 = float(f1_score(val_targets, val_preds, average="macro", zero_division=0))

        history.append({
            "epoch": epoch,
            "train_loss": round(epoch_train_loss, 4),
            "train_acc": round(epoch_train_acc, 4),
            "val_loss": round(epoch_val_loss, 4),
            "val_acc": round(epoch_val_acc, 4),
            "val_f1": round(val_f1, 4)
        })

        if val_f1 > best_val_f1:
            best_val_f1 = val_f1
            best_state_dict = model.state_dict().copy()

        if epoch % 5 == 0 or epoch == epochs:
            print(f"Epoch {epoch:02d}/{epochs:02d} | Train Loss: {epoch_train_loss:.4f} Acc: {epoch_train_acc:.3f} | Val Loss: {epoch_val_loss:.4f} Acc: {epoch_val_acc:.3f} F1: {val_f1:.3f}")

    # Load best weights
    if best_state_dict:
        model.load_state_dict(best_state_dict)

    train_duration = time.time() - start_time
    print(f"\nTraining completed in {train_duration:.2f} seconds. Best Val F1: {best_val_f1:.4f}")

    # 8. Save Isolated Candidate Checkpoint
    checkpoint = {
        "candidate_name": "water_pipe_candidate_v5.pt",
        "domain": "water_pipeline_damage_detection",
        "model_architecture": "MobileNetV3-Small (Custom Head)",
        "num_classes": 2,
        "class_names": {0: "perfect_pipe", 1: "water_leakage"},
        "classes": ["perfect_pipe", "water_leakage"],
        "input_size": (224, 224),
        "mean": [0.485, 0.456, 0.406],
        "std": [0.229, 0.224, 0.225],
        "random_seed": SEED,
        "epochs_trained": epochs,
        "training_duration_seconds": round(train_duration, 2),
        "hardware": f"{platform.system()} {platform.machine()} ({device})",
        "dataset_version": "v5.0_deduplicated_83_samples",
        "train_samples": len(train_set),
        "val_samples": len(val_set),
        "test_samples": len(test_set),
        "approval_status": "EXPERIMENTAL — NOT APPROVED FOR PRODUCTION",
        "model_state_dict": model.state_dict()
    }
    torch.save(checkpoint, CANDIDATE_MODEL_PATH)
    candidate_sha = compute_sha256(CANDIDATE_MODEL_PATH)
    candidate_size_mb = os.path.getsize(CANDIDATE_MODEL_PATH) / (1024 * 1024)
    print(f"Saved Candidate Checkpoint to: {CANDIDATE_MODEL_PATH}")
    print(f"  SHA-256: {candidate_sha}")
    print(f"  Size: {candidate_size_mb:.2f} MB")

    # 9. Evaluate on Frozen Independent Test Set
    from sklearn.metrics import precision_recall_fscore_support, confusion_matrix, accuracy_score

    model.eval()
    test_preds, test_targets, test_latencies = [], [], []

    with torch.no_grad():
        for imgs, labels, fnames in test_loader:
            imgs = imgs.to(device)
            t0 = time.perf_counter()
            outputs = model(imgs)
            t_lat = (time.perf_counter() - t0) * 1000 / imgs.size(0)
            preds = torch.argmax(outputs, dim=1)
            test_preds.extend(preds.cpu().numpy())
            test_targets.extend(labels.numpy())
            test_latencies.extend([t_lat] * imgs.size(0))

    acc = float(accuracy_score(test_targets, test_preds))
    prec, rec, f1, _ = precision_recall_fscore_support(test_targets, test_preds, average="macro", zero_division=0)
    cm = confusion_matrix(test_targets, test_preds).tolist()
    mean_lat = float(np.mean(test_latencies))
    p95_lat = float(np.percentile(test_latencies, 95))

    p_per_class, r_per_class, f1_per_class, _ = precision_recall_fscore_support(test_targets, test_preds, average=None, zero_division=0)

    eval_results = {
        "candidate": {
            "name": "water_pipe_candidate_v5.pt",
            "sha256": candidate_sha,
            "accuracy": round(acc, 4),
            "macro_f1": round(float(f1), 4),
            "macro_precision": round(float(prec), 4),
            "macro_recall": round(float(rec), 4),
            "per_class": {
                "perfect_pipe (normal)": {
                    "precision": round(float(p_per_class[0]), 4),
                    "recall": round(float(r_per_class[0]), 4),
                    "f1": round(float(f1_per_class[0]), 4)
                },
                "water_leakage": {
                    "precision": round(float(p_per_class[1]), 4),
                    "recall": round(float(r_per_class[1]), 4),
                    "f1": round(float(f1_per_class[1]), 4)
                }
            },
            "confusion_matrix": cm,
            "mean_latency_ms": round(mean_lat, 2),
            "p95_latency_ms": round(p95_lat, 2),
            "model_size_mb": round(candidate_size_mb, 2)
        },
        "training_history": history,
        "test_set_files": [x["filename"] for x in test_set],
        "hardware_specs": {
            "platform": platform.platform(),
            "processor": platform.processor(),
            "device": str(device)
        }
    }

    with open(METRICS_PATH, "w") as f:
        json.dump(eval_results, f, indent=2)
    print(f"Saved evaluation metrics to: {METRICS_PATH}")
    print(f"\nCANDIDATE TEST RESULTS:")
    print(f"  Accuracy: {acc:.4f} | Macro F1: {f1:.4f} | Mean Latency: {mean_lat:.2f} ms")
    print(f"  Confusion Matrix: {cm}")

    return eval_results

if __name__ == "__main__":
    train_and_evaluate()

