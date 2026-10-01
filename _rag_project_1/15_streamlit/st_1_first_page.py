import streamlit as st

st.set_page_config(
    page_title="스트림릿 처음 배우기",
    page_icon="😂",
    layout="centered"
)

st.title("나의 첫 streamlit 페이지")
st.header("좀 큰 제목계열")
st.subheader("중간 제목계열")

# 텍스트 입력
st.text("글자를 꾸밈없이 그대로 보여줄 때 사용합니다.")

# 캡션
st.caption("작고 흐리게 적는 글자. 출처, 설명, 문구에 사용")

# 마크다운
st.header("마크다운 부분")
st.markdown("""
# 큰 제목
## 작은 제목
### 더 작은 제목

- 불릿1
- 불릿2
~~~
**굵게**
*기울김*
~~~
`
print("hello")
`
```mermaid
flowchart TB
    S1["`**01 · 체인**
    사람이 실행 순서를 고정한다`"]

    S2["`**02 · 에이전트**
    모델이 다음 행동을 선택하며 반복한다`"]

    S3["`**03 · 계획–실행**
    계획하는 역할과 실행하는 역할을 나눈다`"]

    S4["`**04 · 반성 루프**
    결과를 평가하고 수정한다`"]

    S5["`**05 · 멀티에이전트**
    감독이 전문가에게 작업을 맡긴다`"]

    S1 --- S2 --- S3 --- S4 --- S5

    classDef base fill:#F8FAFC,stroke:#CBD5E1,stroke-width:1.5px,color:#334155,rx:14,ry:14
    classDef focus fill:#FFF3CD,stroke:#E5A100,stroke-width:3px,color:#854D0E,rx:14,ry:14
    classDef team fill:#EEF2FF,stroke:#A5B4FC,stroke-width:1.5px,color:#3730A3,rx:14,ry:14

    class S1,S3,S4 base
    class S2 focus
    class S5 team

    linkStyle default stroke:#CBD5E1,stroke-width:2px
```

### 링크 넣기
[네이버 링크](https://naver.com) 네이버로 가는 링크입니다
""")

st.header("만능 글자 출력 - write")
st.write("문자열 **마크다운** 보일까요?")
st.write(2026)
st.write(["엔코아", "AI캠퍼스", "신대방"])
st.write({"이름": "윤택한", "과정" : "AI캠퍼스"})

# 데이터프레임으로도 표현
import pandas as pd

data = pd.DataFrame({
    "이름": ["윤택한", "송수림", "장안나"],
    "나이" : [41, 45, 32]
})
st.write(data)

# 구분선
st.divider()

# 코드
st.code("""
import pandas as pd
df = pd.read_csv("test.csv", encoding="utf-8")
df.head()
""", language="python")

# 이벤트나 성공, 실패 로그
st.header("이벤트처리")
st.error("에러가 생길경우 출력하도록")
st.success("성공했을 경우 출력하도록")
st.info("정보를 줘야할때")