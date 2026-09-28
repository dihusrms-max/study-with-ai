# 노트북 ↔ 데스크탑 Git 운영 가이드

이 문서는 개인 저장소 `C:\study-with-ai`를 노트북과 데스크탑에서 번갈아 작업하는 절차를 설명합니다. 대회용 저장소와 대회 작업은 이 가이드의 범위에 포함하지 않습니다.

## 1. 이 저장소의 운영 기준

- 원격 저장소 이름은 `origin`입니다.
- GitHub를 두 PC 사이의 코드 전달 지점으로 사용합니다.
- 한 번에 한 PC에서만 작업합니다. 다른 PC에서 이어서 작업하기 전에 현재 PC의 변경을 동기화합니다.
- 작업을 시작할 때 현재 브랜치와 작업 상태를 확인합니다. 현재 브랜치를 모른 채 `main`으로 전환하거나 병합하지 않습니다.
- 저장소에는 `src/scripts/git-auto-sync.ps1` 자동 동기화 스크립트가 있습니다. 이 스크립트는 현재 브랜치에서 `git add -A`를 실행하고, 변경이 있으면 자동 커밋한 뒤 해당 브랜치를 pull/rebase하고 push합니다.

## 2. 작업 시작 전 확인

PowerShell에서 저장소 폴더로 이동하고 상태를 확인합니다.

```powershell
Set-Location C:\study-with-ai
git status --short --branch
git branch -vv
```

`git status`에서 브랜치와 수정 파일을 확인합니다. 수정 파일이 예상과 다르면 작업을 시작하기 전에 파일 내용을 확인합니다. 자동 동기화가 실행 중일 수 있으므로, 동기화 작업과 동시에 브랜치 전환이나 수동 pull/push를 하지 않습니다.

## 3. 같은 PC에서 이어서 작업하기

작업을 시작할 때 현재 브랜치가 의도한 브랜치인지 확인합니다. 저장소의 현재 작업 브랜치 이름을 확인하려면 다음 명령을 사용합니다.

```powershell
git branch --show-current
```

최신 변경을 받은 뒤 작업합니다.

```powershell
git pull --rebase
```

`git pull --rebase`가 실패하면 메시지를 읽고 원인을 확인합니다. 충돌이 난 경우 충돌 파일을 해결하고 상태를 확인한 다음 rebase를 계속합니다. 진행을 취소해야 하는 경우에만 다음 명령을 사용합니다.

```powershell
git rebase --abort
```

## 4. 작업을 마치고 다른 PC로 이동하기

먼저 수정 파일을 확인합니다.

```powershell
git status
git diff
```

의도한 파일만 스테이징하고 커밋합니다.

```powershell
git add <파일경로>
git status
git commit -m "변경 내용 요약"
git push
```

`git add -A` 또는 `git add .`는 저장소의 여러 변경 파일을 한꺼번에 추가할 수 있습니다. 자동 동기화 스크립트도 `git add -A`를 사용하므로, 자동 동기화 전에 `git status`로 포함될 파일을 확인합니다. `.env` 등 비밀 정보나 커밋하지 않을 파일이 포함되지 않았는지 특히 확인합니다.

다른 PC에서는 같은 저장소와 같은 브랜치로 이동한 뒤 변경을 받습니다.

```powershell
Set-Location C:\study-with-ai
git status --short --branch
git switch <작업 브랜치>
git pull --rebase
```

브랜치 이름을 모르면 먼저 다음 명령으로 원격 브랜치 목록을 갱신해 확인합니다.

```powershell
git fetch origin
git branch -a
```

원격에만 있는 브랜치로 처음 전환할 때는 다음 형식을 사용합니다.

```powershell
git switch --track origin/<작업 브랜치>
```

## 5. 새 작업 브랜치가 필요한 경우

작업을 분리하고 싶을 때는 현재 작업 상태를 확인하고, 기준으로 삼을 브랜치와 최신 상태를 명시적으로 확인한 뒤 새 브랜치를 만듭니다.

```powershell
git status --short --branch
git fetch origin
git switch <기준 브랜치>
git pull --rebase
git switch -c feature/<작업 이름>
```

새 브랜치에서 작업을 마친 뒤 원격에 처음 올릴 때는 다음 명령을 사용합니다.

```powershell
git push -u origin feature/<작업 이름>
```

한 작업 브랜치를 두 PC에서 동시에 수정하지 않습니다. 한 PC에서 커밋과 push를 마친 뒤 다른 PC에서 pull하고 이어서 작업합니다.

## 6. `main`에 반영하기

PC 간 작업 동기화와 기능을 `main`에 반영하는 일은 별개의 작업입니다. `main`에 병합하기 전에 현재 브랜치와 변경 내용을 확인합니다.

```powershell
git status --short --branch
git fetch origin
git log --oneline --left-right origin/main...HEAD
```

변경 내용과 기준 브랜치를 검토한 뒤 병합합니다. 현재 브랜치 구조를 모르는 상태에서 `main`으로 전환하거나 병합하지 않습니다. 특히 작업 브랜치가 `main`보다 여러 커밋 앞서 있을 수 있으므로, 병합 전 로그를 확인합니다.

병합을 수행하기로 한 경우:

```powershell
git switch main
git pull --rebase
git merge <작업 브랜치>
git status
```

병합 결과를 확인한 뒤 원격에 반영합니다.

```powershell
git push
```

병합한 작업 브랜치가 더 이상 필요하지 않을 때만 삭제합니다. 브랜치를 삭제하기 전에 해당 변경이 병합됐는지 확인합니다.

```powershell
git branch -d <작업 브랜치>
git push origin --delete <작업 브랜치>
```

## 7. 자동 동기화 사용 시

`src/scripts/git-auto-sync.ps1`은 실행 시 현재 브랜치를 대상으로 동기화합니다. 변경 사항은 모두 스테이징되며, 변경이 있으면 시간 정보가 포함된 메시지로 자동 커밋됩니다.

- 실행 전에 `git status`를 확인해 자동 커밋될 파일을 파악합니다.
- 자동 동기화가 실행되는 동안 수동으로 pull, push, merge, rebase 또는 브랜치 전환을 하지 않습니다.
- 자동 동기화가 실패하면 로그를 확인하고, 실패 원인을 해결한 뒤 상태를 다시 점검합니다.
- 자동 동기화가 실행되더라도 다른 PC에서 작업하기 전에는 GitHub에 push가 완료됐는지 확인합니다.

로그는 Windows 임시 폴더의 `study-with-ai-git-auto-sync\git-auto-sync.log`에 기록됩니다. PowerShell에서 확인하려면 다음과 같이 실행합니다.

```powershell
Get-Content (Join-Path $env:TEMP 'study-with-ai-git-auto-sync\git-auto-sync.log') -Tail 40
```

## 8. 자주 발생하는 상황

| 상황 | 확인 및 대응 |
|---|---|
| 브랜치가 예상과 다름 | `git status --short --branch`, `git branch -vv`로 확인한 뒤 의도한 브랜치로 전환합니다. 로컬 변경이 있으면 먼저 보관하거나 커밋합니다. |
| push가 거부됨 | `git status`로 상태를 확인하고 `git pull --rebase` 후 다시 확인합니다. 충돌이 있으면 해결한 뒤 push합니다. |
| 브랜치를 바꿀 수 없음 | 수정 파일을 확인합니다. 해당 변경을 커밋하거나, 필요한 경우에만 `git stash push -m "작업 임시 보관"`으로 보관합니다. |
| rebase 충돌 | 충돌 파일을 수정하고 `git add <파일경로>`, `git rebase --continue`를 실행합니다. 취소할 때는 `git rebase --abort`를 사용합니다. |
| 자동 동기화 실패 | 임시 폴더의 로그와 `git status`를 확인합니다. 실패 원인을 해결하기 전 반복 실행하지 않습니다. |
| 다른 PC에서 최신 변경이 보이지 않음 | 작업한 PC에서 push가 완료됐는지 확인하고, 다른 PC에서 `git fetch origin` 후 해당 브랜치를 pull합니다. |

## 9. 매일 기억할 흐름

```text
작업 시작: 저장소 위치 확인 → status/branch 확인 → pull --rebase
작업 중: 한 PC에서 한 브랜치만 수정
작업 마침: 변경 파일 확인 → commit → push
PC 이동: 다른 PC에서 같은 브랜치로 전환 → pull --rebase
```
