"""Run the high-score candidate pipeline through the configured Gemma API."""
from __future__ import annotations
import argparse
import importlib.util
import inspect
import json
import os
import sys
from pathlib import Path


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


class ApiAdapter:
    is_mock = False
    load_seconds = 0.0
    def __init__(self, runner, candidate):
        self.runner, self.candidate = runner, candidate
    def count_tokens(self, messages):
        return self.runner.count_tokens(messages)
    def chat(self, messages, mode="primary"):
        texts = self.runner.chat(messages)
        return [self.candidate.Generation(text=t, finish_reason="stop", finished=True)
                for t in texts]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True, type=Path)
    ap.add_argument("--data-dir", required=True, type=Path)
    ap.add_argument("--output", required=True, type=Path)
    ap.add_argument("--env-file", required=True)
    ap.add_argument("--limit", type=int)
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--chunk-size", type=int, default=1)
    ap.add_argument("--doc-chars", type=int, default=9000)
    ap.add_argument("--law-chars", type=int, default=2200)
    ap.add_argument("--max-tokens", type=int, default=1536)
    ap.add_argument("--timeout", type=int, default=240)
    ap.add_argument("--api-attempts", type=int, default=3)
    ap.add_argument("--ultra-compact", action="store_true")
    ap.add_argument("--skip-failures", action="store_true")
    ap.add_argument("--failures-file", type=Path)
    ap.add_argument("--candidate", type=Path)
    ap.add_argument("--base-url", default=os.environ.get("GEMMA_API_BASE_URL",
                    "https://ai.gtcc.app/gemma4/v1"))
    ap.add_argument("--primary-only", action="store_true",
                    help="비교용: 공고당 primary 요청만 보내고 실패 시 즉시 분리")
    args = ap.parse_args()
    root = Path(__file__).resolve().parent
    candidate_path = (args.candidate or (root / "script.py")).resolve()
    sys.path.insert(0, str(candidate_path.parent))
    candidate = load(candidate_path, "gomgom_candidate")
    base = load(root.parents[1] / "baseline" / "p003_script.py", "p003_api")
    records = list(candidate.read_records(args.input, args.limit))
    builder_kwargs = {"doc_chars": args.doc_chars, "law_chars": args.law_chars}
    if args.ultra_compact:
        builder_kwargs["ultra_compact"] = True
    builder = candidate.PromptBuilder(args.data_dir, **builder_kwargs)
    api = base.ApiRunner(candidate.compact_schema(), env_file=args.env_file, workers=args.workers,
                         max_tokens=args.max_tokens, timeout=args.timeout,
                         api_attempts=args.api_attempts, base_url=args.base_url)
    adapter = ApiAdapter(api, candidate)
    # Small chunks make progress visible and keep API retries bounded.
    run_kwargs = {"chunk_size": max(1, args.chunk_size), "max_tokens": args.max_tokens}
    run_params = inspect.signature(candidate.run).parameters
    if "skip_failures" in run_params:
        run_kwargs["skip_failures"] = args.skip_failures
    if "failures_path" in run_params:
        run_kwargs["failures_path"] = args.failures_file
    if "recovery_modes" in run_params:
        run_kwargs["recovery_modes"] = (("primary", args.max_tokens),) if args.primary_only else None
    report = candidate.run(records, builder, adapter, args.output, **run_kwargs)
    print(json.dumps(report, ensure_ascii=False))


if __name__ == "__main__":
    main()
