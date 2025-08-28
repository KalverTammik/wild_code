from qgis.PyQt.QtCore import QSettings
from qgis.core import QgsApplication, QgsAuthMethodConfig
from qgis.PyQt.QtWidgets import QMessageBox

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
        SessionManager._instance.apiToken = settings.value("session/token", None)
        SessionManager._instance.loggedInUser = settings.value("session/active_user", None)
        print(f"[DEBUG] Session loaded: token={bool(SessionManager._instance.apiToken)}")


    @staticmethod
    def save_session():
        """Save session data to QSettings."""
        if not SessionManager._instance:
            SessionManager()
        settings = SessionManager._instance.settings
        settings.setValue("session/token", SessionManager._instance.apiToken)
        settings.setValue("session/active_user", SessionManager._instance.loggedInUser)
        settings.sync()  # Ensure settings are written immediately


    @staticmethod
    def clear():
        """Clear session data from QSettings."""
        if not SessionManager._instance:
            SessionManager()
        settings = SessionManager._instance.settings
        settings.remove("session/token")
        settings.remove("session/active_user")
        SessionManager._instance.apiToken = None
        SessionManager._instance.loggedInUser = None
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
            self.settings.setValue("myplugin/auth_id", config.id())
            self.settings.setValue("myplugin/username", username)
            try:
                from .logger import debug as log_debug
                log_debug("Credentials securely stored.")
            except Exception:
                pass
        else:
            try:
                from .logger import error as log_error
                log_error("Failed to store authentication config.")
            except Exception:
                pass

    def load_credentials(self):
        auth_id = self.settings.value("myplugin/auth_id", "")
        self.username = self.settings.value("myplugin/username", "")

        if not auth_id:
            try:
                from .logger import debug as log_debug
                log_debug("No stored auth ID found.")
            except Exception:
                pass
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
        try:
            from .logger import debug as log_debug
            log_debug("Session data cleared.")
        except Exception:
            pass

    @staticmethod
    def isLoggedIn():
        """Check if the user is logged in."""
        if not SessionManager._instance:  # Ensure the instance is initialized
            SessionManager()
        logged_in = SessionManager._instance.apiToken is not None
        return logged_in

    @staticmethod
    def show_session_expired_dialog(parent=None, lang_manager=None):
        """Show a styled info dialog with Log in and Cancel options. Persist needs_login flag if canceled."""
        if SessionManager._session_expired_shown:
            return "shown"
        SessionManager._session_expired_shown = True
        from qgis.PyQt.QtWidgets import QMessageBox
        msg = QMessageBox(parent)
        msg.setIcon(QMessageBox.Information)
        msg.setWindowTitle("Session Expired")
        text = lang_manager.translate("session_expired") if lang_manager else "Your session has expired. Please sign in again."
        msg.setText(text)
        login_btn = msg.addButton(lang_manager.translate("login_button") if lang_manager else "Log in", QMessageBox.AcceptRole)
        cancel_btn = msg.addButton(lang_manager.translate("cancel_button") if lang_manager else "Cancel", QMessageBox.RejectRole)
        msg.exec_()
        if msg.clickedButton() == login_btn:
            print("[SessionManager] Log in button clicked")
            return "login"
        else:
            print("[SessionManager] Cancel button clicked")
            SessionManager.clear()
            SessionManager._instance.settings.setValue("session/needs_login", True)
            return "cancel"

    @staticmethod
    def setSession(apiToken, user):
        """Set the session data and reset expired dialog flag."""
        if not SessionManager._instance:  # Ensure the instance is initialized
            SessionManager()
        print(f"[DEBUG] Setting session with token: {apiToken[:10] if apiToken else None}...")
        SessionManager._instance.apiToken = apiToken
        SessionManager._instance.loggedInUser = user
        SessionManager._instance._session_expired_shown = False
        SessionManager.save_session()  # Always save after setting

    @staticmethod
    def isSessionExpired():
        """Check if the session is expired."""
        # TODO: Implement real session expiry logic
        expired = False  # Replace with actual logic
        return expired

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
        token = self.settings.value("session/token", None)
        return token