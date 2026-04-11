"""
Async HTTP client for the KTO MdclTursmService Open API.

Improvements over v1:
  - httpx.AsyncClient: non-blocking async HTTP with connection keep-alive pool.
    Synchronous `requests` blocked uvicorn's event loop, preventing concurrent
    tool calls. httpx integrates with asyncio and lets multiple calls run in
    parallel without blocking.
  - TTL response cache: ldongCode cached 24 h (static reference data never
    changes), all other endpoints cached 5 min (dataset refreshes once daily).
    Eliminates redundant upstream calls and preserves the 1,000 req/day quota.
  - Token bucket rate limiter: max 10 real upstream calls per minute.
    Prevents a runaway AI agent from exhausting the daily API quota in seconds.
  - Startup-time key normalisation: API key is read from the environment and
    unquoted once at module load, not on every request.
  - API key masked in all error strings: httpx exceptions include the request
    URL which contains the key as a query param; _mask_key() redacts it.
  - Retry with exponential back-off: up to 3 attempts on 5xx / network errors.
"""
from __future__ import annotations

import asyncio
import hashlib
import json
import os
import time
import urllib.parse
from typing import Any, Optional

import httpx

BASE_URL = "https://apis.data.go.kr/B551011/MdclTursmService"


# ── API key — normalised once at import time ───────────────────────────────────

def _load_api_key() -> str:
    raw = os.environ.get("VISITKOREA_API_KEY", "")
    if not raw:
        raise EnvironmentError(
            "VISITKOREA_API_KEY is not set. Add it to Replit Secrets."
        )
    # data.go.kr issues an "Encoding key" (already URL-percent-encoded) and a
    # "Decoding key" (raw). unquote() normalises either variant to the raw
    # value so that httpx encodes it exactly once in the query string.
    return urllib.parse.unquote(raw)


_API_KEY: str = _load_api_key()

_FIXED_PARAMS: dict = {
    "MobileOS": "ETC",
    "MobileApp": "VisitKoreaMedicalMCP",
    "_type": "json",
    "serviceKey": _API_KEY,
}


# ── Shared async HTTP client with connection pool ──────────────────────────────
# Created once; keeps TCP connections alive across tool calls (no per-call
# TCP handshake + TLS overhead). verify=True enforces upstream TLS certificates.

_http_client = httpx.AsyncClient(
    timeout=httpx.Timeout(30.0, connect=5.0),
    limits=httpx.Limits(max_connections=10, max_keepalive_connections=5),
    verify=True,
)


# ── TTL response cache ─────────────────────────────────────────────────────────
# Simple dict-based cache; no external dependency.
# Key = sha256(endpoint + params without serviceKey).
# Value = (expires_monotonic, result_list).

_CACHE_TTL: dict[str, int] = {
    "ldongCode": 86_400,   # 24 h — administrative codes are effectively static
}
_DEFAULT_TTL = 300          # 5 min for all other endpoints

_cache: dict[str, tuple[float, Any]] = {}


def _cache_key(endpoint: str, params: dict) -> str:
    safe = {k: v for k, v in params.items() if k != "serviceKey"}
    blob = json.dumps(safe, sort_keys=True)
    digest = hashlib.sha256(blob.encode()).hexdigest()[:16]
    return f"{endpoint}:{digest}"


def _cache_get(key: str) -> tuple[bool, Any]:
    entry = _cache.get(key)
    if entry and time.monotonic() < entry[0]:
        return True, entry[1]
    _cache.pop(key, None)
    return False, None


def _cache_set(key: str, value: Any, ttl: int) -> None:
    _cache[key] = (time.monotonic() + ttl, value)


# ── Token bucket rate limiter (guards calls to data.go.kr) ────────────────────
# 10 tokens/minute, burst of 5. A runaway agent hitting cached results never
# consumes tokens. Only real upstream HTTP calls go through acquire().

class _TokenBucket:
    def __init__(self, rate: float, capacity: float) -> None:
        self._rate = rate          # tokens per second
        self._capacity = capacity
        self._tokens = capacity
        self._last = time.monotonic()
        self._lock: asyncio.Lock | None = None

    def _get_lock(self) -> asyncio.Lock:
        if self._lock is None:
            self._lock = asyncio.Lock()
        return self._lock

    async def acquire(self) -> None:
        async with self._get_lock():
            now = time.monotonic()
            self._tokens = min(
                self._capacity,
                self._tokens + (now - self._last) * self._rate,
            )
            self._last = now
            if self._tokens < 1:
                wait = (1.0 - self._tokens) / self._rate
                await asyncio.sleep(wait)
                self._tokens = 0.0
            else:
                self._tokens -= 1.0


_rate_limiter = _TokenBucket(rate=10 / 60, capacity=5)


# ── Helpers ────────────────────────────────────────────────────────────────────

def _mask_key(text: str) -> str:
    """Redact the raw API key from any string before it surfaces to callers."""
    return text.replace(_API_KEY, "[REDACTED]")


# ── Public API ─────────────────────────────────────────────────────────────────

async def call_api(
    endpoint: str,
    params: Optional[dict] = None,
    num_of_rows: int = 10,
    page_no: int = 1,
) -> Any:
    """
    Async GET to MdclTursmService. Returns items list or [].

    Flow:
      1. Check TTL cache — return immediately if hit.
      2. Acquire rate-limit token (waits if bucket is empty).
      3. HTTP GET with up to 3 retry attempts on transient errors.
      4. Parse and validate JSON response envelope.
      5. Store result in cache and return.
    """
    query: dict = {
        **_FIXED_PARAMS,
        "numOfRows": num_of_rows,
        "pageNo": page_no,
    }
    if params:
        query.update({k: v for k, v in params.items() if v is not None})

    ck = _cache_key(endpoint, query)
    hit, cached = _cache_get(ck)
    if hit:
        return cached

    await _rate_limiter.acquire()

    url = f"{BASE_URL}/{endpoint}"
    ttl = _CACHE_TTL.get(endpoint, _DEFAULT_TTL)
    last_exc: Exception | None = None

    for attempt in range(3):
        try:
            response = await _http_client.get(url, params=query)
            response.raise_for_status()
            break
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code >= 500:
                last_exc = exc
                await asyncio.sleep(0.5 * (2 ** attempt))
                continue
            raise RuntimeError(
                f"Upstream returned HTTP {exc.response.status_code}"
            ) from None
        except httpx.RequestError as exc:
            last_exc = exc
            await asyncio.sleep(0.5 * (2 ** attempt))
            continue
    else:
        raise RuntimeError(
            f"Upstream API unreachable after 3 attempts: {type(last_exc).__name__}"
        ) from None

    try:
        data = response.json()
    except Exception:
        raise RuntimeError("Upstream API returned a non-JSON response.") from None

    response_body = data.get("response", {})
    header = response_body.get("header", {})
    result_code = str(header.get("resultCode", ""))
    result_msg = _mask_key(header.get("resultMsg", ""))

    if result_code in ("00", "0000"):
        pass
    elif result_code == "03":
        _cache_set(ck, [], ttl)
        return []
    elif result_code == "10":
        raise ValueError(f"INVALID_REQUEST_PARAMETER_ERROR: {result_msg}")
    elif result_code == "11":
        raise ValueError(f"NO_MANDATORY_REQUEST_PARAMETERS_ERROR: {result_msg}")
    elif result_code == "22":
        raise RuntimeError(
            "RATE_LIMIT_EXCEEDED: Daily upstream quota of 1,000 requests reached."
        )
    elif result_code == "30":
        raise PermissionError(
            "SERVICE_KEY_NOT_REGISTERED: Verify VISITKOREA_API_KEY in Replit Secrets."
        )
    elif result_code == "31":
        raise PermissionError(
            "SERVICE_KEY_EXPIRED: The data.go.kr API key has passed its expiry date."
        )
    else:
        raise RuntimeError(f"API error (code={result_code}): {result_msg}")

    body = response_body.get("body", {})
    if body.get("totalCount", 0) == 0:
        _cache_set(ck, [], ttl)
        return []

    items_wrapper = body.get("items") or {}
    items = items_wrapper.get("item") or []
    if isinstance(items, dict):
        items = [items]

    _cache_set(ck, items, ttl)
    return items
