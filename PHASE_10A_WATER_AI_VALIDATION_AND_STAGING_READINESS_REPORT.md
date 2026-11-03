# PHASE 10A: INDEPENDENT WATER AI VALIDATION & STAGING READINESS REPORT

**Document ID:** NS-AI-P10A-VAL-2026-11-03  
**Generated Date:** 2026-11-03  
**Status:** INDEPENDENT AUDIT COMPLETE / STAGING READINESS CERTIFIED (CONDITIONAL)  
**Governing Standard:** NagarSetu Mandatory Code Protection & Release Gate Specification  
**Authority:** Technical Steering Committee & Municipal AI Safety Directorate  

---

## 1. Executive Summary

Phase 10A was commissioned to independently validate the results of Phase 9 and determine whether the experimental Water AI candidate (`Candidate v5` / `Calibrated Patch v2`) is genuinely ready for controlled staging integration.

### Core Forensic Conclusions:
1. **Model Accuracy Deficit & Gate Failures:**
   - On the 150-sample evaluation corpus, the **Production Baseline (`water_pipe_model.pt`) achieved 96.00% accuracy (144/150)**, whereas **Candidate v5 FP32 achieved 94.00% accuracy (141/150)**.
   - Candidate v5 exhibited a **negative accuracy delta of -2.00 percentage points**, failing the required $\ge +3.0\%$ improvement of **Gate P1** (McNemar $p = 0.5050$, not statistically significant).
   - Candidate v5 suffered severe false-alarm regressions on normal infrastructure scenarios (`condensation_cold_pipe` regressed by -20.0%, `rusted_intact_pipe` regressed by -13.3%), **failing Gate P2**.
   - Consequently, **Gate P7 (Production Release Sign-Off) is FORMALLY BLOCKED**.
2. **Dataset Provenance & Leakage Discovery:**
   - The Phase 9 150-image corpus does **not** consist of 150 independent real-world field photographs. It comprises **150 augmented spatial crops derived from 84 unique parent photographs** (56 leak, 28 normal) from local disk folders (`D:\NAGARSETU\leaking pipes` and `normal pipe images`).
   - Normal parent photographs were recycled an average of **2.68 times**.
   - Furthermore, Candidate v5 was originally trained in Phase 5 on a 70% split of these exact same folders, introducing substantial **parent-photo train/test leakage**.
3. **Systems Stability & Resilience Strengths:**
   - Candidate v5 demonstrated outstanding systems-level maturity: P95 latency is **14.72 ms** (whole-image) and **43.52 ms** (full staging pipeline), delivering $> 70\%$ headroom beneath the 150 ms municipal SLA (**Gate P3 PASS**).
   - Long-running stability proved leak-free across 250 iterations with **0.00 MB/100 req memory drift**, zero handle leaks, and -1.91% latency drift (**Gate P4 PASS**).
   - In 500 shadow evaluations, the candidate achieved **98.60% baseline agreement** with **0 crashes** and 0 database writes (**Gate P5 PASS**).
   - The engine passed all 12 fault-tolerance injection scenarios (**Gate P6 PASS**).
4. **Staging Harness Validation:**
   - An isolated staging adapter (`StagingWaterAIAdapter`) was verified across 9 staging suites, confirming automatic in-memory baseline fallback (39.38 ms), circuit-breaker tripping after 5 failures (state: `OPEN`, bypass latency 28.24 ms), container cold-start in 183.82 ms, zero database writes, and complete client-facing response invariance.
5. **Final Recommendation:**
   - **DIRECT PRODUCTION REPLACEMENT: DEFINITIVE NO-GO.**
   - **ISOLATED STAGING SHADOW / CANARY PILOT: CONDITIONAL GO.**
   - Under this conditional staging authorization, the Production Baseline retains 100% authoritative final dispatch authority, while Candidate v5 runs strictly as a passive advisory shadow.

---

## 2. Dataset Provenance, Duplication & Leakage Audit

An exhaustive forensic audit of the 150 evaluation images was conducted to verify true data provenance:

| Provenance Attribute | Forensic Finding | Verification Evidence |
| :--- | :---: | :--- |
| **Total Evaluation Samples** | **150 images** | Cataloged in `water_phase10a_verified_manifest.json` |
| **True Independent Field Photographs** | **0** | All images derived from local directory assets |
| **Unique Parent Source Photographs** | **84** | 56 in `D:\NAGARSETU\leaking pipes`, 28 in `normal pipe images` |
| **Augmented / Transformed Crops** | **150** | 100% underwent randomized cropping, resizing, and color jitter |
| **Recycled Parent Images (Repeated Crops)** | **66** | 19 leak parent photos cropped 2x; 28 normal parent photos cropped 2x–3x |
| **Normal Parent Image Reuse Factor** | **2.68x** | 75 normal samples generated from only 28 source images |
| **Synthetic Feature Overlays** | **75** | Artificially superimposed spray lines, pinholes, moisture beads, rust tints |
| **Exact Duplicate SHA-256 Hashes** | **0** | Unique crop boundaries and JPEG encoding produced unique hashes |
| **Near-Duplicate Pairs (dHash $\le 5$)** | **18 pairs** | Perceptual hash distance confirmed parent composition overlap |
| **Train/Test Leakage against Phase 5** | **HIGH (~84%)** | Candidate v5 was trained on a 70% split of the same parent folders |

### Provenance Takeaway:
The Phase 9 dataset must formally be designated as an **"Augmented 84-Parent Multi-Crop Evaluation Corpus"**. Future pre-production pilots must ingest at least 200+ novel, independently captured photographs from external municipal wards.

---

## 3. Independent Model Evaluation Results

All four models were evaluated against the identical 150-sample corpus under standardized preprocessing:

| Evaluation Metric | Production Baseline (`water_pipe_model.pt`) | Candidate v5 FP32 (`water_pipe_candidate_v5.pt`) | Candidate v5 INT8 (Dynamic Quantized) | Calibrated Patch v2 Pipeline |
| :--- | :---: | :---: | :---: | :---: |
| **Accuracy** | **96.00% (144/150)** | **94.00% (141/150)** | **94.00% (141/150)** | **94.00% (141/150)** |
| **Accuracy Delta vs Baseline** | *Reference Baseline* | **-2.00% (Degraded)** | **-2.00% (Degraded)** | **-2.00% (Degraded)** |
| **Leak Precision** | **94.81%** | 90.24% | 90.24% | 91.25% |
| **Leak Recall (Sensitivity)** | 97.33% (73/75) | **98.67% (74/75)** | **98.67% (74/75)** | 97.33% (73/75) |
| **Normal Pipe Recall (Specificity)** | **94.67% (71/75)** | 89.33% (67/75) | 89.33% (67/75) | 90.67% (68/75) |
| **Macro F1-Score** | **96.00%** | 93.99% | 93.99% | 93.99% |
| **False Positive Rate (FPR)** | **5.33% (4/75)** | 10.67% (8/75) | 10.67% (8/75) | 9.33% (7/75) |
| **False Negative Rate (FNR)** | 2.67% (2/75) | **1.33% (1/75)** | **1.33% (1/75)** | 2.67% (2/75) |
| **Mean Latency (Single Thread)** | **9.94 ms** | 12.18 ms | 12.75 ms | 23.36 ms |
| **P95 Latency** | **13.36 ms** | 16.87 ms | 17.75 ms | 34.19 ms |

---

## 4. Confusion Matrices & False-Alarm Root Cause Analysis

### 4.1 Confusion Matrices Breakdown
- **Production Baseline:**
  - True Positives (TP): 73 | True Negatives (TN): 71
  - False Positives (FP): 4 | False Negatives (FN): 2
- **Candidate v5 FP32:**
  - True Positives (TP): 74 | True Negatives (TN): 67
  - False Positives (FP): **8 (Twice the baseline)** | False Negatives (FN): **1 (Superior recall)**
- **Calibrated Patch v2:**
  - True Positives (TP): 73 | True Negatives (TN): 68
  - False Positives (FP): 7 | False Negatives (FN): 2

### 4.2 Forensic Root Cause of the 8 False Positives
Candidate v5 committed 8 false alarms on intact normal pipes:
1. **Cold Condensation Pipe (`condensation_cold_pipe`):** 4 false alarms. The model interpreted specular light glints off surface dew beads as pressurized water droplets.
2. **Rusted Cast Iron Pipe (`rusted_intact_pipe`):** 3 false alarms. Reddish-brown oxide patches and rough surface flaking were misinterpreted as mud/leak discoloration.
3. **Dry Utility Trench (`dry_utility_trench`):** 1 false alarm caused by deep soil shadow gradients along the trench trench wall.

### 4.3 Structural Architectural Reason
- **Baseline (3-Class Architecture):** Trained on `[normal, joint_leak, burst]`. Its intermediate representations learned to distinguish normal pipe joints and rust lines from high-velocity bursts.
- **Candidate v5 (2-Class Architecture):** Trained on binary `[normal, leak]` with class weighting to penalize missed leaks. This biased the decision boundary toward over-calling leaks on any surface anomaly.

---

## 5. Statistical Promotion Gates Audit (P1 through P7)

Each of the Seven Hard Gates from the Phase 9 Promotion Framework was audited against verified empirical evidence:

| Gate | Description | Pass Criteria | Measured Result | Verdict |
| :---: | :--- | :--- | :--- | :---: |
| **P1** | **Statistical Performance** | $\Delta_{\text{acc}} \ge +3.0\%$; McNemar $p < 0.05$ | $\Delta_{\text{acc}} = -2.00\%$; McNemar $\chi^2 = 0.444, p = 0.5050$ | **FAIL** |
| **P2** | **Scenario Regression Limits** | No scenario regresses $> 5.0\%$ | 2 scenarios regressed: `cold_pipe` (-20.0%), `rusted_pipe` (-13.3%) | **FAIL** |
| **P3** | **Deterministic Latency Budget** | P95 $< 120.0$ ms; Headroom $\ge 20\%$ | P95 = **14.72 ms**; Headroom = **90.19%** vs 150 ms SLA | **PASS** |
| **P4** | **Memory Hygiene & Stability** | Growth $< 2.0$ MB/100; $\Delta\text{handles}=0$ | Growth = **0.00 MB/100**; $\Delta\text{handles}=0$; Drift = **-1.91%** | **PASS** |
| **P5** | **Passive Shadow Mode** | $\ge 500$ reqs; 0 crashes; Agree $\ge 85\%$ | 500 reqs; **0 crashes**; **98.60% agreement**; 0 DB writes | **PASS** |
| **P6** | **Fault-Tolerance Resilience** | 12/12 Injected failure scenarios passed | **12 / 12 Scenarios Passed (100% Resilience)** | **PASS** |
| **P7** | **Governance & Rollback** | Sub-1ms rollback; dual-engineer sign-off | Rollback verified (0.02 ms); Sign-off **BLOCKED** by P1/P2 | **FAIL** |

**Promotion Gates Scorecard:** **4 GATES PASSED (P3, P4, P5, P6)** | **3 GATES FAILED / BLOCKED (P1, P2, P7)**.

---

## 6. Shadow Evaluation Forensic Audit (500 Requests)

Forensic auditing of `extended_shadow_log.jsonl` separated agreement from accuracy:
- **Baseline-Candidate Agreement:** **98.60% (493 / 500 requests)**.
- **Production Baseline Ground-Truth Accuracy:** **95.60% (478 / 500 requests)**.
- **Shadow Candidate Ground-Truth Accuracy:** **94.20% (471 / 500 requests)**.
- **Divergence Dissection:** Exactly **7 divergences out of 500 requests (1.40%)**.
  - In **100% of divergence events (7/7)**, the **Baseline was objectively correct** and Candidate v5 was wrong (spurious leak predictions on dry rusted/cold pipes).
- **Latency Overhead:** Background candidate execution added an average of **+11.43 ms**, which was completely decoupled from client responses.
- **Safety Audit:** Zero candidate crashes, zero unhandled exceptions, zero database writes, and zero citizen response contamination.

---

## 7. Performance & Stability Verification

1. **Inference Latency:**
   - Single Whole-Image Forward Pass: **12.18 ms Mean / 16.87 ms P95**.
   - Full Hierarchical Staging Pipeline: **25.69 ms Mean / 43.52 ms P95**.
   - Worst-Case High-Resolution $768\times 768$ Image: **61.87 ms P95 (58.75% headroom vs 150 ms SLA)**.
2. **Concurrency & Throughput:**
   - 10 Concurrent Threads: **99.87 req/s peak throughput** with 0.00% error rate.
   - 40-Request Burst: Handled at **91.99 req/s**; post-burst single requests recovered immediately to **27.48 ms P95 latency**.
3. **Memory Hygiene (250 Inferences):**
   - RSS drift: **0.00 MB / 100 requests**.
   - Open OS handles: Exactly **318 at start $\to$ 318 at completion** ($\Delta = 0$).
   - Latency drift: **-1.91%** across 250 iterations.
   - Garbage collection: 0 uncollectables in `gc.garbage`.

---

## 8. Failure Recovery Verification (12 Scenarios)

12 failure modes were verified with 100% pass rate:
- Missing candidate weights $\to$ Dynamic baseline fallback in 36.15 ms.
- Corrupted checkpoint $\to$ Dynamic baseline fallback in 50.45 ms.
- Timeout limit exceeded $\to$ Candidate branch truncated; fast baseline served in 11.36 ms.
- OOM allocation error $\to$ Low-memory single-pass fallback in 11.40 ms.
- NaN/Inf outputs $\to$ Corrupt tensors suppressed; clean baseline served in 18.63 ms.
- Extreme dimensions ($1\times 1$, $3000\times 3000$, L, RGBA) $\to$ Normalized in 102.38 ms.
- Zero-byte file $\to$ Structured HTTP 400 rejection in 112.29 ms.
- Disk full during logging $\to$ Exception swallowed; user request succeeds (0.01 ms).
- Circuit breaker tripping $\to$ Trips to `OPEN` on 5 errors; candidate bypassed in 13.17 ms.
- Unhandled candidate exception $\to$ Transparent baseline fallback in 16.86 ms.
- Dual-model total failure $\to$ Degraded payload routes ticket to manual triage (0.01 ms).
- Container cold start $\to$ First forward pass ready in 79.51 ms (<500 ms SLA).

---

## 9. Staging Integration Harness Results

An isolated staging harness (`StagingWaterAIAdapter`) was verified across 9 integration suites:
1. **Schema Adherence:** Verified response contract matching NagarSetu JSON specification.
2. **Baseline Fallback:** Injected candidate exception defaulted to baseline in **39.38 ms**.
3. **Circuit Breaker:** 5 consecutive candidate errors tripped state to `OPEN`; subsequent requests bypassed candidate in **28.24 ms**.
4. **Cold Start Instantiation:** Instantiation and first prediction completed in **183.82 ms**.
5. **Missing Model Resilience:** Missing candidate checkpoint handled cleanly in **84.18 ms**.
6. **Logging Error Containment:** Invalid log path swallowed silently; primary request succeeded.
7. **Pipeline Latency Profile:** 50 requests achieved a P95 latency of **43.52 ms** (Mean: **25.69 ms**).
8. **Database Isolation:** Verified 0 active database connections.
9. **Citizen Response Invariance:** 100% of authoritative predictions produced strictly by baseline.

---

## 10. Production Safety Audit

The comprehensive safety audit verified:
1. **Cryptographic Model Hash Invariance (4/4 MATCH):**
   - `civicmodel.pt`: `1067a09d37e4e9081164e6d6da337ad66d8ec7a884a6a194e58703beee804aa2` (MATCH)
   - `best.pt`: `0965dfbb16320981abeab3ed50cefe90bef8dede1453407aed2d952898a765e6` (MATCH)
   - `water_pipe_model.pt`: `f1bc766c569d1053b4e252247e37edfcc0fe76d3ce594e8b1ae9020aa52aac86` (MATCH)
   - `drainage_model.pt`: `70821c225a90dd769f097c5d212ebce89a21aaf83667ada4a950d54e9d96e75f` (MATCH)
2. **Git Working Tree Invariance:** Exactly **0 modified tracked production files**.
3. **Dependency & Configuration Invariance:** `pyproject.toml`, `package.json`, and core routers 100% pristine.
4. **Database Safety:** Exactly 0 database migrations, 0 writes, 0 altered records.
5. **Full Regression Test Suite:** **56 total tests executed across 6 test suites | 56 Passed | 0 Failed (100% Pass Rate)**.

---

## 11. Remaining Blockers

Before Candidate v5 can be considered for authoritative production promotion:
1. **Blocker 1 (Accuracy & False Alarm Regression):** Candidate v5 must resolve its 10.67% false positive rate on cold condensation and rusted cast iron pipes. Retraining with hard negative mining on oxidized and dewed surfaces is required to surpass the baseline's 96.00% accuracy.
2. **Blocker 2 (Parent Image Overlap & Dataset Diversity):** The evaluation corpus must be refreshed with 200+ novel field images collected from independent municipal wards to eliminate train/test leakage.
3. **Blocker 3 (Failure on Gate P1 and P2):** Formal project rules forbid production promotion until Gate P1 ($\ge +3.0\%$ delta, $p < 0.05$) and Gate P2 ($\le 5.0\%$ scenario regression) are satisfied.

---

## 12. Final GO / NO-GO Recommendation

| Deployment Phase | Recommendation | Operational Conditions & Rationale |
| :--- | :---: | :--- |
| **Direct Production Model Replacement** | **DEFINITIVE NO-GO** | **BLOCKED.** Candidate v5 regressed accuracy from 96.00% to 94.00%, doubled false positive alarms, and failed Promotion Gates P1, P2, and P7. |
| **Isolated Staging Shadow / Canary Pilot** | **GO (CONDITIONAL)** | **APPROVED FOR STAGING ONLY.** Systems engineering, latency, memory, and circuit breaker tests passed 100%. Candidate v5 can be integrated into the isolated staging cluster under strict constraints. |

### Mandatory Conditions for Staging Canary Pilot:
1. **100% Authoritative Baseline Rule:** The Production Baseline model (`water_pipe_model.pt`) must determine 100% of final citizen-facing outputs and dispatch tickets.
2. **Passive Advisory Role:** Candidate v5 may only execute as a passive shadow or secondary advisor.
3. **Circuit Breaker Active:** The automated circuit breaker must remain active at threshold = 5.
4. **Zero Production Mutation:** No live database writes, no production API routing modifications.

---

## 13. Final Stop Condition

**PHASE 10A EXECUTION IS COMPLETE.**  
In accordance with mandatory safety rules:
- **NO experimental model has been deployed to live production.**
- **NO citizen complaints have been routed through Candidate v5 or Patch v2.**
- **NO live workflows, databases, or configs have been modified.**
- **Execution is halted. Awaiting explicit user review and written approval before proceeding to Phase 10B.**
