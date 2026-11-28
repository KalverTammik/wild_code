"""Reading the tags of a module."""
from __future__ import annotations

from typing import Optional

from ..api_client import APIClient
from ..GraphQLQueryLoader import GraphQLQueryLoader
from ..tag_catalog import TagCatalog
from ...constants.module_names import ModuleSupports
from .status_actions import StatusActions

_PAGE_SIZE = 50  # the most Kavitro returns in one page
_MAX_PAGES = 40  # a stop for a server that never says it is done


class TagActions:
    """Static tag actions; APIModuleActions inherits them so callers keep one entry point."""

    @staticmethod
    def get_module_tag_catalog(module_name: str) -> TagCatalog:
        """Every tag of the module with its group. A failed or unfinished read raises."""
        module_value = StatusActions.status_module_value(module_name)
        if not module_value:
            raise ValueError("A module name is required to read tags")

        query = GraphQLQueryLoader().load_query_by_module(ModuleSupports.TAGS.value, "ModuleTagsWithGroups.graphql")
        client = APIClient()
        nodes: list[dict] = []
        after: Optional[str] = None
        for _page in range(_MAX_PAGES):
            variables = {
                "first": _PAGE_SIZE,
                "after": after,
                "where": {"column": "MODULE", "operator": "EQ", "value": module_value},
            }
            data = client.send_query(query, variables=variables) or {}
            connection = data.get("tags")
            page_info = (connection or {}).get("pageInfo")
            if not isinstance(page_info, dict):
                raise RuntimeError("The tag list answer has no page information")
            nodes.extend((edge or {}).get("node") or {} for edge in connection.get("edges") or [])
            if not page_info.get("hasNextPage"):
                return TagCatalog.from_nodes(nodes)
            cursor = page_info.get("endCursor")
            if not cursor or cursor == after:
                raise RuntimeError("The tag list says there is more but gives no new cursor")
            after = cursor
        raise RuntimeError(f"The tag list did not end within {_MAX_PAGES} pages")
