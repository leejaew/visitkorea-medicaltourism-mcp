"""Bounded, defensive-copy TTL cache for upstream response data."""

from __future__ import annotations

import copy
import hashlib
import json
import time
from collections import OrderedDict
from typing import Any

ENDPOINT_TTL: dict[str, int] = {"ldongCode": 86_400}
DEFAULT_TTL = 300


class TTLCache:
    def __init__(self, max_entries: int = 256) -> None:
        if max_entries < 1:
            raise ValueError("max_entries must be positive.")
        self.max_entries = max_entries
        self._store: OrderedDict[str, tuple[float, Any]] = OrderedDict()

    @staticmethod
    def make_key(endpoint: str, params: dict[str, Any]) -> str:
        safe_params = {
            key: value for key, value in params.items() if key != "serviceKey"
        }
        payload = json.dumps(
            {"endpoint": endpoint, "params": safe_params},
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        )
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def get(self, key: str) -> tuple[bool, Any]:
        entry = self._store.get(key)
        if entry is None:
            return False, None
        expires_at, value = entry
        if time.monotonic() >= expires_at:
            self._store.pop(key, None)
            return False, None
        self._store.move_to_end(key)
        return True, copy.deepcopy(value)

    def set(self, key: str, value: Any, ttl: int) -> None:
        self._store[key] = (time.monotonic() + ttl, copy.deepcopy(value))
        self._store.move_to_end(key)
        while len(self._store) > self.max_entries:
            self._store.popitem(last=False)

    @staticmethod
    def ttl_for(endpoint: str) -> int:
        return ENDPOINT_TTL.get(endpoint, DEFAULT_TTL)
