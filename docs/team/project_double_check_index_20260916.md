# 프로젝트 전체 더블체크 인덱스

작성일: 2026-09-16

이 문서는 다른 PC 또는 리뷰어가 현재 프로젝트의 운영 규칙, 제출물, 점수, Prompt 실험 상태를 한 번에 확인하기 위한 검토 순서표다.

## 1. 가장 먼저 확인할 파일

1. `Guide/나라장터_DACON_AI_경진대회_실전가이드_v1.9_개선전략보완.docx`
2. `docs/team/branch-rules.md`
3. `docs/team/data-contract.md`
4. `docs/team/submission-checklist.md`
5. `docs/team/pitfalls.md`
6. `docs/team/score_improvement_double_check_20260916.md`

## 2. 대회 규칙과 평가 기준

확인할 내용:

- 입력 공고 1건당 v1~v24를 모두 출력하는가
- 제출 CSV가 49개 열인지 확인했는가
- v값이 0 또는 1인지 확인했는가
- evidence가 원문 부분 문자열인지 확인했는가
- 부재탐지 항목의 evidence가 비어 있는가
- 실제 제출 횟수·실행시간·파일 크기 제한을 확인했는가
- 최신 공식 대회 공지를 다시 확인했는가

주요 파일:

- `Guide/나라장터_DACON_AI_경진대회_실전가이드_v1.9_개선전략보완.docx`
- `docs/team/data-contract.md`
- `docs/team/submission-checklist.md`

## 3. 현재 점수 기준선

| 기준 | 점수 | 해석 |
|---|---:|---|
| V0 실제 DACON 제출 | 0.2136954413 | 현재 실전 최고 기준선 |
| V1 Gemma 실제 DACON 제출 | 0.2070737569 | 실제 Gemma 제출 기준선 |
| Gemma API baseline dev 200건 | 0.203517 | 개발 비교 기준선 |
| P001-R API 반복 dev 200건 | 0.209369 | 변동성 확인용, 채택 점수 아님 |
| P002 API dev 200건 | 0.180042 | 폐기된 Prompt |

검토 원칙:

- API dev 점수를 DACON 점수와 동일하게 해석하지 않는다.
- P001-R의 상승을 Prompt 개선 효과로 간주하지 않는다.
- V0를 fallback으로 유지한다.
- 새 후보는 실제 DACON 점수로 검증되기 전까지 제출 기준선을 대체하지 않는다.

## 4. 제출물 확인

확인 대상:

- `outputs/submit_v1_baseline_20260915.zip`
- `DACON_2026/submit/v1_baseline/script.py`
- `DACON_2026/submit/v1_baseline/requirements.txt`
- `DACON_2026/scripts/preflight.py`

검토 항목:

- ZIP 최상위에 필요한 파일만 있는가
- `script.py`가 실제 Gemma를 호출하는가
- `output/submission.csv`를 생성하는가
- 데이터와 모델 가중치를 ZIP에 포함하지 않았는가
- 설치·실행 제한을 초과하지 않는가
- 제출 전 preflight를 통과했는가

## 5. 현재 오류 우선순위

Gemma API baseline dev 200건 기준:

| 항목 | FP | FN | 우선 조치 |
|---|---:|---:|---|
| v13 | 85 | 0 | 오탐 감소 |
| v17 | 52 | 3 | 오탐 감소 |
| v21 | 26 | 4 | 적용 조건 정리 |
| v24 | 29 | 4 | 문서·메타 비교 정교화 |
| v2 | 2 | 7 | 미탐 감소 |
| v6 | 3 | 6 | 미탐 감소 |
| v8 | 0 | 6 | 미탐 감소 |
| v10 | 0 | 7 | 부재탐지 보완 |
| v11 | 0 | 6 | 부재탐지 보완 |
| v14 | 0 | 8 | 미탐 감소 |

상세 근거:

- `DACON_2026/experiments/evaluation_table_baseline_20260915.md`
- `.tmp_user_code_test`의 로컬 API 결과 파일

## 6. Prompt 실험 상태

현재 상태:

- P001-R 기준선 반복 완료
- 기준선 변동성이 확인되어 v13 실험은 아직 보류
- P002는 전체 점수 하락으로 폐기
- 다음 후보는 v13 단독 Prompt

관련 파일:

- `DACON_2026/experiments/P002_v10_v11_absence.md`
- `logs/P001R_baseline_repeat_20260916.md`
- `docs/team/score_improvement_double_check_20260916.md`

모든 Prompt 실험은 다음 순서를 따른다.

```text
기준선 반복성 확인
→ 1건 JSON/evidence 확인
→ 10건 안정성 확인
→ dev 200건 평가
→ 24개 항목 회귀 확인
→ 사람 검토
→ 채택 또는 폐기
```

## 7. 다른 PC에서 재현할 때

```powershell
git pull origin main
```

그 다음 확인한다.

- 저장소 루트에서 VS Code를 열었는가
- `.venv` 커널을 선택했는가
- `DACON_2026` 서브모듈의 상태가 별도로 관리되고 있음을 확인했는가
- `.env`와 API 키가 Git에 포함되지 않았는가
- 데이터 경로가 PC별 절대 경로에 의존하지 않는가

## 8. 최종 검토 승인란

| 검토 항목 | 담당자 | 확인일 | 상태 |
|---|---|---|---|
| 대회 규칙 |  |  | 대기 |
| 데이터·CSV 계약 |  |  | 대기 |
| V0/V1 실제 점수 구분 |  |  | 대기 |
| 제출 ZIP 구조 |  |  | 대기 |
| 기준선 반복성 |  |  | 대기 |
| v13 Prompt 변경 |  |  | 대기 |
| API dev 결과 해석 |  |  | 대기 |
| 실제 DACON 제출 승인 |  |  | 대기 |

## 결론

현재 승인된 다음 작업은 기준선 변동성 확인을 마무리한 뒤 v13 단독 Prompt를 검증하는 것이다. V0 최고점 `0.2136954413`은 유지하고, API dev 결과는 후보 선별용으로만 사용한다.
