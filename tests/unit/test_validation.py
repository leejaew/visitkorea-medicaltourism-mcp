import unittest

from mcp_server.errors.application import InvalidRequest
from mcp_server.services.validation import validate_date, validate_gps, validate_lang


class ValidationTests(unittest.TestCase):
    def test_language_is_normalized(self):
        self.assertEqual(validate_lang(" eng "), "ENG")

    def test_invalid_date_is_rejected(self):
        with self.assertRaises(InvalidRequest):
            validate_date("20241399")

    def test_gps_rejects_non_finite_values(self):
        with self.assertRaises(InvalidRequest):
            validate_gps(float("nan"), 37.5)
