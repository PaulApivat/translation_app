"""CLI: translate IR JSON document using configured provider."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from ir import document_from_json, document_to_json

from . import DeepLProvider, TranslationProgress, TranslationService


def main() -> int:
    parser = argparse.ArgumentParser(description="Translate Document IR JSON.")
    parser.add_argument("input_json", type=Path, help="Path to input IR JSON.")
    parser.add_argument("-o", "--output", type=Path, required=True, help="Path to output IR JSON.")
    parser.add_argument("--source", default="TH", help="Source language code, e.g. TH.")
    parser.add_argument("--target", default="EN", help="Target language code, e.g. EN.")
    parser.add_argument("--batch-size", type=int, default=20)
    parser.add_argument("--retries", type=int, default=3)
    parser.add_argument("--rps", type=float, default=1.0, help="Requests per second throttle.")
    parser.add_argument("--deepl-pro", action="store_true", help="Use DeepL Pro endpoint.")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

    document = document_from_json(args.input_json.read_text(encoding="utf-8"))
    provider = DeepLProvider(use_pro=args.deepl_pro)
    service = TranslationService(
        provider,
        batch_size=args.batch_size,
        max_retries=args.retries,
        requests_per_second=args.rps,
    )
    progress_line_len = 0

    def _on_progress(progress: TranslationProgress) -> None:
        nonlocal progress_line_len
        pct = (
            0.0
            if progress.total_chars == 0
            else (100.0 * progress.translated_chars / progress.total_chars)
        )
        msg = (
            f"Progress: {progress.translated_chars}/{progress.total_chars} chars "
            f"({pct:.1f}%) | {progress.translated_segments}/{progress.total_segments} segments"
        )
        pad = " " * max(0, progress_line_len - len(msg))
        sys.stdout.write("\r" + msg + pad)
        sys.stdout.flush()
        progress_line_len = len(msg)

    translated = service.translate_document(
        document,
        source_lang=args.source,
        target_lang=args.target,
        progress_callback=_on_progress,
    )
    if progress_line_len:
        sys.stdout.write("\n")
        sys.stdout.flush()
    args.output.write_text(document_to_json(translated), encoding="utf-8")
    print(f"Wrote translated IR: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
