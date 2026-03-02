# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import List, Optional

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QLabel, QFrame, QSizePolicy, QVBoxLayout, QWidget

from ...feed.FeedLogic import UnifiedFeedLogic as FeedLogic
from ...module_manager import ModuleManager
from ...modules.Settings.SettinsUtils.SettingsLogic import SettingsLogic
from ...ui.ModuleBaseUI import ModuleBaseUI
from ...utils.FilterHelpers.FilterHelper import FilterHelper, FilterRefreshService
from ...utils.search.SearchOpenItemMixin import SearchOpenItemMixin
from ...utils.url_manager import Module, ModuleSupports
from ...widgets.Filters.StatusFilterWidget import StatusFilterWidget
from ...widgets.Filters.TypeFilterWidget import TypeFilterWidget
from ...widgets.Filters.filter_refresh_helper import FilterRefreshHelper
from ...widgets.theme_manager import ThemeManager, styleExtras
from ...constants.file_paths import QssPaths
from ...Logs.python_fail_logger import PythonFailLogger


class TaskModuleBaseUI(SearchOpenItemMixin, ModuleBaseUI):
    FEED_LOGIC_CLS = FeedLogic
    QUERY_FILE = "ListFilteredTasks.graphql"
    SINGLE_ITEM_QUERY_FILE = "w_tasks_module_data_by_item_id.graphql"

    def __init__(
        self,
        *,
        module_enum: Module,
        empty_state_key: str,
        lang_manager: Optional[object] = None,
        parent: Optional[QWidget] = None,
        qss_files: Optional[List[str]] = None,
    ) -> None:
        super().__init__(parent)
        self.module_key = module_enum.value
        self.setObjectName(self.module_key)

        self.lang_manager = lang_manager
        self.theme_manager = ThemeManager()
        self._settings_logic = SettingsLogic()
        self.qss_files = qss_files

        types, statuses, _tags, _archive = ModuleManager().getModuleSupports(module_enum.name) or {}
        self.supports_status_filter = bool(statuses)
        self.supports_type_filter = bool(types)
        self.supports_tags_filter = False

        self.status_filter = None
        if self.supports_status_filter:
            self.status_filter = StatusFilterWidget(self.module_key, self.toolbar_area, auto_load=False)
            self.toolbar_area.add_left(self.status_filter)
            self.status_filter.selectionChanged.connect(self._on_status_filter_selection)

        self.type_filter = None
        if self.supports_type_filter:
            self.type_filter = TypeFilterWidget(self.module_key, self.toolbar_area, auto_load=False)
            self.toolbar_area.add_left(self.type_filter)
            self.type_filter.selectionChanged.connect(self._on_type_filter_selection)

        self._filter_widgets = [w for w in (self.status_filter, self.type_filter) if w is not None]

        self._refresh_helper = FilterRefreshHelper(self)
        refresh_widget = self._refresh_helper.make_filter_refresh_button(self.toolbar_area)
        self.toolbar_area.set_refresh_widget(refresh_widget)

        self.feed_content = QWidget()
        self.feed_content.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        self.feed_layout = QVBoxLayout(self.feed_content)
        self.feed_layout.setContentsMargins(0, 0, 0, 0)
        self.feed_layout.setSpacing(6)

        self._empty_state = QLabel(self.lang_manager.translate(empty_state_key))
        self._empty_state.setAlignment(Qt.AlignCenter)
        self._empty_state.setVisible(False)
        self.feed_layout.addWidget(self._empty_state)
        self.feed_layout.addStretch(1)

        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setWidget(self.feed_content)

        self.feed_logic = self.FEED_LOGIC_CLS(Module.TASK.value, self.QUERY_FILE, self.lang_manager, root_field="tasks")
        self.feed_logic.configure_single_item_query(self.SINGLE_ITEM_QUERY_FILE)

        self.retheme()

    def on_first_visible(self) -> None:
        self._ensure_filters_loaded()
        self._refresh_filters()

    def deactivate(self) -> None:
        self._clear_filters()
        try:
            FilterHelper.cancel_pending_load(self.status_filter, invalidate_request=True)
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module=self.module_key,
                event="task_module_cancel_status_filter_failed",
            )
        try:
            FilterHelper.cancel_pending_load(self.type_filter, invalidate_request=True)
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module=self.module_key,
                event="task_module_cancel_type_filter_failed",
            )
        super().deactivate()

    def _ensure_filters_loaded(self) -> None:
        for widget in self._filter_widgets:
            ensure_loaded = getattr(widget, "ensure_loaded", None)
            if callable(ensure_loaded):
                try:
                    ensure_loaded()
                except Exception as exc:
                    PythonFailLogger.log_exception(
                        exc,
                        module=self.module_key,
                        event="task_module_filter_load_failed",
                    )

    def _clear_filters(self) -> None:
        for widget in self._filter_widgets:
            clear_data = getattr(widget, "clear_data", None)
            if callable(clear_data):
                try:
                    clear_data()
                except Exception as exc:
                    PythonFailLogger.log_exception(
                        exc,
                        module=self.module_key,
                        event="task_module_filter_clear_failed",
                    )

    def _module_scope_type_ids(self) -> List[str]:
        ids = self._settings_logic.load_module_preference_ids(
            self.module_key,
            support_key=ModuleSupports.TYPES.value,
        )
        return [str(item_id) for item_id in (ids or []) if item_id]

    def _effective_type_ids(self, type_ids: Optional[List[str]]) -> List[str]:
        scope_ids = self._module_scope_type_ids()
        selected_ids = [str(item_id) for item_id in (type_ids or []) if item_id]

        if not scope_ids:
            return selected_ids

        if selected_ids:
            scope_set = set(scope_ids)
            return [item_id for item_id in selected_ids if item_id in scope_set]

        return scope_ids

    def load_next_batch(self):
        return self.process_next_batch(retheme_func=self.retheme)

    def _on_status_filter_selection(self, _texts: List[str], ids: List[str]) -> None:
        self._refresh_filters(status_ids=ids)

    def _on_type_filter_selection(self, _texts: List[str], ids: List[str]) -> None:
        self._refresh_filters(type_ids=ids)

    def _refresh_filters(
        self,
        *,
        status_ids: Optional[List[str]] = None,
        type_ids: Optional[List[str]] = None,
    ) -> None:
        effective_type_ids = self._effective_type_ids(type_ids)
        FilterRefreshService.refresh_filters(
            self,
            status_ids=status_ids,
            type_ids=effective_type_ids,
            tags_ids=None,
            status_filter=self.status_filter,
            type_filter=self.type_filter,
            tags_filter=None,
        )

    def retheme(self) -> None:
        for card in self.scroll_area.findChildren(QFrame, "ModuleInfoCard"):
            ThemeManager.apply_module_style(card, [QssPaths.MODULE_CARD])
            styleExtras.apply_chip_shadow(card)

    def get_widget(self) -> QWidget:
        return self
