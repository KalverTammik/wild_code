# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import List, Optional

from PyQt5.QtCore import Qt, QTimer, pyqtSlot
from PyQt5.QtWidgets import QLabel, QPushButton
from PyQt5.QtWidgets import QWidget
from qgis.core import QgsSettings

from ..task_shared.task_module_base_ui import TaskModuleBaseUI
from ...constants.button_props import ButtonSize, ButtonVariant
from ...languages.translation_keys import TranslationKeys
from ...utils.url_manager import Module
from .works_create_controller import WorksCreateController
from .works_sync_service import WorksSyncService
from .works_list_service import LOCAL_SORTS, REMOTE_SORTS, ListChoices, WorksFeedLogic, WorksListPreferences
from ...constants.file_paths import GraphQLSettings
from ...utils.SessionManager import SessionManager
from ...python.latest_request import LatestRequest
from ...widgets.works_list_widgets import WorksListControls, WorksListView


class WorksModule(TaskModuleBaseUI):
    FEED_LOGIC_CLS = WorksFeedLogic

    def __init__(
        self,
        name: Optional[str] = None,
        lang_manager: Optional[object] = None,
        parent: Optional[QWidget] = None,
        qss_files: Optional[List[str]] = None,
    ) -> None:
        self._list_view = None
        self._list_controls = None
        self._list_choices = ListChoices()
        self._list_preferences = None
        self._feed_request = None
        self._feed_request_key = None
        super().__init__(
            module_enum=Module.WORKS,
            empty_state_key=TranslationKeys.NO_WORKS_FOUND,
            lang_manager=lang_manager,
            parent=parent,
            qss_files=qss_files,
        )

        self._list_view = WorksListView(self)
        self._feed_request = LatestRequest(self)
        self._feed_request.finished.connect(self._on_feed_loaded)
        self._feed_request.error.connect(self._on_feed_failed)
        self._list_controls = WorksListControls(self.lang_manager, self.toolbar_area)
        self.toolbar_area.add_after_filters(self._list_controls)
        self._list_controls.choicesChanged.connect(self._on_list_choices_changed)
        self._list_controls.groupExpansionRequested.connect(self._list_view.set_groups_expanded)
        self._list_scope_label = QLabel(self.footer_area)
        self._list_scope_label.setObjectName("FeedListScope")
        self._list_scope_label.setTextFormat(Qt.PlainText)
        self._list_scope_label.setWordWrap(True)
        self.footer_area.layout().addWidget(self._list_scope_label, 1)
        self._list_view.changed.connect(self._on_list_presentation_changed)

        self._create_controller = WorksCreateController(lang_manager=self.lang_manager)
        self._sync_service = WorksSyncService(lang_manager=self.lang_manager, parent=self)
        self._create_on_map_button = QPushButton(
            self.lang_manager.translate(TranslationKeys.WORKS_CREATE_ON_MAP_BUTTON)
        )
        self._create_on_map_button.setObjectName("WorksCreateOnMapButton")
        self._create_on_map_button.setProperty("variant", ButtonVariant.PRIMARY)
        self._create_on_map_button.setProperty("btnSize", ButtonSize.SMALL)
        self._create_on_map_button.setAutoDefault(False)
        self._create_on_map_button.setDefault(False)
        self._create_on_map_button.style().unpolish(self._create_on_map_button)
        self._create_on_map_button.style().polish(self._create_on_map_button)
        self._create_on_map_button.clicked.connect(self.start_create_on_map)
        self.toolbar_area.add_right(self._create_on_map_button)

    def start_create_on_map(self) -> None:
        self._start_create_on_map()

    def review_pending_gis_works(self, *, progress_anchor=None) -> None:
        self._create_controller.review_pending_gis_features(
            parent_window=self.window(),
            allowed_type_ids=self._module_scope_type_ids(),
            on_created=lambda _task_id: self._refresh_filters(),
            progress_anchor=progress_anchor,
        )

    def _start_create_on_map(self) -> None:
        self._create_controller.preload_dialog_data()
        self._create_controller.start_capture(
            parent_window=self.window(),
            allowed_type_ids=self._module_scope_type_ids(),
            on_created=lambda _task_id: self._refresh_filters(),
        )

    def on_first_visible(self) -> None:
        session = SessionManager()
        user = session.loggedInUser
        user_id = (user.get("id") if isinstance(user, dict) else None) or session.get_username()
        self._list_preferences = WorksListPreferences(
            QgsSettings(), user_id=user_id, endpoint=GraphQLSettings.graphql_endpoint(), module_key=self.module_key,
        )
        self._list_choices = self._list_preferences.load()
        self.feed_logic.choices = self._list_choices
        self._list_controls.set_choices(self._list_choices)
        self._list_view.set_choices(self._list_choices)
        self._sync_service.attach()
        self._create_controller.preload_dialog_data()
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
        self._invalidate_feed_request()
        self._list_view.clear()
        self._sync_service.detach()
        self._create_controller.cancel(bring_front=False)
        super().deactivate()

    def _invalidate_feed_request(self):
        if self._feed_request is not None:
            self._feed_request.invalidate()
            self._feed_request_key = None
            self.feed_logic.is_loading = False

    def load_next_batch(self):
        if not self._activated or not self.feed_logic.has_more:
            return []
        key = (self._active_token, SessionManager.session_signature())
        if self._feed_request.busy and key == self._feed_request_key:
            return []
        self._feed_request_key = key
        snapshot = self.feed_logic.snapshot()
        self.feed_logic.is_loading = True
        if not self._compute_loaded_cards():
            self._show_loading_placeholder()
        self._feed_request.submit(WorksFeedLogic.fetch_snapshot, snapshot)
        return []

    def _feed_request_is_current(self):
        return self._activated and self._feed_request_key == (
            self._active_token, SessionManager.session_signature())

    @pyqtSlot(object)
    def _on_feed_loaded(self, result):
        if not self._feed_request_is_current():
            self._invalidate_feed_request()
            return
        snapshot, items = result
        self.feed_logic.accept_snapshot(snapshot)
        token = self._active_token
        filtered = self.accept_batch_result(items)
        self.feed_load_engine.accept_batch(filtered, token=token)
        if not self.feed_logic.last_error_message:
            QTimer.singleShot(0, self._initial_autofill_tick)

    @pyqtSlot(str)
    def _on_feed_failed(self, message):
        if not self._feed_request_is_current():
            self._invalidate_feed_request()
            return
        self.feed_logic.is_loading = False
        self.feed_logic.last_error_message = message
        self._show_empty_state(message)

    def _schedule_post_batch_updates(self):
        # Cards style themselves when constructed; do not restyle the entire feed per page.
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self._update_counter_snapshot()

    @staticmethod
    def _list_query_key(choices):
        if choices.sort in REMOTE_SORTS:
            return choices.sort, choices.descending
        return "local" if choices.sort in LOCAL_SORTS else "default", False

    def _on_list_choices_changed(self, choices):
        reload_required = self._list_query_key(choices) != self._list_query_key(self._list_choices)
        self._list_choices = choices
        self.feed_logic.choices = choices
        if self._list_preferences is not None:
            self._list_preferences.save(choices)
        if reload_required:
            self._reload_list_feed()
        self._list_view.set_choices(choices)

    def _reload_list_feed(self):
        self.bump_token()
        if self.feed_load_engine is not None:
            self.feed_load_engine.reset()
        self.feed_logic.reset_pagination()
        self.clear_feed(self.feed_layout, self.empty_state)
        self.scroll_area.verticalScrollBar().setValue(0)
        self._show_loading_placeholder()
        if self._activated and self.feed_load_engine is not None:
            self.feed_load_engine.schedule_load()

    def _on_list_item_updated(self, item):
        if str(item.get("id")) not in self._list_view.items:
            return
        if self._list_choices.sort in REMOTE_SORTS:
            self._reload_list_feed()
        else:
            self._list_view.update_item(item)

    def _progressive_insert_card(self, item, insert_at_top=False):
        self._list_view.add_item(item, insert_at_top=insert_at_top)

    def _compute_loaded_cards(self):
        if self._list_view is None:
            return super()._compute_loaded_cards()
        return len(self._list_view.items)

    def _on_list_presentation_changed(self):
        self._update_feed_counter_live()
        count = len(self._list_view.items)
        self.feed_counter.setToolTip(self.lang_manager.translate(TranslationKeys.LIST_UNIQUE_COUNT).format(count=count))
        messages = []
        if self._list_choices.sort in LOCAL_SORTS:
            messages.append(self.lang_manager.translate(TranslationKeys.LIST_LOCAL_NOTICE))
        if self._list_choices.group != "none":
            messages.append(self.lang_manager.translate(TranslationKeys.LIST_GROUP_NOTICE))
        self._list_scope_label.setText(" · ".join(messages))
        self._list_scope_label.setVisible(bool(messages))
        if count and not self.feed_logic.last_error_message:
            self._hide_loading_placeholder()
        QTimer.singleShot(0, self._initial_autofill_tick)

    def clear_feed(self, feed_layout, empty_state=None):
        self._invalidate_feed_request()
        if self._list_view is not None:
            self._list_view.clear()
        super().clear_feed(feed_layout, empty_state)

    def reset_feed_session(self):
        self._invalidate_feed_request()
        if self._list_view is not None:
            self._list_view.clear()
        super().reset_feed_session()

    def _is_filled_plus_one(self):
        if self._list_view is not None and self._list_view.all_collapsed:
            return True
        return super()._is_filled_plus_one()

    def _on_scroll_value(self, value):
        if self._list_view is not None and self._list_view.all_collapsed:
            return
        super()._on_scroll_value(value)

    def _initial_autofill_tick(self):
        self._autofill_ticks = 0
        if not self._activated or self._list_view is None or self._is_filled_plus_one():
            return
        engine = self.feed_load_engine
        if engine is None or self.feed_logic.last_error_message:
            return
        # Resume after a page or a render, never poll while a network request is pending.
        if self._list_view._render_timer.isActive():
            return
        if engine.has_buffer():
            engine.drip_from_buffer(max_cards=3)
        elif self.feed_logic.has_more and not self.feed_logic.is_loading:
            engine.schedule_load()

    def retheme(self):
        super().retheme()
        if self._list_controls is not None:
            self._list_controls.retheme()
        if self._list_view is not None:
            self._list_view.retheme()
