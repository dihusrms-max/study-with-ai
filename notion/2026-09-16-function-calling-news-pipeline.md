# 2026-09-16 Function Calling과 뉴스 분석 파이프라인

## 오늘 새롭게 이해한 내용

- Function Calling은 LLM이 필요한 Python 함수를 선택하고 실행하도록 연결하는 기능이다.
- `tools`에는 함수 이름, 설명, 매개변수 Schema를 작성한다.
- `available_tools`에는 도구 이름과 실제 Python 함수를 연결한다.
- 모델이 생성한 함수 인자는 JSON 문자열이므로 `json.loads()`로 변환해야 한다.
- 변환한 인자는 `function(**args)` 형식으로 실제 함수에 전달한다.
- 함수 실행 결과는 `role: tool` 메시지로 다시 LLM에 전달한다.
- LLM과 Python 함수를 연결하면 날씨 조회, 데이터 조회, 파일 저장 같은 작업을 자동화할 수 있다.
- 뉴스 분석 파이프라인은 읽기 → 분석 → 구조화 → 저장 순서로 설계할 수 있다.

## 오늘 직접 해결한 오류

### 1. `append` 사용 오류

```python
messages.append[...]
```

위 코드는 `append`를 리스트처럼 사용한 코드였다.

```python
messages.append(...)
```

`append`는 함수이므로 괄호로 호출해야 한다.

### 2. `messages` 자료형 오류

`messages`는 문자열이 아니라 메시지 딕셔너리 리스트여야 한다.

```python
messages = [
    {
        "role": "user",
        "content": "신대방 날씨 어때?"
    }
]
```

### 3. 도구 인자 이름 불일치

도구에서 `column`을 전달하는데 함수가 `column`을 받지 않으면 오류가 발생한다.

```python
def check_data(column):
    ...
```

도구 Schema와 Python 함수의 매개변수 이름은 일치해야 한다.

### 4. `NameError`

`available_tools`에 함수를 등록하기 전에 함수가 먼저 정의되어 있어야 한다.

```text
함수 정의
→ tools 정의
→ available_tools 정의
→ chat_with_tools 실행
```

## 뉴스 분석 파이프라인

```text
CSV 읽기
→ 제목과 본문 추출
→ LLM 분석 요청
→ category, summary, keywords 추출
→ 결과 리스트 저장
→ DataFrame 변환
→ CSV 저장
```

뉴스 분석 결과의 목표 구조:

```json
{
    "category": "경제",
    "summary": "뉴스의 핵심 내용",
    "keywords": ["핵심어1", "핵심어2", "핵심어3"]
}
```

## 핵심 코드 구조

```python
analysis = analyze_news(
    title=row["제목"],
    body=row["본문"]
)
```

```python
result_df.to_csv(
    "news_analysis_result.csv",
    index=False,
    encoding="utf-8-sig"
)
```

## 아직 복습할 내용

- `tool_calls` 객체의 내부 구조
- 여러 도구가 동시에 호출될 때 처리 방법
- JSON 응답이 깨졌을 때 예외 처리
- 1000개 API 요청의 비용과 속도 관리
- 실패한 뉴스만 다시 처리하는 방법
- 실제 주가 API와 임시 예시 데이터의 차이

## 다음 학습 목표

1. 뉴스 5개를 먼저 분석한다.
2. 결과 JSON 구조를 확인한다.
3. 실패한 데이터가 있는지 확인한다.
4. 전체 1000개 데이터로 확장한다.
5. 분석 결과의 카테고리와 요약 품질을 직접 검토한다.

## 핵심 정리

LLM은 함수를 직접 실행하는 것이 아니라 도구 이름과 인자를 생성하고, Python이 실제 함수를 실행한다.

```text
사용자 질문
→ 모델의 도구 선택
→ Python 함수 실행
→ 실행 결과를 모델에 전달
→ 최종 답변
```
