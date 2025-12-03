from typing import List, Optional, Set

from .api_client import APIClient

from .GraphQLQueryLoader import GraphQLQueryLoader
from ..languages.language_manager import LanguageManager
from .responses import JsonResponseHandler


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
            print(f"[DEBUG] Connected properties payload: {payload}")
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
        print(f"[DEBUG] Retrieved connected cadastral numbers: {cadastral_numbers}")
        return cadastral_numbers

