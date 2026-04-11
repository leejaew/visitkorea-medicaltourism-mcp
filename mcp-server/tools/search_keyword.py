from typing import Optional
from utils.api_client import call_api
from utils.validation import validate_lang, validate_pagination, validate_arrange


async def search_medical_by_keyword(
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
        lang_div_cd: Language code — ENG, JPN, CHS, KOR, or RUS.
        keyword: Search keyword. Non-ASCII strings are passed as-is (httpx handles encoding).
        arrange: Sort order — 'A'=title, 'C'=modified (default), 'D'=created;
                 'O'/'Q'/'R' = same but image-only results.
        l_dong_regn_cd: Province filter.
        l_dong_signgu_cd: City/county filter (requires l_dong_regn_cd).
        num_of_rows: Results per page (1–100, default 10).
        page_no: Page number (default 1).

    Returns:
        List of facility dicts with fields like contentId, title, baseAddr,
        detailAddr, zipCd, mapX, mapY, tel, orgImage, thumbImage,
        lDongRegnCd, lDongSignguCd, regDt, mdfcnDt.
    """
    lang_div_cd = validate_lang(lang_div_cd)
    num_of_rows, page_no = validate_pagination(num_of_rows, page_no)
    if arrange is not None:
        arrange = validate_arrange(arrange)

    keyword = keyword.strip()
    if not keyword:
        raise ValueError("keyword must not be empty.")

    params = {
        "langDivCd": lang_div_cd,
        "keyword": keyword,
        "arrange": arrange,
        "lDongRegnCd": l_dong_regn_cd,
        "lDongSignguCd": l_dong_signgu_cd,
    }
    return await call_api(
        "searchKeyword", params=params, num_of_rows=num_of_rows, page_no=page_no
    )
