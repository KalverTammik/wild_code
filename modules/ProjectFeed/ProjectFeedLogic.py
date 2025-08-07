
import requests
import threading

class ProjectFeedLogic:
    def __init__(self):
        self.feed_items = []

    def set_feed(self, items):
        self.feed_items = items

    def get_feed(self):
        return self.feed_items

    def add_feed_item(self, item):
        self.feed_items.append(item)

    def remove_feed_item(self, index):
        if 0 <= index < len(self.feed_items):
            del self.feed_items[index]

    def clear_feed(self):
        self.feed_items = []

    def fetch_projects(self, offset=0, limit=10, callback=None):
        """
        Fetch a batch of projects from DummyJSON API asynchronously.
        Calls callback(projects, has_more) on completion.
        """
        def _fetch():
            url = f"https://dummyjson.com/products?limit={limit}&skip={offset}"
            try:
                resp = requests.get(url, timeout=10)
                resp.raise_for_status()
                data = resp.json()
                projects = data.get("products", [])
                has_more = (offset + limit) < data.get("total", 0)
                if callback:
                    callback(projects, has_more)
            except Exception as e:
                if callback:
                    callback([], False)
        thread = threading.Thread(target=_fetch)
        thread.start()
