"""Preview translation quality with side-by-side segment samples."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

from ir import Document, document_from_json

from .segmenter import segment_document


@dataclass(slots=True, frozen=True)
class PreviewRow:
    segment_id: str
    before: str
    after: str


def build_preview_rows(before_doc: Document, after_doc: Document, limit: int) -> list[PreviewRow]:
    before_segments = segment_document(before_doc)
    after_by_id = {seg.id: seg.text for seg in segment_document(after_doc)}
    rows: list[PreviewRow] = []
    for seg in before_segments[: max(0, limit)]:
        rows.append(
            PreviewRow(
                segment_id=seg.id,
                before=seg.text,
                after=after_by_id.get(seg.id, "<missing>"),
            )
        )
    return rows


def _truncate(text: str, max_len: int) -> str:
    if len(text) <= max_len:
        return text
    return text[: max_len - 1] + "…"


def _print_rows(rows: list[PreviewRow], width: int) -> None:
    for idx, row in enumerate(rows, start=1):
        print(f"[{idx}] {row.segment_id}")
        print(f"  before: {_truncate(row.before.replace(chr(10), ' '), width)}")
        print(f"  after : {_truncate(row.after.replace(chr(10), ' '), width)}")
        print()


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Print side-by-side segment samples for translation verification.",
    )
    parser.add_argument("before_json", type=Path, help="IR JSON before translation.")
    parser.add_argument("after_json", type=Path, help="IR JSON after translation.")
    parser.add_argument("-n", "--num", type=int, default=10, help="Number of segments to preview.")
    parser.add_argument(
        "--width",
        type=int,
        default=120,
        help="Max characters per before/after field.",
    )
    args = parser.parse_args()

    before_doc = document_from_json(args.before_json.read_text(encoding="utf-8"))
    after_doc = document_from_json(args.after_json.read_text(encoding="utf-8"))
    rows = build_preview_rows(before_doc, after_doc, args.num)
    if not rows:
        print("No segments found.")
        return 0
    _print_rows(rows, args.width)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
