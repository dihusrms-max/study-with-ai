# Playwright로 뉴스 제목을 수집해 CSV로 저장

## 오늘 이해한 것

- 웹페이지 데이터 처리 흐름은 `Locator → 텍스트 추출 → DataFrame → CSV 저장`이다.
- `title_locator`는 웹 요소를 찾는 Locator이고, `titles`는 추출된 문자열 리스트다.
- `pd.DataFrame()`은 리스트·딕셔너리 데이터를 표 형태로 변환한다.
- `to_csv(..., index=False, encoding="utf-8-sig")`로 행 번호 없이 한글 CSV를 저장할 수 있다.

## 직접 해본 것

- 네이버 뉴스 검색 페이지에서 `a[data-heatmap-target=".tit"]`로 제목 요소를 선택했다.
- `all_text_contents()`로 제목 목록을 추출했다.
- 제목 목록을 `title` 열의 DataFrame으로 만들고 CSV로 저장했다.

## 헷갈렸던 것 / 복습할 것

- `.nth()`는 Locator에만 사용할 수 있고 문자열에는 사용할 수 없다.
- 저장 전에 `df.head()`, `df.shape`, `df.columns`로 데이터가 실제로 들어갔는지 확인한다.
- `total_data`가 비어 있으면 빈 CSV가 생성될 수 있다.
