# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Callable, List, Optional, Sequence, Tuple, Union

from PyQt5.QtCore import Qt, QTimer, pyqtSignal
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
from qgis.gui import QgsCheckableComboBox

from ...languages.language_manager import LanguageManager
from ...languages.translation_keys import TranslationKeys
from ...python.workers import FunctionWorker, start_worker
from ...utils.FilterHelpers.FilterHelper import FilterHelper
from ...utils.logger import error
from ...modules.Settings.SettinsUtils.SettingsLogic import SettingsLogic
from ..theme_manager import ThemeManager
from .select_all_checkbox import SelectAllCheckBox


class _SimplePickerControl(QFrame):
    clicked = pyqtSignal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("SimplePickerControl")
        self.setCursor(Qt.PointingHandCursor)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 4, 8, 4)
        layout.setSpacing(8)

        self._label = QLabel("", self)
        self._label.setObjectName("SimplePickerSummary")
        self._label.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self._label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        self._arrow = QLabel("v", self)
        self._arrow.setObjectName("SimplePickerArrow")
        self._arrow.setAttribute(Qt.WA_TransparentForMouseEvents, True)

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
            "QFrame#SimplePickerControl {"
            f"background: {bg}; border: 1px solid {border}; border-radius: 6px; min-height: 22px;"
            "}"
            "QFrame#SimplePickerControl:hover, QFrame#SimplePickerControl:focus {"
            f"background: {hover}; border-color: {accent};"
            "}"
            "QLabel#SimplePickerSummary {"
            f"color: {text}; font-size: 12px; font-weight: 600;"
            "}"
            "QLabel#SimplePickerArrow {"
            f"color: {accent}; font-size: 12px; font-weight: 700;"
            "}"
        )


class _SimplePickerPopup(QWidget):
    def __init__(self, owner: "BaseSingleFilterWidget", *, min_width: int, parent=None) -> None:
        super().__init__(parent, flags=Qt.Popup | Qt.FramelessWindowHint)
        self.setObjectName("SimplePickerPopup")
        self.setAttribute(Qt.WA_DeleteOnClose, True)
        self._owner = owner
        self._min_width = max(260, min_width)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self._frame = QFrame(self)
        self._frame.setObjectName("SimplePickerPopupFrame")
        self._frame.setMinimumWidth(self._min_width)
        self._frame_layout = QVBoxLayout(self._frame)
        self._frame_layout.setContentsMargins(8, 8, 8, 8)
        self._frame_layout.setSpacing(8)
        root.addWidget(self._frame)

        self._apply_style()
        self.refresh()

    def refresh(self) -> None:
        self._clear_layout(self._frame_layout)

        actions = QHBoxLayout()
        actions.setSpacing(6)
        select_all = QPushButton(self._owner._lang.translate(TranslationKeys.SELECT_ALL), self._frame)
        clear = QPushButton(self._owner._lang.translate(TranslationKeys.CLEAR_SELECTION), self._frame)
        for button in (select_all, clear):
            button.setObjectName("SimplePickerActionButton")
            actions.addWidget(button)
        actions.addStretch(1)
        select_all.clicked.connect(self._owner._select_all_options)
        clear.clicked.connect(self._owner._clear_all_options)
        self._frame_layout.addLayout(actions)

        scroll = QScrollArea(self._frame)
        scroll.setObjectName("SimplePickerScroll")
        scroll.setMaximumHeight(320)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        content = QWidget(scroll)
        content.setObjectName("SimplePickerContent")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(6, 6, 6, 6)
        content_layout.setSpacing(4)

        title = QLabel(self._owner._label_text, content)
        title.setObjectName("SimplePickerSectionLabel")
        content_layout.addWidget(title)
        for row, label, value, checked in self._owner._iter_options():
            option = QPushButton(label, content)
            option.setObjectName("SimplePickerOptionRow")
            option.setCheckable(True)
            option.setChecked(checked)
            option.clicked.connect(lambda is_checked=False, index=row: self._on_option_clicked(index, is_checked))
            content_layout.addWidget(option)
        content_layout.addStretch(1)

        scroll.setWidget(content)
        self._frame_layout.addWidget(scroll)

    def _on_option_clicked(self, row: int, checked: bool) -> None:
        self._owner._set_option_checked(row, checked)
        self.refresh()

    def _clear_layout(self, layout) -> None:
        while layout.count():
            item = layout.takeAt(0)
            child_layout = item.layout()
            widget = item.widget()
            if child_layout is not None:
                self._clear_layout(child_layout)
            if widget is not None:
                widget.deleteLater()

    def _apply_style(self) -> None:
        dark = ThemeManager.effective_theme() == "dark"
        if dark:
            frame_bg = "#252932"
            border = "#1f5d5c"
            text = "#c5c5d2"
            muted = "#9aa4b2"
            hover = "#3a3f4b"
            selected = "rgba(9,144,143,0.28)"
            selected_border = "rgb(9,144,143)"
        else:
            frame_bg = "#ffffff"
            border = "#2188ff"
            text = "#24292e"
            muted = "#6a737d"
            hover = "#eaeef2"
            selected = "rgba(33,136,255,0.14)"
            selected_border = "#2188ff"
        self.setStyleSheet(
            "QFrame#SimplePickerPopupFrame {"
            f"background: {frame_bg}; border: 1px solid {border}; border-radius: 8px;"
            "}"
            "QLabel#SimplePickerSectionLabel {"
            f"color: {muted}; font-size: 10px; font-weight: 800; text-transform: uppercase;"
            "}"
            "QPushButton#SimplePickerOptionRow {"
            f"background: transparent; color: {text}; border: 1px solid transparent; border-radius: 6px;"
            "padding: 5px 8px; text-align: left; font-size: 12px; font-weight: 600;"
            "}"
            "QPushButton#SimplePickerOptionRow:hover {"
            f"background: {hover};"
            "}"
            "QPushButton#SimplePickerOptionRow:checked {"
            f"background: {selected}; border-color: {selected_border};"
            "}"
            "QPushButton#SimplePickerActionButton {"
            f"background: {frame_bg}; color: {text}; border: 1px solid rgba(128,128,128,0.30);"
            "border-radius: 5px; padding: 4px 8px; font-size: 11px; font-weight: 700;"
            "}"
            "QPushButton#SimplePickerActionButton:hover {"
            f"border-color: {border};"
            "}"
            "QScrollArea#SimplePickerScroll { background: transparent; border: none; }"
            "QWidget#SimplePickerContent { background: transparent; }"
        )


class BaseSingleFilterWidget(QWidget):
    """Shared base for single-combo filters (status/tags)."""

    selectionChanged = pyqtSignal(list, list)
    loadFinished = pyqtSignal(bool)

    def __init__(
        self,
        module_name: Union[str, object],
        label_text: str,
        object_name: str,
        support_key: str,
        parent: Optional[QWidget] = None,
        *,
        auto_load: bool = True,
        variant: Optional[str] = None,
        settings_logic: Optional[SettingsLogic] = None,
        lang_manager: Optional[LanguageManager] = None,
        selected_ids_loader: Optional[Callable[[], Sequence[str]]] = None,
    ) -> None:
        super().__init__(parent)
        self._module = getattr(module_name, "value", module_name)
        self._lang = lang_manager or LanguageManager()
        self._settings_logic = settings_logic or SettingsLogic()
        self._support_key = support_key
        self._suppress_emit = False
        self._loaded = False
        self._worker = None
        self._worker_thread = None
        self._auto_load = auto_load
        self._suppress_all_cb = False
        self._load_request_id = 0
        self._selected_ids_loader = selected_ids_loader
        self._label_text = label_text
        self._popup: Optional[_SimplePickerPopup] = None

        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 2, 4, 2)
        layout.setSpacing(1)

        self._control = _SimplePickerControl(self)
        self._control.clicked.connect(self._open_picker)
        self._control.setEnabled(False)
        layout.addWidget(self._control, 1)

        self.combo = QgsCheckableComboBox(self)
        self.combo.setObjectName(object_name)
        self.combo.setMaxVisibleItems(12)
        layout.addWidget(self.combo)
        self.combo.setVisible(False)

        ThemeManager.apply_checkable_combo_popup_style(self.combo)

        self.all_cb = SelectAllCheckBox(self)
        self.all_cb.setTristate(True)
        self.all_cb.setObjectName("SelectAllCheckbox")
        self.all_cb.setProperty("kavitroSelectAll", True)
        self.all_cb.setToolTip(self._lang.translate(TranslationKeys.SELECT_ALL))
        self.all_cb.setEnabled(False)
        self.all_cb.stateChanged.connect(self._on_all_cb_state_changed)
        layout.addWidget(self.all_cb)
        self.all_cb.setVisible(False)

        if variant:
            self.all_cb.setProperty("variant", variant)

        self.combo.setToolTip(label_text)
        self.combo.setDefaultText(label_text)


        self.combo.checkedItemsChanged.connect(self._emit_selection_change)  # type: ignore[attr-defined]
        if self._auto_load:
            QTimer.singleShot(0, self.reload)
        self._update_control_summary()

    def retheme(self) -> None:
        ThemeManager.apply_checkable_combo_popup_style(self.combo)
        self._control.apply_style()
        self.style().unpolish(self)
        self.style().polish(self)
        self.all_cb.style().unpolish(self.all_cb)
        self.all_cb.style().polish(self.all_cb)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def reload(self) -> None:
        self._close_popup()
        self._loaded = False
        self._load_request_id += 1
        self.combo.clear()
        self._set_all_cb_state(Qt.Unchecked, enabled=False)
        self.combo.setEnabled(False)
        self._control.setEnabled(False)
        self._update_control_summary()
        self._show_loading_placeholder()
        self._start_async_load()

    def ensure_loaded(self) -> None:
        if not self._loaded:
            self.reload()

    def selected_ids(self) -> List[str]:
        return FilterHelper.selected_ids(self)

    def selected_texts(self) -> List[str]:
        return FilterHelper.selected_texts(self)

    def set_selected_ids(self, ids: Sequence[str], emit: bool = True) -> None:
        FilterHelper.set_selected_ids(self, ids, emit=emit)
        self._update_control_summary()
        self._refresh_popup()

    def is_loaded(self) -> bool:
        return self._loaded

    def is_loading(self) -> bool:
        return self._worker_thread is not None

    def clear_data(self) -> None:
        """Clear combo data to free memory; safe to call on deactivate."""
        try:
            self._close_popup()
            FilterHelper.cancel_pending_load(self, invalidate_request=True)
            self.combo.clear()
            self.combo.setEnabled(False)
            self._control.setEnabled(False)
            self._set_all_cb_state(Qt.Unchecked, enabled=False)
            self._loaded = False
            self._update_control_summary()
        except Exception as exc:
            error(f"[{self.__class__.__name__}] clear_data failed: {exc}")

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _emit_selection_change(self) -> None:
        if self._suppress_emit:
            return
        texts = FilterHelper.selected_texts(self)
        ids = FilterHelper.selected_ids(self)
        self._sync_all_checkbox_state()
        self._update_control_summary()
        self._refresh_popup()
        self.selectionChanged.emit(texts, ids)

    def _show_loading_placeholder(self) -> None:
        loading_text = self._lang.translate(TranslationKeys.LOADING)
        self.combo.addItem(f"{loading_text}…")

    def _start_async_load(self) -> None:
        FilterHelper.cancel_pending_load(self, invalidate_request=False)
        token = self._current_token()
        request_id = self._load_request_id

        worker = FunctionWorker(
            lambda: FilterHelper.get_filter_edges_by_key_and_module(
                self._support_key, self._module
            )
        )
        worker.active_token = token
        worker.finished.connect(
            lambda payload, tok=token, req=request_id: self._handle_load_success(payload, tok, req)
        )
        worker.error.connect(
            lambda message, tok=token, req=request_id: self._handle_load_error(message, tok, req)
        )
        self._worker = worker
        self._worker_thread = start_worker(worker, on_thread_finished=self._cleanup_worker)

    def _handle_load_success(
        self,
        payload: List[Tuple[str, str]],
        token: int | None,
        request_id: int,
    ) -> None:
        if not self._is_widget_alive():
            return
        if request_id != self._load_request_id:
            return
        if not self._is_token_active(token):
            return
        self.combo.clear()
        for label, value in payload:
            self.combo.addItem(label, value)
        ThemeManager.apply_checkable_combo_popup_style(self.combo)
        self.combo.setEnabled(True)
        self._control.setEnabled(True)
        self._loaded = True
        self.all_cb.setEnabled(True)
        if callable(self._selected_ids_loader):
            try:
                saved_ids = self._selected_ids_loader() or []
            except Exception:
                saved_ids = []
        else:
            saved_ids = self._settings_logic.load_module_preference_ids(
                self._module,
                support_key=self._support_key,
            )
        if saved_ids:
            FilterHelper.set_selected_ids(self, list(saved_ids), emit=False)
        self._sync_all_checkbox_state()
        self._update_control_summary()
        self._refresh_popup()
        self.loadFinished.emit(True)

    def _handle_load_error(self, message: str, token: int | None, request_id: int) -> None:
        if not self._is_widget_alive():
            return
        if request_id != self._load_request_id:
            return
        if not self._is_token_active(token):
            return
        self.combo.clear()
        self.combo.addItem(f"{self._lang.translate(TranslationKeys.ERROR)}: {message[:60]}…")
        self.combo.setEnabled(False)
        self._control.setEnabled(False)
        self.all_cb.setEnabled(False)
        self._loaded = False
        self._update_control_summary()
        self.loadFinished.emit(False)

    def _cleanup_worker(self) -> None:
        if not self._is_widget_alive():
            return
        self._worker = None
        self._worker_thread = None

    def _apply_select_all(self, checked: bool) -> None:
        if checked and hasattr(self.combo, "selectAllOptions"):
            self.combo.selectAllOptions()
            return
        if not checked and hasattr(self.combo, "deselectAllOptions"):
            self.combo.deselectAllOptions()
            return

        target_state = Qt.Checked if checked else Qt.Unchecked
        for i in range(self.combo.count()):
            if self.combo.itemData(i) is None:
                continue
            self.combo.setItemCheckState(i, target_state)

    def _on_all_cb_state_changed(self, state: int) -> None:
        if self._suppress_all_cb:
            return
        self._suppress_emit = True
        try:
            self._apply_select_all(state == Qt.Checked)
        finally:
            self._suppress_emit = False
        self._sync_all_checkbox_state()
        texts = FilterHelper.selected_texts(self)
        ids = FilterHelper.selected_ids(self)
        self._update_control_summary()
        self._refresh_popup()
        self.selectionChanged.emit(texts, ids)

    def _open_picker(self) -> None:
        if not self._loaded or not self._control.isEnabled():
            return
        if self._popup is not None:
            try:
                self._popup.close()
            except RuntimeError:
                pass
            self._popup = None
            return
        popup = _SimplePickerPopup(self, min_width=self._control.width(), parent=self)
        popup.destroyed.connect(lambda *_: setattr(self, "_popup", None))
        self._popup = popup
        popup.move(self._control.mapToGlobal(self._control.rect().bottomLeft()))
        popup.show()

    def _iter_options(self) -> List[Tuple[int, str, str, bool]]:
        options: List[Tuple[int, str, str, bool]] = []
        for row in range(self.combo.count()):
            value = self.combo.itemData(row)
            if value is None:
                continue
            options.append(
                (
                    row,
                    self.combo.itemText(row),
                    str(value),
                    self.combo.itemCheckState(row) == Qt.Checked,
                )
            )
        return options

    def _set_option_checked(self, row: int, checked: bool) -> None:
        if row < 0 or row >= self.combo.count():
            return
        if self.combo.itemData(row) is None:
            return
        self.combo.setItemCheckState(row, Qt.Checked if checked else Qt.Unchecked)

    def _select_all_options(self) -> None:
        self._on_all_cb_state_changed(Qt.Checked)
        self._refresh_popup()

    def _clear_all_options(self) -> None:
        self._on_all_cb_state_changed(Qt.Unchecked)
        self._refresh_popup()

    def _update_control_summary(self) -> None:
        if not hasattr(self, "_control"):
            return
        selected = FilterHelper.selected_texts(self)
        if not selected:
            summary = self._label_text
        elif len(selected) <= 2:
            summary = ", ".join(selected)
        else:
            summary = f"{len(selected)} {self._label_text.lower()}"
        self._control.set_summary(summary)

    def _refresh_popup(self) -> None:
        popup = self._popup
        if popup is None:
            return
        try:
            popup.refresh()
        except RuntimeError:
            self._popup = None

    def _close_popup(self) -> None:
        popup = self._popup
        if popup is None:
            return
        self._popup = None
        try:
            popup.close()
        except RuntimeError:
            pass

    def _sync_all_checkbox_state(self) -> None:
        total = 0
        checked = 0
        for i in range(self.combo.count()):
            val = self.combo.itemData(i)
            if val is None:
                continue
            total += 1
            if self.combo.itemCheckState(i) == Qt.Checked:
                checked += 1
        if total == 0 or checked == 0:
            state = Qt.Unchecked
        elif checked == total:
            state = Qt.Checked
        else:
            state = Qt.PartiallyChecked
        self._set_all_cb_state(state)

    def _set_all_cb_state(self, state: Qt.CheckState, *, enabled: bool | None = None) -> None:
        self._suppress_all_cb = True
        try:
            self.all_cb.setCheckState(state)
            if enabled is not None:
                self.all_cb.setEnabled(enabled)
        finally:
            self._suppress_all_cb = False

    def _current_token(self) -> int | None:
        if not self._is_widget_alive():
            return None
        try:
            parent = self.parent()
        except RuntimeError:
            return None
        while parent is not None:
            if hasattr(parent, "_active_token"):
                return getattr(parent, "_active_token", None)
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
            if hasattr(parent, "_active_token"):
                return bool(getattr(parent, "_activated", False)) and token == getattr(parent, "_active_token", None)
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

