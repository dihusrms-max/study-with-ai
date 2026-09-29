@echo off
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "\\wsl.localhost\Ubuntu-24.04\home\lee\workspace\rag-project-1\scripts\sync_rag_project_to_windows.ps1"
if errorlevel 1 (
  echo Synchronization failed. See the message above.
  pause
  exit /b 1
)
echo.
echo Synchronization completed.
pause
