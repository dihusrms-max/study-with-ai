from pathlib import Path
import copy
import json
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "candidate_v2"))
import pipeline
import retrieval_core as core
from response_protocol import Generation


def record(name):
    return {"id": name, "meta": {}, "docs": [{"doc_id": "d1", "type": "공고문", "text": "Exact original evidence in this document."}]}


def response(flag=0):
    obj = {f"v{i}": {"위반여부": flag if i == 1 else 0,
                      "근거문구": "Exact original evidence" if flag and i == 1 else None} for i in range(1, 25)}
    return json.dumps(obj, ensure_ascii=False)


IDENTITY = {"sha256": "test-identity", "description": {"settings": {"mock": True}}}


class Builder:
    def build(self, rec, runner, max_tokens, mode="primary"):
        return [{"role": "user", "content": rec["id"]}], {"tokens": 1, "full_document_context": True}


class Runner:
    is_mock = True
    load_seconds = 0.0

    def __init__(self, fail=(), recover=False, batch_error=False):
        self.fail = set(fail)
        self.recover = recover
        self.batch_error = batch_error
        self.calls = []

    def chat(self, messages, mode="primary"):
        self.calls.append((mode, len(messages)))
        if self.batch_error and len(messages) > 1:
            raise RuntimeError("Batch error")
        replies = []
        for message in messages:
            rid = message[0]["content"]
            if rid in self.fail:
                replies.append(Generation(text="", finish_reason="stop"))
            elif self.recover and mode == "primary":
                text = '{"v1":{"위반여부":1,"근거문구":"Exact original evidence"},'
                replies.append(Generation(text=text, finish_reason="length"))
            elif mode == "primary":
                replies.append(Generation(text=response(), finish_reason="stop"))
            else:
                replies.append(Generation(text=json.dumps({f"v{i}": int(i == 1) for i in range(1, 25)}), finish_reason="stop"))
        return replies


class PipelineTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.out = Path(self.temp.name)
        self.records = [record("good"), record("bad"), record("later")]

    def tearDown(self):
        self.temp.cleanup()

    def run_pipeline(self, runner, **kwargs):
        return pipeline.run(self.records, Builder(), runner, self.out, IDENTITY, **kwargs)

    def test_resume_preserves_integer_flags_and_skips_calls(self):
        self.run_pipeline(Runner())
        runner = Runner()
        report = self.run_pipeline(runner, resume=True)
        self.assertEqual(report["resumed_records"], 3)
        self.assertEqual(runner.calls, [])
        self.assertEqual(report["format_validation"], "PASS")

    def test_mixed_batch_saves_successes_and_never_creates_final(self):
        report = self.run_pipeline(Runner(fail={"bad"}), skip_failures=True, chunk=3)
        self.assertEqual(report["records"], 2)
        self.assertEqual(report["failed_ids"], ["bad"])
        self.assertFalse((self.out / "mock_submission.csv").exists())
        self.assertTrue((self.out / "mock_partial_submission.csv").exists())
        runner = Runner()
        result = self.run_pipeline(runner, resume=True, chunk=3)
        self.assertEqual(result["resumed_records"], 2)
        self.assertEqual(runner.calls, [("primary", 1)])
        self.assertFalse((self.out / "mock_partial_submission.csv").exists())

    def test_strict_failure_preserves_success_and_unattempted_ids(self):
        with self.assertRaises(RuntimeError):
            self.run_pipeline(Runner(fail={"bad"}), chunk=2)
        report = json.loads((self.out / "mock_run_report.json").read_text())
        self.assertEqual(report["records"], 1)
        self.assertEqual(report["unattempted_ids"], ["later"])
        self.assertFalse((self.out / "mock_submission.csv").exists())
        result = self.run_pipeline(Runner(), resume=True, chunk=2)
        self.assertEqual(result["records"], 3)

    def test_recovery_uses_only_completed_original_evidence(self):
        result = self.run_pipeline(Runner(recover=True))
        self.assertEqual(result["retry_records"], 3)
        rows, _ = pipeline.load_checkpoint(self.out / "mock_checkpoint.json", IDENTITY, self.records)
        self.assertEqual(rows[0]["e1"], "Exact original evidence")

    def test_batch_exception_splits_and_recovers(self):
        result = self.run_pipeline(Runner(batch_error=True))
        self.assertEqual(result["records"], 3)
        self.assertGreater(result["response_diagnostics"]["engine_RuntimeError"], 0)

    def test_changed_identity_rejected_before_calls(self):
        self.run_pipeline(Runner())
        different = copy.deepcopy(IDENTITY)
        different["sha256"] = "different-input-or-options"
        runner = Runner()
        with self.assertRaisesRegex(ValueError, "changed"):
            pipeline.run(self.records, Builder(), runner, self.out, different, resume=True)
        self.assertEqual(runner.calls, [])

    def test_invalid_checkpoint_flags_rejected(self):
        self.run_pipeline(Runner())
        path = self.out / "mock_checkpoint.json"
        value = json.loads(path.read_text())
        value["rows"][0]["v1"] = "0"
        path.write_text(json.dumps(value))
        with self.assertRaisesRegex(ValueError, "Non-binary"):
            self.run_pipeline(Runner(), resume=True)

    def test_existing_output_requires_explicit_resume(self):
        self.run_pipeline(Runner())
        with self.assertRaises(FileExistsError):
            self.run_pipeline(Runner())

    def test_rule_override_off_by_default_and_audited_when_enabled(self):
        class Support:
            def analyze(self, rec):
                return {}, {1: {"value": 1, "evidence": "Exact original evidence", "reason": "test correction"}}
        builder = Builder()
        builder.support = Support()
        off = self.out / "off"
        on = self.out / "on"
        a = pipeline.run(self.records, builder, Runner(), off, IDENTITY)
        b = pipeline.run(self.records, builder, Runner(), on, IDENTITY, rule_corrections=True)
        self.assertEqual(a["rule_change_count"], 0)
        self.assertEqual(b["rule_change_count"], 3)
        changes = json.loads((on / "mock_rule_changes.json").read_text())
        self.assertEqual(changes[0]["before"]["flag"], 0)
        self.assertEqual(changes[0]["after"]["flag"], 1)

    def test_evidence_cannot_cross_document_boundary(self):
        self.assertEqual(core.exact_evidence("first line\nsecond line", ["first line", "second line"]), "")
        self.assertEqual(core.exact_evidence("exact original evidence", ["exact  original\nevidence"]), "exact  original\nevidence")

    def test_duplicate_json_key_and_boolean_flag_rejected(self):
        text = response()
        with self.assertRaises(ValueError):
            core.parse_response(text.replace('{"v1":', '{"v1":{},"v1":', 1))
        with self.assertRaises(ValueError):
            core.parse_response(text.replace('"위반여부": 0', '"위반여부": false', 1))

    def test_all_failed_creates_no_csv(self):
        result = self.run_pipeline(Runner(fail={r["id"] for r in self.records}), skip_failures=True)
        self.assertEqual(result["records"], 0)
        self.assertEqual(list(self.out.glob("*.csv")), [])


if __name__ == "__main__":
    unittest.main()
