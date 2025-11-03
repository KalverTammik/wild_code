# -*- coding: utf-8 -*-
"""
Contracts module UI – residentne muster ModuleBaseUI peal.
Erinevus teiste moodulitega: FEED_LOGIC klass, pealkiri, ning TYPE filter ON lubatud.
"""

from typing import Optional, Type, List, Any  

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QScrollArea, QSizePolicy, QLabel, QFrame
from PyQt5.QtGui import  QColor
from PyQt5.QtWidgets import QGraphicsDropShadowEffect


from ...ui.ModuleBaseUI import ModuleBaseUI
from ...languages.language_manager import LanguageManager
from ...widgets.StatusFilterWidget import StatusFilterWidget
from ...widgets.TypeFilterWidget import TypeFilterWidget
from ...utils.url_manager import Module
from ...widgets.theme_manager import ThemeManager
from ...constants.file_paths import QssPaths
from ...utils.logger import debug as log_debug, is_debug as is_global_debug
from ...constants.pagination import DEFAULT_BATCH_SIZE
from ...feed.FeedLogic import UnifiedFeedLogic as FeedLogic
from ...widgets.OverdueDueSoonPillsWidget import OverdueDueSoonPillsLogic, OverdueDueSoonPillsUtils, OverdueDueSoonPillsWidget
from ...widgets.BaseFilterWidget import FilterRefreshHelper
from ...constants.module_names import CONTRACT_MODULE





class ContractsModule(ModuleBaseUI):
    
    TITLE_KEY = "Contracts"
    MODULE_ENUM = Module.CONTRACT
    FEED_LOGIC_CLS: Type[FeedLogic] = FeedLogic
    BACKEND_ENTITY = "CONTRACT"
    QUERY_FILE = "ListFilteredContracts.graphql"
    USE_TYPE_FILTER = True
    BATCH_SIZE = DEFAULT_BATCH_SIZE


    def __init__(
        self,
        name: Optional[str] = None,                          # if omitted, use class name
        parent: Optional[QWidget] = None,
        qss_files: Optional[List[str]] = None,

    ) -> None:
        
        super().__init__(parent)
        # Use canonical module key by default so registration and icon/name lookup
        # in ModuleManager and Sidebar map correctly (e.g. 'ContractModule').
        self.name = name if name is not None else CONTRACT_MODULE
        self.setObjectName(self.name)
     
        self.lang_manager = LanguageManager()
        self.theme_manager = ThemeManager()

        # lisatud, et dialog.py saaks edasi anda:
        self.qss_files = qss_files


        self.feed_logic = None
        self._current_where = None
        self._status_preferences_loaded = False
        self._type_preferences_loaded = False

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
        try:
            self.status_filter = StatusFilterWidget(Module.CONTRACT, self.toolbar_area, debug=is_global_debug())
            self.toolbar_area.register_filter_widget("status", self.status_filter)

            self.type_filter = None
            if self.USE_TYPE_FILTER:
                self.type_filter = TypeFilterWidget(Module.CONTRACT, self.lang_manager, self.toolbar_area, debug=is_global_debug())
                self.toolbar_area.register_filter_widget("type", self.type_filter)

            #self.toolbar_area.filtersChanged.connect(self._on_filters_changed)
        except Exception as e:
            log_debug(f"[ContractUi] Toolbar init failed: {e}")

        # Add pills to the right side of the toolbar
        try:
            self.toolbar_area.add_right(self.overdue_pills)
        except Exception:
            pass

        # Add a compact refresh button on the left (after filters)
        try:
            self._refresh_helper = FilterRefreshHelper(self)
            refresh_widget = self._refresh_helper.make_filter_refresh_button(self.toolbar_area)
            self.toolbar_area.add_left(refresh_widget)
        except Exception as e:
            log_debug(f"[ContractUi] Toolbar init failed: {e}")

        self.feed_content = QWidget()
        self.feed_content.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        self.feed_layout = QVBoxLayout(self.feed_content)
        self.feed_layout.setContentsMargins(0, 0, 0, 0)
        self.feed_layout.setSpacing(8)

        self._empty_state = QLabel(self.lang_manager.translate("No contracts found") if self.lang_manager else "No contracts found")
        self._empty_state.setAlignment(Qt.AlignCenter)
        self._empty_state.setVisible(False)
        self.feed_layout.addWidget(self._empty_state)
        self.feed_layout.addStretch(1)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setWidget(self.feed_content)
        self.display_area.layout().addWidget(self.scroll_area)

        # Läved ja debounce (ühine muster)
        self.PREFETCH_PX = 300
        self.LOAD_DEBOUNCE_MS = 80

        # Engine alles pärast UI valmimist
        self.init_feed_engine(self.load_next_batch, debounce_ms=self.LOAD_DEBOUNCE_MS)

        # Teema

        #ThemeManager.apply_module_style(self._empty_state, [QssPaths.MODULE_CARD])
        self.theme_manager.apply_module_style(self, [QssPaths.MODULES_MAIN])

    # --- Aktivatsioon / deaktiveerimine (ühine muster) ---
    def activate(self) -> None:
        super().activate()

        # Lazy init feed_logic (use centralized DEFAULT_BATCH_SIZE if module does not override)
        if self.feed_logic is None:
            batch = self.BATCH_SIZE if self.BATCH_SIZE is not None else DEFAULT_BATCH_SIZE
            self.feed_logic = self.FEED_LOGIC_CLS(self.BACKEND_ENTITY, self.QUERY_FILE, self.lang_manager, batch_size=batch)

        # Lazy-load filters
        self._suppress_filter_events = True
        try:
            if hasattr(self, 'status_filter') and self.status_filter:
                self.status_filter.ensure_loaded()
        except Exception:
            pass
        try:
            if hasattr(self, 'type_filter') and self.type_filter:
                self.type_filter.ensure_loaded()
        except Exception:
            pass

        # Drive an initial load using current selections
        self._suppress_filter_events = False
        current_filters = {
            "status": (self.status_filter.selected_ids() if getattr(self, 'status_filter', None) else []),
            "type": (self.type_filter.selected_ids() if getattr(self, 'type_filter', None) else []),
        }
        self._on_filters_changed(current_filters)

        # Load overdue/due-soon counts for the module and apply to buttons
        try:
            overdue_count = OverdueDueSoonPillsUtils.refresh_counts_for_module(Module.CONTRACT)
            OverdueDueSoonPillsLogic.set_counts(overdue_count, getattr(self, 'overdue_btn', None), getattr(self, 'due_soon_btn', None))
        except Exception:
            pass

    def deactivate(self) -> None:
        super().deactivate()

    # --- Andmete laadimine ---
    def load_next_batch(self):
        return self.process_next_batch(retheme_func=self.retheme_contract)

    # --- Filtrid (ühine muster) ---
    def _on_filters_changed(self, filters: dict) -> None:
        # Puhasta buffer filtri muutmisel, et laadida ainult uued andmed
        if hasattr(self, 'feed_load_engine') and hasattr(self.feed_load_engine, 'buffer'):
            self.feed_load_engine.buffer.clear()
        status_ids = filters.get("status") or []
        type_ids = filters.get("type") or []

        # Build base AND list
        and_list = []
        if status_ids:
            and_list.append({"column": "STATUS", "operator": "IN", "value": status_ids})
        if self.USE_TYPE_FILTER and type_ids:
            and_list.append({"column": "TYPE", "operator": "IN", "value": type_ids})

        where = {"AND": and_list} if and_list else None

        # Avoid re-applying same WHERE
        if where == self._current_where:
            return
        self._current_where = where

        if self.feed_logic is None:
            batch = self.BATCH_SIZE if self.BATCH_SIZE is not None else DEFAULT_BATCH_SIZE
            self.feed_logic = self.FEED_LOGIC_CLS(self.BACKEND_ENTITY, self.QUERY_FILE, self.lang_manager, batch_size=batch)

        try:
            self.feed_logic.set_where(where)
        except Exception as e:
            log_debug(f"[ContractUi] set_where failed: {e}")

        self.clear_feed(self.feed_layout, self._empty_state)
        try:
            self.scroll_area.verticalScrollBar().setValue(0)
        except Exception:
            pass
        self.feed_load_engine.schedule_load()

    # --- Teema ---
    def retheme_contract(self) -> None:
        ThemeManager.apply_module_style(self, [QssPaths.MODULES_MAIN])
        for card in self.display_area.findChildren(QFrame, "ModuleInfoCard"):
            ThemeManager.apply_module_style(card, [QssPaths.MODULE_CARD])
            effect = card.graphicsEffect()
            if isinstance(effect, QGraphicsDropShadowEffect):
                theme = ThemeManager.load_theme_setting()
                shadow_color = QColor(255, 255, 255, 90) if theme == 'dark' else QColor(0, 0, 0, 120)
                effect.setColor(shadow_color)

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
            status_ids = self.status_filter.selected_ids() if getattr(self, 'status_filter', None) else []
            type_ids = self.type_filter.selected_ids() if getattr(self, 'type_filter', None) else []
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
        # Avoid re-applying the same WHERE repeatedly
        if where == self._current_where:
            return
        if self.feed_logic is None:
            batch = self.BATCH_SIZE if self.BATCH_SIZE is not None else DEFAULT_BATCH_SIZE
            self.feed_logic = self.FEED_LOGIC_CLS(self.BACKEND_ENTITY, self.QUERY_FILE, self.lang_manager, batch_size=batch)
        try:
            self.feed_logic.set_where(where if where and where.get("AND") else None)
        except Exception as e:
            log_debug(f"[ContractUi] set_where (overdue/dueSoon) failed: {e}")
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
                self.feed_load_engine.buffer.clear()
                self.feed_load_engine.schedule_load()
        except Exception:
            pass
        self._current_where = where
