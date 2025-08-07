import threading

class PaginatedDataLoader:
    def __init__(self, fetch_func, batch_size=10):
        """
        fetch_func: function(offset, limit, callback) that fetches data and calls callback(items, has_more)
        batch_size: number of items to fetch per batch
        """
        self.fetch_func = fetch_func
        self.batch_size = batch_size
        self.offset = 0
        self.has_more = True
        self.is_loading = False
        self.items = []
        self._on_data_loaded = None

    def set_on_data_loaded(self, callback):
        """Set a callback to be called with (items, has_more) after each batch is loaded."""
        self._on_data_loaded = callback

    def reset(self):
        self.offset = 0
        self.has_more = True
        self.is_loading = False
        self.items = []

    def load_next_batch(self):
        if self.is_loading or not self.has_more:
            return
        self.is_loading = True
        def on_fetched(new_items, has_more):
            self.items.extend(new_items)
            self.offset += len(new_items)
            self.has_more = has_more
            self.is_loading = False
            if self._on_data_loaded:
                self._on_data_loaded(new_items, has_more)
        self.fetch_func(self.offset, self.batch_size, on_fetched)

    def get_items(self):
        return self.items
