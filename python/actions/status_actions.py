"""Status and priority actions: the statuses of a module, the task priority values and their labels."""
from typing import List, Optional

from ..api_client import APIClient
from ..GraphQLQueryLoader import GraphQLQueryLoader
from ...languages.language_manager import LanguageManager
from ...languages.translation_keys import TranslationKeys
from ...Logs.python_fail_logger import PythonFailLogger
from ...utils.url_manager import Module


class StatusActions:
    """Static status and priority actions; APIModuleActions inherits them so callers keep one entry point."""
    _TASK_PRIORITY_DEFAULTS = ("URGENT", "HIGH", "MEDIUM", "LOW")
    _task_priority_values_cache: Optional[List[str]] = None

    @staticmethod
    def _status_module_value(module: str) -> str:
        module_name = str(module or "").strip().lower()
        if not module_name:
            return ""
        if module_name == Module.PROPERTY.value:
            return "PROPERTIES"
        if module_name in (Module.TASK.value, Module.WORKS.value, Module.ASBUILT.value):
            return "TASKS"
        return f"{module_name.upper()}S"

    @staticmethod
    def get_module_status_options(module_name: str, *, limit: int = 100) -> List[dict[str, object]]:
        status_module = StatusActions._status_module_value(module_name)
        max_items = max(1, int(limit or 0))
        if not status_module:
            return []

        loader = GraphQLQueryLoader()
        client = APIClient()
        statuses_by_id: dict[str, dict[str, object]] = {}

        try:
            query = loader.load_query_by_module(Module.STATUSES.value, "ListModuleStatuses.graphql")
            after: Optional[str] = None

            while len(statuses_by_id) < max_items:
                remaining = max_items - len(statuses_by_id)
                variables = {
                    "first": min(50, remaining),
                    "after": after,
                    "where": {"column": "MODULE", "operator": "EQ", "value": status_module},
                }
                data = client.send_query(query, variables=variables) or {}
                statuses_connection = (data.get("statuses") or {}) if isinstance(data, dict) else {}
                edges = statuses_connection.get("edges") or []
                if not isinstance(edges, list) or not edges:
                    break

                for edge in edges:
                    node = (edge or {}).get("node") or {}
                    if not isinstance(node, dict):
                        continue

                    status_id = str(node.get("id") or "").strip()
                    name = str(node.get("name") or "").strip()
                    if not status_id or not name:
                        continue

                    statuses_by_id[status_id] = {
                        "id": status_id,
                        "name": name,
                        "color": str(node.get("color") or "cccccc").strip() or "cccccc",
                        "type": str(node.get("type") or "").strip().upper(),
                        "description": str(node.get("description") or "").strip(),
                        "isDefault": bool(node.get("isDefault")),
                        "sortOrder": node.get("sortOrder"),
                    }
                    if len(statuses_by_id) >= max_items:
                        break

                page_info = statuses_connection.get("pageInfo") or {}
                after = str(page_info.get("endCursor") or "").strip()
                if not page_info.get("hasNextPage") or not after:
                    break
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module=Module.STATUSES.value,
                event="module_statuses_fetch_failed",
                extra={"module": str(module_name or "")},
            )
            return []

        def _sort_key(option: dict[str, object]) -> tuple[int, str]:
            raw_sort = option.get("sortOrder")
            try:
                sort_value = int(raw_sort)
            except (TypeError, ValueError):
                sort_value = 0
            return (sort_value, str(option.get("name") or "").lower())

        return sorted(statuses_by_id.values(), key=_sort_key)

    @staticmethod
    def get_task_priority_values(*, force_refresh: bool = False) -> List[str]:
        if StatusActions._task_priority_values_cache and not force_refresh:
            return list(StatusActions._task_priority_values_cache)

        loader = GraphQLQueryLoader()
        client = APIClient()

        try:
            query = loader.load_query_by_module(Module.TASK.value, "taskPriorityEnum.graphql")
            data = client.send_query(query) or {}
            enum_payload = (data.get("__type") or {}) if isinstance(data, dict) else {}
            enum_values = enum_payload.get("enumValues") or []

            values = [
                str(item.get("name") or "").strip().upper()
                for item in enum_values
                if isinstance(item, dict) and str(item.get("name") or "").strip()
            ]
            if values:
                StatusActions._task_priority_values_cache = values
                return list(values)
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module=Module.TASK.value,
                event="task_priority_values_fetch_failed",
            )

        # The server refuses introspection, so do not resend a doomed request on every lookup.
        StatusActions._task_priority_values_cache = list(StatusActions._TASK_PRIORITY_DEFAULTS)
        return list(StatusActions._TASK_PRIORITY_DEFAULTS)

    @staticmethod
    def task_priority_label(priority: str, *, lang_manager=None) -> str:
        lang = lang_manager or LanguageManager()
        normalized = str(priority or "").strip().upper()
        if not normalized:
            return lang.translate(TranslationKeys.WORKS_PRIORITY_NONE)

        translation_map = {
            "URGENT": TranslationKeys.WORKS_PRIORITY_URGENT,
            "HIGH": TranslationKeys.WORKS_PRIORITY_HIGH,
            "MEDIUM": TranslationKeys.WORKS_PRIORITY_MEDIUM,
            "LOW": TranslationKeys.WORKS_PRIORITY_LOW,
        }
        translation_key = translation_map.get(normalized)
        if translation_key:
            return lang.translate(translation_key)

        return normalized.replace("_", " ").title()

    @staticmethod
    def get_task_priority_options(*, lang_manager=None, include_empty: bool = True) -> List[dict[str, str]]:
        lang = lang_manager or LanguageManager()
        options: List[dict[str, str]] = []

        if include_empty:
            options.append(
                {
                    "value": "",
                    "label": lang.translate(TranslationKeys.WORKS_PRIORITY_NONE),
                }
            )

        for value in StatusActions.get_task_priority_values():
            options.append(
                {
                    "value": value,
                    "label": StatusActions.task_priority_label(value, lang_manager=lang),
                }
            )

        return options
