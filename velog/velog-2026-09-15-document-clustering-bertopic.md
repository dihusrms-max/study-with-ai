# 문서 임베딩으로 뉴스 군집화하고 BERTopic으로 토픽 추출하기

## 들어가며

고객 문의, 뉴스, 리뷰처럼 정답 라벨이 없는 문서가 많을 때는 문서의 의미를 벡터로 변환한 뒤 유사한 문서끼리 묶어 데이터의 주제 구조를 탐색할 수 있다. 이번 학습에서는 뉴스 문서를 대상으로 임베딩, KMeans·DBSCAN 군집화, BERTopic 토픽 모델링을 실습했다.

## 문장 임베딩

문장 임베딩은 문서의 의미를 숫자 벡터로 변환하는 과정이다. 단어가 정확히 같지 않더라도 의미가 비슷한 문서는 벡터 공간에서 가까워질 수 있다.

```python
from sentence_transformers import SentenceTransformer

model = SentenceTransformer("dragonkue/BGE-m3-ko", device="cpu")
doc_vecs = model.encode(
    data["정제본문"].tolist(),
    normalize_embeddings=True,
    batch_size=4,
)
```

`normalize_embeddings=True`를 사용하면 벡터 크기를 정규화해 문서 간 유사도 비교에 활용하기 좋다.

## KMeans로 문서 묶기

KMeans는 미리 정한 군집 수 `k`를 기준으로 문서를 묶는다.

```python
from sklearn.cluster import KMeans

km = KMeans(n_clusters=2, random_state=42, n_init=10)
data["군집"] = km.fit_predict(doc_vecs)
```

KMeans에서는 군집 수를 임의로 정하지 않기 위해 여러 `k`를 비교한다. 엘보우 방법은 `inertia`의 감소 폭을 확인하고, 실루엣 점수는 군집 내부의 응집도와 군집 간 분리 정도를 함께 평가한다.

```python
from sklearn.metrics import silhouette_score

scores = []
for k in range(2, 9):
    labels = KMeans(n_clusters=k, random_state=42, n_init=10).fit_predict(doc_vecs)
    scores.append(silhouette_score(doc_vecs, labels))
```

다만 점수가 높다는 이유만으로 군집의 의미가 자동으로 보장되는 것은 아니다. 실제 문서 내용을 읽고 군집이 업무적으로 해석 가능한지도 확인해야 한다.

## DBSCAN과 이상치 문서

DBSCAN은 군집 수를 미리 지정하지 않고, 가까운 문서가 충분히 모인 영역을 군집으로 만든다. 어느 군집에도 속하기 어려운 문서는 `-1`로 표시되어 이상치처럼 확인할 수 있다.

```python
from sklearn.cluster import DBSCAN

labels = DBSCAN(
    eps=0.45,
    min_samples=3,
    metric="cosine",
).fit_predict(doc_vecs)
```

문서 임베딩에서는 코사인 거리를 사용하는 경우가 많지만, `eps`와 `min_samples`에 따라 군집 수와 이상치 수가 크게 달라질 수 있다.

## BERTopic의 흐름

BERTopic은 다음 과정을 연결해 토픽을 추출한다.

1. 문서 임베딩
2. UMAP을 이용한 차원 축소
3. HDBSCAN을 이용한 군집화
4. c-TF-IDF를 이용한 토픽 대표어 추출

c-TF-IDF는 같은 토픽의 문서를 하나의 큰 문서처럼 보고, 다른 토픽과 구별되는 단어를 대표어로 찾는 방식이다.

```python
from bertopic import BERTopic

topic_model = BERTopic(
    embedding_model=embedder,
    vectorizer_model=vectorizer,
    umap_model=umap_model,
    hdbscan_model=hdbscan_model,
    top_n_words=8,
)

topics, _ = topic_model.fit_transform(docs)
info = topic_model.get_topic_info()
```

한국어 문서에서는 형태소 분석기와 불용어 설정이 토픽 품질에 영향을 준다. Kiwi를 이용해 명사·동사·형용사·외국어 등을 선택하고, `기자`, `뉴스`, `사진`처럼 구분에 도움이 적은 단어를 제거했다.

## 배운 점과 한계

문서 군집화는 알고리즘이 정답을 알려주는 과정이 아니라, 임베딩 결과를 바탕으로 데이터의 구조를 탐색하고 사람이 의미를 해석하는 과정이다. 군집 수, 차원 축소 파라미터, 최소 군집 크기, 불용어 기준에 따라 결과가 달라지므로 결과를 그대로 사실처럼 받아들여서는 안 된다.

다음 단계에서는 BERTopic 결과를 사람이 평가하고, 각 토픽의 대표 문서와 대표어가 실제 주제를 잘 설명하는지 확인할 예정이다.

