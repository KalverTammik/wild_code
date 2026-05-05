from __future__ import annotations

from typing import Any

from ..feed.FeedLogic import UnifiedFeedLogic
from ..module_manager import ModuleManager
from ..modules.Settings.SettinsUtils.SettingsLogic import SettingsLogic
from ..utils.FilterHelpers.FilterHelper import FilterHelper
from ..utils.url_manager import ModuleSupports
from .OverdueDueSoonPillsWidget import OverdueDueSoonPillsUtils


class ModuleKpiService:
    @staticmethod
    def _fetch_count(
        module_key: str,
        query_name: str,
        lang_manager,
        where: dict[str, Any] | None,
        extra_args: dict[str, Any] | None,
        root_field: str | None = None,
    ) -> int:
        feed_logic = UnifiedFeedLogic(module_key, query_name, lang_manager, batch_size=1, root_field=root_field)
        feed_logic.set_where(where)
        if extra_args:
            feed_logic.set_extra_arguments(**extra_args)

        items = feed_logic.fetch_next_batch() or []
        if feed_logic.last_error is not None:
            raise feed_logic.last_error

        total_count = feed_logic.total_count
        if total_count is None:
            total_count = len(items)
        return max(0, int(total_count or 0))

    @staticmethod
    def _saved_filter_ids(module_key: str, support_key: str) -> list[str]:
        values = SettingsLogic().load_module_preference_ids(module_key, support_key=support_key) or []
        return [str(value).strip() for value in values if str(value).strip()]

    @staticmethod
    def _build_filters(module_key: str) -> tuple[dict[str, Any] | None, dict[str, Any], int]:
        supports = ModuleManager().getModuleSupports(module_key) or (False, False, False, False)
        supports_types, supports_statuses, supports_tags, _supports_archive = supports

        status_ids = ModuleKpiService._saved_filter_ids(module_key, ModuleSupports.STATUSES.value) if supports_statuses else []
        type_ids = ModuleKpiService._saved_filter_ids(module_key, ModuleSupports.TYPES.value) if supports_types else []
        tag_ids = ModuleKpiService._saved_filter_ids(module_key, ModuleSupports.TAGS.value) if supports_tags else []

        and_conditions: list[dict[str, Any]] = []
        if status_ids:
            and_conditions.append({"column": "STATUS", "operator": "IN", "value": status_ids})
        if type_ids:
            and_conditions.append({"column": "TYPE", "operator": "IN", "value": type_ids})

        where = {"AND": and_conditions} if and_conditions else None
        extra_args: dict[str, Any] = {}
        has_tags = FilterHelper.build_has_tags_condition(tag_ids)
        if has_tags:
            extra_args["hasTags"] = has_tags

        active_groups = sum(1 for ids in (status_ids, type_ids, tag_ids) if ids)
        return where, extra_args, active_groups

    @staticmethod
    def fetch_snapshot(
        module_key: str,
        query_name: str,
        lang_manager=None,
        *,
        root_field: str | None = None,
        include_due_counts: bool = True,
    ) -> dict[str, Any]:
        where, extra_args, active_groups = ModuleKpiService._build_filters(module_key)
        total_count = ModuleKpiService._fetch_count(
            module_key,
            query_name,
            lang_manager,
            where,
            extra_args,
            root_field=root_field,
        )

        overdue_count = 0
        due_soon_count = 0
        if include_due_counts and total_count > 0:
            overdue_where = OverdueDueSoonPillsUtils.build_overdue_where(where)
            due_soon_where = OverdueDueSoonPillsUtils.build_due_soon_where(where)
            overdue_count = ModuleKpiService._fetch_count(
                module_key,
                query_name,
                lang_manager,
                overdue_where,
                extra_args,
                root_field=root_field,
            )
            due_soon_count = ModuleKpiService._fetch_count(
                module_key,
                query_name,
                lang_manager,
                due_soon_where,
                extra_args,
                root_field=root_field,
            )

        return {
            "count": total_count,
            "overdue_count": overdue_count,
            "due_soon_count": due_soon_count,
            "filtered": bool(active_groups),
            "filter_groups": active_groups,
        }