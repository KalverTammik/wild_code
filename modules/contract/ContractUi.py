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
from ...widgets.OverdueDueSoonPillsWidget import OverduePillsMixin
from ...widgets.filter_refresh_helper import FilterRefreshHelper
from ...utils.FilterHelpers.FilterHelper import FilterHelper, FilterRefreshService
from ...utils.search.SearchOpenItemMixin import SearchOpenItemMixin

class ContractsModule(SearchOpenItemMixin, OverduePillsMixin, ModuleBaseUI):

    FEED_LOGIC_CLS: Type[FeedLogic] = FeedLogic
    QUERY_FILE = "ListFilteredContracts.graphql"
    SINGLE_ITEM_QUERY_FILE = "w_contracts_module_data_by_item_id.graphql"

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
        self.setObjectName(self.module_key)

        self.lang_manager = lang_manager
        self.theme_manager = ThemeManager()

        types, statuses, tags, archive_layer = ModuleManager().getModuleSupports(Module.CONTRACT.name) or {}
        self.supports_status_filter = statuses
        self.supports_type_filter = types
        self.supports_tags_filter = tags

        # lisatud, et dialog.py saaks edasi anda:
        self.qss_files = qss_files
        self.feed_logic = None
        self._status_preferences_loaded = False
        self._type_preferences_loaded = False
        self._suppress_filter_events = False

        self.wire_overdue_pills(self.toolbar_area)

        # Register filters (status + optional type)
        if self.supports_status_filter:
            self.status_filter = StatusFilterWidget(self.module_key, self.toolbar_area)
            self.toolbar_area.add_left(self.status_filter)
            self.status_filter.selectionChanged.connect(self._on_status_filter_selection)

        self.type_filter = None
        if self.supports_type_filter:
            self.type_filter = TypeFilterWidget(self.module_key, self.toolbar_area)
            self.toolbar_area.add_left(self.type_filter)
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

        self.retheme_contract()

        # Configure optional single-item query for opening a contract by id
        try:
            if self.feed_logic is None:
                self.feed_logic = self.FEED_LOGIC_CLS(self.module_key, self.QUERY_FILE, self.lang_manager)
            self.feed_logic.configure_single_item_query(self.SINGLE_ITEM_QUERY_FILE)
        except Exception:
            pass

    def activate(self) -> None:
        super().activate()
        self._refresh_filters()

        # Load overdue/due-soon counts for the module and apply to buttons
        self.refresh_overdue_counts(Module.CONTRACT)

    def deactivate(self) -> None:
        super().deactivate()


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
        FilterRefreshService.refresh_filters(
            self,
            status_ids=status_ids,
            type_ids=type_ids,
            tags_ids=tags_ids,
            status_filter=self.status_filter,
            type_filter=self.type_filter,
            tags_filter=self.tags_filter,
        )

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
