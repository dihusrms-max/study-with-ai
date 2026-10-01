import streamlit as st

st.set_page_config(
    page_title="스트림릿 처음 배우기",
    page_icon="😂",
    layout="centered"
)

import pandas as pd
from datetime import datetime

## 1. rerun 대한 이해 - 실행 시간 확인
st.caption(f"이파일이 실행된 시간 : {datetime.now().strftime('%H:%M:%S')}")

## 2. 버튼 만들기
st.header("버튼 클릭")

if st.button("여기 버튼을 눌러보세요"):
    st.write("버튼을 눌렀습니다.")
    st.balloons()

## 3. 텍스트 입력 - 나중에 챗봇에서 대화 입력
name = st.text_input("이름을 입력하세요", placeholder="예: 윤택한")

if name:
    st.write(f"안녕하세요 {name} 님")

# 여러줄인 경우
question = st.text_area("궁금한 점을 전부 적어주세요", height=150)
if question:
    st.write(question)

## 4. 숫자 입력과 슬라이더
st.header("숫자 입력과 슬라이더")
age = st.number_input("나이", min_value=0, max_value=120, step=1)
top_k = st.slider("검색 결과를 몇개까지 볼까요?", min_value=1, max_value=20, value=5)

st.write(age, top_k)

## 5. 고르는 경우
st.header("고르는 경우")
fields = ["금융 분야", "공공기관", "의료 분야", "교육 분야"]

selected_field = st.selectbox("검색할 분야를 골라주세요", fields)
st.write("select 박스 선택 결과:", selected_field)

# 라디오 박스
answer_style = st.radio("답변 스타일", ['짧게', "보통", "자세히"], horizontal=True)
st.write("답변스타일: ", answer_style)

# 멀티 박스
picked_field = st.multiselect("관심 분야 여러개를 선택해주세요", fields, default=['의료 분야'])
st.write("관심 분야 리스트", picked_field)

# 6. 체크박스
st.header("체크박스")
show_detail = st.checkbox("자세한 설명 보기")

if show_detail:
    st.info("체크박스가 선택되엇습니다.")

# 조심해야할 부분
count = 1
count_button = st.button("버튼 클릭시 카운트가 올라갑니다")
if count_button:
    count += 1
st.write("카운트 개수는 : ", count)