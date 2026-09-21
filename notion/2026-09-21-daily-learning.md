# 2026-09-21 일일 학습 기록

## 오늘 새롭게 이해한 것

오늘은 RAG의 검색 결과를 LLM에 연결하는 흐름을 복습하고, 관계형 데이터베이스와 `pgvector`를 Python에서 연결하는 실습을 진행했다. 동시에 사람의 검토 결과를 데이터에 반영할 때 필요한 검증·해시·원자적 저장 구조를 구현했다.

### 1. RAG 파이프라인 복습

```text
PDF·CSV
→ Document와 metadata
→ 청킹
→ 임베딩·벡터 저장소
→ Retriever/심화 검색
→ Context를 Prompt에 주입
→ LLM 답변
→ 문자열 또는 구조화된 출력
```

- 문서의 본문과 출처 metadata를 분리하면 답변에 페이지·파일 근거를 남길 수 있다.
- MMR 검색은 유사도뿐 아니라 결과 간 다양성도 고려한다.
- 구조화 출력은 답변과 출처를 일정한 필드로 받아 후처리하기 쉽다.
- 문서에 없는 내용은 추측하지 않도록 Prompt에 제한을 명시하고, 검색 결과와 답변을 함께 검증해야 한다.

### 2. 관계형 DB와 pgvector

- 회원·책·대출처럼 서로 다른 개체를 테이블로 분리하고, 외래 키로 관계를 표현한다.
- SQL의 `WHERE`, `JOIN`, `GROUP BY`, 집계 함수로 필요한 분석 결과를 만든다.
- PostgreSQL에 `vector` 확장을 활성화하고 Python의 `pgvector` 어댑터를 등록하면 `vector(1536)` 컬럼을 가진 문서 테이블을 만들 수 있다.
- RAG의 벡터 검색 저장소를 Chroma 같은 전용 저장소뿐 아니라 관계형 DB 안에서도 구성할 수 있다는 점을 확인했다.

### 3. 사람 검토 결과의 안전한 반영

새로 만든 `study_with_ai.review_workflow`는 검토 요청과 검토 결과를 분리한다.

- `ID + 항목` 중복을 검사한다.
- 원문 hash와 원본 라벨 hash로 검토 시점 이후의 변경을 감지한다.
- `POSITIVE_CONFIRMED`만 evidence를 요구하며, evidence는 원문의 부분 문자열이어야 한다.
- `INSUFFICIENT_SOURCE`와 `CRITERIA_AMBIGUOUS`는 자동 반영하지 않는다.
- 모든 검증이 통과한 뒤 임시 파일을 같은 폴더에 만들고 `os.replace()`로 원자적으로 교체한다.
- 같은 결과를 다시 실행하면 변경량이 0건이 되는지 테스트했다.

## 직접 확인한 것

- LangChain RAG 복습 노트북에서 Retriever, Prompt, 구조화 출력, 연습 질문을 실행했다.
- PostgreSQL 연결 후 `vector` 확장 버전과 `documents` 테이블의 컬럼 타입을 확인했다.
- `review_workflow`의 양성 반영·보류 상태·evidence 검증·멱등성 테스트를 작성했다.
- 검토 계약과 실제 원본 라벨 파일이 아직 저장소에 함께 있지 않으므로, 현재 구현은 계약 검증과 반영기 준비 단계다.

## 아직 애매하거나 확인할 것

- 실제 운영 데이터에서 검토 요청 CSV와 검토 결과 CSV의 생성·검증 절차를 정해야 한다.
- PostgreSQL/pgvector에서는 임베딩 저장 이후 유사도 검색 SQL과 인덱스 사용 방법을 추가로 실습해야 한다.
- 오늘 수정된 실습 노트북에는 실행 순서와 데이터 적재 부분을 다시 점검할 코드가 있으므로 게시 전에 재실행 검증이 필요하다.
- 의존성 설정의 `psycopg[binaray,binary]` 표기는 오타 가능성이 있어 별도 수정·검증 대상이다.

## 오늘의 한 문장

RAG는 검색 근거를 답변에 연결하는 문제이고, 데이터 반영 workflow는 사람이 확인한 근거만 안전하게 원본에 적용하는 문제다.

## 참고 파일

- `src/study_with_ai/8_RAG파이프라인구축/5_2복습.ipynb`
- `src/study_with_ai/9_관계형DB_pgvector/3_pgvector.ipynb`
- `src/study_with_ai/review_workflow/workflow.py`
- `tests/test_review_workflow.py`
- `docs/review_workflow/README.md`
