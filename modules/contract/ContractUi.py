# -*- coding: utf-8 -*-
"""
Contracts module UI – residentne muster ModuleBaseUI peal.
Erinevus teiste moodulitega: FEED_LOGIC klass, pealkiri, ning TYPE filter ON lubatud.
"""

from typing import Optional, Type, List

from PyQt5.QtWidgets import QWidget

from ...ui.ModuleBaseUI import ModuleBaseUI
from ...ui.mixins.filtered_feed_mixin import FilteredFeedMixin
from ...utils.url_manager import Module
from ...feed.FeedLogic import UnifiedFeedLogic as FeedLogic
from ...widgets.OverdueDueSoonPillsWidget import OverduePillsMixin
from ...utils.search.SearchOpenItemMixin import SearchOpenItemMixin
from ...languages.translation_keys import TranslationKeys


class ContractsModule(SearchOpenItemMixin, OverduePillsMixin, FilteredFeedMixin, ModuleBaseUI):

    FEED_LOGIC_CLS: Type[FeedLogic] = FeedLogic
    QUERY_FILE = "ListFilteredContracts.graphql"
    SINGLE_ITEM_QUERY_FILE = "w_contracts_module_data_by_item_id.graphql"
    FILTER_EVENT_PREFIX = "contract"

    def __init__(
        self,
        name: Optional[str] = None,
        lang_manager: Optional[object] = None,
        parent: Optional[QWidget] = None,
        qss_files: Optional[List[str]] = None,
    ) -> None:
        super().__init__(parent)
        self._init_feed_module(Module.CONTRACT, lang_manager)
        self.wire_overdue_pills(self.toolbar_area, lang_manager=self.lang_manager)
        self._build_filters_and_feed(TranslationKeys.NO_CONTRACTS_FOUND)

        self.feed_logic = self.FEED_LOGIC_CLS(self.module_key, self.QUERY_FILE, self.lang_manager)
        self.feed_logic.configure_single_item_query(self.SINGLE_ITEM_QUERY_FILE)

    def on_first_visible(self) -> None:
        super().on_first_visible()
        self.refresh_overdue_counts(Module.CONTRACT)
