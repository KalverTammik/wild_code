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
    QGridLayout,
)

from ...constants.module_icons import ModuleIconPaths
from ...widgets.theme_manager import styleExtras
from ...widgets.DataDisplayWidgets.module_action_buttons import (
    OpenFolderActionButton,
    OpenWebActionButton,
    ShowOnMapActionButton,
    open_item_in_browser,
)
from ...widgets.DataDisplayWidgets.DatesWidget import DatesWidget
from ...widgets.DataDisplayWidgets.MembersView import MembersView


class PropertyTreeWidget(QFrame):
    """Card-based replacement for the legacy property tree."""

    DEFAULT_MESSAGE = "Vali kinnistu kaardilt"

    def __init__(self, parent: Optional[QWidget] = None, lang_manager=None):
        super().__init__(parent)
        self.setObjectName("PropertyTree")
        self.setFrameStyle(QFrame.NoFrame)
        self._current_entries: List[Dict[str, Any]] = []
        self.lang_manager = lang_manager

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
            card = PropertyConnectionCard(entry, self.lang_manager, self)
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
        self.setObjectName("ModuleInfoCard")
        self.setFrameStyle(QFrame.NoFrame)
        styleExtras.apply_chip_shadow(self, blur_radius=18, y_offset=2)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        content_frame = QFrame(self)
        content_frame.setObjectName("CardContent")
        layout = QHBoxLayout(content_frame)
        layout.setContentsMargins(16, 12, 16, 12)

        label = QLabel(message)
        font = QFont()
        font.setPointSize(10)
        font.setBold(is_loading)
        label.setFont(font)
        label.setWordWrap(True)
        layout.addWidget(label)

        outer.addWidget(content_frame)


class PropertyConnectionCard(QFrame):
    """Visualises a single property and all connected modules."""

    def __init__(
        self,
        entry: Dict[str, Any],
        lang_manager=None,
        parent: Optional[QWidget] = None,
    ):
        super().__init__(parent)
        self.entry = entry or {}
        self.lang_manager = lang_manager
        self.setObjectName("ModuleInfoCard")
        self.setFrameStyle(QFrame.NoFrame)
        styleExtras.apply_chip_shadow(self, blur_radius=25, y_offset=3)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        content_frame = QFrame(self)
        content_frame.setObjectName("CardContent")
        content_layout = QVBoxLayout(content_frame)
        content_layout.setContentsMargins(18, 16, 18, 16)
        content_layout.setSpacing(16)

        header = self._build_header()
        content_layout.addLayout(header)

        modules = self.entry.get("moduleConnections") or {}
        if not modules:
            empty = QLabel("Seoseid ei leitud")
            empty.setStyleSheet("color: rgb(130, 130, 130);")
            content_layout.addWidget(empty)
            outer.addWidget(content_frame)
            return

        for module_key, module_info in modules.items():
            section = ModuleConnectionSection(
                module_key,
                module_info,
                lang_manager=self.lang_manager,
            )
            content_layout.addWidget(section)

        outer.addWidget(content_frame)

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

    def __init__(
        self,
        module_key: str,
        module_info: Dict[str, Any],
        parent: Optional[QWidget] = None,
        *,
        lang_manager=None,
    ):
        super().__init__(parent)
        self.setObjectName("ModuleInfoCard")
        self.setFrameStyle(QFrame.NoFrame)

        module_name = module_key.capitalize()
        count = module_info.get("count", 0)
        items = module_info.get("items") or []

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        content_frame = QFrame(self)
        content_frame.setObjectName("CardContent")
        root = QVBoxLayout(content_frame)
        root.setContentsMargins(12, 12, 12, 12)
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
                row = ModuleConnectionRow(
                    summary,
                    module_key,
                    lang_manager=lang_manager,
                )
                body_layout.addWidget(row)

        root.addWidget(self.body)
        outer.addWidget(content_frame)

    def _toggle_body(self, checked: bool):
        self.body.setVisible(checked)
        self.toggle_button.setArrowType(Qt.DownArrow if checked else Qt.RightArrow)

    @staticmethod
    def _load_icon(module_key: str) -> Optional[str]:
        key = (module_key or "").upper()
        return ModuleIconPaths.get_module_icon(key)


class ModuleConnectionRow(QFrame):
    """Single row describing one connected item inside a module."""

    def __init__(
        self,
        summary: Dict[str, Any],
        module_key: str,
        parent: Optional[QWidget] = None,
        *,
        lang_manager=None,
    ):
        super().__init__(parent)
        self.summary = summary or {}
        self.module_key = module_key
        self.lang_manager = lang_manager
        self.item_id = self.summary.get("id")
        self.raw = self.summary.get("raw", {})
        self.setObjectName("ModuleConnectionRow")
        self.setFrameStyle(QFrame.NoFrame)
        self.setCursor(Qt.PointingHandCursor)

        grid = QGridLayout(self)
        grid.setContentsMargins(10, 8, 10, 8)
        grid.setHorizontalSpacing(10)
        grid.setVerticalSpacing(6)
        grid.setColumnStretch(1, 1)

        number = QLabel(self.summary.get("number") or self.summary.get("id") or "–")
        number.setObjectName("ModuleRowNumber")
        grid.addWidget(number, 0, 0, Qt.AlignTop)

        title = QLabel(self.summary.get("title") or "Nimetus puudub")
        title.setObjectName("ModuleRowTitle")
        title.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        grid.addWidget(title, 0, 1, Qt.AlignTop)

        actions_container = QWidget(self)
        actions_layout = QHBoxLayout(actions_container)
        actions_layout.setContentsMargins(0, 0, 0, 0)
        actions_layout.setSpacing(4)
        actions_layout.addStretch(1)

        file_path = self._extract_file_path()
        has_connections = self._has_property_connections()

        folder_btn = OpenFolderActionButton(file_path, lang_manager)
        actions_layout.addWidget(folder_btn)

        web_btn = OpenWebActionButton(self.module_key, self.item_id, lang_manager)
        actions_layout.addWidget(web_btn)

        map_btn = ShowOnMapActionButton(
            self.module_key,
            self.item_id,
            lang_manager,
            has_connections=has_connections,
        )
        actions_layout.addWidget(map_btn)

        grid.addWidget(actions_container, 0, 2, Qt.AlignRight | Qt.AlignTop)

        meta_widget = QWidget(self)
        meta_layout = QHBoxLayout(meta_widget)
        meta_layout.setContentsMargins(0, 0, 0, 0)
        meta_layout.setSpacing(6)

        status = self.summary.get("status")
        if status:
            meta_layout.addWidget(_build_pill_label(status))

        type_name = self.summary.get("type")
        if type_name:
            meta_layout.addWidget(_build_meta_label(type_name))

        updated = self.summary.get("updatedAt") or self.summary.get("raw", {}).get("updatedAt")
        formatted = _format_datetime(updated)
        if formatted:
            meta_layout.addWidget(_build_meta_label(f"Uuendatud {formatted}"))

        meta_layout.addStretch(1)
        grid.addWidget(meta_widget, 1, 0, 1, 2)

        dates_widget = self._build_dates_widget()
        if dates_widget:
            grid.addWidget(dates_widget, 1, 2, Qt.AlignRight | Qt.AlignTop)

        members_view = self._build_members_view()
        if members_view:
            grid.addWidget(members_view, 2, 0, 1, 3)

    def mouseDoubleClickEvent(self, event):
        if self.module_key and self.item_id:
            open_item_in_browser(self.module_key, self.item_id)
        super().mouseDoubleClickEvent(event)

    def _build_dates_widget(self):
        raw = self.raw if isinstance(self.raw, dict) else {}
        if not raw:
            return None
        has_dates = any(raw.get(key) for key in ("dueAt", "startAt", "createdAt", "updatedAt"))
        if not has_dates:
            return None
        try:
            widget = DatesWidget(raw, parent=self, compact=True, lang_manager=self.lang_manager)
            return widget
        except Exception:
            return None

    def _build_members_view(self):
        raw = self.raw if isinstance(self.raw, dict) else {}
        members = raw.get("members", {}) if isinstance(raw, dict) else {}
        edges = (members or {}).get("edges") or []
        if not edges:
            return None
        try:
            view = MembersView(raw, parent=self)
            return view
        except Exception:
            return None

    def _extract_file_path(self) -> Optional[str]:
        candidates = (
            self.raw.get("filesPath"),
            self.raw.get("files_path"),
            self.raw.get("files"),
        )
        for candidate in candidates:
            if candidate:
                return candidate
        return None

    def _has_property_connections(self) -> Optional[bool]:
        properties_block = self.raw.get("properties")
        if not properties_block:
            return None
        page_info = properties_block.get("pageInfo") or {}
        count = page_info.get("count")
        if count is None:
            count = page_info.get("total")
        if count is None:
            return None
        return bool(count)


def _build_pill_label(text: str) -> QLabel:
    label = QLabel(text)
    label.setObjectName("ModuleRowPill")
    return label


def _build_meta_label(text: str) -> QLabel:
    label = QLabel(text)
    label.setObjectName("ModuleRowMeta")
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
