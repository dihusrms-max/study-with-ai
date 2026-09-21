# 검토 결과 안전 반영

`study_with_ai.review_workflow`는 검토 요청과 검토 결과를 분리하고, 사람 검토가 명확히 끝난 행만 라벨 CSV에 원자적으로 반영한다.

- `POSITIVE_CONFIRMED`: 판정 1과 원문 부분문자열 evidence를 반영
- `NEGATIVE_CONFIRMED`: 판정 0과 빈 evidence를 반영
- `INSUFFICIENT_SOURCE`, `CRITERIA_AMBIGUOUS`: 반영 보류
- `ID + 항목` 중복, 원문/evidence 불일치, 원본 해시 불일치 시 전체 반영 중단
- 같은 결과를 다시 실행하면 변경량이 0건이어야 한다.

현재 저장소에는 검토 문서가 말하는 실제 43건 원본 라벨/검토 CSV가 없으므로, 이 구현은 계약과 반영기를 준비한 상태다. 실제 파일을 받으면 먼저 `validate_tasks()`와 `validate_decisions()`를 실행한 뒤 `apply_decisions_atomically()`를 호출한다.
