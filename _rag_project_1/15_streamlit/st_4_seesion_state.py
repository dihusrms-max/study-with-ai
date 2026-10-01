import streamlit as st

st.set_page_config(
    page_title="상태 관리 배우기",
    page_icon="😂",
    layout="centered"
)

# 테스트용
count = 1

if st.button("버튼 클릭 시 count +1"):
    count += 1
    st.write(count)

st.write(count)

# ssession_state를 이용한 상태 관리
if "count" not in st.session_state:
    st.session_state["count"] = 0

if st.button("세션 상태 관리 버튼 클릭 시 count +1"):
    st.session_state["count"] += 1
st.success(st.session_state["count"])

print(st.session_state)
st.text_input("별명", key="nickname")

if st.button("버튼 클릭 시 닉네임 출력"):
    st.write(st.session_state["nickname"])

# form - 위젯 -> 만질때마다 rerun 일어나는 상황
# 조건이 여러개인 경우 -> 한꺼번에 제출하도록 하자

st.header("form 익혀보기")
with st.form("폼데이터 채우기"):
    name = st.text_input("검색할 이름 입력해 주세요", placeholder="예) 홍길동")
    age = st.text_input("검색할 나이 입력해 주세요", placeholder="예) 18")
    field = st.text_input("검색할 분야 입력해 주세요", placeholder="예) 공공분야")
    submitted = st.form_submit_button("제출")

if submitted:
    st.success(f"입력한 이름은 {name}, 나이는 {age}, 분야는 {field} 입니다.")

# 실습해보기
# 레이아웃 잡아보기
# session_state에 적절한 정보를 담아서 저장해보세요
# form 다뤄보기

import streamlit as st

st.set_page_config(page_title="공부 기록", page_icon="📚")
st.title("공부 기록")


