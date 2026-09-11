"""Data models returned by the data inspector."""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class InspectionReport:
    """Read-only summary of a tabular data source."""

    path: str
    file_type: str
    shape: tuple[int, int]
    columns: list[str]
    dtypes: dict[str, str]
    missing: dict[str, int]
    duplicate_rows: int
    warnings: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable representation of the report."""

        return {
            "path": self.path,
            "file_type": self.file_type,
            "shape": list(self.shape),
            "columns": self.columns,
            "dtypes": self.dtypes,
            "missing": self.missing,
            "duplicate_rows": self.duplicate_rows,
            "warnings": self.warnings,
            "recommendations": self.recommendations,
        }
