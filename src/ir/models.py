"""Core intermediate representation (IR) models for document translation."""

from __future__ import annotations

from dataclasses import dataclass, field
from uuid import uuid4


def _new_id() -> str:
    """Generate a stable per-object ID for translation mapping."""
    return str(uuid4())


@dataclass(slots=True)
class Run:
    text: str
    bold: bool = False
    italic: bool = False
    font_name: str | None = None
    size_pt: float | None = None


@dataclass(slots=True)
class ParagraphBlock:
    id: str = field(default_factory=_new_id)
    runs: list[Run] = field(default_factory=list)


@dataclass(slots=True)
class Cell:
    id: str = field(default_factory=_new_id)
    runs: list[Run] = field(default_factory=list)


@dataclass(slots=True)
class TableBlock:
    id: str = field(default_factory=_new_id)
    rows: list[list[Cell]] = field(default_factory=list)


Block = ParagraphBlock | TableBlock


@dataclass(slots=True)
class Page:
    page_number: int
    width_pt: float | None = None
    height_pt: float | None = None
    blocks: list[Block] = field(default_factory=list)


@dataclass(slots=True)
class Document:
    pages: list[Page] = field(default_factory=list)
