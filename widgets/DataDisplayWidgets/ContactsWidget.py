from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QFrame, QHBoxLayout, QLabel

from ...constants.file_paths import QssPaths
from ...constants.module_icons import IconNames
from ...widgets.theme_manager import ThemeManager
from ...python.responses import DataDisplayExtractors


class ContactsWidget(QFrame):
    """Inline chip list for coordination contacts."""

    def __init__(self, item_data, total=None, parent=None):
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
        icon_label.setStyleSheet("padding-left: 0px;")
        layout.addWidget(icon_label, 0, Qt.AlignLeft | Qt.AlignVCenter)
        

        max_show = 5
        shown = 0
        for name in names[:max_show]:
            chip = QLabel(name)
            chip.setObjectName("ContactChip")
            chip_width = chip.fontMetrics().horizontalAdvance(name) + 6
            chip.setFixedWidth(chip_width)
            layout.addWidget(chip, 0, Qt.AlignLeft | Qt.AlignVCenter)
            shown += 1

        remaining = (total or len(names)) - shown
        if remaining > 0:
            more = QLabel(f"+{remaining}")
            more.setObjectName("ContactChip")
            more_width = more.fontMetrics().horizontalAdvance(more.text()) + 6
            more.setFixedWidth(more_width)
            layout.addWidget(more, 0, Qt.AlignLeft | Qt.AlignVCenter)
        self.retheme()
    def retheme(self):
        """Reapply theme styles when theme changes."""
        ThemeManager.apply_module_style(self, [QssPaths.CONTACTS])
        # Force style refresh
        self.style().unpolish(self)
        self.style().polish(self)