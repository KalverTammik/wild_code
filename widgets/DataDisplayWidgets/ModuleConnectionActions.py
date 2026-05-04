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
        self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Preferred)
        self._layout = QGridLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(4)
        self._compact = False

        folder_btn = None
        supports_folder_action = module_key not in (Module.ASBUILT.value, Module.WORKS.value)
        if supports_folder_action:
            file_path = DataDisplayExtractors.extract_files_path(item_data)
            folder_btn = OpenFolderActionButton(file_path, lang_manager)

        web_btn = OpenWebActionButton(module_key, item_id, lang_manager)

        has_connections = DataDisplayExtractors.extract_properties_connection_count(item_data)

        map_btn = ShowOnMapActionButton(
            module_key,
            item_id,
            lang_manager,
            has_connections=has_connections,
        )

        def _enable_map_button(refreshed_numbers: list[str]):
            if refreshed_numbers:
                map_btn.setEnabled(True)

        actions_btn = MoreActionsButton(
            lang_manager=lang_manager,
            item_data=item_data,
            module=module_key,
            on_properties_linked=_enable_map_button,
        )

        self._buttons = tuple(
            button for button in (folder_btn, web_btn, map_btn, actions_btn) if button is not None
        )
        self.setMinimumWidth(0)
        self._relayout_buttons()

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
