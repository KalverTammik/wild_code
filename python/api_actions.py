from typing import List, Optional, Set

from .api_client import APIClient

from .GraphQLQueryLoader import GraphQLQueryLoader
from ..languages.language_manager import LanguageManager
from ..Logs.python_fail_logger import PythonFailLogger
from .responses import JsonResponseHandler
from ..utils.url_manager import Module


_PROPERTIES_PAGE_SIZE = 50

class APIModuleActions:
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

        query_file = f"W_{module_name}_id.graphql"
        
        loader = GraphQLQueryLoader()
        query = loader.load_query_by_module(module_name, query_file)

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
            payload = client.send_query(query, variables=variables, return_raw=True) or {}
            path = [module_name, "properties"]
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
        cleaned = [str(n).strip() for n in numbers if str(n).strip()]
        if not cleaned:
            return [], cleaned

        loader = GraphQLQueryLoader()
        query = loader.load_query_by_module(Module.PROPERTY.value, "id_number.graphql")
        client = APIClient()

        ids: list[str] = []
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
                    ids.append(str(pid))
                    resolved_numbers.add(str(cnum))

        missing = [n for n in cleaned if n not in resolved_numbers]
        return ids, missing

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

        module_key = module.strip().lower()
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
        return client.send_query(query, variables=variables, return_raw=True)

    @staticmethod
    def get_task_description(item_id: str) -> Optional[str]:
        """Fetch the latest task/asbuilt description from the backend."""

        task_id = str(item_id or "").strip()
        if not task_id:
            return None

        loader = GraphQLQueryLoader()
        query = loader.load_query_by_module(Module.TASK.value, "w_tasks_module_data_by_item_id.graphql")
        client = APIClient()

        try:
            data = client.send_query(query, variables={"id": task_id}) or {}
            task = (data.get("task") or {}) if isinstance(data, dict) else {}
            description = task.get("description")
            return str(description or "")
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module=Module.ASBUILT.value,
                event="task_get_description_failed",
                extra={"item_id": task_id},
            )
            return None

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
                module=Module.ASBUILT.value,
                event="task_update_description_failed",
                extra={"item_id": task_id},
            )
            return False

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
    ) -> Optional[str]:
        task_title = str(title or "").strip()
        task_type_id = str(type_id or "").strip()
        if not task_title or not task_type_id:
            return None

        loader = GraphQLQueryLoader()
        query = loader.load_query_by_module(Module.TASK.value, "createTask.graphql")

        task_input = {
            "title": task_title,
            "typeId": task_type_id,
        }
        if description is not None:
            task_input["description"] = str(description or "")
        if priority:
            task_input["priority"] = str(priority)
        if start_at:
            task_input["startAt"] = str(start_at)
        if due_at:
            task_input["dueAt"] = str(due_at)
        if member_ids:
            cleaned_members = [str(member_id).strip() for member_id in member_ids if str(member_id).strip()]
            if cleaned_members:
                task_input["members"] = {"associate": cleaned_members}

        client = APIClient()
        try:
            data = client.send_query(query, variables={"input": task_input}) or {}
            created = (data.get("createTask") or {}) if isinstance(data, dict) else {}
            task_id = created.get("id")
            return str(task_id) if task_id else None
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module=Module.TASK.value,
                event="task_create_failed",
                extra={"title": task_title, "type_id": task_type_id},
            )
            return None


