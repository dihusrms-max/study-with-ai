# 2026-09-18 일일 학습 보고

## 오늘 이해한 내용

오늘은 PDF·CSV 문서를 LangChain으로 처리하고, 청킹·검색·Prompt·LLM·출력 파서를 연결하여 RAG 파이프라인을 구성하는 과정을 학습했다.

```text
PDF·CSV
→ Document 변환
→ 문서 청킹
→ 임베딩 및 Chroma 저장
→ Retriever 검색
→ Prompt에 Context 주입
→ LLM 답변
→ 문자열 또는 구조화된 출력
```

## 핵심 개념

### 1. 문서 로딩과 Document

PDF와 CSV를 LangChain의 `Document` 객체로 변환한다.

- `page_content`: 문서 본문
- `metadata`: 페이지, 파일명, 행 번호 등

메타데이터는 답변에 출처와 페이지를 표시할 때 사용한다.

### 2. 청킹

긴 문서를 한 번에 임베딩하면 입력 길이 제한에 걸리거나 서로 다른 주제가 섞일 수 있다. `RecursiveCharacterTextSplitter`로 문서를 작은 조각으로 나눈다.

```python
RecursiveCharacterTextSplitter(
    chunk_size=400,
    chunk_overlap=80
)
```

- `chunk_size`: 문서 조각의 최대 크기
- `chunk_overlap`: 조각 사이에 겹치는 문맥

청킹은 검색 단위를 정하는 작업이므로 검색 품질에 영향을 준다.

### 3. Retriever와 MMR

저장된 벡터 DB에서 질문과 관련된 문서를 검색한다.

- Similarity 검색: 질문과 가장 유사한 문서를 선택
- MMR 검색: 유사도와 문서 간 다양성을 함께 고려

MMR은 비슷한 문서만 반복해서 검색되는 문제를 줄이는 데 도움이 된다.

### 4. LCEL

LangChain의 구성요소를 파이프라인처럼 연결한다.

```python
chain = prompt | model | parser
```

- `prompt`: 모델에게 역할과 답변 규칙 전달
- `model`: LLM 호출
- `parser`: 모델의 출력을 원하는 형식으로 변환
- `invoke()`: 체인 실행

`RunnablePassthrough()`는 원래 질문을 그대로 다음 단계로 전달할 때 사용한다.

### 5. RAG Prompt

검색된 문서를 Context로 묶어 Prompt에 전달한다.

```text
[참고자료]
검색된 문서

[질문]
사용자 질문
```

Prompt에는 다음 규칙을 넣을 수 있다.

- 참고자료만 사용하기
- 자료에 없으면 자료에 없다고 답하기
- 자격·금액·기한은 공식 공고 확인 안내
- 답변에 참고 페이지 표시

### 6. 구조화된 출력

LLM의 답변을 Pydantic 모델로 제한하면 일정한 필드 구조로 받을 수 있다.

```python
class AnswerStyle(BaseModel):
    answer: str
    source: str
```

문자열 답변보다 프로그램에서 후처리하기 쉽고, 답변과 출처를 분리해서 관리할 수 있다.

## 오늘 직접 확인한 것

- PDF 페이지를 `Document` 목록으로 변환했다.
- 페이지 메타데이터를 추가했다.
- 문서를 청크로 나누고 벡터 DB에 저장했다.
- Chroma Retriever로 관련 문서를 검색했다.
- Similarity 검색과 MMR 검색을 비교했다.
- Prompt, Model, Parser를 LCEL로 연결했다.
- 일반 문자열 출력과 구조화 출력의 차이를 확인했다.
- 검색 결과 개수 `k`를 바꾸며 답변 품질을 점검하는 방법을 확인했다.

## 주의할 점

- 청킹한 문서와 원본 문서를 혼동하지 않아야 한다.
- Prompt 변수명과 실제 코드 변수명이 일치해야 한다.
- 노트북은 셀 실행 순서에 따라 `NameError`가 발생할 수 있다.
- RAG는 검색 결과가 부정확하면 답변도 부정확해진다.

## 오늘의 한 문장

RAG 파이프라인은 문서를 검색 가능한 형태로 만들고, 검색된 근거를 Prompt에 넣어 LLM의 답변을 제한하는 과정이다.

