"""A list module's toolbar filters, feed area and their loading and shutdown."""
from __future__ import annotations

from typing import List, Optional

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QLabel, QSizePolicy, QVBoxLayout, QWidget

from ...Logs.python_fail_logger import PythonFailLogger
from ...module_manager import ModuleManager
from ...utils.FilterHelpers.FilterHelper import FilterHelper, FilterRefreshService
from ...utils.url_manager import Module
from ...widgets.Filters.StatusFilterWidget import StatusFilterWidget
from ...widgets.Filters.TagsFilterWidget import TagsFilterWidget
from ...widgets.Filters.TypeFilterWidget import TypeFilterWidget
from ...widgets.Filters.filter_refresh_helper import FilterRefreshHelper


class FilteredFeedMixin:
    """For a list module on ModuleBaseUI; goes before it in the bases.

    The module calls `_init_feed_module` and then `_build_filters_and_feed` from `__init__` and names its log events
    in `FILTER_EVENT_PREFIX`.
    """

    FILTER_EVENT_PREFIX: str

    def _init_feed_module(self, module: Module, lang_manager) -> None:
        self.module_key = module.value
        self.setObjectName(self.module_key)
        self.lang_manager = lang_manager

        types, statuses, tags, _archive = ModuleManager().getModuleSupports(module.name)
        self.supports_status_filter = bool(statuses)
        self.supports_type_filter = bool(types)
        self.supports_tags_filter = bool(tags)

    def _build_filters_and_feed(self, empty_state_key: str) -> None:
        if self.supports_status_filter:
            self.status_filter = StatusFilterWidget(self.module_key, self.toolbar_area, auto_load=False)
            self.toolbar_area.add_left(self.status_filter)
            self.status_filter.selectionChanged.connect(self._on_status_filter_selection)

        if self.supports_type_filter:
            self.type_filter = TypeFilterWidget(self.module_key, self.toolbar_area, auto_load=False)
            self.toolbar_area.add_left(self.type_filter)
            self.type_filter.selectionChanged.connect(self._on_type_filter_selection)

        if self.supports_tags_filter:
            self.tags_filter = TagsFilterWidget(self.module_key, self.lang_manager, self.toolbar_area, auto_load=False)
            self.toolbar_area.add_left(self.tags_filter)
            self.tags_filter.selectionChanged.connect(self._on_tags_filter_selection)

        self._filter_widgets = [w for w in (self.status_filter, self.type_filter, self.tags_filter) if w is not None]

        self._refresh_helper = FilterRefreshHelper(self)
        refresh_widget = self._refresh_helper.make_filter_refresh_button(self.toolbar_area)
        self._filter_refresh_widget = refresh_widget
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

    def on_first_visible(self) -> None:
        self._ensure_filters_loaded()
        self._refresh_filters()

    def deactivate(self) -> None:
        self._clear_filters()
        # Filter worker threads must stop before the module goes, or QThread teardown crashes.
        for name, widget in (("status", self.status_filter), ("type", self.type_filter), ("tags", self.tags_filter)):
            try:
                FilterHelper.cancel_pending_load(widget, invalidate_request=True)
            except Exception as exc:
                PythonFailLogger.log_exception(
                    exc,
                    module=self.module_key,
                    event=f"{self.FILTER_EVENT_PREFIX}_cancel_{name}_filter_failed",
                )
        super().deactivate()

    def _ensure_filters_loaded(self) -> None:
        for widget in self._filter_widgets:
            try:
                widget.ensure_loaded()
            except Exception as exc:
                PythonFailLogger.log_exception(exc, module=self.module_key, event="filter_widget_load_failed")

    def _clear_filters(self) -> None:
        for widget in self._filter_widgets:
            try:
                widget.clear_data()
            except Exception as exc:
                PythonFailLogger.log_exception(exc, module=self.module_key, event="filter_widget_clear_failed")

    def load_next_batch(self):
        return self.process_next_batch()

    def _on_status_filter_selection(self, _texts: List[str], ids: List[str]) -> None:
        self._refresh_filters(status_ids=ids)

    def _on_type_filter_selection(self, _texts: List[str], ids: List[str]) -> None:
        self._refresh_filters(type_ids=ids)

    def _on_tags_filter_selection(self, _texts: List[str], ids: List[str]) -> None:
        self._refresh_filters(tags_ids=ids)

    def _refresh_filters(
        self,
        *,
        status_ids: Optional[List[str]] = None,
        type_ids: Optional[List[str]] = None,
        tags_ids: Optional[List[str]] = None,
    ) -> None:
        FilterRefreshService.refresh_filters(
            self,
            status_ids=status_ids,
            type_ids=type_ids,
            tags_ids=tags_ids,
            status_filter=self.status_filter,
            type_filter=self.type_filter,
            tags_filter=self.tags_filter,
        )
