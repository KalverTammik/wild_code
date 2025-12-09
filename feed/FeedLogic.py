# -*- coding: utf-8 -*-
from __future__ import annotations
from typing import Optional, List, Dict, Any, Callable
from ..python.api_client import APIClient
from ..python.GraphQLQueryLoader import GraphQLQueryLoader
from ..python.responses import JsonResponseHandler
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
        self.query_loader = GraphQLQueryLoader()
        # Base configuration
        self._module_name = module_name
        self._base_query_name = query_name
        self._single_item_query_name: Optional[str] = None
        self._single_item_mode: bool = False
        self.query: str = self.query_loader.load_query_by_module(module_name, query_name)

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

    # --- Query mode management -------------------------------------------------
    def configure_single_item_query(self, query_name: str) -> None:
        """Configure an alternate GraphQL query used for single-item mode.

        The ``query_name`` should be a file that can be resolved by
        GraphQLQueryLoader.load_query_by_module for the same module.
        This does not enable single-item mode by itself; call
        ``set_single_item_mode(True, id=...)`` to activate.
        """
        #print(f"[FeedLogic] Configuring single item query: {query_name}")
        self._single_item_query_name = query_name

    def set_single_item_mode(self, enabled: bool, *, id: Optional[str] = None, **extra_vars: Any) -> None:
        """Switch between normal list mode and single-item-by-id mode.

        When enabled and a single-item query has been configured, the next
        ``fetch_next_batch`` call will:
        - Use the configured single-item query instead of the base list query
        - Ignore pagination (``first``/``after``) and ``where``
        - Send only the provided ``id`` and any ``extra_vars`` as variables
        """
        self._single_item_mode = bool(enabled)
        self.reset()
        # In single-item mode we must not leak list-mode extras (e.g. hasTags)
        # into the by-id query variables. Always rebuild _extra_args from
        # scratch when toggling the mode.
        self._extra_args.clear()
        # Store the id/extra vars into _extra_args so fetch_next_batch can see them
        if id is not None:
            self._extra_args["id"] = id
        self._extra_args.update({k: v for k, v in extra_vars.items() if v is not None})

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
        if self.is_loading or (not self.has_more and not self._single_item_mode):
            return []

        self.is_loading = True
        self.last_error = None

        # Build variables and query depending on mode
        if self._single_item_mode and self._single_item_query_name:
            # Single-item: ignore pagination/where and use only id + extra vars
            variables: Dict[str, Any] = {}
            if self._extra_args:
                variables.update(self._extra_args)

            self.query = self.query_loader.load_query_by_module(
                self._module_name,
                self._single_item_query_name,
            )

        else:
            variables = {
                "first": self.batch_size,
                "after": self.end_cursor,
            }
            if self.where:
                variables["where"] = self.where
            if self._extra_args:
                variables.update(self._extra_args)

            # Ensure list-mode query is loaded
            self.query = self.query_loader.load_query_by_module(
                self._module_name,
                self._base_query_name,
            )

        try:
            payload: Dict[str, Any] = self.api_client.send_query(
                self.query,
                variables,
                return_raw=True,
            ) or {}
            #print(f"[FeedLogic] Fetch payload: {payload}")
            # Debug logging for single-item mode removed after verification
            self.last_response = payload

            # In single-item mode, many queries return a single object
            # instead of an edges list. Handle that here and bypass the
            # generic edges/pageInfo logic so modules receive a list with
            # exactly one node (or an empty list if nothing was found).
            if self._single_item_mode:
                data = payload.get("data") or {}
                #print(f"[FeedLogic] Single-item mode payload data: {data}")
                single: Optional[Dict[str, Any]] = None

                # Heuristic: look for common single-item roots by module
                if "project" in data:
                    single = data.get("project")
                elif "contract" in data:
                    single = data.get("contract")
                elif "coordination" in data:
                    single = data.get("coordination")

                if isinstance(single, dict):
                    self.end_cursor = None
                    self.has_more = False
                    node = self.map_node(single) if self.map_node else single
                    result = [node]
                else:
                    # No single object found; treat as empty result
                    self.end_cursor = None
                    self.has_more = False
                    result = []

                return result

            path = [self.root_field]
            root: Dict[str, Any] = JsonResponseHandler.walk_path(
                payload.get("data") or {},
                path,
            ) or {}
            edges: List[Dict[str, Any]] = JsonResponseHandler.get_edges_from_path(payload, path)
            page_info: Dict[str, Any] = JsonResponseHandler.get_page_info_from_path(payload, path)
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

            # In single-item mode we expect only one page; mark as finished.
            if self._single_item_mode:
                self.end_cursor = None
                self.has_more = False
            else:
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
            #print(f"[UnifiedFeedLogic] fetched {len(result)} items (has_more={self.has_more})")
            return result

        except Exception as e:
            self.last_error = e
            try:
                print(f"[UnifiedFeedLogic] fetch error for module '{self._module_name}': {e}")
            except Exception:
                pass
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
