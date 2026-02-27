from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QFrame, QHBoxLayout, QLabel, QSizePolicy

from ...constants.file_paths import QssPaths
from ...constants.module_icons import IconNames
from ...widgets.theme_manager import ThemeManager
from ...python.responses import DataDisplayExtractors


class ContactsWidget(QFrame):
    """Inline chip list for coordination contacts."""

    MAX_VISIBLE_CONTACTS = 5
    def __init__(self, item_data, parent=None):
        super().__init__(parent)
        names = [n for n in (DataDisplayExtractors.extract_contact_names(item_data) or []) if n]
        if not names:
            self.setVisible(False)
            return

        self.setFrameShape(QFrame.NoFrame)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        # Replace the text label with an icon-based label
        icon_label = QLabel()
        icon_label.setObjectName("ContactsIcon")
        icon_label.setFixedSize(16, 16)
        icon_label.setPixmap(ThemeManager.get_qicon(IconNames.ICON_CONTACTS).pixmap(16, 16))
        layout.addWidget(icon_label, 0, Qt.AlignLeft | Qt.AlignVCenter)

        shown = 0
        for name in names[:self.MAX_VISIBLE_CONTACTS]:
            layout.addWidget(self._create_chip(name), 0, Qt.AlignLeft | Qt.AlignVCenter)
            shown += 1

        remaining = len(names) - shown
        if remaining > 0:
            layout.addWidget(self._create_chip(f"+{remaining}"), 0, Qt.AlignLeft | Qt.AlignVCenter)

        self.retheme()

    def _create_chip(self, text: str) -> QLabel:
        chip = QLabel(text)
        chip.setObjectName("ContactChip")
        chip.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        chip.adjustSize()
        return chip

    def retheme(self):
        """Reapply theme styles when theme changes."""
        ThemeManager.apply_module_style(self, [QssPaths.CONTACTS])
        # Force style refresh
        self.style().unpolish(self)
        self.style().polish(self)