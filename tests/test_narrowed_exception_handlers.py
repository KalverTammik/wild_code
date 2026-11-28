"""Handlers narrowed from `except Exception` still catch the failures they exist for.

A narrowed handler that misses its own failure lets the error escape, and inside a Qt slot that
ends QGIS, so each case here is the input the handler was written for.
"""
import os
import sys
import unittest
from unittest.mock import patch

PLUGIN_PARENT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if PLUGIN_PARENT not in sys.path:
    sys.path.insert(0, PLUGIN_PARENT)

from qgis.core import QgsApplication, QgsFeature, QgsField, QgsFields
from qgis.PyQt import sip
from qgis.PyQt.QtCore import QMetaType, QObject, pyqtSignal

from Kavitro_dev.utils.auth.user_utils import UserUtils
from Kavitro_dev.utils.date_helpers import DateHelpers
from Kavitro_dev.utils.property.property_row_builder import PropertyRowBuilder


class _Emitter(QObject):
    changed = pyqtSignal()


class NarrowedHandlersTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QgsApplication.instance() or QgsApplication([], False)

    def setUp(self) -> None:
        log = patch("Kavitro_dev.Logs.python_fail_logger.PythonFailLogger.log")
        self.log = log.start()
        self.addCleanup(log.stop)

    def test_dates_that_are_no_iso_text_read_as_none(self) -> None:
        for value in ("not a date", "2026-13-40", 20261123, ["2026-11-23"]):
            with self.subTest(value=value):
                self.assertIsNone(DateHelpers.parse_iso(value))
        self.assertEqual(DateHelpers.parse_iso("2026-11-23T10:00:00Z").year, 2026)
        self.assertEqual(DateHelpers().date_to_iso_string("2026-11-23T10:00:00Z"), "2026-11-23")

    def test_abilities_that_are_no_json_list_read_as_empty(self) -> None:
        for value in ("{broken", "", "null", '{"a": 1}', None, 5):
            with self.subTest(value=value):
                self.assertEqual(UserUtils.parse_abilities(value), [])
        self.assertEqual(UserUtils.parse_abilities('[{"subject": "Task"}]'), [{"subject": "Task"}])

    def test_a_missing_field_reads_as_empty_text(self) -> None:
        fields = QgsFields()
        fields.append(QgsField("tunnus", QMetaType.Type.QString))
        feature = QgsFeature(fields)
        feature["tunnus"] = "1:1"
        self.assertEqual(PropertyRowBuilder.read_field_text(feature, "tunnus"), "1:1")
        for obj, key in ((feature, "missing_name"), (feature, 7), ({"a": 1}, "b"), (["x"], 3), (None, "a")):
            with self.subTest(obj=type(obj).__name__, key=key):
                self.assertEqual(PropertyRowBuilder.read_field_text(obj, key, log_prefix=f"t{key}"), "")

    def test_qt_reports_a_failed_disconnect_and_a_deleted_object_with_the_caught_types(self) -> None:
        # The disconnect and deleteLater handlers catch (TypeError, RuntimeError) / RuntimeError.
        emitter = _Emitter()
        with self.assertRaises(TypeError):
            emitter.changed.disconnect(self.setUp)
        sip.delete(emitter)
        with self.assertRaises(RuntimeError):
            emitter.deleteLater()
        with self.assertRaises(RuntimeError):
            emitter.changed.disconnect()


if __name__ == "__main__":
    unittest.main()
