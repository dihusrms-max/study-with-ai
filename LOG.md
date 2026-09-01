# 정적 웹 프로젝트 리팩터링 회고

> 기록 범위: 프로젝트 구조 정리, CSS 책임 분리, GIF 프로토타입 안정화, 공통 헤더 통일

## 1. 작업 목표

처음에는 자기소개 페이지와 기능 프로토타입이 빠르게 추가되면서, 공통 스타일과 페이지별 스타일의 경계가 흐려지고 일부 화면의 사용 흐름이 끊기는 문제가 있었다. 이번 작업의 목표는 기능을 더 추가하는 것이 아니라 다음 네 가지 기반을 안정화하는 것이었다.

1. 웹·Python·Node.js의 역할을 분리한다.
2. 디자인 토큰과 페이지 전용 스타일의 책임을 분리한다.
3. GIF 업로드·교체 과정에서 발생하는 폼과 파일 처리 버그를 해결한다.
4. 어느 페이지에서도 같은 내비게이션 경험을 제공한다.

---

## 2. 1단계 — 프로젝트 경계와 가벼운 검증 체계 확정

### 결정한 구조

- 웹사이트는 HTML, CSS, 브라우저 JavaScript만으로 동작하는 정적 사이트다.
- Python과 Jupyter 파일은 별도의 학습 환경이며, 현재 웹 기능과 연결하지 않는다.
- Node.js는 번들러·개발 서버·무거운 의존성 설치에 사용하지 않고, JavaScript 문법 검사에만 사용한다.

이 기준은 `README.md`에 기록했다. 또한 `package.json`에는 의존성 없이 실행되는 검사 명령만 둔다.

```json
{
  "scripts": {
    "check:js": "node tools/check-js.mjs"
  }
}
```

`tools/check-js.mjs`는 `js/` 폴더를 순회하며 각 파일에 `node --check`를 실행한다. 설치 과정이나 잠금 파일을 만들지 않으면서, 문법 오류를 빠르게 발견할 수 있다.

```powershell
npm.cmd run check:js
```

PowerShell 실행 정책으로 `npm` 명령이 막힐 수 있어 `npm.cmd` 사용 방법도 함께 문서화했다.

### 배운 점

작은 정적 웹 프로젝트라고 해도 실행 환경의 경계를 먼저 정해 두면, 나중에 Python 코드나 Node 도구가 서로의 책임을 침범하는 일을 막을 수 있다. 도구는 많을수록 좋은 것이 아니라, 현재 문제를 해결하는 최소한의 도구가 좋다.

---

## 3. 2단계 — CSS 책임 분리

### 문제: 공통 토큰이 두 파일에 중복됨

기존에는 `common.css`와 `style.css`가 모두 `:root` 색상 변수를 선언했다. 같은 값처럼 보여도 나중에 한쪽만 수정하면 페이지별 색상·간격이 달라질 수 있다. `--background`와 `--bg`처럼 같은 의미의 별칭도 함께 존재했다.

### 해결: 전역 토큰은 `global.css` 한 곳으로 이동

`common.css`를 `global.css`로 정리하고, 다음 요소를 단일 책임으로 모았다.

- 다크·라이트 테마 색상 토큰
- 본문·표시용 폰트 토큰
- 콘텐츠 최대 폭과 공통 좌우 패딩
- 기본 리셋, 포커스 표시, 공통 헤더

```css
:root {
  --background: #101116;
  --surface: #1a1c24;
  --text: #f4f2ff;
  --accent: #a89cff;
  --mint: #83f0d2;
  --content-width: 70rem;
  --page-padding: clamp(1.25rem, 5vw, 4rem);
  --font-body: "Gowun Dodum", sans-serif;
  --font-display: "Instrument Sans", sans-serif;
}
```

각 HTML은 항상 다음 순서로 스타일을 읽는다.

```html
<link rel="stylesheet" href="css/global.css" />
<link rel="stylesheet" href="css/페이지-전용.css" />
```

### 파일별 책임

| 파일 | 책임 |
| --- | --- |
| `css/global.css` | 테마 토큰, 폰트, 기본 요소, 공통 헤더와 내비게이션 |
| `css/style.css` | 자기소개 메인 화면의 히어로, 활동 카드, 연락처 |
| `css/gif-editor.css` | GIF 편집기 패널, 업로드 영역, 미리보기, 제어 폼 |
| `css/football-game.css` | 축구 게임 캔버스, 점수판, 모바일 조작부 |
| `css/ideal-worldcup.css` | 이상형 월드컵 대진 카드와 결과 화면 |

### 배운 점

전역 CSS는 “모든 페이지가 알아도 되는 규칙”만 가져야 한다. 어떤 화면에서만 쓰이는 카드·패널·게임 UI를 전역에 두면 수정 범위가 예상보다 커진다. 반대로 색상, 폰트, 폭, 간격처럼 디자인 시스템의 기반은 한 파일에서 관리해야 한다.

---

## 4. 3단계 — GIF 프로토타입 핵심 버그 수정

### 버그 1: 기본값과 `min` 제약이 충돌함

`end-frame` 입력 요소는 최소값이 `1`인데 초기값이 `0`이었다.

```html
<!-- 수정 전: min="1"과 value="0"이 충돌 -->
<input id="end-frame" type="number" min="1" value="0" />
```

이 상태에서는 사용자가 파일을 고른 뒤 제출해도 브라우저 기본 폼 검증이 제출을 막을 수 있다.

```html
<!-- 수정 후: 시작과 끝의 기준을 0 프레임으로 통일 -->
<input id="start-frame" type="number" min="0" step="1" value="0" />
<input id="end-frame" type="number" min="0" step="1" value="0" />
```

JavaScript에서도 끝 프레임이 시작 프레임보다 작지 않은지 확인한다.

```js
const start = Number(startFrame.value);
const end = Number(endFrame.value);

if (!Number.isInteger(start) || !Number.isInteger(end) || start < 0 || end < start) {
  setStatus('구간 값은 0 이상의 정수이며, 끝 값은 시작 값보다 크거나 같아야 합니다.');
  return;
}
```

### 버그 2: 업로드 뒤 파일을 바꿀 방법이 없음

기존 코드는 파일을 읽은 뒤 `dropzone.hidden = true`로 업로드 영역 전체를 숨겼다. 따라서 사용자는 다른 GIF를 선택할 수 없었다.

해결 방법은 미리보기 화면에 별도의 교체 버튼을 두는 것이었다.

```html
<button class="replace-file" type="button" id="replace-file">다른 GIF 선택</button>
```

```js
replaceFileButton.addEventListener('click', () => {
  fileInput.value = '';
  fileInput.click();
});
```

`fileInput.value = ''`는 같은 파일을 다시 골라도 `change` 이벤트가 발생하도록 하는 처리다.

### 버그 3: 잘못된 파일이나 손상된 GIF 처리 부족

초기 구현은 `file.type === 'image/gif'`만 검사했다. 일부 환경은 정상 GIF의 MIME 타입을 비워 둘 수 있고, 확장자만 `.gif`인 손상 파일은 미리보기 과정에서 실패할 수 있다.

수정한 흐름은 다음과 같다.

1. 파일 객체, 이름, 크기를 확인한다.
2. MIME 타입 또는 `.gif` 확장자를 확인한다.
3. 0MB와 20MB 초과 파일을 거부한다.
4. `URL.createObjectURL()`을 `try-catch`로 감싼다.
5. 별도 `Image` 객체로 먼저 읽어 성공했을 때만 화면의 `<img>`를 교체한다.
6. 이전 URL과 대기 중 URL을 적절히 해제한다.

```js
try {
  nextPreviewUrl = URL.createObjectURL(file);
} catch (error) {
  console.error('GIF 미리보기를 만들 수 없습니다.', error);
  setStatus('GIF 미리보기를 만들지 못했습니다. 다른 파일을 선택해 주세요.');
  return;
}

const image = new Image();
image.onload = () => {
  preview.src = nextPreviewUrl;
  enableEditor(file, nextPreviewUrl);
};
image.onerror = () => {
  URL.revokeObjectURL(nextPreviewUrl);
  setStatus('GIF 파일을 읽을 수 없습니다. 손상되지 않은 파일을 선택해 주세요.');
};
image.src = nextPreviewUrl;
```

### 배운 점

파일 입력은 “선택했다”와 “안전하게 화면에 표시할 수 있다”가 다르다. 입력값 검증, 파일 읽기 실패, 빠른 연속 교체, 메모리 해제를 모두 분리해서 다뤄야 브라우저가 멈추거나 기존 데이터를 잃는 경험을 막을 수 있다.

---

## 5. 4단계 — 공통 헤더와 페이지 이동 통일

### 문제: 페이지마다 헤더 구조가 달랐음

메인 페이지는 기능 링크와 테마 버튼을 가졌지만, GIF 편집기·축구 게임·이상형 월드컵 페이지는 로고와 배지만 표시했다. 사용자가 다른 기능으로 이동하려면 먼저 메인으로 돌아가야 했다.

### 해결: 네 페이지에 같은 헤더 마크업 적용

```html
<header class="site-header">
  <a class="brand" href="index.html" aria-label="자기소개 페이지로 이동">KARINA / PROFILE</a>
  <nav class="site-navigation" aria-label="주요 메뉴">
    <a class="navigation-link" href="index.html">PROFILE</a>
    <a class="navigation-link" href="gif-editor.html">GIF EDITOR</a>
    <a class="navigation-link" href="football-game.html">FOOTBALL</a>
    <a class="navigation-link" href="ideal-worldcup.html">WORLD CUP</a>
  </nav>
  <button class="theme-toggle" type="button">…</button>
</header>
```

헤더 관련 레이아웃·링크·활성 상태·반응형 규칙은 `global.css`에 둔다. 현재 페이지는 공통 JavaScript가 경로를 비교해 자동 표시한다.

```js
document.querySelectorAll('.navigation-link').forEach((link) => {
  if (new URL(link.href).pathname === window.location.pathname) {
    link.setAttribute('aria-current', 'page');
  }
});
```

모바일에서는 메뉴가 다음 줄 전체 폭을 사용하도록 처리해 작은 화면에서도 링크가 겹치지 않게 했다.

```css
@media (max-width: 42rem) {
  .site-header { flex-wrap: wrap; }
  .site-navigation { order: 3; width: 100%; }
}
```

### 추가 안정화

`#year` 요소가 없는 기능 페이지에서도 공통 스크립트가 오류를 내지 않도록 존재 여부를 먼저 확인한다.

```js
const currentYear = document.querySelector('#year');

if (currentYear) {
  currentYear.textContent = new Date().getFullYear();
}
```

### 배운 점

공통 UI를 같은 CSS만으로 맞추는 것은 충분하지 않다. HTML 구조와 링크 목록도 같은 순서로 유지해야 페이지가 늘어났을 때 누락을 발견하기 쉽다. 활성 메뉴 같은 상태 정보는 페이지마다 하드코딩하기보다 공통 스크립트가 현재 경로에서 계산하게 하는 편이 안전하다.

---

## 6. 최종 구조와 검증 기준

```text
정적 웹 페이지
├─ index.html                 # 자기소개 메인
├─ gif-editor.html            # GIF 편집기 프로토타입
├─ football-game.html         # 미니 축구 게임
├─ ideal-worldcup.html        # 이상형 월드컵
├─ css/
│  ├─ global.css              # 전역 토큰과 공통 UI
│  └─ 페이지별 CSS            # 각 화면 전용 UI
├─ js/
│  ├─ common.js               # 테마·활성 메뉴
│  └─ 페이지별 JS             # 각 기능의 상태와 이벤트
└─ tools/check-js.mjs         # 의존성 없는 JS 문법 검사
```

이번 작업에서 사용한 최소 검증 항목은 다음과 같다.

```powershell
npm.cmd run check:js
git diff --check
```

- 모든 JavaScript 파일이 문법 검사를 통과해야 한다.
- CSS·HTML 변경에 공백 오류가 없어야 한다.
- 네 HTML의 헤더 구조가 동일해야 한다.
- 네 메뉴 링크의 대상 파일이 실제로 존재해야 한다.

---

## 7. 다음 작업 전에 기억할 원칙

1. 새 기능을 만들기 전에 공통인지 페이지 전용인지 먼저 판단한다.
2. 전역 파일에는 토큰과 공통 UI만 두고, 화면 고유 UI는 페이지 전용 파일에 둔다.
3. 파일 입력 기능은 정상 파일, 잘못된 형식, 손상 파일, 파일 교체, 메모리 해제를 모두 확인한다.
4. 공통 헤더·메뉴처럼 반복되는 구조는 모든 페이지에서 같은 마크업을 사용한다.
5. AI가 만든 결과물도 직접 검토하고, 문법 검사와 Git 기록으로 변경 근거를 남긴다.

이 프로젝트는 기능을 추가하는 단계에서 한 걸음 더 나아가, 작은 정적 웹 프로젝트를 유지보수 가능한 구조로 정리하는 연습이 되었다.
