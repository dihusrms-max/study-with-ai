from __future__ import annotations

import io
import json
import sys
import zipfile

import pandas as pd


sys.stdout.reconfigure(encoding="utf-8")
with zipfile.ZipFile("data/open.zip") as z:
    labels = pd.read_csv(io.BytesIO(z.read("dev_labels.csv")))
    table = json.loads(z.read("data/항목표.json"))["항목"]

print("항목별 양성 분포")
for i in range(1, 25):
    col = f"v{i}"
    print(
        f"{col}: positives={int(labels[col].sum()):2d}/{len(labels)} "
        f"({labels[col].mean():.1%}) | {table[col].get('항목명', '')}"
    )

labels["positive_count"] = labels.iloc[:, 1:25].sum(axis=1)
print("\n공고별 위반 수")
print(labels["positive_count"].value_counts().sort_index().to_string())
print("\n양성 항목 수가 많은 공고")
print(
    labels.sort_values("positive_count", ascending=False)[["id", "positive_count"]]
    .head(10)
    .to_string(index=False)
)
