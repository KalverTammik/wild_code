"""What each module's card menu offers and what its actions start."""
from __future__ import annotations

import ast
import os
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
if os.environ.get("QGIS_PREFIX_PATH"):
    sys.path.append(str(Path(os.environ["QGIS_PREFIX_PATH"]) / "python" / "plugins"))

from PyQt5.QtCore import QCoreApplication, QEvent, Qt
from PyQt5.QtWidgets import QApplication, QDialog, QWidget

from Kavitro_dev import module_manager as module_manager_module
from Kavitro_dev.languages.language_manager import LanguageManager
from Kavitro_dev.languages.translation_keys import ToolbarTranslationKeys, TranslationKeys
from Kavitro_dev.module_manager import ModuleManager
from Kavitro_dev.modules.Settings.setting_keys import SettingDialogPlaceholders
from Kavitro_dev.modules.asbuilt import asbuilt_card_actions
from Kavitro_dev.modules.easements import easement_card_actions
from Kavitro_dev.modules.projects import projects_card_actions
from Kavitro_dev.modules.works import works_card_actions
from Kavitro_dev.python.responses import DataDisplayExtractors
from Kavitro_dev.ui.modules_registry import ModulesRegistry
from Kavitro_dev.utils.messagesHelper import ModernMessageDialog
from Kavitro_dev.utils.url_manager import Module
from Kavitro_dev.widgets.DataDisplayWidgets.module_action_buttons import MoreActionsButton

# Where each module's card actions look up the names these tests replace.
HOME = {
    "project": projects_card_actions,
    "asbuilt": asbuilt_card_actions,
    "easement": easement_card_actions,
    "works": works_card_actions,
}
MENUS = {
    "project": [ToolbarTranslationKeys.GENERATE_PROJECT_FOLDER, TranslationKeys.PROJECT_PREVIEW_ACTION,
                TranslationKeys.PROJECT_DRAW_NEW_ACTION],
    "asbuilt": [TranslationKeys.ASBUILT_UPDATE_NOTES_ACTION, TranslationKeys.ASBUILT_DRAW_NEW_ACTION],
    "easement": [TranslationKeys.TASK_FILES_ACTION, TranslationKeys.EASEMENT_DRAW_NEW_ACTION,
                 TranslationKeys.EASEMENT_ATTACH_EXISTING_ACTION, TranslationKeys.EASEMENT_EDIT_GEOMETRY_ACTION,
                 TranslationKeys.EASEMENT_PREVIEW_ACTION],
    "works": [TranslationKeys.WORKS_ADD_EXISTING_ON_MAP_ACTION, TranslationKeys.WORKS_REPOSITION_ACTION],
    "contract": [],
    "coordination": [],
}
ITEM = {"id": "7", "name": "Nimi", "number": "P-1", "projectNumber": "P-1"}
NO_ID = {"name": "Nimi"}


class CardCase(unittest.TestCase):
    MODULE = ""

    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self) -> None:
        self.lang = LanguageManager("en")
        self.host = QWidget()
        self.addCleanup(self.delete_host)

        # A real message window would wait for a click that never comes.
        for name in ("show_info", "show_warning", "show_error", "Warning_messages_modern"):
            patcher = patch.object(ModernMessageDialog, name)
            patcher.start()
            self.addCleanup(patcher.stop)

        # The menus are built from what the plugin dialog registers.
        manager = ModuleManager()
        names_before = list(module_manager_module.MODULES_LIST_BY_NAME)
        modules_before = dict(manager.modules)
        manager.modules.clear()
        ModulesRegistry.register_all(manager, SimpleNamespace(lang_manager=self.lang, sidebar=Mock()))

        def restore() -> None:
            manager.modules.clear()
            manager.modules.update(modules_before)
            module_manager_module.MODULES_LIST_BY_NAME[:] = names_before

        self.addCleanup(restore)

    def delete_host(self) -> None:
        self.host.hide()
        self.host.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)

    def button(self, item=None, module=None, **options) -> MoreActionsButton:
        button = MoreActionsButton(self.lang, dict(ITEM if item is None else item), module or self.MODULE, **options)
        button.setParent(self.host)
        return button

    def trigger(self, button: MoreActionsButton, key) -> None:
        label = self.lang.translate(key)
        next(action for action in button.menu().actions() if action.text() == label).trigger()

    def replace(self, name: str) -> Mock:
        patcher = patch.object(HOME[self.MODULE], name)
        self.addCleanup(patcher.stop)
        return patcher.start()


class CardMenuTest(CardCase):
    def test_each_module_offers_its_own_actions_in_order_and_linking_last(self) -> None:
        for module, keys in MENUS.items():
            with self.subTest(module=module):
                labels = [action.text() for action in self.button(module=module).menu().actions()]
                self.assertEqual(labels, [self.lang.translate(key) for key in [*keys, TranslationKeys.CONNECT_PROPERTIES]])

    def test_module_given_as_an_enum_or_in_capitals_finds_its_actions(self) -> None:
        for module in (Module.WORKS, "WORKS", " works "):
            with self.subTest(module=module):
                self.assertEqual(len(self.button(module=module).menu().actions()), 3)

    def test_linking_action_starts_property_linking_for_any_module(self) -> None:
        for module in MENUS:
            with self.subTest(module=module), patch.object(MoreActionsButton, "_link_properties_from_map") as link:
                button = self.button(module=module)
                self.trigger(button, TranslationKeys.CONNECT_PROPERTIES)
                link.assert_called_once()
                self.assertEqual(link.call_args.args[0], module)


class ProjectFolderTest(CardCase):
    MODULE = "project"

    def setUp(self) -> None:
        super().setUp()
        self.guard = self.replace("SettingsSetupGuard")
        self.messages = self.replace("ModernMessageDialog")
        self.switch = self.replace("ModuleSwitchHelper")
        self.settings = self.replace("SettingsService")
        self.engine = self.replace("FolderEngines")
        self.settings.return_value.module_label_value.side_effect = lambda _module, key: f"kaust:{key}"

    def generate(self, **options) -> MoreActionsButton:
        button = self.button(**options)
        self.trigger(button, ToolbarTranslationKeys.GENERATE_PROJECT_FOLDER)
        return button

    def test_missing_settings_send_the_user_to_settings(self) -> None:
        self.guard.missing_requirements.return_value = ["puudu"]
        self.guard.redirect_warning_text.return_value = ("Pealkiri", "Tekst")
        self.generate()
        self.guard.redirect_warning_text.assert_called_once_with(self.lang, "project")
        self.assertEqual(self.messages.show_warning.call_args.args, ("Pealkiri", "Tekst"))
        self.switch.switch_module.assert_called_once_with(Module.SETTINGS.name, focus_module="project")
        self.engine.generate_project_folder_from_template.assert_not_called()

    def test_folder_is_made_from_the_configured_folders(self) -> None:
        self.guard.missing_requirements.return_value = []
        self.generate()
        create = self.engine.generate_project_folder_from_template
        create.assert_called_once()
        self.assertEqual(create.call_args.args, (DataDisplayExtractors.extract_item_id(ITEM),
                                                 DataDisplayExtractors.extract_item_name(ITEM),
                                                 DataDisplayExtractors.extract_project_number(ITEM)))
        self.assertEqual(create.call_args.kwargs["source_folder"], f"kaust:{SettingDialogPlaceholders.PROJECTS_SOURCE_FOLDER}")
        self.assertEqual(create.call_args.kwargs["target_folder"], f"kaust:{SettingDialogPlaceholders.PROJECTS_TARGET_FOLDER}")
        self.messages.show_warning.assert_not_called()

    def test_new_path_reaches_the_card_and_its_callback(self) -> None:
        self.guard.missing_requirements.return_value = []
        updated = Mock()
        button = self.generate(on_files_path_updated=updated)
        report = self.engine.generate_project_folder_from_template.call_args.kwargs["on_files_path_updated"]
        report("  C:/Projektid/P-1  ")
        updated.assert_called_once_with("C:/Projektid/P-1")
        self.assertEqual(button.item_data["filesPath"], "C:/Projektid/P-1")

    def test_empty_path_changes_nothing(self) -> None:
        self.guard.missing_requirements.return_value = []
        updated = Mock()
        self.generate(on_files_path_updated=updated)
        self.engine.generate_project_folder_from_template.call_args.kwargs["on_files_path_updated"]("  ")
        updated.assert_not_called()


class PreviewCase(CardCase):
    DIALOG = ""
    ACTION = ""

    def setUp(self) -> None:
        super().setUp()
        self.dialog_class = self.replace(self.DIALOG)

    def open(self, button) -> None:
        self.trigger(button, self.ACTION)

    def built(self) -> list:
        return [call.kwargs for call in self.dialog_class.call_args_list]

    def track(self) -> list:
        opened = []

        def build(**_options):
            dialog = Mock()
            opened.append(dialog)
            return dialog

        self.dialog_class.side_effect = build
        return opened

    def assert_preview_flow(self) -> None:
        opened = self.track()
        button = self.button()
        self.open(button)
        self.assertEqual(len(opened), 1)
        self.assertIs(self.built()[0]["lang_manager"], self.lang)
        self.assertEqual(self.built()[0]["item_data"]["id"], "7")
        self.assertIs(self.built()[0]["parent"], self.host)
        dialog = opened[0]
        dialog.setAttribute.assert_called_once_with(Qt.WA_DeleteOnClose, True)
        dialog.show.assert_called_once_with()
        dialog.raise_.assert_called_once_with()
        dialog.activateWindow.assert_called_once_with()

        # Open already: brought forward, not opened twice.
        dialog.isVisible.return_value = True
        dialog.raise_.reset_mock()
        self.open(button)
        self.assertEqual(len(opened), 1)
        dialog.showNormal.assert_called_once_with()
        dialog.raise_.assert_called_once_with()

        # Closed: the next click opens a new one.
        dialog.finished.connect.call_args.args[0](QDialog.Accepted)
        self.open(button)
        self.assertEqual(len(opened), 2)

    def assert_deleted_preview_is_replaced(self) -> None:
        opened = self.track()
        button = self.button()
        self.open(button)
        opened[0].isVisible.side_effect = RuntimeError("wrapped C/C++ object has been deleted")
        self.open(button)
        self.assertEqual(len(opened), 2)

    def assert_hidden_preview_is_replaced(self) -> None:
        opened = self.track()
        button = self.button()
        self.open(button)
        opened[0].isVisible.return_value = False
        self.open(button)
        self.assertEqual(len(opened), 2)
        opened[0].raise_.assert_called_once_with()


class ProjectPreviewTest(PreviewCase):
    MODULE = "project"
    DIALOG = "ProjectPreviewDialog"
    ACTION = TranslationKeys.PROJECT_PREVIEW_ACTION

    def test_preview_opens_once_and_again_after_closing(self) -> None:
        self.assert_preview_flow()

    def test_deleted_preview_is_replaced(self) -> None:
        self.assert_deleted_preview_is_replaced()

    def test_hidden_preview_is_replaced(self) -> None:
        self.assert_hidden_preview_is_replaced()


class EasementPreviewTest(PreviewCase):
    MODULE = "easement"
    DIALOG = "EasementPreviewDialog"
    ACTION = TranslationKeys.EASEMENT_PREVIEW_ACTION

    def test_preview_opens_once_and_again_after_closing(self) -> None:
        self.assert_preview_flow()

    def test_deleted_preview_is_replaced(self) -> None:
        self.assert_deleted_preview_is_replaced()

    def test_hidden_preview_is_replaced(self) -> None:
        self.assert_hidden_preview_is_replaced()

    def test_preview_reports_status_changes_to_the_card(self) -> None:
        self.track()
        button = self.button()
        self.open(button)
        report = self.built()[0]["on_status_changed"]
        report({"id": "2", "name": "Allkirjastatud"})
        self.assertEqual(button.item_data["status"], {"id": "2", "name": "Allkirjastatud"})


class DrawOnMapCase(CardCase):
    CONTROLLER = ""
    ACTION = ""

    def assert_draw_flow(self) -> None:
        controller_class = self.replace(self.CONTROLLER)
        button = self.button()
        self.trigger(button, self.ACTION)
        self.trigger(button, self.ACTION)
        controller_class.assert_called_once_with(lang_manager=self.lang)
        draw = controller_class.return_value.start_draw
        self.assertEqual(draw.call_count, 2)
        self.assertEqual(draw.call_args.kwargs["item_data"]["id"], "7")

    def assert_nothing_without_an_id(self) -> None:
        controller_class = self.replace(self.CONTROLLER)
        self.trigger(self.button(item=NO_ID), self.ACTION)
        controller_class.assert_not_called()


class ProjectDrawTest(DrawOnMapCase):
    MODULE = "project"
    CONTROLLER = "ProjectsFeatureMapController"
    ACTION = TranslationKeys.PROJECT_DRAW_NEW_ACTION

    def test_controller_is_kept_and_started(self) -> None:
        self.assert_draw_flow()

    def test_item_without_an_id_starts_nothing(self) -> None:
        self.assert_nothing_without_an_id()


class AsBuiltDrawTest(DrawOnMapCase):
    MODULE = "asbuilt"
    CONTROLLER = "AsBuiltFeatureMapController"
    ACTION = TranslationKeys.ASBUILT_DRAW_NEW_ACTION

    def test_controller_is_kept_and_started(self) -> None:
        self.assert_draw_flow()

    def test_item_without_an_id_starts_nothing(self) -> None:
        self.assert_nothing_without_an_id()


class AsBuiltNotesMenuTest(CardCase):
    MODULE = "asbuilt"

    def test_menu_opens_the_notes_of_this_item_over_the_plugin_window(self) -> None:
        api = self.replace("APIModuleActions")
        dialog_class = self.replace("AsBuiltNotesEditorDialog")
        self.replace("AsBuiltNotesService").parse_notes.return_value = ["märge"]
        api.get_task_description.return_value = "<p>kirjeldus</p>"
        dialog_class.return_value.exec_.return_value = QDialog.Rejected

        self.trigger(self.button(), TranslationKeys.ASBUILT_UPDATE_NOTES_ACTION)

        api.get_task_description.assert_called_once_with("7")
        dialog_class.assert_called_once_with(item_name="Nimi", notes=["märge"], lang_manager=self.lang, parent=self.host)
        api.update_task_description.assert_not_called()


class EasementMapActionsTest(CardCase):
    MODULE = "easement"

    def setUp(self) -> None:
        super().setUp()
        self.controller_class = self.replace("EasementAttachExistingController")
        self.controller = self.controller_class.return_value

    def test_all_map_actions_share_one_controller_per_card(self) -> None:
        button = self.button()
        self.trigger(button, TranslationKeys.EASEMENT_DRAW_NEW_ACTION)
        self.trigger(button, TranslationKeys.EASEMENT_ATTACH_EXISTING_ACTION)
        self.trigger(button, TranslationKeys.EASEMENT_EDIT_GEOMETRY_ACTION)
        self.controller_class.assert_called_once()
        self.assertIs(self.controller_class.call_args.kwargs["lang_manager"], self.lang)

    def test_each_action_starts_its_flow_with_this_item(self) -> None:
        button = self.button()
        self.trigger(button, TranslationKeys.EASEMENT_DRAW_NEW_ACTION)
        self.assertEqual(self.controller.start_draw.call_args.kwargs["item_data"]["id"], "7")
        self.trigger(button, TranslationKeys.EASEMENT_ATTACH_EXISTING_ACTION)
        self.assertEqual(self.controller.start_attach.call_args.kwargs["item_data"]["id"], "7")
        self.assertIs(self.controller.start_attach.call_args.kwargs["parent_window"], self.host)
        self.trigger(button, TranslationKeys.EASEMENT_EDIT_GEOMETRY_ACTION)
        self.assertEqual(self.controller.start_edit.call_args.kwargs["item_data"]["id"], "7")

    def test_two_cards_do_not_share_a_controller(self) -> None:
        self.trigger(self.button(), TranslationKeys.EASEMENT_DRAW_NEW_ACTION)
        self.trigger(self.button(), TranslationKeys.EASEMENT_DRAW_NEW_ACTION)
        self.assertEqual(self.controller_class.call_count, 2)

    def test_status_from_the_flow_updates_this_card(self) -> None:
        button = self.button()
        self.trigger(button, TranslationKeys.EASEMENT_DRAW_NEW_ACTION)
        self.controller_class.call_args.kwargs["on_status_changed"]({"id": "2", "name": "Uus"})
        self.assertEqual(button.item_data["status"], {"id": "2", "name": "Uus"})

    def test_item_without_an_id_starts_nothing(self) -> None:
        button = self.button(item=NO_ID)
        for key in (TranslationKeys.EASEMENT_DRAW_NEW_ACTION, TranslationKeys.EASEMENT_ATTACH_EXISTING_ACTION,
                    TranslationKeys.EASEMENT_EDIT_GEOMETRY_ACTION):
            self.trigger(button, key)
        self.controller_class.assert_not_called()


class EasementFilesTest(CardCase):
    MODULE = "easement"
    PATH = "Kavitro_dev.widgets.DataDisplayWidgets.TaskFilesDialog.TaskFilesDialog"

    def test_files_open_for_this_item(self) -> None:
        with patch(self.PATH) as dialog_class:
            button = self.button()
            self.trigger(button, TranslationKeys.TASK_FILES_ACTION)
        dialog_class.assert_called_once_with(item_id="7", item_name="Nimi", module_name="easement",
                                             lang_manager=self.lang, parent=button.window())
        dialog_class.return_value.exec_.assert_called_once_with()

    def test_name_falls_back_to_the_id(self) -> None:
        with patch(self.PATH) as dialog_class:
            self.trigger(self.button(item={"id": "7"}), TranslationKeys.TASK_FILES_ACTION)
        self.assertEqual(dialog_class.call_args.kwargs["item_name"], "7")

    def test_item_without_an_id_opens_nothing(self) -> None:
        with patch(self.PATH) as dialog_class:
            self.trigger(self.button(item=NO_ID), TranslationKeys.TASK_FILES_ACTION)
        dialog_class.assert_not_called()


class WorksAddPointTest(CardCase):
    MODULE = "works"
    ACTION = TranslationKeys.WORKS_ADD_EXISTING_ON_MAP_ACTION

    def setUp(self) -> None:
        super().setUp()
        self.service = self.replace("WorksLayerService")
        self.messages = self.replace("ModernMessageDialog")
        self.controller_class = self.replace("WorksCreateController")
        self.layer = self.service.resolve_main_layer.return_value

    def test_without_a_layer_nothing_starts(self) -> None:
        self.service.resolve_main_layer.return_value = None
        self.trigger(self.button(), self.ACTION)
        self.service.resolve_main_layer.assert_called_once_with(lang_manager=self.lang, silent=False)
        self.service.find_feature_by_task_id.assert_not_called()
        self.controller_class.assert_not_called()

    def test_work_already_on_the_map_is_shown_instead(self) -> None:
        self.service.find_feature_by_task_id.return_value = object()
        self.trigger(self.button(), self.ACTION)
        self.service.find_feature_by_task_id.assert_called_once_with(self.layer, "7")
        self.service.focus_feature_by_task_id.assert_called_once_with(self.layer, "7")
        self.assertEqual(self.messages.show_info.call_args.args, (
            self.lang.translate(TranslationKeys.INFO),
            self.lang.translate(TranslationKeys.WORKS_ADD_EXISTING_ON_MAP_ALREADY_LINKED).format(task_id="7"),
        ))
        self.controller_class.assert_not_called()

    def test_new_point_starts_with_this_item_and_keeps_the_controller(self) -> None:
        self.service.find_feature_by_task_id.return_value = None
        button = self.button()
        self.trigger(button, self.ACTION)
        self.trigger(button, self.ACTION)
        self.controller_class.assert_called_once_with(lang_manager=self.lang)
        start = self.controller_class.return_value.start_add_existing_to_map
        self.assertEqual(start.call_count, 2)
        self.assertEqual(start.call_args.kwargs["task_id"], "7")
        self.assertEqual(start.call_args.kwargs["task_payload"]["id"], "7")
        self.assertIs(start.call_args.kwargs["parent_window"], self.host)

    def test_item_without_an_id_touches_nothing(self) -> None:
        self.trigger(self.button(item=NO_ID), self.ACTION)
        self.service.resolve_main_layer.assert_not_called()


class WorksRepositionTest(CardCase):
    MODULE = "works"
    ACTION = TranslationKeys.WORKS_REPOSITION_ACTION

    def test_reposition_starts_for_this_item_and_keeps_the_controller(self) -> None:
        controller_class = self.replace("WorksRepositionController")
        button = self.button()
        self.trigger(button, self.ACTION)
        self.trigger(button, self.ACTION)
        controller_class.assert_called_once_with(lang_manager=self.lang)
        start = controller_class.return_value.start_reposition
        self.assertEqual(start.call_count, 2)
        start.assert_called_with(task_id="7", parent_window=self.host)

    def test_item_without_an_id_starts_nothing(self) -> None:
        controller_class = self.replace("WorksRepositionController")
        self.trigger(self.button(item=NO_ID), self.ACTION)
        controller_class.assert_not_called()


class CardButtonIndependenceTest(unittest.TestCase):
    def test_the_button_imports_no_module(self) -> None:
        source = (Path(__file__).resolve().parents[1] / "widgets/DataDisplayWidgets/module_action_buttons.py").read_text(encoding="utf-8")
        imported = [node.module for node in ast.walk(ast.parse(source)) if isinstance(node, ast.ImportFrom) and node.module]
        self.assertEqual([name for name in imported if name.startswith("modules")], [])


if __name__ == "__main__":
    unittest.main()
