# LangChain 상세 구조

`2_lagnchain_detail.ipynb`의 RAG 검색 체인과 대화 이력 체인을 한눈에 보는 도식입니다.

```mermaid
flowchart TD
    subgraph SETUP[초기화 및 데이터 저장소]
        ENV[.env\nAPI 키 로드]
        DB[(PostgreSQL\nrag DB)]
        ENGINE[PGEngine\nconnection string]
        EMB[OpenAIEmbeddings\ntext-embedding-3-small]
        STORE[PGVectorStore\nfaq 테이블\nmetadata: field, title]
        ENV --> ENGINE
        ENGINE --> DB
        EMB --> STORE
        ENGINE --> STORE
    end

    subgraph RAG[RAG 검색·생성 체인]
        INPUT[사용자 입력\nquestion + field]
        RETR[Retriever\nsearch_type: MMR\nk=6, fetch_k=50\nlambda_mult=0.25]
        FILTER[RunnableLambda\nquestion으로 검색\nfield metadata 필터]
        DOCS[format_docs\n검색 문서를\n[title] + 내용으로 결합]
        MAP[RunnableParallel\ncontext: 문서 근거\nquestion: 원 질문]
        PROMPT[ChatPromptTemplate\nSystem: 개인정보 상담 도우미\nHuman: 참고자료 + 질문]
        LLM[Chat Model\ninit_chat_model\nopenai:gpt-5.6-luna]
        PARSER[StrOutputParser]
        ANSWER[최종 답변\nFAQ 제목을 [제목] 형식으로 표시]
        INPUT --> FILTER
        FILTER --> RETR
        RETR --> DOCS
        DOCS --> MAP
        INPUT --> MAP
        MAP --> PROMPT
        PROMPT --> LLM
        LLM --> PARSER
        PARSER --> ANSWER
    end

    STORE --> RETR

    subgraph HISTORY[대화 이력 체인]
        SESSION[session_id]
        HDB[(PostgreSQL\nchat_history 테이블)]
        HISTORYOBJ[PostgresChatMessageHistory\nHumanMessage + AIMessage]
        OLD[기존 history.messages]
        HPROMPT[ChatPromptTemplate\nSystem + history + question]
        HLLM[Chat Model\nopenai:gpt-4o-mini]
        HOUT[StrOutputParser\nanswer]
        SAVE[현재 질문과 답변 저장]
        SESSION --> HISTORYOBJ
        HDB --> HISTORYOBJ
        HISTORYOBJ --> OLD
        OLD --> HPROMPT
        HPROMPT --> HLLM
        HLLM --> HOUT
        HOUT --> SAVE
        SAVE --> HISTORYOBJ
    end

    INPUT -. 대화형 실행 시 .-> OLD
    ANSWER -. 응답 기록 .-> SAVE

    classDef input fill:#E0F2FE,stroke:#0284C7,color:#0C4A6E
    classDef process fill:#F0FDF4,stroke:#16A34A,color:#14532D
    classDef model fill:#FEF3C7,stroke:#D97706,color:#78350F
    classDef store fill:#F3E8FF,stroke:#9333EA,color:#581C87
    classDef output fill:#FFE4E6,stroke:#E11D48,color:#881337
    class INPUT,SESSION input
    class FILTER,RETR,DOCS,MAP,PROMPT,HPROMPT process
    class LLM,HLLM,EMB model
    class DB,STORE,HDB,HISTORYOBJ store
    class ANSWER,PARSER,HOUT,SAVE output
```

## 체인 요약

```text
input_data
  ├─ question ───────────────────────────────┐
  └─ field → Retriever(MMR + metadata filter) │
                                             ↓
                                  format_docs(context)
                                             ↓
                 {context, question} → prompt → model → StrOutputParser
```

대화 이력 기능은 검색 결과를 직접 저장하는 구조가 아니라, `chat_history` 테이블에서 이전 메시지를 읽어 프롬프트에 넣고, 생성된 `HumanMessage`와 `AIMessage`를 다시 저장하는 별도 흐름입니다.

> 참고: 원 노트북에는 history용 프롬프트 셀에 괄호/쉼표가 맞지 않는 미완성 코드가 포함되어 있어, 위 도식은 의도된 데이터 흐름을 기준으로 표현했습니다.
