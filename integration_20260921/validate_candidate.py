"""Run unit tests and all local development records through three mock variants."""
from datetime import datetime
from pathlib import Path
import csv
import gzip
import hashlib
import io
import json
import os
import subprocess
import sys
import unicodedata

ROOT = Path(__file__).resolve().parent


def check_csv(path, records):
    raw = path.read_bytes()
    assert not raw.startswith(b"\xef\xbb\xbf")
    reader = csv.DictReader(io.StringIO(raw.decode("utf-8"), newline=""))
    fields = ["id"] + [f"v{i}" for i in range(1, 25)] + [f"e{i}" for i in range(1, 25)]
    assert reader.fieldnames == fields
    rows = list(reader)
    assert [r["id"] for r in rows] == [r["id"] for r in records]
    assert len({r["id"] for r in rows}) == len(rows)
    positives = 0
    for row, rec in zip(rows, records):
        assert set(row) == set(fields)
        docs = [unicodedata.normalize("NFC", d["text"]) for d in rec["docs"]]
        for i in range(1, 25):
            flag, ev = row[f"v{i}"], row[f"e{i}"]
            assert flag in {"0", "1"}
            assert isinstance(ev, str) and len(ev) <= 500 and unicodedata.normalize("NFC", ev) == ev
            assert not ev.startswith(("=", "+", "@"))
            assert not ev or any(ev in doc for doc in docs)
            if flag == "0" or i in {10, 11, 16, 18, 20}:
                assert not ev
            positives += flag == "1"
    return {"rows": len(rows), "columns": len(fields), "positives": positives, "format": "PASS"}


def main():
    latest = json.loads((ROOT / "validation/latest.json").read_text())
    assets = Path(latest["report"]).parent / "data"
    source = ROOT.parent / "DACON_2026/data/raw/dev.jsonl.gz"
    with gzip.open(source, "rt", encoding="utf-8") as stream:
        records = [json.loads(line) for line in stream if line.strip()]
    out = ROOT / "validation" / ("candidate_" + datetime.now().strftime("%Y%m%d_%H%M%S_%f"))
    out.mkdir(parents=True)
    env = {k: v for k, v in os.environ.items() if not k.startswith("PPS_")}
    env.update(PYTHONIOENCODING="utf-8", PYTHONDONTWRITEBYTECODE="1")
    tests = subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", str(ROOT / "tests"), "-v"],
                           env=env, capture_output=True, text=True, encoding="utf-8", timeout=120)
    (out / "unit_tests.log").write_text(tests.stdout + tests.stderr, encoding="utf-8")
    assert tests.returncode == 0, tests.stderr
    summary = {"scope": "mock plumbing; not accuracy, throughput, or GPU validation",
               "unit_tests": "PASS", "input_sha256": hashlib.sha256(source.read_bytes()).hexdigest(), "variants": {}}
    for name, options in (("C_baseline", ["--pipeline", "baseline"]),
                          ("D_retrieval", ["--pipeline", "retrieval"]),
                          ("E_rules", ["--pipeline", "retrieval", "--rule-corrections"])):
        command = [sys.executable, str(ROOT / "candidate/script.py"), "--mock", "--data-dir", str(assets),
                   "--input", str(source), "--output-dir", str(out / name), *options]
        completed = subprocess.run(command, env=env, capture_output=True, text=True, encoding="utf-8", timeout=300)
        (out / f"{name}.log").write_text(completed.stdout + completed.stderr, encoding="utf-8")
        assert completed.returncode == 0, completed.stderr
        results = check_csv(out / name / "mock_submission.csv", records)
        initial_bytes = (out / name / "mock_submission.csv").read_bytes()
        resumed = subprocess.run(command + ["--resume"], env=env, capture_output=True, text=True, encoding="utf-8", timeout=300)
        (out / f"{name}_resume.log").write_text(resumed.stdout + resumed.stderr, encoding="utf-8")
        assert resumed.returncode == 0, resumed.stderr
        report = json.loads((out / name / "mock_run_report.json").read_text(encoding="utf-8"))
        assert report["resumed_records"] == len(records)
        assert report["response_diagnostics"] == {}
        assert initial_bytes == (out / name / "mock_submission.csv").read_bytes()
        results.update(resume="PASS", rule_change_count=report["rule_change_count"])
        summary["variants"][name] = results
        print(name, results, flush=True)
    inventory = json.loads((ROOT / "comparison/inventory.json").read_text(encoding="utf-8"))
    for entry in inventory.values():
        assert hashlib.sha256(Path(entry["source"]).read_bytes()).hexdigest() == entry["sha256"]
    summary["originals_unchanged"] = True
    (out / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    (ROOT / "validation/candidate_latest.json").write_text(json.dumps({"summary": str(out / "summary.json")}, indent=2), encoding="utf-8")
    print(out, flush=True)


if __name__ == "__main__":
    main()
