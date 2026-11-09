# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import List, Optional

from PyQt5.QtWidgets import QWidget

from ...feed.FeedLogic import UnifiedFeedLogic as FeedLogic
from ...ui.ModuleBaseUI import ModuleBaseUI
from ...ui.mixins.filtered_feed_mixin import FilteredFeedMixin
from ...utils.FilterHelpers.FilterHelper import FilterRefreshService
from ...utils.search.SearchOpenItemMixin import SearchOpenItemMixin
from ...utils.url_manager import Module, ModuleSupports


class TaskModuleBaseUI(SearchOpenItemMixin, FilteredFeedMixin, ModuleBaseUI):
    FEED_LOGIC_CLS = FeedLogic
    FEED_MODULE_ENUM = Module.TASK
    FEED_ROOT_FIELD = "tasks"
    QUERY_FILE = "ListFilteredTasks.graphql"
    SINGLE_ITEM_QUERY_FILE = "w_tasks_module_data_by_item_id.graphql"
    FILTER_EVENT_PREFIX = "task_module"

    def __init__(
        self,
        *,
        module_enum: Module,
        empty_state_key: str,
        lang_manager: Optional[object] = None,
        parent: Optional[QWidget] = None,
        qss_files: Optional[List[str]] = None,
    ) -> None:
        super().__init__(parent)
        self._init_feed_module(module_enum, lang_manager)
        self.supports_tags_filter = False
        self._build_filters_and_feed(empty_state_key)

        self.feed_logic = self.FEED_LOGIC_CLS(
            self.FEED_MODULE_ENUM.value,
            self.QUERY_FILE,
            self.lang_manager,
            root_field=self.FEED_ROOT_FIELD,
        )
        self.feed_logic.configure_single_item_query(self.SINGLE_ITEM_QUERY_FILE)

        self.retheme()

    def _module_scope_type_ids(self) -> List[str]:
        ids = self._settings_logic.load_module_preference_ids(
            self.module_key,
            support_key=ModuleSupports.TYPES.value,
        )
        return [str(item_id) for item_id in (ids or []) if item_id]

    def _effective_type_ids(self, type_ids: Optional[List[str]]) -> List[str]:
        scope_ids = self._module_scope_type_ids()
        selected_ids = [str(item_id) for item_id in (type_ids or []) if item_id]

        if not scope_ids:
            return selected_ids

        if selected_ids:
            scope_set = set(scope_ids)
            return [item_id for item_id in selected_ids if item_id in scope_set]

        return scope_ids

    def _refresh_filters(
        self,
        *,
        status_ids: Optional[List[str]] = None,
        type_ids: Optional[List[str]] = None,
        tags_ids: Optional[List[str]] = None,
    ) -> None:
        # The shared clear button passes tags_ids too; task modules have no tags filter.
        effective_type_ids = self._effective_type_ids(type_ids)
        FilterRefreshService.refresh_filters(
            self,
            status_ids=status_ids,
            type_ids=effective_type_ids,
            tags_ids=None,
            status_filter=self.status_filter,
            type_filter=self.type_filter,
            tags_filter=None,
        )
