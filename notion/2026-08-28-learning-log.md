# 2026.08.28 학습 기록 — 웹 프로젝트와 Git 형상관리

**태그:** `HTML/CSS/JavaScript` `Git` `GitHub` `VS Code` `웹 프로젝트`

## 오늘 새롭게 이해한 것

### 웹 프로젝트 구조

- 자기소개 페이지는 사이트의 허브로 두고, GIF 편집기·축구 게임·이상형 월드컵은 독립 페이지로 분리할 수 있다.
- 여러 페이지에 반복되는 색상, 글꼴, 헤더, 포커스 규칙은 `common.css`로 분리하면 유지보수가 쉬워진다.
- 공통 테마 동작은 `common.js`, 페이지별 동작은 각 전용 JavaScript 파일로 나누는 방식이 효율적이다.
- UI에서는 애니메이션보다 기본 콘텐츠가 항상 보이는 안정성이 우선이다. 첫 화면을 JavaScript 애니메이션에 의존하지 않도록 구성해야 한다.

### Git과 GitHub

- 기본 흐름은 `Changes → Stage → Commit → Push/Sync → Graph 확인`이다.
- Changes는 아직 커밋하지 않은 수정 파일, Staged Changes는 다음 커밋에 포함할 파일이다.
- Commit은 로컬 Git 기록 저장이고, Push/Sync는 GitHub 원격 저장소와 동기화하는 작업이다.
- 브랜치는 main을 안전하게 유지하면서 별도 작업을 하는 공간이다.
- 병합 전에는 main으로 전환해 기존 상태를 확인할 수 있고, 병합 후에는 Reset보다 Revert Commit으로 안전하게 되돌린다.

### 파일 관리

- `.gitignore`는 가상환경, 캐시, Jupyter 임시 파일, `.env`, 로그처럼 GitHub에 올리지 않을 파일을 제외한다.
- `.editorconfig`는 UTF-8과 LF 줄바꿈 같은 편집 규칙을 통일한다.
- `.gitattributes`는 텍스트와 이미지 파일을 Git이 일관되게 처리하도록 한다.

## 직접 해본 것

- HTML/CSS/JavaScript로 자기소개 페이지와 다크 테마 전환을 만들었다.
- GIF 업로드·형식/용량 검사·드래그 앤 드롭·로컬 미리보기 기능이 있는 GIF 편집기 프로토타입을 만들었다.
- Canvas와 키보드/모바일 이벤트를 사용한 30초 미니 축구 게임을 만들었다.
- 배열과 상태 관리를 사용한 8강 이상형 월드컵을 만들었다.
- VS Code Changes와 Graph에서 스테이징, 커밋, 원격 동기화 상태를 확인했다.
- `.gitignore`를 커밋하고 GitHub에 동기화했다.
- `chore/project-structure` 브랜치를 만들고 공통 CSS/JS, 문서 위치, 이미지 중복을 정리했다.

## Codex 협업 방식에서 배운 점

- Codex는 단순 코드 생성 도구가 아니라, 제안·구현·검토를 함께 하는 협업 도구로 활용했다.
- 사용자는 기능 목표, 구현 승인, 결과 검토, Git 병합 여부를 결정했다.
- Codex는 파일 구조 제안, 코드 구현, JavaScript 문법 검사, Git 상태 확인을 지원했다.
- `rules.prompt`를 통해 GPT는 자유롭게 실습하는 작업실, Notion은 핵심 학습을 남기는 장기 기록이라는 역할을 분리했다.
- GIF 편집기, 축구 게임, 이상형 월드컵은 모두 기능 범위를 먼저 정하고 승인한 뒤 구현했다.
- AI가 만든 결과도 UI 검토, 테스트, Git 변경사항 확인이 필요하다는 점을 배웠다.

## 개발 환경 구성

- OS: Windows
- uv: 0.12.6
- 시스템 Python: 3.14.7
- 프로젝트 Python: 3.12.14
- Node.js: v24.20.0
- npm: 12.0.2
- Git: 2.55.0.windows.5
- VS Code: 1.135.0

### 환경 관련 메모

- `.python-version`은 3.12이며 프로젝트 실행은 `uv run python` 또는 `.venv`를 기준으로 한다.
- 시스템 Python과 프로젝트 Python 버전이 다를 수 있으므로 프로젝트 명령은 실행 환경을 확인해야 한다.
- PowerShell에서 npm 실행이 막히는 경우 `npm.cmd` 또는 Command Prompt/Git Bash를 사용할 수 있다.

## 현재 결과물

```text
index.html                 자기소개 페이지
gif-editor.html            GIF 편집기 프로토타입
football-game.html         Canvas 미니 축구 게임
ideal-worldcup.html        이상형 월드컵
css/common.css             공통 스타일
js/common.js               공통 테마 로직
docs/                      학습 보고서와 Velog 원고
```

## Weakness Backlog

| 상태 | 항목 | 다음 행동 |
| --- | --- | --- |
| 🟡 | Pull Request와 main 병합 | 브랜치 변경사항을 GitHub에서 검토하고 병합하기 |
| 🟡 | Revert Commit 실제 사용 | 병합 후 안전하게 되돌리는 흐름 실습하기 |
| 🟡 | README와 인코딩 관리 | UTF-8 파일을 수정하고 의미 있는 커밋 만들기 |
| 🟡 | GIF 실제 편집 | 파일 교체와 크기 미리보기부터 직접 구현하기 |
| 🟡 | 직접 코드 수정 | CSS/JS 값을 직접 바꾸고 오류를 확인하기 |

## 다음 학습 행동

1. `chore/project-structure` 브랜치의 Pull Request를 만들고 main 병합 전 Graph를 확인한다.
2. 변경 파일을 직접 읽고 병합한다.
3. 병합 후 main과 origin/main이 같은 위치인지 확인한다.

## 성장 평가

- **이해:** 웹페이지 구조, Changes/Stage/Commit/Push/Graph/Branch의 역할을 설명할 수 있다.
- **실습:** 기능 페이지 제작, 커밋, 원격 동기화, 브랜치 생성과 구조 개선을 수행했다.
- **다음 목표:** Git 병합과 되돌리기를 직접 수행하고, 보조 없이 작은 기능을 수정해 커밋하는 습관을 만든다.
