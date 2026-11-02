# NagarSetu AI — Production Readiness Matrix
**Phase 8 — Task 10 Deliverable**  
**Date:** 2026-11-03  
**Status:** Multi-Domain Production Readiness Classification Complete  
**Acceptance Standard:** Phase 7 Model Acceptance Criteria (`phase7_model_acceptance_criteria.md`)

---

## 1. Executive Summary
This report formalizes the **Production Readiness Decision Matrix** across all eight AI models in the NagarSetu ecosystem. Under the **Mandatory Production Protection Rules**, no candidate model may automatically replace a production baseline without satisfying all four qualification tiers (Cryptographic Integrity, Functional Regression, Empirical Recall/Precision, and Latency SLAs).

---

## 2. Master Production Readiness Matrix (All 8 Models)

| Model Name & Checkpoint | Domain | Primary Performance | Latency (P95) | Size | Phase 8 Classification | Production Deployment Verdict |
| :--- | :--- | :--- | :---: | :---: | :--- | :--- |
| **Water Pipe Baseline** (`water_pipe_model.pt`) | Water | 77.8% Acc / 72.2% Recall | 39.9 ms | 6.22 MB | **1. Existing production baseline** | **RETAIN AS PRIMARY AUTHORITATIVE** |
| **Water Candidate v5** (`water_pipe_candidate_v5.pt`) | Water | 91.7% Acc / 94.4% Recall | 41.0 ms | 6.22 MB | **2. Experimental candidate** | **RETAIN IN EXPERIMENTAL REGISTRY** |
| **Water Calibrated Patch v2 Adapter** | Water | **94.4% - 100% Recall / 0% FPR** | **146.5 ms** | 6.22 MB | **3. Eligible for isolated shadow validation** | **APPROVED FOR ISOLATED SHADOW VALIDATION ONLY** |
| **Water Candidate INT8** (`..._quantized.pt`) | Water | 91.7% Acc / 94.4% Recall | 44.4 ms | **4.24 MB** | **6. Requires further engineering** | **ENGINEERING GATED (FUSE WITH PATCH V2)** |
| **Drainage Baseline** (`drainage_model.pt`) | Drainage | 88.0% Blocked Recall | 13.9 ms | 6.22 MB | **1. Existing production baseline** | **RETAIN AS PRIMARY AUTHORITATIVE** |
| **Drainage Candidate v2** (`drainage_model_v2.pt`) | Drainage | 35.0% False Positive Rate | 14.1 ms | 6.21 MB | **4. Requires more data** | **PROMOTION & RETRAINING BLOCKED** |
| **Solid Waste Baseline** (`best.pt`) | Waste | 0.84 Plastic mAP@0.50 | 36.5 ms | 25.85 MB | **1. Existing production baseline** | **RETAIN AS PRIMARY AUTHORITATIVE** |
| **Road Damage Baseline** (`civicmodel.pt`) | Road | 86.4% Pothole Recall | 21.0 ms | 21.48 MB | **1. Existing production baseline** | **RETAIN AS PRIMARY AUTHORITATIVE** |

---

## 3. Domain-by-Domain Readiness Breakdown

### 3.1 Water Pipeline AI Domain
- **Production Baseline (`water_pipe_model.pt`):** Retains 100% production authority.
- **Calibrated Patch v2 Adapter:** **The sole model across all domains eligible for shadow validation.** It solves the critical municipal vulnerability where thin vertical sprays (< 4px) were previously missed by baseline whole-image downsampling.
- **Quantized INT8 Candidate:** Proven 28.5% smaller and 100% executable; recommended for fusion into the Patch v2 feature extractor during Phase 9 engineering.

### 3.2 Drainage Condition AI Domain
- **Production Baseline (`drainage_model.pt`):** Retains 100% production authority.
- **Candidate v2 (`drainage_model_v2.pt`):** Classified as **Requires more data**. Exhibits an unacceptable 35% false positive rate on dry culverts due to normal drainage class scarcity (only 6 normal samples on disk). Promotion and retraining are strictly blocked until +100 normal drain images are ingested.

### 3.3 Solid Waste AI Domain
- **Production Baseline (`best.pt`):** Retains 100% production authority. Highly capable on street plastic.
- **Candidate Training Status:** Retraining is prohibited until 150-200 ground truth boxes per underrepresented class are curated.

### 3.4 Road Damage AI Domain
- **Production Baseline (`civicmodel.pt`):** Retains 100% production authority for single-class pothole complaints.
- **Multi-Class Candidate:** Conversion pipeline and video sequence burst isolation are verified and ready; model training awaits mounting of the 12.65 GB RDD2022 dataset archive.

---

## 4. Phase 8 Staged Promotion Criteria
No candidate model may replace an active baseline until:
1. It completes a minimum of 14 continuous days in non-blocking shadow mode.
2. It processes at least 1,000 live complaints with zero unhandled exceptions and zero timeouts > 1,500 ms.
3. A formal human-in-the-loop review approves its divergence accuracy on real municipal field reports.
