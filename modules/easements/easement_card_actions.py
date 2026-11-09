"""What an easement card's menu offers."""
from __future__ import annotations

from typing import Optional

from PyQt5.QtCore import Qt

from ...languages.translation_keys import TranslationKeys
from ...python.responses import DataDisplayExtractors
from ...utils.url_manager import Module
from .easement_attach_existing_controller import EasementAttachExistingController
from .easement_preview_dialog import EasementPreviewDialog


class EasementCardActions:
    """One per card button, so that a running map tool or an open preview lives as long as its card."""

    def __init__(self, host) -> None:
        self._host = host
        self._map_controller: Optional[EasementAttachExistingController] = None
        self._preview_dialog: Optional[EasementPreviewDialog] = None

    def menu_actions(self) -> list:
        return [
            (TranslationKeys.TASK_FILES_ACTION, self.open_files),
            (TranslationKeys.EASEMENT_DRAW_NEW_ACTION, self.draw_new_on_map),
            (TranslationKeys.EASEMENT_ATTACH_EXISTING_ACTION, self.attach_existing_on_map),
            (TranslationKeys.EASEMENT_EDIT_GEOMETRY_ACTION, self.edit_geometry_on_map),
            (TranslationKeys.EASEMENT_PREVIEW_ACTION, self.open_preview),
        ]

    def open_files(self) -> None:
        from ...widgets.DataDisplayWidgets.TaskFilesDialog import TaskFilesDialog

        item = self._host.item_data
        item_id = DataDisplayExtractors.extract_item_id(item)
        if not item_id:
            return
        dialog = TaskFilesDialog(
            item_id=item_id,
            item_name=DataDisplayExtractors.extract_item_name(item) or item_id,
            module_name=Module.EASEMENT.value,
            lang_manager=self._host.lang_manager,
            parent=self._host.window(),
        )
        dialog.exec_()

    def _controller_for_item(self) -> Optional[EasementAttachExistingController]:
        if not DataDisplayExtractors.extract_item_id(self._host.item_data):
            return None
        if self._map_controller is None:
            self._map_controller = EasementAttachExistingController(
                lang_manager=self._host.lang_manager,
                on_status_changed=self._host.apply_item_status,
            )
        return self._map_controller

    def attach_existing_on_map(self) -> None:
        controller = self._controller_for_item()
        if controller is not None:
            controller.start_attach(item_data=self._host.item_data, parent_window=self._host.safe_parent_window())

    def draw_new_on_map(self) -> None:
        controller = self._controller_for_item()
        if controller is not None:
            controller.start_draw(item_data=self._host.item_data)

    def edit_geometry_on_map(self) -> None:
        controller = self._controller_for_item()
        if controller is not None:
            controller.start_edit(item_data=self._host.item_data)

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

        dialog = EasementPreviewDialog(
            item_data=self._host.item_data,
            lang_manager=self._host.lang_manager,
            parent=self._host.safe_parent_window(),
            on_status_changed=self._host.apply_item_status,
        )
        dialog.setAttribute(Qt.WA_DeleteOnClose, True)
        dialog.finished.connect(self._forget_preview)
        self._preview_dialog = dialog
        dialog.show()
        dialog.raise_()
        dialog.activateWindow()

    def _forget_preview(self, *_args) -> None:
        self._preview_dialog = None
