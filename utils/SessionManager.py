from typing import Optional, Protocol, TYPE_CHECKING

from qgis.PyQt.QtCore import QTimer

if TYPE_CHECKING:
    from typing import Any

    class ModuleWidgetProtocol(Protocol):
        ...

    class ModuleInstanceProtocol(Protocol):
        def get_widget(self) -> Optional[ModuleWidgetProtocol]: ...

    class ModuleManagerProtocol(Protocol):
        modules: dict
        def getActiveModuleName(self) -> Optional[str]: ...
        def getActiveModuleInstance(self, moduleName: str) -> Optional[ModuleInstanceProtocol]: ...

    class ModuleStackProtocol(Protocol):
        def setCurrentWidget(self, widget: ModuleWidgetProtocol) -> None: ...

    class SidebarProtocol(Protocol):
        def setActiveModuleOnSidebarButton(self, moduleName: str) -> None: ...

    class SessionDialogProtocol(Protocol):
        _has_shown: bool
        moduleManager: ModuleManagerProtocol
        moduleStack: ModuleStackProtocol
        sidebar: SidebarProtocol
        def close(self) -> None: ...
from qgis.core import QgsApplication, QgsAuthMethodConfig, QgsSettings
from ..languages.translation_keys import TranslationKeys
from .messagesHelper import ModernMessageDialog
from ..Logs.python_fail_logger import PythonFailLogger


"""Session persistence + UI session flow (single-file layout).

Sections:
- Session constants
- SessionManager (persistence/auth)
- SessionUIController (UI lifecycle helpers)
"""

# ------------------------------------------------------------------
# Session constants
# ------------------------------------------------------------------
SESSION_TOKEN = "session/token"
SESSION_ACTIVE_USER = "session/user"
SESSION_NEEDS_LOGIN = "session/needs_login"


# Authentication
AUTH_ID = "myplugin/auth_id"
AUTH_USERNAME = "myplugin/username"


# ------------------------------------------------------------------
# SessionManager (persistence/auth)
# ------------------------------------------------------------------
class SessionManager:

    _instance = None
    _session_expired_shown = False
    _login_dialog_open = False
    _login_cancelled_for_reason: Optional[str] = None
    _last_login_reason: Optional[str] = None
    _listeners: list = []

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(SessionManager, cls).__new__(cls)
            cls._instance.apiToken = None
            cls._instance.loggedInUser = None
            cls._instance.settings = QgsSettings()
            cls._instance.auth_manager = QgsApplication.authManager()
            cls._instance.username = None
            cls._instance.password = None
            cls._instance.api_key = None
        return cls._instance


    @staticmethod
    def load() -> None:
        """Load session data from QgsSettings."""
        if not SessionManager._instance:
            SessionManager()
        settings = SessionManager._instance.settings
        SessionManager._instance.apiToken = settings.value(SESSION_TOKEN, None)
        SessionManager._instance.loggedInUser = settings.value(SESSION_ACTIVE_USER, None)
        

    @staticmethod
    def save_session() -> None:
        """Save session data to QgsSettings."""
        if not SessionManager._instance:
            SessionManager()
        settings = SessionManager._instance.settings
        if SessionManager._instance.apiToken:
            settings.setValue(SESSION_TOKEN, SessionManager._instance.apiToken)
        else:
            settings.remove(SESSION_TOKEN)
        if SessionManager._instance.loggedInUser:
            settings.setValue(SESSION_ACTIVE_USER, SessionManager._instance.loggedInUser)
        else:
            settings.remove(SESSION_ACTIVE_USER)
        settings.sync()  # Ensure settings are written immediately


    @staticmethod
    def clear() -> None:
        """Clear session data from QgsSettings (logout without auto-login)."""
        if not SessionManager._instance:
            SessionManager()
        settings = SessionManager._instance.settings
        settings.remove(SESSION_TOKEN)
        settings.remove(SESSION_ACTIVE_USER)
        settings.setValue(SESSION_NEEDS_LOGIN, True)
        SessionManager._instance.apiToken = None
        SessionManager._instance.loggedInUser = None
        SessionManager._session_expired_shown = False
        SessionManager._login_cancelled_for_reason = None
        SessionManager.save_session()  # Ensure persistent storage is updated
        SessionManager._notify_session_changed()
        PythonFailLogger.log(
            "logout_session_cleared",
            module="auth",
        )
    # --- Secure Credential Handling (QgsAuthenticationManager) ---
    def save_credentials(self, username: str, password: str, api_key: str) -> None:
        config = QgsAuthMethodConfig("Basic")
        config.setName("myplugin_session")
        config.setConfig("username", username)
        config.setConfig("password", password)
        config.setConfig("apikey", api_key)

        if self.auth_manager.storeAuthenticationConfig(config):
            self.settings.setValue(AUTH_ID, config.id())
            self.settings.setValue(AUTH_USERNAME, username)
            # Credentials securely stored.
        else:
            try:
                from ..Logs.logger import error as log_error
                log_error("Failed to store authentication config.")
            except Exception as exc:
                PythonFailLogger.log_exception(
                    exc,
                    module="auth",
                    event="auth_store_log_failed",
                )

    def load_credentials(self) -> bool:
        auth_id = self.settings.value(AUTH_ID, "")
        self.username = self.settings.value(AUTH_USERNAME, "")

        if not auth_id:
            # No stored auth ID found.
            return False

        config = QgsAuthMethodConfig()
        if self.auth_manager.loadAuthenticationConfig(auth_id, config):
            self.password = config.config("password")
            self.api_key = config.config("apikey")
            return True
        else:
            try:
                from ..Logs.logger import error as log_error
                log_error("Failed to load authentication config.")
            except Exception as exc:
                PythonFailLogger.log_exception(
                    exc,
                    module="auth",
                    event="auth_load_log_failed",
                )
            return False

    def clear_session(self) -> None:
        self.username = None
        self.password = None
        self.api_key = None
        # Session data cleared.

    def clear_credentials(self) -> None:
        """Forget stored credentials and remove auth config (explicit user action)."""
        try:
            auth_id = self.settings.value(AUTH_ID, "")
            if auth_id:
                try:
                    self.auth_manager.removeAuthenticationConfig(auth_id)
                except Exception as exc:
                    PythonFailLogger.log_exception(
                        exc,
                        module="auth",
                        event="auth_remove_config_failed",
                    )
            self.settings.remove(AUTH_ID)
            self.settings.remove(AUTH_USERNAME)
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module="auth",
                event="auth_clear_credentials_failed",
            )

    @staticmethod
    def isLoggedIn() -> bool:
        """Check if the user is logged in (strict)."""
        return SessionManager.is_session_valid()

    @staticmethod
    def needs_login() -> bool:
        if not SessionManager._instance:
            SessionManager()
        return SessionManager._get_bool_setting(SESSION_NEEDS_LOGIN, False)

    @staticmethod
    def is_session_valid() -> bool:
        if not SessionManager._instance:
            SessionManager()
        needs_login = SessionManager._get_bool_setting(SESSION_NEEDS_LOGIN, False)
        token = SessionManager._instance.apiToken
        token_str = str(token).strip() if token is not None else ""
        return bool(token_str) and not needs_login

    @staticmethod
    def show_session_expired_dialog(parent=None, lang_manager=None) -> bool | str:
        """Show a styled info dialog with Log in and Cancel options. Persist needs_login flag if canceled."""
        if SessionManager._session_expired_shown:
            return "shown"
        SessionManager._session_expired_shown = True
        title = lang_manager.translate(TranslationKeys.SESSION_EXPIRED_TITLE) if lang_manager else "Session expired"
        text = lang_manager.translate(TranslationKeys.SESSION_EXPIRED) if lang_manager else "Session expired. Please log in again."
        login_label = lang_manager.translate(TranslationKeys.LOGIN_BUTTON) if lang_manager else "Login"
        cancel_label = lang_manager.translate(TranslationKeys.CANCEL_BUTTON) if lang_manager else "Cancel"
        choice = ModernMessageDialog.ask_choice_modern(
            title,
            text,
            buttons=[login_label, cancel_label],
            default=login_label,
            cancel=cancel_label,
        )
        if choice == login_label:
            return True
        SessionManager.clear()
        return False

    @staticmethod
    def setSession(apiToken: Optional[str], user: Optional[str]) -> None:
        """Set the session data and reset expired dialog flag."""
        if not SessionManager._instance:  # Ensure the instance is initialized
            SessionManager()
        #print(f"[DEBUG] Setting session with token: {apiToken[:10] if apiToken else None}...")
        SessionManager._instance.apiToken = apiToken
        SessionManager._instance.loggedInUser = user
        SessionManager._session_expired_shown = False
        SessionManager._login_cancelled_for_reason = None
        SessionManager._last_login_reason = None
        SessionManager._instance.settings.setValue(SESSION_NEEDS_LOGIN, False)
        SessionManager.save_session()  # Always save after setting
        SessionManager._notify_session_changed()
        PythonFailLogger.log(
            "login_session_set",
            module="auth",
            extra={"user": str(user or "")},
        )

    @staticmethod
    def isSessionExpired() -> bool:
        """Check if the session is expired."""
        if not SessionManager._instance:
            SessionManager()
        needs_login = SessionManager._get_bool_setting(SESSION_NEEDS_LOGIN, False)
        token_missing = not bool(SessionManager._instance.apiToken)

        return needs_login or token_missing

    @staticmethod
    def revalidateSession() -> bool:
        """Revalidate the session if expired."""
        if not SessionManager._instance:  # Ensure the instance is initialized
            SessionManager()
        return SessionManager.is_session_valid()

    def get_token(self) -> Optional[str]:
        """Return the current session's API token only if session is valid."""
        if not SessionManager.is_session_valid():
            return None
        return self.get_token_raw()

    def get_token_raw(self) -> Optional[str]:
        """Return the current session's API token without validity checks."""
        if hasattr(self, "apiToken") and self.apiToken:
            return self.apiToken
        token = self.settings.value(SESSION_TOKEN, None)
        return token

    @staticmethod
    def register_listener(listener) -> None:
        if listener in SessionManager._listeners:
            return
        SessionManager._listeners.append(listener)

    @staticmethod
    def unregister_listener(listener) -> None:
        if listener in SessionManager._listeners:
            SessionManager._listeners.remove(listener)

    @staticmethod
    def _notify_session_changed() -> None:
        for listener in list(SessionManager._listeners):
            try:
                listener()
            except Exception as exc:
                PythonFailLogger.log_exception(
                    exc,
                    module="auth",
                    event="session_listener_failed",
                )

    @staticmethod
    def invalidate_session(reason: Optional[str] = None) -> None:
        if not SessionManager._instance:
            SessionManager()
        settings = SessionManager._instance.settings
        already_invalid = SessionManager._get_bool_setting(SESSION_NEEDS_LOGIN, False)
        if not already_invalid:
            settings.setValue(SESSION_NEEDS_LOGIN, True)
            settings.remove(SESSION_TOKEN)
            settings.remove(SESSION_ACTIVE_USER)
            SessionManager._instance.apiToken = None
            SessionManager._instance.loggedInUser = None
            SessionManager.save_session()
            SessionManager._notify_session_changed()
        SessionManager.request_login(reason=reason)

    @staticmethod
    def request_login(parent=None, reason: Optional[str] = None) -> None:
        if SessionManager._login_dialog_open:
            return
        if reason and SessionManager._login_cancelled_for_reason == reason and reason not in ("startup", "manual"):
            return
        SessionManager._login_dialog_open = True
        SessionManager._last_login_reason = reason
        PythonFailLogger.log(
            "login_dialog_requested",
            module="auth",
            extra={"reason": str(reason or "")},
        )

        def _resolve_parent():
            try:
                if parent is not None:
                    return parent
            except Exception:
                return None
            try:
                from qgis.utils import iface
                if iface:
                    return iface.mainWindow()
            except Exception:
                return None
            try:
                from PyQt5.QtWidgets import QApplication
                return QApplication.activeWindow()
            except Exception:
                return None

        def _open_dialog():
            try:
                from ..login_dialog import LoginDialog

                dlg = LoginDialog(parent=_resolve_parent())
                result = dlg.exec_()
                if result == 0:
                    SessionManager._login_cancelled_for_reason = reason
                    PythonFailLogger.log(
                        "login_dialog_cancelled",
                        module="auth",
                        extra={"reason": str(reason or "")},
                    )
                if SessionManager.is_session_valid():
                    QTimer.singleShot(0, SessionManager._notify_session_changed)
                    PythonFailLogger.log(
                        "login_dialog_success",
                        module="auth",
                        extra={"reason": str(reason or "")},
                    )
                else:
                    if result != 0:
                        PythonFailLogger.log(
                            "login_dialog_no_session",
                            module="auth",
                            extra={"reason": str(reason or "")},
                        )
            except Exception as exc:
                PythonFailLogger.log_exception(
                    exc,
                    module="auth",
                    event="login_dialog_open_failed",
                )
            finally:
                SessionManager._login_dialog_open = False

        QTimer.singleShot(0, _open_dialog)

    @staticmethod
    def _get_bool_setting(key: str, default: bool) -> bool:
        if not SessionManager._instance:
            SessionManager()
        value = SessionManager._instance.settings.value(key, default, type=bool)
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.strip().lower() in ("1", "true", "yes", "y", "on")
        if isinstance(value, (int, float)):
            return bool(value)
        return bool(value) if value is not None else default


# ------------------------------------------------------------------
# SessionUIController (UI flow helpers)
# ------------------------------------------------------------------
class SessionUIController:
    @staticmethod
    def logout(dialog: "SessionDialogProtocol") -> None:
        import gc

        PythonFailLogger.log(
            "logout_requested",
            module="auth",
        )
        SessionManager.clear()
        gc.collect()
        try:
            setattr(dialog, "_force_close", True)
        except Exception:
            pass
        dialog.close()
        try:
            dialog.deleteLater()
        except Exception:
            pass
        PythonFailLogger.log(
            "logout_dialog_closed",
            module="auth",
        )

    @staticmethod
    def ensure_logged_in(dialog: "SessionDialogProtocol") -> bool:
        if not SessionManager().isLoggedIn():
            dialog.close()
            return False
        return True

    @staticmethod
    def after_show(dialog: "SessionDialogProtocol") -> None:
        from ..Logs.switch_logger import SwitchLogger
        from .url_manager import Module
        from .moduleSwitchHelper import ModuleSwitchHelper
        from ..constants.settings_keys import SettingsService
        if not hasattr(dialog, "_session_listener"):
            def _listener():
                SessionUIController.refresh_login_ui(dialog)

            dialog._session_listener = _listener
            SessionManager.register_listener(_listener)
            try:
                if hasattr(dialog, "destroyed"):
                    dialog.destroyed.connect(lambda *_: SessionManager.unregister_listener(_listener))
            except Exception:
                pass

        SessionUIController.refresh_login_ui(dialog)
        if dialog._has_shown and dialog.moduleManager.getActiveModuleName():
            # Preserve the current active module on subsequent shows
            active_name = dialog.moduleManager.getActiveModuleName()
            inst = dialog.moduleManager.getActiveModuleInstance(active_name)
            if inst:
                try:
                    widget = inst.get_widget()
                    if widget:
                        dialog.moduleStack.setCurrentWidget(widget)
                        dialog.sidebar.setActiveModuleOnSidebarButton(active_name)
                except Exception as exc:
                    SwitchLogger.log(
                        "dialog_restore_widget_failed",
                        module=active_name,
                        extra={"error": str(exc)},
                    )
            return

        pref_key = SettingsService().preferred_module().lower() or ""
        if pref_key and pref_key in dialog.moduleManager.modules:
            ModuleSwitchHelper.switch_module(pref_key, dialog=dialog)
        else:
            ModuleSwitchHelper.switch_module(Module.HOME.name, dialog=dialog)
        dialog._has_shown = True

    @staticmethod
    def refresh_login_ui(dialog: "SessionDialogProtocol") -> None:
        """Update UI state based on session validity (no dialog opening here)."""
        is_valid = SessionManager.is_session_valid()
        try:
            if hasattr(dialog, "sidebar"):
                dialog.sidebar.setEnabled(is_valid)
            if hasattr(dialog, "moduleStack"):
                dialog.moduleStack.setEnabled(is_valid)
            if hasattr(dialog, "footer_widget"):
                dialog.footer_widget.setEnabled(is_valid)
            header = getattr(dialog, "header_widget", None)
            if header and hasattr(header, "logoutButton"):
                header.logoutButton.setEnabled(is_valid)
        except Exception:
            pass