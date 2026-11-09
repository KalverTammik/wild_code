"""What a project card's menu offers."""
from __future__ import annotations

from typing import Optional

from PyQt5.QtCore import Qt

from ...constants.settings_keys import SettingsService
from ...languages.translation_keys import ToolbarTranslationKeys, TranslationKeys
from ...python.responses import DataDisplayExtractors
from ...utils.Folders.foldersHelpers import FolderEngines
from ...utils.messagesHelper import ModernMessageDialog
from ...utils.moduleSwitchHelper import ModuleSwitchHelper
from ...utils.url_manager import Module
from ..Settings.setting_keys import SettingDialogPlaceholders
from ..Settings.settings_setup_guard import SettingsSetupGuard
from .project_preview_dialog import ProjectPreviewDialog
from .projects_feature_map_controller import ProjectsFeatureMapController


class ProjectCardActions:
    """One per card button, so that a running map tool or an open preview lives as long as its card."""

    def __init__(self, host) -> None:
        self._host = host
        self._map_controller: Optional[ProjectsFeatureMapController] = None
        self._preview_dialog: Optional[ProjectPreviewDialog] = None

    def menu_actions(self) -> list:
        return [
            (ToolbarTranslationKeys.GENERATE_PROJECT_FOLDER, self.generate_folder),
            (TranslationKeys.PROJECT_PREVIEW_ACTION, self.open_preview),
            (TranslationKeys.PROJECT_DRAW_NEW_ACTION, self.draw_new_area_on_map),
        ]

    def generate_folder(self) -> None:
        host = self._host
        module = Module.PROJECT.value
        if SettingsSetupGuard.missing_requirements(module):
            title, message = SettingsSetupGuard.redirect_warning_text(host.lang_manager, module)
            ModernMessageDialog.show_warning(title, message, parent=host.safe_parent_window())
            ModuleSwitchHelper.switch_module(Module.SETTINGS.name, focus_module=module)
            return

        settings = SettingsService()
        item = host.item_data
        FolderEngines.generate_project_folder_from_template(
            DataDisplayExtractors.extract_item_id(item),
            DataDisplayExtractors.extract_item_name(item),
            DataDisplayExtractors.extract_project_number(item),
            source_folder=settings.module_label_value(module, SettingDialogPlaceholders.PROJECTS_SOURCE_FOLDER),
            target_folder=settings.module_label_value(module, SettingDialogPlaceholders.PROJECTS_TARGET_FOLDER),
            on_files_path_updated=host.update_files_path,
        )

    def open_preview(self) -> None:
        if self._preview_dialog is not None:
            try:
                if self._preview_dialog.isVisible():
                    self._preview_dialog.showNormal()
                    self._preview_dialog.raise_()
                    self._preview_dialog.activateWindow()
                    return
            except Exception:
                self._preview_dialog = None

        dialog = ProjectPreviewDialog(
            item_data=self._host.item_data,
            lang_manager=self._host.lang_manager,
            parent=self._host.safe_parent_window(),
        )
        dialog.setAttribute(Qt.WA_DeleteOnClose, True)
        dialog.finished.connect(self._forget_preview)
        self._preview_dialog = dialog
        dialog.show()
        dialog.raise_()
        dialog.activateWindow()

    def _forget_preview(self, *_args) -> None:
        self._preview_dialog = None

    def draw_new_area_on_map(self) -> None:
        item = self._host.item_data
        if not DataDisplayExtractors.extract_item_id(item):
            return

        if self._map_controller is None:
            self._map_controller = ProjectsFeatureMapController(lang_manager=self._host.lang_manager)

        self._map_controller.start_draw(item_data=item)
