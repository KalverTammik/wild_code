
import os


from PyQt5.QtCore import pyqtSignal, Qt
from .widgets.FooterWidget import FooterWidget
from qgis.PyQt.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, QHBoxLayout, QComboBox
)
from qgis.PyQt.QtGui import QIcon

from .widgets.theme_manager import ThemeManager, Theme, is_dark
from .constants.file_paths import ResourcePaths, QssPaths
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
        title=LanguageManager().translate(DialogLabels.LOGIN_TITLE),
        username_label=LanguageManager().translate(DialogLabels.USERNAME_LABEL),
        password_label=LanguageManager().translate(DialogLabels.PASSWORD_LABEL),
        button_text=LanguageManager().translate(DialogLabels.LOGIN_BUTTON),
        theme_path=None,
        parent=None
    ):
        super().__init__(parent)
        self.api_token = None
        self.user = None
        self.setWindowTitle(title)
        self.setFixedSize(300, 400)


        ThemeManager.set_initial_theme(
            self,
            None,  # No switch button

            qss_files=[QssPaths.MAIN, QssPaths.LOGIN]
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
        layout.addWidget(self.username_input)

        self.password_label = QLabel(password_label)
        self.password_label.setObjectName(DialogLabels.PASSWORD_LABEL)
        layout.addWidget(self.password_label)
        password_row = QHBoxLayout()
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setObjectName("passwordInput")
        password_row.addWidget(self.password_input)
        self.toggle_password_button = QPushButton()
        self.toggle_password_button.setObjectName("togglePasswordButton")
        self.toggle_password_button.setIcon(ThemeManager.get_qicon(ResourcePaths.EYE_ICON))
        self.toggle_password_button.setCheckable(True)
        self.toggle_password_button.setText("")
        self.toggle_password_button.clicked.connect(self.toggle_password_visibility)
        password_row.addWidget(self.toggle_password_button, alignment=Qt.AlignRight)
        layout.addLayout(password_row)

        self.errorLabel = QLabel("")
        self.errorLabel.setObjectName(TranslationKeys.ERROR)
        self.errorLabel.hide()
        layout.addWidget(self.errorLabel)


        self.login_button = QPushButton(button_text)
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
        self.setWindowTitle(LanguageManager().translate(DialogLabels.LOGIN_TITLE))
        self.language_label.setText(LanguageManager().translate(DialogLabels.LANGUAGE_LABEL))
        self.username_label.setText(LanguageManager().translate(DialogLabels.USERNAME_LABEL))
        self.password_label.setText(LanguageManager().translate(DialogLabels.PASSWORD_LABEL))
        self.login_button.setText(LanguageManager().translate(DialogLabels.LOGIN_BUTTON))

    def toggle_password_visibility(self):
        if self.toggle_password_button.isChecked():
            self.password_input.setEchoMode(QLineEdit.Normal)
        else:
            self.password_input.setEchoMode(QLineEdit.Password)

    def authenticate_user(self):
        """Authenticate the user using the shared APIClient and show a concise server message on failure."""

        # Always clear any existing session before attempting new login
        # This ensures clean state regardless of previous login status
        print("[DEBUG] Clearing any existing session before login")
        SessionManager.clear()

        username = self.username_input.text()
        password = self.password_input.text()

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
                #print(f"[DEBUG] Login successful - setting session with token: {api_token[:10]}...")
                SessionManager().setSession(self.api_token, self.user)
                SessionManager().save_credentials(username, password, api_token)
                #print("[DEBUG] About to emit loginSuccessful signal")
                self.loginSuccessful.emit(self.api_token, self.user)
                #print("[DEBUG] loginSuccessful signal emitted")
                self.close()  # Close the dialog
                #print("[DEBUG] Dialog closed")
            else:
                # One-shot diagnostic: show server-side response issue
                self.errorLabel.setText(lang.translate(TranslationKeys.NO_API_TOKEN_RECEIVED))
                self.errorLabel.show()
        except Exception as e:
            # Clear session on any login failure to allow retry
            SessionManager.clear()
            # One-shot diagnostic: surface the server's message body without logging secrets
            msg = str(e)
            if not msg:
                msg = lang.translate(TranslationKeys.LOGIN_FAILED)
            self.errorLabel.setText(msg)
            self.errorLabel.show()

