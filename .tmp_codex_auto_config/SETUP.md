# DACON Codex 자동진행 설정 — 설치 가이드

## 구성 파일

1. `config.toml`
   - `%USERPROFILE%\.codex\config.toml`
2. `AGENTS.md`
   - DACON repository root
3. `rules/default.rules`
   - `%USERPROFILE%\.codex\rules\default.rules`

## 적용 순서

### 1. 기존 설정 백업

```powershell
Copy-Item "$env:USERPROFILE\.codex\config.toml" "$env:USERPROFILE\.codex\config.toml.bak" -ErrorAction SilentlyContinue
```

기존 `AGENTS.md`가 있다면 덮어쓰지 말고 Autonomous Execution Policy 내용을 병합한다.

### 2. config.toml 적용

핵심:

```toml
approval_policy = "on-request"
approvals_reviewer = "auto_review"
sandbox_mode = "workspace-write"
```

`approval_policy = "never"`와 `danger-full-access`는 사용하지 않는다.

### 3. AGENTS.md 적용

Repository root에 둔다.

목적:
- routine 단계마다 "다음?"을 묻지 않음
- 구현 → 테스트 → 수정 → 검증을 연속 수행
- Student merge / baseline overwrite / Gold·Dataset 수정 / submission / budget 증가 등에서만 멈춤

### 4. default.rules 적용

Read-only Git 조회만 `allow`.
`git push`, `merge`, `rebase`, `reset --hard`, `clean`은 `prompt`.

`python`, `pytest`, `powershell` 전체를 allow하지 않는다.
그렇게 하면 샌드박스 밖 임의 코드 실행 범위를 너무 넓힐 수 있다.

### 5. 규칙 테스트

```powershell
codex execpolicy check --pretty --rules "$env:USERPROFILE\.codex\rules\default.rules" -- git status
```

예상: `allow`

```powershell
codex execpolicy check --pretty --rules "$env:USERPROFILE\.codex\rules\default.rules" -- git push
```

예상: `prompt`

### 6. Codex 재시작

설정 파일과 rules는 Codex 재시작 후 확인한다.

## 기대 동작

자동/저마찰:
- workspace 내부 파일 읽기/수정
- routine 테스트/validator
- ordinary code fixes
- read-only Git inspection
- 승인된 실험 범위의 다음 단계 진행

여전히 검토 가능:
- sandbox 밖 쓰기
- 외부 네트워크가 필요한 shell 명령
- remote Git mutation
- 보안/credential 변경
- destructive operation
- 조직 정책이 강제하는 승인

## Gemma API

기본 설정은 `network_access = false`로 유지한다.
외부 네트워크가 필요한 Gemma API 실행은 필요 시 권한 상향 요청이 발생할 수 있고,
Auto-review가 eligible한 저위험 요청을 검토하게 둔다.

실제 운영에서 Gemma 호출마다 계속 수동 승인이 반복된다면
그때 네트워크 정책만 별도로 조정한다.
처음부터 전역 outbound network를 열지 않는다.

## 계속 "다음?"을 묻는 경우

- Codex 완전 재시작 확인
- repository root 실행 확인
- root `AGENTS.md` 확인
- 상위/하위 `AGENTS.md` 충돌 확인
- workflow 질문과 permission approval을 구분

permission approval → config/rules 문제
"계속할까요?" → AGENTS/instruction 문제
