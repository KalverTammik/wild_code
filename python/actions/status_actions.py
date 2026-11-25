"""Status actions: the statuses of a module, and reading and changing the status of one item."""
from dataclasses import dataclass
from typing import List, Optional

from ..api_client import APIClient
from ..GraphQLQueryLoader import GraphQLQueryLoader
from ...Logs.python_fail_logger import PythonFailLogger
from ...constants.module_names import Module, backend_module


@dataclass(frozen=True)
class _ItemStatusQueries:
    """The GraphQL documents that read and change the status of one Kavitro entity."""

    update_file: str
    update_root: str
    read_file: Optional[str] = None
    read_root: Optional[str] = None


class StatusActions:
    """Static status actions; APIModuleActions inherits them so callers keep one entry point."""

    # Keyed by the Kavitro entity (backend_module), so every task section (works, as-built, ...) shares the "task" row.
    # An entity that gains a status read or change is added here with its .graphql files.
    _ITEM_STATUS_QUERIES = {
        Module.TASK.value: _ItemStatusQueries("updateTaskStatus.graphql", "updateTask"),
        Module.PROJECT.value: _ItemStatusQueries("updateProjectStatus.graphql", "updateProject"),
        Module.CONTRACT.value: _ItemStatusQueries("updateContractStatus.graphql", "updateContract"),
        Module.COORDINATION.value: _ItemStatusQueries("updateCoordinationStatus.graphql", "updateCoordination"),
        Module.EASEMENT.value: _ItemStatusQueries(
            "updateEasementStatus.graphql", "updateEasement", "easementStatus.graphql", "easement",
        ),
    }

    @staticmethod
    def status_module_value(module: str) -> str:
        """The MODULE value the statuses of a plugin module are filed under in Kavitro ("TASKS" for a task section)."""
        module_name = backend_module(module)
        if not module_name:
            return ""
        if module_name == Module.PROPERTY.value:
            return "PROPERTIES"
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
        status_module = StatusActions.status_module_value(module_name)
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
    def can_update_status(module: str) -> bool:
        """True when the status of this module's items can be changed from the plugin."""
        return backend_module(module) in StatusActions._ITEM_STATUS_QUERIES

    @staticmethod
    def get_item_status(module: str, item_id: str) -> Optional[dict]:
        """Return the status the item has in Kavitro now, or None when it cannot be read or the module has no status read."""

        entity = backend_module(module)
        queries = StatusActions._ITEM_STATUS_QUERIES.get(entity)
        item_id_text = str(item_id or "").strip()
        if queries is None or not queries.read_file or not queries.read_root or not item_id_text:
            return None

        loader = GraphQLQueryLoader()
        client = APIClient()
        try:
            query = loader.load_query_by_module(entity, queries.read_file)
            data = client.send_query(query, variables={"id": item_id_text}) or {}
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module=entity,
                event=f"{entity}_status_fetch_failed",
                extra={"item_id": item_id_text},
            )
            return None

        item = (data.get(queries.read_root) or {}) if isinstance(data, dict) else {}
        status = item.get("status") if isinstance(item, dict) else None
        return status if isinstance(status, dict) and str(status.get("id") or "").strip() else None

    @staticmethod
    def update_item_status(module: str, item_id: str, status_id: str) -> Optional[dict]:
        """Change the item status in Kavitro; returns the updated item (id, updatedAt, status), or None.

        None means Kavitro did not take the change, the module has no status change, or the request failed.
        """

        entity = backend_module(module)
        queries = StatusActions._ITEM_STATUS_QUERIES.get(entity)
        item_id_text = str(item_id or "").strip()
        resolved_status_id = str(status_id or "").strip()
        if queries is None or not item_id_text or not resolved_status_id:
            return None

        variables = {"input": {"id": item_id_text, "status": resolved_status_id}}
        extra = {"item_id": item_id_text, "status_id": resolved_status_id}

        loader = GraphQLQueryLoader()
        client = APIClient()
        try:
            query = loader.load_query_by_module(entity, queries.update_file)
            data = client.send_query(query, variables=variables) or {}
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module=entity,
                event=f"{entity}_update_status_failed",
                extra=extra,
            )
            return None

        updated = (data.get(queries.update_root) or {}) if isinstance(data, dict) else {}
        status = updated.get("status") if isinstance(updated, dict) else None
        # An answer with another status means Kavitro did not take the change.
        if (
            isinstance(updated, dict)
            and updated.get("id")
            and isinstance(status, dict)
            and str(status.get("id") or "").strip() == resolved_status_id
        ):
            return updated
        PythonFailLogger.log_exception(
            RuntimeError(f"{queries.update_root} did not return the requested status"),
            module=entity,
            event=f"{entity}_update_status_not_applied",
            extra=extra,
        )
        return None
