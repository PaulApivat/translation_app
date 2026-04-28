"""CLI: export IR JSON to DOCX."""

from __future__ import annotations

import argparse
from pathlib import Path

from ir import document_from_json

from .docx_writer import export_docx


def main() -> int:
    parser = argparse.ArgumentParser(description="Export IR JSON to DOCX.")
    parser.add_argument("input_json", type=Path, help="Path to input IR JSON.")
    parser.add_argument("-o", "--output", type=Path, required=True, help="Output DOCX path.")
    parser.add_argument(
        "--no-page-breaks",
        action="store_true",
        help="Disable page breaks between IR pages.",
    )
    args = parser.parse_args()

    document = document_from_json(args.input_json.read_text(encoding="utf-8"))
    export_docx(document, args.output, include_page_breaks=not args.no_page_breaks)
    print(f"Wrote DOCX: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
