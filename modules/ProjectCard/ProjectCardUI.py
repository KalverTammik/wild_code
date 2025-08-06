from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel
from ...languages.language_manager import LanguageManager
from ...widgets.theme_manager import ThemeManager
from .ProjectCardLogic import ProjectCardLogic

class ProjectCardUI(QWidget):
    def __init__(self, lang_manager: LanguageManager, theme_manager: ThemeManager, theme_dir=None, qss_files=None):
        super().__init__()
        from ...module_manager import PROJECT_CARD_MODULE
        self.name = PROJECT_CARD_MODULE
        self.lang_manager = lang_manager
        self.theme_manager = theme_manager
        from ...constants.file_paths import StylePaths
        self.theme_dir = theme_dir or StylePaths.DARK
        from ...constants.file_paths import QssPaths
        self.qss_files = qss_files or [QssPaths.MAIN, QssPaths.SIDEBAR]
        self.logic = ProjectCardLogic()
        self.setup_ui()
        if self.theme_dir:
            self.theme_manager.apply_theme(self, self.theme_dir, qss_files=self.qss_files)
        else:
            raise ValueError("theme_dir must be provided to ProjectCardUI for theme application.")

    def setup_ui(self):
        layout = QVBoxLayout(self)
        self.nameLabel = QLabel(self.lang_manager.translate("project_name_placeholder"))
        self.descriptionLabel = QLabel(self.lang_manager.translate("project_description_placeholder"))
        self.statusLabel = QLabel(self.lang_manager.translate("project_status_placeholder"))
        layout.addWidget(self.nameLabel)
        layout.addWidget(self.descriptionLabel)
        layout.addWidget(self.statusLabel)
        self.setLayout(layout)
        self.update_ui()

    def update_ui(self):
        summary = self.logic.get_project_summary()
        if summary:
            self.nameLabel.setText(summary["name"])
            self.descriptionLabel.setText(summary["description"])
            self.statusLabel.setText(summary["status"])
        else:
            self.nameLabel.setText(self.lang_manager.translate("project_name_placeholder"))
            self.descriptionLabel.setText(self.lang_manager.translate("project_description_placeholder"))
            self.statusLabel.setText(self.lang_manager.translate("project_status_placeholder"))

    def activate(self):
        pass
    def deactivate(self):
        pass
    def reset(self):
        self.logic.set_project(None)
        self.update_ui()
    def run(self):
        pass
    def get_widget(self):
        return self
