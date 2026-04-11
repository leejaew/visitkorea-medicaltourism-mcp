"""
Input validation for MCP tool parameters.

Validates and sanitises values before they are forwarded to the upstream
data.go.kr API. Invalid inputs are rejected early with a clear error message
rather than letting them produce cryptic upstream API error codes.
"""
from __future__ import annotations

import re

VALID_LANG_CODES = {"ENG", "JPN", "CHS", "RUS", "KOR"}

VALID_ARRANGE_CODES = {"A", "C", "D", "O", "Q", "R"}
VALID_ARRANGE_LOCATION = {"A", "C", "D", "E", "O", "Q", "R", "S"}

VALID_SHOWFLAG = {"0", "1"}

# WGS84 bounding box for South Korea
_LON_MIN, _LON_MAX = 124.0, 132.0
_LAT_MIN, _LAT_MAX = 33.0, 39.0


def validate_lang(lang_div_cd: str) -> str:
    code = lang_div_cd.strip().upper()
    if code not in VALID_LANG_CODES:
        raise ValueError(
            f"Invalid lang_div_cd '{lang_div_cd}'. "
            f"Must be one of: {', '.join(sorted(VALID_LANG_CODES))}"
        )
    return code


def validate_pagination(num_of_rows: int, page_no: int) -> tuple[int, int]:
    """Clamp num_of_rows to [1, 100] and page_no to >= 1."""
    num_of_rows = max(1, min(int(num_of_rows), 100))
    page_no = max(1, int(page_no))
    return num_of_rows, page_no


def validate_radius(radius: int) -> int:
    """Enforce the API's 20 km hard maximum and reject non-positive values."""
    r = int(radius)
    if not (1 <= r <= 20_000):
        raise ValueError(
            f"radius must be between 1 and 20000 metres, got {radius}."
        )
    return r


def validate_gps(map_x: float, map_y: float) -> tuple[float, float]:
    """Validate WGS84 coordinates are within South Korea's bounding box."""
    x, y = float(map_x), float(map_y)
    if not (_LON_MIN <= x <= _LON_MAX):
        raise ValueError(
            f"map_x (longitude) {x} is outside South Korea bounds "
            f"({_LON_MIN}–{_LON_MAX})."
        )
    if not (_LAT_MIN <= y <= _LAT_MAX):
        raise ValueError(
            f"map_y (latitude) {y} is outside South Korea bounds "
            f"({_LAT_MIN}–{_LAT_MAX})."
        )
    return x, y


def validate_date(date_str: str) -> str:
    """Validate YYYYMMDD format. Rejects anything that would confuse the API."""
    if not re.fullmatch(r"\d{8}", date_str.strip()):
        raise ValueError(
            f"Date '{date_str}' must be in YYYYMMDD format (e.g. 20240101)."
        )
    return date_str.strip()


def validate_arrange(arrange: str, location: bool = False) -> str:
    """Validate sort-order code. Pass location=True for GPS-based endpoints."""
    code = arrange.strip().upper()
    valid = VALID_ARRANGE_LOCATION if location else VALID_ARRANGE_CODES
    if code not in valid:
        raise ValueError(
            f"Invalid arrange '{arrange}'. Must be one of: {', '.join(sorted(valid))}"
        )
    return code


def validate_showflag(showflag: str) -> str:
    if showflag not in VALID_SHOWFLAG:
        raise ValueError(
            f"Invalid showflag '{showflag}'. Must be '0' (hidden) or '1' (visible)."
        )
    return showflag
