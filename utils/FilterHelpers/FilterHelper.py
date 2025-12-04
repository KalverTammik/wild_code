from typing import List, Dict, Optional, Sequence, Tuple
from PyQt5.QtCore import Qt

from ...utils.url_manager import ModuleSupports

from ...python.GraphQLQueryLoader import GraphQLQueryLoader
from ...python.responses import JsonResponseHandler
from ...python.api_client import APIClient


class FilterHelper:
    @staticmethod
    def get_filter_edges_by_key_and_module(key, module) -> List[str]:
        print(f"Fetching filter edges for key: {key}, module: {module}")
        key_map = {
            ModuleSupports.TAGS.value: "ListModuleTags.graphql",
            ModuleSupports.STATUSES.value: "ListModuleStatuses.graphql",
            ModuleSupports.TYPES.value: f"{module}_types.graphql",
        }

        query = GraphQLQueryLoader().load_query_by_module(key, key_map.get(key))
        variables = {
            "first": 50,
            "after": None,
            "where": {"column": "MODULE", "value": f"{str(module).upper()}S"},
        }

        if key == ModuleSupports.TYPES.value:
            edges = []
            after: Optional[str] = None
            path = [f"{module}Types"]
            while True:
                variables["after"] = after
                payload = APIClient().send_query(query, variables=variables, return_raw=True) or {}
                page_edges = JsonResponseHandler.get_edges_from_path(payload, path)
                edges.extend(page_edges)

                page_info = JsonResponseHandler.get_page_info_from_path(payload, path)
                has_next = bool(page_info.get("hasNextPage"))
                after = page_info.get("endCursor") if has_next else None
                if not has_next or not after:
                    break
            entries: List[Dict[str, Optional[str]]] = []
            for edge in edges:
                node = (edge or {}).get("node") or {}
                type_id = node.get("id")
                label = node.get("name")
                group_name = (node.get("group") or {}).get("name") if isinstance(node.get("group"), dict) else None

                def group_key(label: str) -> str:
                    """Prefix before first ' - ' (or whole label if not present)."""
                    parts = (label or "").split(" - ", 1)
                    return parts[0].strip() if parts else (label or "").strip()

                if not group_name:
                    group_name = group_key(label)
                if type_id and label:
                    entries.append({"id": type_id, "label": label, "group": group_name})
            return entries
        
        else:
            data = APIClient().send_query(query, variables=variables, return_raw=True) or {}
            edges = JsonResponseHandler.get_edges_from_path(data, [key])
            entries: List[Tuple[str, str]] = []
            for edge in edges:
                node = (edge or {}).get("node") or {}
                sid = node.get("id")
                label = node.get("name")
                if sid and label:
                    entries.append((label, sid))
            return entries

    @staticmethod
    def set_selected_ids(widget, ids: Sequence[str], emit: bool = True) -> None:
        ids_set = {str(v) for v in ids or []}
        widget._suppress_emit = True
        try:
            for row in range(widget.combo.count()):
                val = widget.combo.itemData(row)
                state = Qt.Checked if str(val) in ids_set else Qt.Unchecked
                widget.combo.setItemCheckState(row, state)
        finally:
            widget._suppress_emit = False
        if emit:
            widget._emit_selection_change()

    @staticmethod
    def selected_ids(widget) -> List[str]:
        return list(widget.combo.checkedItemsData() or [])  

    @staticmethod
    def selected_texts(widget) -> List[str]:
        return list(widget.combo.checkedItems() or [])  

    @staticmethod
    def cancel_pending_load(
        widget,
        *,
        invalidate_request: bool = True,
        load_request_attr: str = "_load_request_id",
        worker_attr: str = "_worker",
        thread_attr: str = "_worker_thread",
    ) -> None:
        if not widget:
            return
        try:
            if invalidate_request and hasattr(widget, load_request_attr):
                current = getattr(widget, load_request_attr, 0) or 0
                setattr(widget, load_request_attr, current + 1)

            thread = getattr(widget, thread_attr, None)
            is_running = bool(thread and callable(getattr(thread, "isRunning", None)) and thread.isRunning())

            if hasattr(widget, worker_attr):
                setattr(widget, worker_attr, None)
            if hasattr(widget, thread_attr):
                setattr(widget, thread_attr, None)

            if thread is not None and callable(getattr(thread, "isRunning", None)) and thread.isRunning():
                try:
                    thread.quit()
                    thread.wait(50)
                except Exception:
                    pass

            if is_running and hasattr(widget, "loadFinished"):
                try:
                    widget.loadFinished.emit(False)
                except Exception:
                    pass
        except Exception:
            pass