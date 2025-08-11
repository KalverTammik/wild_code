from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton, QSizePolicy, QFrame, QLineEdit
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QGraphicsDropShadowEffect
from PyQt5.QtGui import QColor

class HeaderWidget(QWidget):
    """
    This widget supports dynamic theme switching via ThemeManager.apply_module_style.
    Call retheme_header() to re-apply QSS after a theme change.
    """
    def __init__(self, title, switch_callback, logout_callback, parent=None, compact=False):
        super().__init__(parent)



        # Outer frame (lets us draw the bottom glow/separator via QSS)
        frame = QFrame(self)
        frame.setObjectName("headerWidgetFrame")

        layout = QHBoxLayout(frame)
        layout.setContentsMargins(10, 6 if not compact else 4, 10, 6 if not compact else 4)
        layout.setSpacing(10)

        # Title (fixed width is okay if you want consistent center balance)
        self.titleLabel = QLabel(title)
        self.titleLabel.setObjectName("headerTitleLabel")
        self.titleLabel.setFixedWidth(180)
        self.titleLabel.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)
        self.titleFrame = QFrame()
        self.titleFrame.setObjectName("headerTitleFrame")
        frame_layout = QHBoxLayout(self.titleFrame)
        frame_layout.setContentsMargins(8, 2, 8, 2)
        frame_layout.setSpacing(0)
        frame_layout.addWidget(self.titleLabel)
        layout.addWidget(self.titleFrame, 0, Qt.AlignLeft | Qt.AlignVCenter)

        # Search (center)
        self.searchEdit = QLineEdit()
        try:
            from wild_code.languages.language_manager import LanguageManager
            lang_manager = LanguageManager()
            placeholder = lang_manager.translations.get("search_placeholder", "search_placeholder")
            self.searchEdit.setPlaceholderText(placeholder)
        except Exception:
            self.searchEdit.setPlaceholderText("search_placeholder")
        self.searchEdit.setObjectName("headerSearchEdit")
        self.searchEdit.setFixedWidth(220)
        shadow = QGraphicsDropShadowEffect(self.searchEdit)
        shadow.setBlurRadius(14)                  # softer spread
        shadow.setXOffset(0)
        shadow.setYOffset(1)
        shadow.setColor(QColor(9, 144, 143, 60))   # teal accent glow (rgb, alpha)
        self.searchEdit.setGraphicsEffect(shadow)
        # Rakenda tooltip keelefailist
        try:
            from wild_code.languages.language_manager import LanguageManager
            lang_manager = LanguageManager()
            tooltip = lang_manager.translations.get("search_tooltip", "search_tooltip")
            self.searchEdit.setToolTip(tooltip)
        except Exception:
            self.searchEdit.setToolTip("search_tooltip")
        layout.addWidget(self.searchEdit, 1, Qt.AlignHCenter | Qt.AlignVCenter)
        
        # Right: theme switch + logout
        self.switchButton = QPushButton()
        self.switchButton.setObjectName("themeSwitchButton")
        self.switchButton.clicked.connect(switch_callback)
        # Rakenda tooltip keelefailist
        try:
            from wild_code.languages.language_manager import LanguageManager
            lang_manager = LanguageManager()
            tooltip = lang_manager.translations.get("theme_switch_tooltip", "theme_switch_tooltip")
            self.switchButton.setToolTip(tooltip)
        except Exception:
            self.switchButton.setToolTip("theme_switch_tooltip")
        layout.addWidget(self.switchButton, 0, Qt.AlignRight | Qt.AlignVCenter)

        self.logoutButton = QPushButton("Logout")
        self.logoutButton.setObjectName("logoutButton")
        self.logoutButton.clicked.connect(logout_callback)
        # Rakenda tooltip keelefailist
        try:
            from wild_code.languages.language_manager import LanguageManager
            lang_manager = LanguageManager()
            tooltip = lang_manager.translations.get("logout_button_tooltip", "logout_button_tooltip")
            self.logoutButton.setToolTip(tooltip)
        except Exception:
            self.logoutButton.setToolTip("logout_button_tooltip")
        layout.addWidget(self.logoutButton, 0, Qt.AlignRight | Qt.AlignVCenter)

        # Outer zero-margin wrapper (consistent with footer structure)
        outer = QHBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(frame)

        # Apply theme (main + header)
        from .theme_manager import ThemeManager
        from ..constants.file_paths import QssPaths
        ThemeManager.apply_module_style(self, [QssPaths.MAIN, QssPaths.HEADER])

    def set_switch_icon(self, icon):
        self.switchButton.setIcon(icon)
        self.switchButton.setText("")

    def set_logout_icon(self, icon):
        self.logoutButton.setIcon(icon)
        self.logoutButton.setText("")

    def retheme_header(self):
        from .theme_manager import ThemeManager
        from ..constants.file_paths import QssPaths
        ThemeManager.apply_module_style(self, [QssPaths.MAIN, QssPaths.HEADER])

    def set_title(self, text):
        self.titleLabel.setText(text)
