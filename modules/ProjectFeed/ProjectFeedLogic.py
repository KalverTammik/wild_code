class ProjectFeedLogic:
    def __init__(self):
        self.feed_items = []

    def set_feed(self, items):
        self.feed_items = items

    def get_feed(self):
        return self.feed_items
