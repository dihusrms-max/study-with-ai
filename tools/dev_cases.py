from __future__ import annotations

import gzip
import io
import json
import re
import sys
import zipfile

import pandas as pd


sys.stdout.reconfigure(encoding="utf-8")


FOCUS = {
    "v3": ["실적", "추정가격", "예산", "배수"],
    "v4": ["실적", "추정가격", "예산", "기관"],
    "v5": ["지역", "소재", "경기도", "서울"],
    "v14": ["중소기업", "소기업", "소상공인", "일반물품"],
    "v10": ["직접생산", "직생"],
    "v11": ["중소기업", "경쟁제품"],
    "v24": ["메타", "입력", "나라장터", "낙찰", "지역"],
}

with zipfile.ZipFile("data/open.zip") as z:
    labels = pd.read_csv(io.BytesIO(z.read("dev_labels.csv")))
    records = {}
    with gzip.open(io.BytesIO(z.read("dev.jsonl.gz")), "rt", encoding="utf-8") as f:
        for line in f:
            record = json.loads(line)
            records[record["id"]] = record

for column, terms in FOCUS.items():
    ids = labels.loc[labels[column] == 1, "id"].tolist()
    print(f"\n=== {column}: {len(ids)}건 ===")
    for record_id in ids:
        record = records[record_id]
        print(f"[{record_id}] meta={record.get('meta', {})}")
        seen = 0
        for document in record.get("docs", []):
            for sentence in re.split(r"(?<=[.!?다])\\s+|\\n+", document.get("text", "")):
                if any(term in sentence for term in terms):
                    print(" ", sentence.strip()[:280])
                    seen += 1
                    if seen >= 3:
                        break
            if seen >= 3:
                break
