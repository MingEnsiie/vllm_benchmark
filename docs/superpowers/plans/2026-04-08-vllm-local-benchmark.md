# Local vLLM Benchmark Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a reusable local vLLM setup in this directory with selectable models and measured 2-way and 4-way benchmark results for `Qwen3.5-0.8B`.

**Architecture:** Add one shared Python helper for model discovery and resolution, keep shell startup thin, and let the benchmark script consume the same helper so serving and load generation stay aligned. Treat `.vllm` as the local runtime boundary and add a setup script for reproducibility.

**Tech Stack:** Python 3.12, vLLM, OpenAI Python SDK, Bash, unittest

---

## Chunk 1: Shared Model Resolution

### Task 1: Add failing tests for model discovery

**Files:**
- Create: `tests/test_vllm_local.py`
- Create: `vllm_local.py`

- [ ] **Step 1: Write the failing test**
- [ ] **Step 2: Run the test to verify it fails**
- [ ] **Step 3: Write the minimal implementation**
- [ ] **Step 4: Run the test to verify it passes**

## Chunk 2: User-Facing Scripts

### Task 2: Make serving and benchmark scripts selectable

**Files:**
- Modify: `start_vllm.sh`
- Modify: `benchmark_speed.py`

- [ ] **Step 1: Wire both scripts to the shared helper**
- [ ] **Step 2: Default to `Qwen3.5-0.8B` and concurrency `2 4`**
- [ ] **Step 3: Add `--list-models` and explicit `--model` selection**
- [ ] **Step 4: Verify script help and dry-run behavior**

### Task 3: Add reproducible environment setup

**Files:**
- Create: `setup_vllm_env.sh`
- Create: `requirements-vllm.txt`

- [ ] **Step 1: Add setup script and pinned minimal requirements**
- [ ] **Step 2: Verify the current `.vllm` satisfies the setup checks**

## Chunk 3: Runtime Verification

### Task 4: Run the real benchmark

**Files:**
- No code changes expected

- [ ] **Step 1: Launch vLLM with `Qwen3.5-0.8B`**
- [ ] **Step 2: Run 2-way and 4-way benchmark measurements**
- [ ] **Step 3: Capture throughput and latency results for the user**
