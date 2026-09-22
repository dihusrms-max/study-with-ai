"""Summarize pilot reliability and existing local label metrics, without API calls."""
from pathlib import Path
import csv
import hashlib
import importlib.util
import json
import statistics
import sys

ROOT = Path(__file__).resolve().parent
PROJECT = ROOT.parent / "DACON_2026"


def main():
    location = json.loads((ROOT / "validation/gemma_pilot_latest.json").read_text())
    summary_path = Path(location["summary"])
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    directory = summary_path.parent
    source_path = PROJECT / "data/raw/dev.jsonl.gz"
    labels_path = PROJECT / "data/raw/dev_labels.csv"
    spec = importlib.util.spec_from_file_location("existing_dev_metrics", PROJECT / "scripts/evaluate_dev200_run.py")
    evaluator = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(evaluator)
    labels = evaluator.read(labels_path)
    output = directory / "submission.csv"
    if not output.exists():
        output = directory / "partial_submission.csv"
    predictions = evaluator.read(output) if output.exists() else {}
    ids = list(predictions)
    assert all(rid in labels for rid in ids)
    per_item = evaluator.metrics(labels, predictions, ids)
    counts = {key: sum(item[key] for item in per_item.values()) for key in ("tp", "fp", "tn", "fn")}
    positives = [(rid, f"v{i}", predictions[rid][f"e{i}"]) for rid in ids for i in range(1, 25)
                 if predictions[rid][f"v{i}"] == "1"]
    evidence_required = [p for p in positives if int(p[1][1:]) not in {10, 11, 16, 18, 20}]
    missing_evidence = [{"id": rid, "item": item} for rid, item, ev in evidence_required if not ev.strip()]
    disagreements = [{"id": rid, "item": f"v{i}", "label": int(labels[rid][f"v{i}"]),
                      "prediction": int(predictions[rid][f"v{i}"])} for rid in ids for i in range(1, 25)
                     if labels[rid][f"v{i}"] != predictions[rid][f"v{i}"]]
    calls = summary["calls"]
    actual = [c for c in calls if c.get("http_status") == 200]
    latencies = [c["latency_seconds"] for c in calls if "latency_seconds" in c]
    usage = {key: sum(c.get("usage", {}).get(key, 0) or 0 for c in actual)
             for key in ("prompt_tokens", "completion_tokens", "total_tokens")}
    verification = None
    if ids:
        sys.path.insert(0, str(ROOT))
        sys.path.insert(0, str(ROOT / "candidate_v2"))
        from validate_candidate import check_csv
        import baseline_core as baseline
        records_by_id = {r["id"]: r for r in baseline.iter_records(str(source_path))}
        verification = check_csv(output, [records_by_id[rid] for rid in ids])
    result = {"scope": "First development records only; diagnostic, not a baseline comparison or official score",
        "records": len(ids), "requested_records": summary["requested_records"], "ids": ids,
        "labels_path": str(labels_path), "labels_sha256": hashlib.sha256(labels_path.read_bytes()).hexdigest(),
        "source_sha256": hashlib.sha256(source_path.read_bytes()).hexdigest(),
        "api_used": summary["api_used"], "api_budget": summary["api_budget"],
        "elapsed_seconds": summary["elapsed_seconds"], "request_usage": usage,
        "request_latency_mean": statistics.mean(latencies) if latencies else None,
        "request_latency_median": statistics.median(latencies) if latencies else None,
        "max_actual_prompt_tokens": max((c.get("usage", {}).get("prompt_tokens", 0) or 0 for c in actual), default=0),
        "returned_models": sorted({c["model"] for c in actual if c.get("model")}),
        "http_errors": [c.get("error_code") for c in calls if c.get("error_code")],
        "output_validation": verification, "per_item": per_item,
        "counts": counts, "macro_f1_local_all24": sum(v["f1"] for v in per_item.values()) / 24,
        "nonabsence_positives": len(evidence_required), "missing_evidence": missing_evidence,
        "disagreements": disagreements, "candidate_report": summary["report"]}
    pipeline_path = directory / "evaluation.json"
    pipeline_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: result[k] for k in ("records", "requested_records", "api_used", "elapsed_seconds",
        "returned_models", "counts", "macro_f1_local_all24", "nonabsence_positives", "missing_evidence", "disagreements")}, ensure_ascii=False, indent=2))
    print('REPORT',pipeline_path)


if __name__ == "__main__":
    main()
