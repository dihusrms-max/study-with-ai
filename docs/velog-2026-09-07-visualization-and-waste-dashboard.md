# Plotly로 폐기물 배출량을 시각화하고 대구광역시 이상치 원인 분석하기

## 들어가며

데이터를 집계한 뒤에는 그래프를 만드는 것만으로 분석이 끝나지 않는다. 그래프에서 눈에 띄는 지역이 있다면 그 원인을 다시 데이터로 확인해야 한다.

이번에는 전국 폐기물 배출업체 표준 데이터를 대상으로 다음 질문을 확인했다.

1. 제공기관별 총배출량이 가장 높은 지역은 어디인가?
2. 사업장 하나의 평균 배출량이 높은 지역은 어디인가?
3. 대구광역시의 총배출량이 높은 이유는 사업장 수 때문인가, 일부 대형 사업장 때문인가?

## Seaborn으로 기본 막대그래프 만들기

`barplot()`은 범주별 수치의 평균을 막대 높이로 표현한다.

```python
import seaborn as sns
import matplotlib.pyplot as plt

ax = sns.barplot(
    data=df,
    x="반",
    y="시험점수",
    errorbar=None,
    color="#4C78A8"
)

ax.set_title("반별 평균 시험점수")
ax.set_xlabel("반")
ax.set_ylabel("평균 시험점수")
ax.set_ylim(0, 100)
ax.grid(axis="y", linestyle="--", alpha=0.4)

for container in ax.containers:
    ax.bar_label(container, fmt="%.1f", padding=3)

plt.tight_layout()
plt.show()
```

`color`는 전체 막대 색상을 지정하고, `hue`가 있을 때 `palette`를 사용하면 그룹별 색상을 지정할 수 있다.

## Plotly 막대그래프와 값 표시

지역별 배출량처럼 집계된 결과를 대화형 그래프로 확인할 때는 Plotly Express를 사용할 수 있다.

```python
import plotly.express as px

fig = px.bar(
    data_frame=summary_df,
    x="제공기관명",
    y="총배출량",
    text_auto=".1f",
    title="제공기관별 총배출량",
    template="plotly_white"
)

fig.update_traces(
    textposition="outside",
    marker_color="#4C78A8"
)

fig.update_layout(
    width=900,
    height=500,
    title_x=0.5
)

fig.show()
```

`x`와 `y`에 컬럼명을 전달할 때는 어떤 DataFrame을 사용할지 `data_frame`으로 지정해야 한다.

## 사업장 단위로 먼저 집계하기

지역별 총배출량을 비교하기 전에 사업장별로 먼저 집계했다. 하나의 사업장이 여러 행으로 나뉘어 있을 수 있기 때문이다.

```python
business_df = (
    clean_df
    .dropna(subset=["제공기관명", "사업장명", "배출량"])
    .groupby(
        ["제공기관명", "사업장명"],
        as_index=False
    )
    .agg(
        사업장별배출량=("배출량", "sum")
    )
)
```

그 다음 사업장 단위 결과를 제공기관별로 다시 요약했다.

```python
region_summary_df = (
    business_df
    .groupby("제공기관명", as_index=False)
    .agg(
        총배출량=("사업장별배출량", "sum"),
        사업장수=("사업장명", "nunique"),
        사업장당평균=("사업장별배출량", "mean"),
        사업장당중앙값=("사업장별배출량", "median")
    )
)
```

총배출량만 비교하면 사업장 수가 많은 지역이 유리할 수 있다. 따라서 사업장당 평균과 중앙값을 함께 확인해야 한다.

## 대구광역시 사업장별 배출량 확인

대구광역시의 총배출량이 높게 나타나 대구 데이터를 별도로 확인했다.

```python
daegu_business_df = business_df[
    business_df["제공기관명"].str.contains("대구", na=False)
].copy()

daegu_business_df = daegu_business_df[
    daegu_business_df["사업장별배출량"] > 0
].copy()
```

배출량의 차이가 매우 큰 경우 로그 스케일 Boxplot을 사용하면 작은 값들이 모두 0 근처에 눌리는 문제를 줄일 수 있다.

```python
fig = px.box(
    daegu_business_df,
    y="사업장별배출량",
    points="all",
    hover_data=["사업장명"],
    title="대구광역시 사업장별 배출량 분포",
    template="plotly_white"
)

fig.update_yaxes(
    type="log",
    title="사업장별 배출량 · 로그 스케일"
)

fig.update_layout(
    width=700,
    height=500,
    title_x=0.5
)

fig.show()
```

Boxplot에서 대부분의 사업장은 낮은 구간에 있고 일부 점만 매우 높다면, 대구의 총배출량은 소수의 대형 사업장에 의해 증가했을 가능성이 있다.

상위 사업장도 함께 확인했다.

```python
top10_df = (
    daegu_business_df
    .nlargest(10, "사업장별배출량")
    .sort_values("사업장별배출량")
)

fig = px.bar(
    top10_df,
    x="사업장별배출량",
    y="사업장명",
    orientation="h",
    text="사업장별배출량",
    title="대구광역시 배출량 상위 10개 사업장",
    template="plotly_white"
)

fig.update_traces(
    texttemplate="%{text:,.0f}",
    textposition="outside"
)

fig.show()
```

## 대구광역시가 높은 이유를 나누어 보기

대구의 총배출량이 높다는 사실만으로는 원인을 알 수 없다. 다음 세 가지 경우를 구분해야 한다.

| 경우 | 총배출량 | 사업장 수 | 평균·중앙값 | 해석 |
| --- | --- | --- | --- | --- |
| 사업장 수 영향 | 높음 | 많음 | 보통 | 사업장 수가 많아서 총량이 높음 |
| 일부 대형 사업장 | 높음 | 보통 또는 낮음 | 평균만 높음 | 소수 사업장이 총량을 끌어올림 |
| 지역 전체 수준 높음 | 높음 | 보통 | 평균·중앙값 모두 높음 | 사업장 전반의 배출량이 높음 |

상위 10개 사업장이 전체에서 차지하는 비중도 계산할 수 있다.

```python
total_daegu = daegu_business_df["사업장별배출량"].sum()
top10_daegu = top10_df["사업장별배출량"].sum()

top10_ratio = top10_daegu / total_daegu * 100
print(f"대구 상위 10개 사업장 비중: {top10_ratio:.1f}%")
```

상위 10개 비중이 높으면 대구 전체를 동일하게 관리하기보다 상위 사업장 중심으로 원인을 조사하는 것이 효율적이다.

## 지역 단위를 먼저 맞춰야 한다

분석 중 다음과 같은 지역명이 함께 나타났다.

```text
대구광역시
대구 달서구
대구 중구
경기도 군포시
경기도 수원시
```

광역자치단체와 기초자치단체를 한 그래프에서 직접 비교하면 해석이 왜곡될 수 있다. `대구광역시`가 광역 단위 집계이고 `달서구·중구`가 하위 지역이라면 중복 집계 가능성도 확인해야 한다.

따라서 다음 중 하나를 기준으로 정해야 한다.

1. 광역자치단체끼리 비교
2. 기초자치단체끼리 비교
3. 사업장 실제 주소를 이용해 지역을 다시 분류

또한 `사업장폐기물`, `지정폐기물`, `의료폐기물`이 서로 독립된 분류인지 상·하위 분류인지도 확인해야 한다. 분류가 겹친다면 단순 합산 시 중복 계산이 발생할 수 있다.

## 분석 결과 해석

현재까지의 결과는 다음처럼 정리할 수 있다.

> 대구광역시는 총배출량이 높았지만, 사업장당 평균배출량이 가장 높은 지역과는 다를 수 있다. 따라서 대구의 높은 총량은 사업장 수와 일부 대형 사업장의 영향으로 나누어 확인해야 한다. 또한 광역·기초자치단체 단위가 섞여 있으므로 동일한 지역 단위로 재분석한 뒤 최종 결론을 내려야 한다.

이처럼 총량, 평균, 중앙값, 사업장 수를 함께 확인하면 단순한 지역 순위를 넘어 배출량이 높게 나타난 원인을 설명할 수 있다.

## 다음 단계: 분석 대시보드

분석 과정이 여러 그래프로 나뉘어 있어 결과를 한눈에 보기 어려웠다. 다음 단계에서는 하나의 대시보드에 아래 내용을 배치할 예정이다.

```text
전체 사업장 수 · 전체 배출량 · 제공기관 수 · 대구 배출량 비중
제공기관별 총배출량 Top 10
사업장당 평균·중앙값 비교
사업장 수와 총배출량 산점도
대구 사업장별 Boxplot
대구 폐기물 종류별 배출량
관찰·해석·활용·한계
```

대시보드는 그래프를 모아놓는 화면이 아니라, “대구가 왜 높은가?”라는 분석 질문에 답하는 요약 결과물로 구성해야 한다.
