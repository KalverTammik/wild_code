from datetime import datetime
from typing import Any, Dict, List, Optional
try:
    import sip
except Exception:  # pragma: no cover - runtime availability depends on QGIS/PyQt packaging
    sip = None

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
    QSizePolicy,
)

from ...constants.module_icons import ModuleIconPaths
from ...widgets.theme_manager import styleExtras, ThemeShadowColors
from ...widgets.DataDisplayWidgets.ModuleConnectionActions import ModuleConnectionActions
from ...languages.translation_keys import TranslationKeys
from ...widgets.DelayHelpers.LoadingSpinner import GradientSpinner
from ...languages.language_manager import LanguageManager
from ...Logs.python_fail_logger import PythonFailLogger
from ...utils.url_manager import Module


class PropertyTreeWidget(QFrame):
    """Card-based replacement for the legacy property tree."""

    def __init__(self, parent: Optional[QWidget] = None, lang_manager=None):
        super().__init__(parent)
        self.setObjectName("PropertyTree")
        self.setFrameStyle(QFrame.NoFrame)
        self._current_entries: List[Dict[str, Any]] = []
        self.lang_manager = lang_manager or LanguageManager()

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

        default_message = self.lang_manager.translate(TranslationKeys.PROPERTY_TREE_DEFAULT_MESSAGE) or ""
  
        self.show_message(default_message)

    # --- Public API ------------------------------------------------------

    def show_message(self, message: str):
        self._current_entries = []
        self._replace_cards([MessageCard(message)])

    def show_loading(self):
        self._current_entries = []
        message = self.lang_manager.translate(TranslationKeys.CONNECTIONS)
        self._replace_cards([MessageCard(message, is_loading=True)])

    def load_connections(self, entries: List[Dict[str, Any]]):
        self._current_entries = entries or []

        if not entries:
            no_connections = self.lang_manager.translate(TranslationKeys.PROPERTY_TREE_NO_CONNECTIONS)
            self._replace_cards([MessageCard(no_connections)])
            return

        widgets: List[QWidget] = []
        for entry in entries:
            try:
                card = PropertyConnectionCard(entry, self.lang_manager, self)
                styleExtras.apply_chip_shadow(
                    card,
                    blur_radius=15,
                    x_offset=1,
                    y_offset=2,
                    color=ThemeShadowColors.ACCENT,
                    alpha_level="medium",
                )
                widgets.append(card)
            except Exception as exc:
                PythonFailLogger.log_exception(
                    exc,
                    module=Module.PROPERTY.value,
                    event="property_tree_build_card_failed",
                )

        self._replace_cards(widgets)

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
                try:
                    widget.hide()
                    widget.setParent(None)
                except Exception:
                    pass
                widget.deleteLater()

    @staticmethod
    def _is_deleted(widget) -> bool:
        try:
            return bool(widget is None or (sip and sip.isdeleted(widget)))
        except Exception:
            return widget is None

    def _replace_cards(self, widgets: List[QWidget]) -> None:
        if self._is_deleted(self) or self._is_deleted(self.cards_container):
            return
        self.cards_container.setUpdatesEnabled(False)
        try:
            self._reset_cards()
            for widget in widgets:
                if self._is_deleted(widget):
                    continue
                self.cards_layout.addWidget(widget)
            self.cards_layout.addStretch(1)
        finally:
            if not self._is_deleted(self.cards_container):
                self.cards_container.setUpdatesEnabled(True)


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
        self.lang_manager = lang_manager or LanguageManager()
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
                lang_manager=self.lang_manager,
            )
            content_layout.addWidget(section)

        outer.addWidget(content_frame)


class ModuleConnectionSection(QFrame):
    """Collapsible section hosting all connections for a module."""

    _pixmap_cache: Dict[tuple, QPixmap] = {}

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

        translator = lang_manager or LanguageManager()
        self._translator = translator
        self._module_key = str(module_key or "").strip()
        module_name = translator.translate_module_name(module_key)
        count = module_info.get("count", 0)
        self._items = list(module_info.get("items") or [])

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
            pix = self._get_icon_pixmap(icon, 24)
            if not pix.isNull():
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
        self.toggle_button.setChecked(len(self._items) <= 5)
        self.toggle_button.setArrowType(Qt.DownArrow if self.toggle_button.isChecked() else Qt.RightArrow)
        self.toggle_button.toggled.connect(self._toggle_body)
        header_row.addWidget(self.toggle_button)

        root.addLayout(header_row)

        self.body = QWidget(self)
        self._body_layout = QVBoxLayout(self.body)
        self._body_layout.setContentsMargins(0, 0, 0, 0)
        self._body_layout.setSpacing(4)
        self._body_built = False

        root.addWidget(self.body)
        outer.addWidget(content_frame)
        self._toggle_body(self.toggle_button.isChecked())

    def _toggle_body(self, checked: bool):
        if checked:
            self._ensure_body_loaded()
        self.body.setVisible(checked)
        self.toggle_button.setArrowType(Qt.DownArrow if checked else Qt.RightArrow)

    def _ensure_body_loaded(self) -> None:
        if self._body_built:
            return
        self._body_built = True

        if not self._items:
            empty_text = self._translator.translate(TranslationKeys.PROPERTY_TREE_MODULE_EMPTY)
            empty = QLabel(empty_text)
            empty.setStyleSheet("color: rgb(120, 120, 120);")
            self._body_layout.addWidget(empty)
            return

        for summary in self._items:
            try:
                row = ModuleConnectionRow(
                    summary,
                    self._module_key,
                    lang_manager=self._translator,
                )
                self._body_layout.addWidget(row)
            except Exception as exc:
                PythonFailLogger.log_exception(
                    exc,
                    module=Module.PROPERTY.value,
                    event="property_tree_build_row_failed",
                    extra={"target_module": self._module_key},
                )

    @classmethod
    def _get_icon_pixmap(cls, icon_path: str, size: int) -> QPixmap:
        key = (icon_path, size)
        cached = cls._pixmap_cache.get(key)
        if cached is not None:
            return cached
        pix = QPixmap(icon_path).scaled(size, size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        cls._pixmap_cache[key] = pix
        return pix


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
        self.lang_manager = lang_manager or LanguageManager()
        self.item_id = self.summary.get("id")
        self.raw = self.summary.get("raw", {})
        self.setObjectName("ModuleConnectionRow")
        self.setFrameStyle(QFrame.NoFrame)

        grid = QGridLayout(self)
        grid.setContentsMargins(0, 4, 0, 4)
        grid.setHorizontalSpacing(6)
        grid.setVerticalSpacing(4)
        grid.setColumnStretch(0, 1)

        title_container = QWidget(self)
        title_layout = QVBoxLayout(title_container)
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setSpacing(3)

        title_row = QHBoxLayout()
        title_row.setContentsMargins(0, 0, 0, 0)
        title_row.setSpacing(6)

        number_text = self._safe_text(
            self.summary.get("number"),
            self.raw.get("number"),
            fallback="",
        )
        if number_text:
            number_badge = QLabel(number_text)
            number_badge.setObjectName("ProjectNumberBadge")
            number_badge.setAlignment(Qt.AlignCenter)
            number_badge.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)
            badge_width = max(24, number_badge.fontMetrics().horizontalAdvance(number_badge.text()) + 18)
            number_badge.setFixedWidth(badge_width)
            title_row.addWidget(number_badge, 0, Qt.AlignVCenter)

        title_text = self._safe_text(
            self.summary.get("title"),
            self.raw.get("name"),
            self.raw.get("jobName"),
            fallback=str(self.item_id or "-"),
        )
        title_label = QLabel(title_text)
        title_label.setObjectName("ProjectNameLabel")
        title_label.setWordWrap(True)
        title_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        title_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        title_row.addWidget(title_label, 1, Qt.AlignVCenter)
        title_layout.addLayout(title_row)

        meta_texts = [
            self._safe_text(self.summary.get("type"), self._extract_type_name(), fallback=""),
            self._safe_text(self.summary.get("status"), self._extract_status_name(), fallback=""),
            self._format_updated_text(),
            self._extract_client_text(),
        ]
        meta_texts = [text for text in meta_texts if text]
        if meta_texts:
            meta_label = QLabel("  •  ".join(meta_texts))
            meta_label.setObjectName("ProjectClientLabel")
            meta_label.setWordWrap(True)
            meta_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
            title_layout.addWidget(meta_label)

        grid.addWidget(title_container, 0, 0, Qt.AlignVCenter)

        file_path = self._extract_file_path()
        actions_payload = {
            "filesPath": file_path,
            "properties": self.raw.get("properties"),
        }
        actions_widget = ModuleConnectionActions(
            self.module_key,
            self.item_id,
            actions_payload,
            lang_manager=self.lang_manager,
            parent=self,
        )
        grid.addWidget(actions_widget, 0, 1, Qt.AlignRight | Qt.AlignTop)
        grid.setColumnStretch(1, 0)
        grid.setColumnMinimumWidth(1, actions_widget.sizeHint().width())


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

    @staticmethod
    def _safe_text(*values, fallback: str = "") -> str:
        for value in values:
            text = str(value or "").strip()
            if text:
                return text
        return fallback

    def _extract_status_name(self) -> str:
        status = self.raw.get("status") or {}
        if isinstance(status, dict):
            return str(status.get("name") or "").strip()
        return ""

    def _extract_type_name(self) -> str:
        type_payload = self.raw.get("type") or {}
        if isinstance(type_payload, dict):
            return str(type_payload.get("name") or type_payload.get("displayName") or "").strip()
        return str(type_payload or "").strip()

    def _extract_client_text(self) -> str:
        client = self.raw.get("client") or {}
        if isinstance(client, dict):
            return str(client.get("displayName") or client.get("name") or "").strip()
        return ""

    def _format_updated_text(self) -> str:
        raw_value = self.summary.get("updatedAt") or self.raw.get("updatedAt") or self.raw.get("createdAt")
        text = str(raw_value or "").strip()
        if not text:
            return ""
        normalized = text.replace("Z", "+00:00")
        try:
            dt = datetime.fromisoformat(normalized)
            return dt.strftime("%Y-%m-%d %H:%M")
        except Exception:
            return text[:16] if len(text) > 16 else text

