# LangChain과 pgvector로 RAG 검색·대화 체인 분리하기

오늘은 LangChain 기반 RAG 애플리케이션의 전체 흐름을 정리하고, PostgreSQL과 pgvector를 벡터 저장소로 사용하는 구조를 살펴봤다. 핵심은 RAG를 단순한 `질문 → LLM` 호출로 보지 않고, 검색 근거와 대화 이력을 검증 가능한 단계로 나누어 이해하는 것이다.

## 1. RAG 체인의 전체 흐름

RAG 체인은 질문을 바로 LLM에 전달하지 않는다. 먼저 질문과 조건으로 관련 문서를 검색하고, 검색 결과를 프롬프트의 근거 자료로 넣은 뒤 답변을 생성한다.

```text
input_data
  ├─ question
  ├─ field
  └─ history
        ↓
RunnableParallel
        ↓
Retriever + metadata filter
        ↓
Document 목록
        ↓
format_docs(context)
        ↓
질문 + context + history 프롬프트
        ↓
LLM
        ↓
StrOutputParser
        ↓
최종 답변
```

`RunnableParallel`은 같은 입력에서 검색에 필요한 값과 프롬프트에 필요한 값을 나누어 준비한다.

- `question`: 검색어와 최종 프롬프트의 질문
- `field`: 문서 metadata 필터
- `history`: 이전 대화 맥락
- `context`: 검색된 문서를 프롬프트에 넣기 위한 문자열

즉, 병렬로 값을 준비한 뒤 `{context, question, history}` 형태로 프롬프트에 전달하는 구조다.

## 2. Document의 본문과 metadata

검색 결과는 보통 `Document` 객체 목록으로 반환된다.

- `page_content`: 검색된 문서의 본문
- `metadata`: 제목, 분야, 출처, 파일명 등 부가정보

답변의 근거를 표시하려면 본문만 전달하지 말고 metadata도 함께 관리해야 한다. `format_docs` 단계에서 문서 제목과 본문을 합쳐 `context` 문자열을 만든다.

```python
def format_docs(documents):
    return "\n\n".join(
        f"[{doc.metadata.get('title')}]\n{doc.page_content}"
        for doc in documents
    )
```

문서 제목이 없거나 검색 결과가 빈 리스트인 경우도 별도로 처리해야 한다.

## 3. PostgreSQL과 pgvector 구조

PostgreSQL에 `vector` 확장을 활성화하고 Python에서 pgvector 연동 클래스를 사용하면 관계형 데이터와 벡터 검색을 한 시스템 안에서 구성할 수 있다.

```text
환경변수
  ↓
PGEngine ── PostgreSQL
  ↓
OpenAIEmbeddings → PGVectorStore
                         ↓
                    Retriever
```

| 구성요소 | 역할 |
| --- | --- |
| `OpenAIEmbeddings` | 텍스트를 벡터로 변환 |
| `PGEngine` | PostgreSQL 연결 관리 |
| `PGVectorStore` | 벡터·문서·metadata 저장 및 검색 |
| `Retriever` | 질문과 유사한 문서 반환 |
| `ChatPromptTemplate` | 검색 근거와 질문을 LLM 입력으로 구성 |
| `StrOutputParser` | 모델 응답을 문자열로 변환 |

## 4. MMR 검색 설정 이해하기

실습 구조의 Retriever는 MMR(Maximal Marginal Relevance) 검색을 사용한다.

```text
search_type = MMR
k = 6
fetch_k = 50
lambda_mult = 0.25
```

- `fetch_k`: 후보로 먼저 가져올 문서 수
- `k`: 최종적으로 반환할 문서 수
- `lambda_mult`: 유사도와 결과 다양성 사이의 균형

유사도 검색만 사용하면 내용이 거의 같은 문서가 여러 개 선택될 수 있다. MMR은 질문과 관련성이 높으면서 서로 다른 정보를 가진 문서를 함께 선택하려는 방식이다.

## 5. 검색 체인과 대화 이력 체인 분리하기

대화형 RAG에서는 검색 결과와 대화 이력이 함께 사용되지만 역할은 다르다.

- 검색 체인: 현재 질문과 조건에 맞는 근거 문서를 찾는다.
- history 체인: `session_id`로 이전 메시지를 읽고 새 질문·답변을 저장한다.

검색 결과를 대화 이력에 저장하는 것이 아니라 `HumanMessage`와 `AIMessage`의 대화 흐름을 저장한다. 두 기능은 검색만 실행하는 버전, 기본 RAG, 출처 포함 RAG, 대화 이력 추가 순서로 나누어 구현하는 것이 좋다.

## 6. 오류를 찾는 순서

```text
1. API 키와 환경변수
2. PostgreSQL 연결
3. 테이블·컬럼·vector 확장
4. embedding 호출
5. 검색 입력 타입
6. 검색 결과가 빈 리스트인지
7. prompt에 전달한 값의 형식
8. LLM 응답 객체와 문자열 변환
9. session_id와 history 저장
```

각 단계에서 입력값의 타입, 기대한 출력, 실제 출력 또는 오류, 다음 단계에서 사용하는 변수를 기록하면 원인 범위를 좁힐 수 있다.

## 7. 다음에 직접 재현할 실습

- `Document(page_content, metadata)` 샘플로 `format_docs` 출력 확인
- `k=2`, `k=4`, `k=6` 결과 비교
- similarity search와 MMR 검색 결과 비교
- 특정 `field`만 검색하도록 metadata 필터 적용
- 검색 결과가 없을 때 안내 메시지 반환
- 답변과 함께 참조 문서 제목 출력
- history를 제거한 단순 RAG와 history를 포함한 RAG 비교

## 마무리

오늘의 핵심은 RAG를 하나의 긴 체인으로 외우는 것이 아니라 **입력 분리 → 문서 검색 → context 구성 → 프롬프트 생성 → LLM 응답 → 대화 이력 저장**의 데이터 흐름으로 이해하는 것이다.
