from datetime import datetime
from typing import Any, Dict, List, Optional

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QPixmap
from PyQt5.QtWidgets import (
    QFrame,
    QVBoxLayout,
    QLabel,
    QWidget,
    QScrollArea,
    QHBoxLayout,
    QToolButton,
    QSizePolicy,
)

from ...constants.module_icons import ModuleIconPaths
from ...widgets.theme_manager import styleExtras


class PropertyTreeWidget(QFrame):
    """Card-based replacement for the legacy property tree."""

    DEFAULT_MESSAGE = "Vali kinnistu kaardilt"

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("PropertyTree")
        self.setFrameStyle(QFrame.NoFrame)
        self._current_entries: List[Dict[str, Any]] = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(10)

        title = QLabel("Kinnistuga seotud andmed")
        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(12)
        title.setFont(title_font)
        layout.addWidget(title)

        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameStyle(QFrame.NoFrame)
        layout.addWidget(self.scroll_area, 1)

        self.cards_container = QWidget()
        self.cards_layout = QVBoxLayout(self.cards_container)
        self.cards_layout.setContentsMargins(0, 0, 0, 0)
        self.cards_layout.setSpacing(10)
        self.scroll_area.setWidget(self.cards_container)

        self.show_message(self.DEFAULT_MESSAGE)

    # --- Public API ------------------------------------------------------

    def show_message(self, message: str):
        self._current_entries = []
        self._reset_cards()
        self.cards_layout.addWidget(MessageCard(message))
        self.cards_layout.addStretch(1)

    def show_loading(self, message: str = "Laen seotud andmeid..."):
        self._current_entries = []
        self._reset_cards()
        self.cards_layout.addWidget(MessageCard(message, is_loading=True))
        self.cards_layout.addStretch(1)

    def load_connections(self, entries: List[Dict[str, Any]]):
        self._current_entries = entries or []
        self._reset_cards()

        if not entries:
            self.cards_layout.addWidget(MessageCard("Seoseid ei leitud"))
            self.cards_layout.addStretch(1)
            return

        for entry in entries:
            card = PropertyConnectionCard(entry, self)
            self.cards_layout.addWidget(card)

        self.cards_layout.addStretch(1)

    def refresh_tree_data(self):
        if not self._current_entries:
            self.show_message("Andmed puuduvad")
            return
        self.load_connections(self._current_entries)

    # --- Internal helpers -------------------------------------------------

    def _reset_cards(self):
        while self.cards_layout.count():
            item = self.cards_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()


class MessageCard(QFrame):
    """Simple card that shows contextual messages inside the scroll area."""

    def __init__(self, message: str, is_loading: bool = False, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setObjectName("PropertyMessageCard")
        self.setFrameStyle(QFrame.StyledPanel)
        styleExtras.apply_chip_shadow(self, blur_radius=18, y_offset=2)
        self.setStyleSheet(
            "#PropertyMessageCard {"
            "  border-radius: 10px;"
            "  border: 1px solid rgba(120, 120, 120, 60);"
            "  background-color: palette(Base);"
            "  padding: 12px;"
            "}"
        )

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)

        label = QLabel(message)
        font = QFont()
        font.setPointSize(10)
        font.setBold(is_loading)
        label.setFont(font)
        label.setWordWrap(True)
        layout.addWidget(label)


class PropertyConnectionCard(QFrame):
    """Visualises a single property and all connected modules."""

    def __init__(self, entry: Dict[str, Any], parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.entry = entry or {}
        self.setObjectName("PropertyConnectionCard")
        self.setFrameStyle(QFrame.StyledPanel)
        styleExtras.apply_chip_shadow(self, blur_radius=25, y_offset=3)
        self.setStyleSheet(
            "#PropertyConnectionCard {"
            "  border-radius: 12px;"
            "  border: 1px solid rgba(120, 120, 120, 70);"
            "  background-color: palette(Base);"
            "}"
        )

        root = QVBoxLayout(self)
        root.setContentsMargins(18, 16, 18, 16)
        root.setSpacing(16)

        header = self._build_header()
        root.addLayout(header)

        modules = self.entry.get("moduleConnections") or {}
        if not modules:
            empty = QLabel("Seoseid ei leitud")
            empty.setStyleSheet("color: rgb(130, 130, 130);")
            root.addWidget(empty)
            return

        for module_key, module_info in modules.items():
            section = ModuleConnectionSection(module_key, module_info)
            root.addWidget(section)

    def _build_header(self) -> QHBoxLayout:
        cadastral = self.entry.get("cadastralNumber") or "–"
        property_id = self.entry.get("propertyId") or "–"

        title = QLabel(f"Katastritunnus {cadastral}")
        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(11)
        title.setFont(title_font)

        info_label = QLabel(f"Property ID: {property_id}")
        info_label.setStyleSheet("color: rgb(120, 120, 120);")

        header = QVBoxLayout()
        header.setContentsMargins(0, 0, 0, 0)
        header.addWidget(title)
        header.addWidget(info_label)
        return header


class ModuleConnectionSection(QFrame):
    """Collapsible section hosting all connections for a module."""

    def __init__(self, module_key: str, module_info: Dict[str, Any], parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setObjectName("PropertyModuleSection")
        self.setFrameStyle(QFrame.StyledPanel)
        self.setStyleSheet(
            "#PropertyModuleSection {"
            "  border: 1px solid rgba(100, 100, 100, 50);"
            "  border-radius: 10px;"
            "  background-color: palette(AlternateBase);"
            "}"
        )

        module_name = module_key.capitalize()
        count = module_info.get("count", 0)
        items = module_info.get("items") or []

        root = QVBoxLayout(self)
        root.setContentsMargins(12, 10, 12, 10)
        root.setSpacing(8)

        header_row = QHBoxLayout()
        header_row.setContentsMargins(0, 0, 0, 0)
        header_row.setSpacing(8)

        icon_label = QLabel()
        icon_label.setFixedSize(24, 24)
        icon = self._load_icon(module_key)
        if icon:
            pix = QPixmap(icon).scaled(24, 24, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            icon_label.setPixmap(pix)
        header_row.addWidget(icon_label)

        title = QLabel(f"{module_name} ({count})")
        title_font = QFont()
        title_font.setBold(True)
        title.setFont(title_font)
        header_row.addWidget(title)
        header_row.addStretch(1)

        self.toggle_button = QToolButton(self)
        self.toggle_button.setCheckable(True)
        self.toggle_button.setChecked(True)
        self.toggle_button.setArrowType(Qt.DownArrow)
        self.toggle_button.toggled.connect(self._toggle_body)
        header_row.addWidget(self.toggle_button)

        root.addLayout(header_row)

        self.body = QWidget(self)
        body_layout = QVBoxLayout(self.body)
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(6)

        if not items:
            empty = QLabel("Kirjeid ei ole")
            empty.setStyleSheet("color: rgb(120, 120, 120);")
            body_layout.addWidget(empty)
        else:
            for summary in items:
                row = ModuleConnectionRow(summary)
                body_layout.addWidget(row)

        root.addWidget(self.body)

    def _toggle_body(self, checked: bool):
        self.body.setVisible(checked)
        self.toggle_button.setArrowType(Qt.DownArrow if checked else Qt.RightArrow)

    @staticmethod
    def _load_icon(module_key: str) -> Optional[str]:
        key = (module_key or "").upper()
        return ModuleIconPaths.get_module_icon(key)


class ModuleConnectionRow(QFrame):
    """Single row describing one connected item inside a module."""

    def __init__(self, summary: Dict[str, Any], parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.summary = summary or {}
        self.setObjectName("ModuleConnectionRow")
        self.setFrameStyle(QFrame.NoFrame)
        self.setStyleSheet(
            "#ModuleConnectionRow {"
            "  border: 1px solid rgba(255, 255, 255, 20);"
            "  border-radius: 6px;"
            "  background-color: palette(Base);"
            "}"
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(4)

        header_row = QHBoxLayout()
        header_row.setSpacing(8)

        number = QLabel(self.summary.get("number") or self.summary.get("id") or "–")
        number.setStyleSheet("font-weight: 600; color: rgb(90, 90, 90);")
        header_row.addWidget(number)

        title = QLabel(self.summary.get("title") or "Nimetus puudub")
        title.setStyleSheet("font-weight: 600;")
        title.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        header_row.addWidget(title, 1)

        layout.addLayout(header_row)

        meta_row = QHBoxLayout()
        meta_row.setSpacing(6)

        status = self.summary.get("status")
        if status:
            meta_row.addWidget(_build_pill_label(status))

        type_name = self.summary.get("type")
        if type_name:
            meta_row.addWidget(_build_meta_label(type_name))

        updated = self.summary.get("updatedAt") or self.summary.get("raw", {}).get("updatedAt")
        formatted = _format_datetime(updated)
        if formatted:
            meta_row.addWidget(_build_meta_label(f"Uuendatud {formatted}"))

        meta_row.addStretch(1)
        layout.addLayout(meta_row)


def _build_pill_label(text: str) -> QLabel:
    label = QLabel(text)
    label.setStyleSheet(
        "padding: 2px 6px;"
        "border-radius: 10px;"
        "background-color: rgba(80, 140, 255, 40);"
        "color: rgb(40, 90, 200);"
        "font-weight: 600;"
    )
    return label


def _build_meta_label(text: str) -> QLabel:
    label = QLabel(text)
    label.setStyleSheet("color: rgb(110, 110, 110);")
    return label


def _format_datetime(raw_value: Optional[str]) -> Optional[str]:
    if not raw_value:
        return None
    value = str(raw_value).strip()
    if not value:
        return None
    try:
        if value.endswith("Z"):
            value = value.replace("Z", "+00:00")
        dt = datetime.fromisoformat(value)
        return dt.strftime("%d.%m.%Y")
    except Exception:
        return raw_value
