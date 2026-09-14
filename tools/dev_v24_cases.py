from __future__ import annotations

import gzip
import io
import json
import re
import sys
import zipfile

import pandas as pd


sys.stdout.reconfigure(encoding="utf-8")
terms = ["계약방법", "낙찰방법", "낙찰하한율", "지역제한", "본점", "추정가격", "사업예산", "입찰방법"]
with zipfile.ZipFile("data/open.zip") as z:
    labels = pd.read_csv(io.BytesIO(z.read("dev_labels.csv")))
    records = {}
    with gzip.open(io.BytesIO(z.read("dev.jsonl.gz")), "rt", encoding="utf-8") as f:
        for line in f:
            record = json.loads(line)
            records[record["id"]] = record

for record_id in labels.loc[labels["v24"] == 1, "id"]:
    record = records[record_id]
    meta = record.get("meta", {})
    print(
        f"\n[{record_id}] meta: 계약={meta.get('계약방법')} 낙찰={meta.get('낙찰방법')} "
        f"하한율={meta.get('낙찰하한율')} 추정가격={meta.get('입찰추정가격')} "
        f"지역여부={meta.get('지역제한여부')} 지역={meta.get('제한지역코드목록')} "
        f"업종={meta.get('면허업종제한목록')}"
    )
    found = 0
    for document in record.get("docs", []):
        for line in re.split(r"\n+", document.get("text", "")):
            line = " ".join(line.split())
            if line and any(term in line for term in terms):
                print("  ", line[:240])
                found += 1
                if found >= 8:
                    break
        if found >= 8:
            break
