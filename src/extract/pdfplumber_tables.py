"""Table extraction via pdfplumber and conversion to IR table blocks."""

from __future__ import annotations

from dataclasses import dataclass

import pdfplumber

from ir import Cell, Run, TableBlock

from .layout import BBox


@dataclass(slots=True)
class ExtractedTable:
    bbox: BBox
    table_block: TableBlock


def _cell_text_to_runs(text: str | None) -> list[Run]:
    t = (text or "").strip()
    if not t:
        return []
    return [Run(text=t)]


def extract_tables_from_page(page: pdfplumber.page.Page) -> list[ExtractedTable]:
    out: list[ExtractedTable] = []
    for table in page.find_tables() or []:
        bbox_raw = getattr(table, "bbox", None)
        if not bbox_raw or len(bbox_raw) != 4:
            continue
        x0, top, x1, bottom = bbox_raw
        bbox = BBox(float(x0), float(top), float(x1), float(bottom))
        rows_ir: list[list[Cell]] = []
        for row in table.extract() or []:
            if row is None:
                continue
            row_cells: list[Cell] = []
            for cell_text in row:
                row_cells.append(Cell(runs=_cell_text_to_runs(cell_text)))
            if row_cells:
                rows_ir.append(row_cells)
        if rows_ir:
            out.append(ExtractedTable(bbox=bbox, table_block=TableBlock(rows=rows_ir)))
    return out
