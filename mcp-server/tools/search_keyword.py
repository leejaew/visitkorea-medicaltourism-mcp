from typing import Optional
from utils.api_client import call_api


def search_medical_by_keyword(
    lang_div_cd: str,
    keyword: str,
    arrange: Optional[str] = None,
    l_dong_regn_cd: Optional[str] = None,
    l_dong_signgu_cd: Optional[str] = None,
    num_of_rows: int = 10,
    page_no: int = 1,
) -> list:
    """
    Search medical tourism facilities by keyword.

    Args:
        lang_div_cd: Language code — ENG, JPN, CHS, or RUS.
        keyword: Search keyword. Non-English strings should be URL-encoded.
        arrange: Sort order — 'A'=title, 'C'=modified (default), 'D'=created;
                 'O'/'Q'/'R' = same but image-only results.
        l_dong_regn_cd: Province filter.
        l_dong_signgu_cd: City/county filter (requires l_dong_regn_cd).
        num_of_rows: Results per page (default 10).
        page_no: Page number (default 1).

    Returns:
        List of facility dicts with fields like contentId, title, baseAddr,
        detailAddr, zipCd, mapX, mapY, tel, orgImage, thumbImage,
        lDongRegnCd, lDongSignguCd, regDt, mdfcnDt.
    """
    params = {
        "langDivCd": lang_div_cd,
        "keyword": keyword,
        "arrange": arrange,
        "lDongRegnCd": l_dong_regn_cd,
        "lDongSignguCd": l_dong_signgu_cd,
    }
    return call_api("searchKeyword", params=params, num_of_rows=num_of_rows, page_no=page_no)
