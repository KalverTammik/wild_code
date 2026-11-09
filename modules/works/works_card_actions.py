"""What a work card's menu offers."""
from __future__ import annotations

from typing import Optional

from ...languages.translation_keys import TranslationKeys
from ...python.responses import DataDisplayExtractors
from ...utils.messagesHelper import ModernMessageDialog
from .works_create_controller import WorksCreateController
from .works_layer_service import WorksLayerService
from .works_reposition_controller import WorksRepositionController


class WorksCardActions:
    """One per card button, so that a running map tool lives as long as its card."""

    def __init__(self, host) -> None:
        self._host = host
        self._reposition_controller: Optional[WorksRepositionController] = None
        self._create_controller: Optional[WorksCreateController] = None

    def menu_actions(self) -> list:
        return [
            (TranslationKeys.WORKS_ADD_EXISTING_ON_MAP_ACTION, self.add_existing_point_on_map),
            (TranslationKeys.WORKS_REPOSITION_ACTION, self.reposition_on_map),
        ]

    def add_existing_point_on_map(self) -> None:
        lm = self._host.lang_manager
        item = self._host.item_data

        item_id = DataDisplayExtractors.extract_item_id(item)
        if not item_id:
            return

        works_layer = WorksLayerService.resolve_main_layer(lang_manager=lm, silent=False)
        if works_layer is None:
            return

        existing_feature = WorksLayerService.find_feature_by_task_id(works_layer, item_id)
        if existing_feature is not None:
            WorksLayerService.focus_feature_by_task_id(works_layer, item_id)
            ModernMessageDialog.show_info(
                lm.translate(TranslationKeys.INFO),
                lm.translate(TranslationKeys.WORKS_ADD_EXISTING_ON_MAP_ALREADY_LINKED).format(
                    task_id=item_id,
                ),
            )
            return

        if self._create_controller is None:
            self._create_controller = WorksCreateController(lang_manager=lm)

        self._create_controller.start_add_existing_to_map(
            task_id=item_id,
            task_payload=item,
            parent_window=self._host.safe_parent_window(),
        )

    def reposition_on_map(self) -> None:
        item_id = DataDisplayExtractors.extract_item_id(self._host.item_data)
        if not item_id:
            return

        if self._reposition_controller is None:
            self._reposition_controller = WorksRepositionController(lang_manager=self._host.lang_manager)

        self._reposition_controller.start_reposition(
            task_id=item_id,
            parent_window=self._host.safe_parent_window(),
        )
