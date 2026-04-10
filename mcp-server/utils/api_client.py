import os
import requests
from typing import Any, Optional

BASE_URL = "https://apis.data.go.kr/B551011/MdclTursmService"

ERROR_CODES = {
    "03": "NODATA_ERROR",
    "10": "INVALID_REQUEST_PARAMETER_ERROR",
    "11": "NO_MANDATORY_REQUEST_PARAMETERS_ERROR",
    "22": "LIMITED_NUMBER_OF_SERVICE_REQUESTS_EXCEEDS_ERROR",
    "30": "SERVICE_KEY_IS_NOT_REGISTERED_ERROR",
    "31": "DEADLINE_HAS_EXPIRED_ERROR",
}


def _get_fixed_params() -> dict:
    api_key = os.environ.get("VISITKOREA_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "VISITKOREA_API_KEY is not set. Please add it to Replit Secrets."
        )
    return {
        "MobileOS": "ETC",
        "MobileApp": "VisitKoreaMedicalMCP",
        "_type": "json",
        "serviceKey": api_key,
    }


def call_api(
    endpoint: str,
    params: Optional[dict] = None,
    num_of_rows: int = 10,
    page_no: int = 1,
) -> Any:
    """
    Make a GET request to the MdclTursmService API.
    Returns the items list from the response body, or [] if no data.
    Raises an exception for API error codes.
    """
    url = f"{BASE_URL}/{endpoint}"

    query = _get_fixed_params()
    query["numOfRows"] = num_of_rows
    query["pageNo"] = page_no
    if params:
        query.update({k: v for k, v in params.items() if v is not None})

    response = requests.get(url, params=query, timeout=30)
    response.raise_for_status()

    data = response.json()

    response_body = data.get("response", {})
    header = response_body.get("header", {})
    result_code = str(header.get("resultCode", ""))
    result_msg = header.get("resultMsg", "")

    if result_code in ("00", "0000"):
        pass
    elif result_code == "03":
        return []
    elif result_code == "10":
        raise ValueError(
            f"INVALID_REQUEST_PARAMETER_ERROR: Check your query parameters. "
            f"API message: {result_msg}"
        )
    elif result_code == "11":
        raise ValueError(
            f"NO_MANDATORY_REQUEST_PARAMETERS_ERROR: A required parameter is missing. "
            f"API message: {result_msg}"
        )
    elif result_code == "22":
        raise RuntimeError(
            f"RATE_LIMIT_EXCEEDED: Daily request limit of 1,000 reached. "
            f"API message: {result_msg}"
        )
    elif result_code == "30":
        raise PermissionError(
            f"SERVICE_KEY_IS_NOT_REGISTERED_ERROR: Verify VISITKOREA_API_KEY uses the "
            f"Decoding key (일반 인증키 (Decoding)), not the Encoding key. "
            f"API message: {result_msg}"
        )
    elif result_code == "31":
        raise PermissionError(
            f"DEADLINE_HAS_EXPIRED_ERROR: Your service key has expired. "
            f"API message: {result_msg}"
        )
    else:
        raise RuntimeError(
            f"API error (code={result_code}): {result_msg}"
        )

    body = response_body.get("body", {})
    total_count = body.get("totalCount", 0)
    if total_count == 0:
        return []

    items_wrapper = body.get("items", {})
    if not items_wrapper:
        return []

    items = items_wrapper.get("item", [])
    if items is None:
        return []

    if isinstance(items, dict):
        items = [items]

    return items
