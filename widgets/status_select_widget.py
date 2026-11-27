"""Status select controls with colour dots: StatusSelectWidget picks one status,
StatusMultiSelectWidget several. Their popups are in status_select_popups."""
from __future__ import annotations

from typing import Iterable, Optional

from qgis.PyQt.QtCore import Qt, pyqtSignal
from qgis.PyQt.QtWidgets import QFrame, QHBoxLayout, QLabel, QSizePolicy, QWidget

from ..languages.translation_keys import TranslationKeys
from ..ui.window_state.popup_helpers import PopupHelpers
from ..utils.status_color_helper import StatusColorHelper
from .select_arrow import SelectArrow
from .status_select_parts import (
    FALLBACK_COLOR,
    ClickableFrame,
    is_dark_theme,
    normalize_status_color,
    normalize_status_option,
    resolve_lang,
    unique_status_options,
)
from .status_select_popups import StatusMultiSelectPopup, StatusSelectPopup


class _StatusControlBase(QWidget):
    """The clickable control (dot, label, arrow) and opening its popup below it."""

    def __init__(self, parent: Optional[QWidget], *, object_name: str, placeholder: Optional[str]) -> None:
        super().__init__(parent)
        self.setObjectName(object_name)
        self._lang = resolve_lang()
        self._placeholder = str(placeholder or self._lang.translate(TranslationKeys.SELECT))
        self._options: list[dict[str, object]] = []
        self._popup: Optional[QWidget] = None
        self._control_min_height = 24

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._control = ClickableFrame(self)
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

        self._arrow = SelectArrow(self._control)
        control_layout.addWidget(self._arrow, 0, Qt.AlignVCenter)

        layout.addWidget(self._control)
        self.setFocusProxy(self._control)

    # --- what a subclass provides ---
    def _refresh(self) -> None:
        raise NotImplementedError

    def _create_popup(self, min_width: int) -> QWidget:
        raise NotImplementedError

    # --- shared ---
    def count(self) -> int:
        return len(self._options)

    def retheme(self) -> None:
        self._refresh()

    def setEnabled(self, enabled: bool) -> None:  # noqa: N802 - Qt override
        super().setEnabled(enabled)
        self._control.setEnabled(enabled)
        self._refresh()

    def _toggle_popup(self) -> None:
        if not self.isEnabled() or not self._options:
            return
        if self._popup is not None and self._popup.isVisible():
            self._close_popup()
            return
        self._show_popup()

    def _show_popup(self) -> None:
        self._close_popup()
        popup = self._create_popup(max(self.width(), self._control.width()))
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

    def _apply_current_look(self, *, label: str, tooltip: str, color: str, has_selection: bool,
                            plain_border: Optional[str] = None) -> None:
        """Label, tooltip, dot and control colours. Without a selection the border is
        plain_border when given, else the status colour."""
        self._label.setText(label)
        self.setToolTip(tooltip)
        self._control.setToolTip(tooltip)
        self._dot.setStyleSheet(
            "QFrame#StatusSelectCurrentDot {"
            f"background-color: {color};"
            f"border: 1px solid {color};"
            "border-radius: 5px;"
            "}"
        )
        dark_theme = is_dark_theme()
        bg_rgb, _fg_rgb, border_rgb = StatusColorHelper.upgrade_status_color(color)

        if not self.isEnabled():
            control_bg = "#f2f4f7" if not dark_theme else "#20252b"
            border = "rgba(98,108,120,0.36)"
            text = "rgba(98,108,120,0.85)" if not dark_theme else "rgba(170,178,188,0.58)"
        else:
            control_bg = (
                f"rgba({bg_rgb[0]},{bg_rgb[1]},{bg_rgb[2]},0.12)"
                if has_selection
                else ("#ffffff" if not dark_theme else "#27313a")
            )
            border = (
                f"rgba({border_rgb[0]},{border_rgb[1]},{border_rgb[2]},0.48)"
                if has_selection or plain_border is None
                else plain_border
            )
            text = "#27313a" if not dark_theme else "#f1f5f9"

        self._control.setStyleSheet(
            "QFrame#StatusSelectControl {"
            f"background-color: {control_bg};"
            f"border: 1px solid {border};"
            "border-radius: 6px;"
            f"min-height: {self._control_min_height}px;"
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
        self._control.setCursor(Qt.PointingHandCursor if self.isEnabled() else Qt.ArrowCursor)


class StatusSelectWidget(_StatusControlBase):
    """Status-only select control with a custom color-dot popup."""

    currentChanged = pyqtSignal(str, str)

    def __init__(
        self,
        parent: Optional[QWidget] = None,
        *,
        placeholder: Optional[str] = None,
    ) -> None:
        super().__init__(parent, object_name="StatusSelectWidget", placeholder=placeholder)
        self._selected_id = ""
        self._refresh()

    def clear(self) -> None:
        self._options = []
        self._selected_id = ""
        self._close_popup()
        self._refresh()

    def set_control_height(self, height: int) -> None:
        # The control's style owns its minimum height and overrides setFixedHeight; 2 px is the border.
        self._control_min_height = int(height) - 2
        self._refresh()

    def set_options(self, options: Iterable[dict[str, object]], *, selected_id: str = "") -> None:
        self._options = unique_status_options(options)
        self._selected_id = self._resolve_initial_selection(selected_id)
        self.setEnabled(bool(self._options))
        self._refresh()

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
        self._refresh()
        if emit:
            self.currentChanged.emit(self.current_status_id(), self.current_status_label())
        return True

    def _create_popup(self, min_width: int) -> QWidget:
        popup = StatusSelectPopup(
            self._options,
            selected_id=self._selected_id,
            min_width=max(min_width, StatusSelectPopup.MIN_WIDTH),
            parent=self.window(),
        )
        popup.optionSelected.connect(self._select_option)
        return popup

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

    def _refresh(self) -> None:
        option = self.current_option()
        current = option or {}
        label = str(current.get("name") or self._placeholder).strip() or self._placeholder
        description = str(current.get("description") or "").strip()
        self._apply_current_look(
            label=label,
            tooltip=description or label,
            color=normalize_status_color(current.get("color")),
            has_selection=bool(option),
        )

    # Kept for callers that normalize like this control does.
    _normalize_option = staticmethod(normalize_status_option)
    _normalize_color = staticmethod(normalize_status_color)


class StatusMultiSelectWidget(_StatusControlBase):
    """Status-only multi-select control with grouped color-dot popup actions."""

    selectionChanged = pyqtSignal(list, list)

    def __init__(
        self,
        parent: Optional[QWidget] = None,
        *,
        placeholder: Optional[str] = None,
    ) -> None:
        super().__init__(parent, object_name="StatusMultiSelectWidget", placeholder=placeholder)
        self._selected_ids: list[str] = []
        self._display_override = ""
        self.setMinimumWidth(210)
        self.setMaximumWidth(360)
        self._refresh()

    def clear(self) -> None:
        self._options = []
        self._selected_ids = []
        self._display_override = ""
        self._close_popup()
        self._refresh()

    def set_options(self, options: Iterable[dict[str, object]], *, selected_ids: Iterable[str] = ()) -> None:
        self._options = unique_status_options(options)
        self._display_override = ""
        self.set_selected_ids(selected_ids, emit=False)
        self.setEnabled(bool(self._options))
        self._refresh()

    def set_loading(self, text: str) -> None:
        self._show_disabled_text(text)

    def set_error(self, text: str) -> None:
        self._show_disabled_text(text)

    def _show_disabled_text(self, text: str) -> None:
        self._options = []
        self._selected_ids = []
        self._display_override = str(text or "").strip() or self._placeholder
        self._close_popup()
        self.setEnabled(False)
        self._refresh()

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
        self._refresh()
        if self._popup is not None and self._popup.isVisible():
            self._close_popup()
            self._show_popup()
        if emit:
            self.selectionChanged.emit(self.selected_texts(), self.selected_ids())

    def _create_popup(self, min_width: int) -> QWidget:
        popup = StatusMultiSelectPopup(
            self._options,
            selected_ids=self._selected_ids,
            min_width=max(min_width, StatusMultiSelectPopup.MIN_WIDTH),
            parent=self.window(),
        )
        popup.selectionChanged.connect(self._on_popup_selection_changed)
        return popup

    def _on_popup_selection_changed(self, texts: list, ids: list) -> None:
        self._selected_ids = [str(value or "").strip() for value in (ids or []) if str(value or "").strip()]
        self._display_override = ""
        self._refresh()
        self.selectionChanged.emit(list(texts or []), self.selected_ids())

    def _refresh(self) -> None:
        texts = self.selected_texts()
        if self._display_override:
            label = self._display_override
        elif texts:
            label = ", ".join(texts)
        else:
            label = self._placeholder

        self._dot.setVisible(bool(texts))
        self._apply_current_look(
            label=label,
            tooltip=", ".join(texts) if texts else label,
            color=self._current_color(),
            has_selection=bool(texts),
            plain_border="rgba(15,23,42,0.18)",
        )

    def _current_color(self) -> str:
        selected = self.selected_ids()
        if not selected:
            return FALLBACK_COLOR
        first_id = selected[0]
        for option in self._options:
            if str(option.get("id") or "").strip() == first_id:
                return normalize_status_color(option.get("color"))
        return FALLBACK_COLOR
