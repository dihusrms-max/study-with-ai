from __future__ import annotations

import gzip
import io
import json
import re
import sys
import zipfile

import pandas as pd


sys.stdout.reconfigure(encoding="utf-8")
terms = ["직접생산", "직생", "중소기업", "중기간", "경쟁제품", "세부품명"]
with zipfile.ZipFile("data/open.zip") as z:
    labels = pd.read_csv(io.BytesIO(z.read("dev_labels.csv")))
    records = {}
    with gzip.open(io.BytesIO(z.read("dev.jsonl.gz")), "rt", encoding="utf-8") as f:
        for line in f:
            record = json.loads(line)
            records[record["id"]] = record

for column in ("v10", "v11"):
    print(f"\n=== {column} 양성 사례 ===")
    for record_id in labels.loc[labels[column] == 1, "id"]:
        record = records[record_id]
        meta = record.get("meta", {})
        print(
            f"[{record_id}] 업무={meta.get('업무구분')} 계약={meta.get('계약방법')} "
            f"추정가격={meta.get('입찰추정가격')} 품명={meta.get('세부품명번호목록')} "
            f"지역={meta.get('지역제한여부')} 조항={meta.get('조항호내용')}"
        )
        found = 0
        for document in record.get("docs", []):
            for line in re.split(r"\n+", document.get("text", "")):
                line = " ".join(line.split())
                if line and any(term in line for term in terms):
                    print("  ", line[:240])
                    found += 1
                    if found >= 5:
                        break
            if found >= 5:
                break
