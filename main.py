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
from .constants.file_paths import ConfigPaths



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
        icon_path = IconNames.KAVITRO_ICON
        
        plugin_title = ConfigPaths.PLUGIN_NAME or LanguageManager.translate_static(TranslationKeys.KAVITRO_PLUGIN_TITLE)

        self.action = QAction(ThemeManager.get_qicon(icon_path), plugin_title, self.iface.mainWindow())  # Set the icon for the action
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
            old_listener = getattr(self, "_pending_login_listener", None)
            if old_listener is not None:
                SessionManager.unregister_listener(old_listener)

            def _on_session_valid():
                if not SessionManager.is_session_valid():
                    SwitchLogger.log("startup_login_listener_ignored_invalid_session")
                    return
                SwitchLogger.log("startup_login_listener_session_valid")
                SessionManager.unregister_listener(_on_session_valid)
                if getattr(self, "_pending_login_listener", None) is _on_session_valid:
                    delattr(self, "_pending_login_listener")

                def _show_after_login():
                    if not SessionManager.is_session_valid():
                        SwitchLogger.log("startup_login_show_aborted_invalid_session")
                        return
                    SwitchLogger.log("startup_login_show_main_dialog")
                    self._show_main_dialog()
                    dlg = self.pluginDialog or PluginDialog.get_instance()
                    if dlg:
                        coordinator = get_dialog_coordinator(self.iface)
                        coordinator.bring_to_front(dlg, retries=2, delay_ms=200)
                        SwitchLogger.log("startup_login_dialog_raise_requested")
                    else:
                        SwitchLogger.log("startup_login_dialog_missing_after_show")

                QTimer.singleShot(0, _show_after_login)

            self._pending_login_listener = _on_session_valid
            SessionManager.register_listener(_on_session_valid)
            SessionManager.request_login(parent=self.iface.mainWindow(), reason="startup")
            return

        # Session looks valid; reuse dialog if alive, else create
        if self.pluginDialog is not None:
            if self._is_dialog_usable(self.pluginDialog):
                self._show_existing_dialog(self.pluginDialog)
                return
            SwitchLogger.log("plugin_dialog_cached_reference_discarded")
            self.pluginDialog = None

        self._show_main_dialog()

    @staticmethod
    def _is_dialog_deleted(dialog):
        if dialog is None:
            return True
        try:
            return bool(sip.isdeleted(dialog))
        except Exception:
            return False

    def _is_dialog_usable(self, dialog):
        if dialog is None:
            return False
        if self._is_dialog_deleted(dialog):
            return False
        if getattr(dialog, "_force_close", False):
            return False
        return True

    def _show_existing_dialog(self, dialog):
        try:
            if dialog.isMinimized():
                dialog.showNormal()
            else:
                dialog.show()
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module="ui",
                event="plugin_dialog_show_failed",
            )
            return

        coordinator = get_dialog_coordinator(self.iface)
        coordinator.bring_to_front(dialog, retries=1, delay_ms=200)
        SwitchLogger.log(
            "plugin_dialog_show_requested",
            extra={
                "visible": str(dialog.isVisible()),
                "minimized": str(dialog.isMinimized()),
            },
        )

    def _show_login_dialog(self):
        """Unified method to show login dialog with consistent setup."""
        self.loginDialog = LoginDialog()
        self.loginDialog.loginSuccessful.connect(self.handle_login_success)
        self.loginDialog.finished.connect(self.reset_login_dialog)
        self.loginDialog.exec_()

    def _show_main_dialog(self):
        """Unified method to show main dialog."""
        dlg = PluginDialog.get_instance()
        if not self._is_dialog_usable(dlg):
            if dlg is not None:
                SwitchLogger.log("plugin_dialog_singleton_discarded")
                try:
                    if PluginDialog._instance is dlg:
                        PluginDialog._instance = None
                except Exception:
                    pass
            dlg = None

        if dlg is None and self.pluginDialog is not None:
            if self._is_dialog_usable(self.pluginDialog):
                dlg = self.pluginDialog
            else:
                SwitchLogger.log("plugin_dialog_cached_reference_discarded")
                self.pluginDialog = None

        if dlg is None:
            dlg = PluginDialog()
            self.pluginDialog = dlg
            dlg.finished.connect(self.reset_plugin_dialog)
            SwitchLogger.log("plugin_dialog_created")
            self._show_existing_dialog(dlg)
        else:
            self.pluginDialog = dlg
            self._show_existing_dialog(dlg)

    def reset_login_dialog(self):
        self.loginDialog = None

    def reset_plugin_dialog(self):
        self.pluginDialog = None

    def handle_login_success(self, api_token, user):
        self.login_successful = True

    def _create_plugin_dialog(self, api_token, user):
        # This method is no longer needed with the simplified approach
        pass
