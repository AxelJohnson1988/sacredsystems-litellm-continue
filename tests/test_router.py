import unittest

from ssa_gateway.router import CloudDisabledError, GatewayRouter, InferenceResult
from ssa_gateway.routes import DEFAULT_BACKENDS, TASK_ROUTES


class RouterTests(unittest.TestCase):
    def test_chat_prefers_ollama(self):
        router = GatewayRouter(allow_cloud=False)
        decision = router.decide("chat")
        self.assertEqual(decision.backend_name, "ollama_chat")
        self.assertEqual(decision.backend_kind, "ollama")
        self.assertFalse(decision.cloud_allowed)

    def test_code_prefers_coder_model(self):
        decision = GatewayRouter(allow_cloud=False).decide("code")
        self.assertEqual(decision.model, "qwen2.5-coder:7b")

    def test_long_context_prefers_vllm(self):
        decision = GatewayRouter(allow_cloud=False).decide("long_context")
        self.assertEqual(decision.backend_name, "vllm")

    def test_cloud_skipped_when_disabled(self):
        routes = {"chat": ("cloud",)}
        router = GatewayRouter(routes=routes, allow_cloud=False)
        with self.assertRaises(CloudDisabledError):
            router.decide("chat")

    def test_cloud_used_when_enabled(self):
        routes = {"chat": ("cloud",)}
        decision = GatewayRouter(routes=routes, allow_cloud=True).decide("chat")
        self.assertEqual(decision.backend_kind, "cloud")

    def test_chat_does_not_claim_receipt(self):
        def fake_http(url, payload, headers, timeout_s):
            self.assertTrue(url.endswith("/chat/completions"))
            return {"choices": [{"message": {"content": "hello"}}]}

        router = GatewayRouter(http_post=fake_http, allow_cloud=False)
        result = router.chat([{"role": "user", "content": "hi"}])
        self.assertIsInstance(result, InferenceResult)
        self.assertFalse(result.is_receipt)
        self.assertEqual(result.content, "hello")
        self.assertNotIn("event_hash", result.raw)

    def test_unknown_task_class_rejected(self):
        with self.assertRaises(ValueError):
            GatewayRouter().decide("commit_state")

    def test_route_table_never_points_embed_at_cloud(self):
        self.assertNotIn("cloud", TASK_ROUTES["embed"])
        self.assertIn("ollama_embed", DEFAULT_BACKENDS)


if __name__ == "__main__":
    unittest.main()
