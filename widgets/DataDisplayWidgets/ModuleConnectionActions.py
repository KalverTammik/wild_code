from typing import Optional
from PyQt5.QtWidgets import QHBoxLayout, QWidget

from .module_action_buttons import (
    OpenFolderActionButton,
    OpenWebActionButton,
    ShowOnMapActionButton,
    MoreActionsButton
)


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
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        layout.addStretch(1)

        file_path = item_data.get('filesPath', '')

        folder_btn = OpenFolderActionButton(file_path, lang_manager)
        layout.addWidget(folder_btn)

        web_btn = OpenWebActionButton(module_key, item_id, lang_manager)
        layout.addWidget(web_btn)

        properties_conn = item_data.get('properties') or {}
        page_info = properties_conn.get('pageInfo') or {}
        has_connections = page_info.get('count') or page_info.get('total', 0)

        map_btn = ShowOnMapActionButton(
            module_key,
            item_id,
            lang_manager,
            has_connections=bool(has_connections),
        )
        layout.addWidget(map_btn)

        def _enable_map_button(refreshed_numbers: list[str]):
            if refreshed_numbers:
                map_btn.setEnabled(True)

        actions_btn = MoreActionsButton(
            lang_manager=lang_manager,
            item_data=item_data,
            module=module_key,
            on_properties_linked=_enable_map_button,
        )
        layout.addWidget(actions_btn)


        self._buttons = (folder_btn, web_btn, map_btn, actions_btn)

    @property
    def buttons(self):
        """Expose the created action buttons for optional external tweaks."""
        return self._buttons
