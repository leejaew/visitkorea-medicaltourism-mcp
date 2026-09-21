"""Plain-Python application service for medical tourism operations."""

from __future__ import annotations

from typing import Any, Protocol

Params = dict[str, Any]
Items = list[dict[str, Any]]


class MedicalClient(Protocol):
    async def call_api(
        self,
        endpoint: str,
        params: Params,
        num_of_rows: int,
        page_no: int,
    ) -> Items: ...


class MedicalTourismService:
    """Coordinates validation-ready operations without importing MCP."""

    def __init__(self, client: MedicalClient) -> None:
        self.client = client

    async def _list(self, endpoint: str, params: Params, rows: int, page: int) -> Items:
        return await self.client.call_api(endpoint, params, rows, page)

    async def ldong_code(self, params: Params, rows: int, page: int) -> Items:
        return await self._list("ldongCode", params, rows, page)

    async def area_based_list(self, params: Params, rows: int, page: int) -> Items:
        return await self._list("areaBasedList", params, rows, page)

    async def location_based_list(self, params: Params, rows: int, page: int) -> Items:
        return await self._list("locationBasedList", params, rows, page)

    async def search_keyword(self, params: Params, rows: int, page: int) -> Items:
        return await self._list("searchKeyword", params, rows, page)

    async def sync_list(self, params: Params, rows: int, page: int) -> Items:
        return await self._list("mdclTursmSyncList", params, rows, page)

    async def _detail(
        self, endpoint: str, params: Params, rows: int, page: int
    ) -> Items:
        items = await self._list(endpoint, params, rows, page)
        if endpoint == "detailCommon":
            result = []
            for item in items:
                value = dict(item)
                if "mapx" in value:
                    value["mapX"] = value.pop("mapx")
                if "mapy" in value:
                    value["mapY"] = value.pop("mapy")
                result.append(value)
            return result
        return items

    async def detail_common(self, params: Params, rows: int, page: int) -> Items:
        return await self._detail("detailCommon", params, rows, page)

    async def detail_intro(self, params: Params, rows: int, page: int) -> Items:
        return await self._detail("detailIntro", params, rows, page)

    async def detail_medical(self, params: Params, rows: int, page: int) -> Items:
        return await self._detail("detailMdclTursm", params, rows, page)
