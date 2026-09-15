"""Data inspection utilities for the study-with-ai project."""

from .inspector import inspect_file
from .models import InspectionReport

__all__ = ["InspectionReport", "inspect_file"]
