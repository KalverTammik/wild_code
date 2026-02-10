import gc
import os
import tempfile
import faulthandler
from qgis.PyQt.QtCore import QTimer
from qgis.PyQt.QtWidgets import QAction
from qgis.PyQt.QtGui import QIcon
from qgis.core import QgsProject

from .dialog import PluginDialog
import sip  # Add this import at the top
from .login_dialog import LoginDialog  # Import the login dialog class
from .constants.module_icons import IconNames
from .utils.SessionManager import SessionManager  # Import the SessionManager
from .languages.language_manager import LanguageManager
from .languages.translation_keys import TranslationKeys
from .widgets.theme_manager import ThemeManager
from .utils.messagesHelper import ModernMessageDialog
from .Logs.switch_logger import SwitchLogger
from .Logs.python_fail_logger import PythonFailLogger
from .utils.MapTools.MapHelpers import MapHelpers
from .constants.layer_constants import IMPORT_PROPERTY_TAG
from .ui.window_state.DialogCoordinator import get_dialog_coordinator



CRASH_LOG_PATH = os.path.join(tempfile.gettempdir(), "kavitro_crash.log")
try:
    _CRASH_LOG_HANDLE = open(CRASH_LOG_PATH, "w", encoding="utf-8")
    faulthandler.enable(_CRASH_LOG_HANDLE, all_threads=True)
except Exception:
    _CRASH_LOG_HANDLE = None

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


    def initGui(self):
        # Force final garbage collection
        gc.collect()
        icon_path = IconNames.VALISEE_V_ICON_NAME

        self.action = QAction(ThemeManager.get_qicon(icon_path), LanguageManager.translate_static(TranslationKeys.KAVITRO_PLUGIN_TITLE), self.iface.mainWindow())  # Set the icon for the action
        self.action.triggered.connect(self.run)
        self.iface.addToolBarIcon(self.action)

    def unload(self):
        self.iface.removeToolBarIcon(self.action)
        self.action = None
        try:
            dlg = self.pluginDialog or PluginDialog.get_instance()
            if dlg is not None:
                try:
                    setattr(dlg, "_force_close", True)
                except Exception:
                    pass
                try:
                    dlg.close()
                except Exception:
                    pass
                try:
                    dlg.deleteLater()
                except Exception:
                    pass
        finally:
            self.pluginDialog = None
        gc.collect()

    def run(self):
        # import universalStatusbar for message display
        try:
            import sip
        except ImportError:
            sip = None

        project = QgsProject.instance()
        if project.fileName() == '':
            heading = LanguageManager.translate_static(TranslationKeys.NO_PROJECT_LOADED_TITLE)
            text = LanguageManager.translate_static(TranslationKeys.NO_PROJECT_LOADED_MESSAGE)
            ModernMessageDialog.Warning_messages_modern(heading, text)
            return

        SwitchLogger.start_session()
        PythonFailLogger.start_session()
        SwitchLogger.log("plugin_run")
        MapHelpers.cleanup_empty_import_layers(IMPORT_PROPERTY_TAG)
        session = SessionManager()
        session.load()
        if not SessionManager.is_session_valid():
            self.pluginDialog = None
            if not hasattr(self, "_pending_login_listener"):
                def _on_session_valid():
                    if SessionManager.is_session_valid():
                        SessionManager.unregister_listener(_on_session_valid)
                        if hasattr(self, "_pending_login_listener"):
                            delattr(self, "_pending_login_listener")
                        self._show_main_dialog()
                        def _raise_dialog():
                            dlg = self.pluginDialog or PluginDialog.get_instance()
                            if dlg:
                                coordinator = get_dialog_coordinator(self.iface)
                                coordinator.bring_to_front(dlg, retries=1, delay_ms=200)
                        QTimer.singleShot(0, _raise_dialog)

                self._pending_login_listener = _on_session_valid
                SessionManager.register_listener(_on_session_valid)
            SessionManager.request_login(parent=self.iface.mainWindow(), reason="startup")
            return

        # Session looks valid; reuse dialog if alive, else create
        if self.pluginDialog is not None:
            try:
                if sip is None or not sip.isdeleted(self.pluginDialog):
                    coordinator = get_dialog_coordinator(self.iface)
                    coordinator.bring_to_front(self.pluginDialog, retries=1, delay_ms=200)
                    return
            except Exception as exc:
                PythonFailLogger.log_exception(
                    exc,
                    module="ui",
                    event="plugin_dialog_show_failed",
                )

        self._show_main_dialog()

    def _show_login_dialog(self):
        """Unified method to show login dialog with consistent setup."""
        self.loginDialog = LoginDialog()
        self.loginDialog.loginSuccessful.connect(self.handle_login_success)
        self.loginDialog.finished.connect(self.reset_login_dialog)
        self.loginDialog.exec_()

    def _show_main_dialog(self):
        """Unified method to show main dialog."""
        dlg = PluginDialog.get_instance()
        if dlg is None and self.pluginDialog is not None:
            try:
                import sip
                if sip and not sip.isdeleted(self.pluginDialog):
                    dlg = self.pluginDialog
            except Exception as exc:
                PythonFailLogger.log_exception(
                    exc,
                    module="ui",
                    event="plugin_dialog_reuse_check_failed",
                )
                dlg = None

        if dlg is None:
            dlg = PluginDialog()
            self.pluginDialog = dlg
            dlg.finished.connect(self.reset_plugin_dialog)
            dlg.show()
            coordinator = get_dialog_coordinator(self.iface)
            coordinator.bring_to_front(dlg, retries=1, delay_ms=200)
        else:
            self.pluginDialog = dlg
            coordinator = get_dialog_coordinator(self.iface)
            coordinator.bring_to_front(dlg, retries=1, delay_ms=200)

    def reset_login_dialog(self):
        self.loginDialog = None

    def reset_plugin_dialog(self):
        self.pluginDialog = None

    def handle_login_success(self, api_token, user):
        try:
            # Just set the flag - the run method will handle showing the dialog
            self.login_successful = True

        except Exception as e:
            print(f"[WildCodePlugin] Error in handle_login_success: {e}")
            import traceback
            print(f"[WildCodePlugin] Full traceback: {traceback.format_exc()}")

    def _create_plugin_dialog(self, api_token, user):
        # This method is no longer needed with the simplified approach
        pass
