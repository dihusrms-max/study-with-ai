import json
from pathlib import Path

OUT = Path(r"C:\study-with-ai\contest_notebooks")
OUT.mkdir(exist_ok=True)

def nb(cells, title):
    return {
        "cells": [{"cell_type": kind, "metadata": {}, "source": src.splitlines(True), "outputs": [], "execution_count": None} for kind, src in cells],
        "metadata": {"kernelspec": {"display_name": "Python 3 (koneps-dacon)", "language": "python", "name": "python3"}, "language_info": {"name": "python", "version": "3.12.13"}, "title": title},
        "nbformat": 4, "nbformat_minor": 5,
    }

cells1 = [
    ("markdown", "# 대회 데이터 구조 확인\n\n원본 `data/open.zip`을 수정하거나 압축 해제하지 않고 파일 구성과 dev 데이터 구조를 확인한다."),
    ("code", "from pathlib import Path\nimport gzip, io, json, zipfile\nimport pandas as pd\n\nZIP_PATH = Path(r'C:/study-contests/data/open.zip')\nassert ZIP_PATH.exists(), ZIP_PATH\nprint(ZIP_PATH, ZIP_PATH.stat().st_size)") ,
    ("code", "with zipfile.ZipFile(ZIP_PATH) as z:\n    infos = z.infolist()\n    for info in infos:\n        print(f'{info.filename}\\t{info.file_size:,} bytes')\nprint('파일 수:', len(infos))"),
    ("code", "def load_jsonl_from_zip(zip_path, member, limit=None):\n    rows = []\n    with zipfile.ZipFile(zip_path) as z, z.open(member) as raw:\n        with gzip.GzipFile(fileobj=raw) as stream:\n            for line in stream:\n                if line.strip():\n                    rows.append(json.loads(line.decode('utf-8')))\n                    if limit and len(rows) >= limit:\n                        break\n    return rows\n\ndev = load_jsonl_from_zip(ZIP_PATH, 'dev.jsonl.gz')\nprint('dev rows:', len(dev))\nprint('top keys:', sorted(dev[0]))\nprint('first id:', dev[0]['id'])\nprint('docs:', len(dev[0]['docs']), 'meta keys:', len(dev[0]['meta']))"),
    ("code", "ids = [r['id'] for r in dev]\nprint('id 결측:', sum(not x for x in ids))\nprint('id 중복:', len(ids) - len(set(ids)))\nprint('docs 개수 분포:\n', pd.Series([len(r['docs']) for r in dev]).value_counts().sort_index())\nprint('문서 유형:', sorted({d['type'] for r in dev for d in r['docs']}))"),
    ("code", "with zipfile.ZipFile(ZIP_PATH) as z:\n    labels = pd.read_csv(io.BytesIO(z.read('dev_labels.csv')))\nprint(labels.shape)\nprint(labels.columns.tolist())\nprint('v 값:', sorted(set(labels.filter(regex=r'^v\\d+$').to_numpy().ravel())))\nprint('label id 중복:', labels['id'].duplicated().sum())"),
    ("markdown", "## 확인 결과 기록\n\n- 원본 ZIP은 읽기 전용으로 사용한다.\n- `dev.jsonl.gz`와 `dev_labels.csv`는 `id`로 대응한다.\n- 다음 단계는 `--mock` 실행과 제출 CSV 검증이다."),
]

cells2 = [
    ("markdown", "# Baseline Mock 실행\n\n모델 없이 입력 로딩, JSON 출력, `submission.csv` 생성과 형식 검증만 확인한다."),
    ("code", "from pathlib import Path\nimport shutil, zipfile\n\nZIP_PATH = Path(r'C:/study-contests/data/open.zip')\nWORK = Path(r'C:/study-contests/.work/mock_baseline')\nif WORK.exists():\n    shutil.rmtree(WORK)\n(WORK / 'data').mkdir(parents=True)\n(WORK / 'baseline').mkdir()\n\nwith zipfile.ZipFile(ZIP_PATH) as z:\n    members = ['data/test.jsonl.gz', 'data/항목표.json', 'data/정답스키마_디코딩.json', 'baseline/script.py']\n    for member in members:\n        target = WORK / member\n        target.parent.mkdir(parents=True, exist_ok=True)\n        target.write_bytes(z.read(member))\nprint('준비 완료:', WORK)"),
    ("code", "import os, subprocess, sys\n\nresult = subprocess.run([sys.executable, 'baseline/script.py', '--mock'], cwd=WORK, capture_output=True, text=True)\nprint('returncode:', result.returncode)\nprint(result.stdout)\nprint(result.stderr[-3000:])\nassert result.returncode == 0"),
    ("code", "import csv\n\nout = WORK / 'output' / 'submission.csv'\nprint('출력:', out, out.exists())\nwith out.open(encoding='utf-8', newline='') as f:\n    rows = list(csv.reader(f))\nprint('shape:', len(rows)-1, 'x', len(rows[0]))\nprint('header:', rows[0])\nassert len(rows[0]) == 49\nassert len(rows) == 11\nprint('MOCK_SUBMISSION_FORMAT_OK')"),
    ("markdown", "## 주의\n\n`--mock`은 모델의 정확도를 검증하지 않는다. 실제 추론은 평가 서버의 고정 모델·vLLM 환경이 필요하다. 이 Notebook은 로컬 형식과 실행 흐름만 확인한다."),
]

(OUT / '01_data_inspection.ipynb').write_text(json.dumps(nb(cells1, 'data inspection'), ensure_ascii=False, indent=2), encoding='utf-8')
(OUT / '02_baseline_mock.ipynb').write_text(json.dumps(nb(cells2, 'baseline mock'), ensure_ascii=False, indent=2), encoding='utf-8')
print(OUT)
