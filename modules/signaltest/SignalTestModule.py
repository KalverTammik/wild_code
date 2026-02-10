from typing import Optional, Sequence
from PyQt5.QtWidgets import QLabel, QVBoxLayout, QWidget, QPushButton

from ...languages.language_manager import LanguageManager
from ...languages.translation_keys import TranslationKeys
from ...modules.signaltest.SignalTestDialog import SignalTestDialog
from ...widgets.theme_manager import ThemeManager
from ...constants.file_paths import QssPaths
from ...utils.url_manager import Module
from ...ui.mixins.token_mixin import TokenMixin


class SignalTestModule(TokenMixin, QWidget):
    """Minimal host that launches the standalone SignalTest dialog."""

    def __init__(
        self,
        lang_manager: Optional[object] = None,
        parent: Optional[QWidget] = None,
        qss_files: Optional[Sequence[str]] = None,
    ) -> None:
        QWidget.__init__(self, parent)
        TokenMixin.__init__(self)

        self.module_key = Module.SIGNALTEST.name.lower()
        self.name = self.module_key
        self.lang_manager = lang_manager or LanguageManager()
        self.display_name = self.lang_manager.translate(TranslationKeys.SIGNALTEST)

        ThemeManager.apply_module_style(self, qss_files or [QssPaths.MAIN])

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(8)

        title = QLabel(self.lang_manager.translate(TranslationKeys.SIGNALTEST))
        title.setObjectName("FilterTitle")
        layout.addWidget(title)

        desc = QLabel(self.lang_manager.translate(TranslationKeys.SIGNALTEST_DESC))
        desc.setWordWrap(True)
        layout.addWidget(desc)

        launch_btn = QPushButton(self.lang_manager.translate(TranslationKeys.SIGNALTEST_LOAD_BTN))
        launch_btn.clicked.connect(self._open_dialog)
        layout.addWidget(launch_btn)

        layout.addStretch(1)

    def activate(self) -> None:
        """Lifecycle hook (unused)."""

    def deactivate(self) -> None:
        """Lifecycle hook (unused)."""

    def get_widget(self) -> QWidget:
        return self

    def _open_dialog(self) -> None:
        dialog = SignalTestDialog(self.lang_manager, parent=self)
        dialog.exec_()
    


