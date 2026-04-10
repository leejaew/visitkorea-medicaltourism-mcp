from utils.api_client import call_api


def get_detail_medical(
    lang_div_cd: str,
    content_id: str,
    num_of_rows: int = 1,
    page_no: int = 1,
) -> list:
    """
    Retrieve medical-specific detail — institution type, medical specialties,
    languages served, history, online reservation status, and SNS info.

    Args:
        lang_div_cd: Language code — ENG, JPN, CHS, or RUS.
        content_id: Content ID obtained from any list tool.
        num_of_rows: Results per page (default 1).
        page_no: Page number (default 1).

    Returns:
        List containing the medical detail dict with fields: contentid,
        mdclTursmDivInfo, svcLangInfo, hmpgInfo, prSnsInfo, histrCn,
        onlineRsvtPsblYn, gdsCnselCn, insttDevInfo, mainMdlcSubjInfo.
    """
    params = {
        "langDivCd": lang_div_cd,
        "contentId": content_id,
    }
    return call_api("detailMdclTursm", params=params, num_of_rows=num_of_rows, page_no=page_no)
