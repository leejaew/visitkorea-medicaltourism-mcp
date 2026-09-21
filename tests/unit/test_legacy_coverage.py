import asyncio
import unittest
from unittest.mock import AsyncMock, patch

import httpx

from mcp_server.clients.cache import TTLCache
from mcp_server.clients.limiter import TokenBucket
from mcp_server.clients.visitkorea import KtoClient
from mcp_server.config import Settings, load_settings
from mcp_server.errors.application import (
    AuthError,
    InvalidRequest,
    RateLimitError,
    UpstreamError,
)
from mcp_server.server import _lifespan, create_server
from mcp_server.services.validation import validate_date, validate_gps


def settings():
    return Settings(api_key="encoded/decoded-safe-test-key")


class LegacySettingsAndCacheTests(unittest.TestCase):
    def test_defaults_and_environment_normalization(self):
        self.assertIn("localhost", Settings(api_key="x").allowed_hosts)
        loaded = load_settings(
            {
                "VISITKOREA_API_KEY": "encoded%2Fkey",
                "PORT": "9000",
                "REPLIT_DOMAINS": "example.replit.app",
            }
        )
        self.assertEqual(loaded.api_key, "encoded/key")
        self.assertIn("example.replit.app:*", loaded.allowed_hosts)
        self.assertIn("https://example.replit.app", loaded.allowed_origins)

    def test_validation_rejects_bad_values(self):
        with self.assertRaises(InvalidRequest):
            validate_date("20241399")
        with self.assertRaises(InvalidRequest):
            validate_gps(float("nan"), 37.5)

    def test_cache_is_defensive_bounded_and_secret_blind(self):
        cache = TTLCache(max_entries=1)
        value = {"items": [{"name": "original"}]}
        cache.set("one", value, 60)
        value["items"][0]["name"] = "changed"
        self.assertEqual(cache.get("one")[1]["items"][0]["name"], "original")
        cache.set("two", {}, 60)
        self.assertFalse(cache.get("one")[0])
        self.assertEqual(
            TTLCache.make_key("x", {"serviceKey": "a", "q": "x"}),
            TTLCache.make_key("x", {"serviceKey": "b", "q": "x"}),
        )


class LegacyClientTests(unittest.IsolatedAsyncioTestCase):
    async def test_cache_and_response_mapping(self):
        payload = {
            "response": {
                "header": {"resultCode": "00"},
                "body": {"totalCount": 1, "items": {"item": {"title": "Seoul"}}},
            }
        }

        async def handler(request):
            return httpx.Response(200, json=payload, request=request)

        client = KtoClient(
            settings(),
            http_client=httpx.AsyncClient(transport=httpx.MockTransport(handler)),
        )
        first = await client.call_api("areaBasedList")
        first[0]["title"] = "changed"
        self.assertEqual((await client.call_api("areaBasedList"))[0]["title"], "Seoul")
        await client._http.aclose()

    async def test_retries_and_maps_upstream_errors(self):
        attempts = 0

        async def handler(request):
            nonlocal attempts
            attempts += 1
            if attempts == 1:
                return httpx.Response(503, request=request)
            return httpx.Response(
                200,
                json={"response": {"header": {"resultCode": "03"}, "body": {}}},
                request=request,
            )

        client = KtoClient(
            settings(),
            http_client=httpx.AsyncClient(transport=httpx.MockTransport(handler)),
        )
        with patch("mcp_server.clients.visitkorea.asyncio.sleep", new=AsyncMock()):
            self.assertEqual(await client.call_api("areaBasedList"), [])
        self.assertEqual(attempts, 2)
        await client._http.aclose()

    async def test_auth_and_retry_after_are_safe(self):
        async def auth(request):
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
            settings(),
            http_client=httpx.AsyncClient(transport=httpx.MockTransport(auth)),
        )
        with self.assertRaises(AuthError) as error:
            await client.call_api("areaBasedList")
        self.assertNotIn(settings().api_key, str(error.exception))
        await client._http.aclose()

        async def limited(request):
            return httpx.Response(429, headers={"Retry-After": "9999"}, request=request)

        client = KtoClient(
            settings(),
            http_client=httpx.AsyncClient(transport=httpx.MockTransport(limited)),
        )
        with (
            patch("mcp_server.clients.visitkorea.asyncio.sleep", new=AsyncMock()),
            self.assertRaises(UpstreamError) as error,
        ):
            await client.call_api("areaBasedList")
        self.assertIn("30s", str(error.exception))
        await client._http.aclose()


class LegacyLifecycleTests(unittest.TestCase):
    def test_limiter_and_lifespan(self):
        async def exercise():
            limiter = TokenBucket(rate=0.1, capacity=1)
            await limiter.acquire()
            with self.assertRaises(RateLimitError):
                await limiter.acquire()
            server = create_server(settings())
            async with _lifespan(server, settings()) as context:
                self.assertFalse(context["client"]._http.is_closed)
            self.assertTrue(context["client"]._http.is_closed)

        asyncio.run(exercise())
