# vLLM Benchmark Report

Date: 2026-04-09

Model: `Qwen3.5-35B-A3B-GPTQ-Int4`

Environment:
- Python: `3.12`
- vLLM: `0.19.0`
- PyTorch: `2.10.0+cu130`
- GPU: `NVIDIA GB10`
- Driver / CUDA runtime: `580.126.09` / `13.0`

## 1. Standard Multi-Request Benchmark

Test settings:
- Server `max-model-len`: `4096`
- Requests per run: `16`
- Max output tokens per request: `200`
- Prompt set: built-in short prompts in [`benchmark_speed.py`](/home/mingzhang/Downloads/code/vllm/benchmark_speed.py)
- Concurrency: `1 / 2 / 4 / 8`

| Concurrency | Avg Latency | First Token Latency | Total Throughput | Per-Request TPS | QPS | token/s |
|---|---:|---:|---:|---:|---:|---:|
| 1 | 5.89s | 0.07s | 34.0 tok/s | 34.0 tok/s | 0.17 req/s | 34.0 |
| 2 | 5.72s | 0.10s | 69.9 tok/s | 35.0 tok/s | 0.35 req/s | 69.9 |
| 4 | 6.71s | 0.11s | 119.2 tok/s | 29.8 tok/s | 0.60 req/s | 119.2 |
| 8 | 8.37s | 0.17s | 191.0 tok/s | 23.9 tok/s | 0.96 req/s | 191.0 |

Observations:
- `8` concurrency delivered the highest overall throughput.
- `2` concurrency gave the best single-request experience among the tested points.
- Throughput scaled well from `1` to `8`, but latency also rose with concurrency.

## 2. Long-Context Benchmark

Test settings:
- Server `max-model-len`: `131072`
- Target prompt length per request: `130000` tokens
- Actual prompt length per request: about `130012` tokens
- Max output tokens per request: `16`
- Concurrency: `1 / 2 / 4 / 8`
- Requests per run matched concurrency: `1 / 2 / 4 / 8`

| Concurrency | Avg Latency | First Token Latency | Total Throughput | Per-Request TPS | QPS | token/s |
|---|---:|---:|---:|---:|---:|---:|
| 1 | 44.07s | 43.52s | 0.4 tok/s | 0.4 tok/s | 0.02 req/s | 0.4 |
| 2 | 68.12s | 64.09s | 0.4 tok/s | 0.3 tok/s | 0.02 req/s | 0.4 |
| 4 | 115.54s | 109.74s | 0.4 tok/s | 0.2 tok/s | 0.02 req/s | 0.4 |
| 8 | 197.07s | 190.56s | 0.4 tok/s | 0.1 tok/s | 0.02 req/s | 0.4 |

Observations:
- In the `128k`-class context regime, the GPU was dominated by prompt prefill cost.
- Raising concurrency from `1` to `8` did not improve total throughput in a meaningful way.
- Higher concurrency only increased first-token latency and end-to-end latency.
- For this model on this single GPU, `1` concurrent request is the practical choice for `128k`-scale prompts.

## 3. Context Length Startup Boundary

Startup-only validation results for the same model:

| Context Length | Result | Notes |
|---|---|---|
| `128k` (`131072`) | Starts | Stable |
| `192k` (`196608`) | Starts | Stable |
| `224k` (`229376`) | Starts | Stable |
| `240k` (`245760`) | Reached weight loading | High likelihood of starting, not carried through to full ready state in the final pass |
| `256k` (`262144`) | Fails | vLLM refused startup due to required GPU memory threshold not being met |
| `512k` (`524288`) | Fails | Exceeds model-derived max context length |
| `1M` (`1048576`) | Fails | Exceeds model-derived max context length |

Summary:
- Practical startup limit on this machine is below `256k`.
- Model-defined limit is `262144`, but the single-GPU runtime configuration does not have enough free memory to start at that exact limit.

## 4. Bottom Line

- For normal short-context serving, `8` concurrency gave the best system throughput.
- For `128k`-class long-context inference, concurrency did not improve throughput; `1` concurrency is the sensible operating point.
- This machine cannot start this `35B` model at full `256k` context under the tested vLLM configuration.
