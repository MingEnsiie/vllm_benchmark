#!/usr/bin/env python3
"""vLLM 本地速度测试脚本。"""
import asyncio
import time
import argparse
import sys
from pathlib import Path
from typing import Any

# Allow running from any working directory and importing from project root.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from vllm_local import discover_models, resolve_model, served_model_name

DEFAULT_BASE_URL = "http://localhost:8000/v1"
PROMPTS = [
    "介绍一下量子计算的基本原理",
    "写一首关于春天的七言绝句",
    "解释什么是机器学习中的过拟合",
    "描述一下中国的四大发明",
    "Python 和 C++ 的主要区别是什么",
    "如何解释相对论的基本概念",
    "介绍一下神经网络的工作原理",
    "描述一下太阳系的结构",
]


def build_prompt_for_target_tokens(tokenizer: Any, target_tokens: int) -> str:
    if target_tokens <= 0:
        return PROMPTS[0]

    base_unit = "请阅读以下测试文本并在最后简要总结其主题。"
    parts: list[str] = []
    while True:
        parts.append(base_unit)
        prompt = " ".join(parts)
        if len(tokenizer.encode(prompt, add_special_tokens=False)) >= target_tokens:
            return prompt


def collect_stream_metrics(chunks: list[dict[str, Any]]) -> dict[str, Any]:
    elapsed = 0.0
    first_token_latency = None
    prompt_tokens = 0
    completion_tokens = 0

    for chunk in chunks:
        elapsed += chunk.get("wait", 0.0)
        prompt_tokens = chunk.get("prompt_tokens", prompt_tokens)
        completion_tokens = chunk.get("completion_tokens", completion_tokens)
        if first_token_latency is None and chunk.get("delta"):
            first_token_latency = elapsed

    return {
        "elapsed": elapsed,
        "first_token_latency": first_token_latency,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
    }


async def single_request(
    client: Any,
    model_name: str,
    prompt: str,
    max_tokens: int = 200,
    temperature: float = 0.7,
):
    start = time.perf_counter()
    stream = await client.chat.completions.create(
        model=model_name,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=max_tokens,
        temperature=temperature,
        stream=True,
        stream_options={"include_usage": True},
    )
    chunks: list[dict[str, Any]] = []
    first_token_latency = None
    tokens_out = 0
    tokens_in = 0

    async for chunk in stream:
        now = time.perf_counter()
        if first_token_latency is None:
            delta_text = ""
            if chunk.choices:
                delta = chunk.choices[0].delta
                delta_text = delta.content or ""
            if delta_text:
                first_token_latency = now - start

        usage = chunk.usage
        if usage:
            tokens_out = usage.completion_tokens or tokens_out
            tokens_in = usage.prompt_tokens or tokens_in

        chunks.append(
            {
                "wait": now - start - sum(item["wait"] for item in chunks),
                "delta": chunk.choices[0].delta.content if chunk.choices else "",
                "prompt_tokens": tokens_in,
                "completion_tokens": tokens_out,
            }
        )

    elapsed = time.perf_counter() - start
    if chunks:
        metrics = collect_stream_metrics(chunks)
        tokens_out = metrics["completion_tokens"]
        tokens_in = metrics["prompt_tokens"]
        if first_token_latency is None:
            first_token_latency = metrics["first_token_latency"]
    return {
        "elapsed": elapsed,
        "first_token_latency": first_token_latency,
        "tokens_out": tokens_out,
        "tokens_in": tokens_in,
        "tps": (tokens_out / elapsed) if elapsed > 0 else 0.0,
    }


async def benchmark(
    client: Any,
    model_name: str,
    concurrency: int,
    num_requests: int = 16,
    max_tokens: int = 200,
    temperature: float = 0.7,
    prompts: list[str] | None = None,
):
    prompt_list = prompts or [PROMPTS[i % len(PROMPTS)] for i in range(num_requests)]

    print(f"\n{'='*60}")
    print(f"并发数: {concurrency}路  |  总请求数: {num_requests}")
    print(f"{'='*60}")

    all_results = []
    semaphore = asyncio.Semaphore(concurrency)

    async def bounded_request(prompt):
        async with semaphore:
            return await single_request(
                client,
                model_name,
                prompt,
                max_tokens=max_tokens,
                temperature=temperature,
            )

    wall_start = time.perf_counter()
    tasks = [bounded_request(p) for p in prompt_list]
    results = await asyncio.gather(*tasks)
    wall_elapsed = time.perf_counter() - wall_start

    total_tokens_out = sum(r["tokens_out"] for r in results)
    total_tokens_in = sum(r["tokens_in"] for r in results)
    avg_latency = sum(r["elapsed"] for r in results) / len(results)
    first_token_samples = [r["first_token_latency"] for r in results if r["first_token_latency"] is not None]
    avg_first_token_latency = (
        sum(first_token_samples) / len(first_token_samples)
        if first_token_samples
        else None
    )
    avg_tps = sum(r["tps"] for r in results) / len(results)
    throughput = total_tokens_out / wall_elapsed

    print(f"总耗时:          {wall_elapsed:.2f}s")
    print(f"平均延迟/请求:   {avg_latency:.2f}s")
    if avg_first_token_latency is None:
        print("平均首token延迟:  无数据")
    else:
        print(f"平均首token延迟: {avg_first_token_latency:.2f}s")
    print(f"平均单请求TPS:   {avg_tps:.1f} tokens/s")
    print(f"系统总吞吐量:    {throughput:.1f} tokens/s")
    print(f"总输入tokens:    {total_tokens_in}")
    print(f"总输出tokens:    {total_tokens_out}")
    print(f"QPS:             {num_requests / wall_elapsed:.2f} req/s")

    return {
        "concurrency": concurrency,
        "wall_elapsed": wall_elapsed,
        "avg_latency": avg_latency,
        "avg_first_token_latency": avg_first_token_latency,
        "throughput": throughput,
        "avg_tps": avg_tps,
        "qps": num_requests / wall_elapsed,
    }


async def main():
    parser = argparse.ArgumentParser(description="vLLM 速度测试")
    parser.add_argument(
        "--model",
        default=None,
        help="要测试的本地模型目录名，默认自动选择 Qwen3.5-0.8B",
    )
    parser.add_argument(
        "--list-models",
        action="store_true",
        help="列出 ../Assets/models/ 下可用的本地模型并退出",
    )
    parser.add_argument(
        "--base-url",
        default=DEFAULT_BASE_URL,
        help=f"OpenAI 兼容接口地址，默认 {DEFAULT_BASE_URL}",
    )
    parser.add_argument(
        "--concurrency",
        type=int,
        nargs="+",
        default=[2, 4],
        help="并发路数列表，默认测试 2路、4路",
    )
    parser.add_argument(
        "--num-requests",
        type=int,
        default=16,
        help="每次测试的总请求数",
    )
    parser.add_argument(
        "--max-tokens",
        type=int,
        default=200,
        help="每个请求的最大生成 token 数",
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=0.7,
        help="采样温度",
    )
    parser.add_argument(
        "--prompt-tokens",
        type=int,
        default=0,
        help="每个请求目标输入 token 数；大于 0 时会构造接近该长度的长上下文提示",
    )
    args = parser.parse_args()

    if args.list_models:
        for model_name in discover_models():
            print(model_name)
        return

    selected_name, selected_path = resolve_model(args.model)
    model_name = served_model_name(selected_name)
    base_url = args.base_url.rstrip("/")

    from openai import AsyncOpenAI
    from transformers import AutoTokenizer

    client = AsyncOpenAI(api_key="EMPTY", base_url=base_url)
    tokenizer = None
    prompt_list = None
    if args.prompt_tokens > 0:
        tokenizer = AutoTokenizer.from_pretrained(
            str(selected_path),
            trust_remote_code=True,
        )
        long_prompt = build_prompt_for_target_tokens(tokenizer, args.prompt_tokens)
        actual_tokens = len(tokenizer.encode(long_prompt, add_special_tokens=False))
        prompt_list = [long_prompt for _ in range(args.num_requests)]
        print(f"目标输入tokens: {args.prompt_tokens}")
        print(f"实际输入tokens: {actual_tokens}")

    print(f"\nvLLM 速度测试 - 模型: {selected_name}")
    print(f"请求模型名: {model_name}")
    print(f"服务地址: {base_url}")

    # 预热
    print("\n[预热中...]")
    try:
        await client.chat.completions.create(
            model=model_name,
            messages=[{"role": "user", "content": "你好"}],
            max_tokens=10,
        )
        print("预热完成")
    except Exception as e:
        print(f"预热失败，请确认 vLLM 服务已启动: {e}")
        return

    summary = []
    for c in args.concurrency:
        result = await benchmark(
            client,
            model_name,
            c,
            args.num_requests,
            max_tokens=args.max_tokens,
            temperature=args.temperature,
            prompts=prompt_list,
        )
        summary.append(result)

    print(f"\n{'='*60}")
    print("汇总对比:")
    print(
        f"{'并发数':>8} {'总耗时(s)':>12} {'平均延迟(s)':>12} "
        f"{'首token(s)':>12} {'单请求TPS':>12} {'吞吐量(tok/s)':>14} {'QPS':>8}"
    )
    print("-" * 60)
    for r in summary:
        first_token = (
            f"{r['avg_first_token_latency']:.2f}"
            if r["avg_first_token_latency"] is not None
            else "N/A"
        )
        print(
            f"{r['concurrency']:>8} {r['wall_elapsed']:>12.2f} {r['avg_latency']:>12.2f} "
            f"{first_token:>12} {r['avg_tps']:>12.1f} {r['throughput']:>14.1f} {r['qps']:>8.2f}"
        )


if __name__ == "__main__":
    asyncio.run(main())
