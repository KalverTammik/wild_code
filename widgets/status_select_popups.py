"""The popups of the status select controls: one pick, or several with select all / clear."""
from __future__ import annotations

from typing import Iterable

from qgis.PyQt.QtCore import Qt, pyqtSignal
from qgis.PyQt.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QScrollArea, QVBoxLayout, QWidget

from ..languages.translation_keys import TranslationKeys
from .status_select_parts import (
    StatusOptionRow,
    group_status_options,
    is_dark_theme,
    resolve_lang,
    section_title,
    status_scroll_style,
)

_POPUP_STYLE_DARK = (
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
_POPUP_STYLE_LIGHT = (
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
_ACTION_STYLE_DARK = (
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
_ACTION_STYLE_LIGHT = (
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


class _StatusPopupBase(QWidget):
    """A frameless popup listing the options in OPEN / CLOSED / other sections.

    A subclass sets its selection state, then calls _build; it says which rows start
    selected and what a row click does.
    """

    MAX_HEIGHT = 286
    MIN_WIDTH = 210
    FRAME_SPACING = 0

    def __init__(self, options: Iterable[dict[str, object]], *, object_name: str, parent=None):
        super().__init__(parent, flags=Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint)
        self.setObjectName(object_name)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, True)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self._lang = resolve_lang()
        self._dark_theme = is_dark_theme()
        self._options = [dict(option or {}) for option in (options or [])]

    def _build(self, min_width: int) -> None:
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
        frame_layout.setSpacing(self.FRAME_SPACING)
        self._add_header(frame, frame_layout)

        scroll = QScrollArea(frame)
        scroll.setObjectName("StatusSelectScroll")
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setStyleSheet(status_scroll_style(self._dark_theme))

        content = QWidget(scroll)
        content.setObjectName("StatusSelectContent")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(2)

        for section_type, section_options in group_status_options(self._options).items():
            section_label = QLabel(section_title(self._lang, section_type), content)
            section_label.setObjectName("StatusSelectSectionLabel")
            section_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
            content_layout.addWidget(section_label)

            for option in section_options:
                status_id = str(option.get("id") or "").strip()
                row = StatusOptionRow(
                    option,
                    selected=self._starts_selected(status_id),
                    dark_theme=self._dark_theme,
                    parent=content,
                )
                self._connect_row(row, status_id)
                content_layout.addWidget(row)

        content_layout.addSpacing(2)
        scroll.setWidget(content)
        content.adjustSize()
        scroll.setFixedHeight(min(self.MAX_HEIGHT, max(42, content.sizeHint().height() + 2)))
        frame_layout.addWidget(scroll)
        root.addWidget(frame)

    def _popup_style(self) -> str:
        return _POPUP_STYLE_DARK if self._dark_theme else _POPUP_STYLE_LIGHT

    def _add_header(self, frame: QFrame, frame_layout: QVBoxLayout) -> None:
        """Widgets above the option list; none by default."""

    def _starts_selected(self, status_id: str) -> bool:
        raise NotImplementedError

    def _connect_row(self, row: StatusOptionRow, status_id: str) -> None:
        raise NotImplementedError


class StatusSelectPopup(_StatusPopupBase):
    optionSelected = pyqtSignal(object)

    def __init__(self, options, *, selected_id: str, min_width: int, parent=None):
        super().__init__(options, object_name="StatusSelectPopup", parent=parent)
        self._selected_id = str(selected_id or "").strip()
        self._build(min_width)

    def _starts_selected(self, status_id: str) -> bool:
        return status_id == self._selected_id

    def _connect_row(self, row: StatusOptionRow, status_id: str) -> None:
        row.clicked.connect(self.optionSelected.emit)


class StatusMultiSelectPopup(_StatusPopupBase):
    selectionChanged = pyqtSignal(list, list)

    MAX_HEIGHT = 320
    MIN_WIDTH = 230
    FRAME_SPACING = 4

    def __init__(self, options, *, selected_ids: Iterable[str], min_width: int, parent=None):
        super().__init__(options, object_name="StatusMultiSelectPopup", parent=parent)
        self._selected_ids = {str(value or "").strip() for value in (selected_ids or []) if str(value or "").strip()}
        self._row_by_id: dict[str, StatusOptionRow] = {}
        self._build(min_width)
        self._sync_action_state()

    def _popup_style(self) -> str:
        return super()._popup_style() + (_ACTION_STYLE_DARK if self._dark_theme else _ACTION_STYLE_LIGHT)

    def _add_header(self, frame: QFrame, frame_layout: QVBoxLayout) -> None:
        actions = QFrame(frame)
        actions.setObjectName("StatusSelectActionRow")
        actions_layout = QHBoxLayout(actions)
        actions_layout.setContentsMargins(6, 3, 6, 5)
        actions_layout.setSpacing(6)

        self._select_all_btn = QPushButton(self._lang.translate(TranslationKeys.SELECT_ALL), actions)
        self._select_all_btn.setObjectName("StatusSelectActionButton")
        self._select_all_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._select_all_btn.clicked.connect(self._select_all)
        actions_layout.addWidget(self._select_all_btn)

        self._clear_btn = QPushButton(self._lang.translate(TranslationKeys.CLEAR_SELECTION), actions)
        self._clear_btn.setObjectName("StatusSelectActionButton")
        self._clear_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._clear_btn.clicked.connect(self._clear_selection)
        actions_layout.addWidget(self._clear_btn)
        frame_layout.addWidget(actions)

    def _starts_selected(self, status_id: str) -> bool:
        return status_id in self._selected_ids

    def _connect_row(self, row: StatusOptionRow, status_id: str) -> None:
        row.clicked.connect(self._toggle_option)
        if status_id:
            self._row_by_id[status_id] = row

    def _option_ids(self) -> list[str]:
        return [str(option.get("id") or "").strip() for option in self._options if str(option.get("id") or "").strip()]

    def _toggle_option(self, option: dict[str, object]) -> None:
        status_id = str((option or {}).get("id") or "").strip()
        if not status_id:
            return
        if status_id in self._selected_ids:
            self._selected_ids.remove(status_id)
        else:
            self._selected_ids.add(status_id)
        self._selection_changed()

    def _select_all(self) -> None:
        self._selected_ids = set(self._option_ids())
        self._selection_changed()

    def _clear_selection(self) -> None:
        if not self._selected_ids:
            return
        self._selected_ids.clear()
        self._selection_changed()

    def _selection_changed(self) -> None:
        for status_id, row in self._row_by_id.items():
            row.set_selected(status_id in self._selected_ids)
        self._sync_action_state()
        ids = [status_id for status_id in self._option_ids() if status_id in self._selected_ids]
        texts = [
            str(option.get("name") or "").strip()
            for option in self._options
            if str(option.get("id") or "").strip() in set(ids) and str(option.get("name") or "").strip()
        ]
        self.selectionChanged.emit(texts, ids)

    def _sync_action_state(self) -> None:
        option_ids = self._option_ids()
        selected_count = sum(1 for status_id in option_ids if status_id in self._selected_ids)
        self._select_all_btn.setEnabled(bool(option_ids) and selected_count != len(option_ids))
        self._clear_btn.setEnabled(selected_count > 0)
