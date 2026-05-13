"""Tests for layout warning helpers (Phase 7)."""

from __future__ import annotations

from extract.warnings import adjacent_page_table_warnings
from ir import Cell, Page, TableBlock


def test_adjacent_page_table_warnings_when_tables_bookend_page_break() -> None:
    t1 = TableBlock(rows=[[Cell(runs=[]), Cell(runs=[])], [Cell(runs=[]), Cell(runs=[])]])
    t2 = TableBlock(rows=[[Cell(runs=[]), Cell(runs=[])]])
    p1 = Page(page_number=1, blocks=[t1])
    p2 = Page(page_number=2, blocks=[t2])
    w = adjacent_page_table_warnings([p1, p2])
    assert len(w) == 1
    assert "1->2" in w[0]
