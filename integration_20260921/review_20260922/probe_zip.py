"""Read-only review of the delivered ZIP; creates isolated diagnostic outputs."""
from pathlib import Path
from datetime import datetime
import csv
import gzip
import hashlib
import json
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
OUT = Path(__file__).resolve().parent / datetime.now().strftime("%H%M%S_%f")
OUT.mkdir()
archive_path = ROOT / "dist/submit_integrated_v1_candidate_20260921.zip"
with zipfile.ZipFile(archive_path) as archive:
    for name in archive.namelist():
        assert (OUT / "runtime" / name).resolve().is_relative_to((OUT / "runtime").resolve())
    archive.extractall(OUT / "runtime")
sys.path.insert(0, str(OUT / "runtime"))
import baseline_core as baseline
import retrieval_core as core
import pipeline
from response_protocol import Generation


class Builder:
    def build(self, rec, runner, max_tokens, mode="primary"):
        return [{"role": "user", "content": rec["id"]}], {"tokens": 1}


class EngineDeadError(Exception):
    pass


class FatalRecoveryRunner:
    is_mock = True
    load_seconds = 0
    def chat(self, messages, mode="primary"):
        if mode != "primary":
            raise EngineDeadError("simulated engine termination")
        zero = baseline.MockRunner({})._one([])
        return [Generation(text=zero if m[0]["content"] == "good" else "", finish_reason="stop") for m in messages]


class RecoveryWithoutEvidenceRunner:
    is_mock = True
    load_seconds = 0
    def chat(self, messages, mode="primary"):
        value = "" if mode == "primary" else json.dumps({f"v{i}": int(i == 1) for i in range(1, 25)})
        return [Generation(text=value, finish_reason="stop") for _ in messages]


records = [{"id": name, "meta": {}, "docs": [{"doc_id": "d", "type": "notice", "text": "Evidence text."}]} for name in ("good", "bad")]
identity = {"sha256": "review-only", "description": {"settings": {"mock": True}}}
result = {"zip_sha256": hashlib.sha256(archive_path.read_bytes()).hexdigest()}
for skip in (False, True):
    directory = OUT / f"fatal_skip_{skip}"
    try:
        pipeline.run(records, Builder(), FatalRecoveryRunner(), directory, identity, skip_failures=skip)
    except RuntimeError as exc:
        checkpoint = json.loads((directory / "mock_checkpoint.json").read_text())
        result[f"fatal_skip_{skip}"] = {"error": str(exc), "primary_successes": 1,
                                          "checkpoint_rows": len(checkpoint["rows"])}
directory = OUT / "no_evidence"
report = pipeline.run(records, Builder(), RecoveryWithoutEvidenceRunner(), directory, identity)
with (directory / "mock_submission.csv").open(newline="", encoding="utf-8") as stream:
    rows = list(csv.DictReader(stream))
result["evidence_free_recovery"] = {"format_validation": report["format_validation"],
    "retry_records": report["retry_records"], "positive_items_without_quote": report["positive_items_without_quote"],
    "first_v1": rows[0]["v1"], "first_e1": rows[0]["e1"]}
resumed = pipeline.run(records, Builder(), RecoveryWithoutEvidenceRunner(), directory, identity, resume=True)
result["resume_report"] = {"retry_records_before": report["retry_records"], "retry_records_after": resumed["retry_records"],
                           "resumed_records": resumed["resumed_records"]}
latest = json.loads((ROOT / "validation/latest.json").read_text())
assets = Path(latest["report"]).parent / "data"
builder = core.PromptBuilder(assets)
source = ROOT.parent / "DACON_2026/data/raw/dev.jsonl.gz"
real = list(baseline.iter_records(str(source)))
forced_zeros, forced_ones, v24_forced_zeros = {}, {}, 0
for rec in real:
    facts, corrections = builder.support.analyze(rec)
    for item, correction in corrections.items():
        counts = forced_ones if correction["value"] else forced_zeros
        counts[f"v{item}"] = counts.get(f"v{item}", 0) + 1
        if item == 24 and correction["value"] == 0:
            v24_forced_zeros += 1
result["rule_candidates_on_dev200"] = {"positive_candidates": forced_ones, "negative_candidates": forced_zeros,
                                        "v24_force_zero_records": v24_forced_zeros,
                                        "note": "rule actions only, not model predictions or accuracy"}
path = OUT / "results.json"
path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
(OUT.parent / "latest.json").write_text(json.dumps({"results": str(path)}, indent=2), encoding="utf-8")
print(json.dumps(result, ensure_ascii=False, indent=2))
