"""
Token bucket rate limiter for upstream API calls.

Limits real HTTP calls to data.go.kr to `rate` tokens per second with a
configurable burst capacity. Cached responses bypass this entirely — only
calls that miss the cache pass through acquire().

Default: 10 calls/minute (≈ 0.167/s), burst of 5.
A runaway AI agent hitting uncached queries will be throttled rather than
allowed to exhaust the 1,000 requests/day upstream quota in seconds.

Fast-fail design: when the bucket is empty, acquire() raises RuntimeError
immediately instead of sleeping. This prevents multi-second hangs that would
cause MCP clients (e.g. Manus AI) to interpret a stalled connection as
"degraded mode". Callers receive a clear message with the retry-after delay.
"""
from __future__ import annotations

import asyncio
import math
import time


class TokenBucket:
    def __init__(self, rate: float, capacity: float) -> None:
        self._rate = rate          # tokens added per second
        self._capacity = capacity
        self._tokens = capacity    # start full
        self._last = time.monotonic()
        self._lock: asyncio.Lock | None = None

    def _get_lock(self) -> asyncio.Lock:
        if self._lock is None:
            self._lock = asyncio.Lock()
        return self._lock

    async def acquire(self) -> None:
        """
        Consume one token, or raise RuntimeError if the bucket is empty.

        Unlike a blocking design, this returns immediately in both the success
        and the failure case — eliminating multi-second hangs that cause MCP
        clients to mark the connection as degraded.
        """
        async with self._get_lock():
            now = time.monotonic()
            self._tokens = min(
                self._capacity,
                self._tokens + (now - self._last) * self._rate,
            )
            self._last = now
            if self._tokens < 1:
                retry_after = math.ceil((1.0 - self._tokens) / self._rate)
                raise RuntimeError(
                    f"Rate limit: too many requests to upstream API. "
                    f"Please retry after {retry_after}s. "
                    f"(Limit: {int(self._rate * 60)} calls/min, burst {int(self._capacity)})"
                )
            self._tokens -= 1.0


# Module-level singleton used by api_client.call_api()
limiter = TokenBucket(rate=10 / 60, capacity=5)
