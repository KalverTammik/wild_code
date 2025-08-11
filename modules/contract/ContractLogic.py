from ...utils.api_client import APIClient
from ...utils.GraphQLQueryLoader import GraphQLQueryLoader

class ContractLogic:
    """
    Non-UI logic for the Contract module. Extend this with data loading,
    API calls, and business rules. Keep UI concerns out of this class.
    """
    def __init__(self, lang_manager=None):
        self.lang_manager = lang_manager
        self._activated = False

    def activate(self):
        """Hook for when the module is shown/activated in the UI."""
        self._activated = True

    def deactivate(self):
        """Hook for when the module is hidden/deactivated in the UI."""
        self._activated = False

    def get_welcome_text(self):
        """Return the localized welcome/loaded text for the UI."""
        base_text = "Contract module loaded!"
        if self.lang_manager:
            try:
                return self.lang_manager.translate(base_text)
            except Exception:
                return base_text
        return base_text

class ContractsFeedLogic:
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
            edges = data.get("contracts", {}).get("edges", [])
            page_info = data.get("contracts", {}).get("pageInfo", {})
            self.end_cursor = page_info.get("endCursor")
            self.has_more = page_info.get("hasNextPage", False)
            return [edge.get("node") for edge in edges]
        finally:
            self.is_loading = False
