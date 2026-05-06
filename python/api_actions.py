import os
from typing import List, Optional, Set
import requests

from .api_client import APIClient

from .GraphQLQueryLoader import GraphQLQueryLoader
from ..languages.language_manager import LanguageManager
from ..languages.translation_keys import TranslationKeys
from ..Logs.python_fail_logger import PythonFailLogger
from .responses import JsonResponseHandler
from ..utils.SessionManager import SessionManager
from ..utils.url_manager import Module


_PROPERTIES_PAGE_SIZE = 50

class APIModuleActions:
    _TASK_PRIORITY_DEFAULTS = ("URGENT", "HIGH", "MEDIUM", "LOW")
    _task_priority_values_cache: Optional[List[str]] = None

    @staticmethod
    def _property_owner_module(module: str) -> str:
        module_name = str(module or "").strip().lower()
        if module_name in (Module.TASK.value, Module.WORKS.value, Module.ASBUILT.value):
            return Module.TASK.value
        return module_name

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
    def _file_owner_module(module: str) -> str:
        module_name = str(module or "").strip().lower()
        if module_name in (Module.TASK.value, Module.WORKS.value, Module.ASBUILT.value):
            return Module.TASK.value
        return module_name

    @staticmethod
    def _file_model_type(module: str) -> str:
        owner = APIModuleActions._file_owner_module(module)
        if not owner:
            return ""
        return str(owner).upper()

    @staticmethod
    def _file_query_name(module: str) -> str:
        owner = APIModuleActions._file_owner_module(module)
        query_map = {
            Module.TASK.value: "taskFiles.graphql",
            Module.PROJECT.value: "projectFiles.graphql",
            Module.CONTRACT.value: "contractFiles.graphql",
            Module.COORDINATION.value: "coordinationFiles.graphql",
            Module.EASEMENT.value: "easementFiles.graphql",
        }
        return query_map.get(owner, "")

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
        cached_user = getattr(session, "loggedInUser", None)
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
    def delete_item(module: str, item_id: str, lang_manager: LanguageManager) -> bool:
        """
        Delete a single item from the specified module using the API.
        Returns True on success, False otherwise.
        """
        # Map module to its delete query file
        query_file = f"D_DELETE_{module}.graphql"

        # Load the GraphQL query
        loader = GraphQLQueryLoader()

        try:
            query = loader.load_query_by_module(module, query_file)
        except Exception as exc:
            print(f"Failed to load delete query for {module}: {exc}")
            return False
        variables = {"id": item_id}

        # Send the request
        client = APIClient()
        try:
            response = client.send_query(query, variables=variables)
            # You may want to check for errors in the response here
            return True
        except Exception as e:
            print(f"Failed to delete item {item_id} in module {module}: {e}")
            return False
        
    @staticmethod
    def get_module_item_connected_properties(
        module: str,
        item_id: str,
        ) -> List[str]:
        """Return cadastralUnitNumber values linked to the given module item."""

        module_name = module.strip().lower()
        query_module = APIModuleActions._property_owner_module(module_name)
        query_root = query_module
        if query_module == Module.TASK.value:
            query_file = "w_tasks_module_data_by_item_id.graphql"
        else:
            query_file = f"W_{module_name}_id.graphql"
        
        loader = GraphQLQueryLoader()
        try:
            query = loader.load_query_by_module(query_module, query_file)
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module=module_name or Module.PROPERTY.value,
                event="module_connected_properties_query_load_failed",
                extra={"item_id": str(item_id or "").strip(), "query_file": query_file},
            )
            return []

        client = APIClient()
        end_cursor: Optional[str] = None
        page_size = _PROPERTIES_PAGE_SIZE
        cadastral_numbers: List[str] = []
        seen: Set[str] = set()

        while True:
            variables = {
                "propertiesFirst": page_size,
                "propertiesAfter": end_cursor,
                "id": item_id,
            }
            try:
                payload = client.send_query(query, variables=variables, return_raw=True) or {}
            except Exception as exc:
                PythonFailLogger.log_exception(
                    exc,
                    module=module_name or Module.PROPERTY.value,
                    event="module_connected_properties_fetch_failed",
                    extra={"item_id": str(item_id or "").strip()},
                )
                return cadastral_numbers

            path = [query_root, "properties"]
            edges = JsonResponseHandler.get_edges_from_path(payload, path) or []
            if not edges:
                break

            for edge in edges:
                node = edge.get("node")
                number = node.get("cadastralUnitNumber")
                if number and number not in seen:
                    seen.add(number)
                    cadastral_numbers.append(number)

            details = JsonResponseHandler.get_page_detalils_from_path(payload, path)
            if details:
                end_cursor, has_next_page, _ = details
            else:
                end_cursor, has_next_page = None, False

            if has_next_page is False or not end_cursor:
                break
        return cadastral_numbers

    @staticmethod
    def resolve_property_ids_by_cadastral(numbers: List[str]) -> tuple[list[str], list[str]]:
        """Resolve cadastral numbers to property IDs (chunked to 25 per query). Returns (ids, missing_numbers)."""
        resolved_map, missing = APIModuleActions.resolve_property_map_by_cadastral(numbers)
        return list(resolved_map.values()), missing

    @staticmethod
    def resolve_property_map_by_cadastral(numbers: List[str]) -> tuple[dict[str, str], list[str]]:
        """Resolve cadastral numbers to property IDs (chunked to 25 per query). Returns (number->id, missing_numbers)."""
        cleaned = [str(n).strip() for n in numbers if str(n).strip()]
        if not cleaned:
            return {}, cleaned

        loader = GraphQLQueryLoader()
        query = loader.load_query_by_module(Module.PROPERTY.value, "id_number.graphql")
        client = APIClient()

        resolved_map: dict[str, str] = {}
        resolved_numbers = set()
        chunk_size = 25

        for start in range(0, len(cleaned), chunk_size):
            chunk = cleaned[start:start + chunk_size]
            variables = {
                "first": len(chunk),
                "after": None,
                "search": None,
                "where": {
                    "AND": [
                        {
                            "column": "CADASTRAL_UNIT_NUMBER",
                            "operator": "IN",
                            "value": chunk,
                        }
                    ]
                },
            }

            payload = client.send_query(query, variables=variables, return_raw=True) or {}
            edges = JsonResponseHandler.get_edges_from_path(payload, ["properties"]) or []
            for edge in edges:
                node = edge.get("node") or {}
                pid = node.get("id")
                cnum = node.get("cadastralUnitNumber")
                if pid and cnum:
                    resolved_map[str(cnum)] = str(pid)
                    resolved_numbers.add(str(cnum))

        missing = [n for n in cleaned if n not in resolved_numbers]
        return resolved_map, missing

    @staticmethod
    def get_easement_property_edges(item_id: str) -> List[dict[str, object]]:
        """Return easement-property edges with easement-specific metadata."""
        easement_id = str(item_id or "").strip()
        if not easement_id:
            return []

        loader = GraphQLQueryLoader()
        try:
            query = loader.load_query_by_module(Module.EASEMENT.value, "W_easement_id.graphql")
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module=Module.EASEMENT.value,
                event="easement_property_edges_query_load_failed",
                extra={"item_id": easement_id},
            )
            return []

        client = APIClient()
        end_cursor: Optional[str] = None
        edges_out: List[dict[str, object]] = []
        seen_numbers: Set[str] = set()

        while True:
            variables = {
                "propertiesFirst": _PROPERTIES_PAGE_SIZE,
                "propertiesAfter": end_cursor,
                "id": easement_id,
            }
            try:
                payload = client.send_query(query, variables=variables, return_raw=True) or {}
            except Exception as exc:
                PythonFailLogger.log_exception(
                    exc,
                    module=Module.EASEMENT.value,
                    event="easement_property_edges_fetch_failed",
                    extra={"item_id": easement_id},
                )
                return edges_out

            path = [Module.EASEMENT.value, "properties"]
            edges = JsonResponseHandler.get_edges_from_path(payload, path) or []
            if not edges:
                break

            for edge in edges:
                if not isinstance(edge, dict):
                    continue
                node = edge.get("node") or {}
                number = str(node.get("cadastralUnitNumber") or "").strip()
                if number and number in seen_numbers:
                    continue
                if number:
                    seen_numbers.add(number)
                edges_out.append(edge)

            details = JsonResponseHandler.get_page_detalils_from_path(payload, path)
            if details:
                end_cursor, has_next_page, _ = details
            else:
                end_cursor, has_next_page = None, False

            if has_next_page is False or not end_cursor:
                break
        return edges_out

    @staticmethod
    def associate_properties(module: str, item_id: str, property_ids: List[str]):
        """Associate property IDs to a module item via its update*Properties mutation.

        - module: lower-case module key (e.g., 'project', 'contract', 'coordination', 'task', 'easement')
        - item_id: target item id
        - property_ids: list of property ids to associate
        - query_file: optional override for mutation filename; defaults to update<Module>Properties.graphql
        """
        if not property_ids:
            raise ValueError("No property IDs provided for association")

        module_key = APIModuleActions._property_owner_module(module)
        qfile = f"update{module_key.capitalize()}Properties.graphql"

        loader = GraphQLQueryLoader()
        query = loader.load_query_by_module(module_key, qfile)
        variables = {
            "input": {
                "id": item_id,
                "properties": {
                    "associate": property_ids,
                },
            }
        }

        client = APIClient()
        response = client.send_query(query, variables=variables, return_raw=True)
        mutation_root = f"update{module_key.capitalize()}"
        data = (response or {}).get("data") or {}
        updated = (data.get(mutation_root) or {}) if isinstance(data, dict) else {}
        if not isinstance(updated, dict) or not updated.get("id"):
            raise RuntimeError(f"Property association did not return {mutation_root}.id")
        return response

    @staticmethod
    def associate_easement_properties(item_id: str, properties: List[dict[str, object]]):
        """Associate easement properties using the easement edge payload shape."""
        easement_id = str(item_id or "").strip()
        cleaned_properties: List[dict[str, object]] = []
        for prop in (properties or []):
            if not isinstance(prop, dict) or not prop.get("id"):
                continue

            cleaned: dict[str, object] = {"id": prop.get("id")}
            if isinstance(prop.get("area"), dict):
                cleaned["area"] = prop.get("area")
            if isinstance(prop.get("pricePerAreaUnit"), dict):
                cleaned["pricePerAreaUnit"] = prop.get("pricePerAreaUnit")
            if "isPayable" in prop:
                cleaned["isPayable"] = bool(prop.get("isPayable"))
            if prop.get("nextPaymentDate"):
                cleaned["nextPaymentDate"] = prop.get("nextPaymentDate")
            cleaned_properties.append(cleaned)

        if not easement_id:
            raise ValueError("No easement id provided for association")
        if not cleaned_properties:
            raise ValueError("No easement properties provided for association")

        loader = GraphQLQueryLoader()
        query = loader.load_query_by_module(Module.EASEMENT.value, "updateEasementProperties.graphql")
        variables = {
            "input": {
                "id": easement_id,
                "properties": {
                    "associate": cleaned_properties,
                },
            }
        }

        client = APIClient()
        response = client.send_query(query, variables=variables, return_raw=True)
        data = (response or {}).get("data") or {}
        updated = (data.get("updateEasement") or {}) if isinstance(data, dict) else {}
        if not isinstance(updated, dict) or not updated.get("id"):
            raise RuntimeError("Easement property association did not return updateEasement.id")
        return response

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
    def get_module_files(module_name: str, item_id: str, *, limit: int = 200) -> Optional[List[dict]]:
        owner = APIModuleActions._file_owner_module(module_name)
        query_name = APIModuleActions._file_query_name(module_name)
        record_id = str(item_id or "").strip()
        if not record_id:
            return []
        if not owner or not query_name:
            return None

        loader = GraphQLQueryLoader()
        query = loader.load_query_by_module(owner, query_name)
        client = APIClient()

        max_items = max(1, int(limit or 0))
        after: Optional[str] = None
        files_by_uuid: dict[str, dict] = {}

        try:
            while len(files_by_uuid) < max_items:
                remaining = max_items - len(files_by_uuid)
                variables = {
                    "id": record_id,
                    "first": min(50, remaining),
                    "after": after,
                }
                if owner == Module.TASK.value:
                    variables["orderBy"] = [
                        {
                            "column": "CREATED_AT",
                            "order": "DESC",
                        }
                    ]
                data = client.send_query(query, variables=variables) or {}
                root_payload = (data.get(owner) or {}) if isinstance(data, dict) else {}
                connection = (root_payload.get("files") or {}) if isinstance(root_payload, dict) else {}
                edges = connection.get("edges") or []

                if not isinstance(edges, list) or not edges:
                    break

                for edge in edges:
                    node = (edge or {}).get("node") or {}
                    if not isinstance(node, dict):
                        continue

                    file_uuid = str(node.get("uuid") or "").strip()
                    file_id = str(node.get("id") or "").strip()
                    if not file_uuid and not file_id:
                        continue

                    key = file_uuid or file_id
                    uploader = node.get("uploader") if isinstance(node.get("uploader"), dict) else {}
                    model = node.get("model") if isinstance(node.get("model"), dict) else {}
                    files_by_uuid[key] = {
                        "id": file_id,
                        "uuid": file_uuid,
                        "fileName": str(node.get("fileName") or "").strip(),
                        "mimeType": str(node.get("mimeType") or "").strip(),
                        "ext": str(node.get("ext") or "").strip(),
                        "size": node.get("size"),
                        "humanReadableSize": str(node.get("humanReadableSize") or "").strip(),
                        "uploader": uploader,
                        "model": model,
                        "createdAt": node.get("createdAt"),
                        "updatedAt": node.get("updatedAt"),
                        "deletedAt": node.get("deletedAt"),
                    }
                    if len(files_by_uuid) >= max_items:
                        break

                page_info = connection.get("pageInfo") or {}
                after = str(page_info.get("endCursor") or "").strip()
                if not page_info.get("hasNextPage") or not after:
                    break

            return list(files_by_uuid.values())
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module=owner or Module.TASK.value,
                event="module_get_files_failed",
                extra={"item_id": record_id, "module": str(module_name or "")},
            )
            return None

    @staticmethod
    def get_task_files(item_id: str, *, limit: int = 200) -> Optional[List[dict]]:
        return APIModuleActions.get_module_files(Module.TASK.value, item_id, limit=limit)

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
    def create_file_download_link(file_uuid: str) -> Optional[str]:
        resolved_uuid = str(file_uuid or "").strip()
        if not resolved_uuid:
            return None

        loader = GraphQLQueryLoader()
        query = loader.load_query_by_module(Module.TASK.value, "createDownloadLink.graphql")
        client = APIClient()

        try:
            data = client.send_query(query, variables={"uuid": resolved_uuid}) or {}
            payload = (data.get("createDownloadLink") or {}) if isinstance(data, dict) else {}
            url = str(payload.get("url") or "").strip()
            return url or None
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module=Module.TASK.value,
                event="task_file_download_link_failed",
                extra={"uuid": resolved_uuid},
            )
            return None

    @staticmethod
    def fetch_file_preview_payload(file_uuid: str, *, max_bytes: int) -> Optional[dict]:
        resolved_uuid = str(file_uuid or "").strip()
        preview_limit = max(1, int(max_bytes or 0))
        if not resolved_uuid:
            return None

        url = APIModuleActions.create_file_download_link(resolved_uuid)
        if not url:
            return None

        headers = {
            "Accept": "*/*",
            "X-Requested-With": "XMLHttpRequest",
        }

        try:
            with requests.get(url, headers=headers, stream=True, timeout=60) as response:
                response.raise_for_status()

                content = bytearray()
                truncated = False
                for chunk in response.iter_content(chunk_size=65536):
                    if not chunk:
                        continue

                    remaining = preview_limit - len(content)
                    if remaining <= 0:
                        truncated = True
                        break

                    if len(chunk) > remaining:
                        content.extend(chunk[:remaining])
                        truncated = True
                        break

                    content.extend(chunk)

                content_type = str(response.headers.get("Content-Type") or "").split(";", 1)[0].strip().lower()
                disposition = str(response.headers.get("Content-Disposition") or "").strip()
                content_length = str(response.headers.get("Content-Length") or "").strip()

                return {
                    "url": url,
                    "content": bytes(content),
                    "contentType": content_type,
                    "contentDisposition": disposition,
                    "contentLength": content_length,
                    "truncated": truncated,
                }
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module=Module.TASK.value,
                event="task_file_preview_fetch_failed",
                extra={"uuid": resolved_uuid, "max_bytes": preview_limit},
            )
            return None

    @staticmethod
    def delete_file(file_uuid: str) -> Optional[dict]:
        resolved_uuid = str(file_uuid or "").strip()
        if not resolved_uuid:
            return None

        loader = GraphQLQueryLoader()
        query = loader.load_query_by_module(Module.TASK.value, "deleteFile.graphql")
        client = APIClient()

        try:
            data = client.send_query(query, variables={"uuid": resolved_uuid}) or {}
            payload = (data.get("deleteFile") or {}) if isinstance(data, dict) else {}
            return payload if isinstance(payload, dict) and str(payload.get("uuid") or "").strip() else None
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module=Module.TASK.value,
                event="task_file_delete_failed",
                extra={"uuid": resolved_uuid},
            )
            return None

    @staticmethod
    def upload_module_file(module_name: str, item_id: str, file_path: str, *, metadata: Optional[dict] = None) -> Optional[dict]:
        owner = APIModuleActions._file_owner_module(module_name)
        model_type = APIModuleActions._file_model_type(module_name)
        task_id = str(item_id or "").strip()
        normalized_path = str(file_path or "").strip()
        if not owner or not model_type or not task_id or not normalized_path or not os.path.isfile(normalized_path):
            return None

        loader = GraphQLQueryLoader()
        query = loader.load_query_by_module(Module.TASK.value, "uploadTaskFile.graphql")
        client = APIClient()

        variables = {
            "file": None,
            "model": {
                "id": task_id,
                "type": model_type,
            },
            "data": metadata if metadata is not None else None,
        }

        try:
            data = client.send_multipart_query(
                query,
                variables=variables,
                file_variables={"file": normalized_path},
                timeout=120,
            ) or {}
            payload = (data.get("uploadFile") or {}) if isinstance(data, dict) else {}
            return payload if isinstance(payload, dict) and str(payload.get("uuid") or "").strip() else None
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module=owner,
                event="module_file_upload_failed",
                extra={
                    "item_id": task_id,
                    "file_name": os.path.basename(normalized_path),
                    "module": str(module_name or ""),
                },
            )
            return None

    @staticmethod
    def upload_task_file(item_id: str, file_path: str, *, metadata: Optional[dict] = None) -> Optional[dict]:
        return APIModuleActions.upload_module_file(Module.TASK.value, item_id, file_path, metadata=metadata)

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
                member_payload["isResponsible"] = member_id == selected_responsible_id
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

        def _build_task_input(associate_payload: Optional[List[object]]) -> dict:
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
            if associate_payload:
                task_input["members"] = {"associate": associate_payload}
            return task_input

        client = APIClient()
        try:
            try:
                data = client.send_query(query, variables={"input": _build_task_input(member_payload)}) or {}
                used_fallback_payload = False
            except Exception as create_exc:
                message = str(create_exc or "")
                should_retry_without_flag = (
                    bool(member_payload)
                    and member_payload != fallback_member_payload
                    and "members.associate" in message
                    and "isResponsible" in message
                )
                if not should_retry_without_flag:
                    raise

                data = client.send_query(query, variables={"input": _build_task_input(fallback_member_payload)}) or {}
                used_fallback_payload = True

            created = (data.get("createTask") or {}) if isinstance(data, dict) else {}
            task_id = created.get("id")
            task_id_text = str(task_id) if task_id else None
            if task_id_text and used_fallback_payload and effective_responsible_id and member_payload:
                APIModuleActions.update_task_members(task_id_text, member_payload)
            return task_id_text
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module=Module.TASK.value,
                event="task_create_failed",
                extra={"title": task_title, "type_id": task_type_id},
            )
            return None


