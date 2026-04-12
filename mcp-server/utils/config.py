"""
API key and fixed request parameters.

Loads the VISITKOREA_API_KEY secret once at import time and exposes:
  - API_KEY      raw (decoded) key, used internally by api_client
  - FIXED_PARAMS base query params shared by every upstream request
  - mask_key()   redacts the raw key from any string before it leaves this process
"""
from __future__ import annotations

import os
import urllib.parse


def _load_api_key() -> str:
    raw = os.environ.get("VISITKOREA_API_KEY", "")
    if not raw:
        raise EnvironmentError(
            "VISITKOREA_API_KEY is not set. Add it to Replit Secrets."
        )
    # data.go.kr issues two key variants:
    #   Encoding key — already URL-percent-encoded (contains %2F, %3D, …)
    #   Decoding key — raw base64 characters
    # unquote() normalises either to the raw value so httpx encodes it
    # exactly once when it builds the query string.
    return urllib.parse.unquote(raw)


API_KEY: str = _load_api_key()

FIXED_PARAMS: dict = {
    "MobileOS": "ETC",
    "MobileApp": "VisitKoreaMedicalMCP",
    "_type": "json",
    "serviceKey": API_KEY,
}


def mask_key(text: str) -> str:
    """Replace the raw API key with [REDACTED] before the string leaves this process."""
    return text.replace(API_KEY, "[REDACTED]")
