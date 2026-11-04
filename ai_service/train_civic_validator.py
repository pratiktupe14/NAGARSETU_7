import os
import sys
import time
import json
import random
from pathlib import Path
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
METRICS_PATH = BASE_DIR / "model" / "civic_validator_metrics.json"

# Dataset Directories
RANDOM_DIR = r"D:\NAGARSETU\random iamges"
ROAD_DIR = r"D:\NAGARSETU\road"
DRAINAGE_DIR = r"D:\NAGARSETU\drainage images"
LEAK_DIR = r"D:\NAGARSETU\leaking pipes"
NORMAL_PIPE_DIR = r"D:\NAGARSETU\normal pipe images"
GARBAGE_DIR = r"D:\NAGARSETU\garbage waste"
DRAINAGE_CATALOG = BASE_DIR / "data" / "drainage_catalog.json"

# Held-out evaluation images (MUST NEVER BE IN TRAIN/VAL)
HELD_OUT_FILES = {
    os.path.normpath(r"D:\NAGARSETU\road\Pothole_01.jpg"),
    os.path.normpath(r"D:\NAGARSETU\drainage images\images (1).jpg"),
    os.path.normpath(r"D:\NAGARSETU\leaking pipes\water-leaking-hole-industrial-hose-260nw-2609724773.jpg"),
    os.path.normpath(r"D:\NAGARSETU\garbage waste\images.jpg"),
    os.path.normpath(r"D:\NAGARSETU\random iamges\WhatsApp Image 2026-11-04 at 5.47.10 AM.jpeg"),
    os.path.normpath(r"D:\NAGARSETU\drainage images\images (10).jpg"),
    os.path.normpath(str(BASE_DIR / "tests" / "fixtures" / "test_animal_cat.jpg")),
    os.path.normpath(r"D:\NAGARSETU\random iamges\WhatsApp Image 2026-11-04 at 5.40.49 AM (1).jpeg"),
    os.path.normpath(str(BASE_DIR / "tests" / "fixtures" / "test_unrelated_vehicle.jpg")),
    os.path.normpath(r"D:\NAGARSETU\random iamges\WhatsApp Image 2026-11-04 at 5.46.41 AM (1).jpeg"),
    os.path.normpath(r"D:\NAGARSETU\road\16tvsbg03-City-17TVTV_ROAD.jpg.jpg")
}

DUPLICATES_RANDOM = {
    "WhatsApp Image 2026-11-04 at 5.46.37 AM.jpeg",
    "WhatsApp Image 2026-11-04 at 5.46.38 AM (1).jpeg",
    "WhatsApp Image 2026-11-04 at 5.46.38 AM (2).jpeg",
    "WhatsApp Image 2026-11-04 at 5.46.38 AM.jpeg"
}


class CivicImageDataset(Dataset):
    def __init__(self, samples, transform=None):
        self.samples = samples
        self.transform = transform

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        file_path, label = self.samples[idx]
        img = Image.open(file_path).convert("RGB")
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


def prepare_datasets():
    # Class 0: NON_CIVIC_IMAGE
    non_civic_files = []
    if os.path.exists(RANDOM_DIR):
        for f in os.listdir(RANDOM_DIR):
            if not f.lower().endswith(('.jpg', '.jpeg', '.png')):
                continue
            if f in DUPLICATES_RANDOM:
                continue
            # Skip clean road (classified as CIVIC_INFRASTRUCTURE_NO_ISSUE / held-out test)
            if f == "WhatsApp Image 2026-11-04 at 5.47.10 AM.jpeg":
                continue
            p = os.path.normpath(os.path.join(RANDOM_DIR, f))
            if p not in HELD_OUT_FILES:
                non_civic_files.append(p)

    # Class 1: CIVIC_INFRASTRUCTURE_NO_ISSUE
    clean_infra_files = []
    if os.path.exists(NORMAL_PIPE_DIR):
        for f in os.listdir(NORMAL_PIPE_DIR):
            if f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):
                p = os.path.normpath(os.path.join(NORMAL_PIPE_DIR, f))
                if p not in HELD_OUT_FILES:
                    clean_infra_files.append(p)

    if os.path.exists(DRAINAGE_CATALOG):
        with open(DRAINAGE_CATALOG, 'r') as f:
            dcat = json.load(f).get('catalog', {})
        for fname, lbl in dcat.items():
            if lbl == 'NORMAL_DRAIN':
                p = os.path.normpath(os.path.join(DRAINAGE_DIR, fname))
                if os.path.exists(p) and p not in HELD_OUT_FILES:
                    clean_infra_files.append(p)

    # Class 2: GENUINE_CIVIC_ISSUE
    civic_defect_files = []
    # Road damage
    if os.path.exists(ROAD_DIR):
        for f in os.listdir(ROAD_DIR):
            if f.lower().endswith(('.jpg', '.jpeg', '.png')):
                p = os.path.normpath(os.path.join(ROAD_DIR, f))
                if p not in HELD_OUT_FILES:
                    civic_defect_files.append(p)

    # Leaking pipes
    if os.path.exists(LEAK_DIR):
        for f in os.listdir(LEAK_DIR):
            if f.lower().endswith(('.jpg', '.jpeg', '.png')):
                p = os.path.normpath(os.path.join(LEAK_DIR, f))
                if p not in HELD_OUT_FILES:
                    civic_defect_files.append(p)

    # Drainage defects
    if os.path.exists(DRAINAGE_CATALOG):
        with open(DRAINAGE_CATALOG, 'r') as f:
            dcat = json.load(f).get('catalog', {})
        for fname, lbl in dcat.items():
            if lbl != 'NORMAL_DRAIN':
                p = os.path.normpath(os.path.join(DRAINAGE_DIR, fname))
                if os.path.exists(p) and p not in HELD_OUT_FILES:
                    civic_defect_files.append(p)

    # Garbage waste
    if os.path.exists(GARBAGE_DIR):
        for f in os.listdir(GARBAGE_DIR):
            if f.lower().endswith(('.jpg', '.jpeg', '.png')):
                p = os.path.normpath(os.path.join(GARBAGE_DIR, f))
                if p not in HELD_OUT_FILES:
                    civic_defect_files.append(p)

    print(f"Dataset Counts (excluding held-out test images):")
    print(f"  Class 0 (NON_CIVIC_IMAGE):            {len(non_civic_files)}")
    print(f"  Class 1 (CIVIC_INFRASTRUCTURE_NO_ISSUE): {len(clean_infra_files)}")
    print(f"  Class 2 (GENUINE_CIVIC_ISSUE):         {len(civic_defect_files)}")
    print(f"  Held-out Test Images:                 {len(HELD_OUT_FILES)}")

    # Split train and validation (85% train, 15% validation)
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

    return train_samples, val_samples


def train_civic_validator(epochs=12, batch_size=8, lr=3e-4):
    train_samples, val_samples = prepare_datasets()

    train_transform = T.Compose([
        T.Resize((224, 224)),
        T.RandomHorizontalFlip(),
        T.RandomVerticalFlip(p=0.2),
        T.RandomRotation(15),
        T.ColorJitter(brightness=0.2, contrast=0.2, saturation=0.2),
        T.ToTensor(),
        T.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])

    eval_transform = T.Compose([
        T.Resize((224, 224)),
        T.ToTensor(),
        T.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])

    train_loader = DataLoader(CivicImageDataset(train_samples, train_transform), batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(CivicImageDataset(val_samples, eval_transform), batch_size=batch_size, shuffle=False)

    model = CivicValidator(num_classes=3, pretrained=True)
    device = torch.device("cpu")
    model.to(device)

    # Class weighting to balance smaller classes
    class_weights = torch.tensor([2.0, 2.5, 1.0]).float()
    criterion = nn.CrossEntropyLoss(weight=class_weights)
    optimizer = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=1e-3)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs)

    best_val_acc = 0.0
    best_state = None

    print("\nStarting CivicValidator Training...")
    start_time = time.time()

    for epoch in range(1, epochs + 1):
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

        print(f"Epoch {epoch:02d}/{epochs:02d} | Train Loss: {train_loss:.4f} Acc: {train_acc:.4f} | Val Loss: {val_loss:.4f} Acc: {val_acc:.4f}")

        if val_acc >= best_val_acc:
            best_val_acc = val_acc
            best_state = model.state_dict().copy()

    elapsed = time.time() - start_time
    print(f"\nTraining completed in {elapsed:.1f}s. Best Val Accuracy: {best_val_acc:.4f}")

    # Save best model
    os.makedirs(os.path.dirname(OUTPUT_MODEL_PATH), exist_ok=True)
    torch.save(best_state or model.state_dict(), OUTPUT_MODEL_PATH)
    print(f"Saved CivicValidator weights to: {OUTPUT_MODEL_PATH}")

    # Save metrics
    metrics = {
        "model_name": "CivicValidator (MobileNetV3-Small)",
        "epochs": epochs,
        "train_samples": len(train_samples),
        "val_samples": len(val_samples),
        "best_val_accuracy": round(best_val_acc, 4),
        "training_time_seconds": round(elapsed, 1),
        "classes": {
            0: "NON_CIVIC_IMAGE",
            1: "CIVIC_INFRASTRUCTURE_NO_ISSUE",
            2: "GENUINE_CIVIC_ISSUE"
        }
    }
    with open(METRICS_PATH, "w") as f:
        json.dump(metrics, f, indent=2)

    return model


if __name__ == "__main__":
    train_civic_validator(epochs=10, batch_size=8, lr=3e-4)
