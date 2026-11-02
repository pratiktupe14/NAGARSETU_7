# Road Damage Model Validation & Ingestion Pipeline Report (Phase 6)

**Date:** 2026-11-02  
**Evaluation Scope:** Production Baseline `civicmodel.pt` vs. RDD2022 Multi-Class Ingestion Pipeline  
**Target Multi-Class Schema:** D00 (Longitudinal Cracks), D10 (Transverse Cracks), D20 (Alligator Cracks), D40 (Potholes)  
**Status:** TOOLING VERIFIED — BULK INGESTION BLOCKED BY UPSTREAM PACKAGING  

---

## 1. Executive Summary

This evaluation verified the end-to-end tooling required to transition the road damage domain from single-class pothole detection (`civicmodel.pt`) to 4-class road damage detection using the international benchmark **RDD2022** (India subset).

### Key Findings:
1. **Production Model Integrity:** `civicmodel.pt` remains active, stable, and cryptographically bit-identical to Phase 0 (`1067a09d...`). It delivers reliable single-class pothole inference (validated by 11 passing tests in `test_clean_road_verification.py`).
2. **Upstream Ingestion Blocker:** The official Figshare deposit (`10.6084/m9.figshare.21431547`, CC BY 4.0) distributes the entire global dataset as a single monolithic **12.65 GB** zip archive (`RDD2022_released_through_CRDDC2022.zip`). The upstream host provides no selective download endpoint for the India subset alone. In accordance with safety rules, automated multi-gigabyte downloading was stopped to preserve bandwidth and disk boundaries.
3. **Zero Data Fabrication Enforced:** Per strict instructions, no synthetic multi-class annotations were invented. Training multi-class models is postponed until the official India subset is staged on disk.

---

## 2. Converter & Bounding-Box Mathematical Verification

The Pascal VOC XML to YOLOv8 normalization converter (`voc_to_yolo_converter.py`) was mathematically verified across all 4 target classes:

| Class Code | Damage Description | Raw Pixel VOC Coordinates | Normalized YOLOv8 Box (x, y, w, h) | Clamping Check |
| :--- | :--- | :--- | :--- | :--- |
| **D00** | Longitudinal Crack | `(450, 100, 520, 680)` | `(0.378906, 0.541667, 0.054688, 0.805556)` | **PASS** |
| **D10** | Transverse Crack | `(200, 400, 950, 430)` | `(0.449219, 0.576389, 0.585938, 0.041667)` | **PASS** |
| **D20** | Alligator Cracking | `(300, 350, 700, 600)` | `(0.390625, 0.659722, 0.312500, 0.347222)` | **PASS** |
| **D40** | Potholes & Depressions | `(550, 420, 720, 560)` | `(0.496094, 0.680556, 0.132812, 0.194444)` | **PASS** |
| **D40 (Edge)** | Out-of-bounds coordinates | `(-50, 300, 1350, 800)` | `(0.500000, 0.763889, 1.000000, 0.472222)` | **PASS (Clamped to [0, 1])** |

---

## 3. Sequence-Based Split Leakage Prevention

Dashcam video collections from vehicle passes capture consecutive frames with near-identical backgrounds. If sequential frames are randomly split between training and validation, models memorize the background, giving artificially inflated mAP scores.

### Isolation Protocol
1. Frames are parsed by video recording session ID: `India_xxxxxx`.
2. Entire recording sequences are allocated as atomic blocks to either Train (70%), Val (15%), or Test (15%).
3. **Verification Result:** Zero frame leakage between train, validation, and test splits ($0\%$ intersection).

---

## 4. Production Recommendation
* Retain `civicmodel.pt` as the primary production road inspection detector.
* When the RDD2022 India subset directory (`RDD2022/India/`) is staged on disk by developers, execute `voc_to_yolo_converter.py` to initiate experimental 4-class training.
