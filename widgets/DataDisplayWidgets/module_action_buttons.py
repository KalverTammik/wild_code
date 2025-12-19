from __future__ import annotations

import subprocess
from typing import Optional

from PyQt5.QtCore import QSize
from PyQt5.QtWidgets import QPushButton

from ...languages.translation_keys import ToolbarTranslationKeys
from ...utils.url_manager import OpenLink, loadWebpage, Module
from ...python.api_actions import APIModuleActions
from ...utils.MapTools.item_selector_tools import PropertiesSelectors
from ..theme_manager import ThemeManager
from ...utils.Folders.foldersHelpers import FolderHelpers, FolderEngines
from PyQt5.QtWidgets import QMessageBox
from ...constants.settings_keys import SettingsService
from ...constants.module_icons import IconNames
from ...modules.Settings.setting_keys import SettingDialogPlaceholders
from ...utils.moduleSwitchHelper import ModuleSwitchHelper
def _resolve_tooltip(lang_manager, key: str) -> str:
    if lang_manager and hasattr(lang_manager, "translate"):
        try:
            return lang_manager.translate(key)
        except Exception:
            pass
    return key


from PyQt5.QtWidgets import QPushButton, QMenu, QAction

def more_actions(parent=None, lang_manager=None):
    btn = QPushButton("More Actions", parent)
    btn.setObjectName("MoreActionsButton")
    menu = QMenu(btn)
    action1 = QAction("Action 1", btn)
    action2 = QAction("Action 2", btn)
    menu.addAction(action1)
    menu.addAction(action2)
    btn.setMenu(menu)
    return btn


def open_item_in_browser(module_name: Optional[str], item_id: Optional[str]) -> None:
    if not module_name or not item_id:
        return
    try:
        wl = OpenLink()
        base = wl.weblink_by_module(module_name)
        if not base:
            return
        base = base.rstrip("/")
        if not base.endswith("s"):
            base = f"{base}s"
        url = f"{base}/{item_id}"
        loadWebpage.open_webpage(url)
    except Exception:
        pass


def show_items_on_map(module_name: Optional[str], item_id: Optional[str]) -> None:
    if not module_name or not item_id:
        return
    numbers = APIModuleActions.get_module_item_connected_properties(module_name, item_id)
    if numbers:
        PropertiesSelectors.show_connected_properties_on_map(numbers, module=module_name)


class CardActionButton(QPushButton):
    def __init__(
        self,
        object_name: str,
        icon_name: Optional[str],
        tooltip_key: Optional[str],
        lang_manager,
    ) -> None:
        super().__init__("")
        self.setObjectName(object_name)
        self.setAutoDefault(False)
        self.setDefault(False)
        self.setFixedSize(22, 20)
        self.setIconSize(QSize(14, 14))
        if icon_name:
            self.setIcon(ThemeManager.get_qicon(icon_name))
        if tooltip_key:
            self.setToolTip(_resolve_tooltip(lang_manager, tooltip_key))


class OpenFolderActionButton(CardActionButton):
    def __init__(self, file_path: Optional[str], lang_manager) -> None:
        super().__init__(
            "OpenFolderButton",
            IconNames.ICON_FOLDERICON,
            ToolbarTranslationKeys.OPEN_FOLDER,
            lang_manager,
        )
        enabled = bool(file_path)
        self.setEnabled(enabled)
        if enabled:
            self.clicked.connect(lambda _, path=file_path: FolderHelpers.open_item_folder(path))


class OpenWebActionButton(CardActionButton):
    def __init__(self, module_name: Optional[str], item_id: Optional[str], lang_manager) -> None:
        super().__init__(
            "OpenWebpageButton",
            IconNames.VALISEE_V_ICON_NAME,
            ToolbarTranslationKeys.OPEN_ITEM_IN_BROWSER,
            lang_manager,
        )
        enabled = bool(module_name and item_id)
        self.setEnabled(enabled)
        if enabled:
            self.clicked.connect(
                lambda _, module=module_name, mid=item_id: open_item_in_browser(module, mid)
            )


class MoreActionsButton(CardActionButton):
    def __init__(self, lang_manager=None, item_data=None, module=None) -> None:
        super().__init__(
            "MoreActionsButton",
            IconNames.ICON_ADD,
            ToolbarTranslationKeys.MORE_ACTIONS,
            lang_manager,
        )
        self._item_data = item_data
        self.module = module  # Ensure module is passed correctly

        menu = QMenu(self)

        if module == Module.PROJECT.value:
            action1 = QAction("Genereeri projecti kaust", self)
            action1.triggered.connect(self._generate_project_folder(module, item_data))
            menu.addAction(action1)

        action2 = QAction("Action 2", self)
        
        menu.addAction(action2)
        self.setMenu(menu)
    @staticmethod
    def _generate_project_folder(module, item_data):
        def handler(checked=False):            
            svc = SettingsService()
            folder_to_copy = svc.module_label_value(module, SettingDialogPlaceholders.PROJECTS_SOURCE_FOLDER)
            target_folder = svc.module_label_value(module, SettingDialogPlaceholders.PROJECTS_TARGET_FOLDER)
            if not folder_to_copy or not target_folder:
                QMessageBox.warning(
                    None,
                    "Action 1",
                    "Project folders are not set for this module. Opening Settings…",
                )

                ModuleSwitchHelper.switch_module(
                    Module.SETTINGS.name,
                    focus_module=module,
                )
                return
            FolderEngines.generate_project_folder_from_template(
                item_data.get("id"),
                item_data.get("name"),
                item_data.get("projectNumber"),
                source_folder=folder_to_copy,
                target_folder=target_folder,
            )

        return handler

class ShowOnMapActionButton(CardActionButton):
    def __init__(
        self,
        module_name: Optional[str],
        item_id: Optional[str],
        lang_manager,
        *,
        has_connections: Optional[bool] = None,
    ) -> None:
        super().__init__(
            "ShowOnMapButton",
            IconNames.ICON_SHOW_ON_MAP,
            ToolbarTranslationKeys.SHOW_ITEMS_ON_MAP,
            lang_manager,
        )
        can_execute = bool(module_name and item_id)
        if has_connections is False:
            can_execute = False
        self.setEnabled(can_execute)
        if can_execute:
            self.clicked.connect(
                lambda _, module=module_name, mid=item_id: show_items_on_map(module, mid)
            )
