#!/usr/bin/env python3
"""
Final test script to demonstrate the improved UserCard layout
"""
import sys
from PyQt5.QtWidgets import (
    QApplication, QVBoxLayout, QWidget, QLabel, QFrame, QHBoxLayout,
    QCheckBox, QPushButton
)
from PyQt5.QtCore import Qt, pyqtSignal

class ImprovedUserCard(QFrame):
    """Improved UserCard with better layout - no user ID, better organization"""

    preferredChanged = pyqtSignal(object)

    def __init__(self):
        super().__init__()
        self.setObjectName("SetupCard")
        self.setFrameShape(QFrame.NoFrame)
        self.setStyleSheet("""
            QFrame#SetupCard {
                background: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 8px;
                padding: 10px;
            }
            QLabel#SetupCardTitle {
                font-weight: bold;
                font-size: 14px;
                color: #495057;
            }
            QLabel#SetupCardSectionTitle {
                font-weight: bold;
                font-size: 12px;
                color: #007bff;
                margin-top: 8px;
            }
            QFrame#UserInfoCard {
                background: white;
                border: 1px solid #e9ecef;
                border-radius: 6px;
                padding: 8px;
                margin: 4px 0;
            }
            QLabel#UserName {
                font-size: 16px;
                font-weight: bold;
                color: #212529;
            }
            QLabel#UserEmail {
                font-size: 12px;
                color: #6c757d;
            }
            QFrame#AccessPill {
                background: #e9ecef;
                border: 1px solid #ced4da;
                border-radius: 20px;
                padding: 4px 12px;
                margin: 2px;
            }
            QFrame#AccessPill[active="true"] {
                background: #d1ecf1;
                border-color: #bee5eb;
            }
        """)

        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        # Header
        title = QLabel("User Profile")
        title.setObjectName("SetupCardTitle")
        layout.addWidget(title)

        # IMPROVED: User Info Card - No ID shown, better organized
        user_info_card = QFrame(self)
        user_info_card.setObjectName("UserInfoCard")

        info_layout = QVBoxLayout(user_info_card)
        info_layout.setContentsMargins(10, 8, 10, 8)
        info_layout.setSpacing(4)

        # Name prominently displayed
        name_label = QLabel("John Doe")
        name_label.setObjectName("UserName")
        info_layout.addWidget(name_label)

        # Email below name
        email_label = QLabel("john.doe@example.com")
        email_label.setObjectName("UserEmail")
        info_layout.addWidget(email_label)

        layout.addWidget(user_info_card)

        # Roles section - better spacing
        roles_title = QLabel("Roles & Permissions")
        roles_title.setObjectName("SetupCardSectionTitle")
        layout.addWidget(roles_title)

        roles_container = QFrame(self)
        roles_layout = QHBoxLayout(roles_container)
        roles_layout.setContentsMargins(0, 0, 0, 0)
        roles_layout.setSpacing(8)

        for role in ["Administrator", "Editor", "Viewer"]:
            pill = QFrame(roles_container)
            pill.setObjectName("AccessPill")
            pill.setProperty("active", True)

            pill_layout = QHBoxLayout(pill)
            pill_layout.setContentsMargins(8, 2, 8, 2)
            pill_layout.setSpacing(4)

            lbl = QLabel(role, pill)
            pill_layout.addWidget(lbl)
            roles_layout.addWidget(pill)

        roles_layout.addStretch(1)
        layout.addWidget(roles_container)

        # Module access - better organized
        access_title = QLabel("Module Access")
        access_title.setObjectName("SetupCardSectionTitle")
        layout.addWidget(access_title)

        access_container = QFrame(self)
        access_layout = QHBoxLayout(access_container)
        access_layout.setContentsMargins(0, 0, 0, 0)
        access_layout.setSpacing(8)

        modules = [("Dashboard", True), ("Reports", True), ("Settings", False), ("Admin", True)]
        for module_name, has_access in modules:
            pill = QFrame(access_container)
            pill.setObjectName("AccessPill")
            pill.setProperty("active", has_access)

            pill_layout = QHBoxLayout(pill)
            pill_layout.setContentsMargins(8, 2, 8, 2)
            pill_layout.setSpacing(6)

            chk = QCheckBox(pill)
            chk.setEnabled(has_access)
            chk.setProperty("moduleName", module_name.lower())

            txt = QLabel(module_name, pill)
            if not has_access:
                font = txt.font()
                font.setStrikeOut(True)
                txt.setFont(font)

            pill_layout.addWidget(chk, 0)
            pill_layout.addWidget(txt, 0)
            pill_layout.addStretch(1)

            access_layout.addWidget(pill)

        access_layout.addStretch(1)
        layout.addWidget(access_container)

        # Footer
        footer_layout = QHBoxLayout()
        footer_layout.addStretch(1)

        confirm_btn = QPushButton("Confirm")
        confirm_btn.setEnabled(False)
        footer_layout.addWidget(confirm_btn)

        layout.addLayout(footer_layout)

class TestWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Improved UserCard Layout")
        self.setGeometry(100, 100, 600, 500)

        layout = QVBoxLayout(self)
        layout.setSpacing(20)

        # Improved layout
        improved_label = QLabel("IMPROVED USER CARD LAYOUT")
        improved_label.setStyleSheet("font-weight: bold; color: green; font-size: 14px;")
        layout.addWidget(improved_label)

        improved_card = ImprovedUserCard()
        layout.addWidget(improved_card)

        improvements_label = QLabel(
            "✓ No User ID displayed (makes no sense to users)\n"
            "✓ Better visual hierarchy with user info card\n"
            "✓ Cleaner organization of information\n"
            "✓ Improved spacing and padding\n"
            "✓ Consistent pill styling"
        )
        improvements_label.setWordWrap(True)
        improvements_label.setStyleSheet("color: green; font-size: 11px; padding: 10px; background: #d4edda; border-radius: 4px;")
        layout.addWidget(improvements_label)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TestWindow()
    window.show()
    sys.exit(app.exec_())
