class SearchOpenItemMixin:
    """Shared helper to open a single item from unified search.

    Host classes are ModuleBaseUI subclasses that define FEED_LOGIC_CLS, QUERY_FILE,
    SINGLE_ITEM_QUERY_FILE and module_key.
    """

    def open_item_from_search(self, search_module: str, item_id: str, title: str) -> None:
        feed_load_engine = self.feed_load_engine
        if feed_load_engine is not None:
            feed_load_engine.buffer.clear()

        if self.feed_layout is not None:
            self.clear_feed(self.feed_layout, self._empty_state)

        feed_logic = self.feed_logic
        if feed_logic is None:
            feed_logic = self.FEED_LOGIC_CLS(self.module_key, self.QUERY_FILE, self.lang_manager)
            self.feed_logic = feed_logic

        feed_logic.configure_single_item_query(self.SINGLE_ITEM_QUERY_FILE)
        feed_logic.set_single_item_mode(True, id=item_id)

        scroll_area = self.scroll_area
        if scroll_area is not None and scroll_area.verticalScrollBar() is not None:
            scroll_area.verticalScrollBar().setValue(0)

        if feed_load_engine is not None:
            feed_load_engine.schedule_load()
