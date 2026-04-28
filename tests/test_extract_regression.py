"""Regression tests for PDF extraction, reading order, and table IR."""

from __future__ import annotations

from pathlib import Path

import pytest

from extract import extract_document
from ir import ParagraphBlock, TableBlock
from tests.fixtures.pdf_factory import (
    write_newspaper_order_pdf,
    write_single_column_pdf,
    write_text_and_table_pdf,
    write_two_column_pdf,
)


def _full_text(page_blocks) -> str:
    parts: list[str] = []
    for b in page_blocks:
        if isinstance(b, ParagraphBlock):
            parts.append("".join(r.text for r in b.runs))
        elif isinstance(b, TableBlock):
            for row in b.rows:
                for cell in row:
                    parts.append("".join(r.text for r in cell.runs))
    return " ".join(parts)


def _paragraph_texts_in_order(page_blocks) -> list[str]:
    return ["".join(r.text for r in b.runs) for b in page_blocks if isinstance(b, ParagraphBlock)]


@pytest.fixture
def tmp_pdf(tmp_path: Path) -> Path:
    return tmp_path / "sample.pdf"


def test_single_column_reading_order(tmp_pdf: Path) -> None:
    write_single_column_pdf(tmp_pdf)
    doc = extract_document(str(tmp_pdf))
    assert len(doc.pages) == 1
    paras = _paragraph_texts_in_order(doc.pages[0].blocks)
    joined = "\n".join(paras)
    assert joined.index("Alpha") < joined.index("Bravo") < joined.index("Charlie")


def test_two_column_newspaper_order(tmp_pdf: Path) -> None:
    write_two_column_pdf(tmp_pdf)
    doc = extract_document(str(tmp_pdf))
    texts = _paragraph_texts_in_order(doc.pages[0].blocks)
    # All left-column lines before any right-column line
    idx_left_top = next(i for i, t in enumerate(texts) if "LeftTop" in t)
    idx_left_bottom = next(i for i, t in enumerate(texts) if "LeftBottom" in t)
    idx_right_top = next(i for i, t in enumerate(texts) if "RightTop" in t)
    assert idx_left_top < idx_left_bottom < idx_right_top


def test_newspaper_column_primary_order(tmp_pdf: Path) -> None:
    write_newspaper_order_pdf(tmp_pdf)
    doc = extract_document(str(tmp_pdf))
    texts = _paragraph_texts_in_order(doc.pages[0].blocks)
    idx_left = next(i for i, t in enumerate(texts) if "LeftLate" in t)
    idx_right = next(i for i, t in enumerate(texts) if "RightEarly" in t)
    assert idx_left < idx_right


def test_mixed_text_and_table(tmp_pdf: Path) -> None:
    write_text_and_table_pdf(tmp_pdf)
    doc = extract_document(str(tmp_pdf))
    blocks = doc.pages[0].blocks
    table_blocks = [b for b in blocks if isinstance(b, TableBlock)]
    assert table_blocks, "Expected pdfplumber to detect at least one table"
    table = table_blocks[0]
    flat = " ".join("".join(r.text for r in c.runs) for row in table.rows for c in row)
    assert "A1" in flat and "B3" in flat
    full = _full_text(blocks)
    assert "Above table intro" in full
    assert "Below table outro" in full

    # Intro should appear before table cell content in block order
    def _para_idx(substr: str) -> int:
        for i, b in enumerate(blocks):
            if not isinstance(b, ParagraphBlock):
                continue
            if substr in "".join(r.text for r in b.runs):
                return i
        raise AssertionError(f"paragraph containing {substr!r} not found")

    intro_i = _para_idx("Above")
    table_i = next(i for i, b in enumerate(blocks) if isinstance(b, TableBlock))
    outro_i = _para_idx("Below")
    assert intro_i < table_i < outro_i
