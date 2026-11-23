"""Task actions: read and list tasks, change the description, status and members, and create a task."""
import re
from typing import Iterable, List, Optional

from ..api_client import APIClient
from ..GraphQLQueryLoader import GraphQLQueryLoader
from ...Logs.python_fail_logger import PythonFailLogger
from ...utils.api_error_handling import ApiError, ApiErrorKind
from ...constants.module_names import Module
from .geometry_actions import GeometryActions
from .user_actions import UserActions


def _clean_ids(values: Optional[Iterable[object]]) -> list[str]:
    """Stripped, non-empty ids without repeats, in their order; None is no id (str(None) would be "None")."""
    texts = (str(value).strip() for value in (values or []) if value is not None)
    return list(dict.fromkeys(text for text in texts if text))


class TaskActions:
    """Static task actions; APIModuleActions inherits them so callers keep one entry point.

    The geometry and current-user lookups go through GeometryActions and UserActions, so the
    domain classes do not inherit from each other.
    """

    @staticmethod
    def get_task_data(item_id: str) -> Optional[dict]:
        """Fetch the latest task payload from the backend."""

        task_id = str(item_id or "").strip()
        if not task_id:
            return None

        loader = GraphQLQueryLoader()
        client = APIClient()

        try:
            query = loader.load_query_by_module(Module.TASK.value, "w_tasks_module_data_by_item_id.graphql")
            data = client.send_query(query, variables={"id": task_id}) or {}
            task = (data.get("task") or {}) if isinstance(data, dict) else {}
            return task if isinstance(task, dict) and task else None
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module=Module.TASK.value,
                event="task_get_data_failed",
                extra={"item_id": task_id},
            )
            return None

    @staticmethod
    def get_tasks_by_ids(item_ids: List[str]) -> dict[str, dict]:
        """Fetch multiple tasks by id using the list query in small chunks."""

        cleaned = _clean_ids(item_ids)
        if not cleaned:
            return {}

        loader = GraphQLQueryLoader()
        client = APIClient()
        try:
            query = loader.load_query_by_module(Module.TASK.value, "ListFilteredTasks.graphql")
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module=Module.TASK.value,
                event="task_bulk_fetch_failed",
                extra={"count": len(cleaned)},
            )
            return {}

        chunk_size = 25
        tasks: dict[str, dict] = {}

        for start in range(0, len(cleaned), chunk_size):
            chunk = cleaned[start:start + chunk_size]
            variables = {
                "first": len(chunk),
                "after": None,
                "where": {
                    "AND": [
                        {
                            "column": "ID",
                            "operator": "IN",
                            "value": chunk,
                        }
                    ]
                },
            }

            try:
                data = client.send_query(query, variables=variables) or {}
            except Exception as exc:
                PythonFailLogger.log_exception(
                    exc,
                    module=Module.TASK.value,
                    event="task_bulk_fetch_failed",
                    extra={"count": len(chunk)},
                )
                continue

            tasks_conn = data.get("tasks") if isinstance(data, dict) else None
            edges = tasks_conn.get("edges") if isinstance(tasks_conn, dict) else None
            if not isinstance(edges, list):
                continue

            for edge in edges:
                node = edge.get("node") if isinstance(edge, dict) else None
                if not isinstance(node, dict):
                    continue
                task_id = node.get("id")
                if task_id:
                    tasks[str(task_id)] = node

        return tasks

    @staticmethod
    def get_task_description(item_id: str) -> Optional[str]:
        """Fetch the latest task/asbuilt description from the backend."""

        task = TaskActions.get_task_data(item_id)
        if not isinstance(task, dict):
            return None
        description = task.get("description")
        return str(description or "")

    @staticmethod
    def update_task_description(item_id: str, description: str) -> bool:
        """Update the task/asbuilt description field used as notes in the UI."""

        task_id = str(item_id or "").strip()
        if not task_id:
            return False

        variables = {
            "input": {
                "id": task_id,
                "description": str(description or ""),
            }
        }

        loader = GraphQLQueryLoader()
        client = APIClient()
        try:
            query = loader.load_query_by_module(Module.TASK.value, "updateTaskDescription.graphql")
            data = client.send_query(query, variables=variables) or {}
            updated = (data.get("updateTask") or {}) if isinstance(data, dict) else {}
            return bool(updated.get("id"))
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module=Module.TASK.value,
                event="task_update_description_failed",
                extra={"item_id": task_id},
            )
            return False

    @staticmethod
    def update_task_status(item_id: str, status_id: str) -> Optional[dict]:
        """Change the task status in Kavitro; returns the updated task, or None when Kavitro did not take the change."""

        task_id = str(item_id or "").strip()
        resolved_status_id = str(status_id or "").strip()
        if not task_id or not resolved_status_id:
            return None

        variables = {
            "input": {
                "id": task_id,
                "status": resolved_status_id,
            }
        }
        extra = {"item_id": task_id, "status_id": resolved_status_id}

        loader = GraphQLQueryLoader()
        client = APIClient()
        try:
            query = loader.load_query_by_module(Module.TASK.value, "updateTaskStatus.graphql")
            data = client.send_query(query, variables=variables) or {}
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module=Module.TASK.value,
                event="task_update_status_failed",
                extra=extra,
            )
            return None

        updated = (data.get("updateTask") or {}) if isinstance(data, dict) else {}
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
            RuntimeError("updateTask did not return the requested status"),
            module=Module.TASK.value,
            event="task_update_status_not_applied",
            extra=extra,
        )
        return None

    @staticmethod
    def update_task_members(item_id: str, members_associate: List[object]) -> bool:
        task_id = str(item_id or "").strip()
        associate_payload = [member for member in (members_associate or []) if member]
        if not task_id or not associate_payload:
            return False

        variables = {
            "input": {
                "id": task_id,
                "members": {
                    "associate": associate_payload,
                },
            }
        }

        loader = GraphQLQueryLoader()
        client = APIClient()
        try:
            query = loader.load_query_by_module(Module.TASK.value, "updateTaskMembers.graphql")
            data = client.send_query(query, variables=variables) or {}
            updated = (data.get("updateTask") or {}) if isinstance(data, dict) else {}
            return bool(updated.get("id"))
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module=Module.TASK.value,
                event="task_update_members_failed",
                extra={"item_id": task_id},
            )
            return False

    @staticmethod
    def _build_task_member_associate_payload(
        member_ids: Optional[List[str]],
        *,
        responsible_id: str = "",
        include_responsible_flag: bool = True,
    ) -> list[dict[str, object]]:
        selected_responsible_id = str(responsible_id or "").strip()

        payload: list[dict[str, object]] = []
        for member_id in _clean_ids(member_ids):
            member_payload: dict[str, object] = {"id": member_id}
            if include_responsible_flag and selected_responsible_id:
                member_payload["responsible"] = member_id == selected_responsible_id
            payload.append(member_payload)

        return payload

    @staticmethod
    def _server_refused_create(exc: Exception) -> bool:
        """True when the server answered and refused the create, so no task was made.

        After an HTTP 5xx error, a timeout or a lost connection it is unknown whether the
        task was created, so create_task does not retry with a simpler input then.
        """
        return isinstance(exc, ApiError) and exc.kind == ApiErrorKind.GRAPHQL

    @staticmethod
    def _is_property_input_error(message: str) -> bool:
        """True when a refused create names the properties input (its path, field or a property)."""
        text = str(message or "").lower()
        return "input.properties" in text or bool(re.search(r"(?<!\w)propert(?:y|ies)(?!\w)", text))

    @staticmethod
    def create_task(
        *,
        title: str,
        type_id: str,
        description: str = "",
        priority: Optional[str] = None,
        start_at: Optional[str] = None,
        due_at: Optional[str] = None,
        member_ids: Optional[List[str]] = None,
        responsible_id: Optional[str] = None,
        status_id: Optional[str] = None,
        geometry: Optional[dict] = None,
        property_ids: Optional[List[str]] = None,
    ) -> Optional[str]:
        """Create a task and return its id, or None.

        property_ids are linked in the same request, which saves a second mutation and its
        pacing wait; if the server refuses them, the task is created without them, so the
        caller checks the created task and links what is missing.
        """
        task_title = str(title or "").strip()
        task_type_id = str(type_id or "").strip()
        if not task_title or not task_type_id:
            return None

        current_user_id = UserActions.get_current_user_id()
        effective_responsible_id = str(responsible_id or "").strip() or current_user_id
        cleaned_members = _clean_ids([effective_responsible_id, current_user_id, *(member_ids or [])])
        member_payload = TaskActions._build_task_member_associate_payload(
            cleaned_members,
            responsible_id=effective_responsible_id,
            include_responsible_flag=True,
        )
        fallback_member_payload = TaskActions._build_task_member_associate_payload(
            cleaned_members,
            include_responsible_flag=False,
        )

        priority_text = str(priority or "").strip().upper()
        status_payload = str(status_id or "").strip()
        geometry_payload = geometry if isinstance(geometry, dict) else None
        cleaned_property_ids = _clean_ids(property_ids or [])

        def _build_task_input(
            associate_payload: Optional[List[object]],
            *,
            include_geometry: bool,
            include_status: bool,
            include_properties: bool,
        ) -> dict:
            task_input = {
                "title": task_title,
                "typeId": task_type_id,
            }
            if description is not None:
                task_input["description"] = str(description or "")
            if priority_text:
                task_input["priority"] = priority_text
            if start_at:
                task_input["startAt"] = str(start_at)
            if due_at:
                task_input["dueAt"] = str(due_at)
            if include_status:
                task_input["status"] = status_payload
            if include_geometry:
                task_input["geometry"] = GeometryActions._geometry_input_value(geometry_payload)
            if associate_payload:
                task_input["members"] = {"associate": associate_payload}
            if include_properties:
                task_input["properties"] = {"associate": cleaned_property_ids}
            return task_input

        loader = GraphQLQueryLoader()
        client = APIClient()
        try:
            query = loader.load_query_by_module(Module.TASK.value, "createTask.graphql")
            include_status = bool(status_payload)
            include_geometry = geometry_payload is not None
            include_properties = bool(cleaned_property_ids)
            flag_dropped = False

            # Every retry switches off the condition that allowed it, so at most three retries follow
            # the first send: without the status, without the responsible flag, without the geometry.
            while True:
                try:
                    data = client.send_query(
                        query,
                        variables={
                            "input": _build_task_input(
                                fallback_member_payload if flag_dropped else member_payload,
                                include_geometry=include_geometry,
                                include_status=include_status,
                                include_properties=include_properties,
                            )
                        },
                    ) or {}
                    break
                except Exception as create_exc:
                    if not TaskActions._server_refused_create(create_exc):
                        # The task may exist already; a changed retry could create a second one.
                        raise
                    message = str(create_exc).lower()
                    if include_status and GeometryActions._is_unknown_input_field_error(message, "status"):
                        include_status = False
                    elif (
                        not flag_dropped
                        and member_payload != fallback_member_payload
                        and "members.associate" in message
                        and "responsible" in message
                    ):
                        flag_dropped = True
                    elif include_geometry and GeometryActions._is_geometry_retryable_create_error(message):
                        include_geometry = False
                    elif include_properties and TaskActions._is_property_input_error(message):
                        include_properties = False
                    else:
                        raise

            created = (data.get("createTask") or {}) if isinstance(data, dict) else {}
            task_id = created.get("id")
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module=Module.TASK.value,
                event="task_create_failed",
                extra={"title": task_title, "type_id": task_type_id},
            )
            return None

        if not task_id:
            return None

        # The task exists now. A follow-up logs its own failure and never changes the result,
        # or the user would create the task a second time.
        task_id_text = str(task_id)
        if flag_dropped and effective_responsible_id:
            TaskActions.update_task_members(task_id_text, member_payload)
        if status_payload and not include_status:
            TaskActions.update_task_status(task_id_text, status_payload)

        return task_id_text
