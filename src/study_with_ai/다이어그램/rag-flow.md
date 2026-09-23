# RAG 흐름

```mermaid
flowchart TD
    A["input_data 딕셔너리<br/>question, field, history"]

    A --> B["RunnableParallel"]

    B --> C["retriever_chain"]
    C --> C1["data['question'] 추출"]
    C1 --> C2["data['field'] 추출"]
    C2 --> C3["retriever.invoke<br/>질문 + field 필터"]
    C3 --> C4["검색된 Document 목록"]
    C4 --> C5["format_docs"]
    C5 --> C6["context 문자열"]

    B --> D["data['question'] 추출"]
    B --> E["data['history'] 추출"]

    C6 --> F["rag_history_prompt"]
    D --> F
    E --> F

    F --> G["프롬프트 완성"]
    G --> H["LLM 모델"]
    H --> I["StrOutputParser"]
    I --> J["최종 답변"]
```

## 실행 흐름

```text
input_data
→ RunnableParallel
→ 문서 검색
→ context 문자열 생성
→ history와 question 결합
→ ChatPromptTemplate
→ LLM
→ StrOutputParser
→ 최종 답변
```

## 입력 예시

```python
input_data = {
    "question": "CCTV 영상을 확인하고 싶은데 어떻게 해야 하나요?",
    "field": "의료 분야",
    "history": [],
}
```
