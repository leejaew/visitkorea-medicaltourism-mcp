from typing import Optional
from utils.api_client import call_api
from utils.validation import (
    validate_lang,
    validate_pagination,
    validate_arrange,
    validate_date,
    validate_showflag,
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
) -> list:
    """
    Retrieve the full synchronisation list of medical tourism content.
    Intended for downstream database sync workflows. Includes display status
    and legacy content ID mapping.

    Args:
        lang_div_cd: Language code — ENG, JPN, CHS, KOR, or RUS.
        arrange: Sort order — 'A'=title, 'C'=modified (default), 'D'=created;
                 'O'/'Q'/'R' = same but image-only results.
        showflag: Display flag — '1'=visible, '0'=hidden.
        mdfcn_dt: Filter by modified date in YYYYMMDD format.
        l_dong_regn_cd: Province filter.
        l_dong_signgu_cd: City/county filter (requires l_dong_regn_cd).
        old_content_id: Previous content ID for database re-key lookups.
        num_of_rows: Results per page (1–100, default 10).
        page_no: Page number (default 1).

    Returns:
        List of facility dicts, same as get_area_based_list plus 'showflag'
        and 'oldContentId'.
    """
    lang_div_cd = validate_lang(lang_div_cd)
    num_of_rows, page_no = validate_pagination(num_of_rows, page_no)
    if arrange is not None:
        arrange = validate_arrange(arrange)
    if mdfcn_dt is not None:
        mdfcn_dt = validate_date(mdfcn_dt)
    if showflag is not None:
        showflag = validate_showflag(showflag)

    params = {
        "langDivCd": lang_div_cd,
        "arrange": arrange,
        "showflag": showflag,
        "mdfcnDt": mdfcn_dt,
        "lDongRegnCd": l_dong_regn_cd,
        "lDongSignguCd": l_dong_signgu_cd,
        "oldContentId": old_content_id,
    }
    return await call_api(
        "mdclTursmSyncList", params=params, num_of_rows=num_of_rows, page_no=page_no
    )
