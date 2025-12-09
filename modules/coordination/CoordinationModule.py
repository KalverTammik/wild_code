# -*- coding: utf-8 -*-
"""Coordination module UI – built on ModuleBaseUI."""

from typing import Optional, Type, List, Any
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QSizePolicy, QLabel, QFrame

from ...ui.ModuleBaseUI import ModuleBaseUI
from ...widgets.StatusFilterWidget import StatusFilterWidget
from ...widgets.TypeFilterWidget import TypeFilterWidget
from ...widgets.TagsFilterWidget import TagsFilterWidget
from ...utils.url_manager import Module
from ...module_manager import ModuleManager
from ...widgets.theme_manager import ThemeManager, styleExtras
from ...constants.file_paths import QssPaths
from ...feed.FeedLogic import UnifiedFeedLogic as FeedLogic
from ...widgets.filter_refresh_helper import FilterRefreshHelper
from ...utils.FilterHelpers.FilterHelper import FilterRefreshService
from ...utils.search.SearchOpenItemMixin import SearchOpenItemMixin


class CoordinationModule(SearchOpenItemMixin, ModuleBaseUI):

    FEED_LOGIC_CLS: Type[FeedLogic] = FeedLogic
    QUERY_FILE = "ListFilteredCoordinations.graphql"
    SINGLE_ITEM_QUERY_FILE = "W_coordination_id.graphql"

    def __init__(
        self,
        language: Optional[str] = None,
        parent: Optional[QWidget] = None,
        qss_files: Optional[List[str]] = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(parent)

        self.module_key = Module.COORDINATION.value
        self.setObjectName(self.module_key)

        self.lang_manager = language
        self.theme_manager = ThemeManager()

        types, statuses, tags, archive_layer = ModuleManager().getModuleSupports(Module.COORDINATION.name) or {}
        self.supports_status_filter = statuses
        self.supports_type_filter = types
        self.supports_tags_filter = tags

        self.qss_files = qss_files
        self.feed_logic = None
        self._current_where = None
        self._suppress_filter_events = False

        if self.supports_status_filter:
            self.status_filter: Optional[StatusFilterWidget] = None
            self.status_filter = StatusFilterWidget(self.module_key, self.toolbar_area)
            self.toolbar_area.add_left(self.status_filter)
            self.status_filter.selectionChanged.connect(self._on_status_filter_selection)

        if self.supports_type_filter:
            self.type_filter: Optional[TypeFilterWidget] = None
            self.type_filter = TypeFilterWidget(self.module_key, self.toolbar_area)
            self.toolbar_area.add_left(self.type_filter)
            self.type_filter.selectionChanged.connect(self._on_type_filter_selection)

        if self.supports_tags_filter:
            self.tags_filter: Optional[TagsFilterWidget] = None
            self.tags_filter = TagsFilterWidget(Module.COORDINATION, self.lang_manager, self.toolbar_area)
            self.toolbar_area.add_left(self.tags_filter)
            self.tags_filter.selectionChanged.connect(self._on_tags_filter_selection)

        self._filter_widgets = [w for w in (self.status_filter, self.type_filter, self.tags_filter) if w is not None]

        self._refresh_helper = FilterRefreshHelper(self)
        refresh_widget = self._refresh_helper.make_filter_refresh_button(self.toolbar_area)
        self.toolbar_area.set_refresh_widget(refresh_widget)

        self.feed_content = QWidget()
        self.feed_content.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        self.feed_layout = QVBoxLayout(self.feed_content)
        self.feed_layout.setContentsMargins(0, 0, 0, 0)
        self.feed_layout.setSpacing(6)

        empty_text = self.lang_manager.translate("No coordinations found") if self.lang_manager else "No coordinations found"
        self._empty_state = QLabel(empty_text or "No coordinations found")
        self._empty_state.setAlignment(Qt.AlignCenter)
        self._empty_state.setVisible(False)
        self.feed_layout.addWidget(self._empty_state)
        self.feed_layout.addStretch(1)

        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setWidget(self.feed_content)
        ThemeManager.apply_module_style(self._empty_state, [QssPaths.MODULE_CARD])

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------
    def activate(self) -> None:
        super().activate()
        print("[CoordinationModule] Activated")
        self._refresh_filters()

    def _ensure_feed_logic(self) -> None:
        print("[CoordinationModule] Ensuring feed logic is initialized")
        if self.feed_logic is not None:
            return
        self.feed_logic = self.FEED_LOGIC_CLS(self.module_key, self.QUERY_FILE, self.lang_manager)
        print("[CoordinationModule] Feed logic initialized")
        configure_single = getattr(self.feed_logic, "configure_single_item_query", None)
        if callable(configure_single):
            configure_single(self.SINGLE_ITEM_QUERY_FILE)

    def load_next_batch(self):
        return self.process_next_batch(retheme_func=self.retheme_coordinations)

    # ------------------------------------------------------------------
    # Filters
    # ------------------------------------------------------------------
    def _on_status_filter_selection(self, _texts, ids):
        self._refresh_filters(status_ids=ids)

    def _on_type_filter_selection(self, _texts, ids):
        self._refresh_filters(type_ids=ids)

    def _on_tags_filter_selection(self, _texts, ids):
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

    # ------------------------------------------------------------------
    # Search integration
    # ------------------------------------------------------------------
    # ------------------------------------------------------------------
    # Theming
    # ------------------------------------------------------------------
    def retheme_coordinations(self) -> None:
        for card in self.scroll_area.findChildren(QFrame, "ModuleInfoCard"):
            ThemeManager.apply_module_style(card, [QssPaths.MODULE_CARD])
            styleExtras.apply_chip_shadow(card)

    # ------------------------------------------------------------------
    # Module contract
    # ------------------------------------------------------------------
    def get_widget(self) -> QWidget:
        return self
