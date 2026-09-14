$ErrorActionPreference = 'Stop'
Set-Location (Split-Path -Parent $PSScriptRoot)

$logDir = Join-Path (Get-Location) 'logs'
New-Item -ItemType Directory -Force -Path $logDir | Out-Null
$logFile = Join-Path $logDir 'git-auto-sync.log'

function Write-Log([string]$message) {
    "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') $message" | Out-File -FilePath $logFile -Append -Encoding utf8
}

try {
    git add -A
    if (-not (git diff --cached --quiet)) {
        git commit -m "Auto-sync: $(Get-Date -Format 'yyyy-MM-dd HH:mm')"
        Write-Log 'Committed local changes.'
    } else {
        Write-Log 'No local changes.'
    }

    git pull --rebase origin main
    git push origin main
    Write-Log 'Push completed.'
} catch {
    Write-Log "FAILED: $($_.Exception.Message)"
    exit 1
}
