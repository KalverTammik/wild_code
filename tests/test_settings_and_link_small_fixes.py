"""Small settings and link fixes from the button audits (2026-11-23).

- the layer mapper does not offer the target layer as its own source;
- the easement status mapping reads the statuses once, not twice;
- a sewer mapping row can be removed;
- the gear of a settings value names what it changes;
- the link review button says it adds links;
- the project folder needs only the folder settings;
- a form closed with Cancel after drawing is a cancel, not a failed save.
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

from qgis.core import QgsApplication, QgsFeature, QgsGeometry, QgsPointXY, QgsProject, QgsVectorLayer
from qgis.PyQt.QtWidgets import QPushButton, QTreeWidget

from Kavitro_dev.languages.language_manager import LanguageManager
from Kavitro_dev.languages.translation_keys import TranslationKeys
from Kavitro_dev.Logs.python_fail_logger import PythonFailLogger
from Kavitro_dev.modules.easements import easement_status_mapping_dialog as mapping_module
from Kavitro_dev.modules.projects import projects_card_actions as project_actions_module
from Kavitro_dev.modules.Settings.cards.ModuleLabelsWidget import ModuleLabelsWidget
from Kavitro_dev.modules.Settings.cards.SettingsProjectBaseLayersCard import SettingsProjectBaseLayersCard
from Kavitro_dev.modules.Settings.GeospatialLayerMapperDialog import GeospatialLayerMapperDialog
from Kavitro_dev.ui import settings_setup_guard as guard_module
from Kavitro_dev.ui.map_tools import module_feature_controllers as controllers_module
from Kavitro_dev.ui.map_tools.module_feature_controllers import FeatureLinkResult, ModuleFeatureDrawController
from Kavitro_dev.ui.messages_helper import ModernMessageDialog
from Kavitro_dev.widgets.DataDisplayWidgets.LinkReviewDialog import PropertyLinkReviewDialog

_APP = QgsApplication.instance() or QgsApplication([], False)
LANG = LanguageManager()


class DialogStubCase(unittest.TestCase):
    def setUp(self) -> None:
        for name in ("show_warning", "show_info", "ask_choice_modern", "ask_yes_no"):
            patcher = patch.object(ModernMessageDialog, name)
            setattr(self, name, patcher.start())
            self.addCleanup(patcher.stop)
        for name in ("log", "log_exception"):
            patcher = patch.object(PythonFailLogger, name)
            setattr(self, name, patcher.start())
            self.addCleanup(patcher.stop)


class MapperSourceTest(DialogStubCase):
    def test_the_target_is_not_offered_and_is_refused(self) -> None:
        target = QgsVectorLayer("Point?crs=EPSG:3301", "siht", "memory")
        other = QgsVectorLayer("Point?crs=EPSG:3301", "allikas", "memory")
        QgsProject.instance().addMapLayers([target, other])
        self.addCleanup(QgsProject.instance().removeMapLayers, [target.id(), other.id()])
        dialog = GeospatialLayerMapperDialog(lang_manager=LANG, module_name="works", target_layer=target)
        self.addCleanup(dialog.deleteLater)

        tree = QTreeWidget()
        dialog._source_combo._populate_tree(tree)
        names = []
        iterator = [tree.topLevelItem(i) for i in range(tree.topLevelItemCount())]
        while iterator:
            item = iterator.pop()
            names.append(item.text(0))
            iterator += [item.child(i) for i in range(item.childCount())]
        self.assertFalse(any(name.startswith("siht") for name in names), names)
        self.assertTrue(any(name.startswith("allikas") for name in names), names)

        dialog._source_combo._current_layer_id = target.id()  # e.g. a layer chosen before the exclusion
        with patch.object(dialog, "_transfer_features") as transfer:
            dialog._on_accept()
        transfer.assert_not_called()
        self.assertEqual(self.show_warning.call_args.args[1],
                         LANG.translate(TranslationKeys.GEOSPATIAL_LAYER_MAPPER_SAME_LAYER))


class StatusMappingOneReadTest(DialogStubCase):
    def test_the_statuses_are_read_once(self) -> None:
        layer = Mock()
        with patch.object(mapping_module.EasementLayerService, "resolve_main_layer", return_value=layer) as resolve, \
                patch.object(mapping_module.EasementLayerService, "resolve_status_field_name", return_value="staatus"), \
                patch.object(mapping_module.EasementLayerService, "layer_status_value_options", return_value=["A"]), \
                patch.object(mapping_module.APIModuleActions, "get_module_status_options",
                             return_value=[{"id": "1", "name": "Uus"}]) as statuses, \
                patch.object(mapping_module.EasementStatusMappingDialog, "exec_", return_value=0):
            mapping_module.EasementStatusMappingDialog.edit_mapping(lang_manager=LANG)
        statuses.assert_called_once()
        resolve.assert_called_once()


class SewerRowRemoveTest(DialogStubCase):
    def test_a_row_can_be_removed(self) -> None:
        card = SettingsProjectBaseLayersCard(LANG)
        self.addCleanup(card.deleteLater)
        card._pend_sewer_mapping_enabled = True
        card._on_add_mapping_row()
        card._on_add_mapping_row()
        self.assertEqual(len(card._pend_sewer_mapping_rows), 2)
        first_kind = card._pend_sewer_mapping_rows[0]["kind"]
        changes = []
        card.pendingChanged.connect(changes.append)

        remove = card._mapping_row_items[1]["widget"].findChild(QPushButton, "MappingRowRemoveButton")
        self.assertEqual(remove.toolTip(), LANG.translate(TranslationKeys.SETTINGS_SHARED_SEWER_REMOVE_ROW))
        remove.click()

        self.assertEqual([row["kind"] for row in card._pend_sewer_mapping_rows], [first_kind])
        self.assertEqual(len(card._mapping_row_items), 1)
        self.assertTrue(changes)


class GearTooltipTest(unittest.TestCase):
    def test_the_gear_names_its_value(self) -> None:
        labels = [{"key": "rule", "title_value": "Kausta nime reegel", "tool": "button", "on_click": lambda *a: None,
                   "value": ""}]
        widget = ModuleLabelsWidget("project", labels, LANG)
        self.addCleanup(widget.deleteLater)
        gear = widget.findChild(QPushButton, "rule_button")
        self.assertIn("Kausta nime reegel", gear.toolTip())


class LinkReviewLabelTest(unittest.TestCase):
    def test_the_confirm_button_says_it_adds(self) -> None:
        dialog = PropertyLinkReviewDialog({"1:1": "1:1"}, {"2:2": "2:2"}, LANG)
        self.addCleanup(dialog.deleteLater)
        texts = [button.text() for button in dialog.findChildren(QPushButton)]
        self.assertIn(LANG.translate(TranslationKeys.LINK_REVIEW_ADD_SELECTED), texts)


class ProjectFolderSettingsTest(DialogStubCase):
    def test_only_the_folder_settings_are_needed(self) -> None:
        host = Mock(item_data={"id": "1", "name": "P"}, lang_manager=LANG)
        actions = project_actions_module.ProjectCardActions(host)
        with patch.object(guard_module.SettingsSetupGuard, "missing_requirements", return_value=["preferred-tags"]), \
                patch.object(guard_module.SettingsSetupGuard, "missing_project_folder_settings", return_value=[]), \
                patch.object(project_actions_module.FolderEngines, "generate_project_folder_from_template") as make:
            actions.generate_folder()
        make.assert_called_once()
        self.show_warning.assert_not_called()

    def test_a_missing_folder_setting_still_stops_it(self) -> None:
        host = Mock(item_data={"id": "1"}, lang_manager=LANG)
        actions = project_actions_module.ProjectCardActions(host)
        with patch.object(guard_module.SettingsSetupGuard, "missing_project_folder_settings",
                          return_value=["label:source"]), \
                patch.object(project_actions_module.ModuleSwitchHelper, "switch_module"), \
                patch.object(project_actions_module.FolderEngines, "generate_project_folder_from_template") as make:
            actions.generate_folder()
        make.assert_not_called()
        self.show_warning.assert_called_once()

    def test_the_check_reads_only_the_three_folder_settings(self) -> None:
        logic = Mock()
        logic.load_module_label_value.side_effect = lambda _module, key: "" if key == sorted(
            guard_module.SettingsSetupGuard._PROJECT_FOLDER_LABEL_KEYS)[0] else "x"
        with patch.object(guard_module, "SettingsLogic", return_value=logic):
            missing = guard_module.SettingsSetupGuard.missing_project_folder_settings("project")
        self.assertEqual(len(missing), 1)
        self.assertEqual(logic.load_module_label_value.call_count, 3)


class FormCancelTest(DialogStubCase):
    def test_cancel_removes_the_feature_without_an_error(self) -> None:
        layer = QgsVectorLayer("Point?crs=EPSG:3301", "draw", "memory")
        timers = []
        for target, name in ((controllers_module, "MapHelpers"), (controllers_module, "iface")):
            patcher = patch.object(target, name)
            patcher.start()
            self.addCleanup(patcher.stop)
        controller = ModuleFeatureDrawController()
        with patch.object(controllers_module.QTimer, "singleShot", side_effect=lambda _ms, fn: timers.append(fn)):
            controller.start_draw(
                item_data={"id": "42"}, resolve_layer=lambda: layer,
                on_feature_created=lambda *_a: FeatureLinkResult(False, "cancelled", cancelled=True),
                start_failed_message="start", layer_save_failed_message="not saved {item_id}: {error}",
                sync_failed_message="x {item_id}: {error}", success_message="ok {item_id}", title_error="E",
                title_success="S", log_module="asbuilt",
            )
            feature = QgsFeature(layer.fields())
            feature.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(1, 2)))
            layer.addFeature(feature)
        timers[0]()

        self.assertEqual(layer.featureCount(), 0)
        self.assertFalse(layer.isEditable())
        self.show_warning.assert_not_called()
        self.show_info.assert_not_called()


if __name__ == "__main__":
    unittest.main()
