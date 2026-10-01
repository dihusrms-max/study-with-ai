@echo off
setlocal

set "WSL_DISTRO=Ubuntu-24.04"
set "SOURCE=/home/lee/workspace/rag-project-1/src/rag_project_1/."
set "DESTINATION=/mnt/c/study-with-ai/_rag_project_1"

echo Synchronizing RAG project from WSL to Windows...
wsl.exe -d "%WSL_DISTRO%" -- bash -lc "set -e; test -d '%SOURCE%'; mkdir -p '%DESTINATION%'; cp -av '%SOURCE%' '%DESTINATION%/'"
if errorlevel 1 (
  echo.
  echo Synchronization failed. Check that WSL distro "%WSL_DISTRO%" is running and the source folder exists.
  pause
  exit /b 1
)

echo.
echo Synchronization completed: %SOURCE% to %DESTINATION%
pause
endlocal
