# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import List, Optional

from PyQt5.QtWidgets import QPushButton
from PyQt5.QtWidgets import QWidget

from ..task_shared.task_module_base_ui import TaskModuleBaseUI
from ...constants.button_props import ButtonSize, ButtonVariant
from ...languages.translation_keys import TranslationKeys
from ...utils.url_manager import Module
from .works_create_controller import WorksCreateController
from .works_sync_service import WorksSyncService


class WorksModule(TaskModuleBaseUI):
    def __init__(
        self,
        name: Optional[str] = None,
        lang_manager: Optional[object] = None,
        parent: Optional[QWidget] = None,
        qss_files: Optional[List[str]] = None,
    ) -> None:
        super().__init__(
            module_enum=Module.WORKS,
            empty_state_key=TranslationKeys.NO_WORKS_FOUND,
            lang_manager=lang_manager,
            parent=parent,
            qss_files=qss_files,
        )

        self._create_controller = WorksCreateController(lang_manager=self.lang_manager)
        self._sync_service = WorksSyncService(lang_manager=self.lang_manager)
        self._create_on_map_button = QPushButton(
            self.lang_manager.translate(TranslationKeys.WORKS_CREATE_ON_MAP_BUTTON)
        )
        self._create_on_map_button.setObjectName("WorksCreateOnMapButton")
        self._create_on_map_button.setProperty("variant", ButtonVariant.PRIMARY)
        self._create_on_map_button.setProperty("btnSize", ButtonSize.SMALL)
        self._create_on_map_button.setAutoDefault(False)
        self._create_on_map_button.setDefault(False)
        self._create_on_map_button.clicked.connect(self._start_create_on_map)
        self.toolbar_area.add_right(self._create_on_map_button)

    def _start_create_on_map(self) -> None:
        self._create_controller.start_capture(
            parent_window=self.window(),
            allowed_type_ids=self._module_scope_type_ids(),
            on_created=lambda _task_id: self._refresh_filters(),
        )

    def on_first_visible(self) -> None:
        self._sync_service.attach()
        super().on_first_visible()

    def _on_status_filter_selection(self, _texts: List[str], ids: List[str]) -> None:
        TaskModuleBaseUI._refresh_filters(self, status_ids=ids)

    def _on_type_filter_selection(self, _texts: List[str], ids: List[str]) -> None:
        TaskModuleBaseUI._refresh_filters(self, type_ids=ids)

    def _refresh_filters(
        self,
        *,
        status_ids: Optional[List[str]] = None,
        type_ids: Optional[List[str]] = None,
        tags_ids: Optional[List[str]] = None,
    ) -> None:
        self._sync_service.attach()
        self._sync_service.sync_from_backend()
        TaskModuleBaseUI._refresh_filters(self, status_ids=status_ids, type_ids=type_ids)

    def deactivate(self) -> None:
        self._sync_service.detach()
        self._create_controller.cancel(bring_front=False)
        super().deactivate()
