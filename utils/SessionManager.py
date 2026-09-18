from threading import RLock
from typing import Optional, Protocol, TYPE_CHECKING

from qgis.PyQt.QtCore import QCoreApplication, QObject, QTimer, pyqtSignal, pyqtSlot

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
        def setEnabled(self, enabled: bool) -> None: ...

    class SidebarProtocol(Protocol):
        def setActiveModuleOnSidebarButton(self, moduleName: str) -> None: ...
        def setEnabled(self, enabled: bool) -> None: ...

    class LogoutButtonProtocol(Protocol):
        def setEnabled(self, enabled: bool) -> None: ...

    class HeaderProtocol(Protocol):
        logoutButton: LogoutButtonProtocol

    class FooterProtocol(Protocol):
        def setEnabled(self, enabled: bool) -> None: ...

    class SessionDialogProtocol(Protocol):
        _has_shown: bool
        moduleManager: ModuleManagerProtocol
        moduleStack: ModuleStackProtocol
        sidebar: SidebarProtocol
        header_widget: HeaderProtocol
        footer_widget: FooterProtocol
        def close(self) -> None: ...
        def hide(self) -> None: ...
from qgis.core import QgsApplication, QgsAuthMethodConfig, QgsSettings
from ..languages.translation_keys import TranslationKeys
from .messagesHelper import ModernMessageDialog
from ..Logs.python_fail_logger import PythonFailLogger
from .secure_session_store import (
    AUTH_ID,
    AUTH_USERNAME,
    LEGACY_SESSION_TOKEN,
    SecureSessionStore,
)


"""Session persistence + UI session flow (single-file layout).

Sections:
- Session constants
- SessionGuiBridge (worker thread -> GUI thread hand-off)
- SessionManager (persistence/auth)
- SessionUIController (UI lifecycle helpers)
"""

# ------------------------------------------------------------------
# Session constants
# ------------------------------------------------------------------
SESSION_TOKEN = LEGACY_SESSION_TOKEN
SESSION_ACTIVE_USER = "session/user"
SESSION_NEEDS_LOGIN = "session/needs_login"

SESSION_STORAGE_PERSISTENT = "persistent"
SESSION_STORAGE_MEMORY_ONLY = "memory_only"
SESSION_STORAGE_MIGRATION_PENDING = "migration_pending"
SESSION_STORAGE_CLEANUP_FAILED = "cleanup_failed"

SESSION_REASON_UNAUTHENTICATED = "unauthenticated"


# ------------------------------------------------------------------
# SessionGuiBridge (worker thread -> GUI thread hand-off)
# ------------------------------------------------------------------
class SessionGuiBridge(QObject):
    """Carries session invalidation from any thread onto the GUI thread.

    Worker threads started by ``start_worker`` run their own event loop, so a
    QTimer or a login dialog created there would live outside the GUI thread.
    This object is pinned to the application thread; the default AutoConnection
    stays direct for GUI-thread emitters and queues for worker threads.
    """

    sessionInvalidated = pyqtSignal(bool, str)

    def __init__(self) -> None:
        super().__init__()
        app = QCoreApplication.instance()
        if app is not None:
            self.moveToThread(app.thread())
        self.sessionInvalidated.connect(self._on_session_invalidated)

    @pyqtSlot(bool, str)
    def _on_session_invalidated(self, notify: bool, reason: str) -> None:
        if notify:
            SessionManager._notify_session_changed()
        SessionManager.request_login(reason=reason or None)


# ------------------------------------------------------------------
# SessionManager (persistence/auth)
# ------------------------------------------------------------------
class SessionManager:

    _instance = None
    _login_dialog_open = False
    _login_cancelled_for_reason: Optional[str] = None
    _listeners: list = []
    _storage_warning_pending: Optional[str] = None
    _state_lock = RLock()
    _gui_bridge_instance: Optional[SessionGuiBridge] = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(SessionManager, cls).__new__(cls)
            cls._instance.apiToken = None
            cls._instance.loggedInUser = None
            cls._instance.settings = QgsSettings()
            cls._instance.auth_manager = QgsApplication.authManager()
            cls._instance.secure_store = SecureSessionStore(
                cls._instance.auth_manager,
                cls._instance.settings,
                QgsAuthMethodConfig,
            )
            cls._instance.username = None
            cls._instance.session_generation = 0
        return cls._instance


    @staticmethod
    def load() -> str:
        """Restore a session from QGIS auth storage and migrate legacy data."""
        if not SessionManager._instance:
            SessionManager()
        session = SessionManager._instance
        settings = session.settings
        session.apiToken = None
        session.loggedInUser = settings.value(SESSION_ACTIVE_USER, None)
        session.username = (
            session.secure_store.username()
            or SessionManager._username_from_user(session.loggedInUser)
        )
        SessionManager._storage_warning_pending = None

        if SessionManager._get_bool_setting(SESSION_NEEDS_LOGIN, False):
            session.secure_store.purge_legacy_token()
            SessionManager._advance_session_generation()
            return "login_required"

        legacy_token = str(settings.value(SESSION_TOKEN, "") or "").strip()
        if legacy_token:
            username = session.username or SessionManager._username_from_user(session.loggedInUser)
            stored = session.secure_store.save_token(username, legacy_token)
            session.apiToken = legacy_token
            SessionManager._advance_session_generation()
            if stored.success:
                if not stored.plaintext_purged:
                    SessionManager._set_storage_warning(SESSION_STORAGE_CLEANUP_FAILED)
                    return SESSION_STORAGE_CLEANUP_FAILED
                if stored.cleanup_pending:
                    SessionManager._set_storage_warning(SESSION_STORAGE_MIGRATION_PENDING)
                    return SESSION_STORAGE_MIGRATION_PENDING
                return SESSION_STORAGE_PERSISTENT

            warning_status = (
                SESSION_STORAGE_MEMORY_ONLY
                if stored.plaintext_purged
                else SESSION_STORAGE_CLEANUP_FAILED
            )
            SessionManager._set_storage_warning(warning_status)
            PythonFailLogger.log(
                "legacy_session_secure_store_failed",
                module="auth",
                extra={"reason": stored.reason},
            )
            return warning_status

        loaded = session.secure_store.load_token()
        if not loaded.success or not loaded.token:
            SessionManager._advance_session_generation()
            PythonFailLogger.log(
                "secure_session_not_restored",
                module="auth",
                extra={"reason": loaded.reason},
            )
            return "login_required"

        session.apiToken = loaded.token
        SessionManager._advance_session_generation()
        if loaded.requires_migration:
            stored = session.secure_store.save_token(session.username, loaded.token)
            if not stored.plaintext_purged:
                warning_status = SESSION_STORAGE_CLEANUP_FAILED
            elif not stored.success or stored.cleanup_pending:
                warning_status = SESSION_STORAGE_MIGRATION_PENDING
            else:
                warning_status = ""
            if warning_status:
                SessionManager._set_storage_warning(warning_status)
                PythonFailLogger.log(
                    "secure_session_migration_pending",
                    module="auth",
                    extra={"reason": stored.reason},
                )
                return warning_status
        elif session.secure_store.cleanup_stale_configs():
            SessionManager._set_storage_warning(SESSION_STORAGE_MIGRATION_PENDING)
            return SESSION_STORAGE_MIGRATION_PENDING
        return SESSION_STORAGE_PERSISTENT

    @staticmethod
    def save_session() -> None:
        """Persist non-secret session metadata; the token stays out of settings."""
        if not SessionManager._instance:
            SessionManager()
        settings = SessionManager._instance.settings
        SessionManager._instance.secure_store.purge_legacy_token()
        if SessionManager._instance.loggedInUser:
            settings.setValue(SESSION_ACTIVE_USER, SessionManager._instance.loggedInUser)
        else:
            settings.remove(SESSION_ACTIVE_USER)
        settings.sync()  # Ensure settings are written immediately


    @staticmethod
    def clear() -> None:
        """Clear the session and forget the stored token (logout, no auto-login)."""
        if not SessionManager._instance:
            SessionManager()
        with SessionManager._state_lock:
            session = SessionManager._instance
            session.settings.setValue(SESSION_NEEDS_LOGIN, True)
            session.apiToken = None
            session.loggedInUser = None
            # Leaving the token at rest would let a flipped needs_login flag restore it.
            session.clear_credentials()
            SessionManager._advance_session_generation()
            SessionManager._login_cancelled_for_reason = None
            SessionManager.save_session()  # purges the legacy token and syncs
        SessionManager._notify_session_changed()
        PythonFailLogger.log(
            "logout_session_cleared",
            module="auth",
        )
    # --- Secure Credential Handling (QgsAuthenticationManager) ---
    def get_username(self) -> str:
        self.username = (
            self.secure_store.username()
            or SessionManager._username_from_user(self.loggedInUser)
        )
        return str(self.username or "").strip()

    def clear_session(self) -> None:
        self.username = None
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
    def is_session_valid() -> bool:
        if not SessionManager._instance:
            SessionManager()
        needs_login = SessionManager._get_bool_setting(SESSION_NEEDS_LOGIN, False)
        token = SessionManager._instance.apiToken
        token_str = str(token).strip() if token is not None else ""
        return bool(token_str) and not needs_login

    @staticmethod
    def setSession(
        apiToken: Optional[str],
        user: Optional[object],
        username: Optional[str] = None,
    ) -> str:
        """Securely persist a token when possible, then activate it in memory."""
        if not SessionManager._instance:  # Ensure the instance is initialized
            SessionManager()
        session = SessionManager._instance
        token = str(apiToken or "").strip()
        resolved_username = str(
            username or SessionManager._username_from_user(user) or session.get_username()
        ).strip()
        stored = session.secure_store.save_token(resolved_username, token)
        if not stored.plaintext_purged:
            storage_status = SESSION_STORAGE_CLEANUP_FAILED
        elif stored.success:
            storage_status = (
                SESSION_STORAGE_MIGRATION_PENDING
                if stored.cleanup_pending
                else SESSION_STORAGE_PERSISTENT
            )
        else:
            storage_status = SESSION_STORAGE_MEMORY_ONLY
            PythonFailLogger.log(
                "login_secure_store_failed",
                module="auth",
                extra={"reason": stored.reason},
            )

        session.apiToken = token or None
        session.loggedInUser = user
        session.username = resolved_username or None
        SessionManager._advance_session_generation()
        SessionManager._login_cancelled_for_reason = None
        session.settings.setValue(SESSION_NEEDS_LOGIN, False)
        SessionManager.save_session()  # Always save after setting
        SessionManager._notify_session_changed()
        PythonFailLogger.log(
            "login_session_set",
            module="auth",
            extra={"user": resolved_username, "storage": storage_status},
        )
        return storage_status

    def get_token(self) -> Optional[str]:
        """Return the in-memory API token only while the session is valid."""
        if not SessionManager.is_session_valid():
            return None
        return self.apiToken or None

    @staticmethod
    def session_signature() -> str:
        """Return a non-secret generation value for session-scoped caches."""
        if not SessionManager._instance:
            SessionManager()
        return str(SessionManager._instance.session_generation)

    @staticmethod
    def show_storage_warning(status: str, parent=None, lang_manager=None) -> None:
        if status not in (
            SESSION_STORAGE_MEMORY_ONLY,
            SESSION_STORAGE_MIGRATION_PENDING,
            SESSION_STORAGE_CLEANUP_FAILED,
        ):
            return
        manager = lang_manager
        if manager is None:
            from ..languages.language_manager import LanguageManager

            manager = LanguageManager()
        title = manager.translate(TranslationKeys.SESSION_STORAGE_WARNING_TITLE)
        message_keys = {
            SESSION_STORAGE_MEMORY_ONLY: TranslationKeys.SESSION_STORAGE_MEMORY_ONLY,
            SESSION_STORAGE_MIGRATION_PENDING: TranslationKeys.SESSION_STORAGE_MIGRATION_PENDING,
            SESSION_STORAGE_CLEANUP_FAILED: TranslationKeys.SESSION_STORAGE_CLEANUP_FAILED,
        }
        ModernMessageDialog.show_warning(
            title,
            manager.translate(message_keys[status]),
            parent=parent,
        )

    @staticmethod
    def show_pending_storage_warning(parent=None, lang_manager=None) -> None:
        status = SessionManager._storage_warning_pending
        SessionManager._storage_warning_pending = None
        if status:
            SessionManager.show_storage_warning(status, parent=parent, lang_manager=lang_manager)

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
        """Drop the active session from any thread.

        The token is cleared synchronously so an in-flight worker cannot send it
        again, while the listener notification and the login dialog are handed to
        the GUI thread by :class:`SessionGuiBridge`.
        """
        if not SessionManager._instance:
            SessionManager()
        with SessionManager._state_lock:
            became_invalid = not SessionManager._get_bool_setting(SESSION_NEEDS_LOGIN, False)
            if became_invalid:
                session = SessionManager._instance
                session.settings.setValue(SESSION_NEEDS_LOGIN, True)
                session.apiToken = None
                session.loggedInUser = None
                SessionManager._advance_session_generation()
                SessionManager.save_session()  # purges the legacy token and syncs
        SessionManager._gui_bridge().sessionInvalidated.emit(became_invalid, str(reason or ""))

    @staticmethod
    def _gui_bridge() -> SessionGuiBridge:
        with SessionManager._state_lock:
            if SessionManager._gui_bridge_instance is None:
                SessionManager._gui_bridge_instance = SessionGuiBridge()
            return SessionManager._gui_bridge_instance

    @staticmethod
    def request_login(parent=None, reason: Optional[str] = None, user_initiated: bool = False) -> None:
        """Open the login dialog.

        A cancelled prompt silences only the automatic retries that share its
        reason; anything the user asked for is always shown, so a cancel can
        never leave the plugin without a way back in.
        """
        if SessionManager._login_dialog_open:
            return
        if not user_initiated and reason and SessionManager._login_cancelled_for_reason == reason:
            return
        SessionManager._login_dialog_open = True
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
                if SessionManager.is_session_valid():
                    QTimer.singleShot(0, SessionManager._notify_session_changed)
                    PythonFailLogger.log(
                        "login_dialog_success",
                        module="auth",
                        extra={"reason": str(reason or "")},
                    )
                elif result == 0:
                    SessionManager._login_cancelled_for_reason = reason
                    PythonFailLogger.log(
                        "login_dialog_cancelled",
                        module="auth",
                        extra={"reason": str(reason or "")},
                    )
                else:
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
    def _set_storage_warning(status: str) -> None:
        SessionManager._storage_warning_pending = status

    @staticmethod
    def _advance_session_generation() -> None:
        if not SessionManager._instance:
            SessionManager()
        SessionManager._instance.session_generation += 1

    @staticmethod
    def _username_from_user(user: Optional[object]) -> str:
        if isinstance(user, dict):
            for key in ("name", "username", "email"):
                value = str(user.get(key) or "").strip()
                if value:
                    return value
            return ""
        return str(user or "").strip()

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
        """Refuse to show an unusable window; ask for a login instead.

        ``close()`` only minimises this dialog, so returning without a prompt
        used to leave a blank window and no explanation.
        """
        if SessionManager.is_session_valid():
            return True
        dialog.hide()
        SessionManager.request_login(reason="dialog_show", user_initiated=True)
        return False

    @staticmethod
    def after_show(dialog: "SessionDialogProtocol") -> None:
        from ..Logs.switch_logger import SwitchLogger
        from .url_manager import Module
        from .moduleSwitchHelper import ModuleSwitchHelper
        from ..constants.settings_keys import SettingsService
        if not hasattr(dialog, "_session_listener"):
            def _listener():
                SessionUIController.handle_session_changed(dialog)

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
    def handle_session_changed(dialog: "SessionDialogProtocol") -> None:
        SessionUIController.refresh_login_ui(dialog)
        refresh = getattr(dialog, "_refresh_session_dependent_ui", None)
        if callable(refresh):
            refresh()

    @staticmethod
    def refresh_login_ui(dialog: "SessionDialogProtocol") -> None:
        """Gate session-scoped UI on session validity (no dialog opening here).

        Logout stays enabled on purpose: it is the only action that resets a
        session stuck behind a cancelled login prompt.
        """
        is_valid = SessionManager.is_session_valid()
        dialog.sidebar.setEnabled(is_valid)
        dialog.moduleStack.setEnabled(is_valid)
        dialog.footer_widget.setEnabled(is_valid)
        dialog.header_widget.logoutButton.setEnabled(True)
