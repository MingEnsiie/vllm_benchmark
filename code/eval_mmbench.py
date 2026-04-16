#!/usr/bin/env python3
"""MMBench 评测脚本：对接 vLLM OpenAI 兼容接口，测试视觉语言模型在 MMBench 上的准确率。

用法示例:
  # 视觉模型（图文）
  python code/eval_mmbench.py --model Qwen3-Omni-30B-A3B-Instruct

  # 纯文本模型（跳过图片，只测文字理解）
  python code/eval_mmbench.py --model Qwen3.5-4B --no-image

  # 快速抽样验证
  python code/eval_mmbench.py --model Qwen3.5-4B --no-image --max-samples 50

  # 测中文版本
  python code/eval_mmbench.py --model Qwen3.5-4B --lang cn --no-image
"""

from __future__ import annotations

import argparse
import base64
import csv
import json
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATASET_DIR = PROJECT_ROOT.parent / "Assets" / "datasets" / "mmbench"
RESULTS_DIR = PROJECT_ROOT / "results"

DEFAULT_BASE_URL = "http://localhost:8000/v1"
DEFAULT_API_KEY = "EMPTY"
OPTION_LABELS = ("A", "B", "C", "D")


# ---------------------------------------------------------------------------
# 数据加载
# ---------------------------------------------------------------------------

def load_mmbench(lang: str, split: str, max_samples: int | None) -> list[dict]:
    filename = f"MMBench_{split.upper()}_{lang.upper()}_legacy.tsv"
    path = DATASET_DIR / filename
    if not path.exists():
        sys.exit(f"找不到数据集文件: {path}")

    rows: list[dict] = []
    with open(path, encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            rows.append(row)
            if max_samples and len(rows) >= max_samples:
                break

    print(f"已加载 {len(rows)} 条样本（{filename}）")
    return rows


# ---------------------------------------------------------------------------
# Prompt 构建
# ---------------------------------------------------------------------------

def build_choices_text(row: dict) -> str:
    parts = []
    for label in OPTION_LABELS:
        text = row.get(label, "").strip()
        if text:
            parts.append(f"{label}. {text}")
    return "\n".join(parts)


def build_messages(row: dict, include_image: bool) -> list[dict]:
    hint = row.get("hint", "").strip()
    question = row["question"].strip()
    choices = build_choices_text(row)

    text_parts = []
    if hint:
        text_parts.append(hint)
    text_parts.append(f"问题：{question}")
    text_parts.append(choices)
    text_parts.append(
        "请从选项中选出正确答案，只输出选项字母（A、B、C 或 D），不要解释。"
    )
    prompt_text = "\n".join(text_parts)

    if include_image and row.get("image"):
        image_b64 = row["image"].strip()
        content = [
            {
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"},
            },
            {"type": "text", "text": prompt_text},
        ]
    else:
        content = prompt_text

    return [{"role": "user", "content": content}]


# ---------------------------------------------------------------------------
# 答案提取
# ---------------------------------------------------------------------------

def extract_answer(response_text: str) -> str | None:
    """从模型回复中提取 A/B/C/D。"""
    text = response_text.strip()

    # 直接就是单个字母
    if text.upper() in OPTION_LABELS:
        return text.upper()

    # 开头是字母加标点
    m = re.match(r"^([ABCD])[\.。\)）\s]", text, re.IGNORECASE)
    if m:
        return m.group(1).upper()

    # 含有"答案是X"、"选X"等
    m = re.search(r"(?:答案[是为：:]\s*|选\s*)([ABCD])", text, re.IGNORECASE)
    if m:
        return m.group(1).upper()

    # 最后出现的孤立字母
    matches = re.findall(r"\b([ABCD])\b", text.upper())
    if matches:
        return matches[-1]

    return None


# ---------------------------------------------------------------------------
# API 调用
# ---------------------------------------------------------------------------

def call_chat(
    base_url: str,
    api_key: str,
    model_name: str,
    messages: list[dict],
    max_tokens: int,
    temperature: float,
) -> str:
    payload = {
        "model": model_name,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature,
    }
    request = urllib.request.Request(
        f"{base_url.rstrip('/')}/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=60) as resp:
        data = json.load(resp)
    return data["choices"][0]["message"]["content"]


# ---------------------------------------------------------------------------
# 主流程
# ---------------------------------------------------------------------------

def evaluate(args: argparse.Namespace) -> None:
    rows = load_mmbench(args.lang, args.split, args.max_samples)

    results: list[dict] = []
    correct = 0
    errors = 0

    print(f"\n模型: {args.model}  |  含图片: {not args.no_image}")
    print(f"{'─'*60}")

    for i, row in enumerate(rows):
        idx = row["index"]
        ground_truth = row["answer"].strip().upper()
        messages = build_messages(row, include_image=not args.no_image)

        try:
            response = call_chat(
                args.base_url,
                args.api_key,
                args.model,
                messages,
                max_tokens=args.max_tokens,
                temperature=0.0,
            )
            predicted = extract_answer(response)
        except (urllib.error.URLError, urllib.error.HTTPError, Exception) as e:
            print(f"[{i+1}/{len(rows)}] index={idx}  错误: {e}")
            results.append({
                "index": idx,
                "category": row["category"],
                "l2_category": row["l2-category"],
                "ground_truth": ground_truth,
                "predicted": None,
                "correct": False,
                "error": str(e),
                "response": None,
            })
            errors += 1
            continue

        is_correct = predicted == ground_truth
        if is_correct:
            correct += 1

        results.append({
            "index": idx,
            "category": row["category"],
            "l2_category": row["l2-category"],
            "ground_truth": ground_truth,
            "predicted": predicted,
            "correct": is_correct,
            "error": None,
            "response": response[:200],
        })

        status = "✓" if is_correct else "✗"
        print(
            f"[{i+1}/{len(rows)}] {status}  index={idx:<6}"
            f"  gt={ground_truth}  pred={predicted or '?':<3}"
            f"  {row['category']}"
        )

    # -----------------------------------------------------------------------
    # 统计
    # -----------------------------------------------------------------------
    valid = len(results) - errors
    accuracy = correct / valid if valid > 0 else 0.0

    print(f"\n{'='*60}")
    print(f"总体准确率: {correct}/{valid} = {accuracy:.1%}  (错误/跳过: {errors})")

    # 按 category 分组
    cat_stats: dict[str, dict] = {}
    for r in results:
        cat = r["category"]
        if cat not in cat_stats:
            cat_stats[cat] = {"correct": 0, "total": 0}
        if r["predicted"] is not None:
            cat_stats[cat]["total"] += 1
            if r["correct"]:
                cat_stats[cat]["correct"] += 1

    print(f"\n{'类别':<30} {'正确':>6} {'总数':>6} {'准确率':>8}")
    print("─" * 55)
    for cat, s in sorted(cat_stats.items(), key=lambda x: -x[1]["correct"] / max(x[1]["total"], 1)):
        acc = s["correct"] / s["total"] if s["total"] > 0 else 0.0
        print(f"{cat:<30} {s['correct']:>6} {s['total']:>6} {acc:>8.1%}")

    # -----------------------------------------------------------------------
    # 保存结果
    # -----------------------------------------------------------------------
    RESULTS_DIR.mkdir(exist_ok=True)
    ts = time.strftime("%Y%m%d_%H%M%S")
    model_slug = args.model.replace("/", "_")
    out_path = RESULTS_DIR / f"mmbench_{args.lang}_{args.split}_{model_slug}_{ts}.json"

    summary = {
        "model": args.model,
        "dataset": "mmbench",
        "lang": args.lang,
        "split": args.split,
        "include_image": not args.no_image,
        "total_samples": len(rows),
        "valid_samples": valid,
        "correct": correct,
        "accuracy": accuracy,
        "errors": errors,
        "category_stats": cat_stats,
    }
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump({"summary": summary, "results": results}, f, ensure_ascii=False, indent=2)

    print(f"\n结果已保存: {out_path}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="MMBench 评测")
    parser.add_argument("--model", required=True, help="vLLM 服务中的模型名（与 GET /v1/models 返回一致）")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    parser.add_argument("--api-key", default=DEFAULT_API_KEY)
    parser.add_argument("--lang", choices=["en", "cn"], default="en", help="题目语言，默认 en")
    parser.add_argument("--split", choices=["dev", "test"], default="dev", help="数据集分割，默认 dev")
    parser.add_argument("--max-samples", type=int, default=None, help="最多评测样本数，默认全量")
    parser.add_argument("--max-tokens", type=int, default=16, help="模型最大输出 token 数，默认 16")
    parser.add_argument("--no-image", action="store_true", help="跳过图片输入（适用于纯文本模型）")
    return parser


if __name__ == "__main__":
    args = build_parser().parse_args()
    evaluate(args)
