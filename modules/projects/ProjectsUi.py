# --- Modular ProjectsModule implementation ---
from ...BaseModule import BaseModule
from ...languages.language_manager import LanguageManager


# PyQt5
from PyQt5.QtWidgets import QVBoxLayout, QScrollArea, QWidget
from PyQt5.QtCore import Qt
from ...widgets.ModuleFeedBuilder import ModuleFeedBuilder
from ...constants.file_paths import StylePaths, QssPaths




# Import the new feed logic
from .ProjectsLogic import ProjectsFeedLogic

class ProjectsModule(BaseModule):
    def on_theme_toggled(self):
        """
        Called by the main dialog after a theme toggle. Re-applies the theme to the main widget and all cards.
        Follows copilot-prompt.md: always use ThemeManager, never hardcode QSS paths.
        """
        if self.theme_manager and self.theme_dir:
            self.theme_manager.apply_theme(self.widget, self.theme_dir, [])
        # Re-apply theme to all module cards in the feed
        for i in range(self.feed_layout.count()):
            card = self.feed_layout.itemAt(i).widget()
            if card and self.theme_manager and self.theme_dir:
                self.theme_manager.apply_theme(card, self.theme_dir, [QssPaths.MODULE_CARD])
    def on_scroll(self, value):
        bar = self.scroll_area.verticalScrollBar()
        if value == bar.maximum() and self.feed_logic.has_more and not self.feed_logic.is_loading:
            self.load_next_batch()
    def __init__(self, name="ProjectsModule", display_name=None, icon=None, lang_manager=None, theme_manager=None, theme_dir=None, qss_files=None):
        super().__init__(name, display_name or "Projects", icon, lang_manager or LanguageManager(), theme_manager)
        self.theme_dir = theme_dir
        self.feed_logic = ProjectsFeedLogic("PROJECT", "ListAllProjects.graphql", self.lang_manager)

        # Main widget and layout
        self.widget = QWidget()
        self.widget.setLayout(QVBoxLayout())
        self.feed_content = QWidget()
        self.feed_layout = QVBoxLayout()
        self.feed_content.setLayout(self.feed_layout)
        self.widget.layout().addWidget(self.feed_content)

        # Add scroll area for feed
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setWidget(self.feed_content)
        self.widget.layout().addWidget(self.scroll_area)

        # Theming
        if self.theme_manager and self.theme_dir:
            self.theme_manager.apply_theme(self.widget, self.theme_dir, [])

        # Connect scroll event for infinite scroll
        self.scroll_area.verticalScrollBar().valueChanged.connect(self.on_scroll)
        self._activated = False

    def activate(self):
        if not self._activated:
            self._activated = True
            self.load_next_batch()

    def deactivate(self):        
        self._activated = False
        pass

    def run(self):
        pass

    def reset(self):
        pass

    def get_widget(self):
        return self.widget

    def load_next_batch(self):
        items = self.feed_logic.fetch_next_batch()
        ModuleFeedBuilder.add_items_to_feed(self, items)
