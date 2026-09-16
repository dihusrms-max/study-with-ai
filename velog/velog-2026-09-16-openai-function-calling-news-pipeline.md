# OpenAI Function Calling으로 Python 함수 연결하기

## 들어가며

오늘은 OpenAI API의 Function Calling을 활용해 LLM이 Python 함수를 선택하고 실행하도록 만드는 과정을 실습했다.

연결한 기능은 다음과 같다.

- 날씨 조회
- 데이터프레임 컬럼 조회
- 옷 코멘트 작성
- 주가 조회
- 질문과 답변 파일 저장
- 저장된 파일 조회

전체적인 구조는 다음과 같다.

```text
사용자 질문
    ↓
LLM이 필요한 도구 선택
    ↓
Python 함수 실행
    ↓
함수 결과를 LLM에 전달
    ↓
최종 답변 생성
```

## 1. Function Calling의 구성 요소

### tools

LLM에게 사용할 수 있는 함수의 이름과 설명을 알려준다.

```python
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "특정 도시의 날씨를 조회한다.",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "날씨를 알고 싶은 도시 이름"
                    }
                },
                "required": ["city"]
            }
        }
    }
]
```

### 실제 Python 함수

모델이 선택한 도구를 실제로 실행할 함수다.

```python
def get_weather(city):
    return f"{city}의 날씨는 맑음, 기온은 25도입니다."
```

### available_tools

도구 이름과 실제 함수를 연결한다.

```python
available_tools = {
    "get_weather": get_weather
}
```

모델이 `get_weather`를 선택하면 Python의 `get_weather()` 함수가 실행된다.

## 2. 모델이 전달한 인자 처리

모델이 보내는 함수 인자는 JSON 문자열이다.

```json
{"city": "신대방"}
```

Python에서 사용하려면 딕셔너리로 변환해야 한다.

```python
import json

args = json.loads(tool_call.function.arguments)
result = get_weather(**args)
```

`**args`는 다음 코드와 같은 의미다.

```python
get_weather(city="신대방")
```

## 3. 실습 중 발생한 오류

### `append` 사용 오류

잘못된 코드:

```python
messages.append[{
    "role": "user",
    "content": user
}]
```

`append`는 함수이므로 대괄호가 아니라 괄호를 사용해야 한다.

```python
messages.append({
    "role": "user",
    "content": user
})
```

### `messages` 자료형 오류

`messages`는 문자열이 아니라 메시지 딕셔너리를 담은 리스트여야 한다.

```python
messages = [
    {
        "role": "user",
        "content": "신대방 날씨 어때?"
    }
]
```

### 함수 인자 이름 불일치

도구에서 `column`을 전달하면 Python 함수도 `column`을 받아야 한다.

```python
def check_data(column):
    ...
```

이름이 다르면 다음 오류가 발생한다.

```text
TypeError: check_data() got an unexpected keyword argument 'column'
```

### 함수 정의 순서 오류

함수가 정의되기 전에 `available_tools`에 등록하면 `NameError`가 발생한다.

올바른 실행 순서는 다음과 같다.

```text
함수 정의
→ tools 정의
→ available_tools 정의
→ chat_with_tools 실행
```

## 4. 여러 도구 연결하기

```python
available_tools = {
    "get_weather": get_weather,
    "check_data": check_data,
    "get_stock_price": get_stock_price,
    "save_result": save_result,
    "read_result": read_result
}
```

모델이 선택한 도구는 다음과 같이 실행할 수 있다.

```python
args = json.loads(tool_call.function.arguments)

tool_function = available_tools[tool_call.function.name]
tool_result = tool_function(**args)
```

## 5. 뉴스 분석 파이프라인 설계

Function Calling 실습을 뉴스 분석 자동화로 확장할 수 있다.

목표는 뉴스 본문을 읽고 다음과 같은 정형 데이터로 변환하는 것이다.

- 카테고리
- 요약
- 핵심어

처리 과정은 다음과 같다.

```text
CSV 파일 읽기
    ↓
뉴스 제목과 본문 추출
    ↓
LLM에 분석 요청
    ↓
JSON 응답 받기
    ↓
카테고리·요약·핵심어 추출
    ↓
DataFrame으로 정리
    ↓
CSV 파일 저장
```

뉴스 1건의 결과는 다음과 같이 구성할 수 있다.

```json
{
    "category": "경제",
    "summary": "기업이 새로운 사업 계획을 발표했다.",
    "keywords": ["기업", "사업", "투자"]
}
```

반복문을 사용하면 여러 건의 뉴스를 처리할 수 있다.

```python
results = []

for index, row in df.iterrows():
    analysis = analyze_news(
        title=row["제목"],
        body=row["본문"]
    )

    results.append({
        "제목": row["제목"],
        "본문": row["본문"],
        "카테고리": analysis["category"],
        "요약": analysis["summary"],
        "핵심어": ", ".join(analysis["keywords"])
    })
```

그 결과를 DataFrame으로 만들고 CSV로 저장한다.

```python
result_df = pd.DataFrame(results)

result_df.to_csv(
    "news_analysis_result.csv",
    index=False,
    encoding="utf-8-sig"
)
```

## 6. 실행 시 주의할 점

처음부터 1000개를 실행하지 않고 5개 정도로 먼저 테스트해야 한다.

```python
test_df = df.head(5)
```

5개 테스트가 정상적으로 끝난 후 전체 데이터를 사용한다.

```python
target_df = df
```

고려해야 할 문제는 다음과 같다.

- JSON 형식이 깨지는 경우
- API 호출 제한
- 네트워크 오류
- 본문이 비어 있는 뉴스
- 응답 항목이 누락되는 경우
- 1000번 호출에 따른 비용과 처리 시간

## 마무리

이번 실습을 통해 LLM은 단순히 텍스트를 생성하는 도구가 아니라 Python 함수와 연결해 실제 작업을 수행하는 시스템으로 확장할 수 있다는 점을 배웠다.

핵심 구조는 다음과 같다.

```text
tools = LLM에게 함수 설명
available_tools = 실제 함수 연결
tool_calls = 모델이 선택한 함수
json.loads() = 함수 인자 변환
messages = 함수 결과 전달
```

앞으로는 뉴스 1000개를 대상으로 카테고리, 요약, 핵심어를 자동 생성하고 결과를 CSV로 저장하는 파이프라인을 완성할 예정이다.

## 참고

- [OpenAI Chat Completions API 공식 문서](https://platform.openai.com/docs/api-reference/chat/create)

## 태그

`Python` `OpenAI API` `Function Calling` `LLM` `Pandas` `데이터 파이프라인` `자동화`
