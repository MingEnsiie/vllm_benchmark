#!/usr/bin/env python3
"""MMMU 评测脚本：对接 vLLM OpenAI 兼容接口，测试视觉语言模型在 MMMU 上的准确率。

MMMU 特点：
  - 33 个学科，每学科 validation/dev/test 三个 parquet 文件
  - 每题最多 7 张图片，问题文本中用 <image 1> ... <image 7> 占位
  - options 为 Python list 字符串，answer 为 A/B/C/D
  - 含少量 open-ended 题（非 multiple-choice），默认跳过

用法示例:
  # 完整 validation 评测（900 条）
  python code/eval_mmmu.py --model gemma-4-E4B-it

  # 快速抽样验证
  python code/eval_mmmu.py --model gemma-4-E4B-it --max-samples 50

  # 只评测指定学科
  python code/eval_mmmu.py --model gemma-4-E4B-it --subjects Accounting Biology

  # 纯文本模型（跳过图片）
  python code/eval_mmmu.py --model Qwen3.5-4B --no-image
"""

from __future__ import annotations

import argparse
import ast
import base64
import json
import pathlib
import re
import sys
import time
import urllib.error
import urllib.request

PROJECT_ROOT = pathlib.Path(__file__).resolve().parent.parent
DATASET_DIR = PROJECT_ROOT.parent / "Assets" / "datasets" / "mmmu"
RESULTS_DIR = PROJECT_ROOT / "results"

DEFAULT_BASE_URL = "http://localhost:8000/v1"
DEFAULT_API_KEY = "EMPTY"
OPTION_LABELS = ("A", "B", "C", "D", "E", "F", "G", "H")


# ---------------------------------------------------------------------------
# 数据加载
# ---------------------------------------------------------------------------

def load_mmmu(split: str, subjects: list[str] | None, max_samples: int | None) -> list[dict]:
    all_subjects = sorted(p.name for p in DATASET_DIR.iterdir() if p.is_dir())
    if subjects:
        missing = [s for s in subjects if s not in all_subjects]
        if missing:
            sys.exit(f"找不到学科: {missing}，可用: {all_subjects}")
        all_subjects = subjects

    try:
        import pyarrow.parquet as pq
    except ImportError:
        sys.exit("缺少 pyarrow，请运行: pip install pyarrow")

    rows: list[dict] = []
    for subj in all_subjects:
        parquet_file = DATASET_DIR / subj / f"{split}-00000-of-00001.parquet"
        if not parquet_file.exists():
            print(f"  跳过 {subj}（找不到 {split} 文件）")
            continue
        tbl = pq.read_table(str(parquet_file))
        for i in range(tbl.num_rows):
            row = {col: tbl[col][i].as_py() for col in tbl.schema.names}
            row["_subject"] = subj
            rows.append(row)
            if max_samples and len(rows) >= max_samples:
                print(f"已加载 {len(rows)} 条样本（--max-samples 限制）")
                return rows

    print(f"已加载 {len(rows)} 条样本（{len(all_subjects)} 个学科，split={split}）")
    return rows


# ---------------------------------------------------------------------------
# 图片处理
# ---------------------------------------------------------------------------

def image_bytes_to_b64(img_dict: dict) -> str | None:
    if not img_dict or not isinstance(img_dict, dict):
        return None
    raw = img_dict.get("bytes")
    if not raw:
        return None
    return base64.b64encode(raw).decode("ascii")


def detect_mime(raw: bytes) -> str:
    if raw[:3] == b"\xff\xd8\xff":
        return "image/jpeg"
    if raw[:4] == b"\x89PNG":
        return "image/png"
    if raw[:4] == b"GIF8":
        return "image/gif"
    return "image/jpeg"


def image_dict_to_url(img_dict: dict) -> str | None:
    if not img_dict or not isinstance(img_dict, dict):
        return None
    raw = img_dict.get("bytes")
    if not raw:
        return None
    mime = detect_mime(raw)
    b64 = base64.b64encode(raw).decode("ascii")
    return f"data:{mime};base64,{b64}"


# ---------------------------------------------------------------------------
# Prompt 构建
# ---------------------------------------------------------------------------

def build_options_text(options: list[str]) -> str:
    return "\n".join(
        f"{OPTION_LABELS[i]}. {opt}"
        for i, opt in enumerate(options)
        if i < len(OPTION_LABELS)
    )


def build_messages(row: dict, include_image: bool) -> list[dict]:
    """将 MMMU 一行构造成 OpenAI messages，图片按 <image N> 顺序插入。"""
    try:
        options: list[str] = ast.literal_eval(row["options"])
    except Exception:
        options = []

    question_text = row["question"]
    options_text = build_options_text(options)
    instruction = "请从选项中选出正确答案，只输出选项字母（A、B、C 或 D），不要解释。"

    # 收集各编号图片的 data URL
    img_urls: dict[int, str] = {}
    if include_image:
        for n in range(1, 8):
            img_dict = row.get(f"image_{n}")
            url = image_dict_to_url(img_dict) if img_dict else None
            if url:
                img_urls[n] = url

    if not img_urls:
        # 纯文本：去掉占位符，拼成普通字符串
        clean_q = re.sub(r"<image \d+>\s*", "", question_text).strip()
        content = f"{clean_q}\n{options_text}\n{instruction}"
        return [{"role": "user", "content": content}]

    # 多模态：按 <image N> 切割文本，交织图片
    parts_text = re.split(r"(<image \d+>)", question_text)
    content: list[dict] = []

    for part in parts_text:
        m = re.match(r"<image (\d+)>", part)
        if m:
            n = int(m.group(1))
            if n in img_urls:
                content.append({"type": "image_url", "image_url": {"url": img_urls[n]}})
        else:
            text = part.strip()
            if text:
                content.append({"type": "text", "text": text})

    # 追加选项和指令
    suffix = f"\n{options_text}\n{instruction}"
    if content and content[-1].get("type") == "text":
        content[-1]["text"] += suffix
    else:
        content.append({"type": "text", "text": suffix})

    return [{"role": "user", "content": content}]


# ---------------------------------------------------------------------------
# 答案提取
# ---------------------------------------------------------------------------

def extract_answer(response_text: str) -> str | None:
    text = response_text.strip()

    if text.upper() in OPTION_LABELS:
        return text.upper()

    m = re.match(r"^([A-H])[\.。\)）\s]", text, re.IGNORECASE)
    if m:
        return m.group(1).upper()

    m = re.search(r"(?:答案[是为：:]\s*|the answer is\s*)([A-H])", text, re.IGNORECASE)
    if m:
        return m.group(1).upper()

    matches = re.findall(r"\b([A-H])\b", text.upper())
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
) -> str:
    payload = {
        "model": model_name,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": 0.0,
    }
    req = urllib.request.Request(
        f"{base_url.rstrip('/')}/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        data = json.load(resp)
    return data["choices"][0]["message"]["content"]


# ---------------------------------------------------------------------------
# 主流程
# ---------------------------------------------------------------------------

def evaluate(args: argparse.Namespace) -> None:
    rows = load_mmmu(args.split, args.subjects, args.max_samples)

    # 只评 multiple-choice（open-ended 答案格式不同）
    mc_rows = [r for r in rows if r.get("question_type") == "multiple-choice"]
    skipped_open = len(rows) - len(mc_rows)
    if skipped_open:
        print(f"跳过 {skipped_open} 条 open-ended 题（仅评 multiple-choice）")

    results: list[dict] = []
    correct = 0
    errors = 0

    print(f"\n模型: {args.model}  |  含图片: {not args.no_image}  |  样本数: {len(mc_rows)}")
    print(f"{'─'*65}")

    for i, row in enumerate(mc_rows):
        sample_id = row["id"]
        ground_truth = row["answer"].strip().upper()
        messages = build_messages(row, include_image=not args.no_image)

        try:
            response = call_chat(
                args.base_url, args.api_key, args.model, messages, args.max_tokens
            )
            predicted = extract_answer(response)
        except Exception as e:
            print(f"[{i+1}/{len(mc_rows)}] 错误: {sample_id}  {e}")
            results.append({
                "id": sample_id, "subject": row["_subject"],
                "subfield": row.get("subfield", ""), "difficulty": row.get("topic_difficulty", ""),
                "ground_truth": ground_truth, "predicted": None,
                "correct": False, "error": str(e), "response": None,
            })
            errors += 1
            continue

        is_correct = predicted == ground_truth
        if is_correct:
            correct += 1

        results.append({
            "id": sample_id, "subject": row["_subject"],
            "subfield": row.get("subfield", ""), "difficulty": row.get("topic_difficulty", ""),
            "ground_truth": ground_truth, "predicted": predicted,
            "correct": is_correct, "error": None, "response": response[:200],
        })

        status = "✓" if is_correct else "✗"
        print(
            f"[{i+1}/{len(mc_rows)}] {status}  {sample_id:<45}"
            f"  gt={ground_truth}  pred={predicted or '?'}"
        )

    # -----------------------------------------------------------------------
    # 统计
    # -----------------------------------------------------------------------
    valid = len(results) - errors
    accuracy = correct / valid if valid > 0 else 0.0

    print(f"\n{'='*65}")
    print(f"总体准确率: {correct}/{valid} = {accuracy:.1%}  (错误/跳过: {errors})")

    # 按学科统计
    subj_stats: dict[str, dict] = {}
    for r in results:
        s = r["subject"]
        if s not in subj_stats:
            subj_stats[s] = {"correct": 0, "total": 0}
        if r["predicted"] is not None:
            subj_stats[s]["total"] += 1
            if r["correct"]:
                subj_stats[s]["correct"] += 1

    print(f"\n{'学科':<42} {'正确':>5} {'总数':>5} {'准确率':>8}")
    print("─" * 65)
    for subj, s in sorted(subj_stats.items(), key=lambda x: x[0]):
        acc = s["correct"] / s["total"] if s["total"] > 0 else 0.0
        print(f"{subj:<42} {s['correct']:>5} {s['total']:>5} {acc:>8.1%}")

    # 按难度统计
    diff_stats: dict[str, dict] = {}
    for r in results:
        d = r.get("difficulty") or "Unknown"
        if d not in diff_stats:
            diff_stats[d] = {"correct": 0, "total": 0}
        if r["predicted"] is not None:
            diff_stats[d]["total"] += 1
            if r["correct"]:
                diff_stats[d]["correct"] += 1

    print(f"\n难度分布:")
    for diff, s in sorted(diff_stats.items()):
        acc = s["correct"] / s["total"] if s["total"] > 0 else 0.0
        print(f"  {diff:<12} {s['correct']:>4}/{s['total']:<4} = {acc:.1%}")

    # -----------------------------------------------------------------------
    # 保存结果
    # -----------------------------------------------------------------------
    RESULTS_DIR.mkdir(exist_ok=True)
    ts = time.strftime("%Y%m%d_%H%M%S")
    model_slug = args.model.replace("/", "_")
    out_path = RESULTS_DIR / f"mmmu_{args.split}_{model_slug}_{ts}.json"

    summary = {
        "model": args.model, "dataset": "mmmu",
        "split": args.split, "include_image": not args.no_image,
        "total_rows": len(rows), "mc_samples": len(mc_rows),
        "valid_samples": valid, "correct": correct,
        "accuracy": accuracy, "errors": errors,
        "subject_stats": subj_stats, "difficulty_stats": diff_stats,
    }
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump({"summary": summary, "results": results}, f, ensure_ascii=False, indent=2)

    print(f"\n结果已保存: {out_path}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="MMMU 评测")
    parser.add_argument("--model", required=True)
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    parser.add_argument("--api-key", default=DEFAULT_API_KEY)
    parser.add_argument("--split", choices=["validation", "dev", "test"], default="validation")
    parser.add_argument("--subjects", nargs="+", default=None, help="只评指定学科，默认全部")
    parser.add_argument("--max-samples", type=int, default=None)
    parser.add_argument("--max-tokens", type=int, default=16)
    parser.add_argument("--no-image", action="store_true", help="跳过图片（纯文本模型）")
    return parser


if __name__ == "__main__":
    args = build_parser().parse_args()
    evaluate(args)
