from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QFormLayout, QMessageBox
from ...languages.language_manager import LanguageManager
from ...widgets.theme_manager import ThemeManager
from .SettingsLogic import SettingsLogic

class SettingsUI(QWidget):
    def __init__(self, lang_manager: LanguageManager, theme_manager: ThemeManager, theme_dir=None, qss_files=None):
        super().__init__()
        from ...module_manager import SETTINGS_MODULE
        self.name = SETTINGS_MODULE
        self.lang_manager = lang_manager
        self.theme_manager = theme_manager
        from ...constants.file_paths import StylePaths
        self.theme_dir = theme_dir or StylePaths.DARK
        from ...constants.file_paths import QssPaths
        self.qss_files = qss_files or [QssPaths.MAIN, QssPaths.SIDEBAR]
        self.logic = SettingsLogic()
        self.setup_ui()
        if self.theme_dir:
            self.theme_manager.apply_theme(self, self.theme_dir, qss_files=self.qss_files)
        else:
            raise ValueError("theme_dir must be provided to SettingsUI for theme application.")

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
