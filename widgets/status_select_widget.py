from __future__ import annotations

from collections import OrderedDict
from typing import Iterable, Optional

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from ..languages.language_manager import LanguageManager
from ..languages.translation_keys import TranslationKeys
from ..ui.window_state.popup_helpers import PopupHelpers
from ..utils.status_color_helper import StatusColorHelper
from .theme_manager import Theme, ThemeManager, is_dark


_STATUS_GROUP_ORDER = ("OPEN", "CLOSED")
_STATUS_GROUP_LABEL_KEYS = {
    "OPEN": TranslationKeys.STATUS_GROUP_OPEN,
    "CLOSED": TranslationKeys.STATUS_GROUP_CLOSED,
    "OTHER": TranslationKeys.STATUS_GROUP_OTHER,
}


def _resolve_lang(lang_manager=None) -> LanguageManager:
    return lang_manager or LanguageManager()


def _group_status_options(options: Iterable[dict[str, object]]) -> OrderedDict[str, list[dict[str, object]]]:
    groups: OrderedDict[str, list[dict[str, object]]] = OrderedDict()
    for group_name in _STATUS_GROUP_ORDER:
        groups[group_name] = []

    for option in options or []:
        status_type = str((option or {}).get("type") or "").strip().upper() or "OTHER"
        if status_type not in groups:
            groups[status_type] = []
        groups[status_type].append(dict(option or {}))

    return OrderedDict((key, value) for key, value in groups.items() if value)


def _section_title(lang_manager: LanguageManager, status_type: str) -> str:
    normalized = str(status_type or "").strip().upper() or "OTHER"
    key = _STATUS_GROUP_LABEL_KEYS.get(normalized)
    return lang_manager.translate(key) if key else normalized


def _is_dark_theme() -> bool:
    theme_name = ThemeManager.effective_theme()
    return is_dark(theme_name) if theme_name in (Theme.DARK, Theme.LIGHT, Theme.SYSTEM) else False


def _status_scroll_style(dark_theme: bool) -> str:
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


class _ClickableFrame(QFrame):
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


class _StatusOptionRow(QFrame):
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
            return "#CCCCCC"
        if not text.startswith("#"):
            text = f"#{text}"
        return text if len(text) == 7 else "#CCCCCC"

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


class _StatusSelectPopup(QWidget):
    optionSelected = pyqtSignal(object)

    MAX_HEIGHT = 286
    MIN_WIDTH = 210

    def __init__(
        self,
        options: Iterable[dict[str, object]],
        *,
        selected_id: str,
        min_width: int,
        lang_manager=None,
        parent=None,
    ):
        super().__init__(parent, flags=Qt.Popup | Qt.FramelessWindowHint)
        self.setObjectName("StatusSelectPopup")
        self.setAttribute(Qt.WA_DeleteOnClose, True)
        self.setFocusPolicy(Qt.NoFocus)
        self._lang = _resolve_lang(lang_manager)
        self._dark_theme = _is_dark_theme()
        self._selected_id = str(selected_id or "").strip()
        self._options = [dict(option or {}) for option in (options or [])]

        width = max(self.MIN_WIDTH, int(min_width or 0))
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        frame = QFrame(self)
        frame.setObjectName("StatusSelectPopupFrame")
        frame.setMinimumWidth(width)
        frame.setStyleSheet(self._popup_style())
        frame_layout = QVBoxLayout(frame)
        frame_layout.setContentsMargins(6, 6, 6, 6)
        frame_layout.setSpacing(0)

        scroll = QScrollArea(frame)
        scroll.setObjectName("StatusSelectScroll")
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setStyleSheet(self._scroll_style())

        content = QWidget(scroll)
        content.setObjectName("StatusSelectContent")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(2)

        for section_type, section_options in self._grouped_options().items():
            section_label = QLabel(self._section_title(section_type), content)
            section_label.setObjectName("StatusSelectSectionLabel")
            section_label.setAttribute(Qt.WA_TransparentForMouseEvents, True)
            content_layout.addWidget(section_label)

            for option in section_options:
                row = _StatusOptionRow(
                    option,
                    selected=str(option.get("id") or "").strip() == self._selected_id,
                    dark_theme=self._dark_theme,
                    parent=content,
                )
                row.clicked.connect(self.optionSelected.emit)
                content_layout.addWidget(row)

        content_layout.addSpacing(2)
        scroll.setWidget(content)
        content.adjustSize()
        scroll.setFixedHeight(min(self.MAX_HEIGHT, max(42, content.sizeHint().height() + 2)))
        frame_layout.addWidget(scroll)
        root.addWidget(frame)

    def _grouped_options(self) -> OrderedDict[str, list[dict[str, object]]]:
        return _group_status_options(self._options)

    def _section_title(self, status_type: str) -> str:
        return _section_title(self._lang, status_type)

    @staticmethod
    def _is_dark_theme() -> bool:
        return _is_dark_theme()

    def _popup_style(self) -> str:
        if self._dark_theme:
            return (
                "QFrame#StatusSelectPopupFrame {"
                "background: #242b33;"
                "border: 1px solid rgba(9,144,143,0.58);"
                "border-radius: 8px;"
                "}"
                "QLabel#StatusSelectSectionLabel {"
                "color: #9aa7b6;"
                "font-size: 10px;"
                "font-weight: 700;"
                "padding: 8px 10px 3px 10px;"
                "}"
            )
        return (
            "QFrame#StatusSelectPopupFrame {"
            "background: #ffffff;"
            "border: 1px solid rgba(15,23,42,0.14);"
            "border-radius: 8px;"
            "}"
            "QLabel#StatusSelectSectionLabel {"
            "color: #667085;"
            "font-size: 10px;"
            "font-weight: 700;"
            "padding: 8px 10px 3px 10px;"
            "}"
        )

    def _scroll_style(self) -> str:
        return _status_scroll_style(self._dark_theme)


class _StatusMultiSelectPopup(QWidget):
    selectionChanged = pyqtSignal(list, list)

    MAX_HEIGHT = 320
    MIN_WIDTH = 230

    def __init__(
        self,
        options: Iterable[dict[str, object]],
        *,
        selected_ids: Iterable[str],
        min_width: int,
        lang_manager=None,
        parent=None,
    ):
        super().__init__(parent, flags=Qt.Popup | Qt.FramelessWindowHint)
        self.setObjectName("StatusMultiSelectPopup")
        self.setAttribute(Qt.WA_DeleteOnClose, True)
        self.setFocusPolicy(Qt.NoFocus)
        self._lang = _resolve_lang(lang_manager)
        self._dark_theme = _is_dark_theme()
        self._options = [dict(option or {}) for option in (options or [])]
        self._selected_ids = {str(value or "").strip() for value in (selected_ids or []) if str(value or "").strip()}
        self._row_by_id: dict[str, _StatusOptionRow] = {}

        width = max(self.MIN_WIDTH, int(min_width or 0))
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        frame = QFrame(self)
        frame.setObjectName("StatusSelectPopupFrame")
        frame.setMinimumWidth(width)
        frame.setStyleSheet(self._popup_style())
        frame_layout = QVBoxLayout(frame)
        frame_layout.setContentsMargins(6, 6, 6, 6)
        frame_layout.setSpacing(4)

        actions = QFrame(frame)
        actions.setObjectName("StatusSelectActionRow")
        actions_layout = QHBoxLayout(actions)
        actions_layout.setContentsMargins(6, 3, 6, 5)
        actions_layout.setSpacing(6)

        self._select_all_btn = QPushButton(self._action_label(TranslationKeys.SELECT_ALL), actions)
        self._select_all_btn.setObjectName("StatusSelectActionButton")
        self._select_all_btn.setCursor(Qt.PointingHandCursor)
        self._select_all_btn.clicked.connect(self._select_all)
        actions_layout.addWidget(self._select_all_btn)

        self._clear_btn = QPushButton(self._action_label(TranslationKeys.CLEAR_SELECTION), actions)
        self._clear_btn.setObjectName("StatusSelectActionButton")
        self._clear_btn.setCursor(Qt.PointingHandCursor)
        self._clear_btn.clicked.connect(self._clear_selection)
        actions_layout.addWidget(self._clear_btn)
        frame_layout.addWidget(actions)

        scroll = QScrollArea(frame)
        scroll.setObjectName("StatusSelectScroll")
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setStyleSheet(self._scroll_style())

        content = QWidget(scroll)
        content.setObjectName("StatusSelectContent")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(2)

        for section_type, section_options in self._grouped_options().items():
            section_label = QLabel(self._section_title(section_type), content)
            section_label.setObjectName("StatusSelectSectionLabel")
            section_label.setAttribute(Qt.WA_TransparentForMouseEvents, True)
            content_layout.addWidget(section_label)

            for option in section_options:
                status_id = str(option.get("id") or "").strip()
                row = _StatusOptionRow(
                    option,
                    selected=status_id in self._selected_ids,
                    dark_theme=self._dark_theme,
                    parent=content,
                )
                row.clicked.connect(self._toggle_option)
                if status_id:
                    self._row_by_id[status_id] = row
                content_layout.addWidget(row)

        content_layout.addSpacing(2)
        scroll.setWidget(content)
        content.adjustSize()
        scroll.setFixedHeight(min(self.MAX_HEIGHT, max(42, content.sizeHint().height() + 2)))
        frame_layout.addWidget(scroll)
        root.addWidget(frame)
        self._sync_action_state()

    def _action_label(self, key: str) -> str:
        return self._lang.translate(key)

    def _grouped_options(self) -> OrderedDict[str, list[dict[str, object]]]:
        return _group_status_options(self._options)

    def _section_title(self, status_type: str) -> str:
        return _section_title(self._lang, status_type)

    def _toggle_option(self, option: dict[str, object]) -> None:
        status_id = str((option or {}).get("id") or "").strip()
        if not status_id:
            return
        if status_id in self._selected_ids:
            self._selected_ids.remove(status_id)
        else:
            self._selected_ids.add(status_id)
        self._sync_rows()
        self._emit_selection_changed()

    def _select_all(self) -> None:
        self._selected_ids = {
            str(option.get("id") or "").strip()
            for option in self._options
            if str(option.get("id") or "").strip()
        }
        self._sync_rows()
        self._emit_selection_changed()

    def _clear_selection(self) -> None:
        if not self._selected_ids:
            return
        self._selected_ids.clear()
        self._sync_rows()
        self._emit_selection_changed()

    def _sync_rows(self) -> None:
        for status_id, row in self._row_by_id.items():
            row.set_selected(status_id in self._selected_ids)
        self._sync_action_state()

    def _sync_action_state(self) -> None:
        option_ids = [
            str(option.get("id") or "").strip()
            for option in self._options
            if str(option.get("id") or "").strip()
        ]
        selected_count = sum(1 for status_id in option_ids if status_id in self._selected_ids)
        self._select_all_btn.setEnabled(bool(option_ids) and selected_count != len(option_ids))
        self._clear_btn.setEnabled(selected_count > 0)

    def _emit_selection_changed(self) -> None:
        ids = self._ordered_selected_ids()
        texts = [
            str(option.get("name") or "").strip()
            for option in self._options
            if str(option.get("id") or "").strip() in set(ids) and str(option.get("name") or "").strip()
        ]
        self.selectionChanged.emit(texts, ids)

    def _ordered_selected_ids(self) -> list[str]:
        return [
            status_id
            for status_id in (str(option.get("id") or "").strip() for option in self._options)
            if status_id and status_id in self._selected_ids
        ]

    def _popup_style(self) -> str:
        if self._dark_theme:
            return (
                "QFrame#StatusSelectPopupFrame {"
                "background: #242b33;"
                "border: 1px solid rgba(9,144,143,0.58);"
                "border-radius: 8px;"
                "}"
                "QLabel#StatusSelectSectionLabel {"
                "color: #9aa7b6;"
                "font-size: 10px;"
                "font-weight: 700;"
                "padding: 8px 10px 3px 10px;"
                "}"
                "QFrame#StatusSelectActionRow {"
                "background: transparent;"
                "border: none;"
                "}"
                "QPushButton#StatusSelectActionButton {"
                "background: rgba(255,255,255,0.07);"
                "border: 1px solid rgba(255,255,255,0.12);"
                "border-radius: 5px;"
                "color: #eef2f7;"
                "font-size: 11px;"
                "font-weight: 700;"
                "padding: 4px 8px;"
                "}"
                "QPushButton#StatusSelectActionButton:hover {"
                "background: rgba(255,255,255,0.12);"
                "}"
                "QPushButton#StatusSelectActionButton:disabled {"
                "color: rgba(238,242,247,0.42);"
                "background: rgba(255,255,255,0.03);"
                "border: 1px solid rgba(255,255,255,0.06);"
                "}"
            )
        return (
            "QFrame#StatusSelectPopupFrame {"
            "background: #ffffff;"
            "border: 1px solid rgba(15,23,42,0.14);"
            "border-radius: 8px;"
            "}"
            "QLabel#StatusSelectSectionLabel {"
            "color: #667085;"
            "font-size: 10px;"
            "font-weight: 700;"
            "padding: 8px 10px 3px 10px;"
            "}"
            "QFrame#StatusSelectActionRow {"
            "background: transparent;"
            "border: none;"
            "}"
            "QPushButton#StatusSelectActionButton {"
            "background: #f8fafc;"
            "border: 1px solid rgba(15,23,42,0.12);"
            "border-radius: 5px;"
            "color: #344054;"
            "font-size: 11px;"
            "font-weight: 700;"
            "padding: 4px 8px;"
            "}"
            "QPushButton#StatusSelectActionButton:hover {"
            "background: #eef4f8;"
            "border: 1px solid rgba(9,144,143,0.34);"
            "}"
            "QPushButton#StatusSelectActionButton:disabled {"
            "color: rgba(52,64,84,0.42);"
            "background: #f9fafb;"
            "border: 1px solid rgba(15,23,42,0.06);"
            "}"
        )

    def _scroll_style(self) -> str:
        return _status_scroll_style(self._dark_theme)


class StatusSelectWidget(QWidget):
    """Status-only select control with a custom color-dot popup."""

    currentChanged = pyqtSignal(str, str)

    def __init__(
        self,
        parent: Optional[QWidget] = None,
        *,
        placeholder: Optional[str] = None,
        lang_manager=None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("StatusSelectWidget")
        self._lang = _resolve_lang(lang_manager)
        self._placeholder = str(placeholder or self._lang.translate(TranslationKeys.SELECT))
        self._options: list[dict[str, object]] = []
        self._selected_id = ""
        self._popup: Optional[_StatusSelectPopup] = None

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._control = _ClickableFrame(self)
        self._control.setObjectName("StatusSelectControl")
        self._control.setFocusPolicy(Qt.StrongFocus)
        self._control.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self._control.clicked.connect(self._toggle_popup)

        control_layout = QHBoxLayout(self._control)
        control_layout.setContentsMargins(10, 5, 9, 5)
        control_layout.setSpacing(8)

        self._dot = QFrame(self._control)
        self._dot.setObjectName("StatusSelectCurrentDot")
        self._dot.setFixedSize(10, 10)
        self._dot.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        control_layout.addWidget(self._dot, 0, Qt.AlignVCenter)

        self._label = QLabel(self._placeholder, self._control)
        self._label.setObjectName("StatusSelectCurrentLabel")
        self._label.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self._label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        control_layout.addWidget(self._label, 1, Qt.AlignVCenter)

        self._arrow = QLabel("v", self._control)
        self._arrow.setObjectName("StatusSelectArrow")
        self._arrow.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self._arrow.setAlignment(Qt.AlignCenter)
        control_layout.addWidget(self._arrow, 0, Qt.AlignVCenter)

        layout.addWidget(self._control)
        self.setFocusProxy(self._control)
        self._apply_selected_option()

    def clear(self) -> None:
        self._options = []
        self._selected_id = ""
        self._close_popup()
        self._apply_selected_option()

    def count(self) -> int:
        return len(self._options)

    def retheme(self) -> None:
        self._apply_selected_option()

    def set_options(self, options: Iterable[dict[str, object]], *, selected_id: str = "") -> None:
        self._options = []
        seen: set[str] = set()
        for option in options or []:
            normalized = self._normalize_option(option)
            status_id = str(normalized.get("id") or "")
            if not status_id or status_id in seen:
                continue
            seen.add(status_id)
            self._options.append(normalized)

        self._selected_id = self._resolve_initial_selection(selected_id)
        self.setEnabled(bool(self._options))
        self._apply_selected_option()

    def currentData(self) -> str:  # noqa: N802 - QComboBox-compatible naming
        return self.current_status_id()

    def currentText(self) -> str:  # noqa: N802 - QComboBox-compatible naming
        return self.current_status_label()

    def current_status_id(self) -> str:
        return str(self._selected_id or "").strip()

    def current_status_label(self) -> str:
        option = self.current_option()
        return str((option or {}).get("name") or "").strip()

    def current_status_color(self) -> str:
        option = self.current_option()
        return str((option or {}).get("color") or "").strip()

    def current_option(self) -> Optional[dict[str, object]]:
        selected_id = self.current_status_id()
        for option in self._options:
            if str(option.get("id") or "").strip() == selected_id:
                return dict(option)
        return None

    def set_current_status_id(self, status_id: str, *, emit: bool = True) -> bool:
        target_id = str(status_id or "").strip()
        if target_id and not any(str(option.get("id") or "").strip() == target_id for option in self._options):
            return False
        if target_id == self._selected_id:
            return True
        self._selected_id = target_id
        self._apply_selected_option()
        if emit:
            self.currentChanged.emit(self.current_status_id(), self.current_status_label())
        return True

    def setEnabled(self, enabled: bool) -> None:  # noqa: N802 - Qt override
        super().setEnabled(enabled)
        self._control.setEnabled(enabled)
        self._apply_selected_option()

    def _toggle_popup(self) -> None:
        if not self.isEnabled() or not self._options:
            return
        if self._popup is not None and self._popup.isVisible():
            self._close_popup()
            return
        self._show_popup()

    def _show_popup(self) -> None:
        self._close_popup()
        popup = _StatusSelectPopup(
            self._options,
            selected_id=self._selected_id,
            min_width=max(self.width(), self._control.width(), _StatusSelectPopup.MIN_WIDTH),
            lang_manager=self._lang,
            parent=self.window(),
        )
        popup.optionSelected.connect(self._select_option)
        popup.destroyed.connect(lambda _obj=None: setattr(self, "_popup", None))
        PopupHelpers.position_popup(popup, self._control, placement="below_left")
        popup.show()
        popup.raise_()
        self._popup = popup

    def _close_popup(self) -> None:
        if self._popup is None:
            return
        self._popup.close()
        self._popup = None

    def _select_option(self, option: dict[str, object]) -> None:
        self._close_popup()
        self.set_current_status_id(str((option or {}).get("id") or "").strip(), emit=True)

    def _resolve_initial_selection(self, selected_id: str) -> str:
        selected_text = str(selected_id or "").strip()
        if selected_text and any(str(option.get("id") or "").strip() == selected_text for option in self._options):
            return selected_text

        for option in self._options:
            if option.get("isDefault"):
                return str(option.get("id") or "").strip()

        if self._options:
            return str(self._options[0].get("id") or "").strip()
        return ""

    def _apply_selected_option(self) -> None:
        option = self.current_option() or {}
        label = str(option.get("name") or self._placeholder).strip() or self._placeholder
        color = self._normalize_color(option.get("color"))

        self._label.setText(label)
        description = str(option.get("description") or "").strip()
        tooltip = description or label
        self.setToolTip(tooltip)
        self._control.setToolTip(tooltip)

        self._dot.setStyleSheet(
            "QFrame#StatusSelectCurrentDot {"
            f"background-color: {color};"
            f"border: 1px solid {color};"
            "border-radius: 5px;"
            "}"
        )
        self._apply_control_style(color)

    def _apply_control_style(self, color: str = "#CCCCCC") -> None:
        dark_theme = _is_dark_theme()
        bg_rgb, _fg_rgb, border_rgb = StatusColorHelper.upgrade_status_color(color)

        if not self.isEnabled():
            control_bg = "#f2f4f7" if not dark_theme else "#20252b"
            border = "rgba(98,108,120,0.36)"
            text = "rgba(98,108,120,0.85)" if not dark_theme else "rgba(170,178,188,0.58)"
            arrow = text
        else:
            control_bg = (
                f"rgba({bg_rgb[0]},{bg_rgb[1]},{bg_rgb[2]},0.12)"
                if self.current_option()
                else ("#ffffff" if not dark_theme else "#27313a")
            )
            border = f"rgba({border_rgb[0]},{border_rgb[1]},{border_rgb[2]},0.48)"
            text = "#27313a" if not dark_theme else "#f1f5f9"
            arrow = "#667085" if not dark_theme else "#a9b4c0"

        self._control.setStyleSheet(
            "QFrame#StatusSelectControl {"
            f"background-color: {control_bg};"
            f"border: 1px solid {border};"
            "border-radius: 6px;"
            "min-height: 24px;"
            "}"
            "QFrame#StatusSelectControl:hover {"
            f"border: 1px solid rgba({border_rgb[0]},{border_rgb[1]},{border_rgb[2]},0.70);"
            "}"
            "QFrame#StatusSelectControl:focus {"
            f"border: 1px solid rgba({border_rgb[0]},{border_rgb[1]},{border_rgb[2]},0.88);"
            "}"
        )
        self._label.setStyleSheet(
            "QLabel#StatusSelectCurrentLabel {"
            f"color: {text};"
            "font-size: 12px;"
            "font-weight: 600;"
            "}"
        )
        self._arrow.setStyleSheet(
            "QLabel#StatusSelectArrow {"
            f"color: {arrow};"
            "font-size: 10px;"
            "font-weight: 700;"
            "}"
        )
        self._control.setCursor(Qt.PointingHandCursor if self.isEnabled() else Qt.ArrowCursor)

    @classmethod
    def _normalize_option(cls, option: dict[str, object]) -> dict[str, object]:
        raw = dict(option or {})
        name = str(raw.get("name") or raw.get("label") or "").strip()
        return {
            "id": str(raw.get("id") or "").strip(),
            "name": name,
            "label": name,
            "color": cls._normalize_color(raw.get("color")),
            "type": str(raw.get("type") or "").strip().upper(),
            "description": str(raw.get("description") or "").strip(),
            "isDefault": bool(raw.get("isDefault")),
            "sortOrder": raw.get("sortOrder"),
        }

    @staticmethod
    def _normalize_color(value: object) -> str:
        text = str(value or "").strip()
        if not text:
            return "#CCCCCC"
        if not text.startswith("#"):
            text = f"#{text}"
        if len(text) == 7:
            try:
                int(text[1:], 16)
                return text.upper()
            except ValueError:
                return "#CCCCCC"
        return "#CCCCCC"


class StatusMultiSelectWidget(QWidget):
    """Status-only multi-select control with grouped color-dot popup actions."""

    selectionChanged = pyqtSignal(list, list)

    def __init__(
        self,
        parent: Optional[QWidget] = None,
        *,
        placeholder: Optional[str] = None,
        lang_manager=None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("StatusMultiSelectWidget")
        self._lang = _resolve_lang(lang_manager)
        self._placeholder = str(placeholder or self._lang.translate(TranslationKeys.SELECT))
        self._options: list[dict[str, object]] = []
        self._selected_ids: list[str] = []
        self._display_override = ""
        self._popup: Optional[_StatusMultiSelectPopup] = None

        self.setMinimumWidth(210)
        self.setMaximumWidth(360)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._control = _ClickableFrame(self)
        self._control.setObjectName("StatusSelectControl")
        self._control.setFocusPolicy(Qt.StrongFocus)
        self._control.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self._control.clicked.connect(self._toggle_popup)

        control_layout = QHBoxLayout(self._control)
        control_layout.setContentsMargins(10, 5, 9, 5)
        control_layout.setSpacing(8)

        self._dot = QFrame(self._control)
        self._dot.setObjectName("StatusSelectCurrentDot")
        self._dot.setFixedSize(10, 10)
        self._dot.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        control_layout.addWidget(self._dot, 0, Qt.AlignVCenter)

        self._label = QLabel(self._placeholder, self._control)
        self._label.setObjectName("StatusSelectCurrentLabel")
        self._label.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self._label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        control_layout.addWidget(self._label, 1, Qt.AlignVCenter)

        self._arrow = QLabel("v", self._control)
        self._arrow.setObjectName("StatusSelectArrow")
        self._arrow.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self._arrow.setAlignment(Qt.AlignCenter)
        control_layout.addWidget(self._arrow, 0, Qt.AlignVCenter)

        layout.addWidget(self._control)
        self.setFocusProxy(self._control)
        self._apply_display_value()

    def clear(self) -> None:
        self._options = []
        self._selected_ids = []
        self._display_override = ""
        self._close_popup()
        self._apply_display_value()

    def count(self) -> int:
        return len(self._options)

    def retheme(self) -> None:
        self._apply_display_value()

    def set_options(self, options: Iterable[dict[str, object]], *, selected_ids: Iterable[str] = ()) -> None:
        self._options = []
        seen: set[str] = set()
        for option in options or []:
            normalized = StatusSelectWidget._normalize_option(option)
            status_id = str(normalized.get("id") or "")
            if not status_id or status_id in seen:
                continue
            seen.add(status_id)
            self._options.append(normalized)

        self._display_override = ""
        self.set_selected_ids(selected_ids, emit=False)
        self.setEnabled(bool(self._options))
        self._apply_display_value()

    def set_loading(self, text: str) -> None:
        self._options = []
        self._selected_ids = []
        self._display_override = str(text or "").strip() or self._placeholder
        self._close_popup()
        self.setEnabled(False)
        self._apply_display_value()

    def set_error(self, text: str) -> None:
        self._options = []
        self._selected_ids = []
        self._display_override = str(text or "").strip() or self._placeholder
        self._close_popup()
        self.setEnabled(False)
        self._apply_display_value()

    def selected_ids(self) -> list[str]:
        option_order = {
            str(option.get("id") or "").strip(): index
            for index, option in enumerate(self._options)
            if str(option.get("id") or "").strip()
        }
        values = [str(value or "").strip() for value in self._selected_ids if str(value or "").strip()]
        return sorted(values, key=lambda value: option_order.get(value, len(option_order)))

    def selected_texts(self) -> list[str]:
        selected = set(self.selected_ids())
        return [
            str(option.get("name") or "").strip()
            for option in self._options
            if str(option.get("id") or "").strip() in selected and str(option.get("name") or "").strip()
        ]

    def set_selected_ids(self, ids: Iterable[str], *, emit: bool = True) -> None:
        available_ids = {
            str(option.get("id") or "").strip()
            for option in self._options
            if str(option.get("id") or "").strip()
        }
        requested_ids = [str(value or "").strip() for value in (ids or []) if str(value or "").strip()]
        if available_ids:
            requested_ids = [value for value in requested_ids if value in available_ids]

        seen: set[str] = set()
        self._selected_ids = []
        for value in requested_ids:
            if value in seen:
                continue
            seen.add(value)
            self._selected_ids.append(value)

        self._display_override = ""
        self._apply_display_value()
        if self._popup is not None and self._popup.isVisible():
            self._close_popup()
            self._show_popup()
        if emit:
            self.selectionChanged.emit(self.selected_texts(), self.selected_ids())

    def setEnabled(self, enabled: bool) -> None:  # noqa: N802 - Qt override
        super().setEnabled(enabled)
        self._control.setEnabled(enabled)
        self._apply_display_value()

    def _toggle_popup(self) -> None:
        if not self.isEnabled() or not self._options:
            return
        if self._popup is not None and self._popup.isVisible():
            self._close_popup()
            return
        self._show_popup()

    def _show_popup(self) -> None:
        self._close_popup()
        popup = _StatusMultiSelectPopup(
            self._options,
            selected_ids=self._selected_ids,
            min_width=max(self.width(), self._control.width(), _StatusMultiSelectPopup.MIN_WIDTH),
            lang_manager=self._lang,
            parent=self.window(),
        )
        popup.selectionChanged.connect(self._on_popup_selection_changed)
        popup.destroyed.connect(lambda _obj=None: setattr(self, "_popup", None))
        PopupHelpers.position_popup(popup, self._control, placement="below_left")
        popup.show()
        popup.raise_()
        self._popup = popup

    def _close_popup(self) -> None:
        if self._popup is None:
            return
        self._popup.close()
        self._popup = None

    def _on_popup_selection_changed(self, texts: list, ids: list) -> None:
        self._selected_ids = [str(value or "").strip() for value in (ids or []) if str(value or "").strip()]
        self._display_override = ""
        self._apply_display_value()
        self.selectionChanged.emit(list(texts or []), self.selected_ids())

    def _apply_display_value(self) -> None:
        texts = self.selected_texts()
        if self._display_override:
            label = self._display_override
        elif texts:
            label = ", ".join(texts)
        else:
            label = self._placeholder

        color = self._current_color()
        self._label.setText(label)
        tooltip = ", ".join(texts) if texts else label
        self.setToolTip(tooltip)
        self._control.setToolTip(tooltip)
        self._dot.setVisible(bool(texts))
        self._dot.setStyleSheet(
            "QFrame#StatusSelectCurrentDot {"
            f"background-color: {color};"
            f"border: 1px solid {color};"
            "border-radius: 5px;"
            "}"
        )
        self._apply_control_style(color, has_selection=bool(texts))

    def _current_color(self) -> str:
        selected = self.selected_ids()
        if not selected:
            return "#CCCCCC"
        first_id = selected[0]
        for option in self._options:
            if str(option.get("id") or "").strip() == first_id:
                return StatusSelectWidget._normalize_color(option.get("color"))
        return "#CCCCCC"

    def _apply_control_style(self, color: str = "#CCCCCC", *, has_selection: bool = False) -> None:
        dark_theme = _is_dark_theme()
        bg_rgb, _fg_rgb, border_rgb = StatusColorHelper.upgrade_status_color(color)

        if not self.isEnabled():
            control_bg = "#f2f4f7" if not dark_theme else "#20252b"
            border = "rgba(98,108,120,0.36)"
            text = "rgba(98,108,120,0.85)" if not dark_theme else "rgba(170,178,188,0.58)"
            arrow = text
        else:
            control_bg = (
                f"rgba({bg_rgb[0]},{bg_rgb[1]},{bg_rgb[2]},0.12)"
                if has_selection
                else ("#ffffff" if not dark_theme else "#27313a")
            )
            border = f"rgba({border_rgb[0]},{border_rgb[1]},{border_rgb[2]},0.48)" if has_selection else "rgba(15,23,42,0.18)"
            text = "#27313a" if not dark_theme else "#f1f5f9"
            arrow = "#667085" if not dark_theme else "#a9b4c0"

        self._control.setStyleSheet(
            "QFrame#StatusSelectControl {"
            f"background-color: {control_bg};"
            f"border: 1px solid {border};"
            "border-radius: 6px;"
            "min-height: 24px;"
            "}"
            "QFrame#StatusSelectControl:hover {"
            f"border: 1px solid rgba({border_rgb[0]},{border_rgb[1]},{border_rgb[2]},0.70);"
            "}"
            "QFrame#StatusSelectControl:focus {"
            f"border: 1px solid rgba({border_rgb[0]},{border_rgb[1]},{border_rgb[2]},0.88);"
            "}"
        )
        self._label.setStyleSheet(
            "QLabel#StatusSelectCurrentLabel {"
            f"color: {text};"
            "font-size: 12px;"
            "font-weight: 600;"
            "}"
        )
        self._arrow.setStyleSheet(
            "QLabel#StatusSelectArrow {"
            f"color: {arrow};"
            "font-size: 10px;"
            "font-weight: 700;"
            "}"
        )
        self._control.setCursor(Qt.PointingHandCursor if self.isEnabled() else Qt.ArrowCursor)
