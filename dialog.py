
import os
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QStackedWidget, QWidget
from PyQt5.QtGui import QMouseEvent
from .widgets.FooterWidget import FooterWidget
from .widgets.HeaderWidget import HeaderWidget
from qgis.PyQt.QtWidgets import QDialog as QgisQDialog  # If needed elsewhere, otherwise can be removed
from qgis.core import QgsMessageLog, Qgis

from .login_dialog import LoginDialog
from .widgets.theme_manager import ThemeManager
from .languages.language_manager import LanguageManager
from .module_manager import ModuleManager
from .widgets.sidebar import Sidebar
from .utils.SessionManager import SessionManager
from .constants.file_paths import ResourcePaths, QssPaths, ConfigPaths, ModuleIconPaths
from .config.setup import Version

lang = LanguageManager()


class PluginDialog(QDialog):
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(PluginDialog, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle(lang.translate("wild_code_plugin_title"))

        from PyQt5.QtWidgets import QSizePolicy
        self.moduleManager = ModuleManager()
        self.moduleStack = QStackedWidget()
        self.moduleStack.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.sidebar = Sidebar()
        self.sidebar.itemClicked.connect(self.switchModule)



        # Main vertical layout for the dialog
        dialog_layout = QVBoxLayout()
        dialog_layout.setContentsMargins(0, 0, 0, 0)
        dialog_layout.setSpacing(0)

        # Header at the absolute top
        self.header_widget = HeaderWidget(
            title=lang.translate("wild_code_plugin_title"),
            switch_callback=self.toggle_theme,
            logout_callback=self.logout
        )
        dialog_layout.addWidget(self.header_widget)

        # Central content area (sidebar + main content + right sidebar)
        content_layout = QHBoxLayout()
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)
        content_layout.addWidget(self.sidebar)

        center_layout = QVBoxLayout()
        center_layout.addWidget(self.moduleStack)
        content_widget = QWidget()
        content_widget.setLayout(center_layout)
        content_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        content_layout.addWidget(content_widget)


        dialog_layout.addLayout(content_layout)

        # Footer at the absolute bottom
        self.footer_widget = FooterWidget(show_left=True, show_right=True)
        dialog_layout.addWidget(self.footer_widget)

        self.setLayout(dialog_layout)
        

        self.theme_base_dir = os.path.join(os.path.dirname(__file__), 'styles')
        # Load and apply the theme from QGIS settings (persistent)
        self.current_theme = ThemeManager.set_initial_theme(
            self,
            self.header_widget.switchButton,
            self.theme_base_dir,
            qss_files=["main.qss", "sidebar.qss", "header.qss", "footer.qss"]
        )
        self.loadModules()
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
        from .modules.PizzaOrderModule import PizzaOrderModule
        from .modules.Hinnapakkuja.HinnapakkujaModule import HinnapakkujaModule

        jokeModule = JokeGeneratorModule()
        weatherModule = WeatherUpdateModule()
        projectCardModule = ProjectCardModule()
        projectFeedModule = ProjectFeedModule()
        imageOfTheDayModule = ImageOfTheDayModule()
        bookQuoteModule = BookQuoteModule()
        pizzaOrderModule = PizzaOrderModule()
        hinnapakkujaModule = HinnapakkujaModule()

        self.moduleManager.registerModule(jokeModule)
        self.moduleManager.registerModule(weatherModule)
        self.moduleManager.registerModule(projectCardModule)
        self.moduleManager.registerModule(projectFeedModule)
        self.moduleManager.registerModule(imageOfTheDayModule)
        self.moduleManager.registerModule(bookQuoteModule)
        self.moduleManager.registerModule(pizzaOrderModule)
        self.moduleManager.registerModule(hinnapakkujaModule)
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
        # Use ThemeManager to toggle theme and update icon
        qss_files = ["main.qss", "sidebar.qss", "header.qss"]
        new_theme = ThemeManager.toggle_theme(
            self,
            self.current_theme,
            self.header_widget.switchButton,
            self.theme_base_dir,
            qss_files=qss_files
        )
        self.current_theme = new_theme



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
