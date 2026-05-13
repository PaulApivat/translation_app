"""DeepL API adapter."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.parse
import urllib.request

from .base import RateLimitError, TranslationError, TranslationProvider, TranslationRequest
from .env_loader import load_first_dotenv, read_deepl_api_key_from_files

DEEPL_FREE_URL = "https://api-free.deepl.com/v2/translate"
DEEPL_PRO_URL = "https://api.deepl.com/v2/translate"


class DeepLProvider(TranslationProvider):
    """Translate using DeepL REST API."""

    def __init__(
        self,
        *,
        api_key: str | None = None,
        use_pro: bool = False,
        timeout_s: float = 30.0,
    ) -> None:
        load_first_dotenv()
        self._api_key = api_key or os.getenv("DEEPL_API_KEY") or read_deepl_api_key_from_files()
        if not self._api_key:
            raise TranslationError(
                "DeepL API key is missing. Set DEEPL_API_KEY in the environment, "
                "or put it in a .env file: project folder when running from source; "
                "when using the packaged app, place .env next to TranslationApp.app, "
                "inside the .app bundle, beside the executable, or save via Settings "
                "(macOS: ~/Library/Application Support/translation-app/.env)."
            )
        self._url = DEEPL_PRO_URL if use_pro else DEEPL_FREE_URL
        self._timeout_s = timeout_s

    def translate_batch(self, request: TranslationRequest) -> list[str | None]:
        payload = urllib.parse.urlencode(
            {
                "source_lang": request.source_lang.upper(),
                "target_lang": request.target_lang.upper(),
                "preserve_formatting": "1",
                "text": request.texts,
            },
            doseq=True,
        ).encode("utf-8")
        req = urllib.request.Request(self._url, data=payload, method="POST")
        req.add_header("Content-Type", "application/x-www-form-urlencoded")
        req.add_header("Authorization", f"DeepL-Auth-Key {self._api_key}")
        try:
            with urllib.request.urlopen(req, timeout=self._timeout_s) as resp:
                body = resp.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            if exc.code == 429:
                raise RateLimitError("DeepL rate limit reached.") from exc
            msg = exc.read().decode("utf-8", errors="replace") if hasattr(exc, "read") else str(exc)
            raise TranslationError(f"DeepL HTTP error {exc.code}: {msg}") from exc
        except urllib.error.URLError as exc:
            raise TranslationError(f"DeepL network error: {exc}") from exc

        data = json.loads(body)
        translations = data.get("translations", [])
        out = [item.get("text") if isinstance(item, dict) else None for item in translations]
        if len(out) != len(request.texts):
            # Signal partial failure for service-level retry handling.
            return out + [None] * (len(request.texts) - len(out))
        return out
