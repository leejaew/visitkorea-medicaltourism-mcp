from utils.api_client import call_api
from utils.validation import validate_lang, validate_pagination


async def get_detail_medical(
    lang_div_cd: str,
    content_id: str,
    num_of_rows: int = 1,
    page_no: int = 1,
) -> list:
    """
    Retrieve medical-specific detail — institution type, medical specialties,
    languages served, history, online reservation status, and SNS info.

    Args:
        lang_div_cd: Language code — ENG, JPN, CHS, KOR, or RUS.
        content_id: Content ID obtained from any list tool.
        num_of_rows: Results per page (1–100, default 1).
        page_no: Page number (default 1).

    Returns:
        List containing the medical detail dict with fields: contentid,
        mdclTursmDivInfo, svcLangInfo, hmpgInfo, prSnsInfo, histrCn,
        onlineRsvtPsblYn, gdsCnselCn, insttDevInfo, mainMdlcSubjInfo.
    """
    lang_div_cd = validate_lang(lang_div_cd)
    num_of_rows, page_no = validate_pagination(num_of_rows, page_no)

    if not str(content_id).strip():
        raise ValueError("content_id must not be empty.")

    params = {
        "langDivCd": lang_div_cd,
        "contentId": str(content_id).strip(),
    }
    return await call_api(
        "detailMdclTursm", params=params, num_of_rows=num_of_rows, page_no=page_no
    )
