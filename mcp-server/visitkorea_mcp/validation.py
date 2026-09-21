"""Strict, bounded validation for public MCP tool inputs."""

from __future__ import annotations

import math
import re
from datetime import datetime
from typing import Any

from .errors import InvalidRequest

VALID_LANG_CODES = {"ENG", "JPN", "CHS", "RUS", "KOR"}
VALID_ARRANGE_CODES = {"A", "C", "D", "O", "Q", "R"}
VALID_ARRANGE_LOCATION = {"A", "C", "D", "E", "O", "Q", "R", "S"}
VALID_SHOWFLAG = {"0", "1"}

_LON_MIN, _LON_MAX = 124.0, 132.0
_LAT_MIN, _LAT_MAX = 33.0, 39.0
_MAX_CODE_LENGTH = 32
_MAX_CONTENT_ID_LENGTH = 128
_MAX_KEYWORD_LENGTH = 200


def validate_lang(lang_div_cd: str) -> str:
    if not isinstance(lang_div_cd, str):
        raise InvalidRequest("lang_div_cd must be a string.")
    code = lang_div_cd.strip().upper()
    if code not in VALID_LANG_CODES:
        raise InvalidRequest(
            f"Invalid lang_div_cd '{lang_div_cd}'. Must be one of: "
            f"{', '.join(sorted(VALID_LANG_CODES))}"
        )
    return code


def validate_pagination(num_of_rows: int, page_no: int) -> tuple[int, int]:
    try:
        rows = int(num_of_rows)
        page = int(page_no)
    except (TypeError, ValueError) as exc:
        raise InvalidRequest("num_of_rows and page_no must be integers.") from exc
    return max(1, min(rows, 100)), max(1, page)


def validate_radius(radius: int) -> int:
    try:
        value = int(radius)
    except (TypeError, ValueError) as exc:
        raise InvalidRequest("radius must be an integer.") from exc
    if not 1 <= value <= 20_000:
        raise InvalidRequest("radius must be between 1 and 20000 metres.")
    return value


def validate_gps(map_x: float, map_y: float) -> tuple[float, float]:
    try:
        longitude, latitude = float(map_x), float(map_y)
    except (TypeError, ValueError) as exc:
        raise InvalidRequest("map_x and map_y must be finite numbers.") from exc
    if not math.isfinite(longitude) or not math.isfinite(latitude):
        raise InvalidRequest("map_x and map_y must be finite numbers.")
    if not _LON_MIN <= longitude <= _LON_MAX:
        raise InvalidRequest("map_x is outside South Korea bounds (124–132).")
    if not _LAT_MIN <= latitude <= _LAT_MAX:
        raise InvalidRequest("map_y is outside South Korea bounds (33–39).")
    return longitude, latitude


def validate_date(date_str: str) -> str:
    if not isinstance(date_str, str):
        raise InvalidRequest("Date must be in YYYYMMDD format.")
    value = date_str.strip()
    if not re.fullmatch(r"\d{8}", value):
        raise InvalidRequest("Date must be in YYYYMMDD format.")
    try:
        datetime.strptime(value, "%Y%m%d")
    except ValueError as exc:
        raise InvalidRequest("Date must be a real calendar date in YYYYMMDD format.") from exc
    return value


def validate_arrange(arrange: str, location: bool = False) -> str:
    if not isinstance(arrange, str):
        raise InvalidRequest("arrange must be a string.")
    code = arrange.strip().upper()
    valid = VALID_ARRANGE_LOCATION if location else VALID_ARRANGE_CODES
    if code not in valid:
        raise InvalidRequest(
            f"Invalid arrange '{arrange}'. Must be one of: {', '.join(sorted(valid))}"
        )
    return code


def validate_showflag(showflag: str) -> str:
    if showflag not in VALID_SHOWFLAG:
        raise InvalidRequest("showflag must be '0' or '1'.")
    return showflag


def validate_optional_code(value: Any, name: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise InvalidRequest(f"{name} must be a string.")
    result = value.strip()
    if len(result) > _MAX_CODE_LENGTH:
        raise InvalidRequest(f"{name} is too long.")
    return result or None


def validate_text(value: Any, name: str, maximum: int) -> str:
    if not isinstance(value, str):
        raise InvalidRequest(f"{name} must be a string.")
    result = value.strip()
    if not result:
        raise InvalidRequest(f"{name} must not be empty.")
    if len(result) > maximum:
        raise InvalidRequest(f"{name} exceeds the maximum length of {maximum}.")
    return result


def validate_content_id(value: Any) -> str:
    return validate_text(value, "content_id", _MAX_CONTENT_ID_LENGTH)