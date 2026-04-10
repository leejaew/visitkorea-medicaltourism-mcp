from typing import Optional
from utils.api_client import call_api


def get_area_based_list(
    lang_div_cd: str,
    l_dong_regn_cd: Optional[str] = None,
    l_dong_signgu_cd: Optional[str] = None,
    arrange: Optional[str] = None,
    mdfcn_dt: Optional[str] = None,
    num_of_rows: int = 10,
    page_no: int = 1,
) -> list:
    """
    Retrieve a list of medical tourism facilities filtered by administrative region.

    Args:
        lang_div_cd: Language code — ENG, JPN, CHS, or RUS.
        l_dong_regn_cd: Province code (e.g. '11' = Seoul).
        l_dong_signgu_cd: City/county code. Requires l_dong_regn_cd.
        arrange: Sort order — 'A'=title, 'C'=modified date (default), 'D'=created date;
                 'O'/'Q'/'R' = same but image-only results.
        mdfcn_dt: Filter by content modified date in YYYYMMDD format.
        num_of_rows: Results per page (default 10).
        page_no: Page number (default 1).

    Returns:
        List of facility dicts with fields like contentId, title, baseAddr,
        detailAddr, zipCd, mapX, mapY, tel, orgImage, thumbImage,
        lDongRegnCd, lDongSignguCd, regDt, mdfcnDt.
    """
    params = {
        "langDivCd": lang_div_cd,
        "lDongRegnCd": l_dong_regn_cd,
        "lDongSignguCd": l_dong_signgu_cd,
        "arrange": arrange,
        "mdfcnDt": mdfcn_dt,
    }
    return call_api("areaBasedList", params=params, num_of_rows=num_of_rows, page_no=page_no)
