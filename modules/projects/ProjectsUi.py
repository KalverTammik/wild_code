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
from ...widgets.OverdueDueSoonPillsWidget import  OverduePillsMixin
from ...widgets.filter_refresh_helper import FilterRefreshHelper
from ...utils.FilterHelpers.FilterHelper import FilterHelper, FilterRefreshService
from ...utils.search.SearchOpenItemMixin import SearchOpenItemMixin


class ProjectsModule(SearchOpenItemMixin, OverduePillsMixin, ModuleBaseUI):

    FEED_LOGIC_CLS: Type[FeedLogic] = FeedLogic
    QUERY_FILE = "ListFilteredProjects.graphql"
    SINGLE_ITEM_QUERY_FILE = "w_projects_module_data_by_item_id.graphql"

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

        supports_types, supports_statuses, supports_tags, supports_archive_layer = ModuleManager().getModuleSupports(Module.PROJECT.name) or {}
        
        


        # edasiandmiseks
        self.qss_files = qss_files

        # Feed/filters state
        self.feed_logic = None
        self._current_where = None
        self._status_preferences_loaded = False
        self._tags_preferences_loaded = False
        self._suppress_filter_events = False

        self.wire_overdue_pills(self.toolbar_area)

        # Status filter (kasuta module_key)
        if supports_statuses:
            self.status_filter = StatusFilterWidget(self.module_key, self.toolbar_area)
            self.toolbar_area.add_left(self.status_filter)
            self.status_filter.selectionChanged.connect(self._on_status_filter_selection)

        # Tags filter (see näib eeldavat Module enum'i; jätame nii)
        if supports_tags:
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

        if self.feed_logic is None:
            self.feed_logic = self.FEED_LOGIC_CLS(self.module_key, self.QUERY_FILE, self.lang_manager)
        self.feed_logic.configure_single_item_query(self.SINGLE_ITEM_QUERY_FILE)

    # --- Aktivatsioon / deaktiveerimine ---
    def activate(self) -> None:
        super().activate()

        self._refresh_filters()
        self.refresh_overdue_counts(Module.PROJECT)


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
        return self.process_next_batch(retheme_func=self.retheme_projects)

    # --- Filtrid ---
    def _on_status_filter_selection(self, _texts: List[str], ids: List[str]) -> None:
        self._refresh_filters(status_ids=ids)

    def _on_tags_filter_selection(self, _texts: List[str], ids: List[str]) -> None:
        self._refresh_filters(tags_ids=ids)

    def _refresh_filters(self, *, status_ids: Optional[List[str]] = None, tags_ids: Optional[List[str]] = None) -> None:
        FilterRefreshService.refresh_filters(
            self,
            status_ids=status_ids,
            tags_ids=tags_ids,
            status_filter=self.status_filter,
            tags_filter=self.tags_filter,
            reset_overdue_pills=True,
        )



    # --- Teema ---
    def retheme_projects(self) -> None:

        for card in self.scroll_area.findChildren(QFrame, "ModuleInfoCard"):
            ThemeManager.apply_module_style(card, [QssPaths.MODULE_CARD])
            styleExtras.apply_chip_shadow(card)

    # --- Module contract ---
    def get_widget(self) -> QWidget:
        return self

