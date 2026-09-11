# Pandas 명령어 사용 가이드

이 문서는 분석 기획을 실제 Pandas 코드로 옮길 때 사용하는 실전 참고서다. 명령어를 외우기 전에 **사용 목적과 결과 형태**를 먼저 확인한다.

## 1. 사용 전 기본 점검

```python
waste_df.head()
waste_df.shape
waste_df.columns
waste_df.info()
waste_df.dtypes
waste_df.isna().sum()
```

확인할 내용:

```text
행과 열의 개수
컬럼 이름
컬럼 자료형
결측치 개수
한 행이 의미하는 대상
```

메서드는 괄호가 있어야 실행된다.

```python
waste_df.info()      # 실행
waste_df.info        # 메서드 자체를 보여 줌
```

## 2. 원본 보존과 분석용 DataFrame

원본은 보존하고 복사본이나 목적별 DataFrame에서 작업한다.

```python
analysis_df = waste_df[
    ["사업장명", "제공기관명", "폐기물분류명", "배출량"]
].copy()
```

변수 역할을 이름에 드러내면 데이터 흐름을 추적하기 쉽다.

```text
waste_df          원본
analysis_df       분석에 필요한 컬럼만 선택
clean_df          정제한 데이터
summary_df        집계 결과
```

## 3. 컬럼과 행 선택

### 단일 컬럼

```python
waste_df["배출량"]
```

문자열 하나를 전달하며 결과는 `Series`다.

### 복수 컬럼

```python
waste_df[["사업장명", "제공기관명", "배출량"]]
```

컬럼 이름 리스트를 전달하며 결과는 `DataFrame`이다.

```text
단일 컬럼 → df["컬럼명"]
복수 컬럼 → df[["컬럼명1", "컬럼명2"]]
```

### 조건으로 행 선택

```python
waste_df[waste_df["배출량"] >= 1000]
```

### 조건과 컬럼을 함께 선택

```python
waste_df.loc[
    waste_df["배출량"] >= 1000,
    ["사업장명", "폐기물분류명", "배출량"]
]
```

### 여러 값 중 선택

```python
waste_df[
    waste_df["제공기관명"].isin(
        ["경기도 수원시", "경기도 군포시"]
    )
]
```

### 문자열 조건

```python
waste_df[
    waste_df["사업장명"].str.contains("병원", na=False)
]
```

## 4. 컬럼 추가·삭제·이름 변경

### 고정값 컬럼 추가

```python
analysis_df["데이터출처"] = "전국 폐기물 표준데이터"
```

### 계산값으로 컬럼 추가

```python
analysis_df["배출량_kg"] = analysis_df["배출량"] * 1000
```

### 조건으로 컬럼 추가

```python
analysis_df["배출량구분"] = analysis_df["배출량"].apply(
    lambda x: "고배출" if x >= 1000 else "일반"
)
```

### 컬럼 삭제

```python
clean_df = analysis_df.drop(
    columns=["데이터출처", "배출량_kg"]
)
```

`drop()`은 결과를 반환하므로 재할당해야 하며, 원본은 유지된다. `del df["컬럼"]`은 원본 DataFrame을 직접 변경하므로 사용 목적을 먼저 확인한다.

### 컬럼 이름 변경

```python
clean_df = analysis_df.rename(
    columns={"배출량": "배출량_톤"}
)
```

## 5. 결측치·중복·자료형

```python
analysis_df.isna().sum()       # 컬럼별 결측치 개수
analysis_df.dropna(            # 필요한 컬럼 기준 결측 행 제거
    subset=["제공기관명", "배출량"]
)
analysis_df["배출량"].fillna(0)  # 결측치를 0으로 대체
analysis_df.duplicated().sum()   # 중복 행 개수
analysis_df.drop_duplicates()     # 완전히 같은 행 제거
```

중복 기준은 분석 목적에 맞게 정한다. `drop_duplicates(subset="제공기관명")`은 같은 지역의 다른 사업장 기록까지 제거할 수 있으므로 지역별 총량 계산에는 부적절하다.

```python
analysis_df["배출량"] = pd.to_numeric(
    analysis_df["배출량"],
    errors="coerce"
)
analysis_df["배출량"].isna().sum()  # 변환 후 생긴 결측치 확인
```

## 6. 정렬과 상위·하위 값

```python
analysis_df.sort_values(
    "배출량",
    ascending=False
)
```

```python
analysis_df.nlargest(10, "배출량")
analysis_df.nsmallest(10, "배출량")
```

여러 컬럼 기준 정렬:

```python
analysis_df.sort_values(
    by=["제공기관명", "배출량"],
    ascending=[True, False]
)
```

`sort_values()`는 컬럼 값을 기준으로 정렬하고, `sort_index()`는 행 인덱스를 기준으로 정렬한다.

## 7. 그룹별 집계

```python
region_sum_df = (
    analysis_df
    .groupby("제공기관명", as_index=False)["배출량"]
    .sum()
    .sort_values("배출량", ascending=False)
)
```

복수 기준 집계:

```python
region_category_df = (
    analysis_df
    .groupby(
        ["제공기관명", "폐기물분류명"],
        as_index=False
    )["배출량"]
    .sum()
)
```

여러 집계를 한 번에 계산:

```python
region_summary_df = (
    analysis_df
    .groupby("제공기관명")
    .agg(
        총배출량=("배출량", "sum"),
        평균배출량=("배출량", "mean"),
        중앙배출량=("배출량", "median"),
        사업장수=("사업장명", "count")
    )
    .reset_index()
)
```

## 8. 피벗·긴 형태·병합

```python
table_df = analysis_df.pivot_table(
    index="제공기관명",
    columns="폐기물분류명",
    values="배출량",
    aggfunc="sum",
    fill_value=0
)
```

피벗 테이블을 세로형으로 바꾸기:

```python
melt_df = table_df.reset_index().melt(
    id_vars="제공기관명",
    var_name="폐기물분류명",
    value_name="배출량"
)
```

두 집계 결과를 공통 컬럼으로 연결하기:

```python
merged_df = pd.merge(
    region_sum_df,
    region_count_df,
    on="제공기관명",
    how="left"
)
```

## 9. 여러 정제 작업을 묶은 함수

URL, 이메일, 특수문자, 불필요한 공백을 여러 번 반복해서 처리해야 한다면 정제 순서를 하나의 함수로 묶어 재사용할 수 있다.

```python
import re
import pandas as pd


def clean_text(value):
    """문자열에서 URL·이메일·특수문자를 제거하고 공백을 정리한다."""
    if pd.isna(value):
        return value

    text = str(value)

    # 1) URL 제거: https://..., http://..., www....
    text = re.sub(r"https?://\S+|www\.\S+", "", text)

    # 2) 이메일 제거
    text = re.sub(r"[\w.+-]+@[\w-]+\.[\w.-]+", "", text)

    # 3) 한글·영문·숫자·공백을 제외한 특수문자 제거
    text = re.sub(r"[^가-힣A-Za-z0-9\s]", "", text)

    # 4) 여러 공백을 하나로 바꾸고 양끝 공백 제거
    return re.sub(r"\s+", " ", text).strip()
```

문자열 컬럼 전체에 적용할 때는 `Series.apply()`를 사용한다. 원본을 보존하려면 결과를 새 컬럼이나 복사한 DataFrame에 저장한다.

```python
clean_df = analysis_df.copy()
clean_df["내용_정제"] = clean_df["내용"].apply(clean_text)
```

예상 결과:

```python
clean_text("  문의: test@example.com https://example.com !!! 데이터  분석  ")
# "문의 데이터 분석"
```

정제 순서가 중요하다. URL과 이메일을 먼저 제거하지 않으면 `:`, `/`, `@`, `.` 등이 특수문자 제거 단계에서 남아 의도하지 않은 문자열이 만들어질 수 있다. 또한 업무상 필요한 하이픈, 괄호, 소수점까지 제거할 수 있으므로 특수문자 허용 범위는 분석 목적에 맞게 조정한다.

## 10. 실행 후 필수 검증

데이터를 바꾼 뒤에는 결과를 확인한다.

```python
result_df.shape
result_df.columns
result_df.head()
result_df.isna().sum()
```

정제 전후 행 개수도 비교한다.

```python
print("변경 전:", analysis_df.shape)
print("변경 후:", clean_df.shape)
```

집계 결과에서는 다음을 확인한다.

```text
그룹 기준 컬럼이 남아 있는가?
계산한 컬럼 이름이 예상과 같은가?
행 개수가 그룹 수와 맞는가?
집계 함수가 분석 질문에 맞는가?
```

## 11. 명령어 선택 기준

```text
한 항목만 필요하다 → 단일 컬럼 선택
여러 항목이 필요하다 → 복수 컬럼 선택
조건에 맞는 기록이 필요하다 → 행 필터링
새 기준이나 계산값이 필요하다 → 컬럼 추가
분석에 불필요한 항목이다 → 컬럼 삭제
전체 양을 알고 싶다 → sum()
평균적인 값을 알고 싶다 → mean()
극단값 영향을 줄이고 싶다 → median()
그룹별 비교가 필요하다 → groupby()
행·열 교차 요약이 필요하다 → pivot_table()
두 표를 연결해야 한다 → merge()
```

## 변경 기록

- 2026-09-07: 목적 중심 Pandas 명령어, 컬럼·행 선택, 컬럼 조작, 정제·집계·검증 예시 작성
- 2026-09-11: URL·이메일·특수문자·공백 처리를 하나의 정제 함수로 묶는 방법과 적용 시 주의사항 추가
