"""Status and priority actions: the statuses of a module, the task priority values and their labels, the easement status."""
from typing import List, Optional

from ..api_client import APIClient
from ..GraphQLQueryLoader import GraphQLQueryLoader
from ...languages.language_manager import LanguageManager
from ...languages.translation_keys import TranslationKeys
from ...Logs.python_fail_logger import PythonFailLogger
from ...constants.module_names import Module


class StatusActions:
    """Static status, priority and easement status actions; APIModuleActions inherits them so callers keep one entry point."""
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
    def get_module_status_options(
        module_name: str,
        *,
        limit: int = 100,
        raise_on_error: bool = False,
    ) -> List[dict[str, object]]:
        """Statuses of the module, sorted; a failed read is logged and gives [] unless raise_on_error is set.

        raise_on_error=True re-raises the failure without logging it, for a caller that shows the error
        itself (the status filter's worker, which logs it); the other callers treat [] as "no statuses"
        and keep the default.
        """
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
            if raise_on_error:
                # The caller logs what it receives; logging here as well would write the failure twice.
                raise
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

    @staticmethod
    def get_easement_status(item_id: str) -> Optional[dict]:
        """Return the status the easement has in Kavitro now, or None when it cannot be read."""

        easement_id = str(item_id or "").strip()
        if not easement_id:
            return None

        loader = GraphQLQueryLoader()
        client = APIClient()
        try:
            query = loader.load_query_by_module(Module.EASEMENT.value, "easementStatus.graphql")
            data = client.send_query(query, variables={"id": easement_id}) or {}
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module=Module.EASEMENT.value,
                event="easement_status_fetch_failed",
                extra={"item_id": easement_id},
            )
            return None

        easement = (data.get("easement") or {}) if isinstance(data, dict) else {}
        status = easement.get("status") if isinstance(easement, dict) else None
        return status if isinstance(status, dict) and str(status.get("id") or "").strip() else None

    @staticmethod
    def update_easement_status(item_id: str, status_id: str) -> Optional[dict]:
        """Change the easement status in Kavitro; returns the status Kavitro saved, or None."""

        easement_id = str(item_id or "").strip()
        resolved_status_id = str(status_id or "").strip()
        if not easement_id or not resolved_status_id:
            return None

        variables = {
            "input": {
                "id": easement_id,
                "status": resolved_status_id,
            }
        }
        extra = {"item_id": easement_id, "status_id": resolved_status_id}

        loader = GraphQLQueryLoader()
        client = APIClient()
        try:
            query = loader.load_query_by_module(Module.EASEMENT.value, "updateEasementStatus.graphql")
            data = client.send_query(query, variables=variables) or {}
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module=Module.EASEMENT.value,
                event="easement_update_status_failed",
                extra=extra,
            )
            return None

        updated = (data.get("updateEasement") or {}) if isinstance(data, dict) else {}
        status = updated.get("status") if isinstance(updated, dict) else None
        # An answer with another status means Kavitro did not take the change.
        if not isinstance(status, dict) or str(status.get("id") or "").strip() != resolved_status_id:
            PythonFailLogger.log_exception(
                RuntimeError("updateEasement did not return the requested status"),
                module=Module.EASEMENT.value,
                event="easement_update_status_not_applied",
                extra=extra,
            )
            return None
        return status
