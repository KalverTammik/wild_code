from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QHBoxLayout


class WelcomePage(QWidget):
    """
    Simple welcome screen shown when no preferred module is set.
    Offers a friendly intro and a button to open Settings to choose a preferred module.
    Supports runtime retranslation via retranslate().
    """

    openSettingsRequested = pyqtSignal()

    def __init__(self, lang_manager=None, theme_manager=None, parent=None):
        super().__init__(parent)
        self.setObjectName("WelcomePage")
        self.lang_manager = lang_manager

        # Build UI widgets and keep references for retranslation
        self.title_lbl = QLabel()
        self.title_lbl.setObjectName("WelcomeTitle")
        self.subtitle_lbl = QLabel()
        self.subtitle_lbl.setObjectName("WelcomeSubtitle")
        self.subtitle_lbl.setWordWrap(True)
        self.open_btn = QPushButton()
        self.open_btn.clicked.connect(self.openSettingsRequested.emit)
        self.open_btn.setObjectName("WelcomeOpenSettingsButton")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)
        layout.addStretch(1)
        layout.addWidget(self.title_lbl)
        layout.addWidget(self.subtitle_lbl)
        hl = QHBoxLayout()
        hl.addWidget(self.open_btn)
        hl.addStretch(1)
        layout.addLayout(hl)
        layout.addStretch(2)

        # Initial text setup
        self.retranslate(self.lang_manager)
        # Theme is applied at dialog level; child inherits. Optionally apply module QSS here if needed.
        # if theme_manager:
        #     try:
        #         from ..constants.file_paths import QssPaths
        #         theme_manager.apply_module_style(self, [QssPaths.MAIN])
        #     except Exception:
        #         pass

    # Public API ------------------------------------------------------
    def retranslate(self, lang_manager=None):
        if lang_manager is not None:
            self.lang_manager = lang_manager
        lm = self.lang_manager
        if lm:
            self.title_lbl.setText(lm.translate("Welcome"))
            self.subtitle_lbl.setText(lm.translate("Select a module from the left or open Settings to set your preferred module."))
            self.open_btn.setText(lm.translate("Open Settings"))
        else:
            self.title_lbl.setText("Welcome")
            self.subtitle_lbl.setText("Select a module from the left or open Settings to set your preferred module.")
            self.open_btn.setText("Open Settings")
