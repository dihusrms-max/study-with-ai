# Pandas 데이터에 사람 검토 결과를 안전하게 반영하는 방법

자동 검출 결과를 바로 원본 데이터에 덮어쓰면 잘못된 판정이 섞일 수 있다. 이번에는 검토 요청, 사람의 검토 결과, 실제 라벨 반영을 분리하는 작은 workflow를 구현했다.

## 핵심 원칙

```text
검토 요청 생성
→ 사람 검토
→ 계약 검증
→ 명확한 판정만 반영
→ 원자적 저장
→ 재실행 결과 검증
```

검토가 끝나지 않았거나 기준이 모호한 항목은 보류하고, 근거가 확인된 항목만 반영한다.

## 검토 상태를 명시적으로 나누기

```python
class ReviewStatus(StrEnum):
    POSITIVE_CONFIRMED = "POSITIVE_CONFIRMED"
    NEGATIVE_CONFIRMED = "NEGATIVE_CONFIRMED"
    INSUFFICIENT_SOURCE = "INSUFFICIENT_SOURCE"
    CRITERIA_AMBIGUOUS = "CRITERIA_AMBIGUOUS"
```

`POSITIVE_CONFIRMED`는 evidence를 반드시 요구한다. 반대로 음성 판정이나 보류 상태에는 양성 근거를 넣지 않도록 검증한다.

## 검토 계약 검증

검토 요청과 결과는 `ID + 항목`을 키로 비교한다.

- 필수 컬럼이 모두 있는가?
- 키가 중복되지 않는가?
- 원문 hash가 현재 원문과 일치하는가?
- 요청과 결과의 키 집합이 같은가?
- evidence가 원문의 부분 문자열인가?
- 상태와 evidence 규칙이 서로 모순되지 않는가?

예를 들어 양성 판정의 근거가 원문에 실제로 포함되지 않으면 반영하지 않는다.

```python
if status == ReviewStatus.POSITIVE_CONFIRMED and not evidence:
    raise ReviewValidationError("양성 판정 evidence 누락")

if evidence and evidence not in str(task["원문"]):
    raise ReviewValidationError("evidence가 원문 부분문자열이 아닙니다")
```

## hash로 변경 감지하기

검토 요청을 만든 뒤 원본 라벨이 바뀌면, 당시 검토한 데이터와 현재 데이터가 달라진다. 그래서 원문과 라벨의 hash를 검토 계약에 저장하고 반영 전에 다시 계산한다.

```python
def sha256_text(value: object) -> str:
    return hashlib.sha256(str(value).encode("utf-8")).hexdigest()
```

hash가 다르면 전체 반영을 중단해 오래된 검토 결과가 새로운 원본을 덮어쓰지 않게 한다.

## 원자적 파일 교체

모든 검증이 통과한 뒤 결과를 임시 파일에 저장하고 같은 폴더의 원본과 교체한다.

```python
result.to_csv(temporary, index=False, encoding="utf-8-sig")
os.replace(temporary, output)
```

중간에 오류가 나더라도 검증이 끝나지 않은 결과를 원본 파일에 남기지 않는 것이 목적이다. 원본 파일 자체를 변경하는 운영 정책은 별도 승인과 백업 정책을 함께 정해야 한다.

## 멱등성 테스트

같은 검토 결과를 다시 적용했을 때 변경량이 0건이어야 한다.

```python
assert apply_decisions_atomically(path, task, decision) == {
    "label_changes": 0,
    "evidence_changes": 0,
    "changed_cells": 0,
}
```

멱등성은 재시도나 배치 재실행에서 중복 변경이 발생하지 않는지 확인하는 기준이다.

## 마무리

데이터 처리에서 중요한 것은 판정을 빠르게 적용하는 것이 아니라, 어떤 근거로 무엇이 바뀌었는지 추적할 수 있게 만드는 것이다. 검토 계약과 hash 검증, 보류 상태, 원자적 저장을 분리해두면 자동화 범위를 넓히면서도 사람의 확인 절차를 보존할 수 있다.

> 이 글은 `study_with_ai.review_workflow`와 테스트 코드를 바탕으로 작성한 게시 전 초안이다. 실제 운영 데이터와 자동 반영은 아직 연결하지 않았다.
