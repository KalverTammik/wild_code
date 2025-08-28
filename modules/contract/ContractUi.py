# -*- coding: utf-8 -*-
"""
Contracts module UI – residentne muster ModuleBaseUI peal.
Erinevus teiste moodulitega: FEED_LOGIC klass, pealkiri, ning TYPE filter ON lubatud.
"""

from typing import Optional, Type, List, Any  

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QScrollArea, QSizePolicy, QLabel, QFrame

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





class ContractUi(ModuleBaseUI):

    NAME = "ContractModule"
    TITLE_KEY = "Contracts"
    MODULE_ENUM = Module.CONTRACT
    FEED_LOGIC_CLS: Type[FeedLogic] = FeedLogic
    BACKEND_ENTITY = "CONTRACT"
    QUERY_FILE = "ListFilteredContracts.graphql"
    USE_TYPE_FILTER = True
    BATCH_SIZE = DEFAULT_BATCH_SIZE


    def __init__(
        self,
        name: str = NAME,                          # kui sul NAME klassikonstant on; muidu eemalda
        lang_manager: Optional[LanguageManager] = None,

        theme_manager=None,
        parent: Optional[QWidget] = None,
        theme_dir: Optional[str] = None,           # <-- lisatud
        qss_files: Optional[List[str]] = None,     # <-- lisatud
        **kwargs: Any                              # <-- lisatud
    ) -> None:
        super().__init__(parent)

        self.name = name
        self.setObjectName(name)
        self.lang_manager = lang_manager
        self.theme_manager = theme_manager

        # lisatud, et dialog.py saaks edasi anda:
        self.theme_dir = theme_dir
        self.qss_files = qss_files
        self._extra_init_kwargs = kwargs

        self.feed_logic = None
        self._current_where = None

        # --- Toolbar & filtrid (ühtne muster) ---
        title = self.lang_manager.translate(self.TITLE_KEY) if self.lang_manager else self.TITLE_KEY
        self.toolbar_area.set_title(title)

        try:
            self.status_filter = StatusFilterWidget(self.MODULE_ENUM, self.lang_manager, self.toolbar_area, debug=is_global_debug())
            self.toolbar_area.register_filter_widget("status", self.status_filter)

            # Move the global refresh button next to the status filter for consistent UX
            try:
                tb = getattr(self, 'toolbar_area', None)
                refresh_btn = getattr(self, '_refresh_button', None)
                if tb and refresh_btn and hasattr(tb, '_left_layout') and hasattr(tb, '_right_layout'):
                    try:
                        tb._right_layout.removeWidget(refresh_btn)
                    except Exception:
                        pass
                    insert_idx = None
                    for i in range(tb._left_layout.count()):
                        w = tb._left_layout.itemAt(i).widget()
                        if w is self.status_filter:
                            insert_idx = i
                            break
                    if insert_idx is None:
                        tb._left_layout.addWidget(refresh_btn)
                    else:
                        tb._left_layout.insertWidget(insert_idx + 1, refresh_btn)
            except Exception:
                pass

            self.type_filter = None
            if self.USE_TYPE_FILTER:
                self.type_filter = TypeFilterWidget(self.MODULE_ENUM, self.lang_manager, self.toolbar_area, debug=is_global_debug())
                self.toolbar_area.register_filter_widget("type", self.type_filter)

            self.toolbar_area.filtersChanged.connect(self._on_filters_changed)
        except Exception as e:
            log_debug(f"[ContractUi] Toolbar init failed: {e}")

        # --- Feed container & layout (ühine muster) ---
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
        if self.theme_manager:
            try:
                ThemeManager.apply_module_style(self._empty_state, [QssPaths.MODULE_CARD])
                ThemeManager.apply_module_style(self, [QssPaths.MODULES_MAIN])
            except Exception:
                pass

    # --- Aktivatsioon / deaktiveerimine (ühine muster) ---
    def activate(self) -> None:
        super().activate()

        if self.feed_logic is None:
            kwargs = {}
            if self.BATCH_SIZE is not None:
                kwargs["batch_size"] = self.BATCH_SIZE
            self.feed_logic = self.FEED_LOGIC_CLS(self.BACKEND_ENTITY, self.QUERY_FILE, self.lang_manager, **kwargs)

        # (valikuline) eellae filtrite sisud
        try:
            if self.status_filter:
                self.status_filter.ensure_loaded()
            if self.type_filter:
                self.type_filter.ensure_loaded()
        except Exception:
            pass

        self.feed_load_engine.schedule_load()

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

        where = {"AND": []}
        status_ids = filters.get("status") or []
        type_ids = filters.get("type") or []


        if status_ids:
            where["AND"].append({"column": "STATUS", "operator": "IN", "value": status_ids})
        if self.USE_TYPE_FILTER and type_ids:
            where["AND"].append({"column": "TYPE", "operator": "IN", "value": type_ids})
        if not where["AND"]:
            where = None

        if where == self._current_where:
            return

        self._current_where = where

        if self.feed_logic is None:
            kwargs = {}
            if self.BATCH_SIZE is not None:
                kwargs["batch_size"] = self.BATCH_SIZE
            self.feed_logic = self.FEED_LOGIC_CLS(self.BACKEND_ENTITY, self.QUERY_FILE, self.lang_manager, **kwargs)

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
        if self.theme_manager:
            try:
                # Apply main module styling
                ThemeManager.apply_module_style(self, [QssPaths.MODULES_MAIN])

                # Apply styling to key child areas that need theme updates
                if hasattr(self, 'display_area') and self.display_area:
                    ThemeManager.apply_module_style(self.display_area, [QssPaths.MODULES_MAIN])

                if hasattr(self, 'footer_area') and self.footer_area:
                    ThemeManager.apply_module_style(self.footer_area, [QssPaths.MODULES_MAIN])

                if hasattr(self, 'toolbar_area') and self.toolbar_area:
                    ThemeManager.apply_module_style(self.toolbar_area, [QssPaths.MODULES_MAIN])
            except Exception:
                pass

        # Retheme existing cards in the display area
        try:
            if hasattr(self, 'display_area') and self.display_area:
                for card in self.display_area.findChildren(QWidget):
                    if hasattr(card, 'retheme') and callable(card.retheme):
                        try:
                            card.retheme()
                        except Exception:
                            # Fallback: apply ModuleCard styling if retheme fails
                            ThemeManager.apply_module_style(card, [QssPaths.MODULE_CARD])
                    # Update shadow colors for QFrame cards
                    elif isinstance(card, QFrame) and card.graphicsEffect():
                        from PyQt5.QtGui import QGraphicsDropShadowEffect, QColor
                        effect = card.graphicsEffect()
                        if isinstance(effect, QGraphicsDropShadowEffect):
                            try:
                                from ...widgets.theme_manager import ThemeManager
                                theme = ThemeManager.load_theme_setting()
                                shadow_color = QColor(255, 255, 255, 90) if theme == 'dark' else QColor(0, 0, 0, 120)
                                effect.setColor(shadow_color)
                            except Exception:
                                pass
        except Exception:
            pass

    # --- Module contract ---
    def get_widget(self) -> QWidget:
        return self
