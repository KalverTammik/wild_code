from qgis.PyQt.QtCore import QSettings
from qgis.core import QgsApplication, QgsAuthMethodConfig
from ..languages.translation_keys import TranslationKeys


SESSION_TOKEN = "session/token"
SESSION_ACTIVE_USER = "session/active_user"
SESSION_NEEDS_LOGIN = "session/needs_login"


# Authentication
AUTH_ID = "myplugin/auth_id"
AUTH_USERNAME = "myplugin/username"


class SessionManager:

    _instance = None
    _session_expired_shown = False

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(SessionManager, cls).__new__(cls, *args, **kwargs)
            cls._instance.apiToken = None
            cls._instance.loggedInUser = None
            cls._instance.settings = QSettings()
            cls._instance.auth_manager = QgsApplication.authManager()
            cls._instance.username = None
            cls._instance.password = None
            cls._instance.api_key = None
        return cls._instance


    @staticmethod
    def load():
        """Load session data from QSettings."""
        if not SessionManager._instance:
            SessionManager()
        settings = SessionManager._instance.settings
        SessionManager._instance.apiToken = settings.value(SESSION_TOKEN, None)
        SessionManager._instance.loggedInUser = settings.value(SESSION_ACTIVE_USER, None)
        SessionManager._instance._needs_login = bool(settings.value(SESSION_NEEDS_LOGIN, False))
        

    @staticmethod
    def save_session():
        """Save session data to QSettings."""
        if not SessionManager._instance:
            SessionManager()
        settings = SessionManager._instance.settings
        settings.setValue(SESSION_TOKEN, SessionManager._instance.apiToken)
        settings.setValue(SESSION_ACTIVE_USER, SessionManager._instance.loggedInUser)
        settings.sync()  # Ensure settings are written immediately


    @staticmethod
    def clear():
        """Clear session data from QSettings."""
        if not SessionManager._instance:
            SessionManager()
        settings = SessionManager._instance.settings
        settings.remove(SESSION_TOKEN)
        settings.remove(SESSION_ACTIVE_USER)
        settings.setValue(SESSION_NEEDS_LOGIN, True)
        SessionManager._instance.apiToken = None
        SessionManager._instance.loggedInUser = None
        SessionManager._instance._needs_login = True
        SessionManager._session_expired_shown = False
        SessionManager.save_session()  # Ensure persistent storage is updated
    # --- Secure Credential Handling (QgsAuthenticationManager) ---
    def save_credentials(self, username: str, password: str, api_key: str):
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
                from .logger import error as log_error
                log_error("Failed to store authentication config.")
            except Exception:
                pass

    def load_credentials(self):
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
                from .logger import error as log_error
                log_error("Failed to load authentication config.")
            except Exception:
                pass
            return False

    def clear_session(self):
        self.username = None
        self.password = None
        self.api_key = None
        # Session data cleared.

    @staticmethod
    def isLoggedIn():
        """Check if the user is logged in."""
        if not SessionManager._instance:  # Ensure the instance is initialized
            SessionManager()
        needs_login = bool(SessionManager._instance.settings.value(SESSION_NEEDS_LOGIN, False))
        logged_in = SessionManager._instance.apiToken is not None and not needs_login
        return logged_in

    @staticmethod
    def needs_login() -> bool:
        if not SessionManager._instance:
            SessionManager()
        return bool(SessionManager._instance.settings.value(SESSION_NEEDS_LOGIN, False))

    @staticmethod
    def show_session_expired_dialog(parent=None, lang_manager=None):
        """Show a styled info dialog with Log in and Cancel options. Persist needs_login flag if canceled."""
        if SessionManager._session_expired_shown:
            return "shown"
        SessionManager._session_expired_shown = True
        from qgis.PyQt.QtWidgets import QMessageBox
        msg = QMessageBox(parent)
        msg.setIcon(QMessageBox.Information)
        msg.setWindowTitle(lang_manager.translate(TranslationKeys.SESSION_EXPIRED_TITLE))
        text = lang_manager.translate(TranslationKeys.SESSION_EXPIRED)
        msg.setText(text)
        login_btn = msg.addButton(lang_manager.translate(TranslationKeys.LOGIN_BUTTON), QMessageBox.AcceptRole)
        cancel_btn = msg.addButton(lang_manager.translate(TranslationKeys.CANCEL_BUTTON), QMessageBox.RejectRole)
        msg.exec_()
        if msg.clickedButton() == login_btn:
            #print("[SessionManager] Log in button clicked")
            return True
        else:
            #print("[SessionManager] Cancel button clicked")
            SessionManager.clear()
            return False

    @staticmethod
    def setSession(apiToken, user):
        """Set the session data and reset expired dialog flag."""
        if not SessionManager._instance:  # Ensure the instance is initialized
            SessionManager()
        #print(f"[DEBUG] Setting session with token: {apiToken[:10] if apiToken else None}...")
        SessionManager._instance.apiToken = apiToken
        SessionManager._instance.loggedInUser = user
        SessionManager._instance._session_expired_shown = False
        SessionManager._instance._needs_login = False
        SessionManager._instance.settings.setValue(SESSION_NEEDS_LOGIN, False)
        SessionManager.save_session()  # Always save after setting

    @staticmethod
    def isSessionExpired():
        """Check if the session is expired."""
        if not SessionManager._instance:
            SessionManager()

        settings = SessionManager._instance.settings
        needs_login = bool(settings.value(SESSION_NEEDS_LOGIN, False))
        token_missing = not bool(SessionManager._instance.apiToken)

        return needs_login or token_missing

    @staticmethod
    def revalidateSession():
        """Revalidate the session if expired."""
        if not SessionManager._instance:  # Ensure the instance is initialized
            SessionManager()
        is_expired = SessionManager.isSessionExpired()
        if is_expired:
            SessionManager.clear()
            return False
        return True

    def get_token(self):
        """Return the current session's API token, or None if not logged in."""
        if hasattr(self, 'apiToken') and self.apiToken:
            return self.apiToken
        # Fallback: try to get from QSettings if not present in memory
        token = self.settings.value(SESSION_TOKEN, None)
        return token