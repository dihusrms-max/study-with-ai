# study-with-ai

HTML, CSS, 브라우저 JavaScript로 만든 정적 웹 학습 프로젝트입니다.

## 개발 경계

- **웹사이트:** `index.html`과 각 기능 페이지, `css/`, `js/`로 구성된 정적 HTML/JavaScript 사이트입니다. 서버나 Python 런타임 없이 브라우저에서 실행됩니다.
- **Python:** `pyproject.toml`, `src/`, `test.ipynb`는 Jupyter와 Python 학습을 위한 별도 환경입니다. 현재 웹사이트 기능과 Python 코드는 연결되어 있지 않습니다.
- **Node.js:** 외부 패키지·번들러·개발 서버는 사용하지 않습니다. Node.js는 프로젝트의 JavaScript 파일 문법을 검사하는 가벼운 검증 도구로만 사용합니다.

## 실행 방법

`index.html`을 브라우저에서 열어 자기소개 페이지와 기능 페이지를 확인합니다.

## JavaScript 문법 검사

의존성 설치 없이 다음 명령으로 `js/` 아래의 모든 JavaScript 파일 문법을 검사합니다.

```powershell
npm.cmd run check:js
```

PowerShell 실행 정책 때문에 `npm`이 실행되지 않으면 `npm.cmd`를 사용합니다.

## Python 학습 환경

프로젝트 Python 버전은 `.python-version`의 3.12를 기준으로 합니다.

```powershell
uv run python --version
```
