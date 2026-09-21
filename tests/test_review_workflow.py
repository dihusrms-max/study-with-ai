import pandas as pd
import pytest

from study_with_ai.review_workflow import (
    ReviewStatus,
    ReviewValidationError,
    apply_decisions_atomically,
    validate_decisions,
)
from study_with_ai.review_workflow.workflow import sha256_text, label_hash


def _contracts():
    source = pd.DataFrame([
        {"ID": "A", "항목": "v1", "원문": "지역 제한 없음", "현재_판정": 0, "evidence": ""},
    ])
    task = pd.DataFrame([{
        "review_batch_id": "batch-1", "ID": "A", "항목": "v1",
        "검출_오류_사유": "positive_without_evidence", "원문": "지역 제한 없음",
        "원문_hash": sha256_text("지역 제한 없음"), "기준표_version": "v1",
        "원본_label_hash": label_hash(source.iloc[0], "현재_판정", "evidence"),
    }])
    decision = pd.DataFrame([{
        "review_batch_id": "batch-1", "ID": "A", "항목": "v1",
        "검토_상태": ReviewStatus.POSITIVE_CONFIRMED.value, "검토_판정": 1,
        "검토_evidence": "지역 제한 없음", "판정_사유_코드": "REGION_RESTRICTION_CONFIRMED",
        "검토_메모": "", "검토자": "tester", "검토시각": "2026-09-21T00:00:00+09:00",
    }])
    return source, task, decision


def test_apply_is_idempotent(tmp_path):
    source, task, decision = _contracts()
    path = tmp_path / "labels.csv"
    source.to_csv(path, index=False, encoding="utf-8-sig")
    assert apply_decisions_atomically(path, task, decision) == {
        "label_changes": 1, "evidence_changes": 1, "changed_cells": 2
    }
    task.iloc[0, task.columns.get_loc("원본_label_hash")] = label_hash(
        pd.read_csv(path, encoding="utf-8-sig").iloc[0], "현재_판정", "evidence"
    )
    assert apply_decisions_atomically(path, task, decision) == {
        "label_changes": 0, "evidence_changes": 0, "changed_cells": 0
    }


def test_pending_status_is_not_applied():
    source, task, decision = _contracts()
    decision.loc[0, "검토_상태"] = ReviewStatus.INSUFFICIENT_SOURCE.value
    decision.loc[0, "검토_evidence"] = ""
    validate_decisions(task, decision)


def test_negative_requires_empty_evidence():
    _, task, decision = _contracts()
    decision.loc[0, "검토_상태"] = ReviewStatus.NEGATIVE_CONFIRMED.value
    with pytest.raises(ReviewValidationError):
        validate_decisions(task, decision)
