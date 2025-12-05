# -*- coding: utf-8 -*-
"""
Contracts module UI – residentne muster ModuleBaseUI peal.
Erinevus teiste moodulitega: FEED_LOGIC klass, pealkiri, ning TYPE filter ON lubatud.
"""

from typing import Optional, Type, List

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
from ...widgets.OverdueDueSoonPillsWidget import (
    OverdueDueSoonPillsLogic,
    OverdueDueSoonPillsUtils,
    OverdueDueSoonPillsWidget,
)
from ...widgets.filter_refresh_helper import FilterRefreshHelper
from ...utils.FilterHelpers.FilterHelper import FilterHelper

class ContractsModule(ModuleBaseUI):

    FEED_LOGIC_CLS: Type[FeedLogic] = FeedLogic
    QUERY_FILE = "ListFilteredContracts.graphql"

    def __init__(
        self,
        name: Optional[str] = None,
        lang_manager: Optional[object] = None,
        parent: Optional[QWidget] = None,
        qss_files: Optional[List[str]] = None,
    ) -> None:

        super().__init__(parent)

        # Kasuta kanonilist module_key'd (lowercase) kõikjal
    

        self.module_key = Module.CONTRACT.name.lower()  # "contract"
        self.name = self.module_key
        self.setObjectName(self.name)

        self.lang_manager = lang_manager
        self.theme_manager = ThemeManager()

        supports = ModuleManager().getModuleSupports(Module.CONTRACT.name) or {}
        self.supports_status_filter = bool(supports.get("statuses", True))
        self.supports_type_filter = bool(supports.get("types", True))
        self.supports_tags_filter = bool(supports.get("tags", True))

        # lisatud, et dialog.py saaks edasi anda:
        self.qss_files = qss_files
        self.feed_logic = None
        self._status_preferences_loaded = False
        self._type_preferences_loaded = False
        self._suppress_filter_events = False

        # Pills and helpers
        self.overdue_pills = OverdueDueSoonPillsWidget()
        self.overdue_pills_logic = OverdueDueSoonPillsLogic()
        self.overdue_pills_utils = OverdueDueSoonPillsUtils()

        # Wire pill buttons
        try:
            self.overdue_btn = self.overdue_pills.overdue_btn
            self.due_soon_btn = self.overdue_pills.due_soon_btn
            self.overdue_btn.clicked.connect(self._on_overdue_clicked)
            self.due_soon_btn.clicked.connect(self._on_due_soon_clicked)
        except Exception:
            pass

        # Register filters (status + optional type)
        if self.supports_status_filter:
            self.status_filter = StatusFilterWidget(self.module_key, self.toolbar_area)
            self.toolbar_area.add_left(self.status_filter)
            self.status_filter.selectionChanged.connect(self._on_status_filter_selection)

        self.type_filter = None
        if self.supports_type_filter:
            self.type_filter = TypeFilterWidget(self.module_key, self.toolbar_area)
            title = self.type_filter.filter_title
            self.toolbar_area.add_left(self.type_filter, title=title)
            self.type_filter.selectionChanged.connect(self._on_type_filter_selection)

        if self.supports_tags_filter:
            self.tags_filter = TagsFilterWidget(self.module_key, self.lang_manager, self.toolbar_area)
            self.toolbar_area.add_left(self.tags_filter)
            self.tags_filter.selectionChanged.connect(self._on_tags_filter_selection)

        self._filter_widgets = [w for w in (self.status_filter, self.type_filter, self.tags_filter) if w is not None]

        self.toolbar_area.add_right(self.overdue_pills)

        # Add a compact refresh button on the left (after filters)
        self._refresh_helper = FilterRefreshHelper(self)
        refresh_widget = self._refresh_helper.make_filter_refresh_button(self.toolbar_area)
        self.toolbar_area.set_refresh_widget(refresh_widget)

        self.feed_content = QWidget()
        self.feed_content.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        self.feed_layout = QVBoxLayout(self.feed_content)
        self.feed_layout.setContentsMargins(0, 0, 0, 0)
        self.feed_layout.setSpacing(6)

        self._empty_state = QLabel(self.lang_manager.translate("No contracts found") if self.lang_manager else "No contracts found")
        self._empty_state.setAlignment(Qt.AlignCenter)
        self._empty_state.setVisible(False)
        self.feed_layout.addWidget(self._empty_state)
        self.feed_layout.addStretch(1)


        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setWidget(self.feed_content)

        ThemeManager.apply_module_style(self, [QssPaths.MODULE_CARD])

        # Configure optional single-item query for opening a contract by id
        try:
            if self.feed_logic is None:
                self.feed_logic = self.FEED_LOGIC_CLS(self.module_key, self.QUERY_FILE, self.lang_manager)
            self.feed_logic.configure_single_item_query("w_contracts_module_data_by_item_id.graphql")
        except Exception:
            pass

    def activate(self) -> None:
        super().activate()
        # Normal activation path (sidebar click) should run full feed loader.
        # When coming from search, PluginDialog will call open_item_from_search
        # directly and we want to avoid triggering a full feed reload there.
        # Rakenda eelistused filtri valikutele
        self._refresh_filters()

        # Load overdue/due-soon counts for the module and apply to buttons
        try:
            overdue_count = OverdueDueSoonPillsUtils.refresh_counts_for_module(Module.CONTRACT)
            OverdueDueSoonPillsLogic.set_counts(
                overdue_count,
                getattr(self, "overdue_btn", None),
                getattr(self, "due_soon_btn", None),
            )
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
        """Open a contract coming from unified search without kicking feed loader.

        Switch UnifiedFeedLogic into single-item mode using the by-id GraphQL
        query so the existing feed rendering pipeline can show a single card
        for the given contract id.
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
                self.feed_logic.configure_single_item_query("w_contracts_module_data_by_item_id.graphql")

            self.feed_logic.set_single_item_mode(True, id=item_id)

            if self.feed_load_engine:
                self.feed_load_engine.schedule_load()
        except Exception:
            # If anything goes wrong, fall back to a simple debug empty state
            try:
                self._empty_state.setText(f"Search wiring error for contract {item_id}")
                self._empty_state.setVisible(True)
            except Exception:
                pass

    # --- Andmete laadimine ---
    def load_next_batch(self):
        return self.process_next_batch(retheme_func=self.retheme_contract)

    # --- Filtrid (ühine muster) ---
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
        if self._suppress_filter_events:
            return
        # Puhasta buffer filtri muutmisel, et laadida ainult uued andmed
        if self.feed_load_engine:
            try:
                self.feed_load_engine.buffer.clear()
            except Exception:
                pass

        if status_ids is None and self.status_filter:
            status_ids = FilterHelper.selected_ids(self.status_filter)
            if not status_ids:
                saved = self._get_saved_status_ids()
                if saved:
                    status_ids = saved
        if type_ids is None and self.type_filter:
            type_ids = self.type_filter.selected_ids()
            if not type_ids:
                saved_types = self._get_saved_type_ids()
                if saved_types:
                    type_ids = saved_types
        if tags_ids is None and self.tags_filter:
            tags_ids = FilterHelper.selected_ids(self.tags_filter)
            if not tags_ids:
                saved_tags = self._get_saved_tag_ids()
                if saved_tags:
                    tags_ids = saved_tags

        # Build base AND list
        and_list = []
        if status_ids:
            and_list.append({"column": "STATUS", "operator": "IN", "value": status_ids})
        if self.supports_type_filter and type_ids:
            and_list.append({"column": "TYPE", "operator": "IN", "value": type_ids})

        has_tags_filter = self._build_has_tags_condition(tags_ids or [])
        where = {"AND": and_list} if and_list else None
        if self.feed_logic is None:
            self.feed_logic = self.FEED_LOGIC_CLS(self.module_key, self.QUERY_FILE, self.lang_manager)
            try:
                self.feed_logic.configure_single_item_query("w_contracts_module_data_by_item_id.graphql")
            except Exception:
                pass

        # Ensure we are back in list mode when filters are used
        try:
            self.feed_logic.set_single_item_mode(False)
        except Exception:
            pass
            try:
                self.feed_logic.configure_single_item_query("w_contracts_module_data_by_item_id.graphql")
            except Exception:
                pass

        try:
            self.feed_logic.set_where(where)
        except Exception:
            pass
        try:
            self.feed_logic.set_extra_arguments(hasTags=has_tags_filter)
        except Exception:
            pass

        self.clear_feed(self.feed_layout, self._empty_state)
        try:
            self.scroll_area.verticalScrollBar().setValue(0)
        except Exception:
            pass
        try:
            self.feed_load_engine.schedule_load()
        except Exception:
            pass

    # --- Teema ---
    def retheme_contract(self) -> None:
        #print("Retheming contract module UI")
        for card in self.scroll_area.findChildren(QFrame, "ModuleInfoCard"):
            #print("Retheming contract card:", card)
            ThemeManager.apply_module_style(card, [QssPaths.MODULE_CARD])
            styleExtras.apply_chip_shadow(card)

    # --- Module contract ---
    def get_widget(self) -> QWidget:
        return self

    def _on_overdue_clicked(self):
        # Set pill active states and apply overdue filter
        self.overdue_pills.set_overdue_active(True)
        self.overdue_pills.set_due_soon_active(False)
        where = self.overdue_pills_utils.build_overdue_where()
        OverdueDueUtils.apply_where(self, where)

    def _on_due_soon_clicked(self):
        # Set pill active states and apply due soon filter
        self.overdue_pills.set_overdue_active(False)
        self.overdue_pills.set_due_soon_active(True)
        where = self.overdue_pills_utils.build_due_soon_where()
        OverdueDueUtils.apply_where(self, where)

class OverdueDueUtils:
    @staticmethod
    def apply_where(module: "ContractsModule", where: dict) -> None:
        if module.feed_logic is None:
            module.feed_logic = module.FEED_LOGIC_CLS(module.module_key, module.QUERY_FILE, module.lang_manager)

        tags_ids = FilterHelper.selected_ids(module.tags_filter) if getattr(module, "tags_filter", None) else []
        has_tags_filter = module._build_has_tags_condition(tags_ids or [])

        if module.feed_load_engine:
            module.feed_load_engine.buffer.clear()

        module.feed_logic.set_where(where if where and where.get("AND") else None)
        module.feed_logic.set_extra_arguments(hasTags=has_tags_filter)

        module.clear_feed(module.feed_layout, module._empty_state)
        module.scroll_area.verticalScrollBar().setValue(0)
        if module.feed_load_engine:
            module.feed_load_engine.schedule_load()
