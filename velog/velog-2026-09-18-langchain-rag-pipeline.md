# LangChain으로 RAG 파이프라인 구성하기

## 문서 로딩

PDF와 CSV를 LangChain의 `Document` 객체로 변환한다.

```python
Document(
    page_content=text,
    metadata={"source": "policy.pdf", "page": 1}
)
```

`page_content`는 검색할 본문이고, `metadata`는 출처·페이지·파일명처럼 답변 검증에 사용할 정보다.

## 청킹

긴 문서를 통째로 임베딩하면 입력 길이 제한에 걸리거나 여러 주제가 섞일 수 있다. 그래서 문서를 작은 조각으로 나눈다.

```python
splitter = RecursiveCharacterTextSplitter(
    chunk_size=400,
    chunk_overlap=80
)
chunks = splitter.split_documents(documents)
```

`chunk_overlap`은 조각 경계에서 문맥이 끊기는 문제를 줄여준다. 다만 청크가 너무 작으면 문맥이 부족하고, 너무 크면 검색 결과에 불필요한 내용이 섞일 수 있다.

## Chroma와 Retriever

청크를 임베딩하여 Chroma에 저장하면 질문과 의미가 가까운 문서를 검색할 수 있다.

```python
retriever = vector_store.as_retriever(
    search_type="mmr",
    search_kwargs={
        "k": 5,
        "fetch_k": 50,
        "lambda_mult": 0.25,
    },
)
```

Similarity 검색은 유사도가 높은 문서를 고르고, MMR은 유사도와 결과의 다양성을 함께 고려한다. `k`는 최종적으로 사용할 문서 수이며, `fetch_k`는 후보 문서 수다.

## LCEL로 체인 연결

LangChain Expression Language에서는 각 구성요소를 파이프 연산자로 연결한다.

```python
chain = prompt | model | parser
```

- Prompt: 질문과 Context를 모델 입력으로 구성
- Model: LLM 호출
- Parser: 결과를 문자열·리스트·JSON 등으로 변환

RAG 체인에서는 질문을 검색기와 Prompt에 동시에 전달한다.

```python
rag_chain = (
    {
        "context": retriever | format_docs,
        "question": RunnablePassthrough(),
    }
    | rag_prompt
    | model
    | StrOutputParser()
)
```

`context`는 검색된 문서이고, `question`은 사용자의 원래 질문이다.

## 근거 기반 Prompt

RAG Prompt에는 모델이 지켜야 할 답변 규칙을 명시한다.

```text
아래 참고자료를 바탕으로 답변한다.
참고자료에 없으면 자료에 없다고 말한다.
답변에 참고 페이지를 표시한다.
```

이 규칙은 모델이 검색 결과 밖의 내용을 임의로 만들어내는 것을 줄이는 데 도움이 된다.

## 구조화된 출력

답변과 출처를 일정한 형식으로 받고 싶다면 구조화 출력을 사용한다.

```python
class AnswerStyle(BaseModel):
    answer: str
    source: str

structured_model = model.with_structured_output(
    AnswerStyle,
    method="json_mode",
)
```

일반 문자열보다 후처리와 저장이 쉽고, 응답 형식을 일관되게 유지할 수 있다.

## 검증 방법

RAG 결과는 다음 항목으로 확인한다.

1. 질문에 직접 답했는가?
2. 검색 문서에 없는 내용을 상상하지 않았는가?
3. 출처나 페이지가 표시되었는가?
4. 검색 결과 수 `k`를 바꿔도 답변이 안정적인가?

## 마무리

RAG 파이프라인은 단순히 LLM을 호출하는 코드가 아니다. 문서 로딩, 청킹, 임베딩, 검색, Prompt 구성, 출력 형식, 검증이 연결된 시스템이다. 각 단계의 품질이 최종 답변의 정확도와 신뢰도를 결정한다.

