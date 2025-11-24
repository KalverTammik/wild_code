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
from ...widgets.theme_manager import ThemeManager, styleExtras
from ...constants.file_paths import QssPaths
from ...feed.FeedLogic import UnifiedFeedLogic as FeedLogic
from ...widgets.OverdueDueSoonPillsWidget import (
    OverdueDueSoonPillsLogic,
    OverdueDueSoonPillsUtils,
    OverdueDueSoonPillsWidget,
)
from ...widgets.filter_refresh_helper import FilterRefreshHelper


class ContractsModule(ModuleBaseUI):

    FEED_LOGIC_CLS: Type[FeedLogic] = FeedLogic
    QUERY_FILE = "ListFilteredContracts.graphql"
    USE_TYPE_FILTER = True

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
        self.status_filter = StatusFilterWidget(self.module_key, self.toolbar_area)
        self.toolbar_area.add_left(self.status_filter)
        self.status_filter.selectionChanged.connect(self._on_status_filter_selection)

        self.type_filter = None
        if self.USE_TYPE_FILTER:
            self.type_filter = TypeFilterWidget(self.module_key, self.toolbar_area)
            self.toolbar_area.add_left(self.type_filter)
            self.type_filter.selectionChanged.connect(self._on_type_filter_selection)

        self.tags_filter = TagsFilterWidget(self.module_key, self.lang_manager, self.toolbar_area)
        self.toolbar_area.add_left(self.tags_filter)
        self.tags_filter.selectionChanged.connect(self._on_tags_filter_selection)

        self._filter_widgets = [w for w in (self.status_filter, self.type_filter, self.tags_filter) if w is not None]

        self.toolbar_area.add_right(self.overdue_pills)

        # Add a compact refresh button on the left (after filters)
        self._refresh_helper = FilterRefreshHelper(self)
        refresh_widget = self._refresh_helper.make_filter_refresh_button(self.toolbar_area)
        self.toolbar_area.add_left(refresh_widget)

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

        self.theme_manager.apply_module_style(self, [QssPaths.MODULES_MAIN])

    def activate(self) -> None:
        super().activate()

        # Lazy init feed_logic 
        if self.feed_logic is None:
            self.feed_logic = self.FEED_LOGIC_CLS(self.module_key, self.QUERY_FILE, self.lang_manager)

        # Lazy-load filters
        self._suppress_filter_events = True
        if self.status_filter:
            self.status_filter.ensure_loaded()
        self._load_and_apply_status_preferences()

        if self.type_filter:
            self.type_filter.ensure_loaded()
            self._load_and_apply_type_preferences()

        if self.tags_filter:
            self.tags_filter.ensure_loaded()
            self._load_and_apply_tags_preferences()

        # Drive an initial load using current selections
        self._suppress_filter_events = False
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
            status_ids = self.status_filter.selected_ids()
        if type_ids is None and self.type_filter:
            type_ids = self.type_filter.selected_ids()
        if tags_ids is None and self.tags_filter:
            tags_ids = self.tags_filter.selected_ids()

        # Build base AND list
        and_list = []
        if status_ids:
            and_list.append({"column": "STATUS", "operator": "IN", "value": status_ids})
        if self.USE_TYPE_FILTER and type_ids:
            and_list.append({"column": "TYPE", "operator": "IN", "value": type_ids})

        has_tags_filter = self._build_has_tags_condition(tags_ids or [])
        where = {"AND": and_list} if and_list else None
        if self.feed_logic is None:
            self.feed_logic = self.FEED_LOGIC_CLS(self.module_key, self.QUERY_FILE, self.lang_manager)

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
        ThemeManager.apply_module_style(self, [QssPaths.MODULES_MAIN])
        for card in self.scroll_area.findChildren(QFrame, "ModuleInfoCard"):
            ThemeManager.apply_module_style(card, [QssPaths.MODULE_CARD])
            styleExtras.apply_chip_shadow(card)

    # --- Module contract ---
    def get_widget(self) -> QWidget:
        return self

    def _on_overdue_clicked(self):
        # Set pill active states and apply overdue filter combined with current filters
        try:
            self.overdue_pills.set_overdue_active(True)
            self.overdue_pills.set_due_soon_active(False)
        except Exception:
            pass
        base_list = self._base_filter_and_list()
        where = self.overdue_pills_utils.build_overdue_where(base_list)
        self._apply_where(where)

    def _on_due_soon_clicked(self):
        try:
            self.overdue_pills.set_overdue_active(False)
            self.overdue_pills.set_due_soon_active(True)
        except Exception:
            pass
        base_list = self._base_filter_and_list()
        where = self.overdue_pills_utils.build_due_soon_where(base_list)
        self._apply_where(where)

    def _base_filter_and_list(self) -> list:
        """Return a list of AND conditions from current filter widgets (status/type)."""
        and_list = []
        try:
            status_ids = self.status_filter.selected_ids() if self.status_filter else []
            type_ids = self.type_filter.selected_ids() if self.type_filter else []
            if status_ids:
                and_list.append({"column": "STATUS", "operator": "IN", "value": status_ids})
            if self.USE_TYPE_FILTER and type_ids:
                and_list.append({"column": "TYPE", "operator": "IN", "value": type_ids})
        except Exception:
            pass
        return and_list

    def _get_base_where(self) -> dict:
        al = self._base_filter_and_list()
        return {"AND": al} if al else {}

    def _apply_where(self, where: dict) -> None:
        # Väldi sama WHERE korduvalt rakendamist
        # Init vajadusel
        if self.feed_logic is None:
            self.feed_logic = self.FEED_LOGIC_CLS(self.module_key, self.QUERY_FILE, self.lang_manager)

        tags_ids = []
        try:
            if self.tags_filter:
                tags_ids = self.tags_filter.selected_ids()
        except Exception:
            tags_ids = []
        has_tags_filter = self._build_has_tags_condition(tags_ids or [])

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
        try:
            self.feed_logic.set_extra_arguments(hasTags=has_tags_filter)
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

