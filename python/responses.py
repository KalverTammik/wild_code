from dataclasses import dataclass
import requests
from typing import Any, Dict, List, Mapping, Optional, Union

Json = Mapping[str, Any]


class GqlKeys:
    # connection pattern
    EDGES = "edges"
    NODE = "node"
    TOTAL_COUNT = "totalCount"
    PAGE_INFO = "pageInfo"

    # common display fields
    DISPLAY_NAME = "displayName"
    NAME = "name"
    COLOR = "color"
    ACTIVE = "active"

    # domain roots
    TAGS = "tags"
    STATUS = "status"
    MEMBERS = "members"
    CONTACTS = "contacts"
    PROPERTIES = "properties"
    FILES_PATH = "filesPath"
    ID = "id"
    NUMBER = "number"
    PROJECT_NUMBER = "projectNumber"
    JOB_NAME = "jobName"
    CLIENT = "client"
    IS_PUBLIC = "isPublic"

    # members edge fields
    IS_RESPONSIBLE = "isResponsible"

    # dates
    START_AT = "startAt"
    DUE_AT = "dueAt"
    CREATED_AT = "createdAt"
    UPDATED_AT = "updatedAt"


@dataclass(frozen=True)
class StatusInfo:
    name: str = "-"
    color: str = "cccccc"


@dataclass(frozen=True)
class DatesInfo:
    start_at: Optional[str] = None
    due_at: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class DataDisplayExtractors:
    """
    Pure helpers reading GraphQL-ish dicts and returning safe defaults.
    No Qt imports. No side effects.
    """

    @staticmethod
    def _as_dict(value: Any) -> Dict[str, Any]:
        return value if isinstance(value, dict) else {}

    @staticmethod
    def _edges_from(item_data: Optional[Json], key: str) -> List[Dict[str, Any]]:
        if not isinstance(item_data, Mapping):
            return []
        conn = item_data.get(key)
        conn_dict = DataDisplayExtractors._as_dict(conn)
        edges = conn_dict.get(GqlKeys.EDGES, [])
        return list(edges) if isinstance(edges, list) else []

    @staticmethod
    def extract_tag_names(item_data: Optional[Json]) -> List[str]:
        names: List[str] = []
        for edge in DataDisplayExtractors._edges_from(item_data, GqlKeys.TAGS):
            node = DataDisplayExtractors._as_dict(edge).get(GqlKeys.NODE) or {}
            name = DataDisplayExtractors._as_dict(node).get(GqlKeys.NAME)
            if isinstance(name, str):
                trimmed = name.strip()
                if trimmed:
                    names.append(trimmed)
        return names

    @staticmethod
    def extract_contact_names(item_data: Optional[Json]) -> List[str]:
        names: List[str] = []
        for edge in DataDisplayExtractors._edges_from(item_data, GqlKeys.CONTACTS):
            node = DataDisplayExtractors._as_dict(edge).get(GqlKeys.NODE) or {}
            name = DataDisplayExtractors._as_dict(node).get(GqlKeys.DISPLAY_NAME)
            if isinstance(name, str):
                trimmed = name.strip()
                if trimmed:
                    names.append(trimmed)
        return names

    @staticmethod
    def extract_status(item_data: Optional[Json]) -> StatusInfo:
        if not isinstance(item_data, Mapping):
            return StatusInfo()
        status = DataDisplayExtractors._as_dict(item_data.get(GqlKeys.STATUS))
        name = status.get(GqlKeys.NAME) or "-"
        color = status.get(GqlKeys.COLOR) or "cccccc"
        return StatusInfo(str(name), str(color))

    @staticmethod
    def extract_members(item_data: Optional[Json]) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        responsible_nodes: List[Dict[str, Any]] = []
        participant_nodes: List[Dict[str, Any]] = []

        for edge in DataDisplayExtractors._edges_from(item_data, GqlKeys.MEMBERS):
            edge_dict = DataDisplayExtractors._as_dict(edge)
            node = DataDisplayExtractors._as_dict(edge_dict.get(GqlKeys.NODE))
            if not node:
                continue
            active = node.get(GqlKeys.ACTIVE, True)
            if active is False:
                continue
            if edge_dict.get(GqlKeys.IS_RESPONSIBLE):
                responsible_nodes.append(node)
            else:
                participant_nodes.append(node)
        return responsible_nodes, participant_nodes

    @staticmethod
    def extract_dates(item_data: Optional[Json]) -> DatesInfo:
        if not isinstance(item_data, Mapping):
            return DatesInfo()
        return DatesInfo(
            start_at=item_data.get(GqlKeys.START_AT),
            due_at=item_data.get(GqlKeys.DUE_AT),
            created_at=item_data.get(GqlKeys.CREATED_AT),
            updated_at=item_data.get(GqlKeys.UPDATED_AT),
        )

    @staticmethod
    def extract_files_path(item_data: Optional[Json]) -> str:
        if not isinstance(item_data, Mapping):
            return ""
        value = item_data.get(GqlKeys.FILES_PATH, "")
        return str(value) if value else ""

    @staticmethod
    def extract_properties_connection_count(item_data: Optional[Json]) -> int:
        if not isinstance(item_data, Mapping):
            return 0
        properties = DataDisplayExtractors._as_dict(item_data.get(GqlKeys.PROPERTIES))
        page_info = DataDisplayExtractors._as_dict(properties.get(GqlKeys.PAGE_INFO))
        for key in ("count", "total", GqlKeys.TOTAL_COUNT):
            value = page_info.get(key)
            if isinstance(value, (int, float)):
                return int(value)
            if isinstance(value, str):
                try:
                    return int(value)
                except ValueError:
                    pass
        edges = properties.get(GqlKeys.EDGES, [])
        if isinstance(edges, list) and edges:
            return len(edges)
        return 0

    @staticmethod
    def extract_item_id(item_data: Optional[Json]) -> Optional[str]:
        if not isinstance(item_data, Mapping):
            return None
        value = item_data.get(GqlKeys.ID)
        return str(value) if value else None

    @staticmethod
    def extract_item_number(item_data: Optional[Json]) -> Optional[str]:
        if not isinstance(item_data, Mapping):
            return None
        value = item_data.get(GqlKeys.NUMBER)
        return str(value) if value else None

    @staticmethod
    def extract_project_number(item_data: Optional[Json]) -> Optional[str]:
        if not isinstance(item_data, Mapping):
            return None
        value = item_data.get(GqlKeys.PROJECT_NUMBER)
        return str(value) if value else None

    @staticmethod
    def extract_item_name(item_data: Optional[Json]) -> Optional[str]:
        if not isinstance(item_data, Mapping):
            return None
        value = item_data.get(GqlKeys.NAME) or item_data.get(GqlKeys.JOB_NAME)
        return str(value) if value else None

    @staticmethod
    def extract_client_display_name(item_data: Optional[Json]) -> Optional[str]:
        if not isinstance(item_data, Mapping):
            return None
        client = DataDisplayExtractors._as_dict(item_data.get(GqlKeys.CLIENT))
        value = client.get(GqlKeys.DISPLAY_NAME)
        return str(value) if value else None

    @staticmethod
    def extract_is_public(item_data: Optional[Json]) -> bool:
        if not isinstance(item_data, Mapping):
            return False
        return bool(item_data.get(GqlKeys.IS_PUBLIC))

    @staticmethod
    def extract_member_display_name(node: Any) -> str:
        if isinstance(node, Mapping):
            value = node.get(GqlKeys.DISPLAY_NAME)
            if isinstance(value, str) and value.strip():
                return value.strip()
        return "-"

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
    def _coerce_to_json(payload: Union[requests.Response, Dict[str, Any], None]) -> Dict[str, Any]:
        if isinstance(payload, dict):
            return payload
        if hasattr(payload, "json"):
            try:
                return payload.json()
            except Exception:
                return {}
        return {}

    @staticmethod
    def get_raw_json(payload: Union[requests.Response, Dict[str, Any]]) -> Dict[str, Any]:
        return JsonResponseHandler._coerce_to_json(payload)

    @staticmethod
    def walk_path(data: Dict[str, Any], path: List[str]) -> Any:
        for key in path:
            if isinstance(data, dict):
                data = data.get(key, {})
            else:
                return {}
        return data

    @staticmethod
    def get_edges_from_path(payload: Union[requests.Response, Dict[str, Any]], path: List[str]) -> List[Dict[str, Any]]:
        data = JsonResponseHandler.get_raw_json(payload)
        #print(f"data = {data}")
        module_data = JsonResponseHandler.walk_path(data.get("data", {}), path)
        return module_data.get("edges", [])


    @staticmethod
    def get_page_info_from_path(payload: Union[requests.Response, Dict[str, Any]], path: List[str]) -> Dict[str, Any]:
        data = JsonResponseHandler.get_raw_json(payload)
        module_data = JsonResponseHandler.walk_path(data.get("data", {}), path)
        return module_data.get("pageInfo", {})

    @staticmethod
    def get_ids_from_path(response: requests.Response, path: List[str]) -> List[str]:
        edges = JsonResponseHandler.get_edges_from_path(response, path)
        return [edge.get("node", {}).get("id") for edge in edges if "node" in edge]

    @staticmethod
    def get_nested_field_from_path(
        response: Union[requests.Response, Dict[str, Any]],
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
    def get_end_cursor_from_path(payload: Union[requests.Response, Dict[str, Any]], path: List[str]) -> Optional[str]:
        page_info = JsonResponseHandler.get_page_info_from_path(payload, path)
        return page_info.get("endCursor")

    @staticmethod
    def is_last_page_from_path(payload: Union[requests.Response, Dict[str, Any]], path: List[str]) -> bool:
        page_info = JsonResponseHandler.get_page_info_from_path(payload, path)
        return page_info.get("lastPage", False)

    @staticmethod    
    def get_page_detalils_from_path(payload:Union[requests.Response, Dict[str, Any]],path:list)->tuple:
        page_info = JsonResponseHandler.get_page_info_from_path(payload, path)
        end_cursor = page_info.get("endCursor")
        has_next_page = page_info.get("hasNextPage", False)
        count = page_info.get("count", 0)
        return end_cursor, has_next_page, count

class GetValuFromEdge:

    @staticmethod
    def get_cadastral_unit_number(edge: Dict[str, Any]) -> str:
        node = edge.get("node", {})
        return node.get("cadastralUnitNumber", False)
