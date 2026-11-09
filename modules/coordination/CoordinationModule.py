# -*- coding: utf-8 -*-
"""Coordination module UI – built on ModuleBaseUI."""

from typing import Optional, Type, List, Any
from PyQt5.QtWidgets import QWidget

from ...ui.ModuleBaseUI import ModuleBaseUI
from ...ui.mixins.filtered_feed_mixin import FilteredFeedMixin
from ...utils.url_manager import Module
from ...feed.FeedLogic import UnifiedFeedLogic as FeedLogic
from ...widgets.OverdueDueSoonPillsWidget import OverduePillsMixin
from ...utils.search.SearchOpenItemMixin import SearchOpenItemMixin
from ...languages.language_manager import LanguageManager
from ...languages.translation_keys import TranslationKeys


class CoordinationModule(SearchOpenItemMixin, OverduePillsMixin, FilteredFeedMixin, ModuleBaseUI):

    FEED_LOGIC_CLS: Type[FeedLogic] = FeedLogic
    QUERY_FILE = "ListFilteredCoordinations.graphql"
    SINGLE_ITEM_QUERY_FILE = "W_coordination_id.graphql"
    FILTER_EVENT_PREFIX = "coordination"

    def __init__(
        self,
        language: Optional[str] = None,
        parent: Optional[QWidget] = None,
        qss_files: Optional[List[str]] = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(parent)
        self._init_feed_module(Module.COORDINATION, language or LanguageManager())
        self.wire_overdue_pills(self.toolbar_area, lang_manager=self.lang_manager)
        self._build_filters_and_feed(TranslationKeys.NO_COORDINATIONS_FOUND)

    def on_first_visible(self) -> None:
        super().on_first_visible()
        self.refresh_overdue_counts(Module.COORDINATION)
