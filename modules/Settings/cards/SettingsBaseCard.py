from PyQt5.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
from ....languages.language_manager import LanguageManager
from ....widgets.theme_manager import ThemeManager
from ....constants.file_paths import QssPaths
from PyQt5.QtGui import  QPixmap
from ....languages.translation_keys import TranslationKeys

class SettingsBaseCard(QFrame):
    """Reusable SetupCard base with header, content area and confirm footer."""
    def __init__(self, lang_manager: LanguageManager, title_text: str, icon_path: str = None):
        super().__init__()
        self.lang_manager = lang_manager or LanguageManager()
        self.setObjectName("SetupCard")
        self.setFrameShape(QFrame.NoFrame)
        self._confirm_btn = None
        self._content = None
        self._build(title_text, icon_path)
        try:
            ThemeManager.apply_module_style(self, [QssPaths.SETUP_CARD])
        except Exception:
            pass

    def _build(self, title_text: str, icon_path: str = None):
        self.lay = QVBoxLayout(self)
        self.lay.setContentsMargins(10, 10, 10, 10)  # Slightly tighter margins
        self.lay.setSpacing(6)  # Reduced spacing
        
        # Header with separator frame
        header_frame = QFrame(self)
        header_frame.setObjectName("SetupCardHeader")
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(1, 1, 1, 1)
        
        if icon_path:
            icon_label = QLabel()
            icon_label.setPixmap(QPixmap(icon_path).scaled(18, 18))  # Smaller icons
            header_layout.addWidget(icon_label, 0)
            header_layout.addSpacing(6)

        title = QLabel(title_text)
        title.setObjectName("SetupCardTitle")
        header_layout.addWidget(title, 0)
        header_layout.addStretch(1)
        self.lay.addWidget(header_frame)
        
        # Content
        self._content = QFrame(self)
        self._content.setObjectName("SetupCardContent")
        self.lay.addWidget(self._content)
        # Footer with improved layout
        footer = self._build_footer()
        self.lay.addLayout(footer)

    def retheme(self):
        ThemeManager.apply_module_style(self, [QssPaths.SETUP_CARD])


    def _build_footer(self):
        """Build flexible footer area for confirm button and status display."""
        ftr = QHBoxLayout()
        ftr.setContentsMargins(0, 6, 0, 0)
        ftr.setSpacing(8)

        # Left side - status/info area (can be used by subclasses)
        self._footer_left = QFrame(self)
        self._footer_left.setObjectName("SetupCardFooterLeft")
        self._footer_left.setVisible(False)  # Hidden by default
        footer_left_layout = QVBoxLayout(self._footer_left)
        footer_left_layout.setContentsMargins(0, 0, 0, 0)
        footer_left_layout.setSpacing(2)

        self._status_label = QLabel("", self)
        self._status_label.setObjectName("SetupCardStatus")
        self._status_label.setWordWrap(True)
        footer_left_layout.addWidget(self._status_label)

        ftr.addWidget(self._footer_left, 1)  # Expands to fill space

        # Right side - buttons
        buttons_frame = QFrame(self)
        buttons_frame.setObjectName("SetupCardFooterRight")
        buttons_layout = QHBoxLayout(buttons_frame)
        buttons_layout.setContentsMargins(0, 0, 0, 0)
        buttons_layout.setSpacing(6)
        buttons_layout.addStretch(1)

        # Reset button (can be shown/hidden by subclasses)
        self._reset_btn = QPushButton(self.lang_manager.translate(TranslationKeys.RESET))
        self._reset_btn.setObjectName("ResetButton")
        self._reset_btn.setVisible(False)  # Hidden by default
        buttons_layout.addWidget(self._reset_btn)

        # Confirm button
        self._confirm_btn = QPushButton(self.lang_manager.translate(TranslationKeys.CONFIRM))
        self._confirm_btn.setVisible(False)
        self._confirm_btn.setObjectName("ConfirmButton")  # For QSS styling
        buttons_layout.addWidget(self._confirm_btn)

        ftr.addWidget(buttons_frame, 0)  # No expansion
        return ftr

    def content_widget(self) -> QFrame:
        return self._content

    def confirm_button(self) -> QPushButton:
        return self._confirm_btn

    def reset_button(self) -> QPushButton:
        return self._reset_btn

    def set_status_text(self, text: str, visible: bool = True):
        """Set status text in footer area."""
        self._status_label.setText(text)
        self._footer_left.setVisible(visible and bool(text))

    def clear_status(self):
        """Clear status text and hide footer left area."""
        self._status_label.setText("")
        self._footer_left.setVisible(False)

