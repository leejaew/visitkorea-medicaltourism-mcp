"""
TTL response cache for upstream API results.

dict-based, no external dependencies.
Key  = sha256(endpoint + sorted params, serviceKey excluded).
Value = (expires_monotonic: float, result: Any).

TTLs
  ldongCode   24 h  — legal district codes are static reference data
  all others   5 min — dataset refreshes once daily; short TTL keeps
                       results fresh without hammering the quota
"""
from __future__ import annotations

import hashlib
import json
import time
from typing import Any

ENDPOINT_TTL: dict[str, int] = {
    "ldongCode": 86_400,   # 24 h
}
DEFAULT_TTL: int = 300      # 5 min

_store: dict[str, tuple[float, Any]] = {}


def make_key(endpoint: str, params: dict) -> str:
    safe = {k: v for k, v in params.items() if k != "serviceKey"}
    blob = json.dumps(safe, sort_keys=True)
    digest = hashlib.sha256(blob.encode()).hexdigest()[:16]
    return f"{endpoint}:{digest}"


def get(key: str) -> tuple[bool, Any]:
    """Return (hit, value). Evicts expired entry on miss."""
    entry = _store.get(key)
    if entry and time.monotonic() < entry[0]:
        return True, entry[1]
    _store.pop(key, None)
    return False, None


def set(key: str, value: Any, ttl: int) -> None:  # noqa: A001
    _store[key] = (time.monotonic() + ttl, value)


def ttl_for(endpoint: str) -> int:
    return ENDPOINT_TTL.get(endpoint, DEFAULT_TTL)
