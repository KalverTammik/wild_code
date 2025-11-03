from ..utils.api_client import APIClient
from ..utils.url_manager import Module
from ..utils.GraphQLQueryLoader import GraphQLQueryLoader
from ..languages.language_manager import LanguageManager

class APIModuleActions:
    @staticmethod
    def delete_item(module: Module, item_id: str, lang_manager: LanguageManager) -> bool:
        """
        Delete a single item from the specified module using the API.
        Returns True on success, False otherwise.
        """
        # Map module to its delete query file
        query_file_map = {
            Module.PROPERTY: "D_DELETE_property.graphql",
            Module.PROJECT: "D_DELETE_project.graphql",
            Module.CONTRACT: "D_DELETE_contract.graphql",
            # Add more as needed
        }
        query_file = query_file_map.get(module)
        if not query_file:
            print(f"No delete query defined for module: {module}")
            return False

        # Load the GraphQL query
        query = GraphQLQueryLoader.load_query(module, query_file)
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