from utils.api_client import call_api
from utils.validation import validate_lang, validate_pagination


async def get_detail_common(
    lang_div_cd: str,
    content_id: str,
    num_of_rows: int = 1,
    page_no: int = 1,
) -> list:
    """
    Retrieve common detail information for a specific content item.
    Includes title, address, GPS coordinates, phone, homepage, and overview text.

    Note: The API returns 'mapx' and 'mapy' in lowercase; this tool normalises
    them to 'mapX' and 'mapY' for consistency with list-endpoint field names.

    Args:
        lang_div_cd: Language code — ENG, JPN, CHS, KOR, or RUS.
        content_id: Content ID obtained from any list tool.
        num_of_rows: Results per page (1–100, default 1).
        page_no: Page number (default 1).

    Returns:
        List containing the detail dict with fields: contentId, title, overview,
        homepage, tel, baseAddr, detailAddr, zipCd, mapX, mapY, orgImage,
        thumbImage, lDongRegnCd, lDongSignguCd, regDt, mdfcnDt.
    """
    lang_div_cd = validate_lang(lang_div_cd)
    num_of_rows, page_no = validate_pagination(num_of_rows, page_no)

    if not str(content_id).strip():
        raise ValueError("content_id must not be empty.")

    params = {
        "langDivCd": lang_div_cd,
        "contentId": str(content_id).strip(),
    }
    items = await call_api(
        "detailCommon", params=params, num_of_rows=num_of_rows, page_no=page_no
    )

    normalised = []
    for item in items:
        if "mapx" in item:
            item["mapX"] = item.pop("mapx")
        if "mapy" in item:
            item["mapY"] = item.pop("mapy")
        normalised.append(item)

    return normalised
