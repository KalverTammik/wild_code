from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtWidgets import QFrame, QGridLayout, QHBoxLayout, QLabel, QSizePolicy, QVBoxLayout, QWidget

from ...Logs.python_fail_logger import PythonFailLogger
from ...constants.file_paths import QssPaths
from ...constants.module_icons import IconNames
from ...widgets.theme_manager import ThemeManager
from ...python.responses import DataDisplayExtractors


class _ContactEntryWidget(QWidget):
    def __init__(self, label_text: str, notes_text: str = "", parent=None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)

        chip = QLabel(label_text, self)
        chip.setObjectName("ContactChip")
        chip.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        chip.adjustSize()
        layout.addWidget(chip, 0, Qt.AlignLeft | Qt.AlignTop)

        trimmed_notes = notes_text.strip()
        if trimmed_notes:
            notes_label = QLabel(trimmed_notes, self)
            notes_label.setObjectName("ContactNote")
            notes_label.setWordWrap(False)
            notes_label.setToolTip(trimmed_notes)
            notes_label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
            layout.addWidget(notes_label, 0, Qt.AlignLeft | Qt.AlignTop)


class _WrappingContactsContainer(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self._items = []
        self._wrap_width = 0
        self._last_available_width = -1
        self._layout = QGridLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setHorizontalSpacing(4)
        self._layout.setVerticalSpacing(4)

    def add_item(self, widget: QWidget):
        widget.setParent(self)
        self._items.append(widget)
        self._relayout_items()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        available_width = self._effective_available_width()
        if available_width != self._last_available_width:
            self._relayout_items()

    def set_wrap_width(self, width: int):
        width = max(1, int(width))
        if width == self._wrap_width:
            return
        self._wrap_width = width
        available_width = self._effective_available_width()
        if available_width != self._last_available_width:
            self._relayout_items()

    def _clear_layout(self):
        while self._layout.count():
            item = self._layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                self._layout.removeWidget(widget)

    def _effective_available_width(self) -> int:
        margins = self._layout.contentsMargins()
        requested_width = self._wrap_width or self.width()
        actual_width = self.width()
        if actual_width > 0:
            requested_width = min(requested_width, actual_width)
        return max(1, requested_width - margins.left() - margins.right())

    def _relayout_items(self):
        self._clear_layout()
        if not self._items:
            return

        available_width = self._effective_available_width()
        self._last_available_width = available_width
        spacing = self._layout.horizontalSpacing()
        row = 0
        column = 0
        used_width = 0
        item_widths = []
        placements = []

        for index, widget in enumerate(self._items):
            item_width = widget.sizeHint().width()
            item_widths.append(item_width)
            next_width = item_width if column == 0 else used_width + spacing + item_width
            if column > 0 and next_width >= available_width:
                row += 1
                column = 0
                used_width = 0

            self._layout.addWidget(widget, row, column, Qt.AlignLeft | Qt.AlignTop)
            placements.append(f"{index}:{row},{column}:{item_width}")
            used_width = item_width if column == 0 else used_width + spacing + item_width
            column += 1

        PythonFailLogger.log(
            "contacts_wrap_metrics",
            module=PythonFailLogger.LOG_MODULE_UI,
            extra={
                "wrap_width": available_width,
                "container_width": self.width(),
                "items": len(self._items),
                "item_widths": "|".join(str(width) for width in item_widths),
                "placements": "|".join(placements),
                "spacing": spacing,
            },
        )


class ContactsWidget(QFrame):
    """Inline wrapping contact list for item cards."""

    def __init__(self, item_data, parent=None):
        super().__init__(parent)
        self._body = None
        self._icon_label = None
        self._root = None
        self._deferred_wrap_timer = None
        contacts = [c for c in (DataDisplayExtractors.extract_contacts(item_data) or []) if c.name]
        if not contacts:
            self.setVisible(False)
            return

        self.setFrameShape(QFrame.NoFrame)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self._root = QHBoxLayout(self)
        self._root.setContentsMargins(0, 0, 0, 0)
        self._root.setSpacing(4)

        self._icon_label = QLabel()
        self._icon_label.setObjectName("ContactsIcon")
        self._icon_label.setFixedSize(16, 16)
        self._icon_label.setPixmap(ThemeManager.get_qicon(IconNames.ICON_CONTACTS).pixmap(16, 16))
        self._root.addWidget(self._icon_label, 0, Qt.AlignLeft | Qt.AlignTop)

        self._body = _WrappingContactsContainer(self)
        for contact in contacts:
            self._body.add_item(self._create_contact_entry(contact))
        self._root.addWidget(self._body, 1)

        self._deferred_wrap_timer = QTimer(self)
        self._deferred_wrap_timer.setSingleShot(True)
        self._deferred_wrap_timer.timeout.connect(self._update_wrap_width)

        self._update_wrap_width()

        self.retheme()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self._body is None:
            return
        self._update_wrap_width()
        self._schedule_deferred_wrap_update()

    def handle_responsive_update(self, *, source="unknown"):
        _ = source
        if self._body is None:
            return
        self._update_wrap_width()
        self._schedule_deferred_wrap_update()

    def _schedule_deferred_wrap_update(self):
        if self._deferred_wrap_timer is None:
            return
        self._deferred_wrap_timer.start(0)

    def _update_wrap_width(self):
        if self._body is None:
            return
        self._body.set_wrap_width(self._available_wrap_width())

    def _available_wrap_width(self) -> int:
        available_width = self.contentsRect().width()
        if self._icon_label is not None:
            available_width -= self._icon_label.width()
        if self._root is not None:
            available_width -= self._root.spacing()
        return max(1, available_width)

    def _create_contact_entry(self, contact) -> QWidget:
        return _ContactEntryWidget(contact.name, contact.notes, self)

    def retheme(self):
        """Reapply theme styles when theme changes."""
        ThemeManager.apply_module_style(self, [QssPaths.CONTACTS])
        # Force style refresh
        self.style().unpolish(self)
        self.style().polish(self)