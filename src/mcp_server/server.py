"""FastMCP composition root; construction does not start a server."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings
from starlette.requests import Request
from starlette.responses import JSONResponse

from .clients.visitkorea import KtoClient
from .config import Settings, load_settings
from .observability.logging import configure_logging
from .tools.registry import register_tools


@asynccontextmanager
async def _lifespan(
    _server: FastMCP, settings: Settings
) -> AsyncIterator[dict[str, KtoClient]]:
    client = KtoClient(settings)
    try:
        yield {"client": client}
    finally:
        await client.aclose()


def create_server(settings: Settings | None = None) -> FastMCP:
    configure_logging()
    resolved = settings or load_settings()

    @asynccontextmanager
    async def lifespan(server: FastMCP):
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
        return JSONResponse({"status": "ok", "server": "visitkorea-medicaltourism"})

    return server
