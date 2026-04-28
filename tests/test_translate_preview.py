from ir import Document, Page, ParagraphBlock, Run
from translate.preview import build_preview_rows


def test_build_preview_rows_maps_by_segment_id() -> None:
    before = Document(pages=[Page(page_number=1, blocks=[ParagraphBlock(runs=[Run(text="สวัสดี")])])])
    after = Document(pages=[Page(page_number=1, blocks=[ParagraphBlock(runs=[Run(text="Hello")])])])

    rows = build_preview_rows(before, after, limit=5)

    assert len(rows) == 1
    assert rows[0].before == "สวัสดี"
    assert rows[0].after == "Hello"


def test_build_preview_rows_handles_missing_segment() -> None:
    before = Document(
        pages=[
            Page(
                page_number=1,
                blocks=[ParagraphBlock(runs=[Run(text="ขอบคุณ")])],
            )
        ]
    )
    after = Document(pages=[])

    rows = build_preview_rows(before, after, limit=5)

    assert len(rows) == 1
    assert rows[0].after == "<missing>"
