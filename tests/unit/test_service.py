import unittest

from mcp_server.services.medical_tourism import MedicalTourismService


class FakeClient:
    def __init__(self):
        self.calls = []

    async def call_api(self, endpoint, params, num_of_rows, page_no):
        self.calls.append((endpoint, params, num_of_rows, page_no))
        if endpoint == "detailCommon":
            return [{"mapx": "126.9", "mapy": "37.5"}]
        return [{"endpoint": endpoint, **params}]


class ServiceTests(unittest.IsolatedAsyncioTestCase):
    async def test_each_domain_method_uses_the_fixed_upstream_endpoint(self):
        cases = {
            "ldong_code": "ldongCode",
            "area_based_list": "areaBasedList",
            "location_based_list": "locationBasedList",
            "search_keyword": "searchKeyword",
            "sync_list": "mdclTursmSyncList",
            "detail_common": "detailCommon",
            "detail_intro": "detailIntro",
            "detail_medical": "detailMdclTursm",
        }
        for method_name, expected_endpoint in cases.items():
            with self.subTest(method=method_name):
                client = FakeClient()
                service = MedicalTourismService(client)
                await getattr(service, method_name)({"langDivCd": "ENG"}, 7, 3)
                self.assertEqual(
                    client.calls,
                    [(expected_endpoint, {"langDivCd": "ENG"}, 7, 3)],
                )

    async def test_service_uses_plain_client_protocol(self):
        client = FakeClient()
        result = await MedicalTourismService(client).area_based_list(
            {"langDivCd": "ENG"}, 10, 1
        )
        self.assertEqual(result[0]["endpoint"], "areaBasedList")
        self.assertEqual(client.calls[0][0], "areaBasedList")

    async def test_detail_common_normalizes_coordinates(self):
        result = await MedicalTourismService(FakeClient()).detail_common(
            {"langDivCd": "ENG", "contentId": "1"}, 1, 1
        )
        self.assertEqual(result, [{"mapX": "126.9", "mapY": "37.5"}])
