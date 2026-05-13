"""Normalize per-page column layout UI / API values."""

from __future__ import annotations

from typing import Literal

ColumnMode = Literal["auto", "single", "two"]


def normalize_column_mode(mode: str | None) -> ColumnMode:
    m = (mode or "auto").strip().lower()
    if m in ("1", "single", "one", "1col", "1-column"):
        return "single"
    if m in ("2", "two", "double", "2col", "2-column"):
        return "two"
    return "auto"
