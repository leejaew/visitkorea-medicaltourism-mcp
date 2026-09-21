import unittest
from unittest.mock import patch

from mcp_server.errors.application import InvalidRequest
from mcp_server.tools import medical


class RecordingService:
    def __init__(self):
        self.calls = []

    def __getattr__(self, method):
        async def record(params, rows, page):
            self.calls.append((method, params, rows, page))
            return [{"method": method}]

        return record


class MedicalToolAdapterTests(unittest.IsolatedAsyncioTestCase):
    async def test_every_tool_maps_arguments_to_the_expected_service_call(self):
        cases = [
            (
                medical.get_ldong_code,
                {
                    "lang_div_cd": " eng ",
                    "l_dong_regn_cd": " 11 ",
                    "l_dong_list_yn": " y ",
                    "num_of_rows": 120,
                    "page_no": 3,
                },
                "ldong_code",
                {
                    "langDivCd": "ENG",
                    "lDongRegnCd": "11",
                    "lDongListYn": "Y",
                },
                100,
                3,
            ),
            (
                medical.get_area_based_list,
                {
                    "lang_div_cd": " jpn ",
                    "l_dong_regn_cd": " 26 ",
                    "l_dong_signgu_cd": " 110 ",
                    "arrange": " q ",
                    "mdfcn_dt": " 20260228 ",
                    "num_of_rows": 25,
                    "page_no": 4,
                },
                "area_based_list",
                {
                    "langDivCd": "JPN",
                    "lDongRegnCd": "26",
                    "lDongSignguCd": "110",
                    "arrange": "Q",
                    "mdfcnDt": "20260228",
                },
                25,
                4,
            ),
            (
                medical.get_location_based_list,
                {
                    "lang_div_cd": " chs ",
                    "map_x": "127.25",
                    "map_y": "37.50",
                    "radius": "1500",
                    "arrange": " s ",
                    "l_dong_regn_cd": " 41 ",
                    "l_dong_signgu_cd": " 135 ",
                    "mdfcn_dt": " 20260921 ",
                    "num_of_rows": 0,
                    "page_no": 0,
                },
                "location_based_list",
                {
                    "langDivCd": "CHS",
                    "mapX": 127.25,
                    "mapY": 37.5,
                    "radius": 1500,
                    "arrange": "S",
                    "mdfcnDt": "20260921",
                    "lDongRegnCd": "41",
                    "lDongSignguCd": "135",
                },
                1,
                1,
            ),
            (
                medical.search_medical_by_keyword,
                {
                    "lang_div_cd": " rus ",
                    "keyword": " dermatology ",
                    "arrange": " a ",
                    "l_dong_regn_cd": " 27 ",
                    "l_dong_signgu_cd": " 140 ",
                    "num_of_rows": 30,
                    "page_no": 5,
                },
                "search_keyword",
                {
                    "langDivCd": "RUS",
                    "keyword": "dermatology",
                    "arrange": "A",
                    "lDongRegnCd": "27",
                    "lDongSignguCd": "140",
                },
                30,
                5,
            ),
            (
                medical.get_medical_sync_list,
                {
                    "lang_div_cd": " kor ",
                    "arrange": " d ",
                    "showflag": "1",
                    "mdfcn_dt": " 20260101 ",
                    "l_dong_regn_cd": " 28 ",
                    "l_dong_signgu_cd": " 177 ",
                    "old_content_id": " previous-42 ",
                    "num_of_rows": 40,
                    "page_no": 6,
                },
                "sync_list",
                {
                    "langDivCd": "KOR",
                    "arrange": "D",
                    "showflag": "1",
                    "mdfcnDt": "20260101",
                    "oldContentId": "previous-42",
                    "lDongRegnCd": "28",
                    "lDongSignguCd": "177",
                },
                40,
                6,
            ),
            (
                medical.get_detail_common,
                {
                    "lang_div_cd": " eng ",
                    "content_id": " facility-1 ",
                    "num_of_rows": 2,
                    "page_no": 7,
                },
                "detail_common",
                {"langDivCd": "ENG", "contentId": "facility-1"},
                2,
                7,
            ),
            (
                medical.get_detail_intro,
                {
                    "lang_div_cd": " jpn ",
                    "content_id": " facility-2 ",
                    "num_of_rows": 3,
                    "page_no": 8,
                },
                "detail_intro",
                {"langDivCd": "JPN", "contentId": "facility-2"},
                3,
                8,
            ),
            (
                medical.get_detail_medical,
                {
                    "lang_div_cd": " chs ",
                    "content_id": " facility-3 ",
                    "num_of_rows": 4,
                    "page_no": 9,
                },
                "detail_medical",
                {"langDivCd": "CHS", "contentId": "facility-3"},
                4,
                9,
            ),
        ]

        for tool, arguments, method, params, rows, page in cases:
            with self.subTest(tool=tool.__name__):
                service = RecordingService()
                with patch.object(medical, "_service", return_value=service):
                    result = await tool(**arguments)

                self.assertEqual(result, [{"method": method}])
                self.assertEqual(service.calls, [(method, params, rows, page)])

    async def test_validation_failures_stop_before_service_resolution(self):
        cases = [
            (medical.get_ldong_code, {"lang_div_cd": "invalid"}),
            (medical.get_area_based_list, {"lang_div_cd": "ENG", "arrange": "Z"}),
            (
                medical.get_location_based_list,
                {"lang_div_cd": "ENG", "map_x": 0, "map_y": 37.5, "radius": 100},
            ),
            (
                medical.search_medical_by_keyword,
                {"lang_div_cd": "ENG", "keyword": "   "},
            ),
            (medical.get_medical_sync_list, {"lang_div_cd": "ENG", "showflag": "2"}),
            (
                medical.get_detail_common,
                {"lang_div_cd": "ENG", "content_id": "   "},
            ),
            (
                medical.get_detail_intro,
                {"lang_div_cd": "ENG", "content_id": "   "},
            ),
            (
                medical.get_detail_medical,
                {"lang_div_cd": "ENG", "content_id": "   "},
            ),
        ]

        for tool, arguments in cases:
            with (
                self.subTest(tool=tool.__name__),
                patch.object(medical, "_service") as resolve_service,
            ):
                with self.assertRaises(InvalidRequest):
                    await tool(**arguments)
                resolve_service.assert_not_called()
