"""**Kustuta ID järgi** also removes the map feature when it belongs to that record alone (2026-11-24).

- Another Kavitro record with the same cadastral number (or an unknown count): the map is not touched.
- A matching layer already in edit mode: nothing is deleted at all, so the user's own edits stay unsaved.
- An unreadable layer: nothing is deleted.
- Kavitro refuses: the map is not touched.
- Removing from the map fails after Kavitro deleted: the user is told the map still has it.
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

from qgis.core import QgsApplication, QgsFeature, QgsProject, QgsVectorLayer

from Kavitro_dev.languages.language_manager import LanguageManager
from Kavitro_dev.languages.translation_keys import TranslationKeys
from Kavitro_dev.modules.Property.dialogs import delete_property_dialog as dialog_module
from Kavitro_dev.modules.Property.dialogs.delete_property_dialog import DeletePropertyUI
from Kavitro_dev.modules.Property.FlowControllers import property_delete as delete_module
from Kavitro_dev.modules.Property.FlowControllers.property_delete import deleteProperty
from Kavitro_dev.utils.MapTools.MapHelpers import LayerLookupError

_APP = QgsApplication.instance() or QgsApplication([], False)
if QgsApplication.instance() is _APP:
    QgsApplication.initQgis()

NUMBER = "12345:001:0001"


def _layer(name: str, numbers: list[str]) -> QgsVectorLayer:
    layer = QgsVectorLayer("Polygon?crs=EPSG:3301&field=tunnus:string", name, "memory")
    features = []
    for number in numbers:
        feature = QgsFeature(layer.fields())
        feature.setAttribute("tunnus", number)
        features.append(feature)
    layer.dataProvider().addFeatures(features)
    return layer


def _numbers(layer: QgsVectorLayer) -> list[str]:
    return sorted(str(f["tunnus"]) for f in layer.getFeatures())


class PreviewCountTest(unittest.TestCase):
    def _preview(self, listing):
        client = Mock()
        client.send_query.side_effect = [{"property": {"cadastralUnitNumber": NUMBER}}, listing]
        with patch.object(delete_module, "APIClient", return_value=client):
            return deleteProperty.load_preview("42")

    def test_total_from_page_info_counts_the_others(self) -> None:
        _status, data = self._preview({"properties": {"pageInfo": {"total": 1},
                                                      "edges": [{"node": {"id": "42"}}]}})
        self.assertEqual(data["others"], 0)

    def test_a_record_missing_from_the_listing_is_an_unknown_count(self) -> None:
        _status, data = self._preview({"properties": {"pageInfo": {"total": 1},
                                                      "edges": [{"node": {"id": "9"}}]}})
        self.assertIsNone(data["others"])


class MapHelpersTest(unittest.TestCase):
    def setUp(self) -> None:
        self.main = _layer("Kinnistud", [NUMBER, "999:1"])
        self.archive = _layer("Arhiiv", [NUMBER])
        QgsProject.instance().addMapLayers([self.main, self.archive])
        self.addCleanup(QgsProject.instance().removeMapLayers, [self.main.id(), self.archive.id()])

    def _settings(self, main, archive):
        settings = Mock()
        settings.module_main_layer_name.return_value = main
        settings.module_archive_layer_name.return_value = archive
        return patch.object(delete_module, "SettingsService", return_value=settings)

    def test_main_and_archive_layers_each_once(self) -> None:
        with self._settings(self.main.id(), self.archive.id()):
            self.assertEqual([lyr.id() for lyr in deleteProperty.property_map_layers()], [self.main.id(), self.archive.id()])
        with self._settings(self.main.id(), self.main.id()):
            self.assertEqual(len(deleteProperty.property_map_layers()), 1)
        with self._settings("", ""):
            self.assertEqual(deleteProperty.property_map_layers(), [])

    def test_matches_and_removal(self) -> None:
        with patch.object(deleteProperty, "property_map_layers", return_value=[self.main, self.archive]):
            matches = deleteProperty.map_matches(NUMBER)
        self.assertEqual([(lyr.id(), n) for lyr, n in matches], [(self.main.id(), 1), (self.archive.id(), 1)])

        removed, errors = deleteProperty.remove_from_map(NUMBER, [self.main, self.archive])

        self.assertEqual((removed, errors), (2, []))
        self.assertEqual(_numbers(self.main), ["999:1"])
        self.assertEqual(_numbers(self.archive), [])
        self.assertFalse(self.main.isEditable())

    def test_a_layer_in_edit_mode_is_refused_and_keeps_its_edits(self) -> None:
        self.main.startEditing()
        self.addCleanup(self.main.rollBack)
        extra = QgsFeature(self.main.fields())
        extra.setAttribute("tunnus", "user-edit")
        self.main.addFeature(extra)

        removed, errors = deleteProperty.remove_from_map(NUMBER, [self.main])

        self.assertEqual(removed, 0)
        self.assertEqual(len(errors), 1)
        self.assertTrue(self.main.isEditable())
        self.assertEqual(self.main.dataProvider().featureCount(), 2)  # the user's feature was not committed


class DeleteDialogMapTest(unittest.TestCase):
    def setUp(self) -> None:
        self.lang = LanguageManager("et")
        with patch.object(DeletePropertyUI, "exec_", return_value=0):
            self.dialog = DeletePropertyUI(None)
        self.addCleanup(self.dialog.deleteLater)
        self.dialog._id_input.setText("42")
        self.main = _layer("Kinnistud", [NUMBER, "999:1"])
        QgsProject.instance().addMapLayer(self.main)
        self.addCleanup(QgsProject.instance().removeMapLayer, self.main.id())
        patches = {
            "preview": patch.object(deleteProperty, "load_preview",
                                    return_value=(deleteProperty.PREVIEW_OK, {"id": "42", "number": NUMBER, "address": "Kase 1", "others": 0})),
            "layers": patch.object(deleteProperty, "property_map_layers", return_value=[self.main]),
            "delete": patch.object(deleteProperty, "delete_single_item", return_value=(True, "")),
            "dialogs": patch.object(dialog_module, "ModernMessageDialog"),
            "log": patch.object(dialog_module, "PythonFailLogger"),
        }
        self.mocks = {name: p.start() for name, p in patches.items()}
        for p in patches.values():
            self.addCleanup(p.stop)
        self.mocks["dialogs"].ask_yes_no.return_value = True

    def _confirm_text(self) -> str:
        return self.mocks["dialogs"].ask_yes_no.call_args.args[1]

    def test_sole_record_removes_the_map_feature_too(self) -> None:
        self.dialog._on_confirm_clicked()

        self.assertIn(self.lang.translate(TranslationKeys.PROPERTY_DELETE_BY_ID_MAP_REMOVE).format(
            count=1, layers="Kinnistud"), self._confirm_text())
        self.mocks["delete"].assert_called_once_with("42")
        self.assertEqual(_numbers(self.main), ["999:1"])
        info = self.mocks["dialogs"].show_info.call_args.args[1]
        self.assertIn(self.lang.translate(TranslationKeys.PROPERTY_DELETE_BY_ID_MAP_REMOVED).format(count=1), info)

    def test_shared_or_unknown_number_leaves_the_map(self) -> None:
        for others in (1, None):
            with self.subTest(others=others):
                self.mocks["preview"].return_value = (deleteProperty.PREVIEW_OK,
                                                      {"id": "42", "number": NUMBER, "address": "", "others": others})
                self.dialog._on_confirm_clicked()
                self.assertIn(self.lang.translate(TranslationKeys.PROPERTY_DELETE_BY_ID_MAP_SHARED), self._confirm_text())
                self.assertEqual(_numbers(self.main), [NUMBER, "999:1"])

    def test_no_feature_on_the_map_says_so(self) -> None:
        self.mocks["preview"].return_value = (deleteProperty.PREVIEW_OK,
                                              {"id": "42", "number": "777:7", "address": "", "others": 0})
        self.dialog._on_confirm_clicked()
        self.assertIn(self.lang.translate(TranslationKeys.PROPERTY_DELETE_BY_ID_MAP_NONE), self._confirm_text())
        self.mocks["delete"].assert_called_once()

    def test_layer_in_edit_mode_stops_before_anything_is_deleted(self) -> None:
        self.main.startEditing()
        self.addCleanup(self.main.rollBack)

        self.dialog._on_confirm_clicked()

        self.mocks["dialogs"].ask_yes_no.assert_not_called()
        self.mocks["delete"].assert_not_called()
        self.assertIn("Kinnistud", self.mocks["dialogs"].show_warning.call_args.args[1])

    def test_unreadable_layer_stops_before_anything_is_deleted(self) -> None:
        with patch.object(deleteProperty, "map_matches", side_effect=LayerLookupError("broken")):
            self.dialog._on_confirm_clicked()

        self.mocks["delete"].assert_not_called()
        self.assertEqual(self.mocks["dialogs"].show_warning.call_args.args[1],
                         self.lang.translate(TranslationKeys.PROPERTY_DELETE_BY_ID_MAP_READ_FAILED))

    def test_cancel_and_kavitro_refusal_leave_the_map(self) -> None:
        self.mocks["dialogs"].ask_yes_no.return_value = False
        self.dialog._on_confirm_clicked()
        self.assertEqual(_numbers(self.main), [NUMBER, "999:1"])

        self.mocks["dialogs"].ask_yes_no.return_value = True
        self.mocks["delete"].return_value = (False, "refused")
        self.dialog._on_confirm_clicked()
        self.assertEqual(_numbers(self.main), [NUMBER, "999:1"])
        self.mocks["dialogs"].show_info.assert_not_called()

    def test_map_failure_after_the_kavitro_delete_is_reported(self) -> None:
        with patch.object(deleteProperty, "remove_from_map", return_value=(0, ["Kinnistud: locked"])):
            self.dialog._on_confirm_clicked()

        self.assertEqual(self.mocks["dialogs"].show_warning.call_args.args[1],
                         self.lang.translate(TranslationKeys.PROPERTY_DELETE_BY_ID_MAP_FAILED).format(error="Kinnistud: locked"))
        self.mocks["dialogs"].show_info.assert_not_called()


if __name__ == "__main__":
    unittest.main()
