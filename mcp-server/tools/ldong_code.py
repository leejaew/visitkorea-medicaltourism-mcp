from typing import Optional
from utils.api_client import call_api
from utils.validation import validate_lang, validate_pagination


async def get_ldong_code(
    lang_div_cd: str,
    l_dong_regn_cd: Optional[str] = None,
    l_dong_list_yn: Optional[str] = None,
    num_of_rows: int = 10,
    page_no: int = 1,
) -> list:
    """
    Retrieve legal administrative district (법정동) codes.
    Returns province (시도) and city/county (시군구) codes required for
    area-based or keyword searches.

    Args:
        lang_div_cd: Language code — ENG, JPN, CHS, KOR, or RUS.
        l_dong_regn_cd: Province code (e.g. '11' = Seoul). Filters by province.
        l_dong_list_yn: 'N' = return code list only (default); 'Y' = full district list.
        num_of_rows: Results per page (1–100, default 10).
        page_no: Page number (default 1).

    Returns:
        List of district code dicts with fields like code, name,
        lDongRegnCd, lDongRegnNm, lDongSignguCd, lDongSignguNm.
    """
    lang_div_cd = validate_lang(lang_div_cd)
    num_of_rows, page_no = validate_pagination(num_of_rows, page_no)

    params = {
        "langDivCd": lang_div_cd,
        "lDongRegnCd": l_dong_regn_cd,
        "lDongListYn": l_dong_list_yn,
    }
    return await call_api(
        "ldongCode", params=params, num_of_rows=num_of_rows, page_no=page_no
    )
