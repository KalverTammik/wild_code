from ..python.GraphQLQueryLoader import GraphQLQueryLoader
from ..python.api_client import APIClient
from ..utils.url_manager import ModuleSupports



MODULE = ModuleSupports.TAGS


def _normalize_tag_module(module: str) -> str:
    """Normalize module value used in tag queries (e.g. 'property' -> 'properties')."""
    m = (str(module) if module is not None else "").strip().lower()
    if not m:
        return ""
    if m.endswith("s"):
        return m
    if m.endswith("y"):
        return f"{m[:-1]}ies"
    return f"{m}s"


def _tag_module_enum(module: str) -> str:
    """GraphQL TagModule enum is case-sensitive (e.g. PROPERTIES, PROJECTS)."""
    return _normalize_tag_module(module).upper()


def _unwrap_data(response: dict) -> dict:
    if not isinstance(response, dict):
        return {}
    # APIClient.send_query() returns `data` by default, but some call sites may still pass raw.
    return response.get("data", response)


class TagsEngines:

    ARHIVEERITUD_TAG_NAME = "Arhiveeritud"
    ARHIVEERITUD_NAME_ADDITION = "ARHIVEERITUD"
    @staticmethod
    def create_tag(tag_name: str, module: str) -> str:
        module_tags = ModuleSupports.TAGS.value
        tag_module = _tag_module_enum(module)

        query_file = "CreateTag.graphql"
        query = GraphQLQueryLoader().load_query_by_module(module=module_tags, query_filename=query_file)

        variables = {
            "input": {
                "name": tag_name,
                "module": tag_module
            }
        }

        client = APIClient()
        response = client.send_query(query, variables=variables)

        data = _unwrap_data(response)
        created_tag = (data or {}).get("createTag") or {}
        created_tag_id = created_tag["id"]
        print(f"Tag created: ID {created_tag_id} -> Name: {created_tag['name']}")
        return created_tag_id

    @staticmethod
    def load_tags_by_module(module: str ,first: int = 50, after: str = None, ) -> list:
        module_tags = ModuleSupports.TAGS.value
        backend_module = _normalize_tag_module(module)
        query_file = 'IDByModuleAndName.graphql'
        query = GraphQLQueryLoader().load_query_by_module(module=module_tags, query_filename=query_file)

        variables = {
            "first": first,
            "after": after,
            "where": {
                "column": "MODULE",
                "value": backend_module
            }
        }

        client = APIClient()
        response = client.send_query(query, variables=variables)

        data = _unwrap_data(response)
        tags_data = (data or {}).get("tags") or {}
        edges = tags_data.get("edges") or []
        tags = [edge.get("node") for edge in edges if isinstance(edge, dict) and edge.get("node")]

        print(f"Loaded {len(tags)} tags for {module} module:")
        for tag in tags:
            print(f" - {tag['id']}: {tag['name']}")

        return tags

    @staticmethod
    def get_modules_tag_id_by_name(tag_name: str,module: str) -> str: 
        #tag_name = "Arhiveeritud"
        module_tags = ModuleSupports.TAGS.value
        backend_module = _normalize_tag_module(module)

        query_file = 'IDByModuleAndName.graphql'
        query = GraphQLQueryLoader().load_query_by_module(module=module_tags, query_filename=query_file)
        #print(f"query_file: {query_file}, module: {module_tags}")

        variables = {
            "first": 50,
            "after": None,
            "where": {
                "column": "MODULE",
                "value": backend_module
            }
        }

        client = APIClient()
        response = client.send_query(query, variables=variables)
        data = _unwrap_data(response)
        tags = ((data or {}).get("tags") or {}).get("edges") or []
        for tag in tags:
            if tag["node"]["name"].lower() == tag_name.lower():
                #print(f"Found tag '{tag_name}' -> ID: {tag['node']['id']}")
                return tag["node"]["id"]

        #print(f"Tag '{tag_name}' not found in module '{module}'")
        return None
    

class TagsHelpers:

    @staticmethod
    def check_if_tag_exists(tag_name: str, module: str) -> bool:
        #print(f"Checking if tag '{tag_name}' exists in module '{module}'...")
        tag_id = TagsEngines.get_modules_tag_id_by_name(tag_name=tag_name, module=module)
        if tag_id is None:
            res = TagsEngines.create_tag(tag_name=tag_name, module=module)

            if res is not False:
                tag_id=res

        return tag_id