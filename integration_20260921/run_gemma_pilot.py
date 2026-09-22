"""Bounded API pilot; submission runtime stays offline and separate."""
from __future__ import annotations

import argparse
from dataclasses import asdict
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sys
import threading
import time
import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parent
PROJECT = ROOT.parent / "DACON_2026"
sys.path.insert(0, str(PROJECT / "src"))
sys.path.insert(0, str(PROJECT / "scripts"))
from gemma_api_runner import GemmaAPIRunner, load_dotenv, DEFAULT_BASE_URL, DEFAULT_MODEL
from experiment_manager import save_checkpoint, append_event
from koneps_ai.experiment_intelligence import ExperimentSessionState, ExperimentStage
from koneps_ai.experiment_intelligence.experiment_budget import ExperimentBudget, BudgetUsage, budget_stop_reason
from koneps_ai.experiment_intelligence.request_identity import canonical_hash, request_payload_hash, build_request_identity

sys.path.insert(0, str(ROOT / "candidate_v2"))
import baseline_core as baseline
import retrieval_core as core
import pipeline
from response_protocol import Generation, flag_schema, COMPACT_TOKENS


class BudgetedAPI(GemmaAPIRunner):
    is_mock = False
    mode = "GEMMA_API"
    token_counts_are_estimates = True

    def __init__(self, *, directory, identity, limit, timeout, api_budget, max_runtime, max_tokens):
        super().__init__(core.compact_schema(), base_url=os.environ.get("GEMMA_BASE_URL", DEFAULT_BASE_URL),
                         model=os.environ.get("GEMMA_MODEL", DEFAULT_MODEL), user_agent="study-contests/1.0",
                         api_key=os.environ["GEMMA_API_KEY"], timeout=timeout, max_tokens=max_tokens,
                         retries=0, seed=core.SEED, concurrency=1)
        self.directory = directory
        self.cache = directory / "api_cache"
        self.cache.mkdir(exist_ok=True)
        self.lock = threading.Lock()
        self.started = time.monotonic()
        self.budget = ExperimentBudget(api_budget=api_budget, max_runtime=max_runtime, max_candidates=1,
                                       max_dev200_runs=1, max_error_rate=1.0)
        self.state_path = directory / "session.json"
        self.events_path = directory / "events.jsonl"
        if self.state_path.exists():
            self.state = ExperimentSessionState.from_dict(json.loads(self.state_path.read_text(encoding="utf-8")))
            if self.state.baseline_fingerprint != identity["sha256"]:
                raise ValueError("API session fingerprint mismatch")
            if json.loads((directory / "budget.json").read_text()) != asdict(self.budget):
                raise ValueError("API budget changed; refusing implicit budget increase")
        else:
            self.state = ExperimentSessionState(session_id=directory.name, baseline_fingerprint=identity["sha256"],
                current_candidate=core.VERSION, current_stage=ExperimentStage.DIAGNOSTIC_12)
            pipeline.atomic_json(directory / "budget.json", asdict(self.budget))
            save_checkpoint(self.state, self.state_path)
            append_event(self.events_path, "pilot_started", self.state, records=limit, budget=asdict(self.budget))
        self.previous_runtime = self.state.elapsed_time
        self.calls = []
        self._request_mode = "primary"

    def count_tokens(self, messages):
        # Conservative character estimate, not the server tokenizer.
        return sum(len(m["content"]) for m in messages) + 64

    def chat(self, messages, mode="primary"):
        self._request_mode = mode
        return super().chat(messages)

    def _one(self, messages):
        mode = self._request_mode
        config = {"temperature": 0.0, "top_p": 1.0, "seed": core.SEED,
                  "max_tokens": self.max_tokens if mode == "primary" else COMPACT_TOKENS,
                  "chat_template_kwargs": {"enable_thinking": False}}
        if mode != "plain":
            config["response_format"] = {"type": "json_schema", "json_schema": {"name": "judgment", "strict": True,
                                         "schema": self.schema if mode == "primary" else flag_schema()}}
        payload = {"model": self.model, "messages": messages, **config}
        request_hash = request_payload_hash(messages, model=self.model, generation_config=config)
        cache_path = self.cache / (canonical_hash({"endpoint": self.base_url, "request_hash": request_hash}) + ".json")
        if cache_path.exists():
            result = json.loads(cache_path.read_text(encoding="utf-8"))
            with self.lock:
                self.state.cache_hits += 1
                save_checkpoint(self.state, self.state_path)
                append_event(self.events_path, "cache_hit", self.state, request_hash=request_hash, mode=mode)
        else:
            with self.lock:
                elapsed = self.previous_runtime + time.monotonic() - self.started
                reason = budget_stop_reason(self.budget, BudgetUsage(api_used=self.state.api_used, runtime=elapsed))
                if reason:
                    return Generation(error_code=reason)
                self.state.api_used += 1
                self.state.elapsed_time = elapsed
                save_checkpoint(self.state, self.state_path)
                append_event(self.events_path, "request_started", self.state, request_hash=request_hash, mode=mode)
            started = time.monotonic()
            result = {"request_hash": request_hash, "mode": mode}
            request = urllib.request.Request(self.base_url + "/chat/completions",
                data=json.dumps(payload, ensure_ascii=False).encode("utf-8"), method="POST",
                headers={"Authorization": "Bearer " + self.api_key, "Content-Type": "application/json", "User-Agent": self.user_agent})
            try:
                with urllib.request.urlopen(request, timeout=self.timeout) as response:
                    data = json.loads(response.read().decode("utf-8"))
                choice = data["choices"][0]
                result.update(text=choice["message"].get("content") or "", finish_reason=choice.get("finish_reason"),
                              model=data.get("model"), usage=data.get("usage") or {}, http_status=200)
                if not result["finish_reason"]:
                    result["error_code"] = "missing_finish_reason"
            except urllib.error.HTTPError as exc:
                result.update(error_code=f"http_{exc.code}", http_status=exc.code)
                exc.close()
            except (urllib.error.URLError, TimeoutError) as exc:
                result["error_code"] = "transport_" + type(exc).__name__
            except (ValueError, KeyError, IndexError, TypeError) as exc:
                result["error_code"] = "response_" + type(exc).__name__
            result["latency_seconds"] = round(time.monotonic() - started, 3)
            with self.lock:
                self.state.elapsed_time = self.previous_runtime + time.monotonic() - self.started
                save_checkpoint(self.state, self.state_path)
                append_event(self.events_path, "request_finished", self.state, request_hash=request_hash, mode=mode,
                             latency_seconds=result["latency_seconds"], error_code=result.get("error_code"),
                             finish_reason=result.get("finish_reason"), model=result.get("model"), usage=result.get("usage", {}))
                if not result.get("error_code"):
                    pipeline.atomic_json(cache_path, result)
        public = {k: v for k, v in result.items() if k != "text"}
        with self.lock:
            self.calls.append(public)
        print(json.dumps(public, ensure_ascii=False), flush=True)
        return Generation(text=result.get("text", ""), finish_reason=result.get("finish_reason"),
                          generated_tokens=int(result.get("usage", {}).get("completion_tokens", 0)),
                          finished=result.get("finish_reason") in ("stop", "length"), error_code=result.get("error_code"))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--limit", type=int, default=12)
    ap.add_argument("--timeout", type=int, default=120)
    ap.add_argument("--api-budget", type=int, default=36)
    ap.add_argument("--max-runtime", type=int, default=1200)
    ap.add_argument("--max-tokens", type=int, default=1536)
    ap.add_argument("--output-dir", type=Path)
    ap.add_argument("--resume", action="store_true")
    ap.add_argument("--env-file", type=Path, default=ROOT.parent / ".env")
    args = ap.parse_args()
    if not 1 <= args.limit <= 20 or args.api_budget < 1:
        ap.error("Pilot requires 1-20 records and a positive request cap")
    load_dotenv(args.env_file)
    if not os.environ.get("GEMMA_API_KEY"):
        raise RuntimeError("GEMMA_API_KEY is missing")
    output = (args.output_dir or ROOT / "validation" / ("gemma_pilot_" + datetime.now().strftime("%Y%m%d_%H%M%S"))).resolve()
    if args.resume and not output.is_dir():
        raise FileNotFoundError("Resume output directory does not exist")
    if output.exists() and not args.resume:
        raise FileExistsError("Use a new output directory or explicit --resume")
    output.mkdir(parents=True, exist_ok=args.resume)
    latest = json.loads((ROOT / "validation/latest.json").read_text())
    assets = Path(latest["report"]).parent / "data"
    source = PROJECT / "data/raw/dev.jsonl.gz"
    records = list(baseline.iter_records(str(source), args.limit))
    settings = {"pipeline": "retrieval", "rule_corrections": False, "doc_chars": 14000, "law_chars": 3000,
                "max_tokens": args.max_tokens, "seed": core.SEED, "chunk": 1, "transport": "API",
                "model": os.environ.get("GEMMA_MODEL", DEFAULT_MODEL), "base_url": os.environ.get("GEMMA_BASE_URL", DEFAULT_BASE_URL),
                "token_estimator": "characters-plus-64", "adapter_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    identity = pipeline.make_identity(records, settings, assets)
    pipeline.atomic_json(output / "identity.json", identity)
    builder = core.PromptBuilder(assets, 14000, 3000)
    runner = BudgetedAPI(directory=output, identity=identity, limit=len(records), timeout=args.timeout,
                         api_budget=args.api_budget, max_runtime=args.max_runtime, max_tokens=args.max_tokens)
    report = None
    error = None
    started = time.monotonic()
    try:
        report = pipeline.run(records, builder, runner, output, identity, chunk=1, max_tokens=args.max_tokens,
                              resume=args.resume, skip_failures=True, rule_corrections=False)
    except Exception as exc:
        error = type(exc).__name__
        raise
    finally:
        runner.state.elapsed_time = runner.previous_runtime + time.monotonic() - runner.started
        runner.state.last_checkpoint = str(output / "checkpoint.json")
        save_checkpoint(runner.state, runner.state_path)
        append_event(runner.events_path, "pilot_finished", runner.state, error_type=error,
                     completed=report.get("records", 0) if report else 0)
        summary = {"output": str(output), "requested_records": len(records), "api_used": runner.state.api_used,
                   "api_budget": args.api_budget, "cache_hits": runner.state.cache_hits, "calls": runner.calls,
                   "elapsed_seconds": round(time.monotonic() - started, 3), "error_type": error,
                   "report": report, "accuracy_evaluated": False}
        summary["request_identity"] = build_request_identity(input_path=source, record_ids=[r["id"] for r in records],
            request_hashes=[c["request_hash"] for c in runner.calls], candidate_id=identity["sha256"], model=runner.model,
            generation_config=settings, project_root=PROJECT)
        pipeline.atomic_json(output / "pilot_summary.json", summary)
        pipeline.atomic_json(ROOT / "validation/gemma_pilot_latest.json", {"summary": str(output / "pilot_summary.json")})
        print(json.dumps({k: summary[k] for k in ("output", "requested_records", "api_used", "elapsed_seconds", "error_type")}), flush=True)
    return 0 if report and report["format_validation"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
