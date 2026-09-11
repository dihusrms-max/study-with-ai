import csv
import gzip
import io
import json
import zipfile
from collections import Counter
from datetime import date
from pathlib import Path

import pandas as pd

ZIP_PATH = Path(r"C:\study-contests\data\open.zip")
OUT_PATH = Path(r"C:\study-with-ai\contest_data_inspection_20260911.md")

def read_jsonl(zf, name):
    records = []
    with zf.open(name) as raw:
        stream = gzip.GzipFile(fileobj=raw) if name.endswith('.gz') else raw
        for line in stream:
            if line.strip():
                records.append(json.loads(line.decode('utf-8')))
    return records

def csv_info(zf, name):
    with zf.open(name) as raw:
        data = raw.read()
    df = pd.read_csv(io.BytesIO(data))
    missing = df.isna().sum()
    dup = int(df.duplicated().sum())
    whitespace = []
    for col in df.select_dtypes(include=['object']).columns:
        s = df[col].dropna().astype(str)
        if bool(s.str.contains(r'^\s|\s$', regex=True).any()):
            whitespace.append(col)
    return {
        'name': name, 'rows': len(df), 'cols': len(df.columns),
        'columns': list(df.columns),
        'dtypes': {str(k): str(v) for k, v in df.dtypes.items()},
        'missing': {str(k): int(v) for k, v in missing.items() if v},
        'duplicate_rows': dup, 'whitespace_columns': whitespace,
        'head': df.head(2).to_dict(orient='records'),
    }

def jsonl_info(zf, name):
    rows = read_jsonl(zf, name)
    ids = [r.get('id') for r in rows]
    duplicate_ids = len(ids) - len(set(ids))
    doc_counts = [len(r.get('docs') or []) for r in rows]
    meta_keys = sorted({k for r in rows for k in (r.get('meta') or {}).keys()})
    return {
        'name': name, 'rows': len(rows), 'top_keys': sorted({k for r in rows for k in r.keys()}),
        'duplicate_ids': duplicate_ids, 'missing_ids': sum(x is None for x in ids),
        'docs_min': min(doc_counts) if doc_counts else 0, 'docs_max': max(doc_counts) if doc_counts else 0,
        'meta_keys': meta_keys,
        'sample_id': ids[0] if ids else None,
        'sample_doc_types': sorted({d.get('type') for r in rows[:20] for d in (r.get('docs') or [])}),
        'sample_meta_missing': sorted({k for r in rows[:20] for k,v in (r.get('meta') or {}).items() if v is None}),
    }

with zipfile.ZipFile(ZIP_PATH) as zf:
    infos = zf.infolist()
    names = [i.filename for i in infos]
    csvs = [n for n in names if n.lower().endswith('.csv')]
    jsonls = [n for n in names if n.lower().endswith('.jsonl.gz')]
    csv_reports = [csv_info(zf, n) for n in csvs]
    jsonl_reports = [jsonl_info(zf, n) for n in jsonls]
    json_files = []
    for n in names:
        if n.lower().endswith('.json'):
            obj = json.loads(zf.read(n).decode('utf-8'))
            json_files.append((n, type(obj).__name__, len(obj) if hasattr(obj, '__len__') else None, list(obj[0].keys()) if isinstance(obj, list) and obj and isinstance(obj[0], dict) else None))
    txts = [n for n in names if n.lower().endswith('.txt')]
    lines = []
    lines.append('# 대회 데이터 읽기 전용 구조 검사 보고서')
    lines.append('')
    lines.append(f'- 검사일: {date.today().isoformat()}')
    lines.append(f'- 입력: `{ZIP_PATH}`')
    lines.append('- 원본 변경: 없음 (ZIP 내부 파일을 압축 해제하거나 수정하지 않음)')
    lines.append('')
    lines.append('## 1. 파일 구성')
    lines.append('')
    lines.append(f'- 전체 항목: {len(infos)}개')
    lines.append(f'- JSONL GZIP: {len(jsonls)}개 / CSV: {len(csvs)}개 / JSON: {len(json_files)}개 / TXT: {len(txts)}개')
    lines.append('')
    lines.append('| 경로 | 압축 전 크기 | 형식 |')
    lines.append('|---|---:|---|')
    for i in infos:
        kind = 'JSONL.GZ' if i.filename.endswith('.jsonl.gz') else 'CSV' if i.filename.lower().endswith('.csv') else 'JSON' if i.filename.lower().endswith('.json') else 'TXT' if i.filename.lower().endswith('.txt') else '기타'
        lines.append(f'| `{i.filename}` | {i.file_size:,} bytes | {kind} |')
    lines.append('')
    lines.append('## 2. CSV 검사')
    lines.append('')
    for r in csv_reports:
        lines.append(f"### `{r['name']}`")
        lines.append(f"- shape: `{r['rows']:,} x {r['cols']}`")
        lines.append(f"- columns: {', '.join(map(str, r['columns']))}")
        lines.append(f"- dtype: {r['dtypes']}")
        lines.append(f"- missing: {r['missing'] or '없음'}")
        lines.append(f"- duplicate rows: {r['duplicate_rows']}")
        lines.append(f"- 앞뒤 공백 후보 컬럼: {r['whitespace_columns'] or '없음'}")
        lines.append('')
    lines.append('## 3. JSONL 입력 구조 검사')
    lines.append('')
    for r in jsonl_reports:
        lines.append(f"### `{r['name']}`")
        lines.append(f"- rows: `{r['rows']:,}`")
        lines.append(f"- top-level keys: {', '.join(r['top_keys'])}")
        lines.append(f"- id 결측: {r['missing_ids']} / 중복 id: {r['duplicate_ids']}")
        lines.append(f"- docs 개수 범위: `{r['docs_min']} ~ {r['docs_max']}`")
        lines.append(f"- 문서 type 샘플: {', '.join(r['sample_doc_types'])}")
        lines.append(f"- meta key 수: {len(r['meta_keys'])}")
        lines.append('')
    lines.append('## 4. 제출 형식 확인')
    lines.append('')
    sample = next((r for r in csv_reports if r['name'].endswith('sample_submission.csv')), None)
    labels = next((r for r in csv_reports if r['name'].endswith('dev_labels.csv')), None)
    if sample:
        lines.append(f"- sample_submission shape: `{sample['rows']} x {sample['cols']}`")
        lines.append(f"- sample_submission columns: {', '.join(map(str, sample['columns']))}")
    if labels:
        lines.append(f"- dev_labels shape: `{labels['rows']} x {labels['cols']}`")
    lines.append('')
    lines.append('## 5. 현재 판단과 다음 조치')
    lines.append('')
    lines.append('- 입력 데이터는 JSONL GZIP이며, 한 레코드가 입찰공고 1건이다.')
    lines.append('- `id`, `docs`, `meta`, `input_completeness`를 기준으로 입력 검사 코드를 먼저 만든다.')
    lines.append('- `dev.jsonl.gz`와 `dev_labels.csv`를 이용해 로컬 형식 검증과 첫 Baseline 실행을 진행한다.')
    lines.append('- `train_unlabeled.jsonl.gz`는 라벨이 없으므로 정답 데이터로 간주하지 않는다.')
    lines.append('- 제출 파일 생성 전 `id` 보존, 행 수, 49개 컬럼, v1~v24 값 범위, e1~e24 근거 문구 규칙을 검증한다.')
    lines.append('- 파일명에 한글이 포함된 일부 경로는 현재 콘솔에서 인코딩이 깨져 보일 수 있으므로, 코드에서는 ZIP 내부 실제 파일명을 자동 탐색하는 방식을 권장한다.')
    OUT_PATH.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print(OUT_PATH)
