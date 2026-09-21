"""Application errors exposed at the MCP protocol boundary."""

from __future__ import annotations


class ApplicationError(Exception):
    """Base class for client-safe application failures."""


class InvalidRequest(ApplicationError):
    """The caller supplied invalid or unsupported input."""


class UpstreamError(ApplicationError):
    """The upstream service returned an unusable response."""


class AuthError(UpstreamError):
    """The upstream rejected the configured service key."""


class QuotaError(UpstreamError):
    """The upstream quota has been exhausted."""


class TransportError(UpstreamError):
    """The upstream could not be reached after bounded retries."""


class RateLimitError(ApplicationError):
    """The local upstream request budget is temporarily exhausted."""

    def __init__(self, retry_after: int) -> None:
        self.retry_after = max(1, retry_after)
        super().__init__(
            "Rate limit exceeded. Retry after "
            f"{self.retry_after}s. (Limit: 10 calls/min, burst 5)"
        )
