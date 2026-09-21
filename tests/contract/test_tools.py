import unittest

from mcp_server.config import Settings
from mcp_server.server import create_server
from mcp_server.tools.registry import TOOL_FUNCTIONS

MISSING = object()


def property_schema(name, value_type, default=MISSING):
    title = name.replace("_", " ").title()
    if default is None:
        return {
            "anyOf": [{"type": value_type}, {"type": "null"}],
            "default": None,
            "title": title,
        }
    schema = {"title": title, "type": value_type}
    if default is not MISSING:
        schema["default"] = default
    return schema


EXPECTED_TOOLS = {
    "get_ldong_code": (
        "Retrieve legal administrative district codes.",
        ["lang_div_cd"],
        [
            ("lang_div_cd", "string", MISSING),
            ("l_dong_regn_cd", "string", None),
            ("l_dong_list_yn", "string", None),
            ("num_of_rows", "integer", 10),
            ("page_no", "integer", 1),
        ],
    ),
    "get_area_based_list": (
        "List medical tourism facilities filtered by administrative region.",
        ["lang_div_cd"],
        [
            ("lang_div_cd", "string", MISSING),
            ("l_dong_regn_cd", "string", None),
            ("l_dong_signgu_cd", "string", None),
            ("arrange", "string", None),
            ("mdfcn_dt", "string", None),
            ("num_of_rows", "integer", 10),
            ("page_no", "integer", 1),
        ],
    ),
    "get_location_based_list": (
        "List medical tourism facilities within a GPS radius.",
        ["lang_div_cd", "map_x", "map_y", "radius"],
        [
            ("lang_div_cd", "string", MISSING),
            ("map_x", "number", MISSING),
            ("map_y", "number", MISSING),
            ("radius", "integer", MISSING),
            ("arrange", "string", None),
            ("l_dong_regn_cd", "string", None),
            ("l_dong_signgu_cd", "string", None),
            ("mdfcn_dt", "string", None),
            ("num_of_rows", "integer", 10),
            ("page_no", "integer", 1),
        ],
    ),
    "search_medical_by_keyword": (
        "Search medical tourism facilities by keyword.",
        ["lang_div_cd", "keyword"],
        [
            ("lang_div_cd", "string", MISSING),
            ("keyword", "string", MISSING),
            ("arrange", "string", None),
            ("l_dong_regn_cd", "string", None),
            ("l_dong_signgu_cd", "string", None),
            ("num_of_rows", "integer", 10),
            ("page_no", "integer", 1),
        ],
    ),
    "get_medical_sync_list": (
        "Retrieve the medical tourism synchronization list.",
        ["lang_div_cd"],
        [
            ("lang_div_cd", "string", MISSING),
            ("arrange", "string", None),
            ("showflag", "string", None),
            ("mdfcn_dt", "string", None),
            ("l_dong_regn_cd", "string", None),
            ("l_dong_signgu_cd", "string", None),
            ("old_content_id", "string", None),
            ("num_of_rows", "integer", 10),
            ("page_no", "integer", 1),
        ],
    ),
    "get_detail_common": (
        "Retrieve common detail information for a facility.",
        ["lang_div_cd", "content_id"],
        [
            ("lang_div_cd", "string", MISSING),
            ("content_id", "string", MISSING),
            ("num_of_rows", "integer", 1),
            ("page_no", "integer", 1),
        ],
    ),
    "get_detail_intro": (
        "Retrieve introductory detail information for a facility.",
        ["lang_div_cd", "content_id"],
        [
            ("lang_div_cd", "string", MISSING),
            ("content_id", "string", MISSING),
            ("num_of_rows", "integer", 1),
            ("page_no", "integer", 1),
        ],
    ),
    "get_detail_medical": (
        "Retrieve medical-specific detail information for a facility.",
        ["lang_div_cd", "content_id"],
        [
            ("lang_div_cd", "string", MISSING),
            ("content_id", "string", MISSING),
            ("num_of_rows", "integer", 1),
            ("page_no", "integer", 1),
        ],
    ),
}


class ToolContractTests(unittest.TestCase):
    def test_public_tool_set_is_exact(self):
        self.assertEqual(
            [tool.__name__ for tool in TOOL_FUNCTIONS],
            [
                "get_ldong_code",
                "get_area_based_list",
                "get_location_based_list",
                "search_medical_by_keyword",
                "get_medical_sync_list",
                "get_detail_common",
                "get_detail_intro",
                "get_detail_medical",
            ],
        )

    def test_context_is_keyword_only(self):
        self.assertIn("ctx", TOOL_FUNCTIONS[-1].__kwdefaults__)

    def test_generated_schemas_are_exact(self):
        server = create_server(Settings(api_key="test"))
        self.assertEqual(
            [route.path for route in server._custom_starlette_routes], ["/healthz"]
        )
        self.assertEqual(list(server._tool_manager._tools), list(EXPECTED_TOOLS))
        for name, (description, required, parameters) in EXPECTED_TOOLS.items():
            tool = server._tool_manager._tools[name]
            expected_schema = {
                "properties": {
                    parameter: property_schema(parameter, value_type, default)
                    for parameter, value_type, default in parameters
                },
                "required": required,
                "title": f"{name}Arguments",
                "type": "object",
            }
            self.assertEqual(tool.description, description)
            self.assertEqual(tool.parameters, expected_schema)
            self.assertNotIn("ctx", tool.parameters["properties"])
