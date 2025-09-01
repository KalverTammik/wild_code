import os
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton, QSizePolicy, QFrame, QLineEdit
from PyQt5.QtCore import Qt, pyqtSignal, QSize
from PyQt5.QtWidgets import QGraphicsDropShadowEffect
from PyQt5.QtGui import QColor, QIcon

class HeaderWidget(QWidget):
    """
    This widget supports dynamic theme switching via ThemeManager.apply_module_style.
    Call retheme_header() to re-apply QSS after a theme change.
    """
    helpRequested = pyqtSignal()
    
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
        frame_layout.setSpacing(5)
        frame_layout.addWidget(self.titleLabel)
        
        # Help button next to title
        self.helpButton = QPushButton()
        self.helpButton.setObjectName("headerHelpButton")
        self.helpButton.setFixedSize(50, 24)
        # Add help icon and text
        try:
            from ..constants.module_icons import ModuleIconPaths, ICON_HELP
            help_icon_path = ModuleIconPaths.themed(ICON_HELP)
            if help_icon_path:
                self.helpButton.setIcon(QIcon(help_icon_path))
                self.helpButton.setIconSize(QSize(18, 18))
                self.helpButton.setText(" Abi")
            else:
                self.helpButton.setText("Abi")
        except Exception:
            self.helpButton.setText("Abi")
        
        # Add tooltip
        try:
            from wild_code.languages.language_manager import LanguageManager
            lang_manager = LanguageManager()
            tooltip = lang_manager.translations.get("help_button_tooltip", "")
            if tooltip:
                self.helpButton.setToolTip(tooltip)
        except Exception:
            pass
        
        self.helpButton.clicked.connect(self._emit_help)
        frame_layout.addWidget(self.helpButton)
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
        
        # Right: Dev controls + theme switch + logout
        # Optional callbacks set by parent controller
        self.on_toggle_debug = None
        self.on_toggle_frame_labels = None

        # Dev controls extracted into dedicated widget
        from .DevControlsWidget import DevControlsWidget
        self.devControls = DevControlsWidget()
        self.devControls.toggleDebugRequested.connect(self._emit_debug_toggle)
        self.devControls.toggleFrameLabelsRequested.connect(self._emit_frame_labels_toggle)
        layout.addWidget(self.devControls, 0, Qt.AlignRight | Qt.AlignVCenter)

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
        # Ensure DevControls' own QSS is applied last so its specific rules override header's generic QPushButton
        try:
            self.devControls.retheme()
        except Exception:
            pass


    def _emit_debug_toggle(self, enabled: bool):
        cb = getattr(self, 'on_toggle_debug', None)
        if callable(cb):
            try:
                cb(bool(enabled))
            except Exception:
                pass

    def _emit_frame_labels_toggle(self, enabled: bool):
        cb = getattr(self, 'on_toggle_frame_labels', None)
        if callable(cb):
            try:
                cb(bool(enabled))
            except Exception:
                pass

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
        try:
            self.devControls.retheme()
        except Exception:
            pass

    def set_title(self, text):
        self.titleLabel.setText(text)

    def _open_home(self):
        pass  # home nupp eemaldatud (kasuta külgriba Avaleht nuppu)
        # Emit a custom signal or call a callback to open the welcome page
        if hasattr(self, 'open_home_callback') and callable(self.open_home_callback):
            self.open_home_callback()

    def set_dev_states(self, debug_enabled: bool, frames_enabled: bool):
        """Initialize or update the dev controls' checked states."""
        try:
            self.devControls.set_states(bool(debug_enabled), bool(frames_enabled))
        except Exception:
            pass

    def _emit_help(self):
        """Emit help requested signal."""
        self.helpRequested.emit()
