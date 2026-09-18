# Runpod Gemma 4 팀원 접속 및 정상 테스트 지시문

작성일: 2026-09-18

## 1. 현재 정상 확인 상태

- Runpod GPU: NVIDIA A100-SXM4-80GB
- Docker Image: `vllm/vllm-openai:gemma4`
- Model: `google/gemma-4-26B-A4B-it`
- Served model name: `gemma-4-26B-A4B-it`
- Context: `16384`
- API Port: `8000`
- 외부 HTTPS endpoint: `https://5js0hp8ye4tq9o-8000.proxy.runpod.net/v1`
- 정상 확인 항목:
  - SSH 접속
  - GPU 인식
  - vLLM 서버 실행
  - `/v1/models` 인증 요청
  - 외부 Chat Completion 인증 요청

실제 테스트 결과는 `Chat Completion` 응답 `OK`로 확인되었다.

## 2. 팀원에게 공유할 값

다음 값만 공유한다.

```text
Base URL: https://5js0hp8ye4tq9o-8000.proxy.runpod.net/v1
Model: gemma-4-26B-A4B-it
API Key: 별도 보안 채널로 전달
```

API Key는 GitHub, Notion 공개 페이지, 단체 채팅에 평문으로 올리지 않는다.
SSH 개인키 `id_ed25519`도 팀원과 공유하지 않는다.

## 3. 팀원 환경변수 설정

프로젝트의 `.env` 파일에 다음을 작성한다.

```env
RUNPOD_BASE_URL=https://5js0hp8ye4tq9o-8000.proxy.runpod.net/v1
VLLM_API_KEY=실제_API_KEY
```

`.env` 파일은 Git에 커밋하지 않는다.

`.gitignore`에 다음 항목이 있는지 확인한다.

```gitignore
.env
```

## 4. Python 연결 테스트

필요 패키지:

```bash
pip install openai python-dotenv
```

테스트 코드:

```python
import os

from dotenv import load_dotenv
from openai import OpenAI


load_dotenv()

client = OpenAI(
    base_url=os.environ["RUNPOD_BASE_URL"],
    api_key=os.environ["VLLM_API_KEY"],
)

response = client.chat.completions.create(
    model="gemma-4-26B-A4B-it",
    messages=[
        {"role": "user", "content": "Reply with exactly: OK"}
    ],
    max_tokens=10,
    temperature=0,
)

print(response.choices[0].message.content)
```

정상 결과:

```text
OK
```

## 5. LangChain 연결

```python
import os

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI


load_dotenv()

model = ChatOpenAI(
    model="gemma-4-26B-A4B-it",
    base_url=os.environ["RUNPOD_BASE_URL"],
    api_key=os.environ["VLLM_API_KEY"],
    temperature=0,
)

response = model.invoke("개인정보 보호의 중요성을 한 문장으로 설명해줘.")
print(response.content)
```

OpenAI Embeddings와 Runpod Gemma는 역할이 다르다.

```text
OpenAI Embeddings: 문서 임베딩과 Chroma 검색
Runpod Gemma: 검색 결과를 바탕으로 답변 생성
```

## 6. RAG에 연결

기존 Chroma Vector DB를 `load_vs`로 불러온 뒤 사용한다.

```python
from langchain_core.prompts import ChatPromptTemplate


question = "개인정보를 수집할 때 동의가 필요한가요?"

retrieved_docs = load_vs.similarity_search(
    question,
    k=4,
)

context = "\n\n".join(
    f"[출처: {doc.metadata.get('source_file', '알 수 없음')}]\n"
    f"{doc.page_content}"
    for doc in retrieved_docs
)

prompt = ChatPromptTemplate.from_template("""
너는 개인정보 문서 안내 도우미다.

아래 참고 문서에 근거해서만 답변해라.
참고 문서에 답이 없으면 "문서에서 확인할 수 없습니다."라고 답변해라.
답변 마지막에 출처 파일명을 표시해라.

[참고 문서]
{context}

[질문]
{question}
""")

messages = prompt.format_messages(
    context=context,
    question=question,
)

response = model.invoke(messages)
print(response.content)
```

## 7. curl 테스트

API Key는 명령 기록이나 문서에 직접 넣지 않는다.

```bash
curl https://5js0hp8ye4tq9o-8000.proxy.runpod.net/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $VLLM_API_KEY" \
  -d '{
    "model": "gemma-4-26B-A4B-it",
    "messages": [
      {"role": "user", "content": "Reply with exactly: OK"}
    ],
    "max_tokens": 10,
    "temperature": 0
  }'
```

## 8. 문제 발생 시 확인 순서

### `401 Unauthorized`

- `VLLM_API_KEY`가 설정되어 있는지 확인한다.
- API Key 값에 앞뒤 공백이 없는지 확인한다.
- `Authorization: Bearer ...` 형식을 확인한다.

### `Connection refused` 또는 timeout

- Pod가 실행 중인지 확인한다.
- HTTP 8000 포트가 노출되어 있는지 확인한다.
- 현재 Pod의 HTTP endpoint URL이 최신인지 확인한다.

### 모델을 찾을 수 없음

다음 model 이름을 정확히 사용한다.

```text
gemma-4-26B-A4B-it
```

### Pod Migration 이후 접속 불가

Pod Migration 또는 새 Pod 생성 후에는 Pod ID와 HTTP URL이 바뀔 수 있다. Runpod의 Connect 화면에서 최신 HTTP 8000 URL을 다시 확인하고 `.env`의 `RUNPOD_BASE_URL`을 갱신한다.

### vLLM 시작 오류

초기 Docker Command는 다음 최소 설정을 사용한다.

```text
google/gemma-4-26B-A4B-it --served-model-name gemma-4-26B-A4B-it --dtype bfloat16 --max-model-len 16384 --gpu-memory-utilization 0.90 --max-num-seqs 4 --host 0.0.0.0 --port 8000
```

다음 옵션은 초기 진단 단계에서 추가하지 않는다.

```text
--limit-mm-per-prompt
```

포트는 반드시 `8000`이어야 하며 `80000`이 아니다.

## 9. 운영 주의사항

- GPU Pod를 사용하지 않을 때는 Stop하여 GPU 사용료를 줄인다.
- API Key를 교체하면 모든 팀원의 `.env`도 갱신한다.
- API Key를 코드에 하드코딩하지 않는다.
- 요청이 동시에 많으면 `max-num-seqs=4` 설정에 따라 대기할 수 있다.
- 팀원 접속용으로는 SSH보다 HTTPS API endpoint 사용을 권장한다.
