"""Shared strict inference and typed, identity-checked recovery state."""
from __future__ import annotations

import hashlib
import json
import time
from collections import Counter
from pathlib import Path

import baseline_core as baseline
import retrieval_core as core
from response_protocol import COMPACT_OUTPUT, COMPACT_TOKENS, ResponseError, completed_quotes, infer_batch, read_decision


class BaselineBuilder:
    """Keep the user's prompt and document selection, with a strict token cap."""

    def __init__(self, data_dir, doc_chars=4000):
        self.system = baseline.build_system_prompt(baseline.item_table(str(data_dir)))
        self.doc_chars = doc_chars

    def build(self, rec, runner, max_tokens, mode="primary"):
        system = self.system
        if mode != "primary":
            system = system.replace(baseline.SYSTEM_TAIL, "\n" + COMPACT_OUTPUT)
        chars = self.doc_chars
        budget = core.MAX_MODEL_LEN - max_tokens - 256
        while True:
            messages = baseline.build_messages(rec, system, chars)
            tokens = runner.count_tokens(messages)
            if tokens <= budget:
                return messages, {"tokens": tokens, "full_document_context": False}
            if chars <= 256:
                raise ValueError("Baseline prompt exceeds context budget")
            chars = max(256, int(chars * min(0.8, budget / tokens * 0.93)))


def atomic_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def digest(value):
    data = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


def make_identity(records, settings, data_dir):
    root = Path(__file__).resolve().parent
    code = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(root.glob("*.py"))}
    data_dir = Path(data_dir)
    assets = {}
    paths = [core.resolve_child(data_dir, "항목표.json")]
    if settings["pipeline"] == "retrieval":
        package = core.resolve_child(data_dir, "법령패키지")
        paths += [p for p in package.rglob("*") if p.is_file() and p.suffix in {".txt", ".csv"}]
    for path in paths:
        assets[str(path.relative_to(data_dir))] = hashlib.sha256(path.read_bytes()).hexdigest()
    description = {"input_sha256": digest(records), "settings": settings, "code": code, "assets": assets}
    return {"sha256": digest(description), "description": description}


def load_checkpoint(path, identity, records):
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if payload.get("version") != 1 or payload.get("identity") != identity:
        raise ValueError("Checkpoint input, code, assets, or inference settings changed")
    rows = payload["rows"]
    lookup = {rec["id"]: rec for rec in records}
    if any(row["id"] not in lookup for row in rows):
        raise ValueError("Checkpoint contains an unknown input ID")
    core.validate_rows(rows, [lookup[row["id"]] for row in rows])
    return rows, payload.get("rule_changes", [])


def apply_corrections(rec, row, support):
    _, corrections = support.analyze(rec)
    changes = []
    for item, change in sorted(corrections.items()):
        flag, evidence = f"v{item}", f"e{item}"
        old = {"flag": row[flag], "evidence": row[evidence]}
        quote = "" if change["value"] == 0 or item in core.ABSENCE else change["evidence"]
        new = {"flag": change["value"], "evidence": quote}
        if old != new:
            changes.append({"id": rec["id"], "item": flag, "before": old, "after": new,
                            "reason": change.get("reason", "")})
        row[flag], row[evidence] = new["flag"], new["evidence"]
    return row, changes


def run(records, builder, runner, output_dir, identity, *, chunk=128, max_tokens=1536,
        resume=False, skip_failures=False, rule_corrections=False):
    if not records or chunk < 1 or max_tokens < 1:
        raise ValueError("Nonempty input and positive chunk/token budgets are required")
    if len({r["id"] for r in records}) != len(records):
        raise ValueError("Duplicate input ID")
    if rule_corrections and not hasattr(builder, "support"):
        raise ValueError("Rule corrections require the retrieval pipeline")
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    prefix = "mock_" if runner.is_mock else ""
    final_path = output_dir / f"{prefix}submission.csv"
    checkpoint = output_dir / f"{prefix}checkpoint.json"
    report_path = output_dir / f"{prefix}run_report.json"
    audit_path = output_dir / f"{prefix}rule_changes.json"
    partial_path = output_dir / f"{prefix}partial_submission.csv"
    failures_path = output_dir / f"{prefix}failures.json"
    if resume:
        rows, changes = load_checkpoint(checkpoint, identity, records)
    else:
        if any(p.exists() for p in (final_path, checkpoint, report_path, partial_path, audit_path, failures_path)):
            raise FileExistsError("Output already exists; use --resume or a new --output-dir")
        rows, changes = [], []
    resumed = len(rows)
    by_id = {row["id"]: row for row in rows}
    pending_records = [r for r in records if r["id"] not in by_id]
    counts, failures, token_counts = Counter(), [], []
    start = time.monotonic()
    recovered = 0

    def save():
        ordered = [by_id[r["id"]] for r in records if r["id"] in by_id]
        core.validate_rows(ordered, [r for r in records if r["id"] in by_id])
        atomic_json(checkpoint, {"version": 1, "identity": identity, "rows": ordered, "rule_changes": changes})
        return ordered

    # Establish resumable identity even if the first request fails.
    save()
    for begin in range(0, len(pending_records), chunk):
        batch = pending_records[begin:begin + chunk]
        decisions = [None] * len(batch)
        quotes = [{} for _ in batch]
        pending = list(range(len(batch)))
        for mode, budget in (("primary", max_tokens), ("compact", COMPACT_TOKENS), ("plain", COMPACT_TOKENS)):
            if not pending:
                break
            prepared = []
            for idx in pending:
                messages, info = builder.build(batch[idx], runner, budget, mode=mode)
                prepared.append(messages)
                token_counts.append(info["tokens"])
            replies = infer_batch(runner, prepared, mode, counts)
            retry = []
            for idx, reply in zip(pending, replies):
                if mode == "primary":
                    quotes[idx] = completed_quotes(reply.text)
                try:
                    obj = read_decision(reply, mode, core.parse_response)
                except ResponseError as exc:
                    counts[str(exc)] += 1
                    retry.append(idx)
                    continue
                if mode != "primary":
                    obj["e"].update(quotes[idx])
                    recovered += 1
                decisions[idx] = obj
                rec = batch[idx]
                row = core.make_row(rec, obj)
                edits = []
                if rule_corrections:
                    row, edits = apply_corrections(rec, row, builder.support)
                core.validate_rows([row], [rec])
                by_id[rec["id"]] = row
                changes.extend(edits)
                counts["validated_" + mode] += 1
            # Persist every validated mode before attempting another recovery call.
            save()
            pending = retry
        failures.extend(batch[idx]["id"] for idx in pending)
        save()
        core.log(f"Saved {len(by_id)}/{len(records)}; unresolved {len(failures)}")
        if failures and not skip_failures:
            break
    ordered = save()
    missing = [r["id"] for r in records if r["id"] not in by_id]
    report = {"version": core.VERSION, "mode": getattr(runner, "mode", "MOCK_ONLY" if runner.is_mock else "FIXED_LLM"),
              "identity": identity["sha256"], "settings": identity["description"]["settings"],
              "requested_records": len(records), "records": len(ordered), "resumed_records": resumed,
              "failed_ids": failures, "missing_ids": missing,
              "unattempted_ids": [rid for rid in missing if rid not in failures],
              "format_validation": "PARTIAL" if missing else "PASS",
              "response_diagnostics": dict(counts), "retry_records": recovered,
              "rule_corrections": rule_corrections, "rule_change_count": len(changes),
              "max_prompt_tokens": max(token_counts, default=0),
              "token_counts_are_estimates": getattr(runner, "token_counts_are_estimates", runner.is_mock),
              "positive_items_without_quote": sum(row[f"v{i}"] == 1 and not row[f"e{i}"]
                  for row in ordered for i in range(1, 25) if i not in core.ABSENCE),
              "elapsed_seconds": round(time.monotonic() - start, 3),
              "model_load_seconds": runner.load_seconds, "accuracy_evaluated": False}
    atomic_json(report_path, report)
    atomic_json(audit_path, changes)
    atomic_json(failures_path, missing)
    if missing:
        if ordered:
            core.write_result(ordered, [r for r in records if r["id"] in by_id], partial_path)
        if not skip_failures:
            raise RuntimeError("Incomplete model decisions; successes saved to checkpoint; no submission created")
    else:
        core.write_result(ordered, records, final_path)
        if partial_path.exists():
            partial_path.unlink()
    return report
