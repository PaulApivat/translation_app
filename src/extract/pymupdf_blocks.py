"""Extract text blocks from a PyMuPDF page using span-level metadata."""

from __future__ import annotations

from dataclasses import dataclass

import fitz

from ir import Run

from .layout import BBox


@dataclass(slots=True)
class TextBlock:
    bbox: BBox
    runs: list[Run]


def _span_to_run(span: dict) -> Run | None:
    text = span.get("text") or ""
    if not text.strip():
        return None
    flags = int(span.get("flags", 0))
    # PyMuPDF span flags: bit 1 italic, bit 4 bold (see TEXT_FONT_* docs).
    italic = bool(flags & 2)
    bold = bool(flags & 16)
    font = span.get("font")
    size = span.get("size")
    size_pt = float(size) if size is not None else None
    font_name = str(font) if font else None
    return Run(text=text, bold=bold, italic=italic, font_name=font_name, size_pt=size_pt)


def extract_text_blocks(page: fitz.Page) -> list[TextBlock]:
    """Return one TextBlock per text block in reading order as returned by MuPDF (pre-layout)."""
    blocks_out: list[TextBlock] = []
    data = page.get_text("dict", flags=fitz.TEXT_PRESERVE_WHITESPACE)
    for block in data.get("blocks", []):
        if block.get("type") != 0:
            continue
        bbox_raw = block.get("bbox")
        if not bbox_raw or len(bbox_raw) != 4:
            continue
        x0, y0, x1, y1 = bbox_raw
        bbox = BBox(float(x0), float(y0), float(x1), float(y1))
        runs: list[Run] = []
        for line in block.get("lines", []):
            for span in line.get("spans", []):
                run = _span_to_run(span)
                if run is not None:
                    runs.append(run)
        if runs:
            blocks_out.append(TextBlock(bbox=bbox, runs=runs))
    return blocks_out
