"""Property-link actions: the properties a module item is linked to, lookup by cadastral number, linking."""
from typing import List, Optional, Set

from ..api_client import APIClient
from ..GraphQLQueryLoader import GraphQLQueryLoader
from ..responses import JsonResponseHandler
from ...Logs.python_fail_logger import PythonFailLogger
from ...constants.module_names import Module


_PROPERTIES_PAGE_SIZE = 50


class PropertyLinkActions:
    """Static property-link actions; APIModuleActions inherits them so callers keep one entry point."""

    @staticmethod
    def _property_owner_module(module: str) -> str:
        module_name = str(module or "").strip().lower()
        if module_name in (Module.TASK.value, Module.WORKS.value, Module.ASBUILT.value):
            return Module.TASK.value
        return module_name

    @staticmethod
    def get_module_item_connected_properties(
        module: str,
        item_id: str,
        ) -> List[str]:
        """Return cadastralUnitNumber values linked to the given module item."""

        module_name = str(module or "").strip().lower()
        record_id = str(item_id or "").strip()
        query_module = PropertyLinkActions._property_owner_module(module_name)
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
                extra={"item_id": record_id, "query_file": query_file},
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
                "id": record_id,
            }
            try:
                payload = client.send_query(query, variables=variables, return_raw=True) or {}
            except Exception as exc:
                PythonFailLogger.log_exception(
                    exc,
                    module=module_name or Module.PROPERTY.value,
                    event="module_connected_properties_fetch_failed",
                    extra={"item_id": record_id},
                )
                return cadastral_numbers

            path = [query_root, "properties"]
            edges = JsonResponseHandler.get_edges_from_path(payload, path) or []
            if not edges:
                break

            for edge in edges:
                node = edge.get("node") if isinstance(edge, dict) else None
                if not isinstance(node, dict):
                    continue
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
        resolved_map, missing = PropertyLinkActions.resolve_property_map_by_cadastral(numbers)
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

        The mutation file is update<Module>Properties.graphql of the owner module. Nothing is caught
        here: no property ids raises ValueError, an answer without update<Module>.id raises RuntimeError
        and request errors propagate, so the caller can show the failure to the user.
        """
        if not property_ids:
            raise ValueError("No property IDs provided for association")

        module_key = PropertyLinkActions._property_owner_module(module)
        if module_key == Module.EASEMENT.value:
            # An easement links each property as an EasementPropertyInput object, not a bare id.
            return PropertyLinkActions.associate_easement_properties(
                item_id, [{"id": property_id} for property_id in property_ids]
            )
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
