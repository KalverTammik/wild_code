

from ...utils.api_client import APIClient
from ...utils.GraphQLQueryLoader import GraphQLQueryLoader

class ProjectsFeedLogic:
    def __init__(self, module_name, query_name, lang_manager, batch_size=5):
        self.api_client = APIClient(lang_manager)
        self.query_loader = GraphQLQueryLoader(lang_manager)
        self.query = self.query_loader.load_query(module_name, query_name)
        self.batch_size = batch_size
        self.end_cursor = None
        self.has_more = True
        self.is_loading = False

    def fetch_next_batch(self):
        if self.is_loading or not self.has_more:
            return []
        self.is_loading = True
        variables = {
            "first": self.batch_size,
            "after": self.end_cursor,
        }
        try:
            data = self.api_client.send_query(self.query, variables)
            projects = data.get("projects", {}).get("edges", [])
            page_info = data.get("projects", {}).get("pageInfo", {})
            self.end_cursor = page_info.get("endCursor")
            self.has_more = page_info.get("hasNextPage", False)
            return [edge["node"] for edge in projects]
        finally:
            self.is_loading = False
