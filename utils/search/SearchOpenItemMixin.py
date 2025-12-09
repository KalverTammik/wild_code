from typing import Any, Optional
from PyQt5.QtWidgets import QScrollArea


class SearchOpenItemMixin:
    """Shared helper to open a single item from unified search.

    Expects host modules to expose feed-related attributes; guards are used so
    missing capabilities degrade gracefully without exceptions.
    """

    def open_item_from_search(self, search_module: str, item_id: str, title: str) -> None:
        feed_load_engine = getattr(self, "feed_load_engine", None)
        if feed_load_engine is not None:
            cancel_pending = getattr(feed_load_engine, "cancel_pending", None)
            if callable(cancel_pending):
                cancel_pending()
            buffer = getattr(feed_load_engine, "buffer", None)
            if buffer is not None and hasattr(buffer, "clear"):
                buffer.clear()

        clear_feed = getattr(self, "clear_feed", None)
        feed_layout = getattr(self, "feed_layout", None)
        empty_state = getattr(self, "_empty_state", None)
        if callable(clear_feed) and feed_layout is not None:
            clear_feed(feed_layout, empty_state)

        feed_logic = getattr(self, "feed_logic", None)
        feed_logic_cls = getattr(self, "FEED_LOGIC_CLS", None)
        module_key = getattr(self, "module_key", None)
        query_file = getattr(self, "QUERY_FILE", None)
        single_item_query = getattr(self, "SINGLE_ITEM_QUERY_FILE", None)
        lang_manager = getattr(self, "lang_manager", None)

        if feed_logic is None and feed_logic_cls and module_key and query_file:
            feed_logic = feed_logic_cls(module_key, query_file, lang_manager)
            setattr(self, "feed_logic", feed_logic)

        if feed_logic is not None:
            configure_single = getattr(feed_logic, "configure_single_item_query", None)
            if callable(configure_single) and single_item_query:
                configure_single(single_item_query)

            set_query_file = getattr(feed_logic, "set_query_file", None)
            if callable(set_query_file) and single_item_query:
                set_query_file(single_item_query)

            set_single_item_mode = getattr(feed_logic, "set_single_item_mode", None)
            if callable(set_single_item_mode):
                set_single_item_mode(True, id=item_id)

        scroll_area: Optional[QScrollArea] = getattr(self, "scroll_area", None)
        if scroll_area is not None and scroll_area.verticalScrollBar() is not None:
            scroll_area.verticalScrollBar().setValue(0)

        if feed_load_engine is not None:
            schedule_load = getattr(feed_load_engine, "schedule_load", None)
            if callable(schedule_load):
                schedule_load()
