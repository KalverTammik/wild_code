
from PyQt5.QtCore import pyqtSignal, Qt
from .widgets.FooterWidget import FooterWidget
from qgis.PyQt.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, QHBoxLayout, QComboBox
)

from .widgets.theme_manager import ThemeManager
from .constants.module_icons import IconNames
from .constants.button_props import ButtonVariant, ButtonSize
from .languages.language_manager import SUPPORTED_LANGUAGES, LanguageManager
from .utils.SessionManager import SessionManager
#import tranlation keys
from .languages.translation_keys import TranslationKeys, DialogLabels
from .python.api_client import APIClient
from .python.GraphQLQueryLoader import GraphQLQueryLoader
from .utils.api_error_handling import ApiErrorKind, parse_tagged_message
from .utils.url_manager import Module

class LoginDialog(QDialog):
    loginSuccessful = pyqtSignal(str, dict)
    _PASSWORD_STEP = "password"
    _MFA_STEP = "mfa"

    def __init__(self, parent=None):
        super().__init__(parent)
        self.api_token = None
        self.user = None
        self._authenticating = False
        self._step = self._PASSWORD_STEP
        self.lang = LanguageManager()
        # The window must grow with a wrapped error message, not clip it.
        self.setMinimumSize(300, 400)

        ThemeManager.set_initial_theme(
            self,
            None,  # No switch button
            qss_files=ThemeManager.login_bundle()
        )

        layout = QVBoxLayout()

        self.language_label = QLabel()
        layout.addWidget(self.language_label)

        self.language_switch = QComboBox()
        self.language_switch.addItems(SUPPORTED_LANGUAGES)
        self.language_switch.setCurrentText(self.lang.language)
        self.language_switch.currentTextChanged.connect(self.change_language)
        layout.addWidget(self.language_switch)

        self.username_label = QLabel()
        self.username_label.setObjectName(DialogLabels.USERNAME_LABEL)
        layout.addWidget(self.username_label)
        self.username_input = QLineEdit()
        self.username_input.setObjectName("usernameInput")
        self.username_input.textChanged.connect(self.clear_validation_state)
        layout.addWidget(self.username_input)

        self.password_label = QLabel()
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
        self.toggle_password_button.setToolTip(self.lang.translate(TranslationKeys.TOGGLE_PASSWORD))
        self.toggle_password_button.setProperty("variant", ButtonVariant.GHOST)
        self.toggle_password_button.setProperty("btnSize", ButtonSize.SMALL)
        self.toggle_password_button.clicked.connect(self.toggle_password_visibility)
        password_row.addWidget(self.toggle_password_button, alignment=Qt.AlignRight)
        layout.addLayout(password_row)

        self.mfa_code_label = QLabel()
        self.mfa_code_label.setWordWrap(True)
        layout.addWidget(self.mfa_code_label)
        self.mfa_code_input = QLineEdit()
        self.mfa_code_input.setObjectName("mfaCodeInput")
        self.mfa_code_input.textChanged.connect(self._clear_mfa_validation_state)
        self.mfa_code_input.returnPressed.connect(self.verify_mfa_code)
        layout.addWidget(self.mfa_code_input)

        self.errorLabel = QLabel("")
        self.errorLabel.setObjectName(TranslationKeys.ERROR)
        self.errorLabel.setWordWrap(True)
        self.errorLabel.hide()
        layout.addWidget(self.errorLabel)


        self.login_button = QPushButton()
        self.login_button.setProperty("variant", ButtonVariant.PRIMARY)
        self.login_button.setProperty("btnSize", ButtonSize.LARGE)
        self.login_button.setAutoDefault(True)
        self.login_button.setDefault(True)
        self.login_button.clicked.connect(self.authenticate_user)

        self.mfa_back_button = QPushButton()
        self.mfa_back_button.setProperty("variant", ButtonVariant.GHOST)
        self.mfa_back_button.setProperty("btnSize", ButtonSize.LARGE)
        self.mfa_back_button.setAutoDefault(False)
        self.mfa_back_button.setDefault(False)
        self.mfa_back_button.clicked.connect(self.show_password_step)

        self.mfa_verify_button = QPushButton()
        self.mfa_verify_button.setProperty("variant", ButtonVariant.PRIMARY)
        self.mfa_verify_button.setProperty("btnSize", ButtonSize.LARGE)
        self.mfa_verify_button.setAutoDefault(True)
        self.mfa_verify_button.setDefault(False)
        self.mfa_verify_button.clicked.connect(self.verify_mfa_code)

        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(self.mfa_back_button)
        button_layout.addWidget(self.login_button)
        button_layout.addWidget(self.mfa_verify_button)
        layout.addLayout(button_layout)

        self.footer_widget = FooterWidget(show_left=False, show_right=True)
        layout.addWidget(self.footer_widget)

        self.toggle_password_button.setStyleSheet("")
        self.login_button.setStyleSheet("")
        self.mfa_back_button.setStyleSheet("")
        self.mfa_verify_button.setStyleSheet("")

        self.setLayout(layout)
        self._retranslate()
        self._apply_step()


    def _retranslate(self) -> None:
        self.setWindowTitle(self.lang.translate(TranslationKeys.LOGIN_BUTTON))
        self.language_label.setText(self.lang.translate(DialogLabels.LANGUAGE_LABEL))
        self.username_label.setText(self.lang.translate(DialogLabels.USERNAME_LABEL))
        self.password_label.setText(self.lang.translate(DialogLabels.PASSWORD_LABEL))
        self.login_button.setText(self.lang.translate(TranslationKeys.LOGIN_BUTTON))
        self.toggle_password_button.setToolTip(self.lang.translate(TranslationKeys.TOGGLE_PASSWORD))
        self.mfa_code_label.setText(self.lang.translate(TranslationKeys.MFA_CODE_PROMPT))
        self.mfa_verify_button.setText(self.lang.translate(TranslationKeys.MFA_VERIFY_BUTTON))
        self.mfa_back_button.setText(self.lang.translate(TranslationKeys.MFA_BACK_BUTTON))

    def change_language(self, language):
        self.lang.set_language(language)
        self._retranslate()

    def toggle_password_visibility(self):
        if self.toggle_password_button.isChecked():
            self.password_input.setEchoMode(QLineEdit.Normal)
        else:
            self.password_input.setEchoMode(QLineEdit.Password)

    def clear_validation_state(self):
        self._set_field_error(self.username_input, False)
        self._set_field_error(self.password_input, False)
        self.errorLabel.hide()

    def _clear_mfa_validation_state(self):
        self._set_field_error(self.mfa_code_input, False)
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

    def _show_mfa_error(self, message: str, *, code=False) -> None:
        self._set_field_error(self.mfa_code_input, code)
        self.errorLabel.setText(message)
        self.errorLabel.show()

    def _apply_step(self) -> None:
        is_mfa = self._step == self._MFA_STEP
        self.username_input.setReadOnly(is_mfa)
        self.password_input.setReadOnly(is_mfa)
        self.toggle_password_button.setEnabled(not is_mfa and not self._authenticating)
        self.mfa_code_label.setVisible(is_mfa)
        self.mfa_code_input.setVisible(is_mfa)
        self.mfa_back_button.setVisible(is_mfa)
        self.mfa_verify_button.setVisible(is_mfa)
        self.login_button.setVisible(not is_mfa)
        self.login_button.setDefault(not is_mfa)
        self.mfa_verify_button.setDefault(is_mfa)
        self._set_authenticating(self._authenticating)

    def _set_authenticating(self, authenticating: bool) -> None:
        self._authenticating = bool(authenticating)
        enabled = not self._authenticating
        self.toggle_password_button.setEnabled(enabled and self._step == self._PASSWORD_STEP)
        self.login_button.setEnabled(enabled)
        self.mfa_back_button.setEnabled(enabled)
        self.mfa_verify_button.setEnabled(enabled)

    def _show_mfa_step(self) -> None:
        self.clear_validation_state()
        self._set_field_error(self.mfa_code_input, False)
        self.toggle_password_button.setChecked(False)
        self.password_input.setEchoMode(QLineEdit.Password)
        self._step = self._MFA_STEP
        self._apply_step()
        self.mfa_code_input.setFocus()

    def show_password_step(self, _checked=False) -> None:
        self.mfa_code_input.clear()
        self.clear_validation_state()
        self._set_field_error(self.mfa_code_input, False)
        self._step = self._PASSWORD_STEP
        self._apply_step()
        self.password_input.setFocus()

    def reject(self) -> None:
        self.show_password_step()
        super().reject()

    def _finish_login(self, username: str, api_token: str) -> None:
        self.api_token = api_token
        self.user = {"name": username, "email": username}
        storage_status = SessionManager().setSession(
            self.api_token,
            self.user,
            username=username,
        )
        self.password_input.clear()
        self.mfa_code_input.clear()
        SessionManager.show_storage_warning(
            storage_status,
            parent=self,
            lang_manager=self.lang,
        )
        self.loginSuccessful.emit(self.api_token, self.user)
        self.accept()

    def _classify_login_error(self, error: Exception) -> tuple[str, bool, bool]:
        """Trust the error's own kind first; only a server message is guessed at."""
        kind, text = parse_tagged_message(error)
        if kind in (ApiErrorKind.NETWORK, ApiErrorKind.SERVER):
            return self.lang.translate(TranslationKeys.LOGIN_SERVER_UNAVAILABLE), False, False
        # The client tags a rejected login as AUTH, and its text never says "invalid password".
        if kind == ApiErrorKind.AUTH:
            return self.lang.translate(TranslationKeys.LOGIN_CREDENTIALS_INVALID), True, True

        lowered = text.lower()
        if lowered.startswith("too many login attempts"):
            return self.lang.translate(TranslationKeys.LOGIN_TOO_MANY_ATTEMPTS), False, False
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
            "unauthenticated",
            "unauthorized",
        )

        if any(marker in lowered for marker in credential_markers):
            return self.lang.translate(TranslationKeys.LOGIN_CREDENTIALS_INVALID), True, True
        if any(marker in lowered for marker in username_markers):
            return self.lang.translate(TranslationKeys.LOGIN_USERNAME_INVALID), True, False
        if any(marker in lowered for marker in password_markers):
            return self.lang.translate(TranslationKeys.LOGIN_PASSWORD_INVALID), False, True
        return self.lang.translate(TranslationKeys.LOGIN_SERVER_UNAVAILABLE), False, False

    def authenticate_user(self):
        """Authenticate the user using the shared APIClient and show a concise server message on failure."""
        if self._authenticating:
            return
        self.clear_validation_state()

        username = self.username_input.text().strip()
        password = self.password_input.text()
        if not username:
            self._show_login_error(
                self.lang.translate(TranslationKeys.LOGIN_USERNAME_REQUIRED),
                username=True,
            )
            self.username_input.setFocus()
            return
        if not password:
            self._show_login_error(
                self.lang.translate(TranslationKeys.LOGIN_PASSWORD_REQUIRED),
                password=True,
            )
            self.password_input.setFocus()
            return

        # Only drop the old session once the attempt is actually going out.
        SessionManager.clear()
        self._set_authenticating(True)

        api = APIClient()
        try:
            graphql = GraphQLQueryLoader().load_query_by_module(
                Module.USER.value,
                "login.graphql",
            )
            variables = {
                "input": {
                    "username": username,
                    "password": password,
                }
            }
            # Use shared client for consistent headers and error handling; no auth required for login
            data = api.send_query(
                graphql,
                variables=variables,
                require_auth=False,
                timeout=10,
                retry_network=False,
                retry_rate_limits=False,
            )
            login_data = (data or {}).get("login") or {}
            api_token = login_data.get("accessToken")
            if api_token:
                self._finish_login(username, api_token)
            else:
                self._show_mfa_step()
        except Exception as e:
            msg, username_error, password_error = self._classify_login_error(e)
            self._show_login_error(
                msg,
                username=username_error,
                password=password_error,
            )
        finally:
            self._set_authenticating(False)

    @staticmethod
    def _normalize_mfa_code(value: str) -> str:
        return "".join((value or "").split()).upper()

    @staticmethod
    def _is_valid_mfa_code(value: str) -> bool:
        is_totp = len(value) == 6 and all(char in "0123456789" for char in value)
        is_recovery = len(value) == 8 and all(
            char in "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789" for char in value
        )
        return is_totp or is_recovery

    def verify_mfa_code(self):
        if self._authenticating or self._step != self._MFA_STEP:
            return
        self._clear_mfa_validation_state()

        code = self._normalize_mfa_code(self.mfa_code_input.text())
        if not code:
            self._show_mfa_error(
                self.lang.translate(TranslationKeys.MFA_CODE_REQUIRED),
                code=True,
            )
            self.mfa_code_input.setFocus()
            return
        if not self._is_valid_mfa_code(code):
            self._show_mfa_error(
                self.lang.translate(TranslationKeys.MFA_CODE_FORMAT),
                code=True,
            )
            self.mfa_code_input.setFocus()
            return

        username = self.username_input.text().strip()
        password = self.password_input.text()
        self._set_authenticating(True)

        try:
            graphql = GraphQLQueryLoader().load_query_by_module(
                Module.USER.value,
                "login_mfa.graphql",
            )
            data = APIClient().send_query(
                graphql,
                variables={
                    "input": {
                        "username": username,
                        "password": password,
                        "mfaCode": code,
                    }
                },
                require_auth=False,
                timeout=10,
                retry_network=False,
                retry_rate_limits=False,
            )
            login_data = (data or {}).get("login") or {}
            api_token = login_data.get("accessToken")
            if api_token:
                self._finish_login(username, api_token)
                return
            if login_data.get("requiresMfa") is True:
                self.mfa_code_input.clear()
                self._show_mfa_error(
                    self.lang.translate(TranslationKeys.MFA_CODE_INVALID),
                    code=True,
                )
                self.mfa_code_input.setFocus()
                return
            self._show_mfa_error(
                self.lang.translate(TranslationKeys.LOGIN_SERVER_UNAVAILABLE)
            )
        except Exception as e:
            msg, username_error, password_error = self._classify_login_error(e)
            if username_error or password_error:
                self.show_password_step()
                self._show_login_error(
                    msg,
                    username=username_error,
                    password=password_error,
                )
            else:
                self._show_mfa_error(msg)
        finally:
            self._set_authenticating(False)

