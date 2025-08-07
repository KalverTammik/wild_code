from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton, QSizePolicy
from PyQt5.QtCore import Qt

class HeaderWidget(QWidget):
    def __init__(self, title, switch_callback, logout_callback, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout()
        layout.setContentsMargins(10, 6, 10, 6)
        layout.setSpacing(10)


        self.titleLabel = QLabel(title)
        self.titleLabel.setObjectName("headerTitleLabel")
        self.titleLabel.setFixedWidth(180)  # Fixed width for consistent layout
        self.titleLabel.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)
        layout.addWidget(self.titleLabel, 0, Qt.AlignLeft | Qt.AlignVCenter)

        # Search widget (centered, no functionality yet)
        from PyQt5.QtWidgets import QLineEdit
        self.searchEdit = QLineEdit()
        self.searchEdit.setPlaceholderText("Search...")
        self.searchEdit.setObjectName("headerSearchEdit")
        self.searchEdit.setFixedWidth(220)
        layout.addWidget(self.searchEdit, 1, Qt.AlignHCenter | Qt.AlignVCenter)

        self.switchButton = QPushButton()
        self.switchButton.setObjectName("themeSwitchButton")
        self.switchButton.clicked.connect(switch_callback)
        layout.addWidget(self.switchButton, 0, Qt.AlignRight | Qt.AlignVCenter)

        self.logoutButton = QPushButton("Logout")
        self.logoutButton.setObjectName("logoutButton")
        self.logoutButton.clicked.connect(logout_callback)
        layout.addWidget(self.logoutButton, 0, Qt.AlignRight | Qt.AlignVCenter)

        self.setLayout(layout)


    def set_switch_icon(self, icon):
        self.switchButton.setIcon(icon)
        self.switchButton.setText("")
    def set_logout_icon(self, icon):
        self.logoutButton.setIcon(icon)
        self.logoutButton.setText("")

    def set_title(self, text):
        self.titleLabel.setText(text)
