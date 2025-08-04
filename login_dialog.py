import os
import platform

from PyQt5.QtCore import pyqtSignal
from qgis.PyQt.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, QHBoxLayout, QComboBox
)
from qgis.PyQt.QtGui import QIcon

from .widgets.theme_manager import ThemeManager
from .constants.file_paths import FilePaths
from .languages.language_manager import LanguageManager
from .constants.DialogLabels import DialogLabels
from .utils.SessionManager import SessionManager

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

        theme_path = FilePaths.get_file_path(FilePaths.LOGIN_DIALOG)
        print(f"Applying theme for login dialog: {theme_path}")
        if theme_path:
            ThemeManager.apply_theme(self, theme_path)

        layout = QVBoxLayout()

        self.language_label = QLabel(DialogLabels.LANGUAGE_LABEL)
        layout.addWidget(self.language_label)

        self.language_switch = QComboBox()
        self.language_switch.addItems(["et", "en", "fr"])
        self.language_switch.currentTextChanged.connect(self.change_language)
        layout.addWidget(self.language_switch)

        self.username_label = QLabel(username_label)
        layout.addWidget(self.username_label)
        self.username_input = QLineEdit()
        layout.addWidget(self.username_input)

        password_label_layout = QHBoxLayout()
        self.password_label = QLabel(password_label)
        password_label_layout.addWidget(self.password_label)

        self.toggle_password_button = QPushButton()
        self.toggle_password_button.setObjectName("togglePasswordButton")
        self.toggle_password_button.setIcon(QIcon(FilePaths.get_file_path(FilePaths.EYE_ICON)))
        self.toggle_password_button.setCheckable(True)
        self.toggle_password_button.setText("")
        self.toggle_password_button.clicked.connect(self.toggle_password_visibility)
        password_label_layout.addWidget(self.toggle_password_button)

        layout.addLayout(password_label_layout)

        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        layout.addWidget(self.password_input)

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

