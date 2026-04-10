"""Local helpers for vLLM setup and model selection."""

from __future__ import annotations

import argparse
from pathlib import Path

DEFAULT_MODEL_NAME = "Qwen3.5-0.8B"
REQUIRED_CONFIG_FILES = ("config.json",)
WEIGHT_FILE_MARKERS = (
    "model.safetensors",
    "model.safetensors.index.json",
)


def _looks_like_model_dir(model_dir: Path) -> bool:
    if not model_dir.is_dir():
        return False
    if not all((model_dir / name).exists() for name in REQUIRED_CONFIG_FILES):
        return False
    return any((model_dir / name).exists() for name in WEIGHT_FILE_MARKERS) or any(
        model_dir.glob("model.safetensors-*.safetensors")
    )


def discover_models(models_dir: Path | None = None) -> dict[str, Path]:
    root = (models_dir or Path(__file__).resolve().parent / "models").resolve()
    if not root.exists():
        return {}

    discovered: dict[str, Path] = {}
    for child in sorted(root.iterdir(), key=lambda item: item.name.lower()):
        if _looks_like_model_dir(child):
            discovered[child.name] = child.resolve()
    return discovered


def resolve_model(
    model_name: str | None,
    models_dir: Path | None = None,
) -> tuple[str, Path]:
    discovered = discover_models(models_dir)
    if not discovered:
        raise ValueError("No local models found under the models directory")

    selected_name = model_name or (
        DEFAULT_MODEL_NAME if DEFAULT_MODEL_NAME in discovered else next(iter(discovered))
    )
    if selected_name not in discovered:
        available = ", ".join(discovered)
        raise ValueError(f"Unknown model: {selected_name}. Available models: {available}")
    return selected_name, discovered[selected_name]


def served_model_name(model_name: str) -> str:
    return model_name


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Local vLLM model helpers")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("list", help="List available local models")

    resolve_parser = subparsers.add_parser("resolve", help="Resolve a local model")
    resolve_parser.add_argument("--model", help="Model directory name under models/")
    resolve_parser.add_argument(
        "--field",
        choices=("name", "path", "served-name"),
        default="path",
        help="Field to print",
    )
    return parser


def main() -> int:
    parser = _build_parser()
    args = parser.parse_args()

    if args.command == "list":
        for model_name in discover_models():
            print(model_name)
        return 0

    if args.command == "resolve":
        model_name, model_path = resolve_model(args.model)
        if args.field == "name":
            print(model_name)
        elif args.field == "served-name":
            print(served_model_name(model_name))
        else:
            print(model_path)
        return 0

    parser.error(f"Unsupported command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
