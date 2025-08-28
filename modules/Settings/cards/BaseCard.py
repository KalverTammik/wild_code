from PyQt5.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
from ....languages.language_manager import LanguageManager
from ....widgets.theme_manager import ThemeManager
from ....constants.file_paths import QssPaths

class BaseCard(QFrame):
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
        lay = QVBoxLayout(self)
        lay.setContentsMargins(10, 10, 10, 10)  # Slightly tighter margins
        lay.setSpacing(6)  # Reduced spacing
        
        # Header with separator frame
        header_frame = QFrame(self)
        header_frame.setObjectName("SetupCardHeader")
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(1, 1, 1, 1)
        
        if icon_path:
            try:
                from PyQt5.QtGui import QIcon, QPixmap
                icon_label = QLabel()
                icon_label.setPixmap(QPixmap(icon_path).scaled(18, 18))  # Smaller icons
                header_layout.addWidget(icon_label, 0)
                header_layout.addSpacing(6)
            except Exception:
                pass
        title = QLabel(title_text)
        title.setObjectName("SetupCardTitle")
        header_layout.addWidget(title, 0)
        header_layout.addStretch(1)
        lay.addWidget(header_frame)
        
        # Content
        self._content = QFrame(self)
        self._content.setObjectName("SetupCardContent")
        lay.addWidget(self._content)
        # Footer with improved layout
        self._build_footer(lay)

    def _build_footer(self, parent_layout):
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

        # Right side - confirm button
        self._confirm_btn = QPushButton(self.lang_manager.translate("Confirm"))
        self._confirm_btn.setEnabled(False)
        self._confirm_btn.setVisible(False)
        self._confirm_btn.setObjectName("ConfirmButton")  # For QSS styling
        ftr.addWidget(self._confirm_btn, 0)  # No expansion

        parent_layout.addLayout(ftr)

    def content_widget(self) -> QFrame:
        return self._content

    def confirm_button(self) -> QPushButton:
        return self._confirm_btn

    def set_status_text(self, text: str, visible: bool = True):
        """Set status text in footer area."""
        self._status_label.setText(text)
        self._footer_left.setVisible(visible and bool(text))

    def clear_status(self):
        """Clear status text and hide footer left area."""
        self._status_label.setText("")
        self._footer_left.setVisible(False)

    def retheme(self):
        try:
            ThemeManager.apply_module_style(self, [QssPaths.SETUP_CARD])
        except Exception:
            pass
