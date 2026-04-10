from typing import Optional
from utils.api_client import call_api


def get_location_based_list(
    lang_div_cd: str,
    map_x: float,
    map_y: float,
    radius: int,
    arrange: Optional[str] = None,
    l_dong_regn_cd: Optional[str] = None,
    l_dong_signgu_cd: Optional[str] = None,
    mdfcn_dt: Optional[str] = None,
    num_of_rows: int = 10,
    page_no: int = 1,
) -> list:
    """
    Retrieve medical tourism facilities within a radius of GPS coordinates.

    Args:
        lang_div_cd: Language code — ENG, JPN, CHS, or RUS.
        map_x: GPS longitude in WGS84 (e.g. 126.981611).
        map_y: GPS latitude in WGS84 (e.g. 37.568477).
        radius: Search radius in metres. Maximum 20000 (20 km).
        arrange: Sort order — 'A'=title, 'C'=modified, 'D'=created, 'E'=distance;
                 'O'/'Q'/'R'/'S' = same but image-only results.
        l_dong_regn_cd: Optional province filter.
        l_dong_signgu_cd: Optional city/county filter (requires l_dong_regn_cd).
        mdfcn_dt: Filter by modified date in YYYYMMDD format.
        num_of_rows: Results per page (default 10).
        page_no: Page number (default 1).

    Returns:
        List of facility dicts, same as get_area_based_list plus 'dist'
        (distance in metres from provided coordinates).
    """
    params = {
        "langDivCd": lang_div_cd,
        "mapX": map_x,
        "mapY": map_y,
        "radius": radius,
        "arrange": arrange,
        "lDongRegnCd": l_dong_regn_cd,
        "lDongSignguCd": l_dong_signgu_cd,
        "mdfcnDt": mdfcn_dt,
    }
    return call_api("locationBasedList", params=params, num_of_rows=num_of_rows, page_no=page_no)
