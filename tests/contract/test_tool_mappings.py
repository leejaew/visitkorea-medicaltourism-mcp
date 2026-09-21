import unittest
from unittest.mock import patch

from mcp_server.errors.application import InvalidRequest
from mcp_server.tools import medical


class RecordingService:
    def __init__(self):
        self.calls = []

    def __getattr__(self, method_name):
        async def record(params, rows, page):
            self.calls.append((method_name, params, rows, page))
            return []

        return record


class ToolMappingTests(unittest.IsolatedAsyncioTestCase):
    async def test_all_tools_map_normalized_arguments_to_the_service(self):
        cases = [
            (
                medical.get_ldong_code,
                {
                    "lang_div_cd": "eng",
                    "l_dong_regn_cd": "11",
                    "l_dong_list_yn": "y",
                    "num_of_rows": 20,
                    "page_no": 2,
                },
                (
                    "ldong_code",
                    {
                        "langDivCd": "ENG",
                        "lDongRegnCd": "11",
                        "lDongListYn": "Y",
                    },
                    20,
                    2,
                ),
            ),
            (
                medical.get_area_based_list,
                {
                    "lang_div_cd": "jpn",
                    "l_dong_regn_cd": "11",
                    "l_dong_signgu_cd": "110",
                    "arrange": "a",
                    "mdfcn_dt": "20250131",
                },
                (
                    "area_based_list",
                    {
                        "langDivCd": "JPN",
                        "lDongRegnCd": "11",
                        "lDongSignguCd": "110",
                        "arrange": "A",
                        "mdfcnDt": "20250131",
                    },
                    10,
                    1,
                ),
            ),
            (
                medical.get_location_based_list,
                {
                    "lang_div_cd": "kor",
                    "map_x": 127.0,
                    "map_y": 37.5,
                    "radius": 1000,
                    "arrange": "e",
                    "l_dong_regn_cd": "11",
                    "l_dong_signgu_cd": "110",
                    "mdfcn_dt": "20250228",
                },
                (
                    "location_based_list",
                    {
                        "langDivCd": "KOR",
                        "mapX": 127.0,
                        "mapY": 37.5,
                        "radius": 1000,
                        "arrange": "E",
                        "mdfcnDt": "20250228",
                        "lDongRegnCd": "11",
                        "lDongSignguCd": "110",
                    },
                    10,
                    1,
                ),
            ),
            (
                medical.search_medical_by_keyword,
                {
                    "lang_div_cd": "chs",
                    "keyword": "clinic",
                    "arrange": "c",
                    "l_dong_regn_cd": "26",
                    "l_dong_signgu_cd": "260",
                },
                (
                    "search_keyword",
                    {
                        "langDivCd": "CHS",
                        "keyword": "clinic",
                        "arrange": "C",
                        "lDongRegnCd": "26",
                        "lDongSignguCd": "260",
                    },
                    10,
                    1,
                ),
            ),
            (
                medical.get_medical_sync_list,
                {
                    "lang_div_cd": "rus",
                    "arrange": "d",
                    "showflag": "1",
                    "mdfcn_dt": "20250301",
                    "l_dong_regn_cd": "27",
                    "l_dong_signgu_cd": "270",
                    "old_content_id": "123",
                },
                (
                    "sync_list",
                    {
                        "langDivCd": "RUS",
                        "arrange": "D",
                        "showflag": "1",
                        "mdfcnDt": "20250301",
                        "oldContentId": "123",
                        "lDongRegnCd": "27",
                        "lDongSignguCd": "270",
                    },
                    10,
                    1,
                ),
            ),
            (
                medical.get_detail_common,
                {"lang_div_cd": "eng", "content_id": "100"},
                (
                    "detail_common",
                    {"langDivCd": "ENG", "contentId": "100"},
                    1,
                    1,
                ),
            ),
            (
                medical.get_detail_intro,
                {"lang_div_cd": "jpn", "content_id": "101"},
                (
                    "detail_intro",
                    {"langDivCd": "JPN", "contentId": "101"},
                    1,
                    1,
                ),
            ),
            (
                medical.get_detail_medical,
                {"lang_div_cd": "kor", "content_id": "102"},
                (
                    "detail_medical",
                    {"langDivCd": "KOR", "contentId": "102"},
                    1,
                    1,
                ),
            ),
        ]

        for tool, arguments, expected in cases:
            with self.subTest(tool=tool.__name__):
                service = RecordingService()
                with patch("mcp_server.tools.medical._service", return_value=service):
                    await tool(**arguments)
                self.assertEqual(service.calls, [expected])

    async def test_invalid_input_never_reaches_the_service(self):
        service = RecordingService()
        with (
            patch("mcp_server.tools.medical._service", return_value=service),
            self.assertRaises(InvalidRequest),
        ):
            await medical.get_location_based_list("ENG", float("nan"), 37.5, 1000)
        self.assertEqual(service.calls, [])
