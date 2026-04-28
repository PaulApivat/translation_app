"""
Per-page reading order: gap-based column clustering, then (column, y, x) sort.

Two-column detection uses the largest horizontal gap among block left edges relative to
page width. A future optional k-means (or 2-means) split on x-centers can be added for
harder layouts without changing the public sort contract.
"""

from __future__ import annotations

from dataclasses import dataclass

from .layout import BBox


@dataclass(slots=True)
class OrderedItem:
    """Sortable wrapper for a paragraph or table on one page."""

    column: int
    y0: float
    x0: float
    kind: str  # "paragraph" | "table"
    payload: object


def _page_width_from_blocks(block_x_ranges: list[tuple[float, float]], fallback: float) -> float:
    if not block_x_ranges:
        return fallback
    return max(x1 for _, x1 in block_x_ranges) - min(x0 for x0, _ in block_x_ranges)


def gap_based_column_split_x0(
    x0_values: list[float],
    page_width: float,
    *,
    min_gap_fraction: float = 0.06,
) -> float | None:
    """
    If there is a large horizontal gap among block left edges, return split x
    so blocks left of split are column 0 and right are column 1.
    Otherwise return None (single column).
    """
    if len(x0_values) < 2 or page_width <= 0:
        return None
    xs = sorted(x0_values)
    min_gap = min_gap_fraction * page_width
    best_gap = 0.0
    best_split: float | None = None
    for i in range(len(xs) - 1):
        gap = xs[i + 1] - xs[i]
        if gap > best_gap:
            best_gap = gap
            best_split = (xs[i] + xs[i + 1]) / 2.0
    if best_split is None or best_gap < min_gap:
        return None
    return best_split


def assign_column(x0: float, split_x: float | None) -> int:
    if split_x is None:
        return 0
    return 0 if x0 < split_x else 1


def table_column_index(bbox: BBox, page_width: float, split_x: float | None) -> int:
    """Narrow tables use left/right column; wide tables read as column 0."""
    if page_width <= 0:
        return 0
    if bbox.width >= 0.55 * page_width:
        return 0
    cx = (bbox.x0 + bbox.x1) / 2.0
    return assign_column(cx, split_x)


def sort_reading_order(items: list[OrderedItem]) -> list[OrderedItem]:
    """Newspaper-style: primary key column, then top-to-bottom, then left-to-right."""
    return sorted(items, key=lambda it: (it.column, it.y0, it.x0))
