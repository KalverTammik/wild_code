# -*- coding: utf-8 -*-
"""
Projects module UI – residentne muster ModuleBaseUI peal.
Erinevus teiste moodulitega: FEED_LOGIC klass, pealkiri, ning TYPE filtrit ei kasutata.
"""

from typing import Optional, Type, List, Any
from PyQt5.QtWidgets import QWidget

from ...ui.ModuleBaseUI import ModuleBaseUI
from ...ui.mixins.filtered_feed_mixin import FilteredFeedMixin
from ...utils.url_manager import Module
from ...feed.FeedLogic import UnifiedFeedLogic as FeedLogic
from ...widgets.OverdueDueSoonPillsWidget import OverduePillsMixin
from ...utils.FilterHelpers.FilterHelper import FilterRefreshService
from ...utils.search.SearchOpenItemMixin import SearchOpenItemMixin
from ...languages.language_manager import LanguageManager
from ...languages.translation_keys import TranslationKeys


class ProjectsModule(SearchOpenItemMixin, OverduePillsMixin, FilteredFeedMixin, ModuleBaseUI):

    FEED_LOGIC_CLS: Type[FeedLogic] = FeedLogic
    QUERY_FILE = "ListFilteredProjects.graphql"
    SINGLE_ITEM_QUERY_FILE = "w_projects_module_data_by_item_id.graphql"
    FILTER_EVENT_PREFIX = "projects"

    def __init__(
        self,
        language: Optional[str] = None,
        parent: Optional[QWidget] = None,
        qss_files: Optional[List[str]] = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(parent)
        self._init_feed_module(Module.PROJECT, language or LanguageManager())
        self.wire_overdue_pills(self.toolbar_area, lang_manager=self.lang_manager)
        self._build_filters_and_feed(TranslationKeys.NO_PROJECTS_FOUND)

        self.feed_logic = self.FEED_LOGIC_CLS(self.module_key, self.QUERY_FILE, self.lang_manager)
        self.feed_logic.configure_single_item_query(self.SINGLE_ITEM_QUERY_FILE)

    def on_first_visible(self) -> None:
        super().on_first_visible()
        self.refresh_overdue_counts(Module.PROJECT)

    def _refresh_filters(
        self,
        *,
        status_ids: Optional[List[str]] = None,
        type_ids: Optional[List[str]] = None,
        tags_ids: Optional[List[str]] = None,
    ) -> None:
        # The shared clear button passes type_ids too; projects have no type filter.
        FilterRefreshService.refresh_filters(
            self,
            status_ids=status_ids,
            tags_ids=tags_ids,
            status_filter=self.status_filter,
            tags_filter=self.tags_filter,
            reset_overdue_pills=True,
        )
