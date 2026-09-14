from __future__ import annotations

import gzip
import io
import json
import re
import sys
import zipfile

import pandas as pd


sys.stdout.reconfigure(encoding="utf-8")
terms = ["실적", "배수", "추정가격", "사업예산", "예산", "제한경쟁", "특정"]
with zipfile.ZipFile("data/open.zip") as z:
    labels = pd.read_csv(io.BytesIO(z.read("dev_labels.csv")))
    records = {}
    with gzip.open(io.BytesIO(z.read("dev.jsonl.gz")), "rt", encoding="utf-8") as f:
        for line in f:
            record = json.loads(line)
            records[record["id"]] = record

for column in ("v3", "v4"):
    print(f"\n=== {column} 양성 사례 ===")
    for record_id in labels.loc[labels[column] == 1, "id"]:
        record = records[record_id]
        meta = record.get("meta", {})
        print(
            f"[{record_id}] 계약법={meta.get('적용계약법')} 업무={meta.get('업무구분')} "
            f"계약={meta.get('계약방법')} 추정가격={meta.get('입찰추정가격')} "
            f"조항={meta.get('조항호내용')}"
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
