# PHASE 10A: WATER AI 150-SAMPLE DATASET PROVENANCE & LEAKAGE AUDIT REPORT
**Audit Date:** 2026-11-03  
**Audited Manifest:** `water_phase9_dataset_manifest.json`  
**Total Samples Audited:** 150  
**Scientific Integrity Mandate:** Absolute honesty; Zero misrepresentation of augmented crops as independent photographs.

---

## 1. Executive Summary & Core Provenance Findings

An independent forensic audit of the 150 images generated in Phase 9 reveals that **they are NOT 150 independent real-world photographs**. Rather, they are **150 augmented spatial crops derived from a finite pool of 84 unique parent photographs**, further combined with synthetic environmental overlays.

| Provenance Classification | Count | Percentage | Description / Audit Finding |
| :--- | :---: | :---: | :--- |
| **Total Evaluation Samples** | **150** | **100.0%** | Total images evaluated in Phase 9 benchmark |
| **True Independent Novel Photographs** | **0** | **0.0%** | Zero external field photographs; all derived from local directory |
| **Unique Parent Source Photographs** | **84** | **56.0%** | 56 leak photos (`D:\NAGARSETU\leaking pipes`) + 28 normal photos (`D:\NAGARSETU\normal pipe images`) |
| **Augmented / Transformed Crops** | **150** | **100.0%** | All 150 images underwent randomized cropping, resizing to 512x512, and lighting jitter |
| **Recycled Parent Images (Repeated Crops)** | **66** | **44.0%** | Samples where the same parent photo was cropped a 2nd or 3rd time (19 leaks, 47 normals) |
| **Synthetic Feature Overlays** | **75** | **50.0%** | Samples containing artificially injected spray lines, pinholes, moisture beads, or rust tints |
| **Exact Duplicate SHA-256 Hashes** | **0** | **0.0%** | Each JPEG was saved with unique crop/compression noise, yielding distinct hashes |
| **Near-Duplicate Pairs (dHash $\le 5$)** | **18** | **N/A** | Pairs sharing near-identical spatial geometry or parent composition |
| **Train/Test Leakage against Phase 5** | **HIGH** | **~84%** | Candidate v5 was trained on a 70% split of the exact same local folder |

---

## 2. Source-Image Provenance Breakdown

### 2.1 Leaking Pipe Samples (75 Images)
- **Source Pool:** `D:\NAGARSETU\leaking pipes` (56 files discovered).
- **Generation Logic:** Round-robin cycling across the 56 files.
- **Parent Reuse:**
  - 37 parent photographs were used **exactly once** (unique crops).
  - 19 parent photographs were used **twice** (different crops and lighting transforms).
- **Synthetic Overlays:**
  - `thin_vertical_water_spray` (15 samples): 3px high-contrast vertical spray injected.
  - `microscopic_pinhole_leak` (15 samples): Sub-millimeter white bubble dot injected.
  - `hairline_cracks_leak`, `slow_joint_trickle`, `large_water_burst` (45 samples): Real parent leak textures without synthetic overlays.

### 2.2 Normal Pipe Samples (75 Images)
- **Source Pool:** `D:\NAGARSETU\normal pipe images` (28 files discovered).
- **Generation Logic:** Round-robin cycling across the 28 files.
- **Parent Reuse (Severe Repetition):**
  - Because 75 normal samples were required from only 28 source images, parent images were recycled **an average of 2.68 times**.
  - 9 parent photographs were cropped **twice**.
  - 19 parent photographs were cropped **three times**.
- **Synthetic Overlays & Potential Label Artifacts:**
  - `condensation_cold_pipe` (15 samples): Artificial moisture beads scattered on normal pipes.
  - `rusted_intact_pipe` (15 samples): Warm reddish rust tint applied to normal pipes.
  - `dry_utility_trench` (15 samples): Desaturated earth tone applied to normal pipes.

---

## 3. Train / Test Data Leakage Audit

A major scientific integrity finding of Phase 10A is the **substantial data leakage between Candidate v5's training corpus and the Phase 9 benchmark**:

1. **Origin of Candidate v5 Training Data:**
   In Phase 5 (`train_water_pipe_candidate_v5.py`), Candidate v5 was trained on an 83-image physical dataset sampled directly from `D:\NAGARSETU\leaking pipes` and `D:\NAGARSETU\normal pipe images` using a 70% train split (approximately 58 training images).
2. **Overlap with Evaluation Set:**
   The Phase 9 evaluation set drew directly from the same 84 images in those directories. Consequently, **at least 70% of the parent photographs in the evaluation benchmark were present in the training set of Candidate v5**.
3. **Implications of Leakage:**
   - **Candidate v5 had prior exposure** to the pipe backgrounds, trench colors, and sensor characteristics present in the benchmark.
   - **Despite this advantage, Candidate v5 still only scored 94.00% accuracy**, making 8 false-positive errors on normal pipes.
   - The production baseline (`water_pipe_model.pt`), which was trained on an earlier independent dataset, scored **96.00% accuracy** on the same images.

---

## 4. Class-Label Correctness & Failure Analysis

Why did Candidate v5 make 8 false positive errors on the normal pipe scenarios?
- In `rusted_intact_pipe` and `condensation_cold_pipe`, normal pipes have dark discoloration and surface dew.
- Candidate v5 (a 2-class model) has an overly aggressive leak boundary, misinterpreting surface oxidation as standing water or wet pipe walls.
- The production baseline (a 3-class model distinguishing normal, joint-leak, and burst) has a more conservative decision boundary that correctly rejected the rusted pipes as normal.

---

## 5. Conclusion & Dataset Certification Status

1. **Rejection of "150 Independent Photographs" Claim:** The Phase 9 dataset must formally be classified as an **"Augmented 84-Parent Multi-Crop Evaluation Corpus"**, not 150 independent real-world field photographs.
2. **Need for External Independent Benchmark:** A true pre-production validation requires 200+ novel, unseen photographs captured from external municipal wards with zero parent-image overlap with `D:\NAGARSETU`.
3. **Artifact Availability:** The full audit is permanently cataloged in `water_phase10a_verified_manifest.json` and `dataset_provenance_audit.json`.
