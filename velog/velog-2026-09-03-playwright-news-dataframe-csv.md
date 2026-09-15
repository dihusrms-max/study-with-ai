# Playwright로 네이버 뉴스 제목을 수집하고 CSV로 저장하기

웹 크롤링 결과를 분석에 사용하려면 화면의 텍스트를 가져오는 것에서 끝나지 않고, 표 형태로 정리한 뒤 파일로 저장해야 한다. 이번에는 네이버 뉴스 검색 결과에서 뉴스 제목을 추출해 Pandas DataFrame으로 만들고 CSV로 저장하는 흐름을 구현했다.

## 전체 흐름

```text
검색 페이지 접속
→ Locator로 뉴스 제목 선택
→ 텍스트 목록 추출
→ DataFrame 생성
→ CSV 저장
→ CSV 다시 읽어 확인
```

## 뉴스 제목 Locator 만들기

```python
title_locator = page.locator('a[data-heatmap-target=".tit"]')
await run_pw(title_locator.first.wait_for(state="visible", timeout=10_000))
```

`title_locator`는 제목 텍스트 자체가 아니라, 브라우저 안의 제목 요소들을 가리키는 Playwright Locator다.

## 제목을 DataFrame으로 변환하기

`all_text_contents()`로 Locator에 해당하는 모든 제목을 문자열 리스트로 가져온다.

```python
titles = await run_pw(title_locator.all_text_contents())
titles = [title.strip() for title in titles if title.strip()]

df = pd.DataFrame({"title": titles})
```

## CSV 저장하기

```python
df.to_csv("real_madrid_news.csv", index=False, encoding="utf-8-sig")
```

`index=False`는 DataFrame의 자동 행 번호를 제외한다. `utf-8-sig`는 Excel에서 한글 CSV를 열 때 글자가 깨질 가능성을 줄인다.

## 저장 전에 빈 DataFrame 확인하기

수집 결과가 비어 있으면 열 정보도 없는 빈 CSV가 저장될 수 있고, 이를 `read_csv()`로 다시 읽을 때 `EmptyDataError`가 발생할 수 있다. 저장 전에 데이터가 실제로 수집됐는지 확인한다.

```python
if df.empty:
    print("수집된 뉴스가 없습니다.")
else:
    df.to_csv("real_madrid_news.csv", index=False, encoding="utf-8-sig")
```

`df.head()`, `df.shape`, `df.columns`도 함께 확인하면 데이터가 예상한 열과 행으로 구성됐는지 검증할 수 있다.

## 발생한 오류: 문자열에는 `.nth()`를 사용할 수 없다

```python
title = "레알 마드리드 뉴스"
title = title.nth(0)
```

`.nth()`는 여러 웹 요소 중 특정 순서를 고르는 Locator 메서드다. 위 코드에서 `title`은 문자열이므로 오류가 발생한다.

따라서 Locator와 텍스트 데이터는 이름부터 분리하는 편이 안전하다.

```python
title_locator = page.locator('a[data-heatmap-target=".tit"]')
target_title = title_locator.nth(0)
title_text = await run_pw(target_title.text_content())
```

## 마무리

웹 크롤링에서는 데이터가 추출됐는지 `df.head()`, `df.shape`, `df.columns`로 확인한 뒤 저장해야 한다. 이 과정을 거치면 웹페이지의 정보를 분석 가능한 CSV 데이터로 바꿀 수 있다.
