import streamlit as st
import pandas as pd

st.set_page_config(
    page_title="스트림릿 처음 배우기",
    page_icon="😂",
    layout="centered"
)

debug_mode = False

df = pd.read_csv("../data/16-6_개인정보FAQ.csv")
field = df['적용분야내용'].unique().tolist()



# 1. 사이드바 만들어보기
st.sidebar.title("필터조건")
with st.sidebar:
    st.write("임시 사이드바")
    #멀티 셀렉트 만들거보기 - 복습
    picked_field = st.multiselect("분야", field, default=['의료 분야'])

    if debug_mode:
        print(picked_field) #디버깅 용

#. cloumn과 metric 만들어보기

st.header("컬럼과 메트릭")
col1, col2, col3 = st.columns(3)

with col1:
    st.subheader("첫번 째 컬럼")
    st.info("컬럼 다루기")
with col2:
    st.subheader("두번 째 컬럼")
    st.info("수치 정보 출력은 metric")
    st.metric("FQA 수", len(df))
with col3:
    st.subheader("세번 째 컬럼")
    st.metric("분야수",df['적용분야내용'].nunique())
    st.metric("평균 조회수 ", df['조회수'].mean())

st.divider()

left, right = st.columns([2,1])
with left:
    st.write("여기는 간격이 넓고, 더길게 쓰면 느껴지는 공간")
    st.info("이걸로 보면 더 쉽게 보여요")
with right:
    st.write("여기는 간격이 좁아요")
    st.info("이걸로 보면 더 쉽게 보이겠죠")

#3. expander - 접어두거나 펼치기 할떄
st.divider()
st.subheader("Expander")

for i in range(5):
    with st.expander(f"{['코드제목'][i]}"):
        st.markdown(f"{df['문제상황내용'][i]}")


#4. tabs - 같은 자리에 여려 면
st.subheader("탭 익혀보기")
tab_1, tab_2,= st.tabs(["처리상황단계내용", "조회수 상위 N개"])

with tab_1:
    st.dataframe(df[['처리상황단계내용']])
with tab_2:
    top5 = df.sort_values('조회수', ascending=False).head(5)
    st.dataframe(top5[['조회수']])
    st.dataframe(top5{["코드제목","조회수"]},with='streach',hide_index=True)

