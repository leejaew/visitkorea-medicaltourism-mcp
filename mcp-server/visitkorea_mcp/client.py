"""KTO API adapter: HTTP lifecycle, caching, retries, and response mapping."""

from __future__ import annotations

import asyncio
from email.utils import parsedate_to_datetime
from datetime import datetime, timezone
from typing import Any

import httpx

from .cache import TTLCache
from .config import Settings
from .errors import AuthError, QuotaError, TransportError, UpstreamError
from .limiter import TokenBucket


class KtoClient:
    def __init__(
        self,
        settings: Settings,
        *,
        http_client: httpx.AsyncClient | None = None,
        cache: TTLCache | None = None,
        limiter: TokenBucket | None = None,
    ) -> None:
        self.settings = settings
        self.cache = cache or TTLCache(settings.cache_capacity)
        self.limiter = limiter or TokenBucket()
        self._http = http_client or httpx.AsyncClient(
            timeout=httpx.Timeout(
                settings.request_timeout, connect=settings.connect_timeout
            ),
            limits=httpx.Limits(
                max_connections=settings.max_connections,
                max_keepalive_connections=settings.max_keepalive_connections,
            ),
            verify=True,
        )
        self._owns_http = http_client is None

    async def aclose(self) -> None:
        if self._owns_http:
            await self._http.aclose()

    async def call_api(
        self,
        endpoint: str,
        params: dict[str, Any] | None = None,
        num_of_rows: int = 10,
        page_no: int = 1,
    ) -> list[dict[str, Any]]:
        query = {
            **self.settings.fixed_params,
            "numOfRows": num_of_rows,
            "pageNo": page_no,
        }
        if params:
            query.update({key: value for key, value in params.items() if value is not None})

        cache_key = self.cache.make_key(endpoint, query)
        hit, cached = self.cache.get(cache_key)
        if hit:
            return cached

        await self.limiter.acquire()
        response = await self._request(endpoint, query)
        items = self._parse_response(response)
        self.cache.set(cache_key, items, self.cache.ttl_for(endpoint))
        return items

    async def _request(
        self, endpoint: str, query: dict[str, Any]
    ) -> httpx.Response:
        last_error: Exception | None = None
        for attempt in range(self.settings.max_retries):
            try:
                response = await self._http.get(
                    f"{self.settings.base_url}/{endpoint}", params=query
                )
            except httpx.RequestError as exc:
                last_error = exc
                if attempt + 1 >= self.settings.max_retries:
                    break
                await asyncio.sleep(0.5 * (2**attempt))
                continue

            status = response.status_code
            if status == 429 or status >= 500:
                retry_after = self._retry_after(response) if status == 429 else None
                last_error = UpstreamError(
                    "Upstream service is temporarily unavailable."
                )
                if attempt + 1 >= self.settings.max_retries:
                    if retry_after is not None:
                        raise UpstreamError(
                            f"Upstream rate limit exceeded. Retry after {retry_after}s."
                        )
                    break
                await asyncio.sleep(
                    retry_after if retry_after is not None else 0.5 * (2**attempt)
                )
                continue
            if status >= 400:
                raise UpstreamError(f"Upstream request failed with HTTP {status}.")
            return response

        if isinstance(last_error, UpstreamError):
            raise last_error
        raise TransportError(
            f"Upstream service could not be reached after "
            f"{self.settings.max_retries} attempts."
        ) from None

    @staticmethod
    def _retry_after(response: httpx.Response) -> int:
        value = response.headers.get("Retry-After", "")
        try:
            seconds = int(value)
        except ValueError:
            try:
                date = parsedate_to_datetime(value)
                if date.tzinfo is None:
                    date = date.replace(tzinfo=timezone.utc)
                seconds = max(0, int((date - datetime.now(timezone.utc)).total_seconds()))
            except (TypeError, ValueError, OverflowError):
                seconds = 1
        return max(1, min(seconds, 30))

    @staticmethod
    def _parse_response(response: httpx.Response) -> list[dict[str, Any]]:
        try:
            data = response.json()
        except (ValueError, TypeError) as exc:
            raise UpstreamError("Upstream API returned an invalid JSON response.") from exc
        if not isinstance(data, dict):
            raise UpstreamError("Upstream API returned an invalid response envelope.")

        response_body = data.get("response")
        if not isinstance(response_body, dict):
            raise UpstreamError("Upstream API returned an invalid response envelope.")
        header = response_body.get("header")
        if not isinstance(header, dict):
            raise UpstreamError("Upstream API returned an invalid response header.")

        result_code = str(header.get("resultCode", ""))
        if result_code in {"03"}:
            return []
        if result_code in {"10", "11"}:
            raise UpstreamError("Upstream rejected the request parameters.")
        if result_code == "22":
            raise QuotaError("Upstream daily quota has been exhausted.")
        if result_code in {"30", "31"}:
            raise AuthError("The configured VisitKorea service key was rejected.")
        if result_code not in {"00", "0000"}:
            raise UpstreamError(f"Upstream API returned error code {result_code}.")

        body = response_body.get("body")
        if not isinstance(body, dict):
            raise UpstreamError("Upstream API returned an invalid response body.")
        if body.get("totalCount", 0) == 0:
            return []
        items_wrapper = body.get("items") or {}
        if not isinstance(items_wrapper, dict):
            raise UpstreamError("Upstream API returned invalid items.")
        items = items_wrapper.get("item") or []
        if isinstance(items, dict):
            items = [items]
        if not isinstance(items, list) or not all(isinstance(item, dict) for item in items):
            raise UpstreamError("Upstream API returned invalid item records.")
        return items