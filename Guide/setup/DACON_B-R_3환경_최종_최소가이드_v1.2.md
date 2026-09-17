# DACON B-R 3환경 최소 셋업 가이드

## 핵심 원칙

```text
GitHub  = 팀 Source of Truth
Desktop = 공식 Dataset / Cache / Experiment Runtime
Notebook = Desktop 원격 개발 + 오프라인 sample 개발
Mobile  = 읽기 전용 상태 확인
```

공식 Dev200/2000 평가와 Gemma 실험은 Desktop 한 곳에서만 실행한다.

## Desktop — 공식 실험 Runtime

필수: Git, Python 또는 uv, OpenSSH Server, Tailscale, 현재 DACON 프로젝트.

관리자 PowerShell:

```powershell
Get-WindowsCapability -Online | Where-Object Name -like 'OpenSSH*'
Add-WindowsCapability -Online -Name OpenSSH.Server~~~~0.0.1.0
Start-Service sshd
Set-Service -Name sshd -StartupType Automatic
```

공유기 22번 포트는 포워딩하지 않는다. Notebook 접속은 Tailscale IP 또는 MagicDNS를 사용한다. 장시간 실험 중에는 전원 연결 상태의 절전 시간을 `없음(Never)`으로 설정한다.

## Notebook — Desktop 원격 개발

설치: Git, VS Code, VS Code Remote - SSH, Tailscale, uv.

```bash
tailscale status
ssh <Desktop사용자>@<Desktop-Tailscale-IP-또는-MagicDNS>
```

SSH 확인 후 VS Code의 `Remote-SSH: Connect to Host`로 Desktop의 DACON 프로젝트 폴더를 연다. Remote Terminal에서 `hostname`, `pwd`, `python --version`, `git status`를 확인한다. Python, Jupyter, pytest, Gemma runner는 Remote Terminal에서 실행한다.

## Notebook — Offline Fallback

Notebook에는 공식 Runtime 전체를 복제하지 않는다. `src/`, `tests/`, `prompts/`, `docs/`, `config/`, `data/sample/`만 유지하고 Full Dataset, 공식 Gemma Cache, Experiment Registry, Runtime State, Full Dev200/2000 outputs는 복제하지 않는다.

```bash
git switch -c offline/my-change
uv sync
pytest
```

Offline 점수는 공식 결과로 취급하지 않는다. 연결 복구 후 `Notebook commit/push → Desktop pull/merge → Desktop 공식 재검증` 순서로 진행한다.

## Python 환경 — uv

이미 `pyproject.toml`이 있으면 `uv init`을 실행하지 않는다.

```bash
python --version
uv python pin <현재_사용중인_Python버전>
uv sync
```

`pyproject.toml`, `uv.lock`, `.python-version`은 GitHub에 포함한다.

## Mobile — 읽기 전용 관제

`127.0.0.1`은 Mobile에서 직접 접근할 수 없다. Desktop Dashboard가 `http://127.0.0.1:8000`에서 실행 중이면 Desktop에서 다음을 실행한다.

```bash
tailscale serve --bg 8000
tailscale serve status
```

Mobile은 Tailscale의 tailnet 전용 HTTPS 주소로 접속한다. Funnel과 인터넷 직접 공개는 사용하지 않는다. 초기에는 Dashboard를 `READ ONLY`로 운영하며 Pause/Resume/Stop 기능은 인증·권한 검증 후에만 활성화한다.

## GitHub 공유 경계

공유: `src/`, `prompts/`, `tests/`, `docs/`, `config/`, `pyproject.toml`, `uv.lock`, `.python-version`, `reports/`

공유하지 않음: `.env`, API Key, Gemma raw cache, Runtime State, 대용량 outputs, 실행 중 DB, Full Dataset.

## 완료 조건

- [ ] Desktop 프로젝트 정상 실행 및 절전 방지
- [ ] OpenSSH 자동 시작
- [ ] Desktop ↔ Notebook Tailscale/SSH 연결
- [ ] VS Code Remote SSH 접속
- [ ] Remote Python/Git 정상
- [ ] GitHub push/pull 정상
- [ ] Notebook Offline sample test 정상
- [ ] SSH 종료 후 Desktop 실험 지속
- [ ] Mobile Dashboard 읽기 가능
- [ ] `.env` / API Key Git 제외
- [ ] Experiment Registry/State 백업 경로 존재

> 코드는 GitHub에서 공유하고, 공식 실험은 Desktop 한 곳에서만 실행하며, Notebook은 Desktop을 원격 개발하고 Mobile은 읽기 전용으로 관제한다.
