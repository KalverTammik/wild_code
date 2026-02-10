from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel
from ..languages.language_manager import LanguageManager
#import translation keys
from ..languages.translation_keys import TranslationKeys
from ..ui.mixins.token_mixin import TokenMixin


class WelcomePage(TokenMixin, QWidget):

    def __init__(self, lang_manager=None, parent=None):
        QWidget.__init__(self, parent)
        TokenMixin.__init__(self)
        self.setObjectName("WelcomePage")
        self.lang_manager = lang_manager or LanguageManager()

        # Build UI widgets and keep references for retranslation
        self.title_lbl = QLabel()
        self.title_lbl.setObjectName("WelcomeTitle")
        self.title_lbl.setText(self.lang_manager.translate(TranslationKeys.WELCOME))

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)
        layout.addStretch(1)
        layout.addWidget(self.title_lbl)
        layout.addStretch(2)

    def activate(self):
        """Activate the welcome page - no special logic needed."""
        pass

    def deactivate(self):
        """Deactivate the welcome page - no special logic needed."""
        pass

    def get_widget(self):
        """Return self as the widget for module system compatibility."""
        return self
