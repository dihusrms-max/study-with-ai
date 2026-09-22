#!/usr/bin/env python3
"""Integrated DACON candidate: user's CLI, teammate retrieval and strict recovery."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

import baseline_core as baseline
import retrieval_core as core
from pipeline import BaselineBuilder, make_identity, run


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", default=os.environ.get("PPS_DATA_DIR", "./data"))
    parser.add_argument("--output-dir", default=os.environ.get("PPS_OUTPUT_DIR", "./output"))
    parser.add_argument("--input")
    parser.add_argument("--model-dir", default=os.environ.get("PPS_MODEL_DIR", baseline.MODEL_DIR))
    parser.add_argument("--quantization", default=os.environ.get("PPS_QUANT", baseline.QUANT))
    parser.add_argument("--gpu-mem", type=float, default=0.92)
    parser.add_argument("--tp", type=int, default=1)
    parser.add_argument("--chunk", type=int, default=128)
    parser.add_argument("--max-chars", "--doc-chars", dest="max_chars", type=int)
    parser.add_argument("--max-tokens", type=int, default=baseline.MAX_TOKENS)
    parser.add_argument("--limit", type=int)
    parser.add_argument("--mock", action="store_true")
    parser.add_argument("--pipeline", choices=("baseline", "retrieval"), default="retrieval")
    parser.add_argument("--law-chars", type=int, default=3000)
    parser.add_argument("--rule-corrections", action="store_true", help="Opt in to logged rule overrides")
    parser.add_argument("--resume", action="store_true", help="Require matching typed checkpoint")
    parser.add_argument("--skip-failures", action="store_true", help="Local partial evaluation; never creates a final submission")
    args = parser.parse_args(argv)
    chars = args.max_chars if args.max_chars is not None else (4000 if args.pipeline == "baseline" else 14000)
    if args.chunk < 1 or args.tp < 1 or not 0 < args.gpu_mem <= 1:
        parser.error("chunk/tp must be positive and gpu-mem must be in (0, 1]")
    if args.limit is not None and args.limit < 1:
        parser.error("limit must be positive")
    if not 1 <= args.max_tokens < core.MAX_MODEL_LEN - 256 or chars < 1400 or args.law_chars < 0:
        parser.error("Invalid token or document budget")
    if args.rule_corrections and args.pipeline != "retrieval":
        parser.error("rule-corrections requires --pipeline retrieval")
    if os.environ.get("PPS_MODEL_DIR") and (args.mock or args.limit is not None or args.input or args.skip_failures):
        parser.error("Server mode prohibits mock, limited/custom input, and partial output")
    data = Path(args.data_dir).resolve()
    input_path = Path(args.input).resolve() if args.input else data / "test.jsonl.gz"
    records = list(baseline.iter_records(str(input_path), args.limit))
    if not records or len({rec["id"] for rec in records}) != len(records):
        parser.error("Input must be nonempty with unique IDs")
    quant = None if args.quantization.lower() in ("", "none") else args.quantization
    settings = {"pipeline": args.pipeline, "rule_corrections": args.rule_corrections,
                "doc_chars": chars, "law_chars": args.law_chars, "max_tokens": args.max_tokens,
                "chunk": args.chunk, "seed": core.SEED, "max_model_len": core.MAX_MODEL_LEN,
                "model_dir": str(Path(args.model_dir).resolve()), "quantization": quant,
                "gpu_mem": args.gpu_mem, "tp": args.tp, "mock": args.mock}
    identity = make_identity(records, settings, data)
    builder = (BaselineBuilder(data, chars) if args.pipeline == "baseline"
               else core.PromptBuilder(data, chars, args.law_chars))
    runner = core.MockRunner() if args.mock else core.VLLMRunner(args.model_dir, args.max_tokens, args.gpu_mem, quant, args.tp)
    report = run(records, builder, runner, Path(args.output_dir), identity, chunk=args.chunk,
                 max_tokens=args.max_tokens, resume=args.resume, skip_failures=args.skip_failures,
                 rule_corrections=args.rule_corrections)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["format_validation"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
