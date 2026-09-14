from __future__ import annotations

import gzip
import io
import json
import re
import sys
import zipfile

import pandas as pd


sys.stdout.reconfigure(encoding="utf-8")
terms = ["지역", "본점", "소재지", "중소기업", "소기업", "소상공인", "일반물품", "경쟁제품"]
with zipfile.ZipFile("data/open.zip") as z:
    labels = pd.read_csv(io.BytesIO(z.read("dev_labels.csv")))
    records = {}
    with gzip.open(io.BytesIO(z.read("dev.jsonl.gz")), "rt", encoding="utf-8") as f:
        for line in f:
            record = json.loads(line)
            records[record["id"]] = record

for column in ("v5", "v14"):
    print(f"\n=== {column} 양성 사례 ===")
    for record_id in labels.loc[labels[column] == 1, "id"]:
        record = records[record_id]
        meta = record.get("meta", {})
        print(
            f"[{record_id}] 계약법={meta.get('적용계약법')} 업무={meta.get('업무구분')} "
            f"계약={meta.get('계약방법')} 추정가격={meta.get('입찰추정가격')} "
            f"지역여부={meta.get('지역제한여부')} 지역={meta.get('제한지역코드목록')} "
            f"조항={meta.get('조항호내용')} 품명={meta.get('세부품명번호목록')}"
        )
        found = 0
        for document in record.get("docs", []):
            for line in re.split(r"\n+", document.get("text", "")):
                line = " ".join(line.split())
                if line and any(term in line for term in terms):
                    print("  ", line[:220])
                    found += 1
                    if found >= 4:
                        break
            if found >= 4:
                break
