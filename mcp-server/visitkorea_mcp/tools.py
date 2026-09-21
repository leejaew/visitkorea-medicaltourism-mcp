"""Thin MCP tool adapters for the public VisitKorea API surface."""

from __future__ import annotations

from typing import Any, Optional

from mcp.server.fastmcp import Context

from .client import KtoClient
from .errors import InvalidRequest
from .validation import (
    validate_arrange,
    validate_content_id,
    validate_date,
    validate_gps,
    validate_lang,
    validate_optional_code,
    validate_pagination,
    validate_radius,
    validate_showflag,
    validate_text,
)


def _client(ctx: Context | None) -> KtoClient:
    if ctx is None:
        raise RuntimeError("MCP request context is required.")
    lifespan = ctx.request_context.lifespan_context
    if not isinstance(lifespan, dict) or not isinstance(lifespan.get("client"), KtoClient):
        raise RuntimeError("MCP server client is unavailable.")
    return lifespan["client"]


def _codes(**values: Any) -> dict[str, str | None]:
    return {
        key: validate_optional_code(value, key)
        for key, value in values.items()
    }


async def get_ldong_code(
    lang_div_cd: str,
    l_dong_regn_cd: Optional[str] = None,
    l_dong_list_yn: Optional[str] = None,
    num_of_rows: int = 10,
    page_no: int = 1,
    *,
    ctx: Context | None = None,
) -> list[dict[str, Any]]:
    """Retrieve legal administrative district codes."""
    lang_div_cd = validate_lang(lang_div_cd)
    num_of_rows, page_no = validate_pagination(num_of_rows, page_no)
    codes = _codes(lDongRegnCd=l_dong_regn_cd)
    if l_dong_list_yn is not None:
        l_dong_list_yn = validate_text(l_dong_list_yn, "l_dong_list_yn", 1).upper()
        if l_dong_list_yn not in {"Y", "N"}:
            raise InvalidRequest("l_dong_list_yn must be 'Y' or 'N'.")
    return await _client(ctx).call_api(
        "ldongCode",
        {
            "langDivCd": lang_div_cd,
            **codes,
            "lDongListYn": l_dong_list_yn,
        },
        num_of_rows,
        page_no,
    )


async def get_area_based_list(
    lang_div_cd: str,
    l_dong_regn_cd: Optional[str] = None,
    l_dong_signgu_cd: Optional[str] = None,
    arrange: Optional[str] = None,
    mdfcn_dt: Optional[str] = None,
    num_of_rows: int = 10,
    page_no: int = 1,
    *,
    ctx: Context | None = None,
) -> list[dict[str, Any]]:
    """List medical tourism facilities filtered by administrative region."""
    lang_div_cd = validate_lang(lang_div_cd)
    num_of_rows, page_no = validate_pagination(num_of_rows, page_no)
    if arrange is not None:
        arrange = validate_arrange(arrange)
    if mdfcn_dt is not None:
        mdfcn_dt = validate_date(mdfcn_dt)
    return await _client(ctx).call_api(
        "areaBasedList",
        {
            "langDivCd": lang_div_cd,
            **_codes(
                lDongRegnCd=l_dong_regn_cd,
                lDongSignguCd=l_dong_signgu_cd,
            ),
            "arrange": arrange,
            "mdfcnDt": mdfcn_dt,
        },
        num_of_rows,
        page_no,
    )


async def get_location_based_list(
    lang_div_cd: str,
    map_x: float,
    map_y: float,
    radius: int,
    arrange: Optional[str] = None,
    l_dong_regn_cd: Optional[str] = None,
    l_dong_signgu_cd: Optional[str] = None,
    mdfcn_dt: Optional[str] = None,
    num_of_rows: int = 10,
    page_no: int = 1,
    *,
    ctx: Context | None = None,
) -> list[dict[str, Any]]:
    """List medical tourism facilities within a GPS radius."""
    lang_div_cd = validate_lang(lang_div_cd)
    num_of_rows, page_no = validate_pagination(num_of_rows, page_no)
    map_x, map_y = validate_gps(map_x, map_y)
    radius = validate_radius(radius)
    if arrange is not None:
        arrange = validate_arrange(arrange, location=True)
    if mdfcn_dt is not None:
        mdfcn_dt = validate_date(mdfcn_dt)
    return await _client(ctx).call_api(
        "locationBasedList",
        {
            "langDivCd": lang_div_cd,
            "mapX": map_x,
            "mapY": map_y,
            "radius": radius,
            "arrange": arrange,
            "mdfcnDt": mdfcn_dt,
            **_codes(
                lDongRegnCd=l_dong_regn_cd,
                lDongSignguCd=l_dong_signgu_cd,
            ),
        },
        num_of_rows,
        page_no,
    )


async def search_medical_by_keyword(
    lang_div_cd: str,
    keyword: str,
    arrange: Optional[str] = None,
    l_dong_regn_cd: Optional[str] = None,
    l_dong_signgu_cd: Optional[str] = None,
    num_of_rows: int = 10,
    page_no: int = 1,
    *,
    ctx: Context | None = None,
) -> list[dict[str, Any]]:
    """Search medical tourism facilities by keyword."""
    lang_div_cd = validate_lang(lang_div_cd)
    keyword = validate_text(keyword, "keyword", 200)
    num_of_rows, page_no = validate_pagination(num_of_rows, page_no)
    if arrange is not None:
        arrange = validate_arrange(arrange)
    return await _client(ctx).call_api(
        "searchKeyword",
        {
            "langDivCd": lang_div_cd,
            "keyword": keyword,
            "arrange": arrange,
            **_codes(
                lDongRegnCd=l_dong_regn_cd,
                lDongSignguCd=l_dong_signgu_cd,
            ),
        },
        num_of_rows,
        page_no,
    )


async def get_medical_sync_list(
    lang_div_cd: str,
    arrange: Optional[str] = None,
    showflag: Optional[str] = None,
    mdfcn_dt: Optional[str] = None,
    l_dong_regn_cd: Optional[str] = None,
    l_dong_signgu_cd: Optional[str] = None,
    old_content_id: Optional[str] = None,
    num_of_rows: int = 10,
    page_no: int = 1,
    *,
    ctx: Context | None = None,
) -> list[dict[str, Any]]:
    """Retrieve the medical tourism synchronization list."""
    lang_div_cd = validate_lang(lang_div_cd)
    num_of_rows, page_no = validate_pagination(num_of_rows, page_no)
    if arrange is not None:
        arrange = validate_arrange(arrange)
    if showflag is not None:
        showflag = validate_showflag(showflag)
    if mdfcn_dt is not None:
        mdfcn_dt = validate_date(mdfcn_dt)
    old_content_id = (
        validate_text(old_content_id, "old_content_id", 128)
        if old_content_id is not None
        else None
    )
    return await _client(ctx).call_api(
        "mdclTursmSyncList",
        {
            "langDivCd": lang_div_cd,
            "arrange": arrange,
            "showflag": showflag,
            "mdfcnDt": mdfcn_dt,
            "oldContentId": old_content_id,
            **_codes(
                lDongRegnCd=l_dong_regn_cd,
                lDongSignguCd=l_dong_signgu_cd,
            ),
        },
        num_of_rows,
        page_no,
    )


async def get_detail_common(
    lang_div_cd: str,
    content_id: str,
    num_of_rows: int = 1,
    page_no: int = 1,
    *,
    ctx: Context | None = None,
) -> list[dict[str, Any]]:
    """Retrieve common detail information for a facility."""
    lang_div_cd = validate_lang(lang_div_cd)
    content_id = validate_content_id(content_id)
    num_of_rows, page_no = validate_pagination(num_of_rows, page_no)
    items = await _client(ctx).call_api(
        "detailCommon",
        {"langDivCd": lang_div_cd, "contentId": content_id},
        num_of_rows,
        page_no,
    )
    normalized: list[dict[str, Any]] = []
    for item in items:
        copy_item = dict(item)
        if "mapx" in copy_item:
            copy_item["mapX"] = copy_item.pop("mapx")
        if "mapy" in copy_item:
            copy_item["mapY"] = copy_item.pop("mapy")
        normalized.append(copy_item)
    return normalized


async def get_detail_intro(
    lang_div_cd: str,
    content_id: str,
    num_of_rows: int = 1,
    page_no: int = 1,
    *,
    ctx: Context | None = None,
) -> list[dict[str, Any]]:
    """Retrieve introductory detail information for a facility."""
    lang_div_cd = validate_lang(lang_div_cd)
    content_id = validate_content_id(content_id)
    num_of_rows, page_no = validate_pagination(num_of_rows, page_no)
    return await _client(ctx).call_api(
        "detailIntro",
        {"langDivCd": lang_div_cd, "contentId": content_id},
        num_of_rows,
        page_no,
    )


async def get_detail_medical(
    lang_div_cd: str,
    content_id: str,
    num_of_rows: int = 1,
    page_no: int = 1,
    *,
    ctx: Context | None = None,
) -> list[dict[str, Any]]:
    """Retrieve medical-specific detail information for a facility."""
    lang_div_cd = validate_lang(lang_div_cd)
    content_id = validate_content_id(content_id)
    num_of_rows, page_no = validate_pagination(num_of_rows, page_no)
    return await _client(ctx).call_api(
        "detailMdclTursm",
        {"langDivCd": lang_div_cd, "contentId": content_id},
        num_of_rows,
        page_no,
    )


TOOL_FUNCTIONS = (
    get_ldong_code,
    get_area_based_list,
    get_location_based_list,
    search_medical_by_keyword,
    get_medical_sync_list,
    get_detail_common,
    get_detail_intro,
    get_detail_medical,
)


def register_tools(server: Any) -> None:
    """Register the public tools in a stable, inspectable order."""
    for tool in TOOL_FUNCTIONS:
        server.tool()(tool)