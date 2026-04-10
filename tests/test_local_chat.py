import unittest

from local_chat import StreamRenderer, resolve_chat_model, should_auto_continue


class LocalChatTests(unittest.TestCase):
    def test_resolve_chat_model_prefers_explicit_model(self) -> None:
        model_name = resolve_chat_model(
            "custom-model",
            "http://127.0.0.1:8000/v1",
            "EMPTY",
            fetch_remote_models=lambda base_url, api_key: ["server-model"],
        )

        self.assertEqual(model_name, "custom-model")

    def test_resolve_chat_model_uses_remote_model_when_available(self) -> None:
        model_name = resolve_chat_model(
            None,
            "http://127.0.0.1:8000/v1",
            "EMPTY",
            fetch_remote_models=lambda base_url, api_key: [
                "Qwen3.5-35B-A3B-GPTQ-Int4",
            ],
        )

        self.assertEqual(model_name, "Qwen3.5-35B-A3B-GPTQ-Int4")

    def test_resolve_chat_model_falls_back_to_local_default(self) -> None:
        model_name = resolve_chat_model(
            None,
            "http://127.0.0.1:8000/v1",
            "EMPTY",
            fetch_remote_models=lambda base_url, api_key: (_ for _ in ()).throw(
                RuntimeError("server offline")
            ),
            resolve_local_model=lambda model_name: ("Qwen3.5-0.8B", "/tmp/model"),
        )

        self.assertEqual(model_name, "Qwen3.5-0.8B")

    def test_stream_renderer_hides_thinking_and_keeps_final_answer(self) -> None:
        renderer = StreamRenderer(show_thinking=False)

        first = renderer.feed("<think>\n先分析问题")
        second = renderer.feed("\n再整理答案</think>\n\n最终回答")

        self.assertEqual(first, "")
        self.assertEqual(second, "最终回答")
        self.assertEqual(renderer.final_answer, "最终回答")

    def test_stream_renderer_shows_thinking_when_enabled(self) -> None:
        renderer = StreamRenderer(show_thinking=True)

        output = renderer.feed("<think>\n先分析</think>\n\n最终回答")

        self.assertEqual(output, "[thinking]\n先分析[/thinking]\n\n最终回答")
        self.assertEqual(renderer.final_answer, "最终回答")

    def test_should_auto_continue_only_on_length_finish_reason(self) -> None:
        self.assertTrue(should_auto_continue("length", 0, 2))
        self.assertFalse(should_auto_continue("stop", 0, 2))
        self.assertFalse(should_auto_continue("length", 2, 2))


if __name__ == "__main__":
    unittest.main()
