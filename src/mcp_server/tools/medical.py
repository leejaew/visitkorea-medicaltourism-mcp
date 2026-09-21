"""Thin MCP adapters: validation and delegation only."""

from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import Context

from ..errors.application import InvalidRequest
from ..services.medical_tourism import MedicalTourismService
from ..services.validation import (
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


def _service(ctx: Context | None) -> MedicalTourismService:
    if ctx is None:
        raise RuntimeError("MCP request context is required.")
    context = ctx.request_context.lifespan_context
    client = context.get("client") if isinstance(context, dict) else None
    if client is None or not callable(getattr(client, "call_api", None)):
        raise RuntimeError("MCP server client is unavailable.")
    return MedicalTourismService(client)


def _codes(**values: Any) -> dict[str, str | None]:
    return {key: validate_optional_code(value, key) for key, value in values.items()}


def _page(rows: int, page: int) -> tuple[int, int]:
    return validate_pagination(rows, page)


async def get_ldong_code(
    lang_div_cd: str,
    l_dong_regn_cd: str | None = None,
    l_dong_list_yn: str | None = None,
    num_of_rows: int = 10,
    page_no: int = 1,
    *,
    ctx: Context | None = None,
) -> list[dict[str, Any]]:
    """Retrieve legal administrative district codes."""
    lang_div_cd = validate_lang(lang_div_cd)
    num_of_rows, page_no = _page(num_of_rows, page_no)
    if l_dong_list_yn is not None:
        l_dong_list_yn = validate_text(l_dong_list_yn, "l_dong_list_yn", 1).upper()
        if l_dong_list_yn not in {"Y", "N"}:
            raise InvalidRequest("l_dong_list_yn must be 'Y' or 'N'.")
    return await _service(ctx).ldong_code(
        {
            "langDivCd": lang_div_cd,
            **_codes(lDongRegnCd=l_dong_regn_cd),
            "lDongListYn": l_dong_list_yn,
        },
        num_of_rows,
        page_no,
    )


async def get_area_based_list(
    lang_div_cd: str,
    l_dong_regn_cd: str | None = None,
    l_dong_signgu_cd: str | None = None,
    arrange: str | None = None,
    mdfcn_dt: str | None = None,
    num_of_rows: int = 10,
    page_no: int = 1,
    *,
    ctx: Context | None = None,
) -> list[dict[str, Any]]:
    """List medical tourism facilities filtered by administrative region."""
    lang_div_cd = validate_lang(lang_div_cd)
    num_of_rows, page_no = _page(num_of_rows, page_no)
    if arrange is not None:
        arrange = validate_arrange(arrange)
    if mdfcn_dt is not None:
        mdfcn_dt = validate_date(mdfcn_dt)
    return await _service(ctx).area_based_list(
        {
            "langDivCd": lang_div_cd,
            **_codes(lDongRegnCd=l_dong_regn_cd, lDongSignguCd=l_dong_signgu_cd),
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
    arrange: str | None = None,
    l_dong_regn_cd: str | None = None,
    l_dong_signgu_cd: str | None = None,
    mdfcn_dt: str | None = None,
    num_of_rows: int = 10,
    page_no: int = 1,
    *,
    ctx: Context | None = None,
) -> list[dict[str, Any]]:
    """List medical tourism facilities within a GPS radius."""
    lang_div_cd = validate_lang(lang_div_cd)
    map_x, map_y = validate_gps(map_x, map_y)
    radius = validate_radius(radius)
    num_of_rows, page_no = _page(num_of_rows, page_no)
    if arrange is not None:
        arrange = validate_arrange(arrange, location=True)
    if mdfcn_dt is not None:
        mdfcn_dt = validate_date(mdfcn_dt)
    return await _service(ctx).location_based_list(
        {
            "langDivCd": lang_div_cd,
            "mapX": map_x,
            "mapY": map_y,
            "radius": radius,
            "arrange": arrange,
            "mdfcnDt": mdfcn_dt,
            **_codes(lDongRegnCd=l_dong_regn_cd, lDongSignguCd=l_dong_signgu_cd),
        },
        num_of_rows,
        page_no,
    )


async def search_medical_by_keyword(
    lang_div_cd: str,
    keyword: str,
    arrange: str | None = None,
    l_dong_regn_cd: str | None = None,
    l_dong_signgu_cd: str | None = None,
    num_of_rows: int = 10,
    page_no: int = 1,
    *,
    ctx: Context | None = None,
) -> list[dict[str, Any]]:
    """Search medical tourism facilities by keyword."""
    lang_div_cd = validate_lang(lang_div_cd)
    keyword = validate_text(keyword, "keyword", 200)
    num_of_rows, page_no = _page(num_of_rows, page_no)
    if arrange is not None:
        arrange = validate_arrange(arrange)
    return await _service(ctx).search_keyword(
        {
            "langDivCd": lang_div_cd,
            "keyword": keyword,
            "arrange": arrange,
            **_codes(lDongRegnCd=l_dong_regn_cd, lDongSignguCd=l_dong_signgu_cd),
        },
        num_of_rows,
        page_no,
    )


async def get_medical_sync_list(
    lang_div_cd: str,
    arrange: str | None = None,
    showflag: str | None = None,
    mdfcn_dt: str | None = None,
    l_dong_regn_cd: str | None = None,
    l_dong_signgu_cd: str | None = None,
    old_content_id: str | None = None,
    num_of_rows: int = 10,
    page_no: int = 1,
    *,
    ctx: Context | None = None,
) -> list[dict[str, Any]]:
    """Retrieve the medical tourism synchronization list."""
    lang_div_cd = validate_lang(lang_div_cd)
    num_of_rows, page_no = _page(num_of_rows, page_no)
    if arrange is not None:
        arrange = validate_arrange(arrange)
    if showflag is not None:
        showflag = validate_showflag(showflag)
    if mdfcn_dt is not None:
        mdfcn_dt = validate_date(mdfcn_dt)
    if old_content_id is not None:
        old_content_id = validate_text(old_content_id, "old_content_id", 128)
    return await _service(ctx).sync_list(
        {
            "langDivCd": lang_div_cd,
            "arrange": arrange,
            "showflag": showflag,
            "mdfcnDt": mdfcn_dt,
            "oldContentId": old_content_id,
            **_codes(lDongRegnCd=l_dong_regn_cd, lDongSignguCd=l_dong_signgu_cd),
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
    num_of_rows, page_no = _page(num_of_rows, page_no)
    return await _service(ctx).detail_common(
        {"langDivCd": lang_div_cd, "contentId": content_id},
        num_of_rows,
        page_no,
    )


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
    num_of_rows, page_no = _page(num_of_rows, page_no)
    return await _service(ctx).detail_intro(
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
    num_of_rows, page_no = _page(num_of_rows, page_no)
    return await _service(ctx).detail_medical(
        {"langDivCd": lang_div_cd, "contentId": content_id},
        num_of_rows,
        page_no,
    )
