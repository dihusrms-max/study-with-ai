from __future__ import annotations

import io
import zipfile

import pandas as pd


with zipfile.ZipFile("data/open.zip") as z:
    labels = pd.read_csv(io.BytesIO(z.read("dev_labels.csv")))

groups = {
    "자격·금액·지역": [f"v{i}" for i in range(1, 9)],
    "문서·중소기업·SW": [f"v{i}" for i in range(9, 21)],
    "공동도급·설명회·메타": ["v21", "v22", "v23", "v24"],
}

print("그룹별 양성 분포")
for name, columns in groups.items():
    cells = int(labels[columns].sum().sum())
    rows = int((labels[columns].sum(axis=1) > 0).sum())
    print(f"{name}: {cells}개 양성 라벨, {rows}건의 공고")

columns = [f"v{i}" for i in range(1, 25)]
pairs = []
for index, first in enumerate(columns):
    for second in columns[index + 1 :]:
        count = int(((labels[first] == 1) & (labels[second] == 1)).sum())
        if count:
            pairs.append((count, first, second))

print("\n동시 양성 상위 항목")
for count, first, second in sorted(pairs, reverse=True)[:20]:
    print(f"{first}-{second}: {count}건")

print("\n우선 검토 항목의 양성 공고")
for column in ["v3", "v14", "v24", "v1", "v2", "v5", "v10", "v16", "v18", "v20"]:
    ids = ", ".join(labels.loc[labels[column] == 1, "id"].tolist())
    print(f"{column}: {ids}")
