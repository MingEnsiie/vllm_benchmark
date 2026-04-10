import tempfile
import unittest
from pathlib import Path

from scripts.benchmark_speed import build_prompt_for_target_tokens, collect_stream_metrics
from vllm_local import (
    DEFAULT_MODEL_NAME,
    discover_models,
    resolve_model,
)


class VllmLocalTests(unittest.TestCase):
    def test_discover_models_only_returns_model_dirs_with_weights(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            models_dir = Path(tmp)
            valid_dir = models_dir / "Qwen3.5-0.8B"
            valid_dir.mkdir()
            (valid_dir / "config.json").write_text("{}", encoding="utf-8")
            (valid_dir / "model.safetensors.index.json").write_text(
                "{}",
                encoding="utf-8",
            )

            invalid_dir = models_dir / "notes"
            invalid_dir.mkdir()
            (invalid_dir / "README.md").write_text("not a model", encoding="utf-8")

            discovered = discover_models(models_dir)

            self.assertEqual(list(discovered.keys()), ["Qwen3.5-0.8B"])
            self.assertEqual(discovered["Qwen3.5-0.8B"], valid_dir.resolve())

    def test_resolve_model_uses_requested_model_when_present(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            models_dir = Path(tmp)
            for model_name in ("Qwen3.5-0.8B", "Qwen3.5-4B"):
                model_dir = models_dir / model_name
                model_dir.mkdir()
                (model_dir / "config.json").write_text("{}", encoding="utf-8")
                (model_dir / "model.safetensors-00001-of-00001.safetensors").write_text(
                    "stub",
                    encoding="utf-8",
                )

            selected_name, selected_path = resolve_model("Qwen3.5-4B", models_dir)

            self.assertEqual(selected_name, "Qwen3.5-4B")
            self.assertEqual(selected_path, (models_dir / "Qwen3.5-4B").resolve())

    def test_resolve_model_falls_back_to_default_model(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            models_dir = Path(tmp)
            model_dir = models_dir / DEFAULT_MODEL_NAME
            model_dir.mkdir()
            (model_dir / "config.json").write_text("{}", encoding="utf-8")
            (model_dir / "model.safetensors.index.json").write_text(
                "{}",
                encoding="utf-8",
            )

            selected_name, selected_path = resolve_model(None, models_dir)

            self.assertEqual(selected_name, DEFAULT_MODEL_NAME)
            self.assertEqual(selected_path, model_dir.resolve())

    def test_resolve_model_raises_for_unknown_model(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            models_dir = Path(tmp)
            model_dir = models_dir / DEFAULT_MODEL_NAME
            model_dir.mkdir()
            (model_dir / "config.json").write_text("{}", encoding="utf-8")
            (model_dir / "model.safetensors.index.json").write_text(
                "{}",
                encoding="utf-8",
            )

            with self.assertRaisesRegex(ValueError, "Unknown model"):
                resolve_model("missing-model", models_dir)

    def test_collect_stream_metrics_tracks_first_token_latency_and_output(self) -> None:
        chunks = [
            {"delta": "", "prompt_tokens": 12, "completion_tokens": 0, "wait": 0.15},
            {"delta": "你", "prompt_tokens": 12, "completion_tokens": 1, "wait": 0.30},
            {"delta": "好", "prompt_tokens": 12, "completion_tokens": 2, "wait": 0.10},
        ]

        metrics = collect_stream_metrics(chunks)

        self.assertEqual(metrics["prompt_tokens"], 12)
        self.assertEqual(metrics["completion_tokens"], 2)
        self.assertAlmostEqual(metrics["first_token_latency"], 0.45, places=2)
        self.assertAlmostEqual(metrics["elapsed"], 0.55, places=2)

    def test_collect_stream_metrics_handles_empty_generation(self) -> None:
        chunks = [
            {"delta": "", "prompt_tokens": 8, "completion_tokens": 0, "wait": 0.20},
            {"delta": "", "prompt_tokens": 8, "completion_tokens": 0, "wait": 0.10},
        ]

        metrics = collect_stream_metrics(chunks)

        self.assertIsNone(metrics["first_token_latency"])
        self.assertEqual(metrics["completion_tokens"], 0)
        self.assertAlmostEqual(metrics["elapsed"], 0.30, places=2)

    def test_build_prompt_for_target_tokens_reaches_requested_size(self) -> None:
        class FakeTokenizer:
            def encode(self, text: str, add_special_tokens: bool = False) -> list[int]:
                return [token for token in text.split(" ") if token]

        prompt = build_prompt_for_target_tokens(FakeTokenizer(), 10)

        self.assertGreaterEqual(len(prompt.split()), 10)
        self.assertLessEqual(len(prompt.split()), 10)


if __name__ == "__main__":
    unittest.main()
