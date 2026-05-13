"""
Per-page reading order: column split, then (column, y, x) sort.

Uses gap-based split on block left edges, with minimum mass per column, optional
two-means refinement on horizontal centers for uneven / dense layouts, and
explicit single/two-column modes for UI overrides.
"""

from __future__ import annotations

from dataclasses import dataclass

from .column_mode import ColumnMode
from .layout import BBox


@dataclass(slots=True)
class OrderedItem:
    """Sortable wrapper for a paragraph or table on one page."""

    column: int
    y0: float
    x0: float
    kind: str  # "paragraph" | "table"
    payload: object


def gap_based_column_split_x0(
    x0_values: list[float],
    page_width: float,
    *,
    min_gap_fraction: float = 0.055,
    min_blocks_left: int = 1,
    min_blocks_right: int = 1,
) -> float | None:
    """
    If there is a large horizontal gap among sorted block left edges, return split x
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
        left_n = i + 1
        right_n = len(xs) - left_n
        if left_n < min_blocks_left or right_n < min_blocks_right:
            continue
        if gap > best_gap:
            best_gap = gap
            best_split = (xs[i] + xs[i + 1]) / 2.0
    if best_split is None or best_gap < min_gap:
        return None
    return best_split


def _two_means_split_centers(centers: list[float], page_width: float) -> float | None:
    """Simple 2-means on x-centers; returns mid-split between cluster means."""
    if len(centers) < 2 or page_width <= 0:
        return None
    lo, hi = min(centers), max(centers)
    span = hi - lo
    if span < page_width * 0.07:
        return None
    m0 = lo + span * 0.28
    m1 = lo + span * 0.72
    for _ in range(14):
        g0: list[float] = []
        g1: list[float] = []
        for c in centers:
            if abs(c - m0) <= abs(c - m1):
                g0.append(c)
            else:
                g1.append(c)
        if len(g0) < 1 or len(g1) < 1:
            return None
        m0, m1 = sum(g0) / len(g0), sum(g1) / len(g1)
    split = (m0 + m1) / 2.0
    margin = 0.11 * page_width
    if split < margin or split > page_width - margin:
        return None
    return split


def resolve_column_split(
    block_x_edges: list[tuple[float, float]],
    page_width: float,
    *,
    mode: ColumnMode = "auto",
) -> float | None:
    """
    Return x coordinate dividing the page into two reading columns, or None for single column.

    ``block_x_edges`` are (x0, x1) for each text block used for ordering (after table overlap drop).
    """
    if page_width <= 0:
        return None
    if mode == "single":
        return None
    x0s = [a for a, _ in block_x_edges]
    centers = [(a + b) / 2.0 for a, b in block_x_edges]

    if mode == "two":
        split = gap_based_column_split_x0(
            x0s,
            page_width,
            min_gap_fraction=0.04,
            min_blocks_left=1,
            min_blocks_right=1,
        )
        if split is not None:
            return split
        split = _two_means_split_centers(centers, page_width)
        if split is not None:
            return split
        return page_width * 0.52

    # auto
    split = gap_based_column_split_x0(
        x0s,
        page_width,
        min_gap_fraction=0.055,
        min_blocks_left=1,
        min_blocks_right=1,
    )
    if split is not None:
        return split
    split = _two_means_split_centers(centers, page_width)
    if split is not None:
        return split
    return gap_based_column_split_x0(
        x0s,
        page_width,
        min_gap_fraction=0.035,
        min_blocks_left=1,
        min_blocks_right=1,
    )


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
