import os
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass
from qgis.PyQt.QtWidgets import QAction
from qgis.PyQt.QtGui import QIcon
from .dialog import PluginDialog
import sip  # Add this import at the top
from .login_dialog import LoginDialog  # Import the login dialog class
from .constants.file_paths import ResourcePaths, QssPaths  # Use new resource management classes
from .utils.SessionManager import SessionManager  # Import the SessionManager
from .module_manager import ModuleManager
from .utils.module_discovery import register_all_modules

class WildCodePlugin:
    def __init__(self, iface):
        self.iface = iface
        self.action = None
        self.loginDialog = None
        self.pluginDialog = None
        self.login_successful = False  # Flag to track login success
        self.pluginDialog = None  # Reference to PluginDialog
        self.loginDialog = None  # Reference to LoginDialog
        # Initialize ModuleManager and register all modules (metadata only)
        self.module_manager = ModuleManager()
        register_all_modules(self.module_manager)

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

        print(f"[DEBUG] Session loaded - isLoggedIn: {session.isLoggedIn()}, apiToken: {session.get_token() is not None}")

        if not session.revalidateSession():
            print("[DEBUG] Session validation failed - showing login dialog")
            self._show_login_dialog()
            # Check if login was successful after dialog closes
            if self.login_successful:
                print("[DEBUG] Login was successful - showing main dialog")
                self._show_main_dialog()
                self.login_successful = False  # Reset flag
            return

        if session.isLoggedIn():
            print("[DEBUG] User is logged in - opening main dialog")
            self._show_main_dialog()
        else:
            print("[DEBUG] User not logged in - showing login dialog")
            self._show_login_dialog()
            # Check if login was successful after dialog closes
            if self.login_successful:
                print("[DEBUG] Login was successful - showing main dialog")
                self._show_main_dialog()
                self.login_successful = False  # Reset flag

    def _show_login_dialog(self):
        """Unified method to show login dialog with consistent setup."""
        print("[DEBUG] Showing login dialog")
        self.loginDialog = LoginDialog()
        self.loginDialog.loginSuccessful.connect(self.handle_login_success)
        self.loginDialog.finished.connect(self.reset_login_dialog)
        self.loginDialog.exec_()
        print("[DEBUG] Login dialog closed")

    def _show_main_dialog(self):
        """Unified method to show main dialog."""
        print("[DEBUG] Showing main dialog")
        dlg = PluginDialog._instance
        if dlg is None or not dlg.isVisible():
            self.pluginDialog = PluginDialog()
            self.pluginDialog.finished.connect(self.reset_plugin_dialog)
            self.pluginDialog.show()
        else:
            dlg.raise_()
            dlg.activateWindow()

    def reset_login_dialog(self):
        self.loginDialog = None

    def reset_plugin_dialog(self):
        self.pluginDialog = None

    def handle_login_success(self, api_token, user):
        try:
            print("[DEBUG] handle_login_success called")
            print(f"[DEBUG] Received token: {api_token is not None}, user: {user}")
            print(f"[DEBUG] Token value: {api_token[:10] if api_token else 'None'}...")
            
            # Just set the flag - the run method will handle showing the dialog
            self.login_successful = True
            print("[DEBUG] Login success flag set to True")
                
        except Exception as e:
            print(f"[WildCodePlugin] Error in handle_login_success: {e}")
            import traceback
            print(f"[WildCodePlugin] Full traceback: {traceback.format_exc()}")

    def _create_plugin_dialog(self, api_token, user):
        # This method is no longer needed with the simplified approach
        pass
