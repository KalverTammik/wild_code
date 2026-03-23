
from PyQt5.QtCore import QCoreApplication
from ...queries.python.FileLoaderHelper import GraphqlEasements, GraphQLQueryLoader
from ...queries.python.query_tools import requestBuilder
from ...KeelelisedMuutujad.modules import Module

class getEasementsWhere:
    @staticmethod
    def query_easement_related_properties(self, id_value):
        #print(f"id value in query {id_value}")
        #Load the project query using the loader instance

        module = Module.EASEMENT

        query_name = GraphqlEasements.RELATED_PROPERTIES
        query = GraphQLQueryLoader.load_query_by_module(module, query_name)  

        
        # Set the desired total number of items to fetch
        desired_total_items = None  # Adjust this to your desired value
        items_for_page = 50  # Adjust this to your desired value
        #Initialize variables for pagination
        end_cursor = None  # Initialize end_cursor before the loop
        total_fetched = 0        # Initialize an empty list to store fetched items
        properties_items = []
        
        while (desired_total_items is None or total_fetched < desired_total_items):
            # Construct variables for the GraphQL query
            variables = {
                    "propertiesFirst": items_for_page,
                    "propertiesAfter": end_cursor if end_cursor else None,
                    "id": id_value
                    }
            response = requestBuilder.construct_and_send_request(query, variables)

            if response.status_code == 200:
                data = response.json()
                project_data = data.get("data", {}).get("easement", {})
                properties_data = project_data.get("properties", {})
                edges = properties_data.get("edges", [])
                pageInfo = properties_data.get("pageInfo", {})
                end_cursor = pageInfo.get("endCursor")
                hasNextPage = pageInfo.get("hasNextPage")
                count = pageInfo.get('count')
                for edge in edges:
                    node = edge.get("node", {})
                    cadastral_unit_number = node.get("cadastralUnitNumber", "")
                    #print(cadastral_unit_number)
                    properties_items.append(cadastral_unit_number)
                print(f"properties_items: {properties_items}")
                total_fetched += count
                if not end_cursor or (desired_total_items is not None and total_fetched >= desired_total_items) or not hasNextPage:
                    break
                QCoreApplication.processEvents()
            else:
                print(f"Error: {response.status_code}")
                return None
        # Return only the desired number of items
        return properties_items
