import json
import unittest

import test_pipeline as fixtures
from test_pipeline import Runner, response
import pipeline
from response_protocol import Generation


class EngineDeadError(Exception):
    pass


class FatalRunner(Runner):
    def chat(self, messages, mode="primary"):
        if mode != "primary":
            raise EngineDeadError("synthetic fatal recovery")
        return [Generation(text=response() if m[0]["content"] != "bad" else "", finish_reason="stop") for m in messages]


class FatalRecoveryTests(unittest.TestCase):
    setUp = fixtures.PipelineTests.setUp
    tearDown = fixtures.PipelineTests.tearDown
    run_pipeline = fixtures.PipelineTests.run_pipeline
    def test_successes_saved_before_fatal_recovery(self):
        with self.assertRaises(RuntimeError):
            self.run_pipeline(FatalRunner(), chunk=3)
        checkpoint = json.loads((self.out / "mock_checkpoint.json").read_text())
        self.assertEqual([r["id"] for r in checkpoint["rows"]], ["good", "later"])
        runner = Runner()
        result = self.run_pipeline(runner, resume=True, chunk=3)
        self.assertEqual(result["resumed_records"], 2)
        self.assertEqual(runner.calls, [("primary", 1)])


if __name__ == "__main__":
    unittest.main()
