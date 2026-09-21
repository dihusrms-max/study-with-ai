"""Validation and idempotent application of human review decisions.

The module deliberately separates review evidence from label mutation.  It does
not infer a decision and never applies insufficient or ambiguous reviews.
"""

from __future__ import annotations

import hashlib
import os
import tempfile
from enum import StrEnum
from pathlib import Path
from typing import Iterable

import pandas as pd


KEY_COLUMNS = ("ID", "항목")
TASK_COLUMNS = (
    "review_batch_id",
    "ID",
    "항목",
    "검출_오류_사유",
    "원문",
    "원문_hash",
    "기준표_version",
    "원본_label_hash",
)
DECISION_COLUMNS = (
    "review_batch_id",
    "ID",
    "항목",
    "검토_상태",
    "검토_판정",
    "검토_evidence",
    "판정_사유_코드",
    "검토_메모",
    "검토자",
    "검토시각",
)


class ReviewStatus(StrEnum):
    POSITIVE_CONFIRMED = "POSITIVE_CONFIRMED"
    NEGATIVE_CONFIRMED = "NEGATIVE_CONFIRMED"
    INSUFFICIENT_SOURCE = "INSUFFICIENT_SOURCE"
    CRITERIA_AMBIGUOUS = "CRITERIA_AMBIGUOUS"


class ReviewValidationError(ValueError):
    """Raised when a review contract is unsafe to apply."""


def sha256_text(value: object) -> str:
    return hashlib.sha256(str(value).encode("utf-8")).hexdigest()


def label_hash(row: pd.Series, label_column: str, evidence_column: str) -> str:
    """Hash the exact key and values that an application is allowed to change."""

    values = [row[column] for column in (*KEY_COLUMNS, label_column, evidence_column)]
    return sha256_text("\x1f".join("" if pd.isna(value) else str(value) for value in values))


def _require_columns(frame: pd.DataFrame, required: Iterable[str], name: str) -> None:
    missing = [column for column in required if column not in frame.columns]
    if missing:
        raise ReviewValidationError(f"{name} 필수 열 누락: {missing}")


def _check_unique_keys(frame: pd.DataFrame, name: str) -> None:
    duplicates = frame.duplicated(list(KEY_COLUMNS), keep=False)
    if duplicates.any():
        keys = frame.loc[duplicates, list(KEY_COLUMNS)].to_dict("records")
        raise ReviewValidationError(f"{name} ID + 항목 중복: {keys}")


def validate_tasks(tasks: pd.DataFrame) -> None:
    """Validate an immutable review-task contract without changing it."""

    _require_columns(tasks, TASK_COLUMNS, "검토 요청")
    _check_unique_keys(tasks, "검토 요청")
    for index, row in tasks.iterrows():
        if sha256_text(row["원문"]) != str(row["원문_hash"]):
            raise ReviewValidationError(f"검토 요청 원문_hash 불일치: 행 {index}")


def validate_decisions(
    tasks: pd.DataFrame,
    decisions: pd.DataFrame,
    *,
    max_evidence_length: int = 2000,
) -> None:
    """Validate decisions, including semantic status/evidence consistency."""

    validate_tasks(tasks)
    _require_columns(decisions, DECISION_COLUMNS, "검토 결과")
    _check_unique_keys(decisions, "검토 결과")
    if set(map(tuple, decisions[list(KEY_COLUMNS)].to_numpy())) != set(
        map(tuple, tasks[list(KEY_COLUMNS)].to_numpy())
    ):
        raise ReviewValidationError("검토 요청과 결과의 ID + 항목 집합이 다릅니다.")

    task_map = tasks.set_index(list(KEY_COLUMNS))
    for index, row in decisions.iterrows():
        key = (row["ID"], row["항목"])
        task = task_map.loc[key]
        status = str(row["검토_상태"])
        evidence = "" if pd.isna(row["검토_evidence"]) else str(row["검토_evidence"])
        if status not in {item.value for item in ReviewStatus}:
            raise ReviewValidationError(f"알 수 없는 검토 상태: 행 {index}")
        if not str(row["판정_사유_코드"]).strip():
            raise ReviewValidationError(f"판정 사유 코드 누락: 행 {index}")
        if len(evidence) > max_evidence_length:
            raise ReviewValidationError(f"evidence 길이 초과: 행 {index}")
        if status == ReviewStatus.POSITIVE_CONFIRMED and not evidence:
            raise ReviewValidationError(f"양성 판정 evidence 누락: 행 {index}")
        if status != ReviewStatus.POSITIVE_CONFIRMED and evidence:
            raise ReviewValidationError(f"양성 이외 상태의 evidence는 비워야 합니다: 행 {index}")
        if evidence and evidence not in str(task["원문"]):
            raise ReviewValidationError(f"evidence가 원문 부분문자열이 아닙니다: 행 {index}")


def apply_decisions_atomically(
    source_csv: str | Path,
    tasks: pd.DataFrame,
    decisions: pd.DataFrame,
    output_csv: str | Path | None = None,
    *,
    label_column: str = "현재_판정",
    evidence_column: str = "evidence",
) -> dict[str, int]:
    """Apply only confirmed decisions through a same-directory atomic replace.

    ``output_csv`` defaults to ``source_csv``.  The source is never modified
    before all checks pass.  Re-running an already applied result returns zero
    changes.
    """

    validate_decisions(tasks, decisions)
    source = Path(source_csv)
    output = Path(output_csv) if output_csv else source
    frame = pd.read_csv(source, encoding="utf-8-sig")
    _require_columns(frame, (*KEY_COLUMNS, label_column, evidence_column), "원본 라벨")
    _check_unique_keys(frame, "원본 라벨")
    task_keys = set(map(tuple, tasks[list(KEY_COLUMNS)].to_numpy()))
    source_keys = set(map(tuple, frame[list(KEY_COLUMNS)].to_numpy()))
    if not task_keys <= source_keys:
        raise ReviewValidationError("검토 대상 키가 원본 라벨에 모두 존재하지 않습니다.")

    task_map = tasks.set_index(list(KEY_COLUMNS))
    for _, row in tasks.iterrows():
        source_row = frame.loc[(frame["ID"] == row["ID"]) & (frame["항목"] == row["항목"])].iloc[0]
        expected = str(row["원본_label_hash"])
        if expected and label_hash(source_row, label_column, evidence_column) != expected:
            raise ReviewValidationError(f"원본 라벨 hash 불일치: {(row['ID'], row['항목'])}")

    result = frame.copy()
    result[evidence_column] = result[evidence_column].fillna("").astype(str)
    changes = {"label_changes": 0, "evidence_changes": 0, "changed_cells": 0}
    result_index = result.set_index(list(KEY_COLUMNS)).index
    for _, decision in decisions.iterrows():
        key = (decision["ID"], decision["항목"])
        status = str(decision["검토_상태"])
        if status not in {ReviewStatus.POSITIVE_CONFIRMED.value, ReviewStatus.NEGATIVE_CONFIRMED.value}:
            continue
        position = result_index.get_loc(key)
        new_label = 1 if status == ReviewStatus.POSITIVE_CONFIRMED.value else 0
        new_evidence = "" if new_label == 0 else str(decision["검토_evidence"])
        old_label = result.iloc[position][label_column]
        old_evidence = "" if pd.isna(result.iloc[position][evidence_column]) else str(result.iloc[position][evidence_column])
        if str(old_label) != str(new_label):
            changes["label_changes"] += 1
            changes["changed_cells"] += 1
        if old_evidence != new_evidence:
            changes["evidence_changes"] += 1
            changes["changed_cells"] += 1
        result.iat[position, result.columns.get_loc(label_column)] = new_label
        result.iat[position, result.columns.get_loc(evidence_column)] = new_evidence

    output.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f".{output.stem}.", suffix=".tmp", dir=output.parent)
    os.close(fd)
    try:
        result.to_csv(temporary, index=False, encoding="utf-8-sig")
        os.replace(temporary, output)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    return changes


