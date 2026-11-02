# NagarSetu AI — Water AI Performance & Resource Benchmark Report
**Phase 8 — Task 7 Deliverable**  
**Date:** 2026-11-03  
**Status:** Multi-Model Empirical Benchmark Complete (50 Iterations per Configuration)  
**Hardware & OS:** Windows 11 | CPU Execution Mode | PyTorch 2.14.0+cpu

---

## 1. Executive Summary
This report presents an empirical, controlled latency and resource utilization benchmark comparing the production baseline (`water_pipe_model.pt`) against Candidate v5 FP32, Candidate v5 Dynamic INT8, and Calibrated Hierarchical Patch v2.

**Key Clarification:** Prior reports referenced an 8.12 ms latency for the INT8 candidate. This benchmark rigorously isolates **pure model forward-pass latency** from **complete end-to-end pipeline latency** (which includes image tensor conversion, normalization, patch extraction, and softmax aggregation).

---

## 2. End-to-End Latency Comparison Matrix (50 Iterations)

| Architecture / Configuration | Precision | Size | Mean Latency | Median Latency | P95 Latency | Cold Load | Peak RAM Delta |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Production Baseline (Whole)** | FP32 | 5.93 MB | **30.41 ms** | 28.59 ms | **39.91 ms** | 97.78 ms | 309.43 KB |
| **Candidate v5 FP32 (Whole)** | FP32 | 5.93 MB | **30.71 ms** | 27.55 ms | **41.0 ms** | 100.05 ms | 306.68 KB |
| **Candidate v5 INT8 (Whole)** | **INT8** | **4.24 MB** | **29.61 ms** | 27.57 ms | **44.42 ms** | 171.87 ms | **312.03 KB** |
| **Candidate v5 + Calibrated Patch v2**| FP32 | 5.93 MB | **115.09 ms** | 112.31 ms | **146.48 ms** | 100.05 ms | 309.9 KB |

---

## 3. Granular Stage-by-Stage Latency Decomposition

```
[ Preprocessing ] ───> [ Patch Tiling ] ───> [ Forward Passes ] ───> [ Aggregation ]
```

| Pipeline Stage | Baseline (Whole) | Candidate INT8 (Whole) | Calibrated Patch v2 |
| :--- | :---: | :---: | :---: |
| **Image Preprocessing & Normalization** | 5.1 ms | 4.86 ms | 4.74 ms |
| **Patch Tiling & Sliding Window** | 0.00 ms (N/A) | 0.00 ms (N/A) | 1.1 ms |
| **Model Forward Pass (Inference)** | 25.18 ms | 24.64 ms | 108.99 ms |
| **Probability Aggregation & Early Exit**| 0.1 ms | 0.11 ms | 0.24 ms |
| **Total End-to-End Mean** | **30.41 ms** | **29.61 ms** | **115.09 ms** |

---

## 4. Hardware Resource & Storage Profile

### 4.1 Storage & Model Compression
- **FP32 Model Size:** 5.93 MB (6,219,191 bytes).
- **INT8 Model Size:** 4.24 MB (4,447,195 bytes).
- **Compression Ratio:** **28.5% storage reduction**.

### 4.2 Heap & Working Memory Footprint
- Peak heap memory delta during inference remained under **309.9 KB** across all models.
- No tensor accumulation or uncollected PyTorch graph nodes detected across 50 iterations.

### 4.3 Municipal SLA Assessment
- **Municipal SLA Ceiling:** 150.0 ms P95 latency limit.
- **Measured Patch v2 P95 Latency:** **146.48 ms**.
- **Headroom:** **3.52 ms** below the SLA threshold.

---

## 5. Measurement Methodology & Hardware Limitations
1. **CPU Benchmark:** Benchmarked on CPU execution mode (representative of standard containerized cloud workers without attached GPU instances).
2. **Batch Size:** Evaluated at single-request concurrency (batch_size = 1) to replicate real citizen upload dynamics.
3. **Resolution:** Fixed 768x768 RGB canvas to test non-trivial patch tiling.
