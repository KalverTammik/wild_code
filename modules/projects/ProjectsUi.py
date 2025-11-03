# -*- coding: utf-8 -*-
"""
Projects module UI – residentne muster ModuleBaseUI peal.
Erinevus teiste moodulitega: FEED_LOGIC klass, pealkiri, ning TYPE filtrit ei kasutata.
"""

from typing import Optional, Type, List, Any  # <- veendu, et Optional/Type on imporditud
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QScrollArea, QSizePolicy, QLabel, QFrame
from PyQt5.QtGui import  QColor
from PyQt5.QtWidgets import QGraphicsDropShadowEffect

from ...ui.ModuleBaseUI import ModuleBaseUI
from ...languages.language_manager import LanguageManager
from ...widgets.StatusFilterWidget import StatusFilterWidget
from ...widgets.TagsFilterWidget import TagsFilterWidget
from ...utils.url_manager import Module
from ...widgets.theme_manager import ThemeManager
from ...constants.file_paths import QssPaths
from ...utils.logger import debug as log_debug, is_debug as is_global_debug
from ...feed.FeedLogic import UnifiedFeedLogic as FeedLogic
from ...widgets.OverdueDueSoonPillsWidget import OverdueDueSoonPillsLogic, OverdueDueSoonPillsUtils, OverdueDueSoonPillsWidget
from PyQt5.QtWidgets import QPushButton
from ...widgets.BaseFilterWidget import FilterRefreshHelper
from ...constants.pagination import DEFAULT_BATCH_SIZE


class ProjectsModule(ModuleBaseUI):
    
    TITLE_KEY = "Projects"
    MODULE_ENUM = Module.PROJECT
    FEED_LOGIC_CLS: Type[FeedLogic] = FeedLogic
    BACKEND_ENTITY = "PROJECT"
    QUERY_FILE = "ListFilteredProjects.graphql"
    USE_TYPE_FILTER = False
    BATCH_SIZE = DEFAULT_BATCH_SIZE

    def __init__(
        self,
        name: Optional[str] = None,

        parent: Optional[QWidget] = None,
        qss_files: Optional[List[str]] = None,    # <-- lisatud
        **kwargs: Any                              # <-- lisatud (neelab tulevased lisad)
    ) -> None:
        
        super().__init__(parent)
        self.name = name if name is not None else self.__class__.__name__
        self.setObjectName(self.name)
        self.lang_manager = LanguageManager()
        self.theme_manager = ThemeManager()

        # lisatud, et dialog.py saaks edasi anda:
        self.qss_files = qss_files
        self._extra_init_kwargs = kwargs  # juhul kui tulevikus midagi veel tuleb
        # FeedLogic laisk initsialiseerimine
        self.feed_logic = None
        self._current_where = None
        self._current_tags_ids = None
        self._status_preferences_loaded = False
        self._tags_preferences_loaded = False
        # Guard flag to avoid double scheduling during initial activation
        self._suppress_filter_events = False

        # lisatud pillide loogika
        self.overdue_pills = OverdueDueSoonPillsWidget()
        
        self.overdue_pills_logic = OverdueDueSoonPillsLogic()
        self.overdue_pills_utils = OverdueDueSoonPillsUtils()


        # Correctly reference the PillOverdue button
        self.overdue_btn = self.overdue_pills.overdue_btn
        self.due_soon_btn = self.overdue_pills.due_soon_btn
        # Wire pill clicks to apply prebuilt WHERE filters
        try:
            self.overdue_btn.clicked.connect(self._on_overdue_clicked)
            self.due_soon_btn.clicked.connect(self._on_due_soon_clicked)
        except Exception:
            pass
    
        # Use toolbar_area provided by ModuleBaseUI (do not re-create)
        # Place overdue/due-soon pills on the right side of toolbar
        self.toolbar_area.add_right(self.overdue_pills)

        # Add status filter for projects
        self.status_filter = StatusFilterWidget(Module.PROJECT, self.toolbar_area, debug=is_global_debug())
        self.toolbar_area.register_filter_widget("status", self.status_filter)

        # Add tags filter for projects
        self.tags_filter = TagsFilterWidget(Module.PROJECT, self.lang_manager, self.toolbar_area, debug=is_global_debug())
        self.toolbar_area.register_filter_widget("tags", self.tags_filter)

        self.toolbar_area.filtersChanged.connect(self._on_filters_changed)
        

        self._refresh_helper = FilterRefreshHelper(self)
        refresh_widget = self._refresh_helper.make_filter_refresh_button(self.toolbar_area)
        self.toolbar_area.add_left(refresh_widget)

    # Do not load preferences here; defer to activate() for lazy loading

        self.feed_content = QWidget()
        self.feed_content.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        self.feed_layout = QVBoxLayout(self.feed_content)
        self.feed_layout.setContentsMargins(0, 0, 0, 0)
        self.feed_layout.setSpacing(8)

        self._empty_state = QLabel(self.lang_manager.translate("No projects found") if self.lang_manager else "No projects found")
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
        ThemeManager.apply_module_style(self._empty_state, [QssPaths.MODULE_CARD])
        ThemeManager.apply_module_style(self, [QssPaths.MODULES_MAIN])

    # --- Aktivatsioon / deaktiveerimine (ühine muster) ---
    def activate(self) -> None:
        super().activate()

        if self.feed_logic is None:
            kwargs = {}
            if self.BATCH_SIZE is not None:
                kwargs["batch_size"] = self.BATCH_SIZE
            self.feed_logic = self.FEED_LOGIC_CLS(self.BACKEND_ENTITY, self.QUERY_FILE, self.lang_manager, **kwargs)

        # Lazy-load filters and then apply saved preferences
        self._suppress_filter_events = True
        try:
            self.status_filter.ensure_loaded()
        except Exception:
            pass
        try:
            self.tags_filter.ensure_loaded()
        except Exception:
            pass
        
        # Apply saved preferences after filters are populated
        self._load_and_apply_status_preferences()
        self._load_and_apply_tags_preferences()

        # Build initial filters from stored preferences and load feed with them
        self._suppress_filter_events = False
        current_filters = {
            "status": (self.status_filter.selected_ids() if self.status_filter else []),
            "tags": (self.tags_filter.selected_ids() if self.tags_filter else []),
        }

        # Drive the initial load via the same path as user-driven filter changes
        self._on_filters_changed(current_filters)
        
        # Load overdue count values when the module is activated
        overdue_count = OverdueDueSoonPillsUtils.refresh_counts_for_module(Module.PROJECT)
        
        OverdueDueSoonPillsLogic.set_counts(overdue_count, self.overdue_btn, self.due_soon_btn)

    def deactivate(self) -> None:
        super().deactivate()

    # --- Andmete laadimine ---
    def load_next_batch(self):
        # Prepare variables for tag filtering
        tags_ids = getattr(self, '_current_tags_ids', None)
        def inject_has_tags(batch_loader):
            # Patch the feed logic's api_client to inject hasTags into variables
            orig_send_query = self.feed_logic.api_client.send_query
            def send_query_with_tags(query, variables=None, *args, **kwargs):
                if variables is None:
                    variables = {}
                # Inject hasTags if tags_ids present
                if tags_ids:
                    variables['hasTags'] = {
                        'column': 'ID',
                        'operator': 'IN',
                        'value': tags_ids
                    }
                return orig_send_query(query, variables, *args, **kwargs)
            self.feed_logic.api_client.send_query = send_query_with_tags
            try:
                return batch_loader()
            finally:
                self.feed_logic.api_client.send_query = orig_send_query
        return inject_has_tags(lambda: self.process_next_batch(retheme_func=self.retheme_projects))

    # --- Filtrid (ühine muster) ---
    def _on_filters_changed(self, filters: dict) -> None:
        # Suppress events during initial activation (when we programmatically populate filters)
        if self._suppress_filter_events:
            return
        #print(f"[ProjectsUi] _on_filters_changed called with filters: {filters}")
        if self.feed_load_engine and self.feed_load_engine.buffer is not None:
            self.feed_load_engine.buffer.clear()
        status_ids = filters.get("status") or []
        tags_ids = filters.get("tags") or []

        # Only status goes into where
        where = {"AND": []}
        if status_ids:
            where["AND"].append({"column": "STATUS", "operator": "IN", "value": status_ids})
        if not where["AND"]:
            where = None

        # Store filters for batch loader
        self._current_where = where
        self._current_tags_ids = tags_ids

        if self.feed_logic is None:
            kwargs = {}
            if self.BATCH_SIZE is not None:
                kwargs["batch_size"] = self.BATCH_SIZE
            self.feed_logic = self.FEED_LOGIC_CLS(self.BACKEND_ENTITY, self.QUERY_FILE, self.lang_manager, **kwargs)

        try:
            self.feed_logic.set_where(where)
        except Exception as e:
            log_debug(f"[ProjectsModule] set_where failed: {e}")

        self.clear_feed(self.feed_layout, self._empty_state)
        try:
            self.scroll_area.verticalScrollBar().setValue(0)
        except Exception:
            pass
        self.feed_load_engine.schedule_load()

        # Reset pill active states when filters change
        self.overdue_pills.set_overdue_active(False)
        self.overdue_pills.set_due_soon_active(False)


    def _base_filter_and_list(self) -> List[dict]:
        and_list: List[dict] = []
        try:
            status_ids = self.status_filter.selected_ids() if self.status_filter else []
            tags_ids = self.tags_filter.selected_ids() if hasattr(self, 'tags_filter') and self.tags_filter else []
            if status_ids:
                and_list.append({"column": "STATUS", "operator": "IN", "value": status_ids})
            if tags_ids:
                and_list.append({"column": "TAGS", "operator": "IN", "value": tags_ids})
        except Exception:
            pass
        #print(f"[ProjectsModule] _base_filter_and_list: {and_list}")
        return and_list

    def _get_base_where(self) -> dict:
        and_list = self._base_filter_and_list()
        return {"AND": and_list} if and_list else {}

    def _apply_where(self, where: dict) -> None:
        # Avoid re-applying the same WHERE repeatedly (prevents loops)
        if where == self._current_where:
            return
        if self.feed_logic is None:
            kwargs = {}
            if self.BATCH_SIZE is not None:
                kwargs["batch_size"] = self.BATCH_SIZE
            self.feed_logic = self.FEED_LOGIC_CLS(self.BACKEND_ENTITY, self.QUERY_FILE, self.lang_manager, **kwargs)
        try:
            self.feed_logic.set_where(where if where.get("AND") else None)
        except Exception as e:
            log_debug(f"[ProjectsModule] set_where (overdue/dueSoon) failed: {e}")
        # Clear current feed UI
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

    def _on_overdue_clicked(self):
        # Set pill active states and apply overdue filter
        self.overdue_pills.set_overdue_active(True)
        self.overdue_pills.set_due_soon_active(False)
        where = self.overdue_pills_utils.build_overdue_where()
        self._apply_where(where)

    def _on_due_soon_clicked(self):
        # Set pill active states and apply due soon filter
        self.overdue_pills.set_overdue_active(False)
        self.overdue_pills.set_due_soon_active(True)
        where = self.overdue_pills_utils.build_due_soon_where()
        self._apply_where(where)

    # --- Teema ---
    def retheme_projects(self) -> None:
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
