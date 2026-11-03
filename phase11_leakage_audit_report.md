# PHASE 11: DATA LEAKAGE PREVENTION & GROUP-BASED SPLIT AUDIT

## 1. Executive Summary

In Phase 10A, an audit revealed that 84% of previous evaluation images shared underlying parent source photographs with the Phase 5 training pool. 

To definitively eliminate all data leakage in Phase 11, a **strict group-based partitioning strategy** was implemented. Partitioning was performed strictly on **unique physical parent photographs** before any crops or augmentations are generated.

---

## 2. Group Partitioning Metrics

- **Unique Parent Images Available:** 85
- **Train Set Parents:** 50 (58.8%)
- **Validation Set Parents:** 18 (21.2%)
- **Frozen Independent Test Parents:** 17 (20.0%)

### Split Breakdown by 3-Class Label

| Class Label | Train Parents | Val Parents | Frozen Test Parents | Total Unique Parents |
| :--- | :---: | :---: | :---: | :---: |
| `normal_pipe` | 14 | 6 | 5 | 25 |
| `pipe_leak` | 35 | 11 | 11 | 57 |
| `rusted_pipe` | 1 | 1 | 1 | 3 |
| **Total** | **50** | **18** | **17** | **85** |

---

## 3. Mathematical Leakage Audit Results

1. **Parent Identity Overlap:**
   - $\text{Train} \cap \text{Frozen Test} = \emptyset$ (0 shared parent images)
   - $\text{Validation} \cap \text{Frozen Test} = \emptyset$ (0 shared parent images)
   - $\text{Train} \cap \text{Validation} = \emptyset$ (0 shared parent images)
   - **Verdict: PASS (100% Disjoint Group Partition)**

2. **Perceptual Hash Near-Duplicate Audit (Hamming Distance $\le 5$):**
   - Cross-split comparisons tested: 1156 pairs.
   - Near-duplicate pairs discovered across split boundaries: 0.
   - **Verdict: PASS (Zero Cross-Split Perceptual Leakage)**

---

## 4. Frozen Independent Test Protocol

The 17 parent photographs assigned to `frozen_test` are strictly isolated:
- Zero model parameter updates or loss calculations are performed on this set.
- All four candidate architectures (Production Baseline, Candidate v5, Candidate v6 3-class, and Multi-Stage) will be evaluated on the **identical, untouched frozen test set**.
