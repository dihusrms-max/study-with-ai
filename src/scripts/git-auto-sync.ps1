$ErrorActionPreference = "Stop"

$repo = "C:\study-with-ai"
$logDir = Join-Path $env:TEMP "study-with-ai-git-auto-sync"
$logFile = Join-Path $logDir "git-auto-sync.log"

New-Item -ItemType Directory -Force -Path $logDir | Out-Null

function Write-Log([string]$message) {
    $line = "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] $message"
    Add-Content -LiteralPath $logFile -Value $line
}

try {
    Set-Location -LiteralPath $repo

    $branch = (git branch --show-current).Trim()
    if ([string]::IsNullOrWhiteSpace($branch)) {
        throw "현재 브랜치를 확인할 수 없습니다."
    }

    Write-Log "자동 동기화 시작: branch=$branch"

    git add -A
    if (-not (git diff --cached --quiet)) {
        $date = Get-Date -Format "yyyy-MM-dd HH:mm"
        git commit -m "chore: auto sync $date"
        Write-Log "변경 사항을 커밋했습니다."
    } else {
        Write-Log "커밋할 변경 사항이 없습니다."
    }

    git pull --rebase origin $branch
    git push origin $branch
    Write-Log "동기화 완료"
}
catch {
    Write-Log "동기화 중단: $($_.Exception.Message)"
    exit 1
}
