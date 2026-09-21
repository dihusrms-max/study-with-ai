"""Create an allowlisted ZIP; test from an isolated extraction."""
from datetime import datetime
from pathlib import Path
import hashlib
import json
import os
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parent
FILES = ["script.py", "pipeline.py", "baseline_core.py", "retrieval_core.py", "response_protocol.py",
         "decision_support.py", "qualification_support.py", "requirements.txt", "README.md"]


def main():
    source = ROOT / "candidate"
    destination = ROOT / "dist"
    destination.mkdir(exist_ok=True)
    zip_path = destination / "submit_integrated_v1_candidate_20260921.zip"
    if zip_path.exists():
        raise FileExistsError("Candidate ZIP already exists; use a new version for a new build")
    files = {}
    for name in FILES:
        content = (source / name).read_bytes()
        if name.endswith(".py"):
            compile(content.decode("utf-8-sig"), name, "exec")
        files[name] = {"bytes": len(content), "sha256": hashlib.sha256(content).hexdigest()}
    inventory = json.loads((ROOT / "comparison/inventory.json").read_text(encoding="utf-8"))
    manifest = {"status": "CANDIDATE_NOT_ACCURACY_VALIDATED", "files": files,
                "source_zips": {owner: entry["sha256"] for owner, entry in inventory.items()},
                "validation": json.loads((ROOT / "validation/candidate_latest.json").read_text())}
    with zipfile.ZipFile(zip_path, "x", compression=zipfile.ZIP_DEFLATED) as archive:
        for name in FILES:
            archive.write(source / name, name)
    verify_dir = ROOT / "validation" / ("packaged_" + datetime.now().strftime("%Y%m%d_%H%M%S_%f"))
    verify_dir.mkdir(parents=True)
    with zipfile.ZipFile(zip_path) as archive:
        assert archive.testzip() is None
        assert set(archive.namelist()) == set(FILES)
        archive.extractall(verify_dir / "runtime")
        for name in FILES:
            assert hashlib.sha256(archive.read(name)).hexdigest() == files[name]["sha256"]
    latest = json.loads((ROOT / "validation/latest.json").read_text())
    data = Path(latest["report"]).parent / "data"
    env = {k: v for k, v in os.environ.items() if not k.startswith("PPS_")}
    env.update(PYTHONIOENCODING="utf-8", PYTHONDONTWRITEBYTECODE="1")
    command = [sys.executable, "script.py", "--mock", "--data-dir", str(data), "--input", str(data / "smoke.jsonl"),
               "--output-dir", str(verify_dir / "output")]
    for suffix in ([], ["--resume"]):
        result = subprocess.run(command + suffix, cwd=verify_dir / "runtime", env=env,
                                capture_output=True, text=True, encoding="utf-8", timeout=120)
        name = "resume.log" if suffix else "run.log"
        (verify_dir / name).write_text(result.stdout + result.stderr, encoding="utf-8")
        if result.returncode:
            raise RuntimeError(f"Packaged candidate failed validation; see {verify_dir / name}")
    sys.path.insert(0, str(ROOT))
    from validate_candidate import check_csv
    records = [json.loads(line) for line in (data / "smoke.jsonl").read_text(encoding="utf-8").splitlines() if line]
    manifest["package_validation"] = check_csv(verify_dir / "output/mock_submission.csv", records)
    report = json.loads((verify_dir / "output/mock_run_report.json").read_text(encoding="utf-8"))
    assert report["resumed_records"] == len(records)
    assert report["response_diagnostics"] == {}
    manifest["package_validation"].update(isolated_execution="PASS", resume="PASS")
    manifest["zip_sha256"] = hashlib.sha256(zip_path.read_bytes()).hexdigest()
    manifest["zip_bytes"] = zip_path.stat().st_size
    (destination / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"zip": str(zip_path), "sha256": manifest["zip_sha256"],
                      "bytes": manifest["zip_bytes"], "validation": manifest["package_validation"]}, indent=2))


if __name__ == "__main__":
    main()
