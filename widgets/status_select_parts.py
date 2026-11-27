"""Shared parts of the status select controls: option normalizing, grouping into sections,
the clickable control frame and one colour-dot option row."""
from __future__ import annotations

from collections import OrderedDict
from typing import Iterable

from qgis.PyQt.QtCore import Qt, pyqtSignal
from qgis.PyQt.QtWidgets import QFrame, QHBoxLayout, QLabel, QSizePolicy

from ..languages.language_manager import LanguageManager
from ..languages.translation_keys import TranslationKeys
from ..ui.theme_manager import Theme, ThemeManager, is_dark
from ..utils.status_color_helper import StatusColorHelper

_STATUS_GROUP_ORDER = ("OPEN", "CLOSED")
_STATUS_GROUP_LABEL_KEYS = {
    "OPEN": TranslationKeys.STATUS_GROUP_OPEN,
    "CLOSED": TranslationKeys.STATUS_GROUP_CLOSED,
    "OTHER": TranslationKeys.STATUS_GROUP_OTHER,
}
FALLBACK_COLOR = "#CCCCCC"


def resolve_lang() -> LanguageManager:
    return LanguageManager()


def group_status_options(options: Iterable[dict[str, object]]) -> OrderedDict[str, list[dict[str, object]]]:
    groups: OrderedDict[str, list[dict[str, object]]] = OrderedDict()
    for group_name in _STATUS_GROUP_ORDER:
        groups[group_name] = []

    for option in options or []:
        status_type = str((option or {}).get("type") or "").strip().upper() or "OTHER"
        if status_type not in groups:
            groups[status_type] = []
        groups[status_type].append(dict(option or {}))

    return OrderedDict((key, value) for key, value in groups.items() if value)


def section_title(lang_manager: LanguageManager, status_type: str) -> str:
    normalized = str(status_type or "").strip().upper() or "OTHER"
    key = _STATUS_GROUP_LABEL_KEYS.get(normalized)
    return lang_manager.translate(key) if key else normalized


def is_dark_theme() -> bool:
    theme_name = ThemeManager.effective_theme()
    return is_dark(theme_name) if theme_name in (Theme.DARK, Theme.LIGHT, Theme.SYSTEM) else False


def status_scroll_style(dark_theme: bool) -> str:
    if dark_theme:
        handle = "rgba(255,255,255,0.24)"
        track = "rgba(255,255,255,0.05)"
    else:
        handle = "rgba(16,24,40,0.25)"
        track = "rgba(16,24,40,0.06)"
    return (
        "QScrollArea#StatusSelectScroll { background: transparent; border: none; }"
        "QScrollArea#StatusSelectScroll QWidget#StatusSelectContent { background: transparent; }"
        "QScrollBar:vertical {"
        f"background: {track};"
        "width: 7px;"
        "margin: 2px 0 2px 0;"
        "border-radius: 3px;"
        "}"
        "QScrollBar::handle:vertical {"
        f"background: {handle};"
        "min-height: 24px;"
        "border-radius: 3px;"
        "}"
        "QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }"
        "QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: transparent; }"
    )


def normalize_status_color(value: object) -> str:
    """'#RRGGBB' in upper case, or the grey fallback for anything else."""
    text = str(value or "").strip()
    if not text:
        return FALLBACK_COLOR
    if not text.startswith("#"):
        text = f"#{text}"
    if len(text) == 7:
        try:
            int(text[1:], 16)
            return text.upper()
        except ValueError:
            return FALLBACK_COLOR
    return FALLBACK_COLOR


def normalize_status_option(option: dict[str, object]) -> dict[str, object]:
    raw = dict(option or {})
    name = str(raw.get("name") or raw.get("label") or "").strip()
    return {
        "id": str(raw.get("id") or "").strip(),
        "name": name,
        "label": name,
        "color": normalize_status_color(raw.get("color")),
        "type": str(raw.get("type") or "").strip().upper(),
        "description": str(raw.get("description") or "").strip(),
        "isDefault": bool(raw.get("isDefault")),
        "sortOrder": raw.get("sortOrder"),
    }


def unique_status_options(options: Iterable[dict[str, object]]) -> list[dict[str, object]]:
    """Normalized options, without the ones that have no id or repeat an earlier id."""
    unique: list[dict[str, object]] = []
    seen: set[str] = set()
    for option in options or []:
        normalized = normalize_status_option(option)
        status_id = str(normalized.get("id") or "")
        if not status_id or status_id in seen:
            continue
        seen.add(status_id)
        unique.append(normalized)
    return unique


class ClickableFrame(QFrame):
    clicked = pyqtSignal()

    def mousePressEvent(self, event) -> None:  # noqa: N802 - Qt override
        if event.button() == Qt.LeftButton and self.isEnabled():
            self.setFocus(Qt.MouseFocusReason)
            self.clicked.emit()
            event.accept()
            return
        super().mousePressEvent(event)

    def keyPressEvent(self, event) -> None:  # noqa: N802 - Qt override
        if event.key() in (Qt.Key_Return, Qt.Key_Enter, Qt.Key_Space):
            self.clicked.emit()
            event.accept()
            return
        super().keyPressEvent(event)


class StatusOptionRow(QFrame):
    clicked = pyqtSignal(object)

    def __init__(self, option: dict[str, object], *, selected: bool, dark_theme: bool, parent=None):
        super().__init__(parent)
        self._option = dict(option or {})
        self._selected = bool(selected)
        self._dark_theme = bool(dark_theme)
        self.setObjectName("StatusSelectOptionRow")
        self.setCursor(Qt.PointingHandCursor)
        self.setAttribute(Qt.WA_Hover, True)

        row_layout = QHBoxLayout(self)
        row_layout.setContentsMargins(12, 7, 12, 7)
        row_layout.setSpacing(9)

        color = self._color_text(self._option.get("color"))
        dot = QFrame(self)
        dot.setObjectName("StatusSelectDot")
        dot.setFixedSize(10, 10)
        dot.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        dot.setStyleSheet(
            "QFrame#StatusSelectDot {"
            f"background-color: {color};"
            f"border: 1px solid {color};"
            "border-radius: 5px;"
            "}"
        )
        row_layout.addWidget(dot, 0, Qt.AlignVCenter)

        self._label = QLabel(str(self._option.get("name") or self._option.get("label") or "-"), self)
        self._label.setObjectName("StatusSelectOptionLabel")
        self._label.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self._label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self._apply_label_style()
        description = str(self._option.get("description") or "").strip()
        if description:
            self._label.setToolTip(description)
            self.setToolTip(description)
        row_layout.addWidget(self._label, 1, Qt.AlignVCenter)

        self._marker = QFrame(self)
        self._marker.setObjectName("StatusSelectSelectedMarker")
        self._marker.setFixedSize(4, 18)
        self._marker.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self._marker.setVisible(self._selected)
        self._marker.setStyleSheet(
            "QFrame#StatusSelectSelectedMarker {"
            f"background-color: {color};"
            "border-radius: 2px;"
            "}"
        )
        row_layout.addWidget(self._marker, 0, Qt.AlignVCenter)

        self._apply_style()

    @staticmethod
    def _color_text(value: object) -> str:
        text = str(value or "").strip()
        if not text:
            return FALLBACK_COLOR
        if not text.startswith("#"):
            text = f"#{text}"
        return text if len(text) == 7 else FALLBACK_COLOR

    def set_selected(self, selected: bool) -> None:
        self._selected = bool(selected)
        self._marker.setVisible(self._selected)
        self._apply_label_style()
        self._apply_style()

    def _apply_label_style(self) -> None:
        self._label.setStyleSheet(
            "QLabel#StatusSelectOptionLabel {"
            f"color: {'#f5f7fa' if self._dark_theme else '#2f363d'};"
            f"font-weight: {'700' if self._selected else '500'};"
            "font-size: 12px;"
            "}"
        )

    def _apply_style(self) -> None:
        color = self._color_text(self._option.get("color"))
        bg_rgb, _fg_rgb, border_rgb = StatusColorHelper.upgrade_status_color(color)

        if self._dark_theme:
            hover_bg = "rgba(255,255,255,0.08)"
            base_border = "rgba(255,255,255,0.00)"
        else:
            hover_bg = "rgba(16,24,40,0.06)"
            base_border = "rgba(16,24,40,0.00)"

        if self._selected:
            base_bg = f"rgba({bg_rgb[0]},{bg_rgb[1]},{bg_rgb[2]},0.18)"
            selected_border = f"rgba({border_rgb[0]},{border_rgb[1]},{border_rgb[2]},0.42)"
        else:
            base_bg = "transparent"
            selected_border = base_border

        self.setStyleSheet(
            "QFrame#StatusSelectOptionRow {"
            f"background-color: {base_bg};"
            f"border: 1px solid {selected_border};"
            "border-radius: 6px;"
            "}"
            "QFrame#StatusSelectOptionRow:hover {"
            f"background-color: {hover_bg};"
            f"border: 1px solid rgba({border_rgb[0]},{border_rgb[1]},{border_rgb[2]},0.34);"
            "}"
        )

    def mousePressEvent(self, event) -> None:  # noqa: N802 - Qt override
        if event.button() == Qt.LeftButton:
            self.clicked.emit(dict(self._option))
            event.accept()
            return
        super().mousePressEvent(event)
