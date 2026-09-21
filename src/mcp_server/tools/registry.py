"""Single source of truth for public tool registration."""

from .medical import (
    get_area_based_list,
    get_detail_common,
    get_detail_intro,
    get_detail_medical,
    get_ldong_code,
    get_location_based_list,
    get_medical_sync_list,
    search_medical_by_keyword,
)

TOOL_FUNCTIONS = (
    get_ldong_code,
    get_area_based_list,
    get_location_based_list,
    search_medical_by_keyword,
    get_medical_sync_list,
    get_detail_common,
    get_detail_intro,
    get_detail_medical,
)


def register_tools(server) -> None:
    for tool in TOOL_FUNCTIONS:
        server.tool()(tool)
