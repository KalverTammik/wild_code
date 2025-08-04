import os
import platform

from PyQt5.QtCore import pyqtSignal, Qt
from .widgets.FooterWidget import FooterWidget
from qgis.PyQt.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, QHBoxLayout, QComboBox
)
from qgis.PyQt.QtGui import QIcon
from qgis.core import Qgis

from .widgets.theme_manager import ThemeManager
from .constants.file_paths import ResourcePaths, QssPaths
from .languages.language_manager import LanguageManager
from .constants.DialogLabels import DialogLabels
from .utils.SessionManager import SessionManager
from .config.setup import Version

lang = LanguageManager(language="et")

class LoginDialog(QDialog):
    loginSuccessful = pyqtSignal(str)

    def __init__(
        self,
        title=DialogLabels.LOGIN_TITLE,
        username_label=DialogLabels.USERNAME_LABEL,
        password_label=DialogLabels.PASSWORD_LABEL,
        button_text=DialogLabels.LOGIN_BUTTON,
        theme_path=None,
        parent=None
    ):
        super().__init__(parent)
        self.api_token = None
        self.user = None
        self.setWindowTitle(title)
        self.setFixedSize(300, 400)


        # Apply the last stored theme (persistent, no switch button)
        theme_base_dir = os.path.join(os.path.dirname(__file__), 'styles')
        # Use login.qss if available, otherwise fallback to all qss
        ThemeManager.set_initial_theme(
            self,
            None,  # No switch button
            theme_base_dir,
            qss_files=[QssPaths.LOGIN]
        )

        layout = QVBoxLayout()

        self.language_label = QLabel(DialogLabels.LANGUAGE_LABEL)
        layout.addWidget(self.language_label)

        self.language_switch = QComboBox()
        self.language_switch.addItems(["et", "en", "fr"])
        self.language_switch.currentTextChanged.connect(self.change_language)
        layout.addWidget(self.language_switch)

        self.username_label = QLabel(username_label)
        self.username_label.setObjectName("usernameLabel")
        layout.addWidget(self.username_label)
        self.username_input = QLineEdit()
        self.username_input.setObjectName("usernameInput")
        layout.addWidget(self.username_input)

        self.password_label = QLabel(password_label)
        self.password_label.setObjectName("passwordLabel")
        layout.addWidget(self.password_label)
        password_row = QHBoxLayout()
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setObjectName("passwordInput")
        password_row.addWidget(self.password_input)
        self.toggle_password_button = QPushButton()
        self.toggle_password_button.setObjectName("togglePasswordButton")
        self.toggle_password_button.setIcon(QIcon(ResourcePaths.EYE_ICON))
        self.toggle_password_button.setCheckable(True)
        self.toggle_password_button.setText("")
        self.toggle_password_button.clicked.connect(self.toggle_password_visibility)
        password_row.addWidget(self.toggle_password_button, alignment=Qt.AlignRight)
        layout.addLayout(password_row)

        self.errorLabel = QLabel("")
        self.errorLabel.setStyleSheet("color: red;")
        self.errorLabel.hide()
        layout.addWidget(self.errorLabel)

        self.login_button = QPushButton(button_text)
        self.login_button.clicked.connect(self.try_login)
        layout.addWidget(self.login_button)

        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(self.login_button)
        layout.addLayout(button_layout)

        # Remove old footer_label QLabel
        # self.footer_label = QLabel(f"QGIS {qgis_version} | Plugin v{plugin_version}")
        # self.footer_label.setAlignment(Qt.AlignCenter)
        # self.footer_label.setObjectName("footerLabel")
        # layout.addWidget(self.footer_label)
        self.footer_widget = FooterWidget(show_left=False, show_right=True)
        layout.addWidget(self.footer_widget)

        self.toggle_password_button.setStyleSheet("")
        self.login_button.setStyleSheet("")

        self.setLayout(layout)

        self.setWindowTitle(DialogLabels.LOGIN_TITLE)
        self.language_label.setText(DialogLabels.LANGUAGE_LABEL)
        self.username_label.setText(DialogLabels.USERNAME_LABEL)
        self.password_label.setText(DialogLabels.PASSWORD_LABEL)
        self.login_button.setText(DialogLabels.LOGIN_BUTTON)


    def change_language(self, language):
        lang.set_language(language)
        lang.save_language_preference()
        self.setWindowTitle(DialogLabels.LOGIN_TITLE)
        self.language_label.setText(DialogLabels.LANGUAGE_LABEL)
        self.username_label.setText(DialogLabels.USERNAME_LABEL)
        self.password_label.setText(DialogLabels.PASSWORD_LABEL)
        self.login_button.setText(DialogLabels.LOGIN_BUTTON)

    def toggle_password_visibility(self):
        if self.toggle_password_button.isChecked():
            self.password_input.setEchoMode(QLineEdit.Normal)
        else:
            self.password_input.setEchoMode(QLineEdit.Password)

    def try_login(self):
        if SessionManager().isLoggedIn():
            self.errorLabel.setText(DialogLabels.SESSION_ACTIVE_ERROR)
            self.errorLabel.show()
            return

        if SessionManager.isSessionExpired():
            self.errorLabel.setText(DialogLabels.SESSION_EXPIRED_ERROR)
            self.errorLabel.show()
            return

        email = self.username_input.text()
        password = self.password_input.text()

        if email == "test@example.com" and password == "password123":
            self.api_token = "mock_api_token"
            self.user = {"name": "Test User", "email": email}
            SessionManager().setSession(self.api_token, self.user)
            self.loginSuccessful.emit(self.api_token)
            self.accept()
        else:
            self.errorLabel.setText(DialogLabels.INVALID_CREDENTIALS_ERROR)
            self.errorLabel.show()

