"""Provider interfaces and translation-domain exceptions."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


class TranslationError(Exception):
    """Base translation error."""


class RateLimitError(TranslationError):
    """Provider reported a rate limit condition."""


@dataclass(slots=True, frozen=True)
class TranslationRequest:
    source_lang: str
    target_lang: str
    texts: list[str]


class TranslationProvider(Protocol):
    """Provider contract used by translation service."""

    def translate_batch(self, request: TranslationRequest) -> list[str | None]:
        """
        Translate a batch of texts.

        Return value is position-aligned with request.texts.
        Any index may be None to signal a failed item that can be retried.
        """
