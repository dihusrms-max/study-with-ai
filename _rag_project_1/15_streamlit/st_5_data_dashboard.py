import streamlit as st
import pandas as pd
import plotly.express as px


st.set_page_config(page_title="데이터 대시보드", page_icon="📊",layout="wide")

st.title("서울 상권 매출 대시 보드")

@st.cache_data
def load_data(path):
    df = pd.read_csv(path)
    return df
    

sales = load_data("../data/07-8_seoul_market_sales.csv")

tab_a, tab_b = st.tabs(["전체 데이터","시각화"])

with tab_a:
    st.subheader("전체 데이터")
    st.dataframe(sales.head(10))
    #구분선
    st.divider()
    st.subheader("상권 구분")
    #보고 싶은 상권만 보기
    market_area = sales['상권_구분_코드_명'].unique().tolist()
    picked_area = st.multiselect("상권 구분", market_area)
    #선택한 상권들만 보기
    sales[sales['상권_구분_코드_명'].isin(picked_area)].head()

with tab_b:
    services = sales['서비스_업종_코드_명'].unique().tolist()
    picked_services = st.multiselect("서비스 업종", services)
    #원하는 서비스 업종 코드 가져오기
    filtered = sales[sales['서비스_업종_코드_명'].isin(picked_services)].head()
    total_sales = filtered['당월_매출_금액'].sum()
    total_count = filtered['당월_매출_건수'].sum()

    #평균
    per_order_sales = total_sales / total_count

    col1, col2, col3 = st.columns(3)
    col1.metric("전체 판매 금액", f"{total_sales:,.0f}원")
    col2.metric("전체 판매 건수", f"{total_count:,}")
    col3.metric("평균 주문 금액", f"{per_order_sales:,.0f}원")

       # 간단한 바차트 그려보기
    rank = filtered.groupby("서비스_업종_코드_명", as_index=False)["당월_매출_금액"].sum().sort_values("당월_매출_금액", ascending=False).head(5)
    st.dataframe(rank)

    st.bar_chart(rank, 
                 x="서비스_업종_코드_명", 
                 y="당월_매출_금액")
   
    fig = px.bar(
        rank,
        x="당월_매출_금액",
        y="서비스_업종_코드_명",
        orientation="h",
        text="당월_매출_금액",
        title="당월 매출 상위 5개 업종",
        labels={
            "서비스_업종_코드_명": "업종",
            "당월_매출_금액": "당월 매출",
        },
        color="당월_매출_금액",
        color_continuous_scale="Blues",
    )

    fig.update_traces(
        texttemplate="%{text:,.0f}원",
        textposition="outside",
        cliponaxis=False,
    )

    fig.update_layout(
        xaxis_title="당월 매출 금액",
        yaxis_title="",
        coloraxis_showscale=False,
        margin=dict(l=20, r=40, t=60, b=20),
    )

    st.plotly_chart(fig, width='stretch')