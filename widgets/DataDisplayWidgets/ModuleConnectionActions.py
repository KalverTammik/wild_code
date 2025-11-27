from typing import Optional
from PyQt5.QtWidgets import QHBoxLayout, QWidget

from .module_action_buttons import (
    OpenFolderActionButton,
    OpenWebActionButton,
    ShowOnMapActionButton,
)


class ModuleConnectionActions(QWidget):
    """Reusable strip of folder/web/map buttons for module connections."""

    def __init__(
        self,
        module_key: str,
        item_id: str,
        file_path: Optional[str],
        has_connections: Optional[bool],
        lang_manager=None,
        parent: Optional[QWidget] = None,
    ):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        layout.addStretch(1)

        folder_btn = OpenFolderActionButton(file_path, lang_manager)
        layout.addWidget(folder_btn)

        web_btn = OpenWebActionButton(module_key, item_id, lang_manager)
        layout.addWidget(web_btn)

        map_btn = ShowOnMapActionButton(
            module_key,
            item_id,
            lang_manager,
            has_connections=has_connections,
        )
        layout.addWidget(map_btn)

        self._buttons = (folder_btn, web_btn, map_btn)

    @property
    def buttons(self):
        """Expose the created action buttons for optional external tweaks."""
        return self._buttons
