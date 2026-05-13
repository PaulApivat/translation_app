"""Translation services package."""

from .base import RateLimitError, TranslationError, TranslationProvider, TranslationRequest
from .deepl_provider import DeepLProvider
from .env_loader import load_dotenv, load_first_dotenv
from .segmenter import Segment, merge_translations, segment_document
from .service import TranslationProgress, TranslationService

__all__ = [
    "DeepLProvider",
    "load_dotenv",
    "load_first_dotenv",
    "RateLimitError",
    "Segment",
    "TranslationError",
    "TranslationProvider",
    "TranslationProgress",
    "TranslationRequest",
    "TranslationService",
    "merge_translations",
    "segment_document",
]
