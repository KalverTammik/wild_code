"""Settings actions do not damage data without the user knowing (the five high settings findings, 2026-11-24).

- Reset asks first and stays pending: Confirm saves it, Discard brings everything back (base layers card here;
  the module card is in test_settings_module_card_behaviour).
- Overwriting a standalone GeoPackage keeps the old file as a backup (flow test in the same file as above).
- The mapper is one transaction: a feature that cannot be written or transformed rolls everything back, so a
  second try cannot double features; with only empty fields the result is saved and the dialog closes.
- A transform that cannot be built, or a layer without a coordinate system, stops the transfer: features
  were copied with untransformed coordinates.
"""
from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
if os.environ.get("QGIS_PREFIX_PATH"):
    sys.path.append(str(Path(os.environ["QGIS_PREFIX_PATH"]) / "python" / "plugins"))

from qgis.core import QgsApplication, QgsCoordinateReferenceSystem, QgsFeature, QgsGeometry, QgsVectorLayer
from qgis.PyQt.QtCore import QCoreApplication, QEvent
from qgis.PyQt.QtWidgets import QWidget

from Kavitro_dev.languages.language_manager import LanguageManager
from Kavitro_dev.languages.translation_keys import TranslationKeys
from Kavitro_dev.Logs.python_fail_logger import PythonFailLogger
from Kavitro_dev.modules.Settings.GeospatialLayerMapperDialog import GeospatialLayerMapperDialog
from Kavitro_dev.modules.Settings.SettingsUI import SettingsModule
from Kavitro_dev.modules.Settings.cards.SettingsProjectBaseLayersCard import SettingsProjectBaseLayersCard
from Kavitro_dev.modules.works.works_entry import WorksTempLayerHelper
from Kavitro_dev.ui.messages_helper import ModernMessageDialog
from Kavitro_dev.utils.project_base_layers import ProjectBaseLayerKeys

_APP = QgsApplication.instance() or QgsApplication([], False)
LANG = LanguageManager("et")


def layer(crs: str, rows, *, name="layer") -> QgsVectorLayer:
    result = QgsVectorLayer(f"Point?crs={crs}&field=name:string&field=ext_job_id:string", name, "memory")
    features = []
    for wkt, value in rows:
        feature = QgsFeature(result.fields())
        feature.setGeometry(QgsGeometry.fromWkt(wkt))
        feature.setAttribute("name", value)
        feature.setAttribute("ext_job_id", value)
        features.append(feature)
    result.dataProvider().addFeatures(features)
    return result


ROWS = [
    {"target": "name", "source": "name", "has_default": False, "default": None},
    {"target": "ext_job_id", "source": "ext_job_id", "has_default": False, "default": None},
]


class DialogCase(unittest.TestCase):
    def setUp(self) -> None:
        for name in ("show_warning", "show_info", "ask_yes_no", "ask_choice_modern"):
            patcher = patch.object(ModernMessageDialog, name)
            setattr(self, name, patcher.start())
            self.addCleanup(patcher.stop)
        for name in ("log", "log_exception"):
            patcher = patch.object(PythonFailLogger, name)
            patcher.start()
            self.addCleanup(patcher.stop)
        self.window = QWidget()
        self.addCleanup(self.window.deleteLater)


class MapperTransactionTest(DialogCase):
    def dialog(self, target) -> GeospatialLayerMapperDialog:
        dialog = GeospatialLayerMapperDialog(lang_manager=LANG, module_name="works", target_layer=target, parent=self.window)
        self.addCleanup(lambda: QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete))
        return dialog

    def test_one_untransformable_feature_writes_nothing(self) -> None:
        source = layer("EPSG:4326", [("POINT(24 58)", "good"), ("POINT(1000000 1000000)", "bad")])
        target = layer("EPSG:3301", [])
        dialog = self.dialog(target)

        result = dialog._transfer_features(source, ROWS)

        self.assertEqual(result[:3], (0, 0, 0))
        self.assertFalse(dialog._last_transfer_written)
        self.assertEqual(target.featureCount(), 0)
        self.assertFalse(target.isEditable())

    def test_a_feature_that_cannot_be_added_writes_nothing(self) -> None:
        source = layer("EPSG:3301", [("POINT(1 1)", "a"), ("POINT(2 2)", "b")])
        target = layer("EPSG:3301", [])
        dialog = self.dialog(target)
        calls = []

        def add(feature):
            calls.append(feature)
            return len(calls) == 1 and QgsVectorLayer.addFeature(target, feature)

        with patch.object(target, "addFeature", side_effect=add):
            dialog._transfer_features(source, ROWS)

        self.assertFalse(dialog._last_transfer_written)
        self.assertEqual(target.featureCount(), 0)

    def test_nothing_written_keeps_the_dialog_open_and_says_so(self) -> None:
        source = layer("EPSG:4326", [("POINT(1000000 1000000)", "bad")])
        target = layer("EPSG:3301", [])
        dialog = self.dialog(target)
        self.ask_yes_no.return_value = True
        with patch.object(dialog._source_combo, "currentLayer", return_value=source), \
                patch.object(dialog, "accept") as accept:
            dialog._on_accept()
        accept.assert_not_called()
        self.assertTrue(self.show_warning.call_args.args[1].startswith(
            LANG.translate(TranslationKeys.GEOSPATIAL_LAYER_MAPPER_NOTHING_WRITTEN).split("{")[0]))

    def test_a_saved_transfer_with_empty_fields_closes_the_dialog(self) -> None:
        source = layer("EPSG:3301", [("POINT(1 1)", "a")])
        target = layer("EPSG:3301", [])
        dialog = self.dialog(target)
        self.ask_yes_no.return_value = True
        with patch.object(dialog._source_combo, "currentLayer", return_value=source), \
                patch.object(dialog, "_value_problems_note", return_value="width left empty"), \
                patch.object(dialog, "_coerce_value_for_field",
                             side_effect=lambda field, value, problems: (problems.append(object()), value)[1]), \
                patch.object(dialog, "_log_value_problems"), \
                patch.object(dialog, "_collect_mapping_rows", return_value=ROWS), \
                patch.object(dialog, "accept") as accept:
            dialog._on_accept()
        self.assertEqual(target.featureCount(), 1)
        accept.assert_called_once()
        self.show_warning.assert_called_once()

    def test_a_target_in_edit_mode_is_refused(self) -> None:
        source = layer("EPSG:3301", [("POINT(1 1)", "a")])
        target = layer("EPSG:3301", [], name="Tööd")
        target.startEditing()
        self.addCleanup(target.rollBack)
        dialog = self.dialog(target)
        with patch.object(dialog._source_combo, "currentLayer", return_value=source):
            dialog._on_accept()
        self.ask_yes_no.assert_not_called()
        self.assertIn("Tööd", self.show_warning.call_args.args[1])


class TransformCheckTest(DialogCase):
    def dialog(self, target):
        return GeospatialLayerMapperDialog(lang_manager=LANG, module_name="works", target_layer=target, parent=self.window)

    def test_a_layer_without_a_crs_stops_before_anything(self) -> None:
        source = QgsVectorLayer("Point?field=name:string", "no crs", "memory")
        source.setCrs(QgsCoordinateReferenceSystem())
        target = layer("EPSG:3301", [])
        dialog = self.dialog(target)
        with patch.object(dialog._source_combo, "currentLayer", return_value=source):
            dialog._on_accept()
        self.ask_yes_no.assert_not_called()
        self.assertEqual(self.show_warning.call_args.args[1],
                         LANG.translate(TranslationKeys.GEOSPATIAL_LAYER_MAPPER_CRS_MISSING))
        self.assertEqual(dialog._transfer_features(source, ROWS)[:3], (0, 0, 0))

    def test_a_transform_that_cannot_be_built_stops_the_transfer(self) -> None:
        source = layer("EPSG:4326", [("POINT(24 58)", "a")])
        target = layer("EPSG:3301", [])
        dialog = self.dialog(target)
        from Kavitro_dev.modules.Settings import GeospatialLayerMapperDialog as mapper_module
        with patch.object(mapper_module.QgsCoordinateTransform, "isValid", return_value=False):
            self.assertTrue(dialog._geometry_transform_problem(source, target))
            self.assertEqual(dialog._transfer_features(source, ROWS)[:3], (0, 0, 0))
        self.assertEqual(target.featureCount(), 0)

    def test_the_same_crs_or_a_good_transform_is_no_problem(self) -> None:
        target = layer("EPSG:3301", [])
        dialog = self.dialog(target)
        self.assertEqual(dialog._geometry_transform_problem(layer("EPSG:3301", []), target), "")
        self.assertEqual(dialog._geometry_transform_problem(layer("EPSG:4326", []), target), "")


class BaseLayersResetTest(DialogCase):
    def card(self) -> SettingsProjectBaseLayersCard:
        card = SettingsProjectBaseLayersCard(LANG)
        self.addCleanup(card.deleteLater)
        card._orig_enabled = card._pend_enabled = True
        card._orig_layers = {key: "" for key in ProjectBaseLayerKeys.ORDER}
        card._orig_layers[ProjectBaseLayerKeys.ORDER[0]] = "layer-1"
        card._pend_layers = dict(card._orig_layers)
        return card

    def test_no_reset_without_a_yes(self) -> None:
        card = self.card()
        self.ask_yes_no.return_value = False
        with patch.object(card._service, "clear") as clear:
            card._on_reset_settings()
        clear.assert_not_called()
        self.assertFalse(card.has_pending_changes())

    def test_the_reset_waits_for_confirm_and_discard_brings_it_back(self) -> None:
        card = self.card()
        self.ask_yes_no.return_value = True
        with patch.object(card._service, "clear") as clear, patch.object(card._service, "save_state") as save:
            card._on_reset_settings()
            clear.assert_not_called()
            save.assert_not_called()
            self.assertTrue(card.has_pending_changes())
            card.revert()
        self.assertFalse(card.has_pending_changes())
        self.assertEqual(card._pend_layers[ProjectBaseLayerKeys.ORDER[0]], "layer-1")
        self.assertTrue(card._pend_enabled)

    def test_confirm_saves_the_reset(self) -> None:
        card = self.card()
        self.ask_yes_no.return_value = True
        card._on_reset_settings()
        with patch.object(card._service, "save_state") as save, \
                patch.object(card._settings_service, "geospatial_setup_mode"):
            card.apply()
        self.assertFalse(save.call_args.kwargs["evel_enabled"])
        self.assertEqual(set(save.call_args.kwargs["layers"].values()), {""})


class GeoPackageBackupTest(unittest.TestCase):
    def test_the_old_file_is_renamed_never_deleted(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            path = os.path.join(folder, "tood.gpkg")
            Path(path).write_text("old data")
            backup = WorksTempLayerHelper.backup_path_for(path, stamp="20261124-120000")
            self.assertEqual(os.path.basename(backup), "tood.backup-20261124-120000.gpkg")
            with patch.object(PythonFailLogger, "log"):
                self.assertEqual(WorksTempLayerHelper.move_gpkg_to_backup(path, backup), (True, ""))
            self.assertFalse(os.path.exists(path))
            self.assertEqual(Path(backup).read_text(), "old data")

    def test_a_locked_file_is_left_alone_and_reported(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            path = os.path.join(folder, "tood.gpkg")
            Path(path).write_text("old data")
            with patch("os.replace", side_effect=PermissionError("locked")), \
                    patch.object(PythonFailLogger, "log_exception"):
                ok, error = WorksTempLayerHelper.move_gpkg_to_backup(path, path + ".bak")
            self.assertFalse(ok)
            self.assertIn("locked", error)
            self.assertTrue(os.path.exists(path))


class LeaveSettingsPromptTest(unittest.TestCase):
    """Found in QGIS 2026-11-24: the leave prompt showed English text and an English Discard button."""

    def _owner(self) -> SimpleNamespace:
        return SimpleNamespace(
            lang_manager=LanguageManager("et"),
            has_unsaved_changes=lambda: True,
            apply_pending_changes=MagicMock(),
            revert_pending_changes=MagicMock(),
        )

    def test_prompt_is_in_estonian_and_discard_reverts(self) -> None:
        owner = self._owner()
        with patch.object(ModernMessageDialog, "ask_choice_modern", return_value="Hülga") as ask:
            self.assertTrue(SettingsModule.confirm_navigation_away(owner))

        title, message = ask.call_args.args
        self.assertEqual(title, "Salvestamata muudatused")
        self.assertIn("salvestamata muudatusi", message)
        self.assertEqual(ask.call_args.kwargs["buttons"], ["Salvesta", "Hülga", "Tühista"])
        owner.revert_pending_changes.assert_called_once_with()
        owner.apply_pending_changes.assert_not_called()

    def test_cancel_stays_in_settings(self) -> None:
        owner = self._owner()
        with patch.object(ModernMessageDialog, "ask_choice_modern", return_value="Tühista"):
            self.assertFalse(SettingsModule.confirm_navigation_away(owner))
        owner.revert_pending_changes.assert_not_called()


if __name__ == "__main__":
    unittest.main()
