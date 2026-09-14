# VS Code Jupyter 사용법

1. VS Code에서 `C:\study-contests` 폴더를 연다.
2. 확장 기능 `Python`과 `Jupyter`를 설치한다.
3. `notebooks` 폴더에서 새 `.ipynb` 파일을 만든다.
4. 우측 상단 `커널 선택`에서 `C:\study-contests\.venv\Scripts\python.exe`를 선택한다.
5. 셀 실행 전 커널 경로가 대회 전용 `.venv`인지 확인한다.

필요한 경우 터미널에서 다음으로 환경을 확인한다.

```powershell
cd C:\study-contests
uv run python -c "import sys; print(sys.executable)"
```

JupyterLab 서버를 별도로 실행하지 않는다. Notebook 커널은 `ipykernel`을 사용한다.
