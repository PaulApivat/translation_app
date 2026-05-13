"""Unit tests for column split heuristics (Phase 7)."""

from __future__ import annotations

import pytest

from extract.column_mode import normalize_column_mode
from extract.reading_order import gap_based_column_split_x0, resolve_column_split


def test_normalize_column_mode_aliases() -> None:
    assert normalize_column_mode("AUTO") == "auto"
    assert normalize_column_mode("1") == "single"
    assert normalize_column_mode("two") == "two"


def test_gap_split_respects_min_block_counts_per_side() -> None:
    xs = [72.0, 72.0, 72.0, 340.0]
    split = gap_based_column_split_x0(
        xs,
        612.0,
        min_gap_fraction=0.01,
        min_blocks_left=2,
        min_blocks_right=2,
    )
    assert split is None


@pytest.mark.parametrize(
    ("edges", "mode", "expect_split"),
    [
        ([(50, 95), (55, 100), (400, 445), (405, 450)], "two", True),
        ([(50, 95), (55, 100), (400, 445), (405, 450)], "single", False),
    ],
)
def test_resolve_column_split_modes(
    edges: list[tuple[float, float]],
    mode: str,
    expect_split: bool,
) -> None:
    s = resolve_column_split(edges, 612.0, mode=normalize_column_mode(mode))
    if expect_split:
        assert s is not None
        assert 150 < s < 500
    else:
        assert s is None
