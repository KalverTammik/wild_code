from qgis.PyQt.QtWidgets import QWidget, QVBoxLayout, QFrame, QScrollArea
from ..languages.language_manager import LanguageManager
from ..ui.mixins.token_mixin import TokenMixin
from ..ui.theme_manager import ThemeManager
from .home.dashboard import HomeDashboard


class WelcomePage(TokenMixin, QWidget):

    def __init__(self, parent=None):
        QWidget.__init__(self, parent)
        TokenMixin.__init__(self)
        self.setObjectName("WelcomePage")
        self.lang_manager = LanguageManager()

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        page = QWidget(scroll)
        scroll.setWidget(page)
        outer.addWidget(scroll)

        layout = QVBoxLayout(page)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(14)
        self._dashboard = HomeDashboard(page)
        layout.addWidget(self._dashboard)
        layout.addStretch(1)

        self.retheme()

    def activate(self):
        self._dashboard.refresh()

    def deactivate(self):
        self._dashboard.cancel()

    def get_widget(self):
        """Return self as the widget for module system compatibility."""
        return self

    def retheme(self):
        ThemeManager.apply_module_style(self)
        self._dashboard.retheme()
