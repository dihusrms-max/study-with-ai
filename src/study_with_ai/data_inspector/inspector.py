"""Read-only inspection of CSV and Excel tabular files."""

from pathlib import Path

from .loaders import load_table
from .models import InspectionReport


def inspect_file(path: str | Path, *, sheet_name: str | int = 0) -> InspectionReport:
    """Inspect basic structure and quality signals of a tabular file."""

    source = Path(path)
    frame, file_type = load_table(source, sheet_name=sheet_name)

    missing = frame.isna().sum().astype(int).to_dict()
    missing = {str(column): count for column, count in missing.items() if count > 0}
    dtypes = {str(column): str(dtype) for column, dtype in frame.dtypes.items()}
    warnings: list[str] = []
    recommendations: list[str] = []

    whitespace_columns = [
        str(column)
        for column in frame.columns
        if isinstance(column, str) and column != column.strip()
    ]
    if whitespace_columns:
        warnings.append(f"컬럼명 앞뒤 공백 발견: {whitespace_columns}")
        recommendations.append("컬럼명 strip 여부를 검토하세요.")

    if missing:
        warnings.append(f"결측치가 있는 컬럼: {list(missing)}")
        recommendations.append("분석 목적에 따라 결측치 처리 방법을 결정하세요.")

    duplicate_rows = int(frame.duplicated().sum())
    if duplicate_rows:
        warnings.append(f"중복 행 {duplicate_rows}개 발견")
        recommendations.append("중복 행 삭제 전 중복 기준을 먼저 확인하세요.")

    return InspectionReport(
        path=str(source),
        file_type=file_type,
        shape=(int(frame.shape[0]), int(frame.shape[1])),
        columns=[str(column) for column in frame.columns],
        dtypes=dtypes,
        missing=missing,
        duplicate_rows=duplicate_rows,
        warnings=warnings,
        recommendations=recommendations,
    )
