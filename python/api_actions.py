import json
from typing import List, Optional

from .api_client import APIClient
from .GraphQLQueryLoader import GraphQLQueryLoader
from ..languages.language_manager import LanguageManager
from ..languages.translation_keys import TranslationKeys
from ..Logs.python_fail_logger import PythonFailLogger
from ..utils.SessionManager import SessionManager
from ..utils.url_manager import Module
from .actions.file_actions import FileActions
from .actions.property_link_actions import PropertyLinkActions


class APIModuleActions(FileActions, PropertyLinkActions):
    """Entry point for the module actions; the file and property-link domains live in python/actions/."""
    _TASK_PRIORITY_DEFAULTS = ("URGENT", "HIGH", "MEDIUM", "LOW")
    _task_priority_values_cache: Optional[List[str]] = None

    @staticmethod
    def _geometry_input_value(geometry: dict) -> str:
        return json.dumps(geometry, ensure_ascii=False, separators=(",", ":"))

    @staticmethod
    def _is_unknown_input_field_error(message: str, field_name: str) -> bool:
        text = str(message or "").lower()
        field_text = str(field_name or "").strip().lower()
        if not field_text or field_text not in text:
            return False

        unknown_field_markers = (
            "unknown field",
            "not defined",
            "undefined field",
            "field is not defined",
            "does not exist on type",
            "did you mean",
        )
        return any(marker in text for marker in unknown_field_markers)

    @staticmethod
    def _is_unknown_geometry_input_error(message: str) -> bool:
        return APIModuleActions._is_unknown_input_field_error(message, "geometry")

    @staticmethod
    def _is_geometry_retryable_create_error(message: str) -> bool:
        text = str(message or "").lower()
        if APIModuleActions._is_unknown_geometry_input_error(message):
            return True

        retryable_markers = (
            "internal server error",
            "[wc-api][server]",
            "http 500",
            "http 502",
            "http 503",
            "http 504",
            "geojson",
            "json",
            "icon",
            "iconcolor",
        )
        return any(marker in text for marker in retryable_markers)

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
        status_module = APIModuleActions._status_module_value(module_name)
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
        if APIModuleActions._task_priority_values_cache and not force_refresh:
            return list(APIModuleActions._task_priority_values_cache)

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
                APIModuleActions._task_priority_values_cache = values
                return list(values)
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module=Module.TASK.value,
                event="task_priority_values_fetch_failed",
            )

        # The server refuses introspection, so do not resend a doomed request on every lookup.
        APIModuleActions._task_priority_values_cache = list(APIModuleActions._TASK_PRIORITY_DEFAULTS)
        return list(APIModuleActions._TASK_PRIORITY_DEFAULTS)

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

        for value in APIModuleActions.get_task_priority_values():
            options.append(
                {
                    "value": value,
                    "label": APIModuleActions.task_priority_label(value, lang_manager=lang),
                }
            )

        return options

    @staticmethod
    def get_current_user_payload() -> Optional[dict]:
        session = SessionManager()
        cached_user = session.loggedInUser
        if isinstance(cached_user, dict) and str(cached_user.get("id") or "").strip():
            return cached_user

        loader = GraphQLQueryLoader()
        query = loader.load_query_by_module(Module.USER.value, "me.graphql")
        client = APIClient()

        try:
            data = client.send_query(query) or {}
            user = (data.get("me") or {}) if isinstance(data, dict) else {}
            if isinstance(user, dict) and str(user.get("id") or "").strip():
                try:
                    session.loggedInUser = user
                    SessionManager.save_session()
                except Exception as cache_exc:
                    PythonFailLogger.log_exception(
                        cache_exc,
                        module=Module.USER.value,
                        event="current_user_cache_failed",
                    )
                return user
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module=Module.USER.value,
                event="current_user_fetch_failed",
            )

        return cached_user if isinstance(cached_user, dict) else None

    @staticmethod
    def get_current_user_id() -> str:
        user = APIModuleActions.get_current_user_payload() or {}
        return str(user.get("id") or "").strip() if isinstance(user, dict) else ""

    @staticmethod
    def user_display_name(user: Optional[dict]) -> str:
        if not isinstance(user, dict):
            return ""

        display_name = str(user.get("displayName") or "").strip()
        if display_name:
            return display_name

        first_name = str(user.get("firstName") or "").strip()
        last_name = str(user.get("lastName") or "").strip()
        full_name = " ".join(part for part in (first_name, last_name) if part).strip()
        if full_name:
            return full_name

        email = str(user.get("email") or "").strip()
        if email:
            return email

        return str(user.get("id") or "").strip()

    @staticmethod
    def get_assignable_users(limit: int = 100) -> list[dict[str, str]]:
        max_items = max(1, int(limit or 0))
        current_user = APIModuleActions.get_current_user_payload() or {}
        current_user_id = str(current_user.get("id") or "").strip()

        users_by_id: dict[str, dict[str, str]] = {}
        current_user_name = APIModuleActions.user_display_name(current_user)
        if current_user_id and current_user_name:
            users_by_id[current_user_id] = {
                "id": current_user_id,
                "displayName": current_user_name,
            }

        loader = GraphQLQueryLoader()
        client = APIClient()

        try:
            query = loader.load_query_by_module(Module.USER.value, "users.graphql")
            after: Optional[str] = None

            while len(users_by_id) < max_items:
                remaining = max_items - len(users_by_id)
                variables = {
                    "first": min(50, remaining),
                    "after": after,
                }
                data = client.send_query(query, variables=variables) or {}
                users_connection = (data.get("users") or {}) if isinstance(data, dict) else {}
                edges = users_connection.get("edges") or []
                if not isinstance(edges, list) or not edges:
                    break

                for edge in edges:
                    node = (edge or {}).get("node") or {}
                    if not isinstance(node, dict):
                        continue

                    user_id = str(node.get("id") or "").strip()
                    if not user_id:
                        continue

                    if str(node.get("deletedAt") or "").strip():
                        continue

                    display_name = APIModuleActions.user_display_name(node)
                    if not display_name:
                        continue

                    users_by_id[user_id] = {
                        "id": user_id,
                        "displayName": display_name,
                    }
                    if len(users_by_id) >= max_items:
                        break

                page_info = users_connection.get("pageInfo") or {}
                after = str(page_info.get("endCursor") or "").strip()
                if not page_info.get("hasNextPage") or not after:
                    break
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module=Module.USER.value,
                event="assignable_users_fetch_failed",
                extra={"limit": max_items},
            )

        users = list(users_by_id.values())
        users.sort(
            key=lambda item: (
                str(item.get("id") or "").strip() != current_user_id,
                str(item.get("displayName") or "").casefold(),
            )
        )
        return users

    @staticmethod
    def get_task_data(item_id: str) -> Optional[dict]:
        """Fetch the latest task payload from the backend."""

        task_id = str(item_id or "").strip()
        if not task_id:
            return None

        loader = GraphQLQueryLoader()
        query = loader.load_query_by_module(Module.TASK.value, "w_tasks_module_data_by_item_id.graphql")
        client = APIClient()

        try:
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

        cleaned = list(dict.fromkeys(str(item_id).strip() for item_id in (item_ids or []) if str(item_id).strip()))
        if not cleaned:
            return {}

        loader = GraphQLQueryLoader()
        query = loader.load_query_by_module(Module.TASK.value, "ListFilteredTasks.graphql")
        client = APIClient()

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

            tasks_conn = (data.get("tasks") or {}) if isinstance(data, dict) else {}
            edges = tasks_conn.get("edges") or []
            if not isinstance(edges, list):
                continue

            for edge in edges:
                node = (edge or {}).get("node") or {}
                if not isinstance(node, dict):
                    continue
                task_id = node.get("id")
                if task_id:
                    tasks[str(task_id)] = node

        return tasks

    @staticmethod
    def get_task_description(item_id: str) -> Optional[str]:
        """Fetch the latest task/asbuilt description from the backend."""

        task = APIModuleActions.get_task_data(item_id)
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

        loader = GraphQLQueryLoader()
        query = loader.load_query_by_module(Module.TASK.value, "updateTaskDescription.graphql")
        variables = {
            "input": {
                "id": task_id,
                "description": str(description or ""),
            }
        }

        client = APIClient()
        try:
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
    def _update_module_geometry(
        *,
        item_id: str,
        geometry: dict,
        module: str,
        query_filename: str,
        response_key: str,
        failure_event: str,
        empty_event: Optional[str] = None,
    ) -> bool:
        resolved_id = str(item_id or "").strip()
        if not resolved_id or not isinstance(geometry, dict):
            return False

        loader = GraphQLQueryLoader()
        query = loader.load_query_by_module(module, query_filename)
        variables = {
            "input": {
                "id": resolved_id,
                "geometry": APIModuleActions._geometry_input_value(geometry),
            }
        }

        client = APIClient()
        try:
            data = client.send_query(query, variables=variables) or {}
            updated = (data.get(response_key) or {}) if isinstance(data, dict) else {}
            if updated.get("id"):
                return True
            if empty_event:
                PythonFailLogger.log_exception(
                    RuntimeError(f"{response_key} geometry update returned no id"),
                    module=module,
                    event=empty_event,
                    extra={
                        "item_id": resolved_id,
                        "geometry_type": str(geometry.get("type") or ""),
                    },
                )
            return False
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module=module,
                event=failure_event,
                extra={"item_id": resolved_id},
            )
            return False

    @staticmethod
    def update_task_geometry(item_id: str, geometry: dict) -> bool:
        """Update the task geometry field in the backend."""

        return APIModuleActions._update_module_geometry(
            item_id=item_id,
            geometry=geometry,
            module=Module.TASK.value,
            query_filename="updateTaskGeometry.graphql",
            response_key="updateTask",
            failure_event="task_update_geometry_failed",
            empty_event="task_update_geometry_empty_response",
        )

    @staticmethod
    def update_project_geometry(item_id: str, geometry: dict) -> bool:
        """Update the project geometry field in the backend."""

        return APIModuleActions._update_module_geometry(
            item_id=item_id,
            geometry=geometry,
            module=Module.PROJECT.value,
            query_filename="updateProjectGeometry.graphql",
            response_key="updateProject",
            failure_event="project_update_geometry_failed",
        )

    @staticmethod
    def update_easement_geometry(item_id: str, geometry: dict) -> bool:
        """Update the easement geometry field in the backend."""

        return APIModuleActions._update_module_geometry(
            item_id=item_id,
            geometry=geometry,
            module=Module.EASEMENT.value,
            query_filename="updateEasementGeometry.graphql",
            response_key="updateEasement",
            failure_event="easement_update_geometry_failed",
        )

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

    @staticmethod
    def update_task_status(item_id: str, status_id: str) -> Optional[dict]:
        task_id = str(item_id or "").strip()
        resolved_status_id = str(status_id or "").strip()
        if not task_id or not resolved_status_id:
            return None

        loader = GraphQLQueryLoader()
        query = loader.load_query_by_module(Module.TASK.value, "updateTaskStatus.graphql")
        variables = {
            "input": {
                "id": task_id,
                "status": resolved_status_id,
            }
        }

        client = APIClient()
        try:
            data = client.send_query(query, variables=variables) or {}
            updated = (data.get("updateTask") or {}) if isinstance(data, dict) else {}
            return updated if isinstance(updated, dict) and updated.get("id") else None
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module=Module.TASK.value,
                event="task_update_status_failed",
                extra={"item_id": task_id, "status_id": resolved_status_id},
            )
            return None

    @staticmethod
    def update_task_members(item_id: str, members_associate: List[object]) -> bool:
        task_id = str(item_id or "").strip()
        associate_payload = [member for member in (members_associate or []) if member]
        if not task_id or not associate_payload:
            return False

        loader = GraphQLQueryLoader()
        query = loader.load_query_by_module(Module.TASK.value, "updateTaskMembers.graphql")
        variables = {
            "input": {
                "id": task_id,
                "members": {
                    "associate": associate_payload,
                },
            }
        }

        client = APIClient()
        try:
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
        cleaned_member_ids = list(
            dict.fromkeys(
                str(member_id).strip()
                for member_id in (member_ids or [])
                if str(member_id).strip()
            )
        )
        selected_responsible_id = str(responsible_id or "").strip()

        payload: list[dict[str, object]] = []
        for member_id in cleaned_member_ids:
            member_payload: dict[str, object] = {"id": member_id}
            if include_responsible_flag and selected_responsible_id:
                member_payload["responsible"] = member_id == selected_responsible_id
            payload.append(member_payload)

        return payload

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
    ) -> Optional[str]:
        task_title = str(title or "").strip()
        task_type_id = str(type_id or "").strip()
        if not task_title or not task_type_id:
            return None

        current_user_id = APIModuleActions.get_current_user_id()
        effective_responsible_id = str(responsible_id or "").strip() or current_user_id
        cleaned_members = list(
            dict.fromkeys(
                member_id
                for member_id in [
                    effective_responsible_id,
                    current_user_id,
                    *[
                        str(member_id).strip()
                        for member_id in (member_ids or [])
                        if str(member_id).strip()
                    ],
                ]
                if member_id
            )
        )
        member_payload = APIModuleActions._build_task_member_associate_payload(
            cleaned_members,
            responsible_id=effective_responsible_id,
            include_responsible_flag=True,
        )
        fallback_member_payload = APIModuleActions._build_task_member_associate_payload(
            cleaned_members,
            include_responsible_flag=False,
        )

        loader = GraphQLQueryLoader()
        query = loader.load_query_by_module(Module.TASK.value, "createTask.graphql")

        status_payload = str(status_id or "").strip()
        geometry_payload = geometry if isinstance(geometry, dict) else None

        def _build_task_input(
            associate_payload: Optional[List[object]],
            *,
            include_geometry: bool = True,
            include_status: bool = True,
        ) -> dict:
            task_input = {
                "title": task_title,
                "typeId": task_type_id,
            }
            if description is not None:
                task_input["description"] = str(description or "")
            if priority:
                task_input["priority"] = str(priority).strip().upper()
            if start_at:
                task_input["startAt"] = str(start_at)
            if due_at:
                task_input["dueAt"] = str(due_at)
            if include_status and status_payload:
                task_input["status"] = status_payload
            if include_geometry and geometry_payload is not None:
                task_input["geometry"] = APIModuleActions._geometry_input_value(geometry_payload)
            if associate_payload:
                task_input["members"] = {"associate": associate_payload}
            return task_input

        def _is_status_retryable_create_error(message: str) -> bool:
            return bool(status_payload) and APIModuleActions._is_unknown_input_field_error(message, "status")

        def _send_create(
            associate_payload: Optional[List[object]],
            *,
            include_geometry: bool,
            include_status: bool,
        ) -> dict:
            return client.send_query(
                query,
                variables={
                    "input": _build_task_input(
                        associate_payload,
                        include_geometry=include_geometry,
                        include_status=include_status,
                    )
                },
            ) or {}

        client = APIClient()
        try:
            associate_payload = member_payload
            include_geometry = True
            include_status = bool(status_payload)
            used_fallback_payload = False
            sent_status_in_create = False
            attempted_states: set[tuple[str, bool, bool]] = set()

            while True:
                payload_kind = "fallback_members" if used_fallback_payload else "members"
                state = (payload_kind, include_geometry, include_status)
                if state in attempted_states:
                    raise RuntimeError("Create task retry loop exhausted")
                attempted_states.add(state)

                try:
                    data = _send_create(
                        associate_payload,
                        include_geometry=include_geometry,
                        include_status=include_status,
                    )
                    sent_status_in_create = bool(include_status and status_payload)
                    break
                except Exception as create_exc:
                    message = str(create_exc or "")
                    should_retry_without_status = include_status and _is_status_retryable_create_error(message)
                    should_retry_without_flag = (
                        bool(associate_payload)
                        and associate_payload == member_payload
                        and member_payload != fallback_member_payload
                        and "members.associate" in message
                        and "responsible" in message
                    )
                    should_retry_without_geometry = (
                        include_geometry
                        and geometry_payload is not None
                        and APIModuleActions._is_geometry_retryable_create_error(message)
                    )

                    if should_retry_without_status:
                        include_status = False
                        continue
                    if should_retry_without_flag:
                        associate_payload = fallback_member_payload
                        used_fallback_payload = True
                        continue
                    if should_retry_without_geometry:
                        include_geometry = False
                        continue
                    raise

            created = (data.get("createTask") or {}) if isinstance(data, dict) else {}
            task_id = created.get("id")
            task_id_text = str(task_id) if task_id else None
            if task_id_text and used_fallback_payload and effective_responsible_id and member_payload:
                APIModuleActions.update_task_members(task_id_text, member_payload)
            if task_id_text and status_payload and not sent_status_in_create:
                APIModuleActions.update_task_status(task_id_text, status_payload)

            return task_id_text
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module=Module.TASK.value,
                event="task_create_failed",
                extra={"title": task_title, "type_id": task_type_id},
            )
            return None
