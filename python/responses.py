import requests
from typing import Any, Dict, List, Optional

class HandlePropertiesResponses:
    @staticmethod
    def _handle_properties_response(response: requests.Response) -> dict:
        data = response.json()
        fetched_data = data.get("data", {}).get("properties", {}).get("edges", [])
        pageInfo = data.get("data", {}).get("properties", {}).get("pageInfo", {})
        end_cursor = pageInfo.get("endCursor")
        last_page = pageInfo.get("lastPage")

        return data, fetched_data, pageInfo, end_cursor, last_page

    @staticmethod
    def _response_data_json(response: requests.Response)->dict:
        data_json = response.json()
        return data_json
    
    @staticmethod
    def _response_properties_data_edges(response: requests.Response)->list:
        data = response.json()
        fetched_data = data.get("data", {}).get("properties", {}).get("edges", [])
        return fetched_data
    
    @staticmethod        
    def _response_properties_data_ids(response: requests.Response)->list:
        data = response.json()
        # Check if the required keys are present in the JSON
        if 'data' in data and 'properties' in data['data'] and 'edges' in data['data']['properties']:
            # Extract IDs from the JSON
            ids = [edge['node']['id'] for edge in data['data']['properties']['edges']]
            # Print the extracted IDs
            #print("Extracted IDs:")
            #print(ids)
            return ids
    
    @staticmethod        
    def _response_properties_cadastral_numbers(response: requests.Response)->list:
        data = response.json()
        # Check if the required keys are present in the JSON
        if 'data' in data and 'properties' in data['data'] and 'edges' in data['data']['properties']:
            # Extract IDs from the JSON
            cadastral_units = [edge['node']['cadastralUnit'] for edge in data['data']['properties']['edges']]
            #print(cadastral_units)
              # Extract numbers from cadastral units
            numbers = [unit['number'] for unit in cadastral_units]
            # Print the extracted IDs
            #print("Extracted IDs:")
            #print(ids)
            return numbers
    
    @staticmethod
    def _response_properties_pageInfo(response: requests.Response)->dict:
        data = response.json()
        pageInfo = data.get("data", {}).get("properties", {}).get("pageInfo", {})
        #print(f"Page info = {pageInfo}")
        return pageInfo
    
    @staticmethod
    def _response_properties_endCursor(response)->str:
        pageInfo = HandlePropertiesResponses._response_properties_pageInfo(response)
        end_cursor = pageInfo.get("endCursor")
        return end_cursor

    @staticmethod    
    def _response_properties_lastPage(response)->bool:
        pageInfo = HandlePropertiesResponses._response_properties_pageInfo(response)
        last_page = pageInfo.get("lastPage")
        #print(f"last_page = {last_page}")
        return last_page




class JsonResponseHandler:

    @staticmethod
    def get_raw_json(response: requests.Response) -> Dict[str, Any]:
        return response.json()

    @staticmethod
    def walk_path(data: Dict[str, Any], path: List[str]) -> Any:
        for key in path:
            if isinstance(data, dict):
                data = data.get(key, {})
            else:
                return {}
        return data

    @staticmethod
    def get_edges_from_path(response: requests.Response, path: List[str]) -> List[Dict[str, Any]]:
        data = JsonResponseHandler.get_raw_json(response)
        #print(f"data = {data}")
        module_data = JsonResponseHandler.walk_path(data.get("data", {}), path)
        return module_data.get("edges", [])


    @staticmethod
    def get_page_info_from_path(response: requests.Response, path: List[str]) -> Dict[str, Any]:
        data = JsonResponseHandler.get_raw_json(response)
        module_data = JsonResponseHandler.walk_path(data.get("data", {}), path)
        return module_data.get("pageInfo", {})

    @staticmethod
    def get_ids_from_path(response: requests.Response, path: List[str]) -> List[str]:
        edges = JsonResponseHandler.get_edges_from_path(response, path)
        return [edge.get("node", {}).get("id") for edge in edges if "node" in edge]

    @staticmethod
    def get_nested_field_from_path(
        response: requests.Response,
        path: List[str],
        field_path: List[str]
    ) -> List[Any]:
        edges = JsonResponseHandler.get_edges_from_path(response, path)
        results = []
        for edge in edges:
            node = edge.get("node", {})
            value = node
            for key in field_path:
                value = value.get(key)
                if value is None:
                    break
            if value is not None:
                results.append(value)
        return results

    @staticmethod
    def get_end_cursor_from_path(response: requests.Response, path: List[str]) -> Optional[str]:
        page_info = JsonResponseHandler.get_page_info_from_path(response, path)
        return page_info.get("endCursor")

    @staticmethod
    def is_last_page_from_path(response: requests.Response, path: List[str]) -> bool:
        page_info = JsonResponseHandler.get_page_info_from_path(response, path)
        return page_info.get("lastPage", False)

    @staticmethod    
    def get_page_detalils_from_path(response:requests.Response,path:list)->tuple:
        page_info = JsonResponseHandler.get_page_info_from_path(response, path)
        end_cursor = page_info.get("endCursor")
        has_next_page = page_info.get("hasNextPage", False)
        count = page_info.get("count", 0)
        return end_cursor, has_next_page, count

class GetValuFromEdge:

    @staticmethod
    def get_cadastral_unit_number(edge: Dict[str, Any]) -> str:
        node = edge.get("node", {})
        return node.get("cadastralUnitNumber", False)
