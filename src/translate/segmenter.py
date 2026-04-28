"""Segment IR text into stable IDs and merge translated text back."""

from __future__ import annotations

from dataclasses import dataclass

from ir import Cell, Document, ParagraphBlock, TableBlock


@dataclass(slots=True, frozen=True)
class Segment:
    id: str
    text: str
    page_index: int
    block_index: int
    run_index: int
    cell_row: int | None = None
    cell_col: int | None = None


def segment_document(document: Document) -> list[Segment]:
    """
    Create stable segment IDs based on structural indices.

    Segments preserve style boundaries by segmenting at run granularity.
    """
    segments: list[Segment] = []
    for p_idx, page in enumerate(document.pages):
        for b_idx, block in enumerate(page.blocks):
            if isinstance(block, ParagraphBlock):
                for r_idx, run in enumerate(block.runs):
                    text = run.text
                    if not text.strip():
                        continue
                    segments.append(
                        Segment(
                            id=f"p{p_idx}-b{b_idx}-r{r_idx}",
                            text=text,
                            page_index=p_idx,
                            block_index=b_idx,
                            run_index=r_idx,
                        )
                    )
            elif isinstance(block, TableBlock):
                for row_idx, row in enumerate(block.rows):
                    for col_idx, cell in enumerate(row):
                        segments.extend(_segment_cell(p_idx, b_idx, row_idx, col_idx, cell))
    return segments


def _segment_cell(
    page_index: int,
    block_index: int,
    row_index: int,
    col_index: int,
    cell: Cell,
) -> list[Segment]:
    out: list[Segment] = []
    for r_idx, run in enumerate(cell.runs):
        text = run.text
        if not text.strip():
            continue
        out.append(
            Segment(
                id=f"p{page_index}-b{block_index}-c{row_index}_{col_index}-r{r_idx}",
                text=text,
                page_index=page_index,
                block_index=block_index,
                run_index=r_idx,
                cell_row=row_index,
                cell_col=col_index,
            )
        )
    return out


def merge_translations(document: Document, translated_by_id: dict[str, str]) -> None:
    """Apply translated strings back to the document in-place by segment ID."""
    for segment in segment_document(document):
        translated = translated_by_id.get(segment.id)
        if translated is None:
            continue
        page = document.pages[segment.page_index]
        block = page.blocks[segment.block_index]
        if isinstance(block, ParagraphBlock):
            block.runs[segment.run_index].text = translated
            continue
        assert isinstance(block, TableBlock)
        assert segment.cell_row is not None and segment.cell_col is not None
        block.rows[segment.cell_row][segment.cell_col].runs[segment.run_index].text = translated
