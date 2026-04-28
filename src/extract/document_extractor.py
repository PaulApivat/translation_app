"""Combine PyMuPDF text blocks, reading order, and pdfplumber tables into IR."""

from __future__ import annotations

import fitz
import pdfplumber

from ir import Block, Document, Page, ParagraphBlock

from .layout import BBox, overlap_ratio
from .pdfplumber_tables import extract_tables_from_page
from .pymupdf_blocks import extract_text_blocks
from .reading_order import (
    OrderedItem,
    gap_based_column_split_x0,
    sort_reading_order,
    table_column_index,
)

# Text blocks whose bbox overlaps a detected table by this much are dropped (table wins).
_DEFAULT_TABLE_OVERLAP_RATIO = 0.28


class DocumentExtractor:
    """Extract a Document IR from a text-based PDF path."""

    def __init__(self, *, table_overlap_ratio: float = _DEFAULT_TABLE_OVERLAP_RATIO) -> None:
        self._table_overlap_ratio = table_overlap_ratio

    def extract(self, pdf_path: str) -> Document:
        doc_fitz = fitz.open(pdf_path)
        pages_ir: list[Page] = []
        try:
            with pdfplumber.open(pdf_path) as plumber_doc:
                for page_index in range(len(doc_fitz)):
                    fitz_page = doc_fitz[page_index]
                    plumber_page = (
                        plumber_doc.pages[page_index]
                        if page_index < len(plumber_doc.pages)
                        else None
                    )
                    pages_ir.append(
                        self._extract_page(
                            fitz_page,
                            plumber_page,
                            page_number=page_index + 1,
                        )
                    )
        finally:
            doc_fitz.close()
        return Document(pages=pages_ir)

    def _extract_page(
        self,
        fitz_page: fitz.Page,
        plumber_page: pdfplumber.page.Page | None,
        *,
        page_number: int,
    ) -> Page:
        page_width = float(fitz_page.rect.width)
        text_blocks = extract_text_blocks(fitz_page)
        tables = extract_tables_from_page(plumber_page) if plumber_page is not None else []
        table_bboxes = [t.bbox for t in tables]

        filtered_text = [
            tb for tb in text_blocks if not self._overlaps_any_table(tb.bbox, table_bboxes)
        ]

        x0s = [tb.bbox.x0 for tb in filtered_text]
        split_x = gap_based_column_split_x0(x0s, page_width)

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
        for et in tables:
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
        return Page(
            page_number=page_number,
            width_pt=float(fitz_page.rect.width),
            height_pt=float(fitz_page.rect.height),
            blocks=blocks,
        )

    def _overlaps_any_table(self, bbox: BBox, table_bboxes: list[BBox]) -> bool:
        for t in table_bboxes:
            if overlap_ratio(bbox, t) >= self._table_overlap_ratio:
                return True
        return False


def extract_document(pdf_path: str) -> Document:
    """Convenience function using default extractor settings."""
    return DocumentExtractor().extract(pdf_path)
