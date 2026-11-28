"""A list module's toolbar filters, feed area and their loading and shutdown."""
from __future__ import annotations

from typing import List, Optional

from qgis.PyQt.QtCore import Qt, QTimer, pyqtSlot
from qgis.PyQt.QtWidgets import QLabel, QSizePolicy, QVBoxLayout, QWidget

from ...Logs.python_fail_logger import PythonFailLogger
from ...module_manager import ModuleManager
from ...python.latest_request import LatestRequest
from ...utils.api_error_handling import user_message
from ...utils.SessionManager import SessionManager
from ...utils.FilterHelpers.due_filters import due_soon_conditions, overdue_conditions
from ...utils.FilterHelpers.FilterHelper import FilterHelper, FilterRefreshService
from ...constants.module_names import Module
from ...widgets.Filters.StatusFilterWidget import StatusFilterWidget
from ...widgets.Filters.TagsFilterWidget import TagsFilterWidget
from ...widgets.Filters.TypeFilterWidget import TypeFilterWidget
from ...widgets.Filters.filter_refresh_helper import FilterRefreshHelper
from ...widgets.home.dashboard_counts import SOURCES, Selection
from ...widgets.home.module_indicator import ModuleIndicator


class FilteredFeedMixin:
    """For a list module on ModuleBaseUI; goes before it in the bases.

    The module calls `_init_feed_module` and then `_build_filters_and_feed` from `__init__` and names its log events
    in `FILTER_EVENT_PREFIX`.
    """

    FILTER_EVENT_PREFIX: str
    _feed_request: Optional[LatestRequest] = None
    _feed_request_key = None

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
            self.status_filter = StatusFilterWidget(
                self.module_key, self.toolbar_area, auto_load=False,
            )
            self.toolbar_area.add_left(self.status_filter)
            self.status_filter.selectionChanged.connect(self._on_status_filter_selection)

        if self.supports_type_filter:
            self.type_filter = TypeFilterWidget(
                self.module_key, self.toolbar_area, auto_load=False,
            )
            self.toolbar_area.add_left(self.type_filter)
            self.type_filter.selectionChanged.connect(self._on_type_filter_selection)

        if self.supports_tags_filter:
            self.tags_filter = TagsFilterWidget(self.module_key, self.toolbar_area, auto_load=False)
            self.toolbar_area.add_left(self.tags_filter)
            self.tags_filter.selectionChanged.connect(self._on_tags_filter_selection)

        self._filter_widgets = [w for w in (self.status_filter, self.type_filter, self.tags_filter) if w is not None]

        self._refresh_helper = FilterRefreshHelper(self)
        refresh_widget = self._refresh_helper.make_filter_refresh_button(self.toolbar_area)
        self._filter_refresh_widget = refresh_widget
        self.toolbar_area.set_refresh_widget(refresh_widget)

        if self.module_key in SOURCES:
            self.module_indicator = ModuleIndicator(self.module_key, self.toolbar_area)
            self.module_indicator.dueClicked.connect(self._on_due_clicked)
            self.toolbar_area.set_indicator(self.module_indicator)

        self.feed_content = QWidget()
        self.feed_content.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        self.feed_layout = QVBoxLayout(self.feed_content)
        self.feed_layout.setContentsMargins(0, 0, 0, 0)
        self.feed_layout.setSpacing(6)

        self._empty_state = QLabel(self.lang_manager.translate(empty_state_key))
        self._empty_state.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._empty_state.setVisible(False)
        self.feed_layout.addWidget(self._empty_state)
        self.feed_layout.addStretch(1)

        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setWidget(self.feed_content)

    def on_first_visible(self) -> None:
        self._ensure_filters_loaded()
        self._refresh_filters()

    def deactivate(self) -> None:
        self._invalidate_feed_request()
        if self.module_indicator is not None:
            self.module_indicator.cancel()
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

    # --- Pages in a worker ---------------------------------------------------------------------
    # A GUI-thread request over 400 ms opens the modal wait window, which also stops the list from
    # scrolling; a page is fetched on a snapshot of the feed in a worker and accepted only while
    # the module, its token and the session are still the ones that asked.

    def load_next_batch(self):
        feed_logic = self.active_feed_logic
        if not self._activated or feed_logic is None:
            return []
        if feed_logic.is_loading or (not feed_logic.has_more and not feed_logic._single_item_mode):
            # No request is sent: the synchronous path shows the empty state and the counter.
            return self.process_next_batch()
        self._feed_request_key = (self._active_token, SessionManager.session_signature())
        snapshot = feed_logic.snapshot()
        feed_logic.is_loading = True
        if not self._compute_loaded_cards():
            self._show_loading_placeholder()
        self._background_feed_request().submit(type(feed_logic).fetch_snapshot, snapshot)
        return []

    def _background_feed_request(self) -> LatestRequest:
        if self._feed_request is None:
            self._feed_request = LatestRequest(self)
            self._feed_request.finished.connect(self._on_feed_loaded)
            self._feed_request.error.connect(self._on_feed_failed)
        return self._feed_request

    def _invalidate_feed_request(self) -> None:
        if self._feed_request is not None:
            self._feed_request.invalidate()
        self._feed_request_key = None
        if self.feed_logic is not None:
            self.feed_logic.is_loading = False

    def _feed_request_is_current(self) -> bool:
        return self._activated and self._feed_request_key == (
            self._active_token, SessionManager.session_signature())

    @pyqtSlot(object)
    def _on_feed_loaded(self, result) -> None:
        if not self._feed_request_is_current():
            self._invalidate_feed_request()
            return
        snapshot, items = result
        feed_logic = self.active_feed_logic
        feed_logic.accept_snapshot(snapshot)
        token = self._active_token
        filtered = self.accept_batch_result(items or [])
        if self.feed_load_engine is not None:
            self.feed_load_engine.accept_batch(filtered, token=token)
        if not feed_logic.last_error_message:
            QTimer.singleShot(0, self._initial_autofill_tick)

    @pyqtSlot(str)
    def _on_feed_failed(self, message: str) -> None:
        if not self._feed_request_is_current():
            self._invalidate_feed_request()
            return
        feed_logic = self.active_feed_logic
        feed_logic.is_loading = False
        feed_logic.last_error_message = user_message(message)
        self._show_empty_state(feed_logic.last_error_message)

    def clear_feed(self, feed_layout, empty_state=None) -> None:
        self._invalidate_feed_request()
        super().clear_feed(feed_layout, empty_state)

    def reset_feed_session(self) -> None:
        self._invalidate_feed_request()
        super().reset_feed_session()

    # --- The indicator: counts what the filters leave, and filters the list by due date --------
    def _module_scope(self) -> Selection:
        """What narrows the module's whole data, whatever the filters say."""
        return Selection()

    def on_filters_applied(self, conditions: list, where_has) -> None:
        if self.module_indicator is not None:
            self.module_indicator.show_selection(Selection(tuple(conditions), where_has), self._module_scope())

    def _on_due_clicked(self, whole: bool, overdue: bool) -> None:
        """Show the records of the clicked number; the same number again returns to the filters."""
        indicator = self.module_indicator
        if indicator.active() == (whole, overdue):
            self._refresh_filters()
            return
        selection = indicator.whole if whole else indicator.shown
        due = overdue_conditions() if overdue else due_soon_conditions()
        engine = self.feed_load_engine
        if engine is not None:
            engine.buffer.clear()
        feed_logic = self.feed_logic
        feed_logic.set_single_item_mode(False)
        feed_logic.set_where({"AND": [*selection.conditions, *due]})
        feed_logic.set_extra_arguments(whereHas=selection.where_has)
        self.clear_feed(self.feed_layout, self._empty_state)
        self.scroll_area.verticalScrollBar().setValue(0)
        indicator.set_active((whole, overdue))
        if engine is not None:
            engine.schedule_load()

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
