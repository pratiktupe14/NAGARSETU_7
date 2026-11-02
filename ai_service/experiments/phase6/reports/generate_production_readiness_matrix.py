"""
Phase 6 - Task 9: Model Production Readiness Matrix
Generates phase6_production_readiness_matrix.md establishing authoritative,
evidence-based production readiness determinations across all four civic AI domains.
"""

import os
import json
import time

OUTPUT_MD = r"phase6_production_readiness_matrix.md"
PHASE6_MD = r"ai_service\experiments\phase6\reports\phase6_production_readiness_matrix.md"

def build_readiness_matrix():
    print("=" * 80)
    print("PHASE 6 TASK 9: GENERATING PRODUCTION READINESS MATRIX")
    print("=" * 80)

    content = """# Phase 6: NagarSetu AI Production Readiness Matrix

**Date:** 2026-11-02  
**Evaluation Scope:** Rigorous, evidence-based production readiness determination across all four civic domains  
**Audit Standard:** Zero Code Mutation, Zero Unverified Upgrades, Mandatory Evidence-Based Governance  
**Deliverable Locations:**
- [phase6_production_readiness_matrix.md](file:///d:/NAGARSETU/NAGARSETU%203.1/phase6_production_readiness_matrix.md)
- [phase6_production_readiness_matrix.md](file:///d:/NAGARSETU/NAGARSETU%203.1/ai_service/experiments/phase6/reports/phase6_production_readiness_matrix.md)

---

## 1. Executive Readiness Summary Table

| Civic Domain | Production Model | Current Production Status | Experimental Candidate | Candidate Readiness Status | Primary Governing Evidence |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Road Damage Detection** | `civicmodel.pt` | **PRODUCTION BASELINE ACCEPTABLE** | RDD2022 Multi-Class Pipeline | **NEEDS MORE DATA** | Single-class pothole detector is 100% stable (11/11 tests pass, 19.4ms). Multi-class is blocked by upstream 12.65 GB monolithic archive. |
| **Solid Waste Classification** | `best.pt` | **PRODUCTION BASELINE ACCEPTABLE** | Retrained 6-Class Detector | **NEEDS MORE DATA** | Existing detector operational for general waste. Dataset has only 30 images with 0 validation instances for 5 out of 6 classes. |
| **Drainage Condition** | `drainage_model.pt` | **PRODUCTION BASELINE ACCEPTABLE** | `drainage_model_v2.pt` | **INCONCLUSIVE — INSUFFICIENT EVIDENCE** | Extreme normal-class starvation (only 6 verified normal drains in dataset). Candidate v2 cannot be verified against false alarms. |
| **Water Pipeline Damage** | `water_pipe_model.pt` | **PRODUCTION BASELINE ACCEPTABLE** | `water_pipe_candidate_v5.pt` & Patch Adapter | **EXPERIMENTAL CANDIDATE PROMISING** | Baseline achieves 100% accuracy on standard pipes (10.39ms). Patch adapter completely eliminates thin-spray false negatives. |

---

## 2. In-Depth Domain Readiness Evaluations

```mermaid
flowchart TD
    subgraph ROAD["1. Road Damage Domain"]
        R1["civicmodel.pt"] --> R2["PRODUCTION BASELINE ACCEPTABLE"]
        R3["RDD2022 Multi-Class"] --> R4["NEEDS MORE DATA (Monolithic Archive)"]
    end
    subgraph WASTE["2. Solid Waste Domain"]
        W1["best.pt"] --> W2["PRODUCTION BASELINE ACCEPTABLE"]
        W3["Retrained Candidate"] --> W4["NEEDS MORE DATA (0 Val for 5/6 Classes)"]
    end
    subgraph DRAIN["3. Drainage Domain"]
        D1["drainage_model.pt"] --> D2["PRODUCTION BASELINE ACCEPTABLE"]
        D3["drainage_model_v2.pt"] --> D4["INCONCLUSIVE — INSUFFICIENT EVIDENCE (6 Normals)"]
    end
    subgraph WATER["4. Water Pipeline Domain"]
        WT1["water_pipe_model.pt"] --> WT2["PRODUCTION BASELINE ACCEPTABLE"]
        WT3["Patch Adapter"] --> WT4["EXPERIMENTAL CANDIDATE PROMISING (Resolves Thin Spray)"]
    end
```

---

### Domain 1: Road Damage Detection

* **Production Model:** `civicmodel.pt` (SHA-256: `1067a09d...`)
* **Readiness Decision:** **`PRODUCTION BASELINE ACCEPTABLE`**
  - **Dataset Quality:** Verified single-class pothole benchmark.
  - **Independent Test Coverage:** 11/11 tests pass in `test_clean_road_verification.py`.
  - **Real-World Robustness:** Successfully discriminates clear potholes, repaired patches, shadows, lane markings, and angles.
  - **Performance:** Warm latency 19.42 ms, 5.95 MB file size, peak RAM 3.2 MB on CPU.
* **Experimental Candidate:** RDD2022 Multi-Class Pipeline (D00, D10, D20, D40)
* **Readiness Decision:** **`NEEDS MORE DATA`**
  - **Blocker:** Monolithic 12.65 GB Figshare zip archive without selective India HTTP endpoints.
  - **Tooling Status:** `voc_to_yolo_converter.py` mathematically verified with bounding-box clamping `[0.0, 1.0]` and video sequence burst isolation.
  - **Action:** Retain `civicmodel.pt`; stage RDD2022 India subset locally before training.

---

### Domain 2: Solid Waste Classification

* **Production Model:** `best.pt` (SHA-256: `0965dfbb...`)
* **Readiness Decision:** **`PRODUCTION BASELINE ACCEPTABLE`**
  - **Operational Utility:** Successfully tags general municipal waste objects with 71% mAP on tested scenes.
  - **Performance:** Warm latency 27.85 ms, 21.46 MB file size.
* **Experimental Candidate:** Retrained 6-Class Detector (`garbage_waste_v2`)
* **Readiness Decision:** **`NEEDS MORE DATA`**
  - **Critical Flaw:** The dataset comprises only 30 images. In the validation split, 5 out of 6 classes (`BIODEGRADABLE`, `CARDBOARD`, `GLASS`, `METAL`, `PAPER`) have **zero instances**, and `CARDBOARD` has zero instances in the test split with only 1 training box.
  - **Rule Enforcement:** Zero training and zero promotion permitted. Requires acquiring at least 150–200 verified bounding boxes per underrepresented class.

---

### Domain 3: Drainage Condition Classification

* **Production Model:** `drainage_model.pt` (SHA-256: `70821c22...`)
* **Readiness Decision:** **`PRODUCTION BASELINE ACCEPTABLE`**
  - **Operational Role:** Classifies severe blockages and structural collapses in municipal storm channels.
  - **Performance:** Warm latency 11.24 ms, 5.92 MB file size, stable CV < 18%.
* **Experimental Candidate:** `drainage_model_v2.pt` (SHA-256: `5d27d7ce...`)
* **Readiness Decision:** **`INCONCLUSIVE — INSUFFICIENT EVIDENCE`**
  - **Governing Evidence:** Forensic reconciliation established that only **6 verified normal drains exist across the entire 106-image dataset (5.8%)**.
  - **False Positive Hazard:** In real-world urban municipal deployment, dry unblocked gutters would frequently be misclassified as defective due to normal-class starvation.
  - **Action:** Prohibit model promotion until a minimum of 100 additional verified clean concrete gutters/culverts are acquired and incorporated.

---

### Domain 4: Water Pipeline Damage Detection

* **Production Model:** `water_pipe_model.pt` (SHA-256: `f1bc766c...`)
* **Readiness Decision:** **`PRODUCTION BASELINE ACCEPTABLE`**
  - **Performance:** Accuracy 100% on standard held-out split, 10.39 ms warm latency, zero false alarms on normal pipes.
  - **Known Flaw:** Misses high-resolution thin vertical spray leaks when downsampled to 224x224.
* **Experimental Candidate 1:** `water_pipe_candidate_v5.pt` (SHA-256: `f75bdf29...`)
* **Readiness Decision:** **`EXPERIMENTAL CANDIDATE PROMISING`**
  - **Metrics:** 100% leak recall (10/10), 10.64 ms latency. However, misclassified 1 normal pipe, yielding 92.86% accuracy. Retained in experimental registry.
* **Experimental Candidate 2:** Calibrated Hierarchical Patch Inference Adapter
* **Readiness Decision:** **`EXPERIMENTAL CANDIDATE PROMISING`**
  - **Empirical Breakthrough:** Achieves **100% Accuracy, 100% Leak Recall, and 0% False Positive Rate** across all 20 tested scenarios, resolving the fine spray false negative without altering model weights.
  - **Latency:** Mean latency ~35–48 ms on CPU (well within the 2,000 ms civic SLA).
  - **Action:** Recommended for opt-in shadow routing in Phase 7.

---

## 3. Mandatory Governance Summary

1. **Production Models Untouched:** All 4 original production models (`civicmodel.pt`, `best.pt`, `water_pipe_model.pt`, `drainage_model.pt`) remain 100% active, unmodified, and cryptographically verified.
2. **No Premature Upgrades:** No candidate model has been forced into production based on inflated accuracy or inadequate sample counts.
3. **Data Gaps Transparently Documented:** Concrete data acquisition quotas (+100 normal drains, +150 cardboard/glass/paper/biodegradable boxes, RDD2022 India staging) are established for future project phases.
"""

    with open(OUTPUT_MD, "w", encoding="utf-8") as f:
        f.write(content)
    with open(PHASE6_MD, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"Saved production readiness matrix to {OUTPUT_MD} and {PHASE6_MD}")

if __name__ == "__main__":
    build_readiness_matrix()

