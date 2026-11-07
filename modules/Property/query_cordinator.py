from typing import Any, Dict, List, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor

from ...module_manager import Module
from ...constants.file_paths import QueryPaths
from ...Logs.python_fail_logger import PythonFailLogger
from ...utils.url_manager import ModuleSupports
from ..Settings.SettinsUtils.SettingsLogic import SettingsLogic

from ...python.api_client import APIClient
from ...python.GraphQLQueryLoader import GraphQLQueryLoader


class PropertiesConnectedElementsQueries:
    PAGE_SIZE = 30
    # Works are picked from all property tasks on the client, so one page could hide some.
    WORKS_MAX_PAGES = 10
    WORKS_CONNECTION = f"{Module.TASK.value}s"

    module_to_filename = {
        Module.CONTRACT.value: "connected_contracts.graphql",
        Module.COORDINATION.value: "connected_coordinations.graphql",
        Module.EASEMENT.value: "connected_easements.graphql",
        Module.PROJECT.value: "connected_projects.graphql",
        Module.SPECIFICATION.value: "connected_specifications.graphql",
        Module.SUBMISSION.value: "connected_submissions.graphql",
        Module.WORKS.value: "connected_tasks.graphql",
    }

    def __init__(self):
        self.query_loader = QueryPaths()
        self._processor = ProcessElementData()

    def _normalize_module_key(self, module_name: Any) -> Optional[str]:
        if isinstance(module_name, Module):
            return module_name.value
        if module_name is None:
            return None
        return str(module_name).lower()

    def fetch_module_data(self, module_name, propertie_id):
        module_key = self._normalize_module_key(module_name)
        if not module_key:
            return []

        module_file = self.module_to_filename.get(module_key)
        if not module_file:
            return []

        query = self.query_loader.load_query_properties_connected_elements(module_file)
        if module_key == Module.WORKS.value:
            return self._fetch_works(query, propertie_id)

        variables = {
            "id": propertie_id,
            "first": self.PAGE_SIZE,
            "tagsFirst": 10,
            "orderBy": [
                {
                    "column": "NUMBER",
                    "order": "ASC"
                }
            ]
        }

        payload = APIClient().send_query(query, variables=variables, return_raw=True) or {}
        return self._processor.process_response_data(module_key, payload)

    def _fetch_works(self, query: str, property_id) -> List[Dict[str, Any]]:
        # A work is a task whose type the Works module lists; with no types chosen it lists every task.
        type_ids = set(
            SettingsLogic().load_module_preference_ids(
                Module.WORKS.value,
                support_key=ModuleSupports.TYPES.value,
            )
        )
        client = APIClient()
        works: List[Dict[str, Any]] = []
        after = None
        for _ in range(self.WORKS_MAX_PAGES):
            variables = {"id": property_id, "first": self.PAGE_SIZE, "after": after}
            payload = client.send_query(query, variables=variables, return_raw=True) or {}
            connection = self._processor.connection_block(self.WORKS_CONNECTION, payload)
            works.extend(
                node
                for node in self._processor.connection_nodes(connection)
                if not type_ids or str((node.get("type") or {}).get("id") or "") in type_ids
            )
            page_info = connection.get("pageInfo") or {}
            after = page_info.get("endCursor")
            if not page_info.get("hasNextPage") or not after:
                return works

        PythonFailLogger.log(
            "property_works_page_limit_reached",
            module=Module.PROPERTY.value,
            extra={"property_id": property_id, "pages": self.WORKS_MAX_PAGES},
        )
        return works

    def fetch_all_module_data(self, propertie_id):
        aggregated: Dict[str, List[Dict[str, Any]]] = {}
        module_keys = list(self.module_to_filename.keys())
        with ThreadPoolExecutor(max_workers=min(4, len(module_keys))) as executor:
            future_by_module = {
                module_key: executor.submit(self.fetch_module_data, module_key, propertie_id)
                for module_key in module_keys
            }

        for module_key in module_keys:
            try:
                nodes = future_by_module[module_key].result()
            except Exception as exc:
                PythonFailLogger.log_exception(
                    exc,
                    module=Module.PROPERTY.value,
                    event="property_connected_module_fetch_failed",
                    extra={"target_module": module_key},
                )
                nodes = []
            if nodes:
                aggregated[module_key] = nodes
        return aggregated

class ProcessElementData:
    def process_response_data(self, module_key: str, payload: Dict[str, Any]):
        module_key = module_key or ""
        return self.connection_nodes(self.connection_block(f"{module_key}s", payload))

    @staticmethod
    def connection_block(connection_field: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        property_block = ((payload or {}).get("data") or {}).get("property") or {}
        return property_block.get(connection_field) or {}

    @staticmethod
    def connection_nodes(connection: Dict[str, Any]) -> List[Dict[str, Any]]:
        nodes: List[Dict[str, Any]] = []
        for edge in connection.get("edges") or []:
            node = edge.get("node") if isinstance(edge, dict) else None
            if node:
                nodes.append(node)
        return nodes

class PropertyLookupService:
    """Utility helpers for resolving property identifiers from cadastral numbers."""

    def __init__(self):
        self._api_client = APIClient()
        self._query_loader = GraphQLQueryLoader()
        self._property_id_query = self._query_loader.load_query_by_module(
            Module.PROPERTY.value,
            "id_number.graphql",
        )

    def property_id_by_cadastral(self, cadastral_number: str) -> Optional[str]:
        if not cadastral_number:
            return None

        where_condition = {
            "column": "CADASTRAL_UNIT_NUMBER",
            "operator": "EQ",
            "value": cadastral_number,
        }
        variables = {
            "first": 1,
            "where": {"AND": [where_condition]},
        }

        payload = self._execute_property_query(variables)
        edges = self._extract_edges(payload)

        if not edges:
            # Fallback to generic search to cover cases where the column filter does not match schema
            payload = self._execute_property_query({"first": 1, "search": cadastral_number})
            edges = self._extract_edges(payload)

        if not edges:
            return None
        return edges[0].get("node", {}).get("id")

    def _execute_property_query(self, variables: Dict[str, Any]) -> Dict[str, Any]:
        return self._api_client.send_query(
            self._property_id_query,
            variables=variables,
            return_raw=True,
        ) or {}

    @staticmethod
    def _extract_edges(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
        edges = (
            payload.get("data", {})
            .get("properties", {})
            .get("edges", [])
        )
        return edges or []

class PropertyConnectionFormatter:
    """Transforms raw module node data into UI-friendly payloads."""

    def build_entry(
        self,
        cadastral_number: str,
        property_id: Optional[str],
        module_connections: Dict[str, List[Dict[str, Any]]],
    ) -> Dict[str, Any]:
        return {
            "cadastralNumber": cadastral_number,
            "propertyId": property_id,
            "moduleConnections": self._format_module_connections(module_connections),
        }

    def _format_module_connections(self, module_connections):
        formatted = {}
        for module_key, nodes in module_connections.items():
            summaries = [self._extract_node_summary(node) for node in nodes]
            formatted[module_key] = {
                "count": len(nodes),
                "items": summaries,
            }
        return formatted

    def _extract_node_summary(self, node: Dict[str, Any]):
        if not isinstance(node, dict):
            return {"raw": node}

        summary = {
            "id": node.get("id"),
            "number": node.get("number") or node.get("code"),
            "title": node.get("name") or node.get("title"),
            "status": self._extract_nested_text(
                node,
                ("status", "name"),
                ("currentStatus", "name"),
            ),
            "type": self._extract_nested_text(node, ("type", "name")),
            "updatedAt": node.get("updatedAt") or node.get("modifiedAt"),
            "raw": node,
        }
        return summary

    @staticmethod
    def _extract_nested_text(node: Dict[str, Any], *paths: Tuple[str, ...]) -> Optional[str]:
        for path in paths:
            current = node
            for key in path:
                if not isinstance(current, dict):
                    current = None
                    break
                current = current.get(key)
            if isinstance(current, str) and current:
                return current
        return None