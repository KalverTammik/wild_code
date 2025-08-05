import os
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass
from qgis.PyQt.QtWidgets import QAction
from qgis.PyQt.QtGui import QIcon  # Import QIcon to set an icon for the toolbar action
from .dialog import PluginDialog
import sip  # Add this import at the top
from .login_dialog import LoginDialog  # Import the login dialog class
from .constants.file_paths import ResourcePaths, QssPaths  # Use new resource management classes
from .utils.SessionManager import SessionManager  # Import the SessionManager

class WildCodePlugin:
    def __init__(self, iface):
        self.iface = iface
        self.action = None
        self.pluginDialog = None  # Reference to PluginDialog
        self.loginDialog = None  # Reference to LoginDialog

    def initGui(self):
        icon_path = ResourcePaths.ICON
        self.action = QAction(QIcon(icon_path), "Wild Code", self.iface.mainWindow())  # Set the icon for the action
        self.action.triggered.connect(self.run)
        self.iface.addToolBarIcon(self.action)

    def unload(self):
        self.iface.removeToolBarIcon(self.action)
        self.action = None

    def run(self):
        session = SessionManager()
        session.load()

        if not session.revalidateSession():
            self.loginDialog = LoginDialog()
            self.loginDialog.accepted.connect(self.handle_login_success)
            self.loginDialog.finished.connect(self.reset_login_dialog)
            self.loginDialog.exec_()
            return

        if session.isLoggedIn():
            dlg = PluginDialog._instance
            if dlg is None or not dlg.isVisible():
                self.pluginDialog = PluginDialog()
                self.pluginDialog.finished.connect(self.reset_plugin_dialog)
                self.pluginDialog.show()
            else:
                dlg.raise_()
                dlg.activateWindow()
        else:
            theme_path = QssPaths.LIGHT_THEME
            self.loginDialog = LoginDialog(theme_path=theme_path)
            self.loginDialog.accepted.connect(self.handle_login_success)
            self.loginDialog.finished.connect(self.reset_login_dialog)
            self.loginDialog.exec_()

    def reset_login_dialog(self):
        self.loginDialog = None

    def reset_plugin_dialog(self):
        self.pluginDialog = None

    def handle_login_success(self):
        session = SessionManager()
        session.setSession(self.loginDialog.api_token, self.loginDialog.user)
        dlg = PluginDialog._instance
        if dlg is None or not dlg.isVisible():
            self.pluginDialog = PluginDialog()
            self.pluginDialog.finished.connect(self.reset_plugin_dialog)
            self.pluginDialog.show()
        else:
            dlg.raise_()
            dlg.activateWindow()
