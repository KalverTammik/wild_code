
from ...ui.ModuleBaseUI import ModuleBaseUI
from PyQt5.QtWidgets import QLabel
from ...languages.language_manager import LanguageManager_NEW


class ProjectsModule(ModuleBaseUI):
    name = "ProjectsModule"

    def get_widget(self):
        """Return the widget instance for use in module manager or UI stack."""
        return self

    def __init__(self, lang_manager=None, theme_manager=None, theme_dir=None, qss_files=None, parent=None):
        super().__init__(parent)
        # Use LanguageManager_NEW if not provided
        if lang_manager is None:
            self.lang_manager = LanguageManager_NEW()
        else:
            self.lang_manager = lang_manager
        self.theme_manager = theme_manager
        self.theme_dir = theme_dir
        self.qss_files = qss_files or []
        # Example: apply theme if theme_manager is provided
        if self.theme_manager and self.theme_dir and self.qss_files:
            self.theme_manager.apply_theme(self, self.theme_dir, self.qss_files)
        # Use lang_manager for translated label if available (now always LanguageManager_NEW)
        label_text = self.lang_manager.translate("projects_module_loaded")
        self.display_area.layout().addWidget(QLabel(label_text))

    def activate(self):
        """Activate the module."""
        pass

    def deactivate(self):
        """Deactivate the module."""
        pass

