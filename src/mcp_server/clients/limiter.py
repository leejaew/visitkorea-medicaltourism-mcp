"""Per-client token bucket for bounded upstream usage."""

from __future__ import annotations

import asyncio
import math
import time

from ..errors.application import RateLimitError


class TokenBucket:
    def __init__(self, rate: float = 10 / 60, capacity: float = 5) -> None:
        if rate <= 0 or capacity < 1:
            raise ValueError("rate must be positive and capacity must be at least one.")
        self.rate = rate
        self.capacity = capacity
        self._tokens = capacity
        self._last = time.monotonic()
        self._lock = asyncio.Lock()

    async def acquire(self) -> None:
        async with self._lock:
            now = time.monotonic()
            self._tokens = min(
                self.capacity, self._tokens + (now - self._last) * self.rate
            )
            self._last = now
            if self._tokens < 1:
                retry_after = math.ceil((1 - self._tokens) / self.rate)
                raise RateLimitError(retry_after)
            self._tokens -= 1
