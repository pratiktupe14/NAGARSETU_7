# PHASE 10A: STATISTICAL PROMOTION GATES AUDIT REPORT
**Audit Date:** 2026-11-03  
**Framework Reference:** `phase9_model_promotion_framework.md` (Seven Hard Gates P1–P7)  
**Evaluated Candidate:** Water AI Candidate v5 (`water_pipe_candidate_v5.pt`) / Calibrated Patch v2  
**Overall Promotion Gate Verdict:** **BLOCKED / NO-GO FOR DIRECT PRODUCTION PROMOTION**

---

## 1. Executive Summary & Promotion Gates Audit Scorecard

In Phase 9, a formal quantitative framework consisting of Seven Hard Gates was codified to prevent premature promotion of experimental models. In Phase 10A, each gate was audited against verified empirical telemetry:

| Gate Identifier | Gate Description | Target Specification | Measured Telemetry | Gate Verdict |
| :---: | :--- | :--- | :--- | :---: |
| **P1** | **Statistical Significance & Performance Floor** | $\Delta \ge +3.0\%$ accuracy; McNemar $p < 0.05$ | $\Delta = -2.00\%$ (Base: 96% vs Cand: 94%); $p = 0.508$ | **FAIL** |
| **P2** | **Multi-Scenario Coverage & Regression Limits** | No scenario regresses $> 5.0\%$ | 2 scenarios regressed: `cold_pipe` (-20%), `rusted_pipe` (-13.3%) | **FAIL** |
| **P3** | **Deterministic Latency Budget & Headroom** | P95 $< 120.0$ ms; Headroom $\ge 20.0\%$ | P95 = **14.72 ms**; Headroom = **90.19%** | **PASS** |
| **P4** | **Memory Hygiene & Long-Running Stability** | Growth $< 2.0$ MB/100; $\Delta$ handles = 0 | Growth = **-0.00 MB/100**; $\Delta$ handles = 0 | **PASS** |
| **P5** | **Passive Shadow Mode Verification** | $\ge 500$ reqs; 0 crashes; Agree $\ge 85\%$ | 500 reqs; **0 crashes**; **98.60% agreement**; 0 DB writes | **PASS** |
| **P6** | **Exhaustive Fault-Tolerance Resilience** | 12/12 Injected failure scenarios passed | **12 / 12 Scenarios Passed (100% Resilience)** | **PASS** |
| **P7** | **Independent Governance & Rollback** | Sub-1ms rollback; dual-engineer sign-off | Rollback verified (0.02 ms); Sign-off **BLOCKED** by P1/P2 | **FAIL** |

**Summary Result:** **4 GATES PASSED (P3, P4, P5, P6)** | **3 GATES FAILED / BLOCKED (P1, P2, P7)**.

---

## 2. Deep-Dive Forensic Audit of Failed Gates

### 2.1 Gate P1 Failure: Negative Accuracy Delta & Statistical Insignificance
- **The Requirement:** The candidate model must achieve a statistically significant improvement over the production baseline:
  Accuracy delta >= +3.0% with a McNemar test significance level p < 0.05.
- **The Empirical Reality:**
  - Production Baseline Accuracy: **96.00% (144 / 150)**
  - Candidate v5 FP32 Accuracy: **94.00% (141 / 150)**
  - Observed Accuracy Delta: **-2.00 percentage points (Net Regression)**.
  - McNemar Contingency Matrix: Baseline was solely correct on 6 samples (b=6); Candidate was solely correct on 3 samples (c=3).
  - McNemar Statistic with continuity correction:
    chi2 = (|6 - 3| - 1)^2 / (6 + 3) = 4 / 9 = 0.444
    p = 0.508
- **Finding:** The candidate did not improve accuracy; it reduced accuracy by 2.0 percentage points due to excessive false alarms on intact infrastructure.

### 2.2 Gate P2 Failure: Scenario Regression Violation
- **The Requirement:** To ensure real-world robustness, no single scenario may regress by more than 5.0% compared to the baseline.
- **The Empirical Reality:** Two scenarios exhibited severe regressions:
  1. `condensation_cold_pipe`: Baseline: 14/15 (**93.3%**) vs. Candidate: 11/15 (**73.3%**) -> **Regression of -20.0 percentage points**.
  2. `rusted_intact_pipe`: Baseline: 14/15 (**93.3%**) vs. Candidate: 12/15 (**80.0%**) -> **Regression of -13.3 percentage points**.
- **Root Cause:** Candidate v5's binary loss over-penalized false negatives during training, leading it to treat surface oxidation and condensation beads as water leaks.

### 2.3 Gate P7 Failure: Mandatory Production Sign-Off Blocked
- While the operational rollback mechanism passed with flying colors (0.02 ms in-memory pointer switch), the Technical Steering Committee cannot sign off on promoting a model to production that lowers platform accuracy from 96% to 94% and generates false alarms on cold and rusted pipes.
- Gate P7 is therefore **FORMALLY BLOCKED** for live production deployment.

---

## 3. Deep-Dive Audit of Passed Gates

1. **Gate P3 (Latency):** P95 latency is **14.72 ms**, providing an exceptional **90.19% buffer** beneath the 150.0 ms SLA.
2. **Gate P4 (Stability):** 250 continuous executions showed **-0.00 MB/100 req memory drift**, zero OS handle leaks, and -1.91% latency drift.
3. **Gate P5 (Shadow Mode):** 500 shadow evaluations yielded **98.60% baseline agreement** with **0 crashes**, 0 DB writes, and 0 user-facing leaks.
4. **Gate P6 (Resilience):** All 12 failure scenarios (corrupt weights, timeouts, OOM, NaNs, zero-byte uploads, etc.) recovered flawlessly.

---

## 4. Architectural Verdict & Next Steps

Because **Gates P1 and P2 have failed**, Candidate v5 **CANNOT BE PROMOTED AS A REPLACEMENT FOR THE PRODUCTION BASELINE**.

However, because **Gates P3, P4, P5, and P6 passed**, Candidate v5 exhibits excellent systems-level stability, low latency, and superior leak sensitivity (Recall: **98.67%** vs. Baseline **97.33%**).

**Recommendation:**
- **DO NOT** deploy Candidate v5 as an authoritative production model.
- **PROCEED** to Task 5 to build an isolated staging harness that uses Candidate v5 strictly as a **secondary high-recall shadow/canary advisor** with the Production Baseline retaining 100% final authority.
