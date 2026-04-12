"""
Token bucket rate limiter for upstream API calls.

Limits real HTTP calls to data.go.kr to `rate` tokens per second with a
configurable burst capacity. Cached responses bypass this entirely — only
calls that miss the cache pass through acquire().

Default: 10 calls/minute (≈ 0.167/s), burst of 5.
A runaway AI agent hitting uncached queries will be throttled rather than
allowed to exhaust the 1,000 requests/day upstream quota in seconds.
"""
from __future__ import annotations

import asyncio
import time


class TokenBucket:
    def __init__(self, rate: float, capacity: float) -> None:
        self._rate = rate          # tokens added per second
        self._capacity = capacity
        self._tokens = capacity    # start full
        self._last = time.monotonic()
        self._lock: asyncio.Lock | None = None

    def _get_lock(self) -> asyncio.Lock:
        # Lazy init: asyncio.Lock must be created inside a running event loop.
        if self._lock is None:
            self._lock = asyncio.Lock()
        return self._lock

    async def acquire(self) -> None:
        """Block until one token is available, then consume it."""
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


# Module-level singleton used by api_client.call_api()
limiter = TokenBucket(rate=10 / 60, capacity=5)
