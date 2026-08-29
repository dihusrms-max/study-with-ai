# 정적 웹 프로젝트를 만들며 배운 JavaScript, Codex, Git 파일 관리 기반 바이브 코딩

## 프로젝트를 시작한 이유

처음 목표는 HTML, CSS, JavaScript만 사용해 간단한 자기소개 페이지를 만드는 것이었다. 프레임워크 없이 시작한 이유는 웹페이지의 기본 구조와 브라우저에서 JavaScript가 동작하는 방식을 직접 익히기 위해서였다.

프로젝트는 자기소개 페이지 하나에서 시작했지만, 진행하며 GIF 편집기 테스트 페이지, Canvas 기반 미니 축구 게임, 이상형 월드컵을 추가했다. 기능을 추가하는 과정에서 화면을 만드는 것뿐 아니라 여러 파일을 어떻게 나누고 Git/GitHub로 변경 이력을 어떻게 관리하는지도 함께 학습했다.

## Codex를 활용하기 위해 정한 작업 규칙

이번 작업에서 Codex는 코드를 무조건 생성하는 도구가 아니라, 구현 방향을 함께 검토하는 협업 도구로 사용했다. 작업 범위는 `C:\study-with-ai` 프로젝트 폴더로 제한했고, Notion 서비스에는 직접 연결하지 않았다. 학습 기록은 Markdown으로 만든 뒤 사용자가 Notion이나 Velog에 직접 옮기는 방식으로 관리했다.

기능 작업은 다음 흐름으로 진행했다.

```text
기능 아이디어 제안
→ 선택지와 추천안 확인
→ 사용자 승인
→ Codex 구현
→ 코드와 UI 검토
→ Git 변경사항 확인
→ 사용자 판단 후 Commit/Push
```

사용자는 기능의 목적, 디자인 방향, 실제 반영 여부, 브랜치 병합 여부를 결정했다. Codex는 파일 구조 제안, 코드 구현, JavaScript 문법 검사, Git 상태 확인, UI 문제 진단을 지원했다. 이 역할 분리는 AI가 만든 결과를 그대로 사용하는 대신, 사용자가 왜 변경하는지 이해하고 최종 판단을 하도록 돕는다.

프로젝트에는 `rules.prompt`를 두고 학습 운영 규칙으로 사용했다. 이 파일은 Codex 기본 설정은 아니지만, 프로젝트에서 Codex와 협업할 때 따르는 사용자 정의 규칙이다. 핵심은 GPT에서 충분히 생각하고 실습한 뒤, Notion에는 다시 볼 가치가 있는 내용만 남기는 것이다.

## 자기소개 페이지를 허브로 구성하기

자기소개 페이지는 사이트의 시작점 역할을 한다. 프로필 이미지, 소개, 관심사, 외부 링크를 보여 주고 GIF Editor, Football, World Cup 페이지로 이동하는 링크를 제공한다.

각 기능은 한 페이지에 모두 넣지 않고 독립 HTML 페이지로 분리했다.

```text
index.html           자기소개와 기능 이동 허브
gif-editor.html      GIF 편집기 프로토타입
football-game.html   미니 축구 게임
ideal-worldcup.html  이상형 월드컵
```

이 방식은 각 기능이 서로 영향을 적게 주고, 페이지별 JavaScript를 독립적으로 연습할 수 있다는 장점이 있다.

## 공통 CSS와 JavaScript를 분리한 이유

기능 페이지가 늘어나자 모든 CSS에 배경색, 글자색, 글꼴, 헤더, 포커스 스타일이 반복되기 시작했다. 중복된 코드는 색상이나 헤더를 수정할 때 여러 파일을 함께 고쳐야 한다는 문제가 있다.

그래서 공통 규칙은 `css/common.css`로, 공통 테마 동작은 `js/common.js`로 분리했다.

```text
css/
  common.css
  style.css
  gif-editor.css
  football-game.css
  ideal-worldcup.css

js/
  common.js
  script.js
  gif-editor.js
  football-game.js
  ideal-worldcup.js
```

각 페이지는 공통 파일과 전용 파일을 순서대로 연결한다.

```html
<link rel="stylesheet" href="css/common.css" />
<link rel="stylesheet" href="css/football-game.css" />

<script src="js/common.js" defer></script>
<script src="js/football-game.js" defer></script>
```

`common.css`에는 `box-sizing`, 기본 글꼴, 포커스 표시, 공통 헤더와 배지처럼 어느 페이지에서도 필요한 규칙을 넣었다. 페이지 전용 CSS에는 게임 화면, GIF 옵션 패널, 월드컵 카드처럼 그 페이지에만 필요한 규칙을 남겼다.

## GIF 편집기: 완성보다 프로토타입 먼저 만들기

GIF를 실제로 편집하려면 GIF를 프레임 단위로 읽고, Canvas에서 수정하고, 다시 GIF로 인코딩해야 한다. 이 기능은 파일 업로드보다 훨씬 복잡하다.

그래서 첫 단계에서는 다음 흐름을 검증하는 프로토타입을 만들었다.

```text
GIF 파일 선택
→ GIF 형식과 20MB 용량 검사
→ 브라우저 내부 미리보기
→ 속도·크기·구간·반복 설정 UI 확인
→ 실제 인코딩은 다음 단계로 분리
```

파일 미리보기에는 `URL.createObjectURL()`을 사용했다.

```javascript
const previewUrl = URL.createObjectURL(file);
preview.src = previewUrl;
```

이 방식은 파일을 서버에 올리지 않고 현재 브라우저에서만 미리보기로 사용한다. 페이지를 닫을 때는 `URL.revokeObjectURL()`로 임시 URL을 해제한다.

이 페이지를 통해 File API, 드래그 앤 드롭, 폼 상태 관리, 브라우저 메모리 관리의 기초를 학습했다.

Codex를 사용할 때는 처음부터 GIF 인코딩 라이브러리와 모든 편집 기능을 추가하지 않았다. 먼저 UI와 파일 업로드 흐름을 제안받고, 사용자가 프로토타입 범위를 승인한 뒤 구현했다. 이 방식은 기능의 복잡도를 작게 유지하면서 다음 구현 단계를 판단하기 좋았다.

## Canvas 미니 축구 게임

축구 게임은 Canvas로 경기장을 그리고 JavaScript로 선수, 공, 골키퍼의 좌표를 갱신하는 방식으로 만들었다.

```text
게임 시작
→ 방향키 또는 WASD 입력
→ 선수 이동
→ 선수와 공 충돌
→ 공 속도와 위치 변경
→ 골키퍼 이동과 충돌
→ 골 판정, 점수 증가
→ 30초 종료
```

Canvas는 HTML 요소를 이동시키는 대신 JavaScript가 매 프레임 화면을 다시 그린다.

```javascript
const canvas = document.querySelector('#game-canvas');
const context = canvas.getContext('2d');
```

반복 렌더링은 `requestAnimationFrame()`을 사용한다.

```javascript
function frame() {
  movePlayer();
  updateBall();
  updateKeeper();
  drawField();
  drawPlayers();
  requestAnimationFrame(frame);
}
```

이 기능에서 Canvas 좌표계, 키보드와 터치 이벤트, 게임 루프, 충돌 계산, 타이머와 점수 상태 관리를 경험했다.

게임 구현 뒤에는 Codex가 문법과 파일 연결을 점검하고, 사용자는 조작 방식과 게임 흐름이 원하는 형태인지 검토했다. 코드가 오류 없이 실행되는 것과 사용자가 자연스럽게 플레이할 수 있는 것은 다른 문제라는 점을 확인했다.

## 이상형 월드컵: 배열과 상태 관리

이상형 월드컵은 실제 인물 사진 대신 성격과 취향을 나타내는 가상 카드 8개를 사용했다. 후보는 JavaScript 배열로 관리하고, 매번 무작위 대진을 만든다.

```text
후보 8명 섞기
→ 2명 비교
→ 선택한 후보를 다음 라운드에 저장
→ 4강
→ 결승
→ 최종 결과 출력
```

핵심은 현재 라운드와 다음 라운드를 분리하는 것이다.

```javascript
let currentRound = [];
let nextRound = [];
```

선택한 후보는 `nextRound`에 넣고, 현재 라운드가 끝나면 다음 라운드를 새 현재 라운드로 바꾼다. 이 과정으로 배열, 랜덤 정렬, 동적 DOM 렌더링, 상태 전환을 학습했다.

후보는 실제 인물 사진을 임의로 수집하지 않고 가상 스타일 카드로 구성했다. 기능 요구사항과 자산 사용 범위를 먼저 정한 뒤 구현한 사례다.

## UI 검토에서 발견한 문제

스크롤 시 요소가 나타나는 애니메이션을 만들기 위해 `.reveal` 클래스를 사용했다. 하지만 첫 화면까지 숨기면 JavaScript가 실행되지 않거나 브라우저 저장소 접근이 막힌 상황에서 화면 전체가 비어 보일 수 있다.

따라서 첫 화면은 항상 보이게 하고, 아래 섹션과 카드에만 애니메이션을 적용하도록 수정했다.

또한 큰 제목, 격자 배경, 네온 색상, 원형 장식, 카드 애니메이션이 동시에 많으면 시선이 분산될 수 있다는 점을 확인했다. 디자인을 더하는 것보다 정보 구조를 먼저 정리하고 장식 요소를 줄이는 것이 자연스러운 화면을 만드는 데 중요했다.

## Git과 GitHub 기본 흐름

Git은 파일 내용을 직접 복사해 올리는 도구가 아니다. 수정된 파일을 확인하고, 선택해 기록을 만들고, 그 기록을 GitHub에 올리는 도구다.

```text
파일 수정
→ Changes 확인
→ Stage
→ Commit
→ Push 또는 Sync
→ Graph 확인
```

`Changes`는 아직 커밋하지 않은 수정 파일이다. `+`를 눌러 Stage하면 해당 파일은 다음 커밋에 포함될 `Staged Changes`로 이동한다.

`Commit`은 내 컴퓨터의 Git 기록에 변경을 저장한다. `Push` 또는 `Sync Changes`를 해야 GitHub에도 커밋이 올라간다.

커밋 메시지는 변경 의도를 설명해야 한다.

```text
좋지 않은 예: test, update
좋은 예: chore: add editor and Git attributes
좋은 예: refactor: extract shared site styles
```

Graph에서는 점 하나가 커밋 하나이고, `HEAD`는 현재 작업 위치, `main`은 기본 브랜치, `origin/main`은 GitHub의 main 위치다. `ahead 1`은 내 컴퓨터에만 커밋이 하나 더 있고 아직 Push하지 않았다는 뜻이다.

## .gitignore, .editorconfig, .gitattributes

`.gitignore`에는 가상환경, Python 캐시, Jupyter 임시 파일, 로그, `.env` 같은 로컬 설정을 넣었다. 이런 파일은 자동 생성되거나 비밀 정보가 포함될 수 있어 GitHub에 올리지 않는 것이 좋다.

```gitignore
.venv/
__pycache__/
.ipynb_checkpoints/
.env
*.log
```

README가 UTF-16으로 저장되어 Git에서 Binary 파일처럼 보인 문제가 있었다. 이를 예방하기 위해 `.editorconfig`에 UTF-8, LF 줄바꿈, 마지막 줄바꿈 규칙을 설정했다.

`.gitattributes`에는 텍스트 파일의 줄바꿈을 통일하고 JPG, PNG, GIF 같은 이미지를 바이너리로 처리하는 규칙을 추가했다.

```gitattributes
* text=auto eol=lf
*.jpg binary
*.png binary
*.gif binary
```

## 브랜치로 파일 구조 개선하기

파일 구조 개선은 안정 버전인 `main`에서 바로 하지 않고 `chore/project-structure` 브랜치에서 진행했다.

```text
main
  └─ 기존 안정 버전

chore/project-structure
  └─ 설정, 문서, 이미지, 공통 코드 정리 작업
```

브랜치는 기존 파일과 무관한 새 프로젝트가 아니다. `main`의 현재 상태를 출발점으로 가져오고, 그 위에 새 변경을 쌓는 독립 작업 공간이다. 따라서 작업 브랜치에서 수정하거나 삭제해도 `main`에는 병합 전까지 영향을 주지 않는다.

이번 구조 개선은 다음 세 커밋으로 나눴다.

```text
chore: add editor and Git attributes
chore: organize assets and documents
refactor: extract shared site styles
```

병합 전에는 `main`으로 전환하면 기존 안정 버전을 확인할 수 있다. 병합 후 문제가 생기면 `Reset`보다 Graph나 GitHub에서 `Revert Commit`을 사용해 새 되돌리기 커밋을 만드는 방식이 안전하다.

## 다음 학습 목표

다음에는 `chore/project-structure` 브랜치로 Pull Request를 만들고 변경 파일을 직접 검토한 뒤 main에 병합하는 과정을 경험하고 싶다. 병합 전과 후 Graph가 어떻게 달라지는지 확인하고, 필요하다면 Revert Commit으로 되돌리는 과정도 연습할 계획이다.

또한 GIF 편집기는 파일 교체와 실제 크기 미리보기부터 직접 구현하고, 이후 프레임 처리와 GIF 내보내기를 단계적으로 확장할 예정이다.

이번 프로젝트를 통해 웹 기능을 만드는 일과 파일 구조, 인코딩, Git 기록을 관리하는 일이 분리된 작업이 아니라 하나의 개발 과정이라는 점을 배웠다.

Codex를 사용한 바이브 코딩에서도 AI의 구현 결과는 출발점일 뿐이다. 기능 범위 결정, 화면 검토, 파일 변경 확인, 브랜치 병합, GitHub 반영은 사용자가 이해하고 판단해야 한다. 앞으로는 작은 기능을 직접 수정한 뒤 의미 있는 커밋 메시지로 기록하고, Pull Request와 Revert Commit까지 직접 경험하는 것을 목표로 한다.
