# 2026-09-23 일일 학습 기록

## 오늘 학습한 주제

일반적인 RAG 흐름에 Agent와 Tool을 연결하는 구조를 학습 지도 형태로 정리했다. 참고 자료는 `2_agent_multi_toll.ipynb`이며, 전체 구성요소와 입력·처리·출력의 흐름을 한눈에 파악할 수 있도록 다이어그램과 설명을 구성했다.

## 오늘 이해한 것

### 1. Agent 기반 RAG의 전체 흐름

사용자 질문을 받은 Agent는 요청에 맞는 Tool을 선택한다. 검색 Tool은 PGVectorStore에서 관련 문서를 찾고, 분야 검색 Tool은 metadata 조건을 적용한다. 저장 요청은 CSV 저장 Tool과 검증 Tool로 이어질 수 있다. 각 Tool의 결과는 Agent로 돌아가 최종 답변을 만드는 데 사용된다.

```text
사용자 질문
→ Agent
→ 검색·분야 검색·CSV 저장 또는 검증 Tool 선택
→ Tool 실행 결과 반환
→ Agent 최종 답변
```

### 2. Tool과 입력 스키마

Tool은 함수만 작성한다고 Agent가 자동으로 사용할 수 있는 것이 아니다. Tool의 목적과 입력을 설명하고, Pydantic 스키마로 입력 형식을 정한 뒤 Agent의 `tools` 목록에 등록해야 한다. `Field(description=...)`는 Agent가 입력값을 판단하는 데 필요한 설명으로 사용된다.

### 3. 검색 구성요소와 파라미터

`OpenAIEmbeddings`는 텍스트를 벡터로 변환하고, `PGVectorStore`는 문서 벡터와 metadata를 저장·검색하는 구성요소다. Retriever의 `search_type`, `k`, `fetch_k`, `lambda_mult`는 검색 결과의 방식과 개수, 다양성에 영향을 준다. 자료에는 similarity와 MMR 결과 및 파라미터를 비교하는 실험 순서를 정리했다.

### 4. CSV 저장 결과 확인

검색 결과를 CSV로 저장한 뒤에는 파일이 존재하는지만 보는 데 그치지 않고, `DictReader`로 다시 읽어 원래 질문과 일치하는 행이 있는지 확인하는 흐름을 정리했다. 저장 경로, 실행 기준 디렉터리, header와 저장·검증 시의 질문 일치 여부가 확인 지점이다.

### 5. 중간 결과를 따라가는 디버깅

최종 답변이 이상할 때 곧바로 답변 문구부터 고치기보다 Agent가 선택한 Tool, 전달된 입력, 검색된 Document와 metadata, `format_docs` 결과, CSV 저장 결과 순으로 확인해야 문제 위치를 좁힐 수 있다.

## 오늘 정리한 산출물

- `src/study_with_ai/다이어그램/00_agent_rag_learning_map.md`
- 전체 시스템 개요와 초기화·벡터 검색·Retriever·Tool·Agent·CSV 흐름도
- 파라미터 실험 순서, 디버깅 절차, 비교 분석 및 Markdown 보고서 확장 아이디어

## 검증 상태

이번 기록의 근거는 Agent 기반 RAG 학습 지도 문서의 작성 내용이다. 문서에는 노트북 실행 방법과 확인 절차가 정리되어 있지만, 이 자료만으로 PostgreSQL 연결, 실제 검색 및 Tool 호출, CSV 저장·검증의 실행 성공까지 확인되지는 않는다.

## 다음에 직접 해볼 실습

1. `2_agent_multi_toll.ipynb`의 초기화 셀부터 실행해 API 설정과 PostgreSQL 연결을 확인한다.
2. Agent에 등록된 Tool과 Pydantic 입력 스키마가 의도한 대로 동작하는지 확인한다.
3. 같은 질문으로 similarity와 MMR 검색 결과를 비교하고 제목·분야 metadata를 살펴본다.
4. Agent 실행 결과의 `messages`에서 실제 Tool 선택과 Tool 입력·출력을 확인한다.
5. CSV 저장 Tool을 실행한 뒤 파일을 다시 읽어 저장한 질문과 결과 행을 검증한다.

## 오늘의 한 줄 결론

Agent 기반 RAG는 검색 체인에 Tool 선택과 외부 작업을 연결한 구조다. 동작을 이해하고 오류를 찾으려면 최종 답변뿐 아니라 Agent의 Tool 선택부터 각 단계의 중간 결과까지 확인해야 한다.
