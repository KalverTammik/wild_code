"""A main-layer read that fails is its own attention cause, never "missing in main layer"."""
from __future__ import annotations

import importlib
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
if os.environ.get("QGIS_PREFIX_PATH"):
    sys.path.append(str(Path(os.environ["QGIS_PREFIX_PATH"]) / "python" / "plugins"))

from qgis.core import QgsApplication, QgsFeature, QgsVectorLayer

from Kavitro_dev.Logs.python_fail_logger import PythonFailLogger
from Kavitro_dev.languages import en, et
from Kavitro_dev.languages.translation_keys import TranslationKeys as K
from Kavitro_dev.modules.Property.FlowControllers.AttentionDisplayRules import AttentionDisplayRules
from Kavitro_dev.modules.Property.FlowControllers.MainLayerCheckController import MainLayerCheckController
from Kavitro_dev.utils.MapTools.MapHelpers import LayerLookupError, MapHelpers
from Kavitro_dev.ui.messages_helper import ModernMessageDialog

# The package re-exports the class under the module's name, so the module is loaded by path.
check_module = importlib.import_module("Kavitro_dev.modules.Property.FlowControllers.MainLayerCheckController")

MESSAGE_DIALOG_METHODS = ("Info_messages_modern", "Warning_messages_modern", "Error_messages_modern",
                          "show_info", "show_warning", "show_error", "ask_choice_modern", "get_text_modern")
LOOKUP_FAILED = K.ATTENTION_CAUSE_MAIN_LAYER_LOOKUP_FAILED
MISSING = "missing in main layer"


def memory_layer(fields: str, *tunnused: str) -> QgsVectorLayer:
    layer = QgsVectorLayer(f"Polygon?crs=EPSG:3301{fields}", "main", "memory")
    features = []
    for tunnus in tunnused:
        feature = QgsFeature(layer.fields())
        feature.setAttribute("tunnus", tunnus)
        features.append(feature)
    layer.dataProvider().addFeatures(features)
    return layer


def broken_iteration_layer() -> Mock:
    layer = Mock()
    layer.isValid.return_value = True
    layer.fields.return_value.indexOf.return_value = 0
    layer.getFeatures.side_effect = RuntimeError("provider gone")
    return layer


class _QuietTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QgsApplication.instance() or QgsApplication([], False)

    def setUp(self) -> None:
        for name in MESSAGE_DIALOG_METHODS:
            if hasattr(ModernMessageDialog, name):
                patcher = patch.object(ModernMessageDialog, name)
                patcher.start()
                self.addCleanup(patcher.stop)
        log = patch.object(PythonFailLogger, "log")
        self.log = log.start()
        self.addCleanup(log.stop)

    def logged_events(self) -> list:
        return [call.args[0] if call.args else call.kwargs.get("event") for call in self.log.call_args_list]


class StrictLookupTest(_QuietTestCase):
    """Strict mode tells a failed read from a miss; the default keeps returning []."""

    def test_strict_found_and_missed_rows_read_normally(self) -> None:
        layer = memory_layer("&field=tunnus:string", "A", "B")
        found = MapHelpers.find_features_by_fields_and_values(layer, "tunnus", ["A"], strict=True)
        self.assertEqual([f["tunnus"] for f in found], ["A"])
        self.assertEqual(MapHelpers.find_features_by_fields_and_values(layer, "tunnus", ["Z"], strict=True), [])

    def test_strict_raises_when_the_layer_cannot_be_read(self) -> None:
        cases = {
            "invalid layer": QgsVectorLayer("not-a-real-uri", "broken", "ogr"),
            "no layer": None,
            "field missing": memory_layer("&field=other:string"),
            "iteration fails": broken_iteration_layer(),
        }
        for name, layer in cases.items():
            with self.subTest(name):
                with self.assertRaises(LayerLookupError):
                    MapHelpers.find_features_by_fields_and_values(layer, "tunnus", ["A"], strict=True)

    def test_default_mode_still_returns_empty_on_the_same_failures(self) -> None:
        # Easement/project previews, the item selector, focus service and action
        # buttons rely on this: a failed read is logged and gives no matches.
        for layer in (QgsVectorLayer("not-a-real-uri", "broken", "ogr"), None,
                      memory_layer("&field=other:string"), broken_iteration_layer()):
            self.assertEqual(MapHelpers.find_features_by_fields_and_values(layer, "tunnus", ["A"]), [])
        self.assertIn("property_layer_field_missing", self.logged_events())
        self.assertIn("property_layer_feature_iter_error", self.logged_events())

    def test_no_values_is_an_empty_answer_even_when_strict(self) -> None:
        self.assertEqual(MapHelpers.find_features_by_fields_and_values(None, "tunnus", [], strict=True), [])


class ControllerLookupFailureTest(_QuietTestCase):
    def controller(self, layer) -> MainLayerCheckController:
        controller = MainLayerCheckController()
        self.addCleanup(controller.deleteLater)
        self.addCleanup(controller.stop)
        controller.configure(
            rows_for_verify_by_row={0: ("A", "")},
            main_layer=layer,
            main_layer_lookup={},
            lookup_is_complete=False,
        )
        return controller

    def emitted_causes(self, controller) -> list:
        results = []
        controller.rowResult.connect(lambda _row, causes: results.append(causes))
        controller.ensure_row(0)
        return results[0]

    def test_unreadable_layer_reports_a_lookup_failure_not_a_missing_property(self) -> None:
        for name, layer in (("field missing", memory_layer("&field=other:string")),
                            ("iteration fails", broken_iteration_layer())):
            with self.subTest(name):
                self.log.reset_mock()
                causes = self.emitted_causes(self.controller(layer))
                self.assertEqual(causes, [LOOKUP_FAILED])
                self.assertNotIn(MISSING, causes)
                self.assertIn("main_layer_lookup_failed", self.logged_events())

    def test_a_real_miss_is_still_missing(self) -> None:
        causes = self.emitted_causes(self.controller(memory_layer("&field=tunnus:string", "B")))
        self.assertEqual(causes, [MISSING])

    def test_a_found_row_has_no_cause(self) -> None:
        layer = memory_layer("&field=tunnus:string&field=muudet:string", "A")
        self.assertEqual(self.emitted_causes(self.controller(layer)), [])

    def test_controller_asks_for_the_strict_lookup(self) -> None:
        with patch.object(check_module.MapHelpers, "find_features_by_fields_and_values",
                          return_value=[]) as lookup:
            self.emitted_causes(self.controller(object()))
        self.assertIs(lookup.call_args.kwargs.get("strict"), True)


class LookupFailedCauseTextTest(unittest.TestCase):
    def test_both_languages_name_the_cause(self) -> None:
        self.assertEqual(et.TRANSLATIONS[LOOKUP_FAILED], "põhikihi lugemine ebaõnnestus")
        self.assertEqual(en.TRANSLATIONS[LOOKUP_FAILED], "main layer lookup failed")

    def test_tooltip_shows_the_translated_cause(self) -> None:
        text = AttentionDisplayRules.causes_text([LOOKUP_FAILED], translate=et.TRANSLATIONS.__getitem__)
        self.assertEqual(text, "põhikihi lugemine ebaõnnestus")


if __name__ == "__main__":
    unittest.main()
