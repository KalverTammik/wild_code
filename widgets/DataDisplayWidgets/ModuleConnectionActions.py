from typing import Optional
from PyQt5.QtCore import QSize
from PyQt5.QtWidgets import QGridLayout, QWidget, QSizePolicy

from .module_action_buttons import (
    OpenFolderActionButton,
    OpenWebActionButton,
    ShowOnMapActionButton,
    MoreActionsButton
)
from ...python.responses import DataDisplayExtractors
from ...utils.url_manager import Module


class ModuleConnectionActions(QWidget):
    """Reusable strip of folder/web/map buttons for module connections."""

    def __init__(
        self,
        module_key: str,
        item_id: str,
        item_data: Optional[dict],
        lang_manager=None,
        parent: Optional[QWidget] = None,
    ):
        super().__init__(parent)
        module_key = str(module_key or "").strip().lower()
        action_payload = dict(item_data or {})
        if item_id and not action_payload.get("id"):
            action_payload["id"] = item_id
        self._action_payload = action_payload

        self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Preferred)
        self._layout = QGridLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(4)
        self._compact = False

        folder_btn = None
        supports_folder_action = module_key not in (Module.ASBUILT.value, Module.WORKS.value)
        if supports_folder_action:
            file_path = DataDisplayExtractors.extract_files_path(action_payload)
            folder_btn = OpenFolderActionButton(file_path, lang_manager)
        self._folder_button = folder_btn

        web_btn = OpenWebActionButton(module_key, item_id, lang_manager)

        has_connections = DataDisplayExtractors.extract_properties_connection_count(action_payload)

        map_btn = ShowOnMapActionButton(
            module_key,
            item_id,
            lang_manager,
            has_connections=has_connections,
        )
        self._map_button = map_btn

        actions_btn = MoreActionsButton(
            lang_manager=lang_manager,
            item_data=action_payload,
            module=module_key,
            on_properties_linked=self.set_connected_properties,
            on_files_path_updated=self.set_files_path,
        )
        self._more_actions_button = actions_btn
        map_btn.set_link_properties_callback(actions_btn.start_property_linking)

        self._buttons = tuple(
            button for button in (folder_btn, web_btn, map_btn, actions_btn) if button is not None
        )
        self.setMinimumWidth(0)
        self._relayout_buttons()

    def set_files_path(self, files_path: str) -> None:
        """Update only this card's local folder action after a verified mutation."""
        resolved_path = str(files_path or "").strip()
        if not resolved_path:
            return
        self._action_payload["filesPath"] = resolved_path
        if self._folder_button is not None:
            self._folder_button.set_file_path(resolved_path)

    def set_connected_properties(self, property_numbers: list[str]) -> None:
        """Switch only this card from linking mode to map-display mode."""
        self._map_button.set_connection_count(len(property_numbers or []))

    def _clear_layout(self):
        while self._layout.count():
            item = self._layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                self._layout.removeWidget(widget)

    def _relayout_buttons(self):
        self._clear_layout()
        if self._compact:
            for index, button in enumerate(self._buttons):
                row = index // 2
                column = index % 2
                self._layout.addWidget(button, row, column)
        else:
            for index, button in enumerate(self._buttons):
                self._layout.addWidget(button, 0, index)

    def set_compact(self, compact: bool):
        if compact == self._compact:
            return
        self._compact = compact
        self._layout.setSpacing(2 if compact else 4)
        icon_size = QSize(12, 12) if compact else QSize(14, 14)
        for button in self._buttons:
            button.setFixedSize(20, 18) if compact else button.setFixedSize(22, 20)
            button.setIconSize(icon_size)
        self._relayout_buttons()
        self.updateGeometry()

    @property
    def buttons(self):
        """Expose the created action buttons for optional external tweaks."""
        return self._buttons
