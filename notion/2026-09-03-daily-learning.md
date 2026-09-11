# 2026-09-03 일일 학습 보고

## 오늘 새롭게 이해한 것

- 동적 웹페이지의 데이터 처리 흐름은 `Locator → 텍스트 추출 → DataFrame 생성 → CSV 저장 → 저장 결과 확인`이다.
- Playwright의 Locator는 웹 요소를 가리키는 객체이고, `all_text_contents()`의 결과는 문자열 리스트다.
- `pd.DataFrame()`은 리스트 또는 딕셔너리 데이터를 표 형태로 바꾸며, `to_csv()`와 `read_csv()`로 파일 저장과 확인을 할 수 있다.
- `index=False`는 자동 행 번호를 제외하고, `encoding="utf-8-sig"`는 Excel에서 한글이 깨질 가능성을 줄인다.

## 아직 애매하거나 복습할 것

- Locator와 문자열의 역할을 혼동하지 않기: `.nth()`는 Locator에서만 사용한다.
- 수집 코드 실행 뒤 `total_data`가 실제로 채워졌는지, `df.head()`, `df.shape`, `df.columns`로 확인하기.
- 제목과 요약문을 같은 뉴스 카드 기준으로 안정적으로 묶는 selector 구조 이해하기.

## 직접 해본 것

- 네이버 뉴스 검색 페이지에서 `a[data-heatmap-target=".tit"]` 제목 요소를 선택했다.
- `all_text_contents()`로 뉴스 제목을 수집해 `title` 열의 DataFrame을 만들었다.
- CSV 저장 중 빈 DataFrame으로 인해 `EmptyDataError`가 발생할 수 있음을 확인했고, 저장 전 데이터 검증의 필요성을 이해했다.
- 개념 테스트로 Locator·문자열·DataFrame·CSV 저장 옵션의 역할을 설명해 봤다.

## 다음 학습 한 단계

- 제목뿐 아니라 같은 뉴스 카드의 요약문도 수집해 `title`, `content` 두 열의 CSV를 직접 완성한다.
