# 대회 데이터 읽기 전용 구조 검사 보고서

- 검사일: 2026-09-11
- 입력: `C:\study-contests\data\open.zip`
- 원본 변경: 없음 (ZIP 내부 파일을 압축 해제하거나 수정하지 않음)

## 1. 파일 구성

- 전체 항목: 35개
- JSONL GZIP: 3개 / CSV: 3개 / JSON: 2개 / TXT: 24개

| 경로 | 압축 전 크기 | 형식 |
|---|---:|---|
| `README.md` | 7,176 bytes | 기타 |
| `baseline/requirements.txt` | 273 bytes | TXT |
| `baseline/script.py` | 24,507 bytes | 기타 |
| `data/test.jsonl.gz` | 133,965 bytes | JSONL.GZ |
| `data/법령패키지/법령/(계약예규) 공동계약운용요령.txt` | 44,425 bytes | TXT |
| `data/법령패키지/법령/(계약예규) 정부 입찰·계약 집행기준.txt` | 357,167 bytes | TXT |
| `data/법령패키지/법령/국가를 당사자로 하는 계약에 관한 법률 등의 재정경제부장관이 정하는 고시금액.txt` | 4,095 bytes | TXT |
| `data/법령패키지/법령/국가를 당사자로 하는 계약에 관한 법률 시행규칙.txt` | 253,770 bytes | TXT |
| `data/법령패키지/법령/국가를 당사자로 하는 계약에 관한 법률 시행령.txt` | 331,790 bytes | TXT |
| `data/법령패키지/법령/국가를 당사자로 하는 계약에 관한 법률.txt` | 51,478 bytes | TXT |
| `data/법령패키지/법령/소상공인기본법 시행령.txt` | 31,101 bytes | TXT |
| `data/법령패키지/법령/소상공인기본법.txt` | 29,231 bytes | TXT |
| `data/법령패키지/법령/소프트웨어 진흥법 시행령.txt` | 100,223 bytes | TXT |
| `data/법령패키지/법령/소프트웨어 진흥법.txt` | 88,410 bytes | TXT |
| `data/법령패키지/법령/중소 소프트웨어사업자의 사업 참여 지원에 관한 지침.txt` | 244,210 bytes | TXT |
| `data/법령패키지/법령/중소기업기본법 시행령.txt` | 91,044 bytes | TXT |
| `data/법령패키지/법령/중소기업기본법.txt` | 45,740 bytes | TXT |
| `data/법령패키지/법령/중소기업자간 경쟁제품 및 공사용자재 직접구매 대상 품목 지정 내역.txt` | 3,995 bytes | TXT |
| `data/법령패키지/법령/중소기업자간 경쟁제품 직접생산 확인기준.txt` | 175,177 bytes | TXT |
| `data/법령패키지/법령/중소기업제품 구매촉진 및 판로지원에 관한 법률 시행규칙.txt` | 125,248 bytes | TXT |
| `data/법령패키지/법령/중소기업제품 구매촉진 및 판로지원에 관한 법률 시행령.txt` | 113,231 bytes | TXT |
| `data/법령패키지/법령/중소기업제품 구매촉진 및 판로지원에 관한 법률.txt` | 101,444 bytes | TXT |
| `data/법령패키지/법령/지방자치단체 입찰 및 계약 집행기준.txt` | 803,014 bytes | TXT |
| `data/법령패키지/법령/지방자치단체 입찰시 낙찰자 결정기준.txt` | 921,863 bytes | TXT |
| `data/법령패키지/법령/지방자치단체를 당사자로 하는 계약에 관한 법률 시행규칙.txt` | 221,615 bytes | TXT |
| `data/법령패키지/법령/지방자치단체를 당사자로 하는 계약에 관한 법률 시행령.txt` | 342,537 bytes | TXT |
| `data/법령패키지/법령/지방자치단체를 당사자로 하는 계약에 관한 법률.txt` | 76,831 bytes | TXT |
| `data/법령패키지/중기부고시/중기부고시_경쟁제품_세부품명.csv` | 75,014 bytes | CSV |
| `data/법령패키지/중기부고시/중기부고시_경쟁제품_제2025-96호.hwpx` | 158,694 bytes | 기타 |
| `data/정답스키마_디코딩.json` | 13,751 bytes | JSON |
| `data/항목표.json` | 11,273 bytes | JSON |
| `dev.jsonl.gz` | 2,270,965 bytes | JSONL.GZ |
| `dev_labels.csv` | 28,044 bytes | CSV |
| `sample_submission.csv` | 1,018 bytes | CSV |
| `train_unlabeled.jsonl.gz` | 213,346,480 bytes | JSONL.GZ |

## 2. CSV 검사

### `data/법령패키지/중기부고시/중기부고시_경쟁제품_세부품명.csv`
- shape: `616 x 8`
- columns: 대분류번호, 대분류, 제품명번호, 제품명, 세부품명번호, 세부품명, 특이사항, 공사용자재직접구매
- dtype: {'대분류번호': 'float64', '대분류': 'str', '제품명번호': 'float64', '제품명': 'str', '세부품명번호': 'float64', '세부품명': 'str', '특이사항': 'str', '공사용자재직접구매': 'str'}
- missing: {'대분류번호': 1, '제품명번호': 1, '세부품명번호': 1, '특이사항': 431, '공사용자재직접구매': 256}
- duplicate rows: 0
- 앞뒤 공백 후보 컬럼: 없음

### `dev_labels.csv`
- shape: `200 x 49`
- columns: id, v1, v2, v3, v4, v5, v6, v7, v8, v9, v10, v11, v12, v13, v14, v15, v16, v17, v18, v19, v20, v21, v22, v23, v24, e1, e2, e3, e4, e5, e6, e7, e8, e9, e10, e11, e12, e13, e14, e15, e16, e17, e18, e19, e20, e21, e22, e23, e24
- dtype: {'id': 'str', 'v1': 'int64', 'v2': 'int64', 'v3': 'int64', 'v4': 'int64', 'v5': 'int64', 'v6': 'int64', 'v7': 'int64', 'v8': 'int64', 'v9': 'int64', 'v10': 'int64', 'v11': 'int64', 'v12': 'int64', 'v13': 'int64', 'v14': 'int64', 'v15': 'int64', 'v16': 'int64', 'v17': 'int64', 'v18': 'int64', 'v19': 'int64', 'v20': 'int64', 'v21': 'int64', 'v22': 'int64', 'v23': 'int64', 'v24': 'int64', 'e1': 'str', 'e2': 'str', 'e3': 'str', 'e4': 'str', 'e5': 'str', 'e6': 'str', 'e7': 'str', 'e8': 'str', 'e9': 'str', 'e10': 'float64', 'e11': 'float64', 'e12': 'str', 'e13': 'str', 'e14': 'str', 'e15': 'str', 'e16': 'float64', 'e17': 'str', 'e18': 'float64', 'e19': 'str', 'e20': 'float64', 'e21': 'str', 'e22': 'str', 'e23': 'str', 'e24': 'str'}
- missing: {'e1': 199, 'e2': 193, 'e3': 192, 'e4': 195, 'e5': 199, 'e6': 199, 'e7': 193, 'e8': 198, 'e9': 197, 'e10': 200, 'e11': 200, 'e12': 199, 'e13': 199, 'e14': 199, 'e15': 198, 'e16': 200, 'e17': 199, 'e18': 200, 'e19': 199, 'e20': 200, 'e21': 199, 'e22': 195, 'e23': 195, 'e24': 199}
- duplicate rows: 0
- 앞뒤 공백 후보 컬럼: 없음

### `sample_submission.csv`
- shape: `10 x 49`
- columns: id, v1, v2, v3, v4, v5, v6, v7, v8, v9, v10, v11, v12, v13, v14, v15, v16, v17, v18, v19, v20, v21, v22, v23, v24, e1, e2, e3, e4, e5, e6, e7, e8, e9, e10, e11, e12, e13, e14, e15, e16, e17, e18, e19, e20, e21, e22, e23, e24
- dtype: {'id': 'str', 'v1': 'int64', 'v2': 'int64', 'v3': 'int64', 'v4': 'int64', 'v5': 'int64', 'v6': 'int64', 'v7': 'int64', 'v8': 'int64', 'v9': 'int64', 'v10': 'int64', 'v11': 'int64', 'v12': 'int64', 'v13': 'int64', 'v14': 'int64', 'v15': 'int64', 'v16': 'int64', 'v17': 'int64', 'v18': 'int64', 'v19': 'int64', 'v20': 'int64', 'v21': 'int64', 'v22': 'int64', 'v23': 'int64', 'v24': 'int64', 'e1': 'float64', 'e2': 'float64', 'e3': 'float64', 'e4': 'float64', 'e5': 'float64', 'e6': 'float64', 'e7': 'float64', 'e8': 'float64', 'e9': 'float64', 'e10': 'float64', 'e11': 'float64', 'e12': 'float64', 'e13': 'float64', 'e14': 'float64', 'e15': 'float64', 'e16': 'float64', 'e17': 'float64', 'e18': 'float64', 'e19': 'float64', 'e20': 'float64', 'e21': 'float64', 'e22': 'float64', 'e23': 'float64', 'e24': 'float64'}
- missing: {'e1': 10, 'e2': 10, 'e3': 10, 'e4': 10, 'e5': 10, 'e6': 10, 'e7': 10, 'e8': 10, 'e9': 10, 'e10': 10, 'e11': 10, 'e12': 10, 'e13': 10, 'e14': 10, 'e15': 10, 'e16': 10, 'e17': 10, 'e18': 10, 'e19': 10, 'e20': 10, 'e21': 10, 'e22': 10, 'e23': 10, 'e24': 10}
- duplicate rows: 0
- 앞뒤 공백 후보 컬럼: 없음

## 3. JSONL 입력 구조 검사

### `data/test.jsonl.gz`
- rows: `10`
- top-level keys: anon_applied, assembly_policy_version, docs, dropped_doc_counts, id, input_completeness, meta
- id 결측: 0 / 중복 id: 0
- docs 개수 범위: `1 ~ 3`
- 문서 type 샘플: 공고문, 과업지시서, 규격서, 제안요청서
- meta key 수: 21

### `dev.jsonl.gz`
- rows: `200`
- top-level keys: anon_applied, assembly_policy_version, docs, dropped_doc_counts, id, input_completeness, meta
- id 결측: 0 / 중복 id: 0
- docs 개수 범위: `1 ~ 3`
- 문서 type 샘플: 공고문, 과업지시서, 규격서, 제안요청서
- meta key 수: 21

### `train_unlabeled.jsonl.gz`
- rows: `20,000`
- top-level keys: anon_applied, assembly_policy_version, docs, dropped_doc_counts, id, input_completeness, meta
- id 결측: 0 / 중복 id: 0
- docs 개수 범위: `1 ~ 35`
- 문서 type 샘플: 공고문, 과업지시서, 규격서, 제안요청서
- meta key 수: 21

## 4. 제출 형식 확인

- sample_submission shape: `10 x 49`
- sample_submission columns: id, v1, v2, v3, v4, v5, v6, v7, v8, v9, v10, v11, v12, v13, v14, v15, v16, v17, v18, v19, v20, v21, v22, v23, v24, e1, e2, e3, e4, e5, e6, e7, e8, e9, e10, e11, e12, e13, e14, e15, e16, e17, e18, e19, e20, e21, e22, e23, e24
- dev_labels shape: `200 x 49`

## 5. 현재 판단과 다음 조치

- 입력 데이터는 JSONL GZIP이며, 한 레코드가 입찰공고 1건이다.
- `id`, `docs`, `meta`, `input_completeness`를 기준으로 입력 검사 코드를 먼저 만든다.
- `dev.jsonl.gz`와 `dev_labels.csv`를 이용해 로컬 형식 검증과 첫 Baseline 실행을 진행한다.
- `train_unlabeled.jsonl.gz`는 라벨이 없으므로 정답 데이터로 간주하지 않는다.
- 제출 파일 생성 전 `id` 보존, 행 수, 49개 컬럼, v1~v24 값 범위, e1~e24 근거 문구 규칙을 검증한다.
- 파일명에 한글이 포함된 일부 경로는 현재 콘솔에서 인코딩이 깨져 보일 수 있으므로, 코드에서는 ZIP 내부 실제 파일명을 자동 탐색하는 방식을 권장한다.
