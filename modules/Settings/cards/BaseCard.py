from PyQt5.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
from ....languages.language_manager import LanguageManager
from ....widgets.theme_manager import ThemeManager
from ....constants.file_paths import QssPaths

class BaseCard(QFrame):
    """Reusable SetupCard base with header, content area and confirm footer."""
    def __init__(self, lang_manager: LanguageManager, title_text: str):
        super().__init__()
        self.lang_manager = lang_manager or LanguageManager()
        self.setObjectName("SetupCard")
        self.setFrameShape(QFrame.NoFrame)
        self._confirm_btn = None
        self._content = None
        self._build(title_text)
        try:
            ThemeManager.apply_module_style(self, [QssPaths.SETUP_CARD])
        except Exception:
            pass

    def _build(self, title_text: str):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(16, 16, 16, 16)
        lay.setSpacing(10)
        # Header
        hdr = QHBoxLayout(); hdr.setContentsMargins(0,0,0,0)
        title = QLabel(title_text)
        title.setObjectName("SetupCardTitle")
        hdr.addWidget(title, 0)
        hdr.addStretch(1)
        lay.addLayout(hdr)
        # Content
        self._content = QFrame(self)
        self._content.setObjectName("SetupCardContent")
        lay.addWidget(self._content)
        # Footer
        ftr = QHBoxLayout(); ftr.setContentsMargins(0,6,0,0)
        ftr.addStretch(1)
        self._confirm_btn = QPushButton(self.lang_manager.translate("Confirm"))
        self._confirm_btn.setEnabled(False)
        self._confirm_btn.setVisible(False)
        ftr.addWidget(self._confirm_btn)
        lay.addLayout(ftr)

    def content_widget(self) -> QFrame:
        return self._content

    def confirm_button(self) -> QPushButton:
        return self._confirm_btn

    def retheme(self):
        try:
            ThemeManager.apply_module_style(self, [QssPaths.SETUP_CARD])
        except Exception:
            pass
