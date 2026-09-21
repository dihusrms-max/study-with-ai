# Gomgom recovery candidate

이 후보 파이프라인은 팀 저장소의 `submit/` 아래에서 기준 제출 후보로 관리한다.

- `script.py`: 고정 LLM 판정·검색·근거문구 후처리
- `run_api.py`: Gemma API 검증용 어댑터
- `qualification_support.py`, `decision_support.py`: 자격·상품 보조 판정
- `response_protocol.py`: JSON 응답 및 근거문구 검증
- `methodology_repair.py`: 방법론 기준 보수 보정
- `실행_제출_안내.md`, `자가라벨링_방법론_적용보고서.md`: 실행·검토 문서

공고 원문, API 키, raw 응답, 예측 CSV는 저장소에 포함하지 않는다.
