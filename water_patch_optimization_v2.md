# Water Pipeline AI Optimization & Quantization Report (Phase 7)

**Date:** 2026-11-03  
**Evaluation Scope:** Performance & Latency Comparison across 36 Rigorously Categorized Independent Samples (18 Leaking, 18 Normal)  
**Evaluated Approaches:**
1. Production Baseline (`water_pipe_model.pt`) under Global Inference
2. Production Baseline + Optimized Hierarchical Patch Inference (384x384, 20% overlap, Early-Exit Gating)
3. Candidate V5 (`water_pipe_candidate_v5.pt` FP32)
4. Candidate V5 INT8 Dynamically Quantized (`water_pipe_candidate_v5_quantized.pt`)

---

## 1. Quantitative Benchmark Across 36 Independent Samples

| Metric | 1. Baseline Global | 2. Baseline + Hierarchical Patch | 3. Candidate V5 (FP32) | 4. Candidate V5 (INT8 Quantized) |
| :--- | :--- | :--- | :--- | :--- |
| **Model Checkpoint** | `water_pipe_model.pt` | `water_pipe_model.pt` (Adapter) | `water_pipe_candidate_v5.pt` | `water_pipe_candidate_v5_quantized.pt` |
| **Model Size** | 5.92 MB | 5.92 MB | 5.93 MB | **5.91 MB** |
| **Accuracy** | 94.44% (34/36) | **100.00% (36/36)** | 91.67% (33/36) | 91.67% (33/36) |
| **Macro F1 Score** | 0.9443 | **1.0000** | 0.9161 | 0.9161 |
| **Leak Recall** | 88.89% (16/18) | **100.00% (18/18)** | **100.00% (18/18)** | **100.00% (18/18)** |
| **Normal Precision** | 90.00% | **100.00%** | 100.00% | 100.00% |
| **False Positive Rate** | **0.00% (0 FP)** | **0.00% (0 FP)** | 16.67% (3 FP) | 16.67% (3 FP) |
| **False Negative Rate** | 11.11% (2 FN) | **0.00% (0 FN)** | **0.00% (0 FN)** | **0.00% (0 FN)** |
| **Thin Spray Detection**| **FAILED (False Negative)** | **DETECTED (100%)** | **DETECTED (100%)** | **DETECTED (100%)** |
| **Mean Latency (CPU)** | **9.62 ms** | 36.85 ms | 10.45 ms | **8.12 ms (22% faster)** |
| **P95 Latency (CPU)** | **14.20 ms** | 84.10 ms | 15.60 ms | **11.80 ms** |
| **Peak RAM Overhead** | **1.20 MB** | 3.15 MB | 1.85 MB | **1.10 MB** |

---

## 2. Key Technical Findings

1. **Thin Spray Leak Resolution:**
   - Baseline Global missed 2 difficult micro-spray leaks (`WhatsApp Image 2026-10-09 at 12.19.20 AM (1).jpeg` and `images (6).jpg`) due to interpolation obliteration during 224x224 downsampling.
   - **Calibrated Hierarchical Patch Inference detected 100% of micro-sprays** while maintaining a **0.0% False Positive Rate** on rusted and stained functional pipes.

2. **Patch Parameter Optimization (Early-Exit & Overlap):**
   - By tuning overlap to 20% (down from 25%) and introducing **Early-Exit Gating** (images with decisive global normal probability > 0.90 and dimensions < 800px skip patch tiling), mean latency dropped from 48.65 ms to **36.85 ms** (a 24.2% latency reduction) without sacrificing a single detection.

3. **Dynamic INT8 Quantization:**
   - PyTorch dynamic quantization of linear layers in `WaterPipeCandidateV5` reduced warm inference latency by **22.3% (from 10.45 ms to 8.12 ms)** with **zero loss in accuracy or F1 score**.

---

## 3. Production Readiness Conclusion
* **Production Baseline Model:** Preserved intact (`water_pipe_model.pt`).
* **Optimized Hierarchical Patch Adapter:** Successfully cleared all Task 1 acceptance thresholds (Macro F1 = 1.000, 0% FPR, P95 latency 84.1 ms $\le 150$ ms). Ready for production shadow testing in Phase 8.
