from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QFormLayout, QMessageBox
from ...languages.language_manager import LanguageManager
from ...widgets.theme_manager import ThemeManager
from .SettingsLogic import SettingsLogic

class SettingsUI(QWidget):
    """
    This module supports dynamic theme switching via ThemeManager.apply_module_style.
    Call retheme_settings() to re-apply QSS after a theme change.
    """
    def __init__(self, lang_manager=None, theme_manager=None, theme_dir=None, qss_files=None):
        super().__init__()
        from ...module_manager import SETTINGS_MODULE
        self.name = SETTINGS_MODULE
        # Ensure we always use LanguageManager_NEW
        if lang_manager is None:
            self.lang_manager = LanguageManager()
        elif not hasattr(lang_manager, 'sidebar_button'):
            language = getattr(lang_manager, 'language', None)
            if language:
                self.lang_manager = LanguageManager(language=language)
            else:
                self.lang_manager = LanguageManager()
        else:
            self.lang_manager = lang_manager
        from ...widgets.theme_manager import ThemeManager
        from ...constants.file_paths import QssPaths
        self.theme_manager = theme_manager
        self.logic = SettingsLogic()
        self.setup_ui()
        # Centralized theming: always use main theme for this module
        ThemeManager.apply_module_style(self, [QssPaths.MAIN])

    def setup_ui(self):
        layout = QVBoxLayout(self)
        self.formLayout = QFormLayout()
        self.keyEdit = QLineEdit()
        self.valueEdit = QLineEdit()
        self.saveButton = QPushButton(self.lang_manager.translate("save_setting"))
        self.saveButton.clicked.connect(self.on_save)
        self.formLayout.addRow(self.lang_manager.translate("setting_key"), self.keyEdit)
        self.formLayout.addRow(self.lang_manager.translate("setting_value"), self.valueEdit)
        layout.addLayout(self.formLayout)
        layout.addWidget(self.saveButton)
        self.setLayout(layout)

    def on_save(self):
        key = self.keyEdit.text()
        value = self.valueEdit.text()
        if key:
            self.logic.set_setting(key, value)
            QMessageBox.information(self, self.lang_manager.translate("setting_saved_title"), self.lang_manager.translate("setting_saved_message").format(key=key, value=value))
            self.keyEdit.clear()
            self.valueEdit.clear()
        else:
            QMessageBox.warning(self, self.lang_manager.translate("setting_error_title"), self.lang_manager.translate("setting_error_message"))

    def activate(self):
        pass
    def deactivate(self):
        pass
    def reset(self):
        self.logic.settings.clear()
        self.keyEdit.clear()
        self.valueEdit.clear()
    def run(self):
        pass
    def get_widget(self):
        return self

    def retheme_settings(self):
        """
        Re-applies the correct theme and QSS to the settings UI, forcing a style refresh.
        """
        from ...widgets.theme_manager import ThemeManager
        from ...constants.file_paths import QssPaths
        ThemeManager.apply_module_style(self, [QssPaths.MAIN])
