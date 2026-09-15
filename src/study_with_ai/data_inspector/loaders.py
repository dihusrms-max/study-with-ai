"""Input loaders for supported tabular file formats."""

from pathlib import Path

import pandas as pd


def load_table(path: str | Path, *, sheet_name: str | int = 0) -> tuple[pd.DataFrame, str]:
    """Load a CSV or XLSX file without modifying the source file."""

    source = Path(path)
    suffix = source.suffix.lower()

    if suffix == ".csv":
        return pd.read_csv(source), "CSV"
    if suffix in {".xlsx", ".xlsm", ".xltx", ".xltm"}:
        return pd.read_excel(source, sheet_name=sheet_name), "Excel"

    raise ValueError(f"지원하지 않는 파일 형식입니다: {source.suffix or '(확장자 없음)'}")
