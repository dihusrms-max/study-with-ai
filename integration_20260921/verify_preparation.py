"""Reproduce ZIP integrity, syntax, and identical-input mock checks (no API/GPU)."""
from pathlib import Path
from datetime import datetime
import csv
import gzip
import hashlib
import io
import json
import os
import subprocess
import sys
import unicodedata
import zipfile

ROOT = Path(__file__).resolve().parent
WORKSPACE = ROOT.parent


def main():
    run_dir = ROOT / "validation" / datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    run_dir.mkdir(parents=True)
    assets = run_dir / "data"
    assets.mkdir()
    inventory = json.loads((ROOT / "comparison/inventory.json").read_text(encoding="utf-8"))
    report = {"scope": "mock plumbing only; no accuracy or GPU validation", "integrity": {}, "runs": {}}
    for owner, entry in inventory.items():
        archive = ROOT / "originals" / Path(entry["source"]).name
        assert hashlib.sha256(archive.read_bytes()).hexdigest() == entry["sha256"]
        for item in entry["files"]:
            path = ROOT / "sources" / owner / item["path"]
            raw = path.read_bytes()
            assert hashlib.sha256(raw).hexdigest() == item["sha256"], str(path)
            if path.suffix == ".py":
                compile(raw.decode("utf-8-sig"), str(path), "exec")
        report["integrity"][owner] = {"sha256": entry["sha256"], "files": len(entry["files"]), "syntax": "PASS"}
    package = WORKSPACE / "data/open.zip"
    report["assets_archive"] = str(package)
    report["assets_archive_sha256"] = hashlib.sha256(package.read_bytes()).hexdigest()
    with zipfile.ZipFile(package) as archive:
        for item in archive.infolist():
            if not item.filename.startswith("data/") or item.is_dir():
                continue
            if not item.filename.endswith((".json", ".txt", ".csv")):
                continue
            target = (assets / item.filename[len("data/"):]).resolve()
            assert target.is_relative_to(assets.resolve())
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(archive.read(item))
    source = WORKSPACE / "DACON_2026/data/raw/dev.jsonl.gz"
    with gzip.open(source, "rt", encoding="utf-8") as stream:
        records = []
        for line in stream:
            if line.strip():
                records.append(json.loads(line))
            if len(records) == 3:
                break
    assert len(records) == 3
    input_file = assets / "smoke.jsonl"
    input_file.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in records), encoding="utf-8")
    report["input"] = {"source": str(source), "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
                       "ids": [r["id"] for r in records], "sha256": hashlib.sha256(input_file.read_bytes()).hexdigest()}
    env = dict(os.environ)
    for key in list(env):
        if key.startswith("PPS_"):
            env.pop(key)
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    columns = ["id"] + [f"v{i}" for i in range(1, 25)] + [f"e{i}" for i in range(1, 25)]
    for owner in ("mine", "teammate"):
        output = run_dir / owner
        command = [sys.executable, str(ROOT / "sources" / owner / "script.py"), "--mock",
                   "--data-dir", str(assets), "--input", str(input_file), "--output-dir", str(output)]
        result = subprocess.run(command, cwd=ROOT, env=env, capture_output=True, text=True, encoding="utf-8", timeout=180)
        (run_dir / f"{owner}.log").write_text(result.stdout + result.stderr, encoding="utf-8")
        item = report["runs"][owner] = {"exit_code": result.returncode, "command": command}
        if result.returncode:
            item["status"] = "FAIL"
            continue
        csv_path = output / ("submission.csv" if owner == "mine" else "mock_submission.csv")
        raw = csv_path.read_bytes()
        assert not raw.startswith(b"\xef\xbb\xbf")
        reader = csv.DictReader(io.StringIO(raw.decode("utf-8"), newline=""))
        assert reader.fieldnames == columns
        rows = list(reader)
        assert [r["id"] for r in rows] == [r["id"] for r in records]
        for row, rec in zip(rows, records):
            assert set(row) == set(columns)
            docs = [unicodedata.normalize("NFC", d["text"]) for d in rec["docs"]]
            for i in range(1, 25):
                flag, evidence = row[f"v{i}"], row[f"e{i}"]
                assert flag in ("0", "1")
                assert len(evidence) <= 500 and not evidence.startswith(("=", "+", "@"))
                assert not evidence or any(evidence in d for d in docs)
                if flag == "0" or i in {10, 11, 16, 18, 20}:
                    assert evidence == ""
        item.update(status="PASS", rows=len(rows), columns=len(columns),
                    positives=sum(r[f"v{i}"] == "1" for r in rows for i in range(1, 25)))
        if owner == "teammate":
            repeated = subprocess.run(command, cwd=ROOT, env=env, capture_output=True, text=True, encoding="utf-8", timeout=180)
            (run_dir / "teammate_resume.log").write_text(repeated.stdout + repeated.stderr, encoding="utf-8")
            report["teammate_resume_probe"] = {"exit_code": repeated.returncode,
                "non_binary_flag_error": "Non-binary output flag" in repeated.stderr}
    report_path = run_dir / "report.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (ROOT / "validation/latest.json").write_text(json.dumps({"report": str(report_path)}, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if all(r["status"] == "PASS" for r in report["runs"].values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
