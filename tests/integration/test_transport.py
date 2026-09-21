import json
import unittest
from unittest.mock import patch

import httpx

from mcp_server.config import Settings
from mcp_server.server import create_server


class TransportTests(unittest.TestCase):
    def test_server_is_stateless_and_has_health_route(self):
        server = create_server(Settings(api_key="test-key"))
        self.assertTrue(server.settings.stateless_http)
        self.assertIn(
            "/healthz", [route.path for route in server._custom_starlette_routes]
        )


class FakeClient:
    async def call_api(self, endpoint, params=None, num_of_rows=10, page_no=1):
        return [{"endpoint": endpoint}]

    async def aclose(self):
        return None


def parse_sse(body):
    data = next(
        line.removeprefix("data: ")
        for line in body.splitlines()
        if line.startswith("data: ")
    )
    return json.loads(data)


async def get_json(client, path):
    async with client.stream("GET", path) as response:
        await response.aread()
        return response.json()


async def post_rpc(client, headers, payload):
    async with client.stream("POST", "/mcp", headers=headers, json=payload) as response:
        await response.aread()
        if response.headers["content-type"].startswith("application/json"):
            return response.json()
        return parse_sse(response.text)


class StreamableHttpTests(unittest.IsolatedAsyncioTestCase):
    async def test_initialize_list_and_call_over_streamable_http(self):
        with patch("mcp_server.server.KtoClient", lambda _settings: FakeClient()):
            server = create_server(Settings(api_key="test-key"))
            # The MCP SDK's in-process SSE response leaves an AnyIO receive stream
            # for garbage collection. JSON response mode exercises the same
            # Streamable HTTP request path with deterministic stream cleanup.
            server.settings.json_response = True
            app = server.streamable_http_app()
            transport = httpx.ASGITransport(app=app)
            headers = {"Accept": "application/json, text/event-stream"}

            async with (
                app.router.lifespan_context(app),
                httpx.AsyncClient(
                    transport=transport, base_url="http://localhost"
                ) as client,
            ):
                health = await get_json(client, "/healthz")
                initialize = await post_rpc(
                    client,
                    headers,
                    {
                        "jsonrpc": "2.0",
                        "id": 1,
                        "method": "initialize",
                        "params": {
                            "protocolVersion": "2025-06-18",
                            "capabilities": {},
                            "clientInfo": {"name": "test", "version": "1"},
                        },
                    },
                )
                tools = await post_rpc(
                    client,
                    headers,
                    {
                        "jsonrpc": "2.0",
                        "id": 2,
                        "method": "tools/list",
                        "params": {},
                    },
                )
                call = await post_rpc(
                    client,
                    headers,
                    {
                        "jsonrpc": "2.0",
                        "id": 3,
                        "method": "tools/call",
                        "params": {
                            "name": "get_ldong_code",
                            "arguments": {"lang_div_cd": "ENG"},
                        },
                    },
                )

        self.assertEqual(
            health, {"status": "ok", "server": "visitkorea-medicaltourism"}
        )
        self.assertEqual(initialize["result"]["protocolVersion"], "2025-06-18")
        self.assertEqual(len(tools["result"]["tools"]), 8)
        call_result = call["result"]
        self.assertFalse(call_result["isError"])
        self.assertEqual(
            call_result["structuredContent"]["result"],
            [{"endpoint": "ldongCode"}],
        )
