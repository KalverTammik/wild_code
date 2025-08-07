from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QScrollArea, QFrame, QSpacerItem, QSizePolicy
from PyQt5.QtCore import Qt, pyqtSignal
from ...languages.language_manager import LanguageManager
from ...widgets.theme_manager import ThemeManager
from .ProjectFeedLogic import ProjectFeedLogic
from .ProjectCard import ProjectCard
from ...utils.pagination import PaginatedDataLoader

class ProjectFeedUI(QWidget):
    dataFetched = pyqtSignal(list, bool)
    def __init__(self, lang_manager: LanguageManager, theme_manager: ThemeManager, theme_dir=None, qss_files=None):
        super().__init__()
        from ...module_manager import PROJECT_FEED_MODULE
        self.name = PROJECT_FEED_MODULE
        self.lang_manager = lang_manager
        self.theme_manager = theme_manager
        from ...constants.file_paths import StylePaths
        self.theme_dir = theme_dir or StylePaths.DARK
        from ...constants.file_paths import QssPaths
        self.qss_files = qss_files or [QssPaths.MAIN, QssPaths.SIDEBAR]
        self.logic = ProjectFeedLogic()
        self.loader = PaginatedDataLoader(self.logic.fetch_projects, batch_size=10)
        self.setup_ui()
        if self.theme_dir:
            self.theme_manager.apply_theme(self, self.theme_dir, qss_files=self.qss_files)
        else:
            raise ValueError("theme_dir must be provided to ProjectFeedUI for theme application.")

        self.dataFetched.connect(self._on_data_fetched)
        self.loader.set_on_data_loaded(self._on_loader_data_loaded)

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(self.lang_manager.translate("project_feed_title")))
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_layout.setAlignment(Qt.AlignTop)
        self.scroll_content.setLayout(self.scroll_layout)
        self.scroll_area.setWidget(self.scroll_content)
        layout.addWidget(self.scroll_area)
        self.setLayout(layout)
        self.scroll_area.verticalScrollBar().valueChanged.connect(self.on_scroll)
        self.update_ui()

    def update_ui(self):
        # Remove all widgets from layout
        while self.scroll_layout.count():
            item = self.scroll_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        feed = self.loader.get_items()
        # Add cards
        for item in feed:
            try:
                card = ProjectCard(
                    title=item.get("title", item.get("project", "Untitled")),
                    description=item.get("description", item.get("activity", "No description")),
                    price=item.get("price", "-"),
                    brand=item.get("brand", item.get("user", "-")),
                    image_url=item.get("images", [None])[0] if "images" in item else None
                )
                self.scroll_layout.addWidget(card)
            except Exception:
                pass
        self.scroll_layout.addItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))
    def on_scroll(self, value):
        bar = self.scroll_area.verticalScrollBar()
        if not self.loader.is_loading and self.loader.has_more and value > bar.maximum() - 100:
            self.load_next_batch()

    def load_next_batch(self):
        self.loader.load_next_batch()

    def _on_loader_data_loaded(self, new_items, has_more):
        # This is always called in the worker thread, so emit signal for main thread
        self.dataFetched.emit(new_items, has_more)

    def _on_data_fetched(self, projects, has_more):
        # Only update UI, as loader already manages feed_items and state
        self.update_ui()


    def activate(self):
        """Called when the module is activated/shown."""
        self.logic.clear_feed()
        self.loader.reset()
        self.load_next_batch()

    def deactivate(self):
        """Called when the module is deactivated/hidden."""
        # Clear all cards from the layout
        while self.scroll_layout.count():
            item = self.scroll_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

    def reset(self):
        """Reset the feed to empty."""
        self.logic.clear_feed()
        self.update_ui()

    def run(self):
        """Optional: for future extensibility."""
        pass

    def get_widget(self):
        return self
