"""MCP server factory and lifecycle composition root."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator

from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings
from starlette.requests import Request
from starlette.responses import JSONResponse

from .client import KtoClient
from .config import Settings, load_settings
from .tools import register_tools


def _configure_logging() -> None:
    """Prevent HTTP client request URLs from exposing query-string secrets."""
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)


@asynccontextmanager
async def _lifespan(
    _server: FastMCP,
    settings: Settings,
) -> AsyncIterator[dict[str, KtoClient]]:
    client = KtoClient(settings)
    try:
        yield {"client": client}
    finally:
        await client.aclose()


def create_server(settings: Settings | None = None) -> FastMCP:
    """Construct the MCP app without starting a transport or network client."""
    _configure_logging()
    resolved = settings or load_settings()

    @asynccontextmanager
    async def lifespan(server: FastMCP) -> AsyncIterator[dict[str, KtoClient]]:
        async with _lifespan(server, resolved) as context:
            yield context

    server = FastMCP(
        "visitkorea-medicaltourism",
        host="0.0.0.0",
        port=resolved.port,
        stateless_http=True,
        lifespan=lifespan,
        transport_security=TransportSecuritySettings(
            allowed_hosts=list(resolved.allowed_hosts),
            allowed_origins=list(resolved.allowed_origins),
        ),
    )
    register_tools(server)

    @server.custom_route("/healthz", methods=["GET"])
    async def healthz(_request: Request) -> JSONResponse:
        """Lightweight liveness probe for production health checks."""
        return JSONResponse(
            {"status": "ok", "server": "visitkorea-medicaltourism"}
        )

    return server


def run() -> None:
    """Load configuration, construct the app, and start Streamable HTTP."""
    create_server().run(transport="streamable-http")