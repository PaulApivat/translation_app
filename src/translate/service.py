"""Translation orchestration with batching, retries, and rate-limit handling."""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import Callable

from ir import Document

from .base import RateLimitError, TranslationError, TranslationProvider, TranslationRequest
from .segmenter import merge_translations, segment_document

logger = logging.getLogger(__name__)


@dataclass(slots=True, frozen=True)
class TranslationProgress:
    translated_segments: int
    total_segments: int
    translated_chars: int
    total_chars: int


class TranslationService:
    def __init__(
        self,
        provider: TranslationProvider,
        *,
        batch_size: int = 20,
        max_retries: int = 3,
        base_backoff_s: float = 1.0,
        requests_per_second: float = 1.0,
    ) -> None:
        self._provider = provider
        self._batch_size = max(1, batch_size)
        self._max_retries = max(0, max_retries)
        self._base_backoff_s = max(0.0, base_backoff_s)
        self._min_interval_s = 0.0 if requests_per_second <= 0 else (1.0 / requests_per_second)
        self._last_request_ts = 0.0

    def translate_document(
        self,
        document: Document,
        *,
        source_lang: str,
        target_lang: str,
        progress_callback: Callable[[TranslationProgress], None] | None = None,
        should_cancel: Callable[[], bool] | None = None,
    ) -> Document:
        segments = segment_document(document)
        if not segments:
            logger.warning("No translatable segments found in document.")
            return document

        translated: dict[str, str] = {}
        pending = [(s.id, s.text) for s in segments if s.text.strip()]
        if not pending:
            logger.warning("All segments are empty after whitespace filtering.")
            return document

        total_segments = len(pending)
        total_chars = sum(len(text) for _, text in pending)
        translated_segments = 0
        translated_chars = 0

        for chunk in _chunks(pending, self._batch_size):
            if should_cancel is not None and should_cancel():
                logger.warning("Translation cancelled before next batch.")
                break
            done_segments, done_chars = self._translate_chunk(
                chunk=chunk,
                source_lang=source_lang,
                target_lang=target_lang,
                translated=translated,
                should_cancel=should_cancel,
            )
            translated_segments += done_segments
            translated_chars += done_chars
            if progress_callback is not None:
                progress_callback(
                    TranslationProgress(
                        translated_segments=translated_segments,
                        total_segments=total_segments,
                        translated_chars=translated_chars,
                        total_chars=total_chars,
                    )
                )

        missing = [seg_id for seg_id, _ in pending if seg_id not in translated]
        if missing:
            logger.error(
                "Failed to translate %s segment(s). Keeping source text for those segments.",
                len(missing),
            )
        merge_translations(document, translated)
        return document

    def _translate_chunk(
        self,
        *,
        chunk: list[tuple[str, str]],
        source_lang: str,
        target_lang: str,
        translated: dict[str, str],
        should_cancel: Callable[[], bool] | None = None,
    ) -> tuple[int, int]:
        pending = list(chunk)
        attempt = 0
        newly_translated_segments = 0
        newly_translated_chars = 0
        while pending and attempt <= self._max_retries:
            if should_cancel is not None and should_cancel():
                logger.warning("Translation cancelled during batch retries.")
                break
            attempt += 1
            self._throttle()
            ids = [seg_id for seg_id, _ in pending]
            texts = [text for _, text in pending]
            try:
                result = self._provider.translate_batch(
                    TranslationRequest(
                        source_lang=source_lang,
                        target_lang=target_lang,
                        texts=texts,
                    )
                )
            except RateLimitError:
                delay = self._delay_for_attempt(attempt, rate_limited=True)
                logger.warning("Rate limit hit on attempt %s; sleeping %.2fs", attempt, delay)
                time.sleep(delay)
                continue
            except TranslationError as exc:
                delay = self._delay_for_attempt(attempt, rate_limited=False)
                logger.warning(
                    "Batch failed on attempt %s: %s; retrying in %.2fs",
                    attempt,
                    exc,
                    delay,
                )
                time.sleep(delay)
                continue

            failed: list[tuple[str, str]] = []
            for seg_id, src, maybe_translated in zip(ids, texts, result):
                if maybe_translated is None or not maybe_translated.strip():
                    failed.append((seg_id, src))
                    continue
                translated[seg_id] = maybe_translated
                newly_translated_segments += 1
                newly_translated_chars += len(src)

            if len(result) < len(pending):
                failed.extend(pending[len(result) :])

            if failed:
                delay = self._delay_for_attempt(attempt, rate_limited=False)
                logger.warning(
                    (
                        "Partial batch failure: %s/%s segment(s) failed on attempt %s;"
                        " retrying in %.2fs"
                    ),
                    len(failed),
                    len(pending),
                    attempt,
                    delay,
                )
                pending = failed
                time.sleep(delay)
                continue
            return newly_translated_segments, newly_translated_chars

        if pending:
            logger.error("Giving up on %s segment(s) after %s attempt(s).", len(pending), attempt)
        return newly_translated_segments, newly_translated_chars

    def _delay_for_attempt(self, attempt: int, *, rate_limited: bool) -> float:
        factor = 2.0 if rate_limited else 1.0
        return self._base_backoff_s * factor * (2 ** (attempt - 1))

    def _throttle(self) -> None:
        if self._min_interval_s <= 0:
            return
        now = time.monotonic()
        elapsed = now - self._last_request_ts
        if elapsed < self._min_interval_s:
            time.sleep(self._min_interval_s - elapsed)
        self._last_request_ts = time.monotonic()


def _chunks(items: list[tuple[str, str]], size: int) -> list[list[tuple[str, str]]]:
    return [items[i : i + size] for i in range(0, len(items), size)]
