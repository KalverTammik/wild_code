# -*- coding: utf-8 -*-
from __future__ import annotations
from typing import Optional, List, Dict, Any, Callable
from ..utils.api_client import APIClient
from ..utils.GraphQLQueryLoader import GraphQLQueryLoader
# from ..utils.logger import debug as log_debug

class UnifiedFeedLogic:
    """
    Ühtne GraphQL feed-loogika (paginatsioon + where), sobib Projects/Contracts jms.
    Ei ole üleliia keeruline, aga sisaldab mugavaid välju: last_error, total_count, root_field tuletus.
    """

    def __init__(
        self,
        module_name: str,
        query_name: str,
        lang_manager=None,
        *,
        batch_size: int = 5,
        root_field: Optional[str] = None,
        map_node: Optional[Callable[[Dict[str, Any]], Dict[str, Any]]] = None,
    ) -> None:
        self.api_client = APIClient()
        self.query_loader = GraphQLQueryLoader(lang_manager)
        self.query: str = self.query_loader.load_query(module_name, query_name)

        # root_field tuletus: "PROJECT" -> "projects", "CONTRACT" -> "contracts"
        default_root = (module_name or "").strip().lower()
        if default_root.endswith("s"):
            inferred = default_root
        elif default_root:
            inferred = f"{default_root}s"
        else:
            inferred = "items"
        self.root_field: str = root_field or inferred

        self.map_node = map_node
        self.batch_size: int = int(batch_size) if batch_size else 5

        # Pagination & state
        self.end_cursor: Optional[str] = None
        self.has_more: bool = True
        self.is_loading: bool = False
        self.where: Optional[Dict[str, Any]] = None
        self._extra_args: Dict[str, Any] = {}
        self.last_response: Optional[Dict[str, Any]] = None
        self.last_error: Optional[Exception] = None
        self.total_count: Optional[int] = None

    def reset(self) -> None:
        """Reset pagination/loading flags without changing current 'where'."""
        self.end_cursor = None
        self.has_more = True
        self.total_count = None
        self.last_error = None

    def set_where(self, where: Optional[Dict[str, Any]]) -> None:
        self.where = where
        self.reset()

    def set_extra_arguments(self, **kwargs: Any) -> None:
        """Store additional GraphQL arguments (e.g., hasTags) passed alongside where."""
        cleaned = {k: v for k, v in kwargs.items() if v is not None}
        if cleaned == self._extra_args:
            return
        self._extra_args = cleaned
        self.reset()

    def fetch_next_batch(self) -> List[Dict[str, Any]]:
        if self.is_loading or not self.has_more:
            return []

        self.is_loading = True
        self.last_error = None

        variables: Dict[str, Any] = {
            "first": self.batch_size,
            "after": self.end_cursor,
        }
        if self.where:
            variables["where"] = self.where
        if self._extra_args:
            variables.update(self._extra_args)

        try:
            #print(f"[FeedLogic] GraphQL query variables: {variables}")
            #print(f"[FeedLogic] GraphQL query: {self.query}")
            data: Dict[str, Any] = self.api_client.send_query(self.query, variables) or {}
            #print(f"[FeedLogic] API response: {data}")
            self.last_response = data

            # GraphQL error pinda
            errors = data.get("errors")
            if isinstance(errors, list) and errors:
                self.last_error = Exception(str(errors[-1]))
                # log_debug(f"[UnifiedFeedLogic] GraphQL errors: {errors}")

            root: Dict[str, Any] = data.get(self.root_field) or {}
            edges: List[Dict[str, Any]] = root.get("edges") or []

            page_info: Dict[str, Any] = root.get("pageInfo") or {}
            #print(f"[FeedLogic] GraphQL pageInfo: {page_info}")
            # Prefer item totalCount on root if available; some APIs put page count in pageInfo.total
            root_total = root.get("totalCount") if isinstance(root, dict) else None
            page_total = page_info.get("total") if isinstance(page_info, dict) else None
            self.total_count = root_total if root_total is not None else page_total

            # Heuristic: if total looks like a small number of pages (<= number of fetched pages) while
            # we have already loaded more items than that number, invalidate it so UI can adapt.
            try:
                if isinstance(self.total_count, int):
                    # pages_seen approximated by (loaded_items // batch_size) + 1
                    loaded_items_guess = getattr(self, '_loaded_items_debug', 0)
                    if loaded_items_guess == 0:
                        loaded_items_guess = 0
                    pages_seen = (loaded_items_guess // max(1, self.batch_size)) + 1 if loaded_items_guess else 1
                    if self.total_count <= pages_seen and loaded_items_guess > self.total_count:
                        # Mark unknown so counter can show only loaded or loaded+
                        self.total_count = None
            except Exception:
                pass

            self.end_cursor = page_info.get("endCursor") if isinstance(page_info, dict) else None
            self.has_more = bool(page_info.get("hasNextPage", False)) if isinstance(page_info, dict) else False

            result: List[Dict[str, Any]] = []
            for edge in edges:
                if not isinstance(edge, dict):
                    continue
                node = edge.get("node")
                if not isinstance(node, dict):
                    continue
                result.append(self.map_node(node) if self.map_node else node)

            # Track loaded items for heuristics
            try:
                prev = getattr(self, '_loaded_items_debug', 0)
                setattr(self, '_loaded_items_debug', prev + len(result))
            except Exception:
                pass

            return result

        except Exception as e:
            self.last_error = e
            # log_debug(f"[UnifiedFeedLogic] Exception during fetch: {e}")
            return []
        finally:
            self.is_loading = False

    # Introspection
    def has_more_items(self) -> bool:
        return self.has_more

    def get_total_count(self) -> Optional[int]:
        return self.total_count

    def get_last_error(self) -> Optional[Exception]:
        return self.last_error
