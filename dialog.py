from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QStackedWidget
from PyQt5.QtGui import QMouseEvent
from qgis.PyQt.QtWidgets import QDialog as QgisQDialog  # If needed elsewhere, otherwise can be removed
from qgis.core import QgsMessageLog, Qgis

from .login_dialog import LoginDialog
from .widgets.theme_manager import ThemeManager
from .languages.language_manager import LanguageManager
from .module_manager import ModuleManager
from .widgets.sidebar import Sidebar
from .utils.SessionManager import SessionManager

lang = LanguageManager()

class PluginDialog(QDialog):
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(PluginDialog, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle(lang.translate("wild_code_plugin_title"))  # Set window title

        self.moduleManager = ModuleManager()
        self.moduleStack = QStackedWidget()
        self.sidebar = Sidebar()
        self.sidebar.itemClicked.connect(self.switchModule)

        main_layout = QHBoxLayout()
        main_layout.addWidget(self.sidebar)

        center_layout = QVBoxLayout()
        self.header = QLabel(lang.translate("wild_code_plugin_title"))
        center_layout.addWidget(self.header)

        self.switch_button = QPushButton(lang.translate("switch_to_dark_mode"))
        self.switch_button.clicked.connect(self.toggle_theme)
        center_layout.addWidget(self.switch_button)

        center_layout.addWidget(self.moduleStack)
        self.footer = QLabel(lang.translate("footer_text"))
        center_layout.addWidget(self.footer)
        main_layout.addLayout(center_layout)
        self.setLayout(main_layout)

        self.current_theme = "light"
        self.apply_theme()
        self.loadModules()

        self.logout_button = QPushButton("Logout")
        self.logout_button.clicked.connect(self.logout)
        self.layout().addWidget(self.logout_button)

        self.destroyed.connect(self._on_destroyed)

    def _on_destroyed(self, obj):
        PluginDialog._instance = None

    def loadModules(self):
        from .modules.example_module import WeatherUpdateModule
        from .modules.joke_generator_module import JokeGeneratorModule
        from .modules.ProjectCardModule import ProjectCardModule
        from .modules.ProjectFeedModule import ProjectFeedModule
        from .modules.ImageOfTheDayModule import ImageOfTheDayModule
        from .modules.BookQuoteModule import BookQuoteModule

        jokeModule = JokeGeneratorModule()
        weatherModule = WeatherUpdateModule()
        projectCardModule = ProjectCardModule()
        projectFeedModule = ProjectFeedModule()
        imageOfTheDayModule = ImageOfTheDayModule()
        bookQuoteModule = BookQuoteModule()

        self.moduleManager.registerModule(jokeModule)
        self.moduleManager.registerModule(weatherModule)
        self.moduleManager.registerModule(projectCardModule)
        self.moduleManager.registerModule(projectFeedModule)
        self.moduleManager.registerModule(imageOfTheDayModule)
        self.moduleManager.registerModule(bookQuoteModule)

        for moduleName, moduleInfo in self.moduleManager.modules.items():
            iconPath = moduleInfo["icon"]
            displayName = moduleInfo["display_name"]
            self.sidebar.addItem(displayName, moduleName, iconPath)
            self.moduleStack.addWidget(moduleInfo["module"].get_widget())

    def switchModule(self, moduleName):
        try:
            self.moduleManager.activateModule(moduleName)
            activeModule = self.moduleManager.getActiveModule()
            if activeModule:
                self.moduleStack.setCurrentWidget(activeModule["module"].get_widget())
            else:
                raise AttributeError("No active module found.")
        except Exception as e:
            QgsMessageLog.logMessage(f"Error switching module: {e}", "Wild Code", level=Qgis.Critical)

    def toggle_theme(self):
        self.current_theme = "dark" if self.current_theme == "light" else "light"
        self.apply_theme()

    def apply_theme(self):
        if self.current_theme == "light":
            ThemeManager.apply_light_theme(self)
            self.switch_button.setText(lang.translate("switch_to_dark_mode"))
        else:
            ThemeManager.apply_dark_theme(self)
            self.switch_button.setText(lang.translate("switch_to_light_mode"))

    def mousePressEvent(self, event: QMouseEvent):
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        super().mouseMoveEvent(event)

    def create_button_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Button Dialog")
        layout = QVBoxLayout(dialog)
        label = QLabel("This is a custom dialog with buttons.", dialog)
        layout.addWidget(label)
        self.okButton = QPushButton("OK", dialog)
        self.cancelButton = QPushButton("Cancel", dialog)
        layout.addWidget(self.okButton)
        layout.addWidget(self.cancelButton)
        ThemeManager.apply_theme(dialog)
        return dialog

    def logout(self):
        SessionManager.clear()
        self.close()

    def showEvent(self, event):
        if not SessionManager().isLoggedIn():
            self.close()
        super().showEvent(event)

    def closeEvent(self, event):
        super().closeEvent(event)

    def handleSessionExpiration(self):
        self.close()
        loginDialog = LoginDialog()
