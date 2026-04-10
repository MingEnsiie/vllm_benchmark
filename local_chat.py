#!/usr/bin/env python3
"""Simple terminal chat client for a local vLLM OpenAI-compatible server."""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass

from vllm_local import resolve_model

DEFAULT_BASE_URL = "http://127.0.0.1:8000/v1"
DEFAULT_API_KEY = "EMPTY"
DEFAULT_SYSTEM_PROMPT = "你是一个简洁的助手。"
DEFAULT_MAX_CONTINUATIONS = 2


def fetch_remote_models(base_url: str, api_key: str) -> list[str]:
    request = urllib.request.Request(
        f"{base_url.rstrip('/')}/models",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
    )
    with urllib.request.urlopen(request) as response:
        payload = json.load(response)
    return [item["id"] for item in payload.get("data", []) if item.get("id")]


@dataclass
class ChatTurnResult:
    raw_text: str
    final_answer: str
    finish_reason: str | None


class StreamRenderer:
    def __init__(self, show_thinking: bool) -> None:
        self.show_thinking = show_thinking
        self.raw_text = ""
        self._last_rendered = ""

    @property
    def final_answer(self) -> str:
        return _extract_final_answer(self.raw_text)

    def feed(self, text: str) -> str:
        self.raw_text += text
        rendered = _render_text(self.raw_text, self.show_thinking)
        delta = rendered[len(self._last_rendered) :]
        self._last_rendered = rendered
        return delta


def _extract_final_answer(raw_text: str) -> str:
    output: list[str] = []
    cursor = 0
    while True:
        start = raw_text.find("<think>", cursor)
        if start == -1:
            output.append(raw_text[cursor:])
            break
        output.append(raw_text[cursor:start])
        end = raw_text.find("</think>", start)
        if end == -1:
            break
        cursor = end + len("</think>")
    return "".join(output).strip()


def _render_text(raw_text: str, show_thinking: bool) -> str:
    if not show_thinking:
        return _extract_final_answer(raw_text)

    rendered = raw_text.replace("<think>\n", "[thinking]\n")
    rendered = rendered.replace("<think>", "[thinking]")
    rendered = rendered.replace("</think>\n\n", "[/thinking]\n\n")
    rendered = rendered.replace("</think>", "[/thinking]")
    return rendered


def should_auto_continue(
    finish_reason: str | None,
    continuation_index: int,
    max_continuations: int,
) -> bool:
    return finish_reason == "length" and continuation_index < max_continuations


def iter_sse_events(response) -> dict:
    event_lines: list[str] = []
    for raw_line in response:
        line = raw_line.decode("utf-8", errors="replace").strip()
        if not line:
            if event_lines:
                data_lines = [item[5:].strip() for item in event_lines if item.startswith("data:")]
                event_lines = []
                if not data_lines:
                    continue
                data = "\n".join(data_lines)
                if data == "[DONE]":
                    return
                yield json.loads(data)
            continue
        event_lines.append(line)


def resolve_chat_model(
    model_name: str | None,
    base_url: str,
    api_key: str,
    fetch_remote_models=fetch_remote_models,
    resolve_local_model=resolve_model,
) -> str:
    if model_name:
        return model_name

    try:
        remote_models = fetch_remote_models(base_url, api_key)
    except Exception:
        remote_models = []

    if remote_models:
        return remote_models[0]

    selected_name, _ = resolve_local_model(None)
    return selected_name


def stream_chat_completion(
    base_url: str,
    api_key: str,
    model_name: str,
    messages: list[dict[str, str]],
    temperature: float,
    max_tokens: int,
) -> ChatTurnResult:
    payload = {
        "model": model_name,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "stream": True,
        "stream_options": {"include_usage": True},
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
    renderer = StreamRenderer(show_thinking=False)
    finish_reason = None
    with urllib.request.urlopen(request) as response:
        for event in iter_sse_events(response):
            choices = event.get("choices", [])
            if not choices:
                continue
            choice = choices[0]
            delta = choice.get("delta", {})

            reasoning = delta.get("reasoning_content") or ""
            if reasoning:
                renderer.feed(f"<think>{reasoning}</think>")

            content = delta.get("content") or ""
            if content:
                renderer.feed(content)

            if choice.get("finish_reason"):
                finish_reason = choice["finish_reason"]

    return ChatTurnResult(
        raw_text=renderer.raw_text,
        final_answer=renderer.final_answer,
        finish_reason=finish_reason,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Chat with a local vLLM server")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL, help="OpenAI-compatible API base URL")
    parser.add_argument("--api-key", default=DEFAULT_API_KEY, help="API key placeholder for the local server")
    parser.add_argument("--model", help="Model ID returned by GET /v1/models")
    parser.add_argument("--system", default=DEFAULT_SYSTEM_PROMPT, help="System prompt")
    parser.add_argument("--temperature", type=float, default=0.7, help="Sampling temperature")
    parser.add_argument("--max-tokens", type=int, default=512, help="Maximum output tokens per turn")
    parser.add_argument("--show-thinking", action="store_true", help="Print the model's thinking content when available")
    parser.add_argument(
        "--max-continuations",
        type=int,
        default=DEFAULT_MAX_CONTINUATIONS,
        help="Automatically continue when the server stops because of max_tokens",
    )
    parser.add_argument(
        "--no-thinking",
        action="store_true",
        help="Disable Qwen3.5 thinking mode through chat_template_kwargs",
    )
    return parser


def request_streaming_turn(
    base_url: str,
    api_key: str,
    model_name: str,
    messages: list[dict[str, str]],
    temperature: float,
    max_tokens: int,
    show_thinking: bool,
    max_continuations: int,
    enable_thinking: bool,
) -> str:
    renderer = StreamRenderer(show_thinking=show_thinking)
    current_messages = list(messages)

    for continuation_index in range(max_continuations + 1):
        payload = {
            "model": model_name,
            "messages": current_messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": True,
            "stream_options": {"include_usage": True},
            "chat_template_kwargs": {"enable_thinking": enable_thinking},
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

        finish_reason = None
        with urllib.request.urlopen(request) as response:
            for event in iter_sse_events(response):
                choices = event.get("choices", [])
                if not choices:
                    continue
                choice = choices[0]
                delta = choice.get("delta", {})

                reasoning = delta.get("reasoning_content") or ""
                if reasoning:
                    chunk = renderer.feed(f"<think>{reasoning}</think>")
                    if chunk:
                        print(chunk, end="", flush=True)

                content = delta.get("content") or ""
                if content:
                    chunk = renderer.feed(content)
                    if chunk:
                        print(chunk, end="", flush=True)

                if choice.get("finish_reason"):
                    finish_reason = choice["finish_reason"]

        if not should_auto_continue(finish_reason, continuation_index, max_continuations):
            if not renderer._last_rendered.endswith("\n"):
                print()
            return renderer.final_answer

        current_messages = current_messages + [
            {"role": "assistant", "content": renderer.final_answer},
            {"role": "user", "content": "继续"},
        ]

    if not renderer._last_rendered.endswith("\n"):
        print()
    return renderer.final_answer


def main() -> int:
    args = build_parser().parse_args()
    model_name = resolve_chat_model(args.model, args.base_url, args.api_key)
    messages = [{"role": "system", "content": args.system}]

    print(f"Connected to {args.base_url.rstrip('/')}")
    print(f"Using model: {model_name}")
    print("Type 'exit' or 'quit' to stop.")

    while True:
        try:
            user_input = input("You> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return 0

        if not user_input:
            continue
        if user_input.lower() in {"exit", "quit"}:
            return 0

        messages.append({"role": "user", "content": user_input})
        try:
            print("Bot> ", end="", flush=True)
            answer = request_streaming_turn(
                args.base_url,
                args.api_key,
                model_name,
                messages,
                args.temperature,
                args.max_tokens,
                args.show_thinking,
                args.max_continuations,
                not args.no_thinking,
            )
        except urllib.error.HTTPError as error:
            detail = error.read().decode("utf-8", errors="replace")
            print(f"Request failed: HTTP {error.code} {detail}", file=sys.stderr)
            messages.pop()
            continue
        except urllib.error.URLError as error:
            print(f"Request failed: {error.reason}", file=sys.stderr)
            messages.pop()
            continue
        except Exception as error:
            print(f"Request failed: {error}", file=sys.stderr)
            messages.pop()
            continue

        if not answer:
            print("Bot> ", flush=True)
        messages.append({"role": "assistant", "content": answer})


if __name__ == "__main__":
    raise SystemExit(main())
