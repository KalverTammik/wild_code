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
    QGridLayout,
)

from ...constants.module_icons import ModuleIconPaths
from ...widgets.theme_manager import styleExtras, ThemeShadowColors
from ...widgets.DataDisplayWidgets.MembersView import MembersView
from ...widgets.DataDisplayWidgets.StatusWidget import StatusWidget
from ...widgets.DataDisplayWidgets.InfoCardHeader import InfocardHeaderFrame
from ...widgets.DataDisplayWidgets.ModuleConnectionActions import ModuleConnectionActions
from ...widgets.DataDisplayWidgets.DatesWidget import DatesWidget
from ...languages.translation_keys import TranslationKeys
from ...widgets.DelayHelpers.LoadingSpinner import GradientSpinner
from ...languages.language_manager import LanguageManager


class PropertyTreeWidget(QFrame):
    """Card-based replacement for the legacy property tree."""

    def __init__(self, parent: Optional[QWidget] = None, lang_manager=None):
        super().__init__(parent)
        self.setObjectName("PropertyTree")
        self.setFrameStyle(QFrame.NoFrame)
        self._current_entries: List[Dict[str, Any]] = []
        self.lang_manager = LanguageManager()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(10)

        title_text = self.lang_manager.translate(TranslationKeys.PROPERTY_TREE_HEADER)
        title = QLabel(title_text)
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

        default_message = self.lang_manager.translate(TranslationKeys.PROPERTY_TREE_DEFAULT_MESSAGE) or default_message
  
        self.show_message(default_message)

    # --- Public API ------------------------------------------------------

    def show_message(self, message: str):
        self._current_entries = []
        self._reset_cards()
        self.cards_layout.addWidget(MessageCard(message))
        self.cards_layout.addStretch(1)

    def show_loading(self):
        self._current_entries = []
        self._reset_cards()
        message = self.lang_manager.translate(TranslationKeys.CONNECTIONS)
        self.cards_layout.addWidget(MessageCard(message, is_loading=True))
        self.cards_layout.addStretch(1)

    def load_connections(self, entries: List[Dict[str, Any]]):
        self._current_entries = entries or []
        self._reset_cards()

        if not entries:
            no_connections = self.lang_manager.translate(TranslationKeys.PROPERTY_TREE_NO_CONNECTIONS)
            self.cards_layout.addWidget(MessageCard(no_connections))
            self.cards_layout.addStretch(1)
            return

        for entry in entries:
            card = PropertyConnectionCard(entry, self.lang_manager, self)
            styleExtras.apply_chip_shadow(
                card,
                blur_radius=15,
                x_offset=1,
                y_offset=2,
                color=ThemeShadowColors.ACCENT,
                alpha_level="medium",
            )
            self.cards_layout.addWidget(card)

        self.cards_layout.addStretch(1)

    def refresh_tree_data(self):
        if not self._current_entries:
            no_data = self.lang_manager.translate(TranslationKeys.PROPERTY_TREE_NO_DATA)
            self.show_message(no_data)
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
        styleExtras.apply_chip_shadow(
            self,
            blur_radius=15,
            x_offset=1,
            y_offset=2,
            color=ThemeShadowColors.ACCENT,
            alpha_level="medium",
        )

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        content_frame = QFrame(self)
        content_frame.setObjectName("CardContent")
        layout = QVBoxLayout(content_frame)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(10)
        layout.setAlignment(Qt.AlignCenter)

        if is_loading:
            spinner = GradientSpinner(
                content_frame,
                diameter=80,
                text=LanguageManager().translate(TranslationKeys.LOADING),
                sub_text= message,
                border_thickness=8,
                dots_interval_ms=320,
            )
            spinner.setFixedSize(120, 120)
            spinner.start()
            layout.addWidget(spinner, alignment=Qt.AlignCenter)

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
        self.setObjectName("ModuleInfoCard")
        self.setFrameStyle(QFrame.NoFrame)
        styleExtras.apply_chip_shadow(
            self,
            blur_radius=15,
            x_offset=1,
            y_offset=2,
            color=ThemeShadowColors.ACCENT,
            alpha_level="medium",
        )

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        content_frame = QFrame(self)
        content_frame.setObjectName("CardContent")
        content_layout = QVBoxLayout(content_frame)
        content_layout.setContentsMargins(4, 3, 4, 3)
        content_layout.setSpacing(4)

        modules = self.entry.get("moduleConnections") or {}
        if not modules:
            empty_text = LanguageManager().translate(TranslationKeys.PROPERTY_TREE_NO_CONNECTIONS)
            empty = QLabel(empty_text)
            empty.setStyleSheet("color: rgb(130, 130, 130);")
            content_layout.addWidget(empty)
            outer.addWidget(content_frame)
            return

        for module_key, module_info in modules.items():
            section = ModuleConnectionSection(
                module_key,
                module_info,
                lang_manager=LanguageManager(),
            )
            content_layout.addWidget(section)

        outer.addWidget(content_frame)


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
        styleExtras.apply_chip_shadow(
            self,
            blur_radius=15,
            x_offset=1,
            y_offset=2,
            color=ThemeShadowColors.ACCENT,
            alpha_level="medium",
        )

        module_name = lang_manager.translate(module_key)
        count = module_info.get("count", 0)
        items = module_info.get("items") or []

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        content_frame = QFrame(self)
        content_frame.setObjectName("CardContent")
        root = QVBoxLayout(content_frame)
        root.setContentsMargins(4, 4, 4, 4)
        root.setSpacing(4)

        header_row = QHBoxLayout()
        header_row.setContentsMargins(0, 0, 0, 0)
        header_row.setSpacing(4)

        icon_label = QLabel()
        icon_label.setFixedSize(24, 24)

        icon = ModuleIconPaths.get_module_icon(module_key.upper())
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
        body_layout.setSpacing(4)

        if not items:
            empty_text = lang_manager.translate(TranslationKeys.PROPERTY_TREE_MODULE_EMPTY)
            empty = QLabel(empty_text)
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

        grid = QGridLayout(self)
        grid.setContentsMargins(2, 0, 2, 0)
        grid.setHorizontalSpacing(2)
        grid.setColumnStretch(1, 1)

        pos = 0

        header_frame = InfocardHeaderFrame(self.raw, module_name=self.module_key)
        grid.addWidget(header_frame, 0, pos, Qt.AlignVCenter)

        pos_next = pos + 1

        date = DatesWidget(
            self.raw,
            parent=self,
            compact= False,
            lang_manager=self.lang_manager,
        )
        grid.addWidget(date, 0, pos_next, Qt.AlignRight | Qt.AlignVCenter)

        pos_next = pos_next + 1

        file_path = self._extract_file_path()
        has_connections = self._has_property_connections()
        actions_widget = ModuleConnectionActions(
            self.module_key,
            self.item_id,
            file_path,
            has_connections,
            lang_manager=lang_manager,
            parent=self,
        )
        grid.addWidget(actions_widget, 0, pos_next, Qt.AlignRight | Qt.AlignVCenter)

        pos_next = pos_next + 1

        members_view = MembersView(self.raw, parent=self)
        if members_view:
            members_view.setFixedWidth(100)
            grid.addWidget(members_view, 0, pos_next, Qt.AlignRight | Qt.AlignVCenter)

        pos_next = pos_next + 1
        status_widget = StatusWidget(
                self.raw,
                parent=self,
            )
        if status_widget:
            grid.addWidget(status_widget, 0, pos_next, Qt.AlignRight | Qt.AlignVCenter)


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
            return None
        return bool(count)

