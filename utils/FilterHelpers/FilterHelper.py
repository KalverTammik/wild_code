from typing import List, Dict, Optional, Sequence, Tuple, Union
from PyQt5.QtCore import Qt

from ...utils.url_manager import ModuleSupports, Module
from ...modules.Settings.SettinsUtils.SettingsLogic import SettingsLogic

from ...python.GraphQLQueryLoader import GraphQLQueryLoader
from ...python.responses import JsonResponseHandler
from ...python.api_client import APIClient
from ...Logs.python_fail_logger import PythonFailLogger
from ...Logs.switch_logger import SwitchLogger


class FilterHelper:
    @staticmethod
    def get_filter_edges_by_key_and_module(
        key,
        module,
    ) -> Union[List[Dict[str, Optional[str]]], List[Tuple[str, str]]]:
        #print(f"[FilterHelper] Fetching filter edges for key: {key}, module: {module}")
        key_map = {
            ModuleSupports.TAGS.value: "ListModuleTags.graphql",
            ModuleSupports.STATUSES.value: "ListModuleStatuses.graphql",
            ModuleSupports.TYPES.value: f"{module}_types.graphql",
        }

        if module == Module.PROPERTY.name.lower():
            module_value = "PROPERTIES"
        else:
            module_value = str(module).upper() + "S"

        query = GraphQLQueryLoader().load_query_by_module(key, key_map.get(key))
        variables = {
            "first": 50,
            "after": None,
            # IMPORTANT: value must be JSON-serializable (no Python set)
            "where": {"column": "MODULE", "operator": "EQ", "value": module_value},
        }

        if key == ModuleSupports.TYPES.value:
            after: Optional[str] = None
            path = [f"{module}Types"]
            entries: List[Dict[str, Optional[str]]] = []

            def group_key(label: str) -> str:
                """Prefix before first ' - ' (or whole label if not present)."""
                parts = (label or "").split(" - ", 1)
                return parts[0].strip() if parts else (label or "").strip()

            while True:
                variables["after"] = after
                payload = APIClient().send_query(query, variables=variables, return_raw=True) or {}
                page_edges = JsonResponseHandler.get_edges_from_path(payload, path)

                for edge in page_edges:
                    node = (edge or {}).get("node") or {}
                    type_id = node.get("id")
                    label = node.get("name")
                    group_name = (node.get("group") or {}).get("name") if isinstance(node.get("group"), dict) else None
                    if not group_name:
                        group_name = group_key(label)
                    if type_id and label:
                        entries.append({"id": type_id, "label": label, "group": group_name})

                page_info = JsonResponseHandler.get_page_info_from_path(payload, path)
                has_next = bool(page_info.get("hasNextPage"))
                after = page_info.get("endCursor") if has_next else None
                if not has_next or not after:
                    break

            #print(f"[FilterHelper] Fetched {entries} entries for types.")
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
        values = list(widget.combo.checkedItemsData() or [])
        return [v for v in values if v]

    @staticmethod
    def selected_texts(widget) -> List[str]:
        values = list(widget.combo.checkedItems() or [])
        return [v for v in values if v]

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
                try:
                    current = int(getattr(widget, load_request_attr, 0) or 0)
                    setattr(widget, load_request_attr, current + 1)
                except Exception:
                    pass
            thread = getattr(widget, thread_attr, None)
            is_running = bool(thread and callable(getattr(thread, "isRunning", None)) and thread.isRunning())

            if hasattr(widget, worker_attr):
                setattr(widget, worker_attr, None)
            if hasattr(widget, thread_attr):
                setattr(widget, thread_attr, None)

            if thread is not None and callable(getattr(thread, "isRunning", None)) and thread.isRunning():
                try:
                    thread.quit()
                except Exception as exc:
                    PythonFailLogger.log_exception(
                        exc,
                        module="filter",
                        event="filter_thread_quit_failed",
                    )

            if is_running and invalidate_request and hasattr(widget, "loadFinished"):
                try:
                    widget.loadFinished.emit(False)
                except Exception as exc:
                    PythonFailLogger.log_exception(
                        exc,
                        module="filter",
                        event="filter_load_finished_emit_failed",
                    )
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module="filter",
                event="filter_cancel_pending_load_failed",
            )


    @staticmethod
    def build_has_tags_condition(
        tag_ids: Sequence[str],
        *,
        match_mode: Optional[str] = None,
        default_mode: str = "ANY",
    ) -> Optional[dict]:
        """Map tag selections to Kavitro Query*HasTagsWhereHasConditions."""
        ids = [str(tag_id).strip() for tag_id in tag_ids if tag_id]
        if not ids:
            return None

        mode = (match_mode or default_mode or "ANY").upper()
        if mode == "ALL":
            return {
                "AND": [
                    {"column": "ID", "operator": "EQ", "value": tag_id}
                    for tag_id in ids
                ]
            }

        return {"column": "ID", "operator": "IN", "value": ids}



class FilterRefreshService:
    """Shared filter refresh pipeline for module UIs."""

    @staticmethod
    def _selected_type_ids(type_filter) -> List[str]:
        if type_filter is None:
            return []
        if hasattr(type_filter, "combo"):
            return FilterHelper.selected_ids(type_filter)
        selected = getattr(type_filter, "selected_ids", None)
        return list(selected()) if callable(selected) else []

    @staticmethod
    def _resolve_ids(
        module,
        status_ids,
        type_ids,
        tags_ids,
        *,
        status_filter,
        type_filter,
        tags_filter,
        status_getter,
        type_getter,
        tags_getter,
    ) -> Dict[str, List[str]]:
        resolved_status = status_ids
        resolved_type = type_ids
        resolved_tags = tags_ids

        if resolved_status is None and status_filter is not None:
            resolved_status = FilterHelper.selected_ids(status_filter)
            if not resolved_status:
                if callable(status_getter):
                    resolved_status = status_getter() or []

        if resolved_type is None and type_filter is not None:
            resolved_type = FilterRefreshService._selected_type_ids(type_filter)
            if not resolved_type:
                if callable(type_getter):
                    resolved_type = type_getter() or []

        if resolved_tags is None and tags_filter is not None:
            resolved_tags = FilterHelper.selected_ids(tags_filter)
            if not resolved_tags:
                if callable(tags_getter):
                    resolved_tags = tags_getter() or []

        return {
            "status": resolved_status or [],
            "type": resolved_type or [],
            "tags": resolved_tags or [],
        }

    @staticmethod
    def refresh_filters(
        module,
        *,
        status_ids=None,
        type_ids=None,
        tags_ids=None,
        status_filter=None,
        type_filter=None,
        tags_filter=None,
        status_getter=None,
        type_getter=None,
        tags_getter=None,
        reset_overdue_pills: bool = False,
        force_list_mode: bool = True,
    ) -> None:
        if getattr(module, "_suppress_filter_events", False):
            return

        status_filter = status_filter if status_filter is not None else getattr(module, "status_filter", None)
        type_filter = type_filter if type_filter is not None else getattr(module, "type_filter", None)
        tags_filter = tags_filter if tags_filter is not None else getattr(module, "tags_filter", None)

        status_getter = status_getter if status_getter is not None else lambda: FilterRefreshService.saved_status_ids(module)
        type_getter = type_getter if type_getter is not None else lambda: FilterRefreshService.saved_type_ids(module)
        tags_getter = tags_getter if tags_getter is not None else lambda: FilterRefreshService.saved_tag_ids(module)

        feed_load_engine = getattr(module, "feed_load_engine", None)
        buffer = getattr(feed_load_engine, "buffer", None)
        if buffer is not None and hasattr(buffer, "clear"):
            buffer.clear()

        ids = FilterRefreshService._resolve_ids(
            module,
            status_ids,
            type_ids,
            tags_ids,
            status_filter=status_filter,
            type_filter=type_filter,
            tags_filter=tags_filter,
            status_getter=status_getter,
            type_getter=type_getter,
            tags_getter=tags_getter,
        )
        try:
            module_key = getattr(module, "module_key", None) or getattr(module, "name", None) or ""
            SwitchLogger.log(
                "filter_refresh",
                module=str(module_key),
                extra={
                    "status_count": len(ids.get("status") or []),
                    "type_count": len(ids.get("type") or []),
                    "tags_count": len(ids.get("tags") or []),
                },
            )
        except Exception:
            pass

        and_list: List[dict] = []
        if ids["status"]:
            and_list.append({"column": "STATUS", "operator": "IN", "value": ids["status"]})
        supports_type = bool(getattr(module, "supports_type_filter", False))
        if supports_type and ids["type"]:
            and_list.append({"column": "TYPE", "operator": "IN", "value": ids["type"]})

        where = {"AND": and_list} if and_list else None

        if ids["tags"]:
            build_has_tags = getattr(module, "_build_has_tags_condition", None)
            if callable(build_has_tags):
                has_tags_filter = build_has_tags(ids["tags"])
            else:
                default_mode = getattr(module, "tags_match_mode", None)
                has_tags_filter = FilterHelper.build_has_tags_condition(
                    ids["tags"], match_mode=default_mode
                )
        else:
            has_tags_filter = None

        feed_logic = getattr(module, "feed_logic", None)
        if feed_logic is None:
            feed_logic_cls = getattr(module, "FEED_LOGIC_CLS", None)
            module_key = getattr(module, "module_key", None)
            query_file = getattr(module, "QUERY_FILE", None)
            lang_manager = getattr(module, "lang_manager", None)
            if feed_logic_cls and module_key and query_file:
                feed_logic = feed_logic_cls(module_key, query_file, lang_manager)
                setattr(module, "feed_logic", feed_logic)

        single_item_query = getattr(module, "SINGLE_ITEM_QUERY_FILE", None)
        if feed_logic is not None and single_item_query:
            configure_single = getattr(feed_logic, "configure_single_item_query", None)
            if callable(configure_single):
                configure_single(single_item_query)

        if force_list_mode and feed_logic is not None:
            set_single_mode = getattr(feed_logic, "set_single_item_mode", None)
            if callable(set_single_mode):
                set_single_mode(False)

        if feed_logic is not None:
            set_where = getattr(feed_logic, "set_where", None)
            if callable(set_where):
                set_where(where)
            set_extra = getattr(feed_logic, "set_extra_arguments", None)
            if callable(set_extra):
                set_extra_arguments = {"hasTags": has_tags_filter}
                set_extra(**set_extra_arguments)

        if hasattr(module, "_current_where"):
            setattr(module, "_current_where", where)

        clear_feed = getattr(module, "clear_feed", None)
        feed_layout = getattr(module, "feed_layout", None)
        empty_state = getattr(module, "_empty_state", None)
        if callable(clear_feed) and feed_layout is not None:
            clear_feed(feed_layout, empty_state)

        scroll_area = getattr(module, "scroll_area", None)
        if scroll_area is not None and scroll_area.verticalScrollBar() is not None:
            scroll_area.verticalScrollBar().setValue(0)

        if feed_load_engine is not None:
            schedule = getattr(feed_load_engine, "schedule_load", None)
            if callable(schedule):
                schedule()

        if reset_overdue_pills and getattr(module, "overdue_pills", None):
            module.overdue_pills.set_overdue_active(False)
            module.overdue_pills.set_due_soon_active(False)


# ------------------------------------------------------------------
# Saved filter accessors (centralized)
# ------------------------------------------------------------------

    @staticmethod
    def saved_status_ids(module) -> List[str]:
        return FilterRefreshService.saved_filter_ids(module, "status")

    @staticmethod
    def saved_type_ids(module) -> List[str]:
        return FilterRefreshService.saved_filter_ids(module, "type")

    @staticmethod
    def saved_tag_ids(module) -> List[str]:
        return FilterRefreshService.saved_filter_ids(module, "tag")

    @staticmethod
    def saved_filter_ids(module, kind: str) -> List[str]:
        logic = getattr(module, "_settings_logic", None) or SettingsLogic()
        module_key = getattr(module, "module_key", None)
        if not logic or not module_key:
            return []
        support_map = {
            "status": ModuleSupports.STATUSES.value,
            "type": ModuleSupports.TYPES.value,
            "tag": ModuleSupports.TAGS.value,
        }
        support_key = support_map.get(kind)
        if not support_key:
            return []

        values = logic.load_module_preference_ids(module_key, support_key=support_key) or []
        return [str(token).strip() for token in values if str(token).strip()]