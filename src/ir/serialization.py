"""Serialization helpers for IR debug snapshots."""

from __future__ import annotations

import json
from dataclasses import asdict
from typing import Any

from .models import Block, Cell, Document, Page, ParagraphBlock, Run, TableBlock


def _block_to_dict(block: Block) -> dict[str, Any]:
    data = asdict(block)
    if isinstance(block, ParagraphBlock):
        return {"type": "paragraph", **data}
    if isinstance(block, TableBlock):
        return {"type": "table", **data}
    raise TypeError(f"Unsupported block type: {type(block)!r}")


def document_to_dict(document: Document) -> dict[str, Any]:
    return {
        "pages": [
            {
                "page_number": page.page_number,
                "width_pt": page.width_pt,
                "height_pt": page.height_pt,
                "blocks": [_block_to_dict(block) for block in page.blocks],
            }
            for page in document.pages
        ]
    }


def document_to_json(document: Document, *, indent: int = 2) -> str:
    return json.dumps(document_to_dict(document), indent=indent, ensure_ascii=False)


def _run_from_dict(data: dict[str, Any]) -> Run:
    return Run(
        text=data["text"],
        bold=data.get("bold", False),
        italic=data.get("italic", False),
        font_name=data.get("font_name"),
        size_pt=data.get("size_pt"),
    )


def _cell_from_dict(data: dict[str, Any]) -> Cell:
    return Cell(
        id=data["id"],
        runs=[_run_from_dict(run_data) for run_data in data.get("runs", [])],
    )


def _block_from_dict(data: dict[str, Any]) -> Block:
    block_type = data["type"]
    if block_type == "paragraph":
        return ParagraphBlock(
            id=data["id"],
            runs=[_run_from_dict(run_data) for run_data in data.get("runs", [])],
        )
    if block_type == "table":
        return TableBlock(
            id=data["id"],
            rows=[
                [_cell_from_dict(cell_data) for cell_data in row_data]
                for row_data in data.get("rows", [])
            ],
        )
    raise ValueError(f"Unknown block type: {block_type}")


def document_from_dict(data: dict[str, Any]) -> Document:
    return Document(
        pages=[
            Page(
                page_number=page_data["page_number"],
                width_pt=page_data.get("width_pt"),
                height_pt=page_data.get("height_pt"),
                blocks=[_block_from_dict(block_data) for block_data in page_data.get("blocks", [])],
            )
            for page_data in data.get("pages", [])
        ]
    )


def document_from_json(payload: str) -> Document:
    return document_from_dict(json.loads(payload))
