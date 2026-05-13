"""Build small synthetic PDFs for extraction regression tests (PyMuPDF)."""

from __future__ import annotations

from pathlib import Path

import fitz


def write_single_column_pdf(path: Path) -> None:
    doc = fitz.open()
    page = doc.new_page(width=612, height=792)
    page.insert_text((72, 100), "Alpha line one")
    page.insert_text((72, 140), "Bravo line two")
    page.insert_text((72, 180), "Charlie line three")
    doc.save(str(path))
    doc.close()


def write_two_column_pdf(path: Path) -> None:
    doc = fitz.open()
    page = doc.new_page(width=612, height=792)
    # Left column (wide horizontal gap to right column)
    page.insert_text((72, 100), "LeftTop")
    page.insert_text((72, 200), "LeftMid")
    page.insert_text((72, 300), "LeftBottom")
    # Right column
    page.insert_text((340, 100), "RightTop")
    page.insert_text((340, 160), "RightSecond")
    doc.save(str(path))
    doc.close()


def write_newspaper_order_pdf(path: Path) -> None:
    """Left column lower on page than right; column-primary order still reads left then right."""
    doc = fitz.open()
    page = doc.new_page(width=612, height=792)
    page.insert_text((72, 220), "LeftLate")
    page.insert_text((340, 80), "RightEarly")
    doc.save(str(path))
    doc.close()


def write_text_and_table_pdf(path: Path) -> None:
    """Paragraphs plus a simple ruled grid for pdfplumber.find_tables()."""
    doc = fitz.open()
    page = doc.new_page(width=612, height=792)
    page.insert_text((72, 60), "Above table intro")
    x0, y0 = 72, 120
    rows, cols = 3, 2
    cell_w, cell_h = 120, 28
    # Outer border + grid lines (helps pdfplumber detect a table)
    rect = fitz.Rect(x0, y0, x0 + cols * cell_w, y0 + rows * cell_h)
    page.draw_rect(rect, color=(0, 0, 0), width=0.5)
    for r in range(1, rows):
        y = y0 + r * cell_h
        page.draw_line(
            fitz.Point(x0, y),
            fitz.Point(x0 + cols * cell_w, y),
            color=(0, 0, 0),
            width=0.5,
        )
    for c in range(1, cols):
        x = x0 + c * cell_w
        page.draw_line(
            fitz.Point(x, y0),
            fitz.Point(x, y0 + rows * cell_h),
            color=(0, 0, 0),
            width=0.5,
        )
    # Cell labels (also duplicated as loose text would overlap table; keep inside cells only)
    page.insert_text((x0 + 8, y0 + 8), "A1")
    page.insert_text((x0 + cell_w + 8, y0 + 8), "B1")
    page.insert_text((x0 + 8, y0 + cell_h + 8), "A2")
    page.insert_text((x0 + cell_w + 8, y0 + cell_h + 8), "B2")
    page.insert_text((x0 + 8, y0 + 2 * cell_h + 8), "A3")
    page.insert_text((x0 + cell_w + 8, y0 + 2 * cell_h + 8), "B3")
    page.insert_text((72, y0 + rows * cell_h + 40), "Below table outro")
    doc.save(str(path))
    doc.close()


def write_table_near_page_bottom(path: Path) -> None:
    """Grid table with bbox bottom flush to page (layout warning: possible page split)."""
    doc = fitz.open()
    page = doc.new_page(width=612, height=792)
    x0, y0 = 72, 700
    rows, cols = 2, 2
    cell_w, cell_h = 100, 40
    rect = fitz.Rect(x0, y0, x0 + cols * cell_w, y0 + rows * cell_h)
    page.draw_rect(rect, color=(0, 0, 0), width=0.5)
    for r in range(1, rows):
        yy = y0 + r * cell_h
        page.draw_line(
            fitz.Point(x0, yy),
            fitz.Point(x0 + cols * cell_w, yy),
            color=(0, 0, 0),
            width=0.5,
        )
    for c in range(1, cols):
        xx = x0 + c * cell_w
        page.draw_line(
            fitz.Point(xx, y0),
            fitz.Point(xx, y0 + rows * cell_h),
            color=(0, 0, 0),
            width=0.5,
        )
    page.insert_text((x0 + 6, y0 + 8), "X1")
    page.insert_text((x0 + cell_w + 6, y0 + 8), "Y1")
    page.insert_text((x0 + 6, y0 + cell_h + 8), "X2")
    page.insert_text((x0 + cell_w + 6, y0 + cell_h + 8), "Y2")
    doc.save(str(path))
    doc.close()
