"""CLI: ``python -m extract path/to.pdf`` writes IR JSON to stdout or ``-o`` file."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from ir.serialization import document_to_json

from .document_extractor import extract_document


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Extract layout from a PDF into intermediate representation (JSON).",
    )
    parser.add_argument("pdf", type=Path, help="Path to input PDF")
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=None,
        help="Write JSON to this file instead of stdout",
    )
    args = parser.parse_args(argv)
    pdf_path = args.pdf
    if not pdf_path.is_file():
        print(f"Not a file: {pdf_path}", file=sys.stderr)
        return 1
    document = extract_document(str(pdf_path))
    text = document_to_json(document)
    if args.output is not None:
        args.output.write_text(text, encoding="utf-8")
    else:
        sys.stdout.write(text)
        if not text.endswith("\n"):
            sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
