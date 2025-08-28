import os
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass
from PyQt5.QtCore import Qt
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
            self.loginDialog = LoginDialog()
            print(f"[DEBUG] LoginDialog created: {self.loginDialog}")
            print("[DEBUG] Connecting signals...")
            self.loginDialog.loginSuccessful.connect(self.handle_login_success, Qt.QueuedConnection)
            print("[DEBUG] loginSuccessful signal connected with QueuedConnection")
            self.loginDialog.finished.connect(self.reset_login_dialog)
            print("[DEBUG] finished signal connected")
            print("[DEBUG] About to call exec_()")
            result = self.loginDialog.exec_()
            print(f"[DEBUG] exec_() returned: {result}")
            print(f"[DEBUG] LoginDialog result: {self.loginDialog.result()}")
            return

        if session.isLoggedIn():
            print("[DEBUG] User is logged in - opening main dialog")
            dlg = PluginDialog._instance
            if dlg is None or not dlg.isVisible():
                self.pluginDialog = PluginDialog()  # Try without parent first
                self.pluginDialog.finished.connect(self.reset_plugin_dialog)
                self.pluginDialog.show()
            else:
                dlg.raise_()
                dlg.activateWindow()
        else:
            print("[DEBUG] User not logged in - showing login dialog")
            theme_path = QssPaths.LIGHT_THEME
            self.loginDialog = LoginDialog(theme_path=theme_path)
            self.loginDialog.loginSuccessful.connect(self.handle_login_success, Qt.QueuedConnection)
            self.loginDialog.finished.connect(self.reset_login_dialog)
            self.loginDialog.exec_()

    def reset_login_dialog(self):
        self.loginDialog = None

    def reset_plugin_dialog(self):
        self.pluginDialog = None

    def handle_login_success(self, api_token, user):
        try:
            print("[DEBUG] handle_login_success called")
            print(f"[DEBUG] Received token: {api_token is not None}, user: {user}")
            print(f"[DEBUG] Token value: {api_token[:10] if api_token else 'None'}...")

            # Defer PluginDialog creation until after login dialog is closed
            from PyQt5.QtCore import QTimer
            QTimer.singleShot(100, lambda: self._create_plugin_dialog(api_token, user))
                
        except Exception as e:
            print(f"[WildCodePlugin] Error in handle_login_success: {e}")
            import traceback
            print(f"[WildCodePlugin] Full traceback: {traceback.format_exc()}")

    def _create_plugin_dialog(self, api_token, user):
        try:
            print("[DEBUG] _create_plugin_dialog called")
            print("[DEBUG] Checking PluginDialog instance...")
            dlg = PluginDialog._instance
            print(f"[DEBUG] PluginDialog._instance: {dlg}")
            
            if dlg is None or not dlg.isVisible():
                print("[DEBUG] Creating new PluginDialog")
                self.pluginDialog = PluginDialog()  # Try without parent first
                print(f"[DEBUG] PluginDialog created: {self.pluginDialog}")
                self.pluginDialog.finished.connect(self.reset_plugin_dialog)
                print("[DEBUG] About to call show()")
                self.pluginDialog.show()
                print("[DEBUG] show() called successfully")
            else:
                print("[DEBUG] Raising existing PluginDialog")
                dlg.raise_()
                dlg.activateWindow()
                
        except Exception as e:
            print(f"[WildCodePlugin] Error creating plugin dialog: {e}")
            import traceback
            print(f"[WildCodePlugin] Full traceback: {traceback.format_exc()}")
            # Fallback: try to show a basic error message
            from qgis.PyQt.QtWidgets import QMessageBox
            QMessageBox.warning(None, "Login Success", f"Login successful but failed to open main interface: {str(e)}")
