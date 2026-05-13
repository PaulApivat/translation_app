"""Combine PyMuPDF text blocks, reading order, and pdfplumber tables into IR."""

from __future__ import annotations

import fitz
import pdfplumber

from ir import Block, Document, Page, ParagraphBlock

from .column_mode import ColumnMode, normalize_column_mode
from .layout import BBox, overlap_ratio
from .pdfplumber_tables import extract_tables_from_page
from .pymupdf_blocks import extract_text_blocks
from .reading_order import (
    OrderedItem,
    resolve_column_split,
    sort_reading_order,
    table_column_index,
)
from .warnings import adjacent_page_table_warnings

# Text blocks whose bbox overlaps a detected table by this much are dropped (table wins).
_DEFAULT_TABLE_OVERLAP_RATIO = 0.28

# Table bbox bottom within this fraction of page height triggers a layout notice.
_TABLE_BOTTOM_MARGIN_FRAC = 0.02


def pdf_page_count(pdf_path: str) -> int:
    """Return number of pages without running the full extraction pipeline."""
    doc = fitz.open(pdf_path)
    try:
        return len(doc)
    finally:
        doc.close()


class DocumentExtractor:
    """Extract a Document IR from a text-based PDF path."""

    def __init__(self, *, table_overlap_ratio: float = _DEFAULT_TABLE_OVERLAP_RATIO) -> None:
        self._table_overlap_ratio = table_overlap_ratio

    def extract(
        self,
        pdf_path: str,
        *,
        page_column_modes: dict[int, str] | None = None,
    ) -> Document:
        doc_fitz = fitz.open(pdf_path)
        pages_ir: list[Page] = []
        layout_warnings: list[str] = []
        try:
            with pdfplumber.open(pdf_path) as plumber_doc:
                for page_index in range(len(doc_fitz)):
                    fitz_page = doc_fitz[page_index]
                    plumber_page = (
                        plumber_doc.pages[page_index]
                        if page_index < len(plumber_doc.pages)
                        else None
                    )
                    page_number = page_index + 1
                    raw_mode = (page_column_modes or {}).get(page_number, "auto")
                    column_mode = normalize_column_mode(raw_mode)
                    page_ir, max_table_y1 = self._extract_page(
                        fitz_page,
                        plumber_page,
                        page_number=page_number,
                        column_mode=column_mode,
                    )
                    pages_ir.append(page_ir)
                    h = float(fitz_page.rect.height)
                    if max_table_y1 is not None and h > 0:
                        if max_table_y1 >= h * (1.0 - _TABLE_BOTTOM_MARGIN_FRAC):
                            layout_warnings.append(
                                f"Page {page_number}: a table reaches near the bottom of the page; "
                                "it may be split across pages or continued on the next page. "
                                "Verify table boundaries in the output DOCX."
                            )
        finally:
            doc_fitz.close()

        layout_warnings.extend(adjacent_page_table_warnings(pages_ir))

        return Document(pages=pages_ir, layout_warnings=layout_warnings)

    def _extract_page(
        self,
        fitz_page: fitz.Page,
        plumber_page: pdfplumber.page.Page | None,
        *,
        page_number: int,
        column_mode: ColumnMode,
    ) -> tuple[Page, float | None]:
        page_width = float(fitz_page.rect.width)
        text_blocks = extract_text_blocks(fitz_page)
        tables = extract_tables_from_page(plumber_page) if plumber_page is not None else []
        table_bboxes = [t.bbox for t in tables]

        filtered_text = [
            tb for tb in text_blocks if not self._overlaps_any_table(tb.bbox, table_bboxes)
        ]

        edges = [(tb.bbox.x0, tb.bbox.x1) for tb in filtered_text]
        split_x = resolve_column_split(edges, page_width, mode=column_mode)

        items: list[OrderedItem] = []
        for tb in filtered_text:
            col = 0 if split_x is None else (0 if tb.bbox.x0 < split_x else 1)
            para = ParagraphBlock(runs=list(tb.runs))
            items.append(
                OrderedItem(
                    column=col,
                    y0=tb.bbox.y0,
                    x0=tb.bbox.x0,
                    kind="paragraph",
                    payload=para,
                )
            )
        max_table_y1: float | None = None
        for et in tables:
            max_table_y1 = (
                et.bbox.y1 if max_table_y1 is None else max(max_table_y1, et.bbox.y1)
            )
            col = table_column_index(et.bbox, page_width, split_x)
            items.append(
                OrderedItem(
                    column=col,
                    y0=et.bbox.y0,
                    x0=et.bbox.x0,
                    kind="table",
                    payload=et.table_block,
                )
            )

        ordered = sort_reading_order(items)
        blocks: list[Block] = [it.payload for it in ordered]
        page = Page(
            page_number=page_number,
            width_pt=float(fitz_page.rect.width),
            height_pt=float(fitz_page.rect.height),
            blocks=blocks,
        )
        return page, max_table_y1

    def _overlaps_any_table(self, bbox: BBox, table_bboxes: list[BBox]) -> bool:
        for t in table_bboxes:
            if overlap_ratio(bbox, t) >= self._table_overlap_ratio:
                return True
        return False


def extract_document(
    pdf_path: str,
    *,
    page_column_modes: dict[int, str] | None = None,
) -> Document:
    """Convenience function using default extractor settings."""
    return DocumentExtractor().extract(pdf_path, page_column_modes=page_column_modes)
