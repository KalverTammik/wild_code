from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QListWidget, QListWidgetItem
from ...languages.language_manager import LanguageManager
from ...widgets.theme_manager import ThemeManager
from .ProjectFeedLogic import ProjectFeedLogic

class ProjectFeedUI(QWidget):
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
        self.setup_ui()
        if self.theme_dir:
            self.theme_manager.apply_theme(self, self.theme_dir, qss_files=self.qss_files)
        else:
            raise ValueError("theme_dir must be provided to ProjectFeedUI for theme application.")

    def setup_ui(self):
        layout = QVBoxLayout(self)
        self.feedList = QListWidget()
        layout.addWidget(QLabel(self.lang_manager.translate("project_feed_title")))
        layout.addWidget(self.feedList)
        self.setLayout(layout)
        self.update_ui()

    def update_ui(self):
        self.feedList.clear()
        for item in self.logic.get_feed():
            list_item = QListWidgetItem(str(item))
            self.feedList.addItem(list_item)

    def activate(self):
        pass
    def deactivate(self):
        pass
    def reset(self):
        self.logic.set_feed([])
        self.update_ui()
    def run(self):
        pass
    def get_widget(self):
        return self
