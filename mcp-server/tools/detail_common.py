from utils.api_client import call_api


def get_detail_common(
    lang_div_cd: str,
    content_id: str,
    num_of_rows: int = 1,
    page_no: int = 1,
) -> list:
    """
    Retrieve common detail information for a specific content item.
    Includes title, address, GPS coordinates, phone, homepage, and overview text.

    Note: The API returns 'mapx' and 'mapy' in lowercase; this tool normalises
    them to 'mapX' and 'mapY'.

    Args:
        lang_div_cd: Language code — ENG, JPN, CHS, or RUS.
        content_id: Content ID obtained from any list tool.
        num_of_rows: Results per page (default 1).
        page_no: Page number (default 1).

    Returns:
        List containing the detail dict with fields: contentId, title, overview,
        homepage, tel, baseAddr, detailAddr, zipCd, mapX, mapY, orgImage,
        thumbImage, lDongRegnCd, lDongSignguCd, regDt, mdfcnDt.
    """
    params = {
        "langDivCd": lang_div_cd,
        "contentId": content_id,
    }
    items = call_api("detailCommon", params=params, num_of_rows=num_of_rows, page_no=page_no)

    normalised = []
    for item in items:
        if "mapx" in item:
            item["mapX"] = item.pop("mapx")
        if "mapy" in item:
            item["mapY"] = item.pop("mapy")
        normalised.append(item)

    return normalised
