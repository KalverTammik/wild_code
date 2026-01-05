from typing import Optional, Sequence

from PyQt5.QtWidgets import QLabel, QVBoxLayout, QWidget

from ...constants.file_paths import QssPaths
from ...utils.url_manager import Module
from ...widgets.theme_manager import ThemeManager


class SignalTestModule(QWidget):
    """Retired placeholder for the former SignalTest sandbox."""

    def __init__(
        self,
        lang_manager: Optional[object] = None,
        parent: Optional[QWidget] = None,
        qss_files: Optional[Sequence[str]] = None,
    ) -> None:
        super().__init__(parent)

        self._qss_files = qss_files

        self.module_key = Module.SIGNALTEST.name.lower()
        self.name = self.module_key
        self.lang_manager = lang_manager
        self.display_name = "Signaltest"

        ThemeManager.apply_module_style(self, qss_files or [QssPaths.MAIN])

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(8)

        title = QLabel("SignalTest")
        title.setObjectName("FilterTitle")
        layout.addWidget(title)

        desc = QLabel(
            "The SignalTest module has completed its test role and is now a placeholder.\n\n"
            "You can remove or repurpose this slot as needed."
        )
        desc.setWordWrap(True)
        layout.addWidget(desc)

        layout.addStretch(1)

    def activate(self) -> None:
        """Lifecycle hook (unused)."""

    def deactivate(self) -> None:
        """Lifecycle hook (unused)."""

    def get_widget(self) -> QWidget:
        return self

    def _on_test_button(self, n: int) -> None:
        # legacy toggle removed; this method is intentionally a no-op
        return

