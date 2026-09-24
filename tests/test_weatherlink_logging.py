import unittest
from unittest.mock import Mock, patch

import requests
from loguru import logger

from app.services.aire import consumir_api_aire, obtener_historico_aire


class WeatherLinkLoggingTests(unittest.TestCase):
    def setUp(self):
        self.messages = []
        self.sink = logger.add(lambda message: self.messages.append(str(message)), level="WARNING")

    def tearDown(self):
        logger.remove(self.sink)

    @patch("app.services.aire.requests.get")
    def test_http_failure_logged_once_without_url_credentials(self, get):
        response = Mock(status_code=503)
        response.raise_for_status.side_effect = requests.HTTPError(
            "https://example.test/?api-key=secret-key", response=response
        )
        get.return_value = response
        result = consumir_api_aire()
        self.assertTrue(result.descrip.startswith("WEATHERLINK_CAIDO"))
        self.assertEqual(len(self.messages), 1)
        self.assertIn("503", self.messages[0])
        self.assertNotIn("secret-key", self.messages[0])
        self.assertNotIn("secret-key", result.descrip)

    @patch("app.services.aire.requests.get")
    def test_invalid_json_has_specific_status_and_one_warning(self, get):
        get.return_value.json.side_effect = requests.exceptions.JSONDecodeError("invalid", "x", 0)
        result = consumir_api_aire()
        self.assertTrue(result.descrip.startswith("WEATHERLINK_JSON_INVALIDO"))
        self.assertEqual(len(self.messages), 1)

    @patch("app.services.aire.requests.get")
    def test_invalid_historical_records_are_summarized(self, get):
        get.return_value.json.return_value = {"sensors": [{
            "lsid": 794536, "data": [{"ts": 1700000000, "pm_1_hi": "invalid"}] * 3
        }]}
        self.assertEqual(obtener_historico_aire(1699990000, 1700010000), [])
        self.assertEqual(len(self.messages), 1)
        self.assertIn("registros inválidos=3", self.messages[0])


if __name__ == "__main__":
    unittest.main()
