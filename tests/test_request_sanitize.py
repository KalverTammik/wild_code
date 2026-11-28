"""What a request carries is safe on both versions: plain JSON variables, ASCII headers."""
import json
import unittest
from enum import Enum
from unittest.mock import Mock, patch

from qgis.PyQt.QtCore import Qt, QVariant

from Kavitro_dev.python import api_client as client_module
from Kavitro_dev.python.api_client import APIClient, requestBuilder


class _Kind(Enum):
    ROAD = "road"


class SanitizeForJsonTest(unittest.TestCase):
    def _sent(self, value):
        return json.loads(json.dumps(requestBuilder.sanitize_for_json({"v": value})))["v"]

    def test_a_qt_enum_is_sent_as_its_number(self) -> None:
        self.assertEqual(self._sent(Qt.CheckState.Checked), 2)
        self.assertEqual(self._sent([Qt.AlignmentFlag.AlignLeft]), [1])

    def test_a_python_enum_is_sent_as_its_value(self) -> None:
        self.assertEqual(self._sent(_Kind.ROAD), "road")

    def test_an_empty_qgis_value_is_sent_as_null(self) -> None:
        self.assertIsNone(self._sent(QVariant()))


class RequestHeadersTest(unittest.TestCase):
    def test_a_release_name_with_accents_is_sent_as_ascii(self) -> None:
        with patch.object(client_module, "Qgis", Mock(QGIS_VERSION="4.2.3-Belém do Pará")):
            headers = APIClient(session_manager=Mock())._request_headers(False, json_body=True)

        self.assertTrue(headers["User-Agent"].startswith("QGIS/4.2.3-Belem do Para ("), headers["User-Agent"])
        for name, value in headers.items():
            self.assertTrue(value.isascii(), name)


if __name__ == "__main__":
    unittest.main()
