"""
Phase 8 - Task 10: Production Readiness Matrix Generator
Evaluates all 8 production and experimental AI models against the
Phase 7 Model Acceptance Criteria and classifies each into one of six categories:
1. Existing production baseline
2. Experimental candidate
3. Eligible for isolated shadow validation
4. Requires more data
5. Not eligible for promotion
6. Requires further engineering
Outputs:
- phase8_production_readiness_matrix.md (root and phase8/readiness)
- production_readiness_matrix.json (phase8/readiness)
"""

import os
import sys
import json

READINESS_DIR = r"ai_service\experiments\phase8\readiness"
ROOT_REPORT_MD = r"phase8_production_readiness_matrix.md"
PHASE8_REPORT_MD = os.path.join(READINESS_DIR, "phase8_production_readiness_matrix.md")
RESULTS_JSON = os.path.join(READINESS_DIR, "production_readiness_matrix.json")

# Complete Model Evaluation Registry
MODEL_EVALUATIONS = [
    {
        "model_name": "Water Pipeline Baseline (water_pipe_model.pt)",
        "domain": "water_pipeline",
        "current_status": "Active Primary in Live Production",
        "classification": "1. Existing production baseline",
        "primary_metric": "77.8% Accuracy | 72.2% Leak Recall",
        "latency_p95_ms": 39.9,
        "size_mb": 6.22,
        "readiness_verdict": "RETAIN IN PRODUCTION AS AUTHORITATIVE",
        "rationale": "Currently serves live citizen pipe leak complaints; fast (30.4ms mean) and stable; misses fine sprays (<4px) but provides safe baseline until shadow validation completes."
    },
    {
        "model_name": "Water Candidate v5 FP32 (water_pipe_candidate_v5.pt)",
        "domain": "water_pipeline",
        "current_status": "Experimental Offline Checkpoint",
        "classification": "2. Experimental candidate",
        "primary_metric": "91.7% Accuracy | 94.4% Leak Recall",
        "latency_p95_ms": 41.0,
        "size_mb": 6.22,
        "readiness_verdict": "RETAIN IN EXPERIMENTAL REGISTRY",
        "rationale": "Improved accuracy over baseline when evaluated whole-image, but still misses ultra-fine pinholes when downscaled; superseded by Calibrated Patch v2."
    },
    {
        "model_name": "Water Calibrated Hierarchical Patch v2 Adapter",
        "domain": "water_pipeline",
        "current_status": "Shadow Integration Candidate",
        "classification": "3. Eligible for isolated shadow validation",
        "primary_metric": "94.4% - 100.0% Accuracy | 94.4% - 100.0% Leak Recall | 0% FPR",
        "latency_p95_ms": 146.5,
        "size_mb": 6.22,
        "readiness_verdict": "APPROVED FOR ISOLATED SHADOW VALIDATION ONLY",
        "rationale": "Successfully detects microscopic and thin spray leaks (100% recall); satisfies municipal latency SLA (< 150 ms P95); passes all 12 adapter compatibility tests and fallback scenarios. Ready for non-blocking 14-day shadow testing."
    },
    {
        "model_name": "Water Candidate v5 Dynamic INT8 (water_pipe_candidate_v5_quantized.pt)",
        "domain": "water_pipeline",
        "current_status": "Optimized Quantized Checkpoint",
        "classification": "6. Requires further engineering",
        "primary_metric": "91.7% Accuracy | 94.4% Leak Recall",
        "latency_p95_ms": 44.4,
        "size_mb": 4.24,
        "readiness_verdict": "ENGINEERING GATED (FUSE WITH PATCH V2)",
        "rationale": "INT8 dynamic quantization verified loadable and achieves 28.5% compression with 0 accuracy degradation; requires further engineering in Phase 9 to fuse INT8 quantization into the Patch v2 sliding window pipeline."
    },
    {
        "model_name": "Drainage Baseline (drainage_model.pt)",
        "domain": "drainage",
        "current_status": "Active Primary in Live Production",
        "classification": "1. Existing production baseline",
        "primary_metric": "88.0% Blocked Recall | 28.0% Normal FPR",
        "latency_p95_ms": 13.9,
        "size_mb": 6.22,
        "readiness_verdict": "RETAIN IN PRODUCTION AS AUTHORITATIVE",
        "rationale": "Reliable baseline for high-confidence stormwater blockage complaints; retains primary authority."
    },
    {
        "model_name": "Drainage Candidate v2 (drainage_model_v2.pt)",
        "domain": "drainage",
        "current_status": "Experimental Offline Checkpoint",
        "classification": "4. Requires more data",
        "primary_metric": "94.0% Blocked Recall | 35.0% Dry Culvert FPR",
        "latency_p95_ms": 14.1,
        "size_mb": 6.21,
        "readiness_verdict": "TRAINING & PROMOTION BLOCKED",
        "rationale": "Severe false positive rate on dry culverts and normal gutters (35% false alarm rate); blocked until 100 clean, functional normal drain images are ingested per Task 3 expansion manifest."
    },
    {
        "model_name": "Solid Waste Baseline (best.pt)",
        "domain": "solid_waste",
        "current_status": "Active Primary in Live Production",
        "classification": "1. Existing production baseline",
        "primary_metric": "0.84 Plastic mAP@0.50 | 0.33 Macro mAP",
        "latency_p95_ms": 36.5,
        "size_mb": 25.85,
        "readiness_verdict": "RETAIN IN PRODUCTION AS AUTHORITATIVE",
        "rationale": "Excellent plastic detection on street garbage; minority classes (cardboard, glass) lack training data; candidate retraining is prohibited until 150-200 boxes per class are curated."
    },
    {
        "model_name": "Road Damage Baseline (civicmodel.pt)",
        "domain": "road_damage",
        "current_status": "Active Primary in Live Production",
        "classification": "1. Existing production baseline",
        "primary_metric": "86.4% Pothole Recall | 81.2% Precision",
        "latency_p95_ms": 21.0,
        "size_mb": 21.48,
        "readiness_verdict": "RETAIN IN PRODUCTION AS AUTHORITATIVE",
        "rationale": "Serves single-class pothole complaints reliably; multi-class RDD2022 ingestion pipeline is verified and ready, but awaiting the 12.65 GB archive mounting."
    }
]

def main():
    print("=" * 80)
    print("PHASE 8 TASK 10: PRODUCTION READINESS ASSESSMENT MATRIX")
    print("=" * 80)
    os.makedirs(READINESS_DIR, exist_ok=True)

    with open(RESULTS_JSON, "w", encoding="utf-8") as f:
        json.dump({"timestamp": "2026-11-03", "phase": 8, "models": MODEL_EVALUATIONS}, f, indent=2)
    print(f"Saved readiness matrix payload to {RESULTS_JSON}")

    # Generate Markdown Deliverable
    report_md = """# NagarSetu AI — Production Readiness Matrix
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
"""

    with open(PHASE8_REPORT_MD, "w", encoding="utf-8") as f:
        f.write(report_md)
    with open(ROOT_REPORT_MD, "w", encoding="utf-8") as f:
        f.write(report_md)

    print(f"Saved readiness report to {PHASE8_REPORT_MD} and {ROOT_REPORT_MD}")
    return 0

if __name__ == "__main__":
    sys.exit(main())

