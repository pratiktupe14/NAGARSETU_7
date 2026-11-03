"""
Phase 11 - Task 8: Latency, Memory & Resource Stability Benchmarking
Runs 100 deterministic inference iterations on CPU for each model:
- Baseline (water_pipe_model.pt)
- Candidate v5 (water_pipe_candidate_v5.pt)
- Candidate v6 3-Class (water_pipe_candidate_v6_3class.pt)
- Candidate Multi-Stage (water_pipe_multistage_v1.pt)

Measures:
- Mean, P50, P90, P95, P99 latency
- Peak RSS memory & growth over 100 requests
- Concurrency / throughput (req/sec)
"""

import os
import time
import json
import psutil
import tracemalloc
import numpy as np
from PIL import Image

import torch
import torchvision.transforms as transforms

PHASE11_DIR = r"ai_service\experiments\phase11"
BENCH_DIR = os.path.join(PHASE11_DIR, "benchmarks")
os.makedirs(BENCH_DIR, exist_ok=True)

# Import model loaders and predict functions from evaluation script
sys_path = os.path.abspath(os.path.join(PHASE11_DIR, "evaluation"))
if sys_path not in os.sys.path:
    os.sys.path.append(sys_path)

from evaluate_all_models import (
    load_all_models,
    predict_baseline,
    predict_cand_v5,
    predict_cand_v6,
    predict_multistage
)

def benchmark_model(m_name, model, sample_tensor, iterations=100):
    print(f"Benchmarking {m_name} over {iterations} iterations...")
    
    # Warmup
    for _ in range(10):
        if m_name == "Baseline":
            _ = predict_baseline(model, sample_tensor)
        elif m_name == "Candidate_v5":
            _ = predict_cand_v5(model, sample_tensor)
        elif m_name == "Candidate_v6_3Class":
            _ = predict_cand_v6(model, sample_tensor)
        elif m_name == "Candidate_MultiStage":
            _ = predict_multistage(model, sample_tensor)

    process = psutil.Process()
    mem_before = process.memory_info().rss / (1024 * 1024)
    tracemalloc.start()
    
    latencies = []
    start_total = time.perf_counter()
    
    for _ in range(iterations):
        t0 = time.perf_counter()
        if m_name == "Baseline":
            _ = predict_baseline(model, sample_tensor)
        elif m_name == "Candidate_v5":
            _ = predict_cand_v5(model, sample_tensor)
        elif m_name == "Candidate_v6_3Class":
            _ = predict_cand_v6(model, sample_tensor)
        elif m_name == "Candidate_MultiStage":
            _ = predict_multistage(model, sample_tensor)
        t1 = time.perf_counter()
        latencies.append((t1 - t0) * 1000.0)
        
    total_time = time.perf_counter() - start_total
    current_trace, peak_trace = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    mem_after = process.memory_info().rss / (1024 * 1024)
    mem_growth = max(0.0, mem_after - mem_before)
    
    p50 = float(np.percentile(latencies, 50))
    p90 = float(np.percentile(latencies, 90))
    p95 = float(np.percentile(latencies, 95))
    p99 = float(np.percentile(latencies, 99))
    mean_lat = float(np.mean(latencies))
    throughput = iterations / total_time
    
    return {
        "model_name": m_name,
        "iterations": iterations,
        "total_time_sec": round(total_time, 3),
        "throughput_req_per_sec": round(throughput, 2),
        "mean_latency_ms": round(mean_lat, 2),
        "p50_latency_ms": round(p50, 2),
        "p90_latency_ms": round(p90, 2),
        "p95_latency_ms": round(p95, 2),
        "p99_latency_ms": round(p99, 2),
        "mem_before_mb": round(mem_before, 2),
        "mem_after_mb": round(mem_after, 2),
        "mem_growth_mb": round(mem_growth, 2),
        "traced_peak_mb": round(peak_trace / (1024 * 1024), 2),
        "sla_150ms_compliance": p95 <= 150.0,
        "headroom_pct": round(((150.0 - p95) / 150.0) * 100.0, 2)
    }

def main():
    print("=" * 80)
    print("PHASE 11: WATER AI LATENCY, MEMORY & RESOURCE BENCHMARKING")
    print("=" * 80)
    
    models_dict = load_all_models()
    dummy_input = torch.randn(1, 3, 224, 224)
    
    benchmark_results = {}
    for m_name, model in models_dict.items():
        res = benchmark_model(m_name, model, dummy_input, iterations=100)
        benchmark_results[m_name] = res
        print(f"  {m_name:24s} | Mean: {res['mean_latency_ms']:5.2f} ms | P95: {res['p95_latency_ms']:5.2f} ms | Throughput: {res['throughput_req_per_sec']:5.1f} req/s | Mem Peak: {res['traced_peak_mb']:4.2f} MB")

    out_path = os.path.join(BENCH_DIR, "benchmarks_results.json")
    with open(out_path, "w") as f:
        json.dump(benchmark_results, f, indent=2)
    with open("benchmarks_results.json", "w") as f:
        json.dump(benchmark_results, f, indent=2)
    print(f"\nSaved benchmark results to {out_path}")

if __name__ == "__main__":
    main()

