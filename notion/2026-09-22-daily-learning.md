# 2026-09-22 일일 학습 기록

## 오늘 이해한 것

### 1. RAG의 질문 처리 흐름

오늘은 `RunnableParallel`을 중심으로 질문, 분야 필터, 대화 이력을 분리해 처리한 뒤 검색 결과를 `context`로 만들고 LLM 응답으로 연결하는 구조를 정리했다.

```text
input_data(question, field, history)
→ RunnableParallel
→ Retriever 검색 + field metadata 필터
→ Document 목록
→ format_docs(context 문자열)
→ 질문·context·history 프롬프트
→ LLM
→ StrOutputParser
→ 최종 답변
```

`question`은 검색과 프롬프트에 사용되고, `field`는 metadata 필터에 사용되며, `history`는 이전 대화 맥락을 보완한다. 검색 결과의 본문은 `page_content`, 출처·분야·제목 같은 부가정보는 `metadata`에서 관리한다.

### 2. PostgreSQL과 pgvector를 이용한 RAG 구성

- `OpenAIEmbeddings`가 텍스트를 벡터로 변환한다.
- `PGVectorStore`가 임베딩과 문서 metadata를 PostgreSQL에 저장한다.
- Retriever는 MMR 검색으로 유사도뿐 아니라 결과의 다양성도 고려한다.
- `field` 같은 metadata 조건을 검색 단계에 함께 적용할 수 있다.
- 검색 체인과 대화 이력 체인은 분리해서 이해한 뒤 연결하는 편이 오류를 찾기 쉽다.

### 3. 대화 이력 처리

`session_id`로 대화방을 구분하고 PostgreSQL의 `chat_history`에서 기존 메시지를 읽어 프롬프트에 넣는다. 응답이 생성되면 `HumanMessage`와 `AIMessage`를 다시 저장해 다음 질문에서 사용할 수 있게 한다. 검색 결과 자체를 대화 이력에 저장하는 것이 아니라 메시지 흐름을 저장한다는 점을 구분했다.

### 4. 산업재해 RAG 프로젝트의 초기 범위

`[1]데이터 수집 및 API 데이터 정상 여부 점검_9.22` 문서를 기준으로 M0/M1 단계의 목적은 전처리보다 원본 확보와 구조 확인이다.

- 핵심 데이터: SIF 고위험요인 아카이브
- 보조 데이터: 사고재해자수, 사고사망자수, 사업장수, 사망만인율
- API 상태 코드·응답 형식·실제 행·전체 건수 확인
- `head`, `shape`, `columns`, `info`, 결측치, 중복 행 확인
- 기준연도, 산업·업종, 사업장 규모, 지역, 단위, 행의 grain 확인
- SIF가 사고 1건 단위인지 위험요인 1건 단위인지 먼저 확인

오늘 단계에서는 원본을 수정하지 않고 결측치와 중복은 개수만 확인해야 한다.

## 직접 확인한 산출물

- `1_pgvector_langchain.ipynb`: pgvector 기반 LangChain RAG 실습 노트북
- `2_lagnchain_detail.ipynb`: 검색 체인과 대화 이력 체인 상세 실습
- `rag-flow.md`: 질문부터 최종 답변까지의 RAG 흐름도
- `2_lagnchain_detail_mermaid.md`: PostgreSQL·PGVectorStore·Retriever·history 통합 구조도
- `2_lagnchain_detail_study_guide_draft.md`: 셀별 역할, 변수 흐름, 오류 확인 순서, 변형 과제, 완료 기준
- `[1]데이터 수집 및 API 데이터 정상 여부 점검_9.22`: 산업재해 RAG 데이터 수집·API 점검 계획

## 아직 확인하지 못한 것

- 실제 API 호출 성공 여부와 인증키 상태
- SIF 및 보조 데이터 원본의 실제 파일·URL·기준연도
- 각 데이터의 실제 `shape`, 컬럼명, dtype, 결측치, 중복 수
- SIF의 실제 grain과 사고사례 5~10건의 텍스트 구조
- PostgreSQL/pgvector 연결과 실제 검색 결과
- 노트북의 history용 프롬프트 셀에 남은 괄호·쉼표 오류의 수정 및 재실행 결과

## 직접 재현할 다음 실습

1. API 또는 CSV에서 원본을 읽고 상태 코드와 응답 형식을 출력한다.
2. 원본을 복사하지 않고 `head`, `shape`, `columns`, `info`, 결측치, 중복 수를 점검한다.
3. `Document(page_content, metadata)` 샘플을 만들어 `format_docs`의 출력을 확인한다.
4. 검색만 수행하는 체인과 검색 결과를 LLM에 전달하는 기본 RAG를 분리해 실행한다.
5. 검색 결과가 없을 때와 metadata 필터가 적용되지 않을 때를 별도 검증한다.

## 오늘의 한 줄 결론

RAG는 LLM 호출 코드 하나가 아니라 **원본 데이터의 구조·검색 근거·프롬프트·대화 이력을 검증 가능한 흐름으로 연결하는 시스템**이며, 산업재해 프로젝트도 먼저 API와 데이터 grain을 확인해야 안전하게 다음 단계로 넘어갈 수 있다.
