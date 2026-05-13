"""Heuristic layout notices derived from IR (Phase 7)."""

from __future__ import annotations

from ir import Block, Page, TableBlock


def adjacent_page_table_warnings(pages: list[Page]) -> list[str]:
    """Warn when a page ends with a table and the next page begins with a table."""
    out: list[str] = []
    for i in range(len(pages) - 1):
        a, b = pages[i].blocks, pages[i + 1].blocks
        if _last_is_table(a) and _first_is_table(b):
            out.append(
                f"Pages {pages[i].page_number}->{pages[i + 1].page_number}: "
                "a table ends one page and another table starts the next — "
                "this may be one logical table split across pages. Check ordering and cells."
            )
    return out


def _last_is_table(blocks: list[Block]) -> bool:
    return bool(blocks) and isinstance(blocks[-1], TableBlock)


def _first_is_table(blocks: list[Block]) -> bool:
    return bool(blocks) and isinstance(blocks[0], TableBlock)
