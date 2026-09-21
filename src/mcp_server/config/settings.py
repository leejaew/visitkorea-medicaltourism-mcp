"""Pure runtime configuration loading for the MCP server."""

from __future__ import annotations

import os
import urllib.parse
from collections.abc import Mapping
from dataclasses import dataclass

DEFAULT_BASE_URL = "https://apis.data.go.kr/B551011/MdclTursmService"
DEFAULT_ALLOWED_HOSTS = (
    "127.0.0.1",
    "127.0.0.1:*",
    "localhost",
    "localhost:*",
    "[::1]",
    "[::1]:*",
)
DEFAULT_ALLOWED_ORIGINS = (
    "http://127.0.0.1:*",
    "http://localhost:*",
    "http://[::1]:*",
)


@dataclass(frozen=True, slots=True)
class Settings:
    api_key: str
    port: int = 8000
    base_url: str = DEFAULT_BASE_URL
    request_timeout: float = 15.0
    connect_timeout: float = 5.0
    max_connections: int = 10
    max_keepalive_connections: int = 5
    max_retries: int = 3
    cache_capacity: int = 256
    allowed_hosts: tuple[str, ...] = DEFAULT_ALLOWED_HOSTS
    allowed_origins: tuple[str, ...] = DEFAULT_ALLOWED_ORIGINS

    @property
    def fixed_params(self) -> dict[str, str]:
        return {
            "MobileOS": "ETC",
            "MobileApp": "VisitKoreaMedicalMCP",
            "_type": "json",
            "serviceKey": self.api_key,
        }


def load_settings(environ: Mapping[str, str] | None = None) -> Settings:
    """Load and validate settings without performing I/O or network work."""
    values = os.environ if environ is None else environ
    raw_key = values.get("VISITKOREA_API_KEY", "")
    if not raw_key:
        raise OSError("VISITKOREA_API_KEY is not set. Add it to Replit Secrets.")

    raw_port = values.get("PORT", "8000")
    try:
        port = int(raw_port)
    except (TypeError, ValueError) as exc:
        raise ValueError("PORT must be an integer between 1 and 65535.") from exc
    if not 1 <= port <= 65535:
        raise ValueError("PORT must be an integer between 1 and 65535.")

    # data.go.kr provides both URL-encoded and decoded variants.
    api_key = urllib.parse.unquote(raw_key)
    if not api_key:
        raise OSError("VISITKOREA_API_KEY must not be empty.")
    allowed_hosts = list(DEFAULT_ALLOWED_HOSTS)
    allowed_origins = list(DEFAULT_ALLOWED_ORIGINS)
    configured_hosts = values.get("MCP_ALLOWED_HOSTS", "")
    if not configured_hosts:
        configured_hosts = values.get("REPLIT_DOMAINS", "")
    for raw_host in configured_hosts.split(","):
        host = (
            raw_host.strip().removeprefix("https://").removeprefix("http://").strip("/")
        )
        if not host:
            continue
        allowed_hosts.append(host)
        if ":" not in host and "*" not in host:
            allowed_hosts.append(f"{host}:*")
        allowed_origins.extend((f"https://{host}", f"http://{host}"))

    configured_origins = values.get("MCP_ALLOWED_ORIGINS", "")
    allowed_origins.extend(
        origin.strip() for origin in configured_origins.split(",") if origin.strip()
    )
    return Settings(
        api_key=api_key,
        port=port,
        allowed_hosts=tuple(dict.fromkeys(allowed_hosts)),
        allowed_origins=tuple(dict.fromkeys(allowed_origins)),
    )
