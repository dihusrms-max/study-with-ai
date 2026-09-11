# 나라장터 DACON 작업 공간

## 폴더 사용 규칙

- `Guide`: 서버 및 개인 작업 환경 설치 가이드
- `data/raw`: 원본 ZIP·CSV. 직접 수정하지 않는다.
- `data/processed`: 전처리 결과
- `data/sample`: 빠른 테스트용 샘플 데이터
- `260911`: 날짜별 작업 기록과 임시 작업물
- `notebooks`: 탐색 분석 및 실험용 Notebook
- `src`: 재사용할 전처리·분석 코드
- `configs`: 경로와 실험 설정
- `outputs`: 예측 결과와 제출 파일
- `logs`: 실행 로그와 전후 검증 기록
- `tests`: 데이터·코드 검증

## 작업 순서

1. 원본은 `data/raw`에 보존한다.
2. 원본을 확인한 뒤 전처리 결과를 `data/processed`에 저장한다.
3. 제출 파일은 `outputs/submission_YYYYMMDD_v01.csv`처럼 버전을 붙인다.
4. 실행 전후 행 수, 컬럼 수, 결측치 변화를 `logs`에 기록한다.
5. 개인 PC의 V0 환경이 안정화된 뒤에만 GPU·서버 환경을 별도로 검토한다.
