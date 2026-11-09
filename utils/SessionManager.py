from threading import RLock
from typing import Callable, Optional

from qgis.PyQt.QtCore import QCoreApplication, QObject, pyqtSignal, pyqtSlot

from qgis.core import QgsApplication, QgsAuthMethodConfig, QgsSettings
from ..Logs.python_fail_logger import PythonFailLogger
from .secure_session_store import (
    AUTH_ID,
    AUTH_USERNAME,
    LEGACY_SESSION_TOKEN,
    SecureSessionStore,
)


"""Session state and persistence. Nothing here shows a window: the UI layer registers how a login is asked for.

Sections:
- Session constants
- SessionGuiBridge (worker thread -> GUI thread hand-off)
- SessionManager (persistence/auth)
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
            SessionManager.notify_session_changed()
        SessionManager.request_login(reason=reason or None)


# ------------------------------------------------------------------
# SessionManager (persistence/auth)
# ------------------------------------------------------------------
class SessionManager:

    _instance = None
    _login_dialog_open = False
    _login_prompt: Optional[Callable[[object, Optional[str]], None]] = None
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
        SessionManager.notify_session_changed()
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
        SessionManager.notify_session_changed()
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
    def take_pending_storage_warning() -> Optional[str]:
        """Return the storage problem found while loading, once."""
        status = SessionManager._storage_warning_pending
        SessionManager._storage_warning_pending = None
        return status

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
    def notify_session_changed() -> None:
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
    def set_login_prompt(prompt: Optional[Callable[[object, Optional[str]], None]]) -> None:
        """Set how a login is asked for: ``prompt(parent, reason)``. The plugin does this at start and unload."""
        SessionManager._login_prompt = prompt

    @staticmethod
    def request_login(parent=None, reason: Optional[str] = None, user_initiated: bool = False) -> None:
        """Ask the user to log in.

        A cancelled prompt silences only the automatic retries that share its
        reason; anything the user asked for is always shown, so a cancel can
        never leave the plugin without a way back in.
        """
        if SessionManager._login_dialog_open:
            return
        if not user_initiated and reason and SessionManager._login_cancelled_for_reason == reason:
            return
        prompt = SessionManager._login_prompt
        if prompt is None:
            PythonFailLogger.log(
                "login_prompt_unavailable",
                module="auth",
                extra={"reason": str(reason or "")},
            )
            return
        SessionManager._login_dialog_open = True
        PythonFailLogger.log(
            "login_dialog_requested",
            module="auth",
            extra={"reason": str(reason or "")},
        )
        prompt(parent, reason)

    @staticmethod
    def finish_login_prompt(reason: Optional[str], *, cancelled: bool = False) -> None:
        """The prompt has closed; a cancel silences automatic retries that share its reason."""
        if cancelled:
            SessionManager._login_cancelled_for_reason = reason
        SessionManager._login_dialog_open = False

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
