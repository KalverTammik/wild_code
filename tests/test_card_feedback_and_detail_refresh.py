"""Card buttons say what went wrong, the card detail reloads after a change, and an as-built keeps one feature.

From the button audits, fixed 2026-11-23:
- "Show on map" was silent when linked properties were missing from the property layer;
- "Open in browser" and the Maa-amet page were silent when the page could not open;
- the card detail was loaded once and did not change after linking properties or a new folder (user decision:
  reload after the change, plus a Refresh button);
- drawing an as-built again added a second feature with the same id (user decision: as for projects).
"""
from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
if os.environ.get("QGIS_PREFIX_PATH"):
    sys.path.append(str(Path(os.environ["QGIS_PREFIX_PATH"]) / "python" / "plugins"))

from qgis.core import QgsApplication, QgsFeature, QgsGeometry, QgsVectorLayer
from qgis.PyQt.QtWidgets import QApplication, QLabel

from Kavitro_dev.constants.cadastral_fields import Katastriyksus
from Kavitro_dev.languages.language_manager import LanguageManager
from Kavitro_dev.languages.translation_keys import TranslationKeys
from Kavitro_dev.Logs.python_fail_logger import PythonFailLogger
from Kavitro_dev.modules.asbuilt import asbuilt_feature_map_controller as asbuilt_module
from Kavitro_dev.modules.asbuilt.asbuilt_layer_service import AsBuiltLayerService
from Kavitro_dev.modules.Settings.cards.SettingsPropertyManagement import PropertyManagementUI
from Kavitro_dev.ui.messages_helper import ModernMessageDialog
from Kavitro_dev.widgets.DataDisplayWidgets import ExtraInfoWidget as extra_info_module
from Kavitro_dev.widgets.DataDisplayWidgets import ModuleConnectionActions as connection_module
from Kavitro_dev.widgets.DataDisplayWidgets import module_action_buttons as buttons_module

_APP = QgsApplication.instance() or QgsApplication([], False)
LANG = LanguageManager()


class DialogStubCase(unittest.TestCase):
    def setUp(self) -> None:
        for name in ("show_warning", "show_info", "ask_choice_modern"):
            patcher = patch.object(ModernMessageDialog, name)
            setattr(self, name, patcher.start())
            self.addCleanup(patcher.stop)
        for name in ("log", "log_exception"):
            patcher = patch.object(PythonFailLogger, name)
            patcher.start()
            self.addCleanup(patcher.stop)


class ShowOnMapSummaryTest(DialogStubCase):
    def show(self, numbers, on_layer):
        layer = Mock()
        layer.selectedFeatures.return_value = [{Katastriyksus.tunnus: n} for n in on_layer]
        with patch.object(buttons_module.APIModuleActions, "get_module_item_connected_properties",
                          return_value=numbers), \
                patch.object(buttons_module.PropertiesSelectors, "show_connected_properties_on_map",
                             return_value=layer if on_layer else None), \
                patch.object(buttons_module.ModuleItemFocusService, "focus_item_on_map", return_value=False):
            buttons_module.show_items_on_map("project", "5", LANG)

    def test_all_found_says_nothing(self) -> None:
        self.show(["1:1", "2:2"], ["1:1", "2:2"])
        self.show_warning.assert_not_called()

    def test_some_missing_are_named(self) -> None:
        self.show(["1:1", "2:2", "3:3"], ["1:1"])
        text = self.show_warning.call_args.args[1]
        self.assertIn("2:2", text)
        self.assertIn("3:3", text)
        self.assertNotIn("1:1,", text)

    def test_none_found_says_so(self) -> None:
        self.show(["1:1"], [])
        expected = LANG.translate(TranslationKeys.MAP_SHOW_NONE_FOUND).format(total=1, missing="1:1")
        self.assertEqual(self.show_warning.call_args.args[1], expected)

    def test_a_failed_read_is_not_shown_as_success(self) -> None:
        self.show([], [])
        self.assertEqual(self.show_warning.call_args.args[1], LANG.translate(TranslationKeys.MAP_SHOW_LOAD_FAILED))


class OpenPageTest(DialogStubCase):
    def test_a_page_that_does_not_open_is_reported(self) -> None:
        with patch.object(buttons_module.OpenLink, "weblink_by_module", return_value="https://kavitro.com/project"), \
                patch.object(buttons_module.loadWebpage, "open_webpage", return_value=False):
            self.assertFalse(buttons_module.open_item_in_browser("project", "5", LANG))
        self.assertIn("https://kavitro.com/projects/5", self.show_warning.call_args.args[1])

    def test_a_missing_address_is_reported(self) -> None:
        with patch.object(buttons_module.OpenLink, "weblink_by_module", return_value=""):
            self.assertFalse(buttons_module.open_item_in_browser("project", "5", LANG))
        self.assertEqual(self.show_warning.call_args.args[1], LANG.translate(TranslationKeys.WEB_LINK_MISSING))

    def test_an_opened_page_says_nothing(self) -> None:
        with patch.object(buttons_module.OpenLink, "weblink_by_module", return_value="https://kavitro.com/project"), \
                patch.object(buttons_module.loadWebpage, "open_webpage", return_value=True):
            self.assertTrue(buttons_module.open_item_in_browser("project", "5", LANG))
        self.show_warning.assert_not_called()

    def test_the_maa_amet_page_that_does_not_open_is_reported(self) -> None:
        from Kavitro_dev.utils import url_manager
        with patch.object(url_manager.loadWebpage, "open_webpage", return_value=False):
            PropertyManagementUI._handle_maa_amet_page()
        self.show_warning.assert_called_once()


class DetailRefreshTest(DialogStubCase):
    def frame(self):
        self.loads = []

        def loader():
            label = QLabel(f"detail {len(self.loads)}")
            self.loads.append(label)
            return label

        config = Mock(show_detail_handle=True, detail_loader=loader, detail_open_callback=None)
        with patch.object(extra_info_module.ModuleConfigFactory, "create_config", return_value=config):
            frame = extra_info_module.ExtraInfoFrame({"id": "1"}, "contract", lang_manager=LANG)
        self.addCleanup(frame.deleteLater)
        return frame

    def test_a_change_reloads_an_open_detail(self) -> None:
        frame = self.frame()
        frame._toggle_project_detail()
        self.assertEqual(len(self.loads), 1)

        frame.invalidate_detail()

        self.assertEqual(len(self.loads), 2)
        self.assertIs(frame._detail_widget, self.loads[1])

    def test_a_closed_detail_reloads_on_its_next_opening(self) -> None:
        frame = self.frame()
        frame._toggle_project_detail()
        frame._toggle_project_detail()  # closed again
        frame.invalidate_detail()
        self.assertEqual(len(self.loads), 1)
        frame._toggle_project_detail()
        self.assertEqual(len(self.loads), 2)

    def test_the_refresh_button_reloads(self) -> None:
        frame = self.frame()
        frame._toggle_project_detail()
        frame._refresh_button.click()
        QApplication.processEvents()
        self.assertEqual(len(self.loads), 2)
        self.assertEqual(frame._refresh_button.text(), LANG.translate(TranslationKeys.CARD_DETAIL_REFRESH))

    def test_linking_or_a_new_folder_tells_the_card(self) -> None:
        actions = connection_module.ModuleConnectionActions.__new__(connection_module.ModuleConnectionActions)
        connection_module.QWidget.__init__(actions)
        self.addCleanup(actions.deleteLater)
        actions._map_button, actions._folder_button, actions._action_payload = Mock(), Mock(), {}
        changes = []
        actions.item_changed.connect(lambda: changes.append(1))

        actions.set_connected_properties(["1:1"])
        actions.set_files_path("X:\\kaust")

        self.assertEqual(changes, [1, 1])


class AsBuiltOneFeatureTest(DialogStubCase):
    def layer(self, kind: str = "MultiLineString") -> QgsVectorLayer:
        layer = QgsVectorLayer(f"{kind}?crs=EPSG:3301&field=ext_job_id:string", "Teostus", "memory")
        old = QgsFeature(layer.fields())
        old.setAttributes(["77"])
        old.setGeometry(QgsGeometry.fromWkt("LINESTRING(0 0, 10 0)"))
        layer.dataProvider().addFeatures([old])
        return layer

    def mode(self, layer, index: int):
        controller = asbuilt_module.AsBuiltFeatureMapController.__new__(asbuilt_module.AsBuiltFeatureMapController)
        controller._lang = LANG
        controller._workflow = Mock()
        self.ask_choice_modern.side_effect = lambda *_a, **kw: kw["buttons"][index]
        with patch.object(AsBuiltLayerService, "prepare_layer_for_draw", return_value=(layer, "")):
            controller.start_draw(item_data={"id": "77"})
        return controller._workflow.start_draw

    def test_drawing_again_asks_and_passes_the_choice(self) -> None:
        start = self.mode(self.layer(), 1)
        self.assertEqual(start.call_args.kwargs["item_data"]["_existing_feature_mode"], AsBuiltLayerService.AREA_ADD_PART)
        self.assertIn("77", self.ask_choice_modern.call_args.args[1])

    def test_cancel_does_not_start_drawing(self) -> None:
        self.mode(self.layer(), 2).assert_not_called()

    def test_replace_leaves_one_feature(self) -> None:
        layer = self.layer()
        layer.startEditing()
        drawn = QgsFeature(layer.fields())
        drawn.setAttributes(["77"])
        drawn.setGeometry(QgsGeometry.fromWkt("LINESTRING(20 0, 30 0)"))
        layer.addFeature(drawn)

        ok, _error = AsBuiltLayerService.fold_existing_areas(
            layer, keep_feature_id=drawn.id(), item_id="77", mode=AsBuiltLayerService.AREA_REPLACE)

        self.assertTrue(ok)
        self.assertTrue(layer.commitChanges())
        self.assertEqual(layer.featureCount(), 1)
        self.assertAlmostEqual(next(layer.getFeatures()).geometry().length(), 10.0)

    def test_add_part_keeps_both_lines_in_one_feature(self) -> None:
        layer = self.layer()
        layer.startEditing()
        drawn = QgsFeature(layer.fields())
        drawn.setAttributes(["77"])
        drawn.setGeometry(QgsGeometry.fromWkt("LINESTRING(20 0, 30 0)"))
        layer.addFeature(drawn)

        ok, _error = AsBuiltLayerService.fold_existing_areas(
            layer, keep_feature_id=drawn.id(), item_id="77", mode=AsBuiltLayerService.AREA_ADD_PART)

        self.assertTrue(ok)
        self.assertTrue(layer.commitChanges())
        self.assertEqual(layer.featureCount(), 1)
        self.assertAlmostEqual(next(layer.getFeatures()).geometry().length(), 20.0)


if __name__ == "__main__":
    unittest.main()
