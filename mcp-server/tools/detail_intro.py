from utils.api_client import call_api


def get_detail_intro(
    lang_div_cd: str,
    content_id: str,
    num_of_rows: int = 1,
    page_no: int = 1,
) -> list:
    """
    Retrieve introductory facility detail — operating hours, rest days,
    parking, capacity, and age suitability.

    Args:
        lang_div_cd: Language code — ENG, JPN, CHS, or RUS.
        content_id: Content ID obtained from any list tool.
        num_of_rows: Results per page (default 1).
        page_no: Page number (default 1).

    Returns:
        List containing the intro detail dict with fields: contentId,
        accomcount, expagerange, expguide, heritage1, infocenter,
        opendate, parking, restdate, useseason, usetime.
    """
    params = {
        "langDivCd": lang_div_cd,
        "contentId": content_id,
    }
    return call_api("detailIntro", params=params, num_of_rows=num_of_rows, page_no=page_no)
