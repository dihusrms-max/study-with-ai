from pathlib import Path
import io
import json
import os
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from run_gemma_pilot import BudgetedAPI


class AdapterTests(unittest.TestCase):
    def test_preserves_length_and_plain_mode_drops_schema(self):
        with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, {"GEMMA_API_KEY": "test-only"}):
            runner = BudgetedAPI(directory=Path(directory), identity={"sha256": "test"}, limit=1,
                timeout=1, api_budget=2, max_runtime=60, max_tokens=1536)
            body = {"choices": [{"message": {"content": "{}"}, "finish_reason": "length"}],
                    "model": "test-model", "usage": {"completion_tokens": 768}}
            with patch("urllib.request.urlopen", return_value=io.BytesIO(json.dumps(body).encode())) as transport:
                result = runner.chat([[{"role": "user", "content": "test"}]], mode="plain")[0]
                payload = json.loads(transport.call_args.args[0].data)
            self.assertEqual(result.finish_reason, "length")
            self.assertEqual(result.generated_tokens, 768)
            self.assertNotIn("response_format", payload)
            self.assertEqual(payload["max_tokens"], 768)
            self.assertEqual(runner.state.api_used, 1)

    def test_request_cap_prevents_network(self):
        with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, {"GEMMA_API_KEY": "test-only"}):
            runner = BudgetedAPI(directory=Path(directory), identity={"sha256": "test"}, limit=1,
                timeout=1, api_budget=0, max_runtime=60, max_tokens=1536)
            with patch("urllib.request.urlopen") as transport:
                result = runner.chat([[{"role": "user", "content": "test"}]])[0]
            self.assertEqual(result.error_code, "api_budget_exceeded")
            transport.assert_not_called()


if __name__ == "__main__":
    unittest.main()
