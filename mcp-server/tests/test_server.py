from __future__ import annotations

import asyncio
import logging
import os
import subprocess
import sys
import unittest
from unittest.mock import AsyncMock, patch

import httpx

from visitkorea_mcp.cache import TTLCache
from visitkorea_mcp.client import KtoClient
from visitkorea_mcp.config import Settings, load_settings
from visitkorea_mcp.errors import AuthError, InvalidRequest, RateLimitError, UpstreamError
from visitkorea_mcp.limiter import TokenBucket
from visitkorea_mcp.server import _lifespan, create_server
from visitkorea_mcp.validation import validate_date, validate_gps


def settings() -> Settings:
    return Settings(api_key="encoded/decoded-safe-test-key")


class ValidationTests(unittest.TestCase):
    def test_default_hosts_allow_local_proxy_requests(self) -> None:
        defaults = Settings(api_key="test").allowed_hosts
        self.assertIn("localhost", defaults)
        self.assertIn("localhost:*", defaults)

    def test_settings_normalize_key_and_configure_public_host(self) -> None:
        loaded = load_settings(
            {
                "VISITKOREA_API_KEY": "encoded%2Fkey",
                "PORT": "9000",
                "REPLIT_DOMAINS": "example.replit.app",
            }
        )
        self.assertEqual(loaded.api_key, "encoded/key")
        self.assertEqual(loaded.port, 9000)
        self.assertIn("example.replit.app", loaded.allowed_hosts)
        self.assertIn("example.replit.app:*", loaded.allowed_hosts)
        self.assertIn("https://example.replit.app", loaded.allowed_origins)

    def test_date_rejects_impossible_calendar_date(self) -> None:
        with self.assertRaises(InvalidRequest):
            validate_date("20241399")

    def test_gps_rejects_non_finite_values(self) -> None:
        with self.assertRaises(InvalidRequest):
            validate_gps(float("nan"), 37.5)


class CacheTests(unittest.TestCase):
    def test_cache_returns_defensive_copy_and_evicts_oldest(self) -> None:
        cache = TTLCache(max_entries=1)
        first = {"items": [{"name": "original"}]}
        cache.set("first", first, 60)
        first["items"][0]["name"] = "caller mutation"
        hit, value = cache.get("first")
        self.assertTrue(hit)
        self.assertEqual(value["items"][0]["name"], "original")
        cache.set("second", {"value": 2}, 60)
        self.assertFalse(cache.get("first")[0])

    def test_cache_key_excludes_service_key_and_uses_full_digest(self) -> None:
        key = TTLCache.make_key("endpoint", {"serviceKey": "a", "q": "x"})
        same = TTLCache.make_key("endpoint", {"serviceKey": "b", "q": "x"})
        self.assertEqual(key, same)
        self.assertEqual(len(key), 64)


class LimiterTests(unittest.IsolatedAsyncioTestCase):
    async def test_limiter_reports_retry_after(self) -> None:
        limiter = TokenBucket(rate=0.1, capacity=1)
        await limiter.acquire()
        with self.assertRaises(RateLimitError) as raised:
            await limiter.acquire()
        self.assertGreaterEqual(raised.exception.retry_after, 1)


class ClientTests(unittest.IsolatedAsyncioTestCase):
    async def test_client_parses_success_and_isolates_cache_values(self) -> None:
        payload = {
            "response": {
                "header": {"resultCode": "00"},
                "body": {
                    "totalCount": 1,
                    "items": {"item": {"contentId": "1", "title": "Seoul"}},
                },
            }
        }

        async def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json=payload, request=request)

        client = KtoClient(
            settings(), http_client=httpx.AsyncClient(transport=httpx.MockTransport(handler))
        )
        try:
            first = await client.call_api("areaBasedList", {"langDivCd": "ENG"})
            first[0]["title"] = "mutated"
            second = await client.call_api("areaBasedList", {"langDivCd": "ENG"})
            self.assertEqual(second[0]["title"], "Seoul")
        finally:
            await client._http.aclose()

    async def test_client_retries_5xx_without_sleeping_after_final_attempt(self) -> None:
        attempts = 0

        async def handler(request: httpx.Request) -> httpx.Response:
            nonlocal attempts
            attempts += 1
            if attempts < 2:
                return httpx.Response(503, request=request)
            return httpx.Response(
                200,
                json={
                    "response": {
                        "header": {"resultCode": "03"},
                        "body": {},
                    }
                },
                request=request,
            )

        client = KtoClient(
            settings(), http_client=httpx.AsyncClient(transport=httpx.MockTransport(handler))
        )
        try:
            with patch("visitkorea_mcp.client.asyncio.sleep", new=AsyncMock()):
                self.assertEqual(await client.call_api("areaBasedList"), [])
            self.assertEqual(attempts, 2)
        finally:
            await client._http.aclose()

    async def test_client_maps_secret_errors_without_exposing_key(self) -> None:
        async def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(
                200,
                json={
                    "response": {
                        "header": {"resultCode": "30", "resultMsg": "secret"},
                        "body": {},
                    }
                },
                request=request,
            )

        client = KtoClient(
            settings(), http_client=httpx.AsyncClient(transport=httpx.MockTransport(handler))
        )
        try:
            with self.assertRaises(AuthError) as raised:
                await client.call_api("areaBasedList")
            self.assertNotIn("encoded/decoded-safe-test-key", str(raised.exception))
        finally:
            await client._http.aclose()

    async def test_client_honors_bounded_retry_after_for_429(self) -> None:
        async def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(
                429, headers={"Retry-After": "9999"}, request=request
            )

        client = KtoClient(
            settings(), http_client=httpx.AsyncClient(transport=httpx.MockTransport(handler))
        )
        try:
            with patch("visitkorea_mcp.client.asyncio.sleep", new=AsyncMock()):
                with self.assertRaises(UpstreamError) as raised:
                    await client.call_api("areaBasedList")
            self.assertIn("30s", str(raised.exception))
        finally:
            await client._http.aclose()


class ServerContractTests(unittest.TestCase):
    def test_server_suppresses_secret_bearing_http_request_logs(self) -> None:
        create_server(settings())
        self.assertGreaterEqual(logging.getLogger("httpx").level, logging.WARNING)
        self.assertGreaterEqual(logging.getLogger("httpcore").level, logging.WARNING)

    def test_server_registers_exactly_eight_public_tools(self) -> None:
        server = create_server(settings())
        tools = server._tool_manager._tools
        self.assertEqual(
            list(tools),
            [
                "get_ldong_code",
                "get_area_based_list",
                "get_location_based_list",
                "search_medical_by_keyword",
                "get_medical_sync_list",
                "get_detail_common",
                "get_detail_intro",
                "get_detail_medical",
            ],
        )
        schema = tools["get_detail_common"].parameters
        self.assertNotIn("ctx", schema["properties"])

    def test_lifespan_closes_owned_http_client(self) -> None:
        async def exercise() -> None:
            server = create_server(settings())
            async with _lifespan(server, settings()) as context:
                self.assertFalse(context["client"]._http.is_closed)
            self.assertTrue(context["client"]._http.is_closed)

        asyncio.run(exercise())

    def test_import_does_not_require_secret(self) -> None:
        env = os.environ.copy()
        env.pop("VISITKOREA_API_KEY", None)
        env["PYTHONPATH"] = os.path.abspath("mcp-server")
        result = subprocess.run(
            [sys.executable, "-c", "import visitkorea_mcp; import visitkorea_mcp.server"],
            env=env,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()