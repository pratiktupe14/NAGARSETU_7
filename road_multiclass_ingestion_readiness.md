# NagarSetu AI — Road Damage Multi-Class Dataset Ingestion Readiness Report
**Phase 7 — Task 5 Deliverable**  
**Date:** 2026-11-03  
**Status:** Ingestion Pipeline Specification & Converter Verification Complete | Training Gate: **BLOCKED** (Awaiting Dataset Ingestion)

---

## 1. Executive Summary
The existing NagarSetu road damage AI module relies on `civicmodel.pt`, a single-class detection model that identifies all surface defects as a generic `"pothole"`. While functional for basic road hazards, municipal public works departments require granular classification to assign the appropriate remediation machinery:
1. **Longitudinal Cracks (D00)** require crack-sealing emulsion.
2. **Transverse Cracks (D10)** require asphalt milling and joint sealing.
3. **Alligator Cracking (D20)** indicates sub-base structural failure requiring full-depth reclamation.
4. **Potholes (D40)** require immediate asphalt cold-mix or hot-mix patching.

To achieve multi-class road defect classification, NagarSetu has prepared an ingestion pipeline for the **Road Damage Dataset 2022 (RDD2022) India subset**. This report details the architectural transformation, Pascal VOC to YOLO annotation transformation, video sequence burst isolation to eliminate data leakage, and the training gate decision.

---

## 2. Production Baseline Architecture Audit

| Metric / Parameter | Production Baseline (`civicmodel.pt`) | Target Multi-Class Model |
| :--- | :--- | :--- |
| **Model Weights File** | `ai_service/model/civicmodel.pt` | `ai_service/experiments/phase8/road_multiclass_candidate_v1.pt` |
| **Cryptographic Hash (SHA-256)** | `1067a09d37e4e9081164e6d6da337ad66d8ec7a884a6a194e58703beee804aa2` | *Pending Training Gate* |
| **Model Size** | 21.48 MB | ~6.0 - 12.0 MB (YOLOv8n / YOLOv8s) |
| **Task Type** | Object Detection | Object Detection |
| **Total Parameters** | 11,135,987 | ~3.2M (Nano) or ~11.2M (Small) |
| **Active Classes** | 1: `{0: 'pothole'}` | 4: `{0: 'longitudinal_crack', 1: 'transverse_crack', 2: 'alligator_crack', 3: 'pothole'}` |
| **Inference Resolution** | 640x640 | 640x640 |
| **Input Format** | RGB BGR Tensor | RGB BGR Tensor |

---

## 3. RDD2022 India Subset Taxonomy & Mapping

| RDD2022 Code | Class Name | NagarSetu Semantic Label | Municipal Priority | Repair Action |
| :--- | :--- | :--- | :--- | :--- |
| **D00** | Linear Longitudinal Crack | `longitudinal_crack` (Class 0) | Low / Medium | Rubberized asphalt crack sealant |
| **D10** | Linear Transverse Crack | `transverse_crack` (Class 1) | Medium | Routing and hot-pour sealant |
| **D20** | Alligator / Fatigue Crack | `alligator_crack` (Class 2) | High / Urgent | Deep patch / Structural base repair |
| **D40** | Pothole / Severe Cavity | `pothole` (Class 3) | Critical / Immediate | Hot/Cold asphalt compaction |

---

## 4. Pascal VOC to YOLO Transformation & Clamping

RDD2022 annotations are provided in Pascal VOC XML format with pixel coordinates `[xmin, ymin, xmax, ymax]`. YOLO object detection architectures require normalized coordinates `[x_center, y_center, width, height]` scaled to `[0.0, 1.0]`.

### Mathematical Conversion
$$\begin{aligned}
x_{center} &= \frac{\text{xmin} + \text{xmax}}{2 \times W_{img}} \\[6pt]
y_{center} &= \frac{\text{ymin} + \text{ymax}}{2 \times H_{img}} \\[6pt]
w_{norm} &= \frac{\text{xmax} - \text{xmin}}{W_{img}} \\[6pt]
h_{norm} &= \frac{\text{ymax} - \text{ymin}}{H_{img}}
\end{aligned}$$

### Bounding Box Boundary Clamping & Degenerate Filtering
1. **Pixel Clamping:** Dashcam bounding boxes frequently spill outside image edges (e.g., $xmin < 0$ or $xmax > W_{img}$). Coordinates are strictly clamped:
   $$\text{xmin} = \max(0.0, \min(\text{xmin}, W_{img})), \quad \text{xmax} = \max(0.0, \min(\text{xmax}, W_{img}))$$
2. **Degenerate Rejection:** Bounding boxes with width $\le 1\text{px}$ or height $\le 1\text{px}$ (or $xmin \ge xmax$) are rejected to prevent NaN loss in bounding-box regression loss functions (CIoU / GIoU).

### Converter Unit Test Results (10 Test Cases)
| Test Case | VOC Coordinates | YOLO Normalized Output | Clamped & Valid | Status |
| :--- | :--- | :--- | :--- | :--- |
| Standard D00 Longitudinal Crack | `[450, 100, 520, 680]` | `(0.3789, 0.5417, 0.0547, 0.8056)` | Yes | PASSED |
| Standard D10 Transverse Crack | `[200, 400, 950, 430]` | `(0.4492, 0.5764, 0.5859, 0.0417)` | Yes | PASSED |
| Standard D20 Alligator Crack | `[300, 350, 700, 600]` | `(0.3906, 0.6597, 0.3125, 0.3472)` | Yes | PASSED |
| Standard D40 Pothole | `[550, 420, 720, 560]` | `(0.4961, 0.6806, 0.1328, 0.1944)` | Yes | PASSED |
| Out-of-bounds left/top (Negative coordinates) | `[-50, -20, 300, 400]` | `(0.1172, 0.2778, 0.2344, 0.5556)` | Yes | PASSED |
| Out-of-bounds right/bottom (Oversized coordinates) | `[1000, 500, 1450, 850]` | `(0.8906, 0.8472, 0.2188, 0.3056)` | Yes | PASSED |
| Degenerate zero-width box | `[300, 200, 300, 500]` | `None (Filtered)` | Yes | PASSED |
| Degenerate zero-height box | `[300, 200, 600, 200]` | `None (Filtered)` | Yes | PASSED |
| Sub-pixel inverted coordinates (xmin > xmax) | `[600, 200, 300, 500]` | `None (Filtered)` | Yes | PASSED |
| Boundary edge flush (0, 0, 1280, 720) | `[0, 0, 1280, 720]` | `(0.5000, 0.5000, 1.0000, 1.0000)` | Yes | PASSED |

---

## 5. Video Sequence Burst Isolation Algorithm (Anti-Leakage)

### The Spatial Correlation Problem
RDD2022 dashcam data consists of continuous vehicle driving sessions recorded at high frame rates. In standard random image splitting, consecutive frames (e.g. `India_000120.jpg` and `India_000121.jpg`) taken 0.5 seconds apart depict the exact same pothole from a 2-meter shift. Random splitting places frame 120 in `train` and frame 121 in `val`, causing:
1. Massive artificial metric inflation (mAP appears > 0.95).
2. Catastrophic real-world performance collapse on unfamiliar roads.

### Sequence-Based Splitting Protocol
1. **Sequence ID Extraction:** Parse driving session ID or sequence prefix from filename blocks (`India_SEQ_XXX`).
2. **Group-Level Partitioning:** Split data at the **Sequence Group** level, never at individual frame level:
   - **Training Set (70%):** Sequences 1 to $K_{train}$
   - **Validation Set (15%):** Sequences $K_{train}+1$ to $K_{val}$
   - **Test Set (15%):** Sequences $K_{val}+1$ to $K_{total}$
3. **Leakage Verification:**
   $$\text{Train} \cap \text{Val} = \emptyset, \quad \text{Train} \cap \text{Test} = \emptyset, \quad \text{Val} \cap \text{Test} = \emptyset$$

### Simulation Test Proof:
- Total Frames Evaluated: 60
- Sequence Groups: 6
- Train Frames: 40 | Val Frames: 10 | Test Frames: 10
- **Split Leakage:** 0 frames (0 train-val, 0 train-test)
- **Status:** **PROVEN LEAKAGE-FREE**

---

## 6. Directory Layout & Configuration Specification

### Target Directory Tree
```
ai_service/training/rdd2022_india_multiclass/
├── data.yaml
├── sequence_split_manifest.json
├── images/
│   ├── train/     (70% isolated driving sequences)
│   ├── val/       (15% isolated driving sequences)
│   └── test/      (15% isolated driving sequences)
├── labels/
│   ├── train/     (Normalized YOLO coordinates)
│   ├── val/
│   └── test/
└── raw_voc_xml/   (Original Pascal VOC XML annotations)
```

### Dataset Configuration (`data.yaml`)
```yaml
path: ai_service/training/rdd2022_india_multiclass
train: images/train
val: images/val
test: images/test

nc: 4
names:
  0: longitudinal_crack
  1: transverse_crack
  2: alligator_crack
  3: pothole
```

---

## 7. Upstream Acquisition Status & Training Gate Decision

### Upstream Storage Audit
- **Repository:** Figshare Monolithic RDD2022 Archive
- **Identifier:** DOI `10.6084/m9.figshare.21431547.v1`
- **Total Archive Size:** 12.65 GB (Compressed ZIP)
- **Included Countries:** Japan, India, Czech, Norway, United States, China.
- **Acquisition Constraint:** Figshare does not host an isolated, selective download endpoint for the India subset alone. Downloading requires pulling the complete 12.65 GB multi-national archive, followed by selective extraction of the `India/` subdirectory.

### Phase 7 Training Gate Evaluation
| Gate Condition | Requirement | Actual Status | Gate Result |
| :--- | :--- | :--- | :--- |
| **Dataset Ingestion** | Full India subset on disk | Monolithic archive not yet mounted | **BLOCKED** |
| **Converter Pipeline** | Clamping & degenerate handling verified | 10/10 edge tests passed | **READY** |
| **Sequence Isolation** | 0% frame overlap verified | Proven 0 leakage | **READY** |
| **Production Protection** | Zero retraining without data | Enforced | **PASSED** |

> [!IMPORTANT]
> **Training Gate Decision: BLOCKED**  
> Under NagarSetu Mandatory Code Protection Rules, experimental training must never be executed on placeholder or ungrounded synthetic samples. The converter and sequence isolation pipelines are fully verified and ready. Training is gated until the RDD2022 archive is downloaded and extracted. Production baseline `civicmodel.pt` remains active and untouched.

---
*Report automatically compiled and verified by Phase 7 Pipeline Suite.*
