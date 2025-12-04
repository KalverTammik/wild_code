# -*- coding: utf-8 -*-
"""
Projects module UI – residentne muster ModuleBaseUI peal.
Erinevus teiste moodulitega: FEED_LOGIC klass, pealkiri, ning TYPE filtrit ei kasutata.
"""

from typing import Optional, Type, List, Any
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QSizePolicy, QLabel, QFrame

from ...ui.ModuleBaseUI import ModuleBaseUI
from ...widgets.StatusFilterWidget import StatusFilterWidget
from ...widgets.TagsFilterWidget import TagsFilterWidget
from ...utils.url_manager import Module
from ...module_manager import ModuleManager
from ...widgets.theme_manager import ThemeManager, styleExtras
from ...constants.file_paths import QssPaths
from ...feed.FeedLogic import UnifiedFeedLogic as FeedLogic
from ...widgets.OverdueDueSoonPillsWidget import (
    OverdueDueSoonPillsLogic,
    OverdueDueSoonPillsUtils,
    OverdueDueSoonPillsWidget,
)
from ...widgets.filter_refresh_helper import FilterRefreshHelper
from ...utils.FilterHelpers.FilterHelper import FilterHelper


class ProjectsModule(ModuleBaseUI):

    FEED_LOGIC_CLS: Type[FeedLogic] = FeedLogic
    QUERY_FILE = "ListFilteredProjects.graphql"

    def __init__(
        self,
        language: Optional[str] = None,
        parent: Optional[QWidget] = None,
        qss_files: Optional[List[str]] = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(parent)

        # Kasuta kanonilist module_key'd (lowercase) kõikjal
        self.module_key = Module.PROJECT.name.lower()  # "project"
        self.name = self.module_key
        self.setObjectName(self.name)

        self.lang_manager = language
        self.theme_manager = ThemeManager()

        # Determine which filters this module should expose based on module registration metadata
        supports = ModuleManager().getModuleSupports(Module.PROJECT.name) or {}
        self.supports_status_filter = bool(supports.get("statuses", True))
        self.supports_tags_filter = bool(supports.get("tags", True))

        # edasiandmiseks
        self.qss_files = qss_files

        # Feed/filters state
        self.feed_logic = None
        self._current_where = None
        self._status_preferences_loaded = False
        self._tags_preferences_loaded = False
        self._suppress_filter_events = False

        # Pills
        self.overdue_pills = OverdueDueSoonPillsWidget()
        self.overdue_pills_logic = OverdueDueSoonPillsLogic()
        self.overdue_pills_utils = OverdueDueSoonPillsUtils()

        # Wire pill clicks
        try:
            self.overdue_btn = self.overdue_pills.overdue_btn
            self.due_soon_btn = self.overdue_pills.due_soon_btn
            self.overdue_btn.clicked.connect(self._on_overdue_clicked)
            self.due_soon_btn.clicked.connect(self._on_due_soon_clicked)
        except Exception:
            pass

        # Toolbar: pills right
        self.toolbar_area.add_right(self.overdue_pills)

        # Status filter (kasuta module_key)
        if self.supports_status_filter:
            self.status_filter = StatusFilterWidget(self.module_key, self.toolbar_area)
            self.toolbar_area.add_left(self.status_filter)
            self.status_filter.selectionChanged.connect(self._on_status_filter_selection)

        # Tags filter (see näib eeldavat Module enum'i; jätame nii)
        if self.supports_tags_filter:
            self.tags_filter = TagsFilterWidget(Module.PROJECT, self.lang_manager, self.toolbar_area)
            self.toolbar_area.add_left(self.tags_filter)
            self.tags_filter.selectionChanged.connect(self._on_tags_filter_selection)

        self._filter_widgets = [w for w in (self.status_filter, self.tags_filter) if w is not None]


        self._refresh_helper = FilterRefreshHelper(self)
        refresh_widget = self._refresh_helper.make_filter_refresh_button(self.toolbar_area)
        self.toolbar_area.set_refresh_widget(refresh_widget)


        # Feed area
        self.feed_content = QWidget()
        self.feed_content.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        self.feed_layout = QVBoxLayout(self.feed_content)
        self.feed_layout.setContentsMargins(0, 0, 0, 0)
        self.feed_layout.setSpacing(6)

        self._empty_state = QLabel(self.lang_manager.translate("No projects found") if self.lang_manager else "No projects found")
        self._empty_state.setAlignment(Qt.AlignCenter)
        self._empty_state.setVisible(False)
        self.feed_layout.addWidget(self._empty_state)
        self.feed_layout.addStretch(1)

        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setWidget(self.feed_content)
        # Teema
        ThemeManager.apply_module_style(self._empty_state, [QssPaths.MODULE_CARD])

        # Configure optional single-item query for opening a project by id
        try:
            if self.feed_logic is None:
                self.feed_logic = self.FEED_LOGIC_CLS(self.module_key, self.QUERY_FILE, self.lang_manager)
            self.feed_logic.configure_single_item_query("w_projects_module_data_by_item_id.graphql")
        except Exception:
            pass

    # --- Aktivatsioon / deaktiveerimine ---
    def activate(self) -> None:
        super().activate()
        # Normal activation path (sidebar click) should run full feed loader.
        # When coming from search, PluginDialog will call open_item_from_search
        # directly and we want to avoid triggering a full feed reload there.

        # Lazy init FeedLogic
        if self.feed_logic is None:
            self.feed_logic = self.FEED_LOGIC_CLS(self.module_key, self.QUERY_FILE, self.lang_manager)
            try:
                self.feed_logic.configure_single_item_query("w_projects_module_data_by_item_id.graphql")
            except Exception:
                pass

        self._refresh_filters()

        # Overdue/due soon count
        try:
            overdue_count = OverdueDueSoonPillsUtils.refresh_counts_for_module(Module.PROJECT)
            OverdueDueSoonPillsLogic.set_counts(overdue_count, self.overdue_btn, self.due_soon_btn)
        except Exception:
            pass

    def deactivate(self) -> None:
        super().deactivate()
        # Kosmeetika: lülita pillid passiivseks
        try:
            self.overdue_pills.set_overdue_active(False)
            self.overdue_pills.set_due_soon_active(False)
        except Exception:
            pass

    def open_item_from_search(self, search_module: str, item_id: str, title: str) -> None:
        """Open a project coming from unified search without kicking feed loader.

        Switch UnifiedFeedLogic into single-item mode using the by-id GraphQL
        query so the existing feed rendering pipeline can show a single card
        for the given project id.
        """
        # Stop any pending feed loads and clear existing cards
        try:
            if self.feed_load_engine:
                self.feed_load_engine.cancel_pending()
                if self.feed_load_engine.buffer:
                    self.feed_load_engine.buffer.clear()
        except Exception:
            pass

        try:
            self.clear_feed(self.feed_layout, self._empty_state)
        except Exception:
            pass

        # Switch feed logic to single-item mode using the by-id GraphQL query
        try:
            if self.feed_logic is None:
                self.feed_logic = self.FEED_LOGIC_CLS(self.module_key, self.QUERY_FILE, self.lang_manager)
                self.feed_logic.configure_single_item_query("w_projects_module_data_by_item_id.graphql")

            self.feed_logic.set_single_item_mode(True, id=item_id)

            if self.feed_load_engine:
                self.feed_load_engine.schedule_load()
        except Exception:
            # If anything goes wrong, fall back to a simple debug empty state
            try:
                self._empty_state.setText(f"Search wiring error for project {item_id}")
                self._empty_state.setVisible(True)
            except Exception:
                pass

    # --- Andmete laadimine ---
    def load_next_batch(self):
        return self.process_next_batch(retheme_func=self.retheme_projects)

    # --- Filtrid ---
    def _on_status_filter_selection(self, _texts: List[str], ids: List[str]) -> None:
        self._refresh_filters(status_ids=ids)

    def _on_tags_filter_selection(self, _texts: List[str], ids: List[str]) -> None:
        self._refresh_filters(tags_ids=ids)

    def _refresh_filters(self, *, status_ids: Optional[List[str]] = None, tags_ids: Optional[List[str]] = None) -> None:
        # Vaikne faas algse initsialiseerimise ajal
        if self._suppress_filter_events:
            return

        # Puhasta buffer enne uue WHERE'i rakendamist
        if self.feed_load_engine and self.feed_load_engine.buffer:
            try:
                self.feed_load_engine.buffer.clear()
            except Exception:
                pass

        if status_ids is None and self.status_filter:
            status_ids = FilterHelper.selected_ids(self.status_filter)
            if not status_ids:
                saved_status = self._get_saved_status_ids()
                if saved_status:
                    status_ids = saved_status
        if tags_ids is None and self.tags_filter:
            tags_ids = FilterHelper.selected_ids(self.tags_filter)
            if not tags_ids:
                saved_tags = self._get_saved_tag_ids()
                if saved_tags:
                    tags_ids = saved_tags

        # Ainult status läheb WHERE'i, sildid antakse hasTags kaudu
        and_list: List[dict] = []
        if status_ids:
            and_list.append({"column": "STATUS", "operator": "IN", "value": status_ids})
        where = {"AND": and_list} if and_list else None

        has_tags_filter = self._build_has_tags_condition(tags_ids or [])

        # Hoia hetke seisu
        self._current_where = where

        # Init vajadusel
        if self.feed_logic is None:
            self.feed_logic = self.FEED_LOGIC_CLS(self.module_key, self.QUERY_FILE, self.lang_manager)
            try:
                self.feed_logic.configure_single_item_query("w_projects_module_data_by_item_id.graphql")
            except Exception:
                pass

        # Ensure we are back in list mode when filters are used
        try:
            self.feed_logic.set_single_item_mode(False)
        except Exception:
            pass

        if self.feed_logic:
            self.feed_logic.set_extra_arguments(hasTags=has_tags_filter)

        # Rakenda WHERE
        try:
            self.feed_logic.set_where(where)
        except Exception:
            pass

        # UI reset & laadimine
        self.clear_feed(self.feed_layout, self._empty_state)
        try:
            self.scroll_area.verticalScrollBar().setValue(0)
        except Exception:
            pass
        try:
            self.feed_load_engine.schedule_load()
        except Exception:
            pass

        # Reset pillid
        try:
            self.overdue_pills.set_overdue_active(False)
            self.overdue_pills.set_due_soon_active(False)
        except Exception:
            pass

    def _base_filter_and_list(self) -> List[dict]:
        and_list: List[dict] = []
        try:
            status_ids = FilterHelper.selected_ids(self.status_filter) if self.status_filter else []
            if status_ids:
                and_list.append({"column": "STATUS", "operator": "IN", "value": status_ids})
        except Exception:
            pass
        return and_list

    def _get_base_where(self) -> dict:
        and_list = self._base_filter_and_list()
        return {"AND": and_list} if and_list else {}

    def _apply_where(self, where: dict) -> None:
        # Väldi sama WHERE korduvalt rakendamist
        if where == self._current_where:
            return

        # Init vajadusel
        if self.feed_logic is None:
            self.feed_logic = self.FEED_LOGIC_CLS(self.module_key, self.QUERY_FILE, self.lang_manager)

        # Puhasta enne uue WHERE rakendamist
        try:
            if self.feed_load_engine:
                self.feed_load_engine.buffer.clear()
        except Exception:
            pass

        # Rakenda WHERE (tühi AND -> None)
        try:
            self.feed_logic.set_where(where if where and where.get("AND") else None)
        except Exception:
            pass

        # UI reset & laadimine
        try:
            self.clear_feed(self.feed_layout, self._empty_state)
        except Exception:
            pass
        try:
            self.scroll_area.verticalScrollBar().setValue(0)
        except Exception:
            pass
        try:
            if self.feed_load_engine:
                self.feed_load_engine.schedule_load()
        except Exception:
            pass

        self._current_where = where

    def _on_overdue_clicked(self):
        # Set pill active states and apply overdue filter
        try:
            self.overdue_pills.set_overdue_active(True)
            self.overdue_pills.set_due_soon_active(False)
        except Exception:
            pass
        where = self.overdue_pills_utils.build_overdue_where()
        self._apply_where(where)

    def _on_due_soon_clicked(self):
        # Set pill active states and apply due soon filter
        try:
            self.overdue_pills.set_overdue_active(False)
            self.overdue_pills.set_due_soon_active(True)
        except Exception:
            pass
        where = self.overdue_pills_utils.build_due_soon_where()
        self._apply_where(where)

    # --- Teema ---
    def retheme_projects(self) -> None:

        for card in self.scroll_area.findChildren(QFrame, "ModuleInfoCard"):
            ThemeManager.apply_module_style(card, [QssPaths.MODULE_CARD])
            styleExtras.apply_chip_shadow(card)

    # --- Module contract ---
    def get_widget(self) -> QWidget:
        return self

