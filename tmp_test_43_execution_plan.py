import csv
import gzip
import json

from scripts.implement_43_execution_plan import build_risk_queue, build_tasks, contract_summary


def test_execution_plan_contract_counts_missing_evidence(tmp_path):
    dev = tmp_path / "dev.jsonl.gz"
    labels = tmp_path / "labels.csv"
    with gzip.open(dev, "wt", encoding="utf-8") as handle:
        handle.write(json.dumps({"id": "d1", "docs": [{"text": "direct evidence"}]}) + "\n")
    with labels.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["id", "v1", "e1", "v10", "e10"])
        writer.writeheader()
        writer.writerow({"id": "d1", "v1": "1", "e1": "", "v10": "1", "e10": ""})
    result = contract_summary(dev, labels)
    assert result["positive_without_evidence_count"] == 1
    assert result["error_count"] == 1


def test_execution_plan_tasks_and_risk_queue_are_deduplicated(tmp_path):
    dev = tmp_path / "dev.jsonl.gz"
    labels = tmp_path / "labels.csv"
    review = tmp_path / "review.csv"
    with gzip.open(dev, "wt", encoding="utf-8") as handle:
        handle.write(json.dumps({"id": "d1", "docs": [{"text": "source"}]}) + "\n")
    with labels.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["id", "v8", "e8"])
        writer.writeheader()
        writer.writerow({"id": "d1", "v8": "1", "e8": ""})
    with review.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["ID", "항목", "현재_판정", "현재_evidence", "오류_사유", "원문"])
        writer.writeheader()
        row = {"ID": "d1", "항목": "v8", "현재_판정": "1", "현재_evidence": "", "오류_사유": "x", "원문": "source"}
        writer.writerow(row)
        writer.writerow(row)
    tasks = build_tasks(review, dev, labels, tmp_path / "tasks.json", "v1")
    assert tasks["task_count"] == 1
    queue = build_risk_queue(dev, labels, tmp_path / "tasks.json", tmp_path / "queue.json")
    assert queue["queue_count"] == 1
    assert "review_43" in queue["items"][0]["reasons"]
