"""
Async HTTP client for the KTO MdclTursmService Open API.

Responsibilities (this module only):
  - Maintain one shared httpx.AsyncClient (connection pool, TLS, timeouts).
  - Implement call_api(): cache lookup → rate limit → HTTP with retry → parse.

Supporting concerns are delegated to dedicated modules:
  - utils.config        API key, fixed params, key masking
  - utils.cache         TTL response cache
  - utils.rate_limiter  token bucket guard against quota exhaustion
"""
from __future__ import annotations

import asyncio
from typing import Any, Optional

import httpx

from utils.config import FIXED_PARAMS, mask_key
from utils import cache as _cache
from utils.rate_limiter import limiter as _limiter

BASE_URL = "https://apis.data.go.kr/B551011/MdclTursmService"

# One shared client — keeps TCP connections alive across all tool calls.
# verify=True enforces TLS certificate validation on the upstream API.
_http_client = httpx.AsyncClient(
    timeout=httpx.Timeout(15.0, connect=5.0),
    limits=httpx.Limits(max_connections=10, max_keepalive_connections=5),
    verify=True,
)


async def call_api(
    endpoint: str,
    params: Optional[dict] = None,
    num_of_rows: int = 10,
    page_no: int = 1,
) -> Any:
    """
    Async GET to MdclTursmService/{endpoint}.

    Flow:
      1. Build full query params (fixed + caller-supplied).
      2. Check TTL cache — return immediately on hit.
      3. Acquire rate-limit token (blocks if bucket empty).
      4. HTTP GET with up to 3 retry attempts on 5xx / network errors.
      5. Parse JSON response envelope, map error codes to exceptions.
      6. Store result in cache and return.

    Returns a list of item dicts, or [] when the API signals no data (code 03).
    Raises ValueError / PermissionError / RuntimeError on non-retryable errors.
    """
    query: dict = {
        **FIXED_PARAMS,
        "numOfRows": num_of_rows,
        "pageNo": page_no,
    }
    if params:
        query.update({k: v for k, v in params.items() if v is not None})

    ck = _cache.make_key(endpoint, query)
    hit, cached = _cache.get(ck)
    if hit:
        return cached

    await _limiter.acquire()

    url = f"{BASE_URL}/{endpoint}"
    ttl = _cache.ttl_for(endpoint)
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
    result_msg = mask_key(header.get("resultMsg", ""))

    if result_code in ("00", "0000"):
        pass
    elif result_code == "03":
        _cache.set(ck, [], ttl)
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
        _cache.set(ck, [], ttl)
        return []

    items_wrapper = body.get("items") or {}
    items = items_wrapper.get("item") or []
    if isinstance(items, dict):
        items = [items]

    _cache.set(ck, items, ttl)
    return items
