"""Parts the filter widgets share: loading state, the request token lookup and the picker's control and popup."""
from __future__ import annotations

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import QFrame, QHBoxLayout, QLabel, QSizePolicy, QVBoxLayout, QWidget

from ...python.workers import FunctionWorker, start_worker
from ...utils.FilterHelpers.FilterHelper import FilterHelper
from ..select_arrow import SelectArrow
from ..theme_manager import ThemeManager


class FilterLoadingMixin:
    """For a QWidget that fills itself in a worker thread. Goes before QWidget in the bases.

    The widget sets `_loaded`, `_worker`, `_worker_thread` and `_load_request_id`, and has `reload`, `_fetch_options`,
    `_handle_load_success` and `_handle_load_error`.
    """

    def ensure_loaded(self) -> None:
        if not self._loaded:
            self.reload()

    def is_loaded(self) -> bool:
        return self._loaded

    def is_loading(self) -> bool:
        return self._worker_thread is not None

    def _cleanup_worker(self) -> None:
        if not self._is_widget_alive():
            return
        self._worker = None
        self._worker_thread = None

    def _start_async_load(self) -> None:
        FilterHelper.cancel_pending_load(self, invalidate_request=False)
        token = self._current_token()
        request_id = self._load_request_id

        worker = FunctionWorker(self._fetch_options)
        worker.finished.connect(
            lambda payload, tok=token, req=request_id: self._handle_load_success(payload, tok, req)
        )
        worker.error.connect(
            lambda message, tok=token, req=request_id: self._handle_load_error(message, tok, req)
        )
        self._worker = worker
        self._worker_thread = start_worker(worker, on_thread_finished=self._cleanup_worker)

    def _is_response_current(self, token: int | None, request_id: int) -> bool:
        return request_id == self._load_request_id and self._is_token_active(token)

    def _current_token(self) -> int | None:
        if not self._is_widget_alive():
            return None
        try:
            parent = self.parent()
        except RuntimeError:
            return None
        while parent is not None:
            if hasattr(parent, "_active_token"):
                return parent._active_token
            parent = parent.parent()
        return None

    def _is_token_active(self, token: int | None) -> bool:
        if not self._is_widget_alive():
            return False
        if token is None:
            return True
        try:
            parent = self.parent()
        except RuntimeError:
            return False
        while parent is not None:
            if hasattr(parent, "is_token_active"):
                try:
                    return bool(parent.is_token_active(token))
                except Exception:
                    return False
            parent = parent.parent()
        return True

    def _is_widget_alive(self) -> bool:
        try:
            import sip
        except Exception:
            sip = None
        try:
            return not bool(sip and sip.isdeleted(self))
        except RuntimeError:
            return False


class PickerFilterMixin(FilterLoadingMixin):
    """A filter with a popup in `_popup`, a select-all box in `all_cb` and its options in `_options_combo`.

    The closed picker is `_control`; `_create_popup` builds the open list.
    """

    def _create_popup(self) -> "PickerPopupBase":
        raise NotImplementedError

    def _open_picker(self) -> None:
        """A click on the control opens the list, or closes it when it is already open."""
        if not self._loaded or not self._control.isEnabled():
            return
        if self._popup is not None:
            self._close_popup()
            return
        popup = self._create_popup()
        self._popup = popup
        popup.destroyed.connect(lambda *_: setattr(self, "_popup", None))
        popup.move(self._control.mapToGlobal(self._control.rect().bottomLeft()))
        popup.show()

    def _close_popup(self) -> None:
        popup = self._popup
        if popup is None:
            return
        self._popup = None
        try:
            popup.close()
        except RuntimeError:
            pass

    def _show_summary(self, label: str, selected: list[str], prefix: str = "") -> None:
        """Up to two picks by name, more as a count; `prefix` (the chosen groups) goes in front."""
        if not selected:
            text = label
        elif len(selected) <= 2:
            text = ", ".join(selected)
        else:
            text = f"{len(selected)} {label.lower()}"
        self._control.set_summary(f"{prefix}: {text}" if prefix else text)

    def _set_all_cb_state(self, state: Qt.CheckState, *, enabled: bool | None = None) -> None:
        self._suppress_all_cb = True
        try:
            self.all_cb.setCheckState(state)
            if enabled is not None:
                self.all_cb.setEnabled(enabled)
        finally:
            self._suppress_all_cb = False

    def _refresh_popup(self) -> None:
        popup = self._popup
        if popup is None:
            return
        try:
            popup.refresh()
        except RuntimeError:
            self._popup = None

    def _sync_all_checkbox_state(self) -> None:
        total = 0
        checked = 0
        for i in range(self._options_combo.count()):
            val = self._options_combo.itemData(i)
            if val is None:
                continue
            total += 1
            if self._options_combo.itemCheckState(i) == Qt.Checked:
                checked += 1
        if total == 0 or checked == 0:
            state = Qt.Unchecked
        elif checked == total:
            state = Qt.Checked
        else:
            state = Qt.PartiallyChecked
        self._set_all_cb_state(state)

    def _apply_select_all(self, checked: bool) -> None:
        if checked and hasattr(self._options_combo, "selectAllOptions"):
            self._options_combo.selectAllOptions()
            return
        if not checked and hasattr(self._options_combo, "deselectAllOptions"):
            self._options_combo.deselectAllOptions()
            return

        target_state = Qt.Checked if checked else Qt.Unchecked
        for i in range(self._options_combo.count()):
            if self._options_combo.itemData(i) is None:
                continue
            self._options_combo.setItemCheckState(i, target_state)


class PickerControlBase(QFrame):
    """The closed picker: a summary in `_label` that opens the list when clicked. A subclass names its two parts."""

    CONTROL_NAME: str
    SUMMARY_NAME: str

    clicked = pyqtSignal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName(self.CONTROL_NAME)
        self.setCursor(Qt.PointingHandCursor)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 4, 8, 4)
        layout.setSpacing(8)

        self._label = QLabel("", self)
        self._label.setObjectName(self.SUMMARY_NAME)
        self._label.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self._label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        self._arrow = SelectArrow(self)

        layout.addWidget(self._label, 1)
        layout.addWidget(self._arrow, 0, Qt.AlignVCenter)
        self.apply_style()

    def set_summary(self, text: str) -> None:
        self._label.setText(text)

    def mousePressEvent(self, event) -> None:  # noqa: N802
        if event.button() == Qt.LeftButton and self.isEnabled():
            self.clicked.emit()
            event.accept()
            return
        super().mousePressEvent(event)

    def keyPressEvent(self, event) -> None:  # noqa: N802
        if event.key() in (Qt.Key_Return, Qt.Key_Enter, Qt.Key_Space):
            self.clicked.emit()
            event.accept()
            return
        super().keyPressEvent(event)

    def apply_style(self) -> None:
        dark = ThemeManager.effective_theme() == "dark"
        if dark:
            bg = "#303a42"
            hover = "#2e2f38"
            border = "#4d4d4d"
            accent = "#1f5d5c"
            text = "#c5c5d2"
        else:
            bg = "#ffffff"
            hover = "#f9fafb"
            border = "#d7dee5"
            accent = "#2188ff"
            text = "#24292e"
        self.setStyleSheet(
            f"QFrame#{self.CONTROL_NAME} {{"
            f"background: {bg}; border: 1px solid {border}; border-radius: 6px; min-height: 22px;"
            "}"
            f"QFrame#{self.CONTROL_NAME}:hover, QFrame#{self.CONTROL_NAME}:focus {{"
            f"background: {hover}; border-color: {accent};"
            "}"
            f"QLabel#{self.SUMMARY_NAME} {{"
            f"color: {text}; font-size: 12px; font-weight: 600;"
            "}"
        )


class PickerPopupBase(QWidget):
    """The picker's open list: a frameless popup holding one frame, which `refresh` fills.

    Every object name starts with NAME. ROW_NAMES are the checkable rows; ACTION_BACKGROUND is the color the action
    buttons take; `_extra_style` adds rules for parts only one popup has.
    """

    NAME: str
    MIN_WIDTH: int
    ROW_NAMES: tuple[str, ...]
    ACTION_BACKGROUND = "frame_bg"

    def __init__(self, owner, *, min_width: int, parent=None) -> None:
        super().__init__(parent, flags=Qt.Popup | Qt.FramelessWindowHint)
        self.setObjectName(f"{self.NAME}Popup")
        self.setAttribute(Qt.WA_DeleteOnClose, True)
        self._owner = owner
        self._min_width = max(self.MIN_WIDTH, min_width)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self._frame = QFrame(self)
        self._frame.setObjectName(f"{self.NAME}PopupFrame")
        self._frame.setMinimumWidth(self._min_width)
        self._frame_layout = QVBoxLayout(self._frame)
        self._frame_layout.setContentsMargins(8, 8, 8, 8)
        self._frame_layout.setSpacing(8)
        root.addWidget(self._frame)

        self._apply_style()
        self.refresh()

    def refresh(self) -> None:
        raise NotImplementedError

    def _apply_style(self) -> None:
        if ThemeManager.effective_theme() == "dark":
            colors = {
                "frame_bg": "#252932",
                "panel_bg": "#2e2f38",
                "border": "#1f5d5c",
                "text": "#c5c5d2",
                "muted": "#9aa4b2",
                "hover": "#3a3f4b",
                "selected": "rgba(9,144,143,0.28)",
                "selected_border": "rgb(9,144,143)",
            }
        else:
            colors = {
                "frame_bg": "#ffffff",
                "panel_bg": "#f9fafb",
                "border": "#2188ff",
                "text": "#24292e",
                "muted": "#6a737d",
                "hover": "#eaeef2",
                "selected": "rgba(33,136,255,0.14)",
                "selected_border": "#2188ff",
            }
        name = self.NAME
        rows = [f"QPushButton#{name}{row}" for row in self.ROW_NAMES]
        self.setStyleSheet(
            f"QFrame#{name}PopupFrame {{"
            f"background: {colors['frame_bg']}; border: 1px solid {colors['border']}; border-radius: 8px;"
            "}"
            f"QLabel#{name}SectionLabel {{"
            f"color: {colors['muted']}; font-size: 10px; font-weight: 800; text-transform: uppercase;"
            "}"
            f"{', '.join(rows)} {{"
            f"background: transparent; color: {colors['text']}; border: 1px solid transparent; border-radius: 6px;"
            "padding: 5px 8px; text-align: left; font-size: 12px; font-weight: 600;"
            "}"
            f"{', '.join(row + ':hover' for row in rows)} {{"
            f"background: {colors['hover']};"
            "}"
            f"{', '.join(row + ':checked' for row in rows)} {{"
            f"background: {colors['selected']}; border-color: {colors['selected_border']};"
            "}"
            f"QPushButton#{name}ActionButton {{"
            f"background: {colors[self.ACTION_BACKGROUND]}; color: {colors['text']};"
            "border: 1px solid rgba(128,128,128,0.30); border-radius: 5px; padding: 4px 8px; font-size: 11px;"
            "font-weight: 700;"
            "}"
            f"QPushButton#{name}ActionButton:hover {{"
            f"border-color: {colors['border']};"
            "}"
            f"QScrollArea#{name}Scroll {{ background: transparent; border: none; }}"
            f"QWidget#{name}Content {{ background: transparent; }}"
            + self._extra_style(colors)
        )

    def _extra_style(self, colors: dict[str, str]) -> str:
        return ""

    def _clear_layout(self, layout) -> None:
        while layout.count():
            item = layout.takeAt(0)
            child_layout = item.layout()
            widget = item.widget()
            if child_layout is not None:
                self._clear_layout(child_layout)
            if widget is not None:
                widget.deleteLater()
