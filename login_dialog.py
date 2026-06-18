
from PyQt5.QtCore import pyqtSignal, Qt
from .widgets.FooterWidget import FooterWidget
from qgis.PyQt.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, QHBoxLayout, QComboBox
)

from .widgets.theme_manager import ThemeManager
from .constants.file_paths import QssPaths
from .constants.module_icons import IconNames
from .constants.button_props import ButtonVariant, ButtonSize
from .languages.language_manager import LanguageManager
from .utils.SessionManager import SessionManager
#import tranlation keys
from .languages.translation_keys import TranslationKeys, DialogLabels
from .python.api_client import APIClient

lang = LanguageManager(language="et")

class LoginDialog(QDialog):
    loginSuccessful = pyqtSignal(str, dict)

    def __init__(
        self,
        title=LanguageManager().translate(TranslationKeys.LOGIN_BUTTON),
        username_label=LanguageManager().translate(DialogLabels.USERNAME_LABEL),
        password_label=LanguageManager().translate(DialogLabels.PASSWORD_LABEL),
        button_text=LanguageManager().translate(DialogLabels.LOGIN_BUTTON),
        theme_path=None,
        parent=None
    ):
        super().__init__(parent)
        self.api_token = None
        self.user = None
        self._authenticating = False
        self.setWindowTitle(title)
        self.setFixedSize(300, 400)


        ThemeManager.set_initial_theme(
            self,
            None,  # No switch button
            qss_files=ThemeManager.login_bundle()
        )

        layout = QVBoxLayout()

        self.language_label = QLabel(DialogLabels.LANGUAGE_LABEL)
        layout.addWidget(self.language_label)

        self.language_switch = QComboBox()
        self.language_switch.addItems(["et", "en", "fr"])
        self.language_switch.currentTextChanged.connect(self.change_language)
        layout.addWidget(self.language_switch)

        self.username_label = QLabel(username_label)
        self.username_label.setObjectName(DialogLabels.USERNAME_LABEL)
        layout.addWidget(self.username_label)
        self.username_input = QLineEdit()
        self.username_input.setObjectName("usernameInput")
        self.username_input.textChanged.connect(self.clear_validation_state)
        layout.addWidget(self.username_input)

        self.password_label = QLabel(password_label)
        self.password_label.setObjectName(DialogLabels.PASSWORD_LABEL)
        layout.addWidget(self.password_label)
        password_row = QHBoxLayout()
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setObjectName("passwordInput")
        self.password_input.returnPressed.connect(self.authenticate_user)
        self.password_input.textChanged.connect(self.clear_validation_state)
        password_row.addWidget(self.password_input)
        self.toggle_password_button = QPushButton()
        self.toggle_password_button.setObjectName("togglePasswordButton")
        self.toggle_password_button.setIcon(ThemeManager.get_qicon(icon_name=IconNames.ICON_EYE))
        self.toggle_password_button.setCheckable(True)
        self.toggle_password_button.setAutoDefault(False)
        self.toggle_password_button.setDefault(False)
        self.toggle_password_button.setFocusPolicy(Qt.NoFocus)
        self.toggle_password_button.setToolTip(lang.translate(TranslationKeys.TOGGLE_PASSWORD))
        self.toggle_password_button.setProperty("variant", ButtonVariant.GHOST)
        self.toggle_password_button.setProperty("btnSize", ButtonSize.SMALL)
        self.toggle_password_button.clicked.connect(self.toggle_password_visibility)
        password_row.addWidget(self.toggle_password_button, alignment=Qt.AlignRight)
        layout.addLayout(password_row)

        self.errorLabel = QLabel("")
        self.errorLabel.setObjectName(TranslationKeys.ERROR)
        self.errorLabel.setWordWrap(True)
        self.errorLabel.hide()
        layout.addWidget(self.errorLabel)


        self.login_button = QPushButton(button_text)
        self.login_button.setProperty("variant", ButtonVariant.PRIMARY)
        self.login_button.setProperty("btnSize", ButtonSize.LARGE)
        self.login_button.setAutoDefault(True)
        self.login_button.setDefault(True)
        self.login_button.clicked.connect(self.authenticate_user)
        layout.addWidget(self.login_button)

        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(self.login_button)
        layout.addLayout(button_layout)

        self.footer_widget = FooterWidget(show_left=False, show_right=True)
        layout.addWidget(self.footer_widget)

        self.toggle_password_button.setStyleSheet("")
        self.login_button.setStyleSheet("")

        self.setLayout(layout)

        self.setWindowTitle(title)
        self.language_label.setText(lang.translate(DialogLabels.LANGUAGE_LABEL))
        self.username_label.setText(username_label)
        self.password_label.setText(password_label)
        self.login_button.setText(button_text)


    def change_language(self, language):
        lang.set_language(language)
        lang.save_language_preference()
        self.setWindowTitle(LanguageManager().translate(TranslationKeys.LOGIN_BUTTON))
        self.language_label.setText(LanguageManager().translate(DialogLabels.LANGUAGE_LABEL))
        self.username_label.setText(LanguageManager().translate(DialogLabels.USERNAME_LABEL))
        self.password_label.setText(LanguageManager().translate(DialogLabels.PASSWORD_LABEL))
        self.login_button.setText(LanguageManager().translate(DialogLabels.LOGIN_BUTTON))

    def toggle_password_visibility(self):
        if self.toggle_password_button.isChecked():
            self.password_input.setEchoMode(QLineEdit.Normal)
        else:
            self.password_input.setEchoMode(QLineEdit.Password)

    def clear_validation_state(self):
        self._set_field_error(self.username_input, False)
        self._set_field_error(self.password_input, False)
        self.errorLabel.hide()

    def _set_field_error(self, field, is_error: bool) -> None:
        field.setProperty("validationState", "error" if is_error else "")
        field.style().unpolish(field)
        field.style().polish(field)
        field.update()

    def _show_login_error(self, message: str, *, username=False, password=False) -> None:
        self._set_field_error(self.username_input, username)
        self._set_field_error(self.password_input, password)
        self.errorLabel.setText(message)
        self.errorLabel.show()

    def _classify_login_error(self, error: Exception) -> tuple[str, bool, bool]:
        raw = str(error or "")
        lowered = raw.lower()

        username_markers = (
            "username",
            "user name",
            "email",
            "e-mail",
            "account",
            "user not found",
            "not found",
            "unknown user",
        )
        password_markers = (
            "password",
            "parool",
        )
        credential_markers = (
            "credential",
            "credentials",
            "email or password",
            "username or password",
            "user name or password",
            "invalid login",
            "invalid_grant",
            "authentication",
            "unauthorized",
        )

        if any(marker in lowered for marker in credential_markers):
            return lang.translate(TranslationKeys.LOGIN_CREDENTIALS_INVALID), True, True
        if any(marker in lowered for marker in username_markers):
            return lang.translate(TranslationKeys.LOGIN_USERNAME_INVALID), True, False
        if any(marker in lowered for marker in password_markers):
            return lang.translate(TranslationKeys.LOGIN_PASSWORD_INVALID), False, True
        return lang.translate(TranslationKeys.LOGIN_SERVER_UNAVAILABLE), False, False

    def authenticate_user(self):
        """Authenticate the user using the shared APIClient and show a concise server message on failure."""
        if self._authenticating:
            return
        self.clear_validation_state()

        # Always clear any existing session before attempting new login.
        SessionManager.clear()

        username = self.username_input.text().strip()
        password = self.password_input.text()
        if not username:
            self._show_login_error(
                lang.translate(TranslationKeys.LOGIN_USERNAME_REQUIRED),
                username=True,
            )
            self.username_input.setFocus()
            return
        if not password:
            self._show_login_error(
                lang.translate(TranslationKeys.LOGIN_PASSWORD_REQUIRED),
                password=True,
            )
            self.password_input.setFocus()
            return

        self._authenticating = True
        self.login_button.setEnabled(False)

        # Build GraphQL mutation (server accepts username/password in input)
        graphql = f'''
            mutation {{
                login(input: {{ username: "{username}", password: "{password}" }}) {{
                    accessToken
                    refreshToken
                    expiresIn
                }}
            }}
        '''

        api = APIClient()
        try:
            # Use shared client for consistent headers and error handling; no auth required for login
            data = api.send_query(graphql, variables=None, require_auth=False, timeout=10)
            login_data = (data or {}).get("login", {})
            api_token = login_data.get("accessToken")
            if api_token:
                self.api_token = api_token
                self.user = {"name": username, "email": username}
                SessionManager().setSession(self.api_token, self.user)
                SessionManager().save_credentials(username, password, api_token)
                self.loginSuccessful.emit(self.api_token, self.user)
                self.accept()
            else:
                # One-shot diagnostic: show server-side response issue
                self._show_login_error(
                    lang.translate(TranslationKeys.NO_API_TOKEN_RECEIVED),
                    username=True,
                    password=True,
                )
                self.login_button.setEnabled(True)
                self._authenticating = False
        except Exception as e:
            # Clear session on any login failure to allow retry
            SessionManager.clear()
            msg, username_error, password_error = self._classify_login_error(e)
            self._show_login_error(
                msg,
                username=username_error,
                password=password_error,
            )
            self.login_button.setEnabled(True)
            self._authenticating = False

