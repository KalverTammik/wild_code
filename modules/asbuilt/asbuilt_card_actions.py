"""What an as-built card's menu offers."""
from __future__ import annotations

from typing import Optional

from PyQt5.QtWidgets import QDialog

from ...languages.translation_keys import TranslationKeys
from ...python.api_actions import APIModuleActions
from ...python.responses import DataDisplayExtractors
from ...utils.messagesHelper import ModernMessageDialog
from .asbuilt_feature_map_controller import AsBuiltFeatureMapController
from .asbuilt_notes_dialog import AsBuiltNotesEditorDialog
from .asbuilt_notes_service import AsBuiltNotesService


class AsBuiltCardActions:
    """One per card button, so that a running map tool lives as long as its card."""

    def __init__(self, host) -> None:
        self._host = host
        self._map_controller: Optional[AsBuiltFeatureMapController] = None

    def menu_actions(self) -> list:
        return [
            (TranslationKeys.ASBUILT_UPDATE_NOTES_ACTION, self.edit_notes),
            (TranslationKeys.ASBUILT_DRAW_NEW_ACTION, self.draw_new_on_map),
        ]

    def edit_notes(self) -> None:
        lm = self._host.lang_manager
        item = self._host.item_data

        item_id = DataDisplayExtractors.extract_item_id(item)
        if not item_id:
            return

        item_name = DataDisplayExtractors.extract_item_name(item) or item_id
        source_description = APIModuleActions.get_task_description(item_id)
        if source_description is None:
            # Without the current description a save would replace all of it with the notes table.
            ModernMessageDialog.show_warning(
                lm.translate(TranslationKeys.ERROR),
                lm.translate(TranslationKeys.ASBUILT_NOTES_LOAD_FAILED).format(name=item_name),
            )
            return

        dialog = AsBuiltNotesEditorDialog(
            item_name=item_name,
            notes=AsBuiltNotesService.parse_notes(source_description),
            lang_manager=lm,
            parent=self._host.safe_parent_window(),
        )
        if dialog.exec_() != QDialog.Accepted:
            return

        latest_description = APIModuleActions.get_task_description(item_id)
        base_description = latest_description if latest_description is not None else source_description
        merged_description = AsBuiltNotesService.merge_notes_into_description(
            base_description,
            dialog.get_notes(),
        )

        if merged_description == (base_description or ""):
            return

        success = APIModuleActions.update_task_description(item_id, merged_description)
        if success:
            item["description"] = merged_description
            ModernMessageDialog.show_info(
                lm.translate(TranslationKeys.SUCCESS),
                lm.translate(TranslationKeys.ASBUILT_UPDATE_NOTES_SUCCESS).format(name=item_name),
            )
            return

        ModernMessageDialog.show_warning(
            lm.translate(TranslationKeys.ERROR),
            lm.translate(TranslationKeys.ASBUILT_UPDATE_NOTES_FAILED).format(name=item_name),
        )

    def draw_new_on_map(self) -> None:
        item = self._host.item_data
        if not DataDisplayExtractors.extract_item_id(item):
            return

        if self._map_controller is None:
            self._map_controller = AsBuiltFeatureMapController(lang_manager=self._host.lang_manager)

        self._map_controller.start_draw(item_data=item)
