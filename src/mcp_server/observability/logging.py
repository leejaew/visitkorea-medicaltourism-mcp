"""Safe logging defaults for HTTP clients."""

from __future__ import annotations

import logging


def configure_logging() -> None:
    """Suppress request URL logging, which can contain the service key."""
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
