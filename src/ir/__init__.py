"""Intermediate representation models package."""

from .models import Block, Cell, Document, Page, ParagraphBlock, Run, TableBlock
from .serialization import (
    document_from_dict,
    document_from_json,
    document_to_dict,
    document_to_json,
)

__all__ = [
    "Block",
    "Cell",
    "Document",
    "Page",
    "ParagraphBlock",
    "Run",
    "TableBlock",
    "document_from_dict",
    "document_from_json",
    "document_to_dict",
    "document_to_json",
]
