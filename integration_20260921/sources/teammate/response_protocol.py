"""Bounded per-record recovery of actual fixed-model responses.

No predictions are invented for missing fields. Evidence recovery only reads
completed cells from the SAME record; the caller verifies source substrings.
"""
from __future__ import annotations

import json
from dataclasses import dataclass

ITEMS = [f"v{i}" for i in range(1, 25)]
COMPACT_TOKENS = 768
COMPACT_OUTPUT = """
출력 형식: v1부터 v24까지 정확히 24개 키를 가진 JSON 객체 하나.
각 값은 정수 0 또는 1이다. 중첩 객체, 근거문구, 배열, 설명, 마크다운은 출력하지 않는다.
앞의 24항목 기준과 이 공고 내용을 검토하여 각 키의 판정을 완성한다.
"""


@dataclass(frozen=True)
class Generation:
    text: str = ""
    finish_reason: str | None = None
    generated_tokens: int = 0
    finished: bool = True
    error_code: str | None = None


class ResponseError(ValueError):
    """Contains only a fixed diagnostic code, never private model text."""


def flag_schema():
    return {"type": "object", "additionalProperties": False, "required": ITEMS,
            "properties": {key: {"type": "integer", "enum": [0, 1]} for key in ITEMS}}


def _unique_object(pairs):
    obj = {}
    for key, value in pairs:
        if key in obj:
            raise ValueError("Duplicate JSON key")
        obj[key] = value
    return obj


def parse_flags(text):
    decoder = json.JSONDecoder(object_pairs_hook=_unique_object)
    for pos, char in enumerate(text):
        if char != "{":
            continue
        try:
            obj, _ = decoder.raw_decode(text[pos:])
        except ValueError:
            continue
        if not isinstance(obj, dict) or set(obj) != set(ITEMS):
            continue
        if any(type(obj[key]) is not int or obj[key] not in (0, 1) for key in ITEMS):
            raise ResponseError("invalid_compact_flag")
        return {"v": [obj[key] for key in ITEMS], "e": {}}
    raise ResponseError("incomplete_compact_json")


def normalize_generation(value):
    if isinstance(value, Generation):
        return value
    # Compatibility for local scripted test runners. VLLMRunner always returns
    # Generation with the engine's actual finish metadata.
    if isinstance(value, str):
        return Generation(text=value, finish_reason="stop")
    return Generation(error_code="invalid_runner_result")


def read_decision(value, mode, full_parser):
    reply = normalize_generation(value)
    if reply.error_code:
        raise ResponseError(reply.error_code)
    if not reply.finished or reply.finish_reason not in ("stop", "length"):
        raise ResponseError("unfinished_or_aborted_generation")
    if not reply.text.strip():
        raise ResponseError("empty_model_response")
    try:
        obj = full_parser(reply.text) if mode == "primary" else parse_flags(reply.text)
    except (ValueError, TypeError, AttributeError):
        suffix = "after_token_limit" if reply.finish_reason == "length" else "after_stop"
        raise ResponseError("invalid_json_" + suffix) from None
    # A fully complete, validated object remains usable even if the engine
    # happened to hit its length limit immediately after the closing brace.
    return obj


def completed_quotes(text):
    """Read only complete leading per-item cells, never pad missing decisions."""
    decoder = json.JSONDecoder(object_pairs_hook=_unique_object)
    start = text.find("{")
    if start < 0:
        return {}
    pos, quotes, seen = start + 1, {}, set()
    while pos < len(text):
        while pos < len(text) and text[pos].isspace():
            pos += 1
        try:
            key, end = decoder.raw_decode(text[pos:])
        except ValueError:
            break
        if not isinstance(key, str) or key not in ITEMS or key in seen:
            break
        seen.add(key)
        pos += end
        while pos < len(text) and text[pos].isspace():
            pos += 1
        if pos >= len(text) or text[pos] != ":":
            break
        pos += 1
        while pos < len(text) and text[pos].isspace():
            pos += 1
        try:
            cell, end = decoder.raw_decode(text[pos:])
        except ValueError:
            break
        if (isinstance(cell, dict) and set(cell) == {"위반여부", "근거문구"}
                and type(cell["위반여부"]) is int and cell["위반여부"] == 1
                and isinstance(cell["근거문구"], str)):
            quotes[key[1:]] = cell["근거문구"]
        pos += end
        while pos < len(text) and text[pos].isspace():
            pos += 1
        if pos >= len(text) or text[pos] != ",":
            break
        pos += 1
    return quotes


def infer_batch(runner, prepared, mode, counts):
    """Retry only failed requests; split engine batch failures in bounded steps."""
    if not prepared:
        return []
    counts["requested_" + mode] += len(prepared)
    try:
        if mode == "primary":
            outputs = runner.chat(prepared)
        else:
            outputs = runner.chat(prepared, mode=mode)
        if not isinstance(outputs, (list, tuple)) or len(outputs) != len(prepared):
            raise ValueError("Unexpected response batch size")
        return [normalize_generation(value) for value in outputs]
    except Exception as exc:
        name = type(exc).__name__
        # Error messages may contain prompt excerpts. Preserve the exception
        # type, but do not print the exception message or traceback.
        counts["engine_" + name] += 1
        if name in {"EngineDeadError", "AsyncEngineDeadError"}:
            raise RuntimeError("Fixed-model engine stopped; no rule-only submission is permitted") from None
        if len(prepared) > 1:
            mid = len(prepared) // 2
            return (infer_batch(runner, prepared[:mid], mode, counts)
                    + infer_batch(runner, prepared[mid:], mode, counts))
        return [Generation(error_code="engine_" + name)]
