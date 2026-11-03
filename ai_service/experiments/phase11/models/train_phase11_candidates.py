"""
Phase 11 - Task 4: Model Redesign and Experimental Candidate Training
Trains:
1. Candidate v6 (3-Class Classifier): MobileNetV3-Small with balanced multi-class head.
2. Candidate D (Multi-Stage Classifier): Stage 1 Anomaly Detection -> Stage 2 Liquid vs Surface Disambiguation.

Strictly isolated in ai_service/experiments/phase11/models/.
Zero changes to production model_manager.py or production weights.
"""

import os
import time
import json
import random
import copy
from collections import Counter
import numpy as np
from PIL import Image

import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from torchvision import models, transforms

# Paths
PHASE11_DIR = r"ai_service\experiments\phase11"
MODELS_DIR = os.path.join(PHASE11_DIR, "models")
DATASET_DIR = os.path.join(PHASE11_DIR, "dataset")
SPLIT_MANIFEST_PATH = os.path.join(DATASET_DIR, "water_phase11_group_split_manifest.json")

os.makedirs(MODELS_DIR, exist_ok=True)

SEED = 42
random.seed(SEED)
np.random.seed(SEED)
torch.manual_seed(SEED)

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# Dataset class
class WaterPipeDataset(Dataset):
    def __init__(self, items, transform=None):
        self.items = items
        self.transform = transform

    def __len__(self):
        return len(self.items)

    def __getitem__(self, idx):
        it = self.items[idx]
        img_path = it["filepath"]
        img = Image.open(img_path).convert("RGB")
        if self.transform:
            img = self.transform(img)
        # Return image, 3class label, binary label, subscenario, parent_id
        return img, it["class_id_3class"], it["class_id_binary"], it["subscenario"], it["parent_id"]

# Architecture C: Candidate v6 (3-Class MobileNetV3-Small)
class WaterPipeCandidateV6_3Class(nn.Module):
    def __init__(self, num_classes=3):
        super(WaterPipeCandidateV6_3Class, self).__init__()
        weights = models.MobileNet_V3_Small_Weights.DEFAULT
        self.backbone = models.mobilenet_v3_small(weights=weights)
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

# Architecture D: Multi-Stage Classifier
class WaterPipeMultiStageV1(nn.Module):
    """
    Two-Stage Architecture:
    Stage 1: Surface Anomaly Detector (0: normal, 1: anomaly)
    Stage 2: Disambiguation Classifier (0: surface rust/condensation, 1: active leak)
    """
    def __init__(self):
        super(WaterPipeMultiStageV1, self).__init__()
        # Shared feature extractor
        weights = models.MobileNet_V3_Small_Weights.DEFAULT
        base = models.mobilenet_v3_small(weights=weights)
        self.features = base.features
        self.avgpool = base.avgpool
        
        # Stage 1 Head (Anomaly Detection)
        self.stage1_head = nn.Sequential(
            nn.Linear(576, 128),
            nn.Hardswish(),
            nn.Dropout(p=0.2),
            nn.Linear(128, 2)  # 0: normal, 1: anomaly
        )
        
        # Stage 2 Head (Liquid Leak vs Surface Condition)
        self.stage2_head = nn.Sequential(
            nn.Linear(576, 128),
            nn.Hardswish(),
            nn.Dropout(p=0.2),
            nn.Linear(128, 2)  # 0: dry rust/condensation, 1: active leak
        )

    def forward(self, x):
        feat = self.features(x)
        feat = self.avgpool(feat)
        feat = torch.flatten(feat, 1)
        
        logits_s1 = self.stage1_head(feat)
        logits_s2 = self.stage2_head(feat)
        return logits_s1, logits_s2

def train_candidate_v6(train_items, val_items, epochs=25, batch_size=8):
    print("\n--- Training Candidate v6 (3-Class MobileNetV3-Small) ---")
    
    train_transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.RandomHorizontalFlip(),
        transforms.RandomRotation(15),
        transforms.ColorJitter(brightness=0.15, contrast=0.15, saturation=0.15),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
    ])
    
    val_transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
    ])
    
    train_ds = WaterPipeDataset(train_items, transform=train_transform)
    val_ds = WaterPipeDataset(val_items, transform=val_transform)
    
    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(val_ds, batch_size=batch_size, shuffle=False)
    
    # Compute inverse class frequencies for balanced loss
    labels = [it["class_id_3class"] for it in train_items]
    counts = Counter(labels)
    total = len(labels)
    class_weights = [total / (3.0 * max(1, counts[c])) for c in range(3)]
    # Clamp weights
    class_weights = [min(max(w, 0.5), 3.0) for w in class_weights]
    weights_tensor = torch.tensor(class_weights, dtype=torch.float).to(DEVICE)
    print(f"Class counts in train: {dict(counts)}")
    print(f"Computed loss weights: {[round(w, 3) for w in class_weights]}")
    
    model = WaterPipeCandidateV6_3Class(num_classes=3).to(DEVICE)
    criterion = nn.CrossEntropyLoss(weight=weights_tensor)
    optimizer = torch.optim.AdamW(model.parameters(), lr=1e-4, weight_decay=1e-4)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs)
    
    best_val_f1 = -1.0
    best_model_weights = None
    training_log = []
    
    for epoch in range(1, epochs + 1):
        model.train()
        train_loss = 0.0
        correct = 0
        total_samples = 0
        
        for imgs, labels_3c, _, _, _ in train_loader:
            imgs, labels_3c = imgs.to(DEVICE), labels_3c.to(DEVICE)
            optimizer.zero_grad()
            outputs = model(imgs)
            loss = criterion(outputs, labels_3c)
            loss.backward()
            optimizer.step()
            
            train_loss += loss.item() * imgs.size(0)
            preds = outputs.argmax(dim=1)
            correct += (preds == labels_3c).sum().item()
            total_samples += imgs.size(0)
            
        scheduler.step()
        train_acc = correct / total_samples
        train_loss = train_loss / total_samples
        
        # Validation
        model.eval()
        val_loss = 0.0
        val_correct = 0
        val_total = 0
        all_preds = []
        all_targets = []
        
        with torch.no_grad():
            for imgs, labels_3c, _, _, _ in val_loader:
                imgs, labels_3c = imgs.to(DEVICE), labels_3c.to(DEVICE)
                outputs = model(imgs)
                loss = criterion(outputs, labels_3c)
                val_loss += loss.item() * imgs.size(0)
                preds = outputs.argmax(dim=1)
                val_correct += (preds == labels_3c).sum().item()
                val_total += imgs.size(0)
                all_preds.extend(preds.cpu().numpy())
                all_targets.extend(labels_3c.cpu().numpy())
                
        val_acc = val_correct / val_total
        val_loss = val_loss / val_total
        
        # Compute Macro F1
        f1s = []
        for c in range(3):
            tp = sum((p == c and t == c) for p, t in zip(all_preds, all_targets))
            fp = sum((p == c and t != c) for p, t in zip(all_preds, all_targets))
            fn = sum((p != c and t == c) for p, t in zip(all_preds, all_targets))
            prec = tp / (tp + fp) if (tp + fp) > 0 else 0.0
            rec = tp / (tp + fn) if (tp + fn) > 0 else 0.0
            f1 = 2 * prec * rec / (prec + rec) if (prec + rec) > 0 else 0.0
            if (tp + fn) > 0: # only include classes present in targets
                f1s.append(f1)
        val_macro_f1 = np.mean(f1s) if f1s else 0.0
        
        if val_macro_f1 > best_val_f1:
            best_val_f1 = val_macro_f1
            best_model_weights = copy.deepcopy(model.state_dict())
            
        training_log.append({
            "epoch": epoch,
            "train_loss": round(train_loss, 4),
            "train_acc": round(train_acc, 4),
            "val_loss": round(val_loss, 4),
            "val_acc": round(val_acc, 4),
            "val_macro_f1": round(val_macro_f1, 4)
        })
        if epoch % 5 == 0 or epoch == epochs:
            print(f"Epoch {epoch:2d}/{epochs:2d} | Train Loss: {train_loss:.4f} Acc: {train_acc:.3f} | Val Loss: {val_loss:.4f} Acc: {val_acc:.3f} F1: {val_macro_f1:.3f}")

    # Load best weights
    if best_model_weights is not None:
        model.load_state_dict(best_model_weights)
        
    cand_path = os.path.join(MODELS_DIR, "water_pipe_candidate_v6_3class.pt")
    torch.save({
        "model_architecture": "WaterPipeCandidateV6_3Class",
        "num_classes": 3,
        "classes": ["normal_pipe", "pipe_leak", "rusted_pipe"],
        "model_state_dict": model.state_dict(),
        "best_val_macro_f1": best_val_f1,
        "training_history": training_log
    }, cand_path)
    print(f"Saved Candidate v6 3-class checkpoint to: {cand_path}")
    return cand_path, training_log

def train_multistage_v1(train_items, val_items, epochs=25, batch_size=8):
    print("\n--- Training Candidate D (Multi-Stage Classifier) ---")
    
    train_transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.RandomHorizontalFlip(),
        transforms.RandomRotation(15),
        transforms.ColorJitter(brightness=0.15, contrast=0.15, saturation=0.15),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
    ])
    
    val_transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
    ])
    
    train_ds = WaterPipeDataset(train_items, transform=train_transform)
    val_ds = WaterPipeDataset(val_items, transform=val_transform)
    
    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(val_ds, batch_size=batch_size, shuffle=False)
    
    model = WaterPipeMultiStageV1().to(DEVICE)
    crit_s1 = nn.CrossEntropyLoss()
    crit_s2 = nn.CrossEntropyLoss()
    optimizer = torch.optim.AdamW(model.parameters(), lr=1e-4, weight_decay=1e-4)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs)
    
    best_val_score = -1.0
    best_weights = None
    
    for epoch in range(1, epochs + 1):
        model.train()
        total_loss = 0.0
        
        for imgs, labels_3c, labels_bin, _, _ in train_loader:
            imgs = imgs.to(DEVICE)
            # Stage 1 Target: 0 if clean normal, 1 if anomaly (leak or rust)
            t_s1 = torch.tensor([1 if l != 0 else 0 for l in labels_3c], dtype=torch.long).to(DEVICE)
            # Stage 2 Target: 1 if active leak, 0 if dry rust/surface condition
            t_s2 = torch.tensor([1 if l == 1 else 0 for l in labels_3c], dtype=torch.long).to(DEVICE)
            
            optimizer.zero_grad()
            logits_s1, logits_s2 = model(imgs)
            loss1 = crit_s1(logits_s1, t_s1)
            loss2 = crit_s2(logits_s2, t_s2)
            loss = loss1 + loss2
            loss.backward()
            optimizer.step()
            total_loss += loss.item() * imgs.size(0)
            
        scheduler.step()
        
        # Validation
        model.eval()
        s1_correct = 0
        s2_correct = 0
        total_val = 0
        with torch.no_grad():
            for imgs, labels_3c, _, _, _ in val_loader:
                imgs = imgs.to(DEVICE)
                t_s1 = torch.tensor([1 if l != 0 else 0 for l in labels_3c], dtype=torch.long).to(DEVICE)
                t_s2 = torch.tensor([1 if l == 1 else 0 for l in labels_3c], dtype=torch.long).to(DEVICE)
                logits_s1, logits_s2 = model(imgs)
                p1 = logits_s1.argmax(dim=1)
                p2 = logits_s2.argmax(dim=1)
                s1_correct += (p1 == t_s1).sum().item()
                s2_correct += (p2 == t_s2).sum().item()
                total_val += imgs.size(0)
                
        val_score = (s1_correct + s2_correct) / (2.0 * total_val)
        if val_score > best_val_score:
            best_val_score = val_score
            best_weights = copy.deepcopy(model.state_dict())
            
        if epoch % 5 == 0 or epoch == epochs:
            print(f"Stage Epoch {epoch:2d}/{epochs:2d} | Loss: {total_loss/len(train_ds):.4f} | Val S1 Acc: {s1_correct/total_val:.3f} S2 Acc: {s2_correct/total_val:.3f}")

    if best_weights is not None:
        model.load_state_dict(best_weights)
        
    ms_path = os.path.join(MODELS_DIR, "water_pipe_multistage_v1.pt")
    torch.save({
        "model_architecture": "WaterPipeMultiStageV1",
        "description": "Two-stage Anomaly Detector + Liquid Disambiguator",
        "model_state_dict": model.state_dict(),
        "best_val_score": best_val_score
    }, ms_path)
    print(f"Saved Multi-Stage Candidate checkpoint to: {ms_path}")
    return ms_path

def main():
    print("=" * 80)
    print("PHASE 11: WATER AI MODEL REDESIGN & CANDIDATE TRAINING")
    print("=" * 80)
    
    with open(SPLIT_MANIFEST_PATH, "r") as f:
        split_data = json.load(f)
        
    train_items = split_data["splits"]["train"]
    val_items = split_data["splits"]["val"]
    
    print(f"Loaded {len(train_items)} train parent images, {len(val_items)} val parent images.")
    
    cand_v6_path, hist_v6 = train_candidate_v6(train_items, val_items, epochs=20)
    ms_path = train_multistage_v1(train_items, val_items, epochs=20)
    
    print("\nPhase 11 Model Training Completed Successfully!")
    print(f"  Candidate v6 (3-Class): {cand_v6_path}")
    print(f"  Candidate D (Multi-Stage): {ms_path}")

if __name__ == "__main__":
    main()

