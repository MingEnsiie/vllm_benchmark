# Local vLLM Benchmark Design

**Goal:** Create a reproducible local vLLM workflow in this directory using `.vllm` with Python 3.12, defaulting to `../Assets/models/Qwen3.5-0.8B`, while allowing any local model under `../Assets/models/` to be selected for serving and benchmarking.

## Scope

- Reuse or rebuild `.vllm` in the current directory with Python 3.12.
- Standardize local model discovery from `../Assets/models/`.
- Make the startup flow and benchmark flow accept a selectable model.
- Benchmark `Qwen3.5-0.8B` at 2-way and 4-way concurrency by default.

## Design

- Add a small Python helper module to discover valid local models, resolve the selected model, and derive the served model name from the directory name.
- Keep [`start_vllm.sh`](/home/mingzhang/Downloads/code/vllm/start_vllm.sh) as the main entrypoint for serving, but remove hard-coded model details.
- Keep [`benchmark_speed.py`](/home/mingzhang/Downloads/code/vllm/benchmark_speed.py) as the benchmark entrypoint, but make it accept `--model`, `--base-url`, and concurrency lists. It should default to `Qwen3.5-0.8B` and `2 4`.
- Add a reproducible environment setup script and pinned minimal requirements for the local workflow.

## Validation

- Unit-test the model discovery and resolution logic first.
- Verify the `.vllm` interpreter can import the required packages.
- Launch vLLM against `Qwen3.5-0.8B` and run benchmark measurements for 2-way and 4-way concurrency.
