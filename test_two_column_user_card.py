#!/usr/bin/env python3
"""
Test script to demonstrate the improved UserCard with two-column layout
"""
import sys
from PyQt5.QtWidgets import (
    QApplication, QVBoxLayout, QWidget, QLabel, QFrame, QHBoxLayout,
    QCheckBox, QPushButton
)
from PyQt5.QtCore import Qt, pyqtSignal
from languages.language_manager import LanguageManager

class ImprovedUserCard(QFrame):
    """Improved UserCard with two-column layout and integrated roles/permissions"""

    preferredChanged = pyqtSignal(object)

    def __init__(self):
        super().__init__()
        self._lang = LanguageManager()
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
            QLabel#UserRolesLabel {
                font-size: 12px;
                color: #005a9e;
                font-weight: 500;
            }
            QLabel#UserRoles {
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
        title = QLabel(self._lang.translate("User Profile"))
        title.setObjectName("SetupCardTitle")
        layout.addWidget(title)

        # IMPROVED: User Info Card with two-column layout
        user_info_card = QFrame(self)
        user_info_card.setObjectName("UserInfoCard")

        # Two-column layout for user info
        user_info_main_layout = QHBoxLayout(user_info_card)
        user_info_main_layout.setContentsMargins(10, 8, 10, 8)
        user_info_main_layout.setSpacing(20)  # Space between columns

        # Left column: Basic user info
        left_column = QVBoxLayout()
        left_column.setSpacing(4)

        # Name prominently displayed
        self.lbl_name = QLabel("John Doe")
        self.lbl_name.setObjectName("UserName")
        left_column.addWidget(self.lbl_name)

        # Email below name
        self.lbl_email = QLabel("john.doe@example.com")
        self.lbl_email.setObjectName("UserEmail")
        left_column.addWidget(self.lbl_email)

        left_column.addStretch(1)  # Push content to top
        user_info_main_layout.addLayout(left_column)

        # Right column: Roles
        right_column = QVBoxLayout()
        right_column.setSpacing(4)

        # Roles label
        roles_label = QLabel(self._lang.translate("Roles"))
        roles_label.setObjectName("UserRolesLabel")
        right_column.addWidget(roles_label)

        # Roles value (separate line)
        self.lbl_roles = QLabel("Administrator, Editor")
        self.lbl_roles.setObjectName("UserRoles")
        right_column.addWidget(self.lbl_roles)

        right_column.addStretch(1)  # Push content to top
        user_info_main_layout.addLayout(right_column)

        layout.addWidget(user_info_card)

        # Module access - separate section
        access_title = QLabel(self._lang.translate("Preferred module"))
        access_title.setObjectName("SetupCardSectionTitle")
        layout.addWidget(access_title)

        access_container = QFrame(self)
        access_layout = QHBoxLayout(access_container)
        access_layout.setContentsMargins(0, 0, 0, 0)
        access_layout.setSpacing(8)

        modules = [(self._lang.translate("Dashboard"), True), (self._lang.translate("Reports"), True), (self._lang.translate("Settings"), False), (self._lang.translate("Admin"), True)]
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

        confirm_btn = QPushButton(self._lang.translate("Confirm"))
        confirm_btn.setEnabled(False)
        footer_layout.addWidget(confirm_btn)

        layout.addLayout(footer_layout)

class TestWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Improved UserCard - Two Column Layout")
        self.setGeometry(100, 100, 700, 500)

        layout = QVBoxLayout(self)
        layout.setSpacing(20)

        # Improved layout
        improved_label = QLabel("IMPROVED USER CARD - TWO COLUMN LAYOUT")
        improved_label.setStyleSheet("font-weight: bold; color: green; font-size: 14px;")
        layout.addWidget(improved_label)

        improved_card = ImprovedUserCard()
        layout.addWidget(improved_card)

        improvements_label = QLabel(
            "✓ Two-column layout within user info card\n"
            "✓ Roles displayed on separate line below label\n"
            "✓ Consistent styling with email format\n"
            "✓ Better information hierarchy\n"
            "✓ Updated terminology: 'Preferred module' instead of 'Module access'"
        )
        improvements_label.setWordWrap(True)
        improvements_label.setStyleSheet("color: green; font-size: 11px; padding: 10px; background: #d4edda; border-radius: 4px;")
        layout.addWidget(improvements_label)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TestWindow()
    window.show()
    sys.exit(app.exec_())
