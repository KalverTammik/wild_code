from __future__ import annotations

import subprocess
from typing import Optional

from PyQt5.QtCore import QSize
from PyQt5.QtWidgets import QPushButton

from ...languages.translation_keys import ToolbarTranslationKeys
from ...utils.url_manager import OpenLink, loadWebpage
from ...python.api_actions import APIModuleActions
from ...utils.MapTools.item_selector_tools import PropertiesSelectors
from ..theme_manager import ThemeManager


def _resolve_tooltip(lang_manager, key: str) -> str:
    if lang_manager and hasattr(lang_manager, "translate"):
        try:
            return lang_manager.translate(key)
        except Exception:
            pass
    return key


def open_item_folder(file_path: Optional[str]) -> None:
    if not file_path:
        return
    target = file_path.replace("/", "\\")
    try:
        if target.lower().startswith("http"):
            subprocess.Popen(["start", "", target], shell=True)
        else:
            subprocess.Popen(["explorer", target], shell=True)
    except Exception:
        pass


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
        PropertiesSelectors.show_connected_properties_on_map(numbers)


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
            ThemeManager.ICON_FOLDER,
            ToolbarTranslationKeys.OPEN_FOLDER,
            lang_manager,
        )
        enabled = bool(file_path)
        self.setEnabled(enabled)
        if enabled:
            self.clicked.connect(lambda _, path=file_path: open_item_folder(path))


class OpenWebActionButton(CardActionButton):
    def __init__(self, module_name: Optional[str], item_id: Optional[str], lang_manager) -> None:
        super().__init__(
            "OpenWebpageButton",
            ThemeManager.VALISEE_V_ICON_NAME,
            ToolbarTranslationKeys.OPEN_ITEM_IN_BROWSER,
            lang_manager,
        )
        enabled = bool(module_name and item_id)
        self.setEnabled(enabled)
        if enabled:
            self.clicked.connect(
                lambda _, module=module_name, mid=item_id: open_item_in_browser(module, mid)
            )


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
            ThemeManager.ICON_SHOW_ON_MAP,
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
