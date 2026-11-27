"""Property buttons fixed in the medium audit round (04_01 audit doc).

1. In Geospatial mode **Lisa kinnistuid** follows the import layer, and the add dialog
   stops in its missing-layer view without building the rest.
2. A new SHP import replaces the earlier tagged import layers, so one import layer stays.
3. **Kustuta ID järgi** loads the record and asks before deleting; no preview, no delete.
4. A related-records answer for an earlier map pick is ignored once a newer pick started.
5. The related-records group arrow has a tooltip and an accessible name.
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

from qgis.PyQt.QtWidgets import QWidget
from qgis.core import QgsApplication, QgsFeature, QgsProject, QgsVectorLayer

from Kavitro_dev.constants.layer_constants import IMPORT_PROPERTY_TAG
from Kavitro_dev.engines.LayerCreationEngine import MailablGroupFolders
from Kavitro_dev.languages.language_manager import LanguageManager
from Kavitro_dev.languages.translation_keys import TranslationKeys
from Kavitro_dev.modules.Property.dialogs import delete_property_dialog as delete_dialog_module
from Kavitro_dev.modules.Property.dialogs.delete_property_dialog import DeletePropertyUI
from Kavitro_dev.modules.Property.FlowControllers import property_delete as delete_module
from Kavitro_dev.modules.Property.FlowControllers import property_shp_import_flow as flow_module
from Kavitro_dev.modules.Property.FlowControllers.property_delete import deleteProperty
from Kavitro_dev.modules.Property.FlowControllers.property_shp_import_flow import SHPLayerLoader, SHPLoadStatus
from Kavitro_dev.modules.Property.widgets import property_ui_tools as tools_module
from Kavitro_dev.modules.Property.widgets.property_tree_widget import ModuleConnectionSection
from Kavitro_dev.modules.Property.widgets.property_ui_tools import PropertyUITools
from Kavitro_dev.modules.Settings.cards import SettingsPropertyManagement as card_module
from Kavitro_dev.modules.Settings.cards.SettingsPropertyManagement import PropertyManagementUI
from Kavitro_dev.utils.MapTools.MapHelpers import MapHelpers

_APP = QgsApplication.instance() or QgsApplication([], False)
if QgsApplication.instance() is _APP:
    QgsApplication.initQgis()


def _memory_layer(name: str, *, features: int = 0, tagged: bool = False) -> QgsVectorLayer:
    layer = QgsVectorLayer("Polygon?crs=EPSG:3301&field=tunnus:string", name, "memory")
    layer.dataProvider().addFeatures([QgsFeature(layer.fields()) for _ in range(features)])
    if tagged:
        layer.setCustomProperty(IMPORT_PROPERTY_TAG, "true")
    return layer


class _Settings:
    def __init__(self, mode: str) -> None:
        self._mode = mode

    def geospatial_setup_mode(self):
        return self._mode


# ---------------------------------------------------------------- 1: add button / dialog


class GeospatialAddButtonTest(unittest.TestCase):
    def _card(self, mode: str, *, import_layer=None, main_layer=None) -> PropertyManagementUI:
        patches = [
            patch.object(card_module, "SettingsService", return_value=_Settings(mode)),
            patch.object(card_module.MapHelpers, "get_layer_by_tag", return_value=import_layer),
            patch.object(card_module.ActiveLayersHelper, "resolve_main_property_layer", return_value=main_layer),
            patch.object(card_module.PropertySearchFieldService, "has_search_field", return_value=True),
        ]
        for p in patches:
            p.start()
            self.addCleanup(p.stop)
        card = PropertyManagementUI(LanguageManager())
        self.addCleanup(card.deleteLater)
        return card

    def test_geospatial_mode_without_import_layer_keeps_add_disabled(self) -> None:
        card = self._card("geospatial")

        self.assertFalse(card.btn_add_property.isEnabled())
        self.assertEqual(card.btn_add_property.toolTip(),
                         LanguageManager().translate(TranslationKeys.PROPERTY_ADD_NO_IMPORT_LAYER_TOOLTIP))
        self.assertFalse(card.btn_add_shp.isEnabled())
        self.assertFalse(card.btn_remove_property.isEnabled())

    def test_geospatial_mode_with_an_import_layer_enables_add_but_not_shp(self) -> None:
        card = self._card("geospatial", import_layer=_memory_layer("import", features=2), main_layer=Mock())

        self.assertTrue(card.btn_add_property.isEnabled())
        self.assertEqual(card.btn_add_property.toolTip(), "")
        self.assertFalse(card.btn_add_shp.isEnabled())
        self.assertFalse(card.btn_open_maa_amet.isEnabled())
        self.assertTrue(card.btn_remove_property.isEnabled())

    def test_an_empty_import_layer_does_not_enable_add_in_geospatial_mode(self) -> None:
        card = self._card("geospatial", import_layer=_memory_layer("import", features=0))

        self.assertFalse(card.btn_add_property.isEnabled())

    def test_manual_mode_keeps_shp_import_available(self) -> None:
        card = self._card("manual")

        self.assertTrue(card.btn_add_shp.isEnabled())
        self.assertTrue(card.btn_open_maa_amet.isEnabled())
        self.assertFalse(card.btn_add_property.isEnabled())

    def test_switching_to_geospatial_recomputes_the_add_button(self) -> None:
        card = self._card("manual")
        card.set_geospatial_mode_active(True)

        self.assertFalse(card.btn_add_property.isEnabled())
        self.assertFalse(card.btn_add_shp.isEnabled())


class MissingImportLayerDialogTest(unittest.TestCase):
    def test_map_mode_stops_in_the_error_view(self) -> None:
        from Kavitro_dev.modules.Property.dialogs import AddUpdatePropertyDialog as dialog_module
        from Kavitro_dev.modules.Property.dialogs.AddUpdatePropertyDialog import AddPropertyDialog
        from Kavitro_dev.modules.Property.FlowControllers.property_dialog_phase import PropertyDialogMode

        loader = Mock(property_layer=None)
        with patch.object(dialog_module, "PropertyDataLoader", return_value=loader), \
                patch.object(AddPropertyDialog, "_create_ui") as create_ui, \
                patch.object(AddPropertyDialog, "_setup_connections") as setup, \
                patch.object(dialog_module.QTimer, "singleShot") as single_shot:
            dialog = AddPropertyDialog(None, mode=PropertyDialogMode.FROM_MAP)
        self.addCleanup(dialog.deleteLater)

        create_ui.assert_not_called()
        setup.assert_not_called()
        single_shot.assert_not_called()
        self.assertIsNone(dialog.properties_table)
        dialog.reject()


# ---------------------------------------------------------------- 2: one import layer


class CanonicalImportLayerTest(unittest.TestCase):
    def setUp(self) -> None:
        self.project = QgsProject.instance()
        self.old = _memory_layer("old_memory", features=1, tagged=True)
        self.other = _memory_layer("unrelated", features=1)
        self.project.addMapLayer(self.old)
        self.project.addMapLayer(self.other)
        self.addCleanup(self._remove_all)

    def _remove_all(self) -> None:
        for layer in list(self.project.mapLayers().values()):
            self.project.removeMapLayer(layer.id())

    def _loader(self, new_layer):
        loader = SHPLayerLoader.__new__(SHPLayerLoader)
        loader.parent = None
        loader.target_group = MailablGroupFolders.NEW_PROPERTIES
        loader.lang_manager = LanguageManager()
        loader.engine = Mock(project=self.project)
        loader.engine.import_shapefile_to_memory_layer.return_value = new_layer
        loader._get_shp_file_path = Mock(return_value="C:/data/new.shp")
        loader._choose_bootstrap_path = Mock(return_value=(False, ""))
        loader._resolve_import_result = Mock(return_value=new_layer)
        return loader

    def _run(self, loader):
        source = Mock()
        source.isValid.return_value = True
        with patch.object(flow_module, "QgsVectorLayer", return_value=source), \
                patch.object(flow_module, "ProgressDialogModern"), \
                patch.object(flow_module, "QCoreApplication"), \
                patch.object(flow_module, "PythonFailLogger"), \
                patch.object(flow_module, "ModernMessageDialog") as dialogs:
            result = loader.load_shp_layer()
        return result, dialogs

    def test_a_new_import_replaces_the_old_import_layer(self) -> None:
        new = _memory_layer("new_memory", features=3)
        self.project.addMapLayer(new)

        result, dialogs = self._run(self._loader(new))

        self.assertEqual(result.status, SHPLoadStatus.SUCCESS)
        tagged = [layer for layer in self.project.mapLayers().values() if layer.customProperty(IMPORT_PROPERTY_TAG)]
        self.assertEqual(tagged, [new])
        self.assertIs(MapHelpers.get_layer_by_tag(IMPORT_PROPERTY_TAG), new)
        self.assertIn(self.other.id(), self.project.mapLayers())
        self.assertIn("old_memory", dialogs.show_info.call_args.args[1])

    def test_a_cancelled_import_keeps_the_old_import_layer(self) -> None:
        loader = self._loader(None)
        loader._get_shp_file_path = Mock(return_value=None)

        result, _dialogs = self._run(loader)

        self.assertEqual(result.status, SHPLoadStatus.CANCELLED)
        self.assertIs(MapHelpers.get_layer_by_tag(IMPORT_PROPERTY_TAG), self.old)

    def test_a_failed_import_keeps_the_old_import_layer(self) -> None:
        loader = self._loader(None)

        result, _dialogs = self._run(loader)

        self.assertEqual(result.status, SHPLoadStatus.FAILED)
        self.assertIs(MapHelpers.get_layer_by_tag(IMPORT_PROPERTY_TAG), self.old)


# ---------------------------------------------------------------- 3: delete by ID


class DeleteByIdPreviewTest(unittest.TestCase):
    def _client(self, *responses):
        client = Mock()
        client.send_query.side_effect = list(responses)
        return patch.object(delete_module, "APIClient", return_value=client), client

    def test_preview_reads_number_and_address(self) -> None:
        listing = {"properties": {"edges": [
            {"node": {"id": "9", "displayAddress": "Other"}},
            {"node": {"id": "42", "displayAddress": "Kase tee 1"}},
        ]}}
        api, client = self._client({"property": {"cadastralUnitNumber": "12345:001:0001"}}, listing)
        with api:
            status, data = deleteProperty.load_preview("42")

        self.assertEqual(status, deleteProperty.PREVIEW_OK)
        # Without pageInfo the edges count: one other record shares the number.
        self.assertEqual(data, {"id": "42", "number": "12345:001:0001", "address": "Kase tee 1", "others": 1})
        where = client.send_query.call_args_list[1].kwargs["variables"]["where"]["AND"][0]
        self.assertEqual(where["value"], "12345:001:0001")

    def test_missing_record_is_not_found(self) -> None:
        api, _client = self._client({"property": None})
        with api:
            status, _data = deleteProperty.load_preview("42")
        self.assertEqual(status, deleteProperty.PREVIEW_NOT_FOUND)

    def test_request_error_is_a_failed_preview(self) -> None:
        api, _client = self._client(RuntimeError("offline"))
        with api:
            status, data = deleteProperty.load_preview("42")
        self.assertEqual(status, deleteProperty.PREVIEW_FAILED)
        self.assertTrue(data["error"])


class DeleteByIdDialogTest(unittest.TestCase):
    def setUp(self) -> None:
        with patch.object(DeletePropertyUI, "exec", return_value=0):
            self.dialog = DeletePropertyUI(None)
        self.addCleanup(self.dialog.deleteLater)
        self.dialog._id_input.setText(" 42 ")
        patches = {
            "preview": patch.object(deleteProperty, "load_preview"),
            "delete": patch.object(deleteProperty, "delete_single_item", return_value=(True, "")),
            "dialogs": patch.object(delete_dialog_module, "ModernMessageDialog"),
            "log": patch.object(delete_dialog_module, "PythonFailLogger"),
        }
        self.mocks = {}
        for name, p in patches.items():
            self.mocks[name] = p.start()
            self.addCleanup(p.stop)

    def _preview(self, status, data=None):
        self.mocks["preview"].return_value = (status, data or {})

    def test_confirm_dialog_shows_the_record_and_defaults_to_cancel(self) -> None:
        self._preview(deleteProperty.PREVIEW_OK, {"id": "42", "number": "123:45", "address": "Kase tee 1"})
        self.mocks["dialogs"].ask_yes_no.return_value = False

        self.dialog._on_confirm_clicked()

        self.mocks["preview"].assert_called_once_with("42")
        args, kwargs = self.mocks["dialogs"].ask_yes_no.call_args
        self.assertIn("123:45", args[1])
        self.assertIn("Kase tee 1", args[1])
        self.assertEqual(kwargs["default"], kwargs["no_label"])
        self.mocks["delete"].assert_not_called()
        self.assertTrue(self.dialog._btn_confirm.isEnabled())

    def test_confirmed_delete_runs(self) -> None:
        self._preview(deleteProperty.PREVIEW_OK, {"id": "42", "number": "123:45", "address": ""})
        self.mocks["dialogs"].ask_yes_no.return_value = True

        self.dialog._on_confirm_clicked()

        self.mocks["delete"].assert_called_once_with("42")

    def test_failed_preview_does_not_delete(self) -> None:
        for status in (deleteProperty.PREVIEW_FAILED, deleteProperty.PREVIEW_NOT_FOUND):
            with self.subTest(status=status):
                self.mocks["dialogs"].reset_mock()
                self._preview(status, {"error": "offline"})

                self.dialog._on_confirm_clicked()

                self.mocks["dialogs"].show_warning.assert_called_once()
                self.mocks["dialogs"].ask_yes_no.assert_not_called()
                self.mocks["delete"].assert_not_called()

    def test_an_error_does_not_escape_the_slot(self) -> None:
        self.mocks["preview"].side_effect = RuntimeError("boom")

        self.dialog._on_confirm_clicked()

        self.mocks["log"].log_exception.assert_called_once()
        self.mocks["delete"].assert_not_called()
        self.assertTrue(self.dialog._btn_cancel.isEnabled())


# ---------------------------------------------------------------- 4: stale related records


class _FakeTree(QWidget):
    """A real widget: the tools skip a tree that is not a live Qt object."""

    def __init__(self) -> None:
        super().__init__()
        self.load_connections = Mock()
        self.show_message = Mock()
        self.show_loading = Mock()

    def reset_mock(self) -> None:
        for name in ("load_connections", "show_message", "show_loading"):
            getattr(self, name).reset_mock()


class _FakeUi(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.tree_section = _FakeTree()
        self.property_selection_completed = Mock()
        self._active_token = 1

    def is_token_active(self, token) -> bool:
        return token == self._active_token


class StaleConnectionsTest(unittest.TestCase):
    def setUp(self) -> None:
        self.ui = _FakeUi()
        self.addCleanup(self.ui.deleteLater)
        self.tools = PropertyUITools(self.ui, data_service=Mock())
        p = patch.object(tools_module, "start_worker", return_value=Mock())
        self.start_worker = p.start()
        self.addCleanup(p.stop)

    def _worker(self, index: int):
        return self.start_worker.call_args_list[index].args[0]

    def test_an_older_answer_does_not_fill_the_newer_pick(self) -> None:
        tree = self.ui.tree_section
        self.tools._load_property_connections("A")
        self.tools._load_property_connections("B")

        self._worker(0).finished.emit({"entries": ["a-record"]})
        tree.load_connections.assert_not_called()

        self._worker(1).finished.emit({"entries": ["b-record"]})
        tree.load_connections.assert_called_once_with(["b-record"])

    def test_an_older_error_does_not_replace_the_newer_pick(self) -> None:
        tree = self.ui.tree_section
        self.tools._load_property_connections("A")
        self.tools._load_property_connections("B")
        tree.reset_mock()

        self._worker(0).error.emit("timeout")
        tree.show_message.assert_not_called()

    def test_an_older_search_lookup_is_ignored(self) -> None:
        with patch.object(self.tools, "_load_property_connections") as load:
            self.tools.open_property_from_search("1")
            self.tools.open_property_from_search("2")
            self._worker(0).finished.emit({"cadastralUnitNumber": "A"})
            load.assert_not_called()

    def test_a_map_pick_cancels_a_pending_search_lookup(self) -> None:
        with patch.object(self.tools, "_load_property_connections") as load, \
                patch.object(self.tools, "update_property_display"), \
                patch.object(self.tools, "bring_dialog_to_front"):
            self.tools.open_property_from_search("1")
            self.tools._handle_property_layer_selection(Mock(), [])
            self._worker(0).finished.emit({"cadastralUnitNumber": "A"})
            load.assert_not_called()


# ---------------------------------------------------------------- 5: arrow tooltip


class ToggleArrowTooltipTest(unittest.TestCase):
    def test_arrow_has_tooltip_and_accessible_name(self) -> None:
        lang = LanguageManager()
        section = ModuleConnectionSection("projects", {"count": 0, "items": []})
        self.addCleanup(section.deleteLater)
        expected = lang.translate(TranslationKeys.PROPERTY_TREE_TOGGLE_TOOLTIP)

        self.assertEqual(section.toggle_button.toolTip(), expected)
        self.assertEqual(section.toggle_button.accessibleName(), expected)
        self.assertNotEqual(expected, TranslationKeys.PROPERTY_TREE_TOGGLE_TOOLTIP)


if __name__ == "__main__":
    unittest.main()
