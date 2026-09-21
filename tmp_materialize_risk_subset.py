#!/usr/bin/env python3
"""Materialize a human-review subset from the integrated risk queue."""

from __future__ import annotations

import argparse
import csv
import gzip
import json
from pathlib import Path


def load_records(path: Path) -> dict[str, dict]:
    with gzip.open(path, "rt", encoding="utf-8") as handle:
        return {row["id"]: row for row in map(json.loads, handle)}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dev", type=Path, required=True)
    parser.add_argument("--labels", type=Path, required=True)
    parser.add_argument("--queue", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    records = load_records(args.dev)
    with args.labels.open("r", encoding="utf-8-sig", newline="") as handle:
        labels = {row["id"]: row for row in csv.DictReader(handle)}
    queue = json.loads(args.queue.read_text(encoding="utf-8"))
    items = []
    for item in queue["items"]:
        if item["priority"] != 1:
            continue
        label = labels.get(item["document_id"], {})
        record = records.get(item["document_id"], {})
        item_name = item["item"]
        items.append({
            **item,
            "current_label": label.get(item_name, ""),
            "current_evidence": label.get(item_name.replace("v", "e"), ""),
            "document_text": "\n".join(str(doc.get("text", "")) for doc in record.get("docs", [])),
            "rubric_version": "43-items-v1",
            "review_status": "PENDING_HUMAN_REVIEW",
            "auto_apply": False,
        })
    payload = {
        "manifest_type": "high_risk_semantic_review_subset",
        "source_queue": str(args.queue),
        "source_dev": str(args.dev),
        "source_labels": str(args.labels),
        "subset_count": len(items),
        "auto_apply": False,
        "items": items,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"subset_count": len(items), "auto_apply": False}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
