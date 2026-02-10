# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import List, Optional, Sequence, Tuple, Union

from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtWidgets import QCheckBox, QHBoxLayout, QWidget
from qgis.gui import QgsCheckableComboBox

from ...languages.language_manager import LanguageManager
from ...languages.translation_keys import TranslationKeys
from ...python.workers import FunctionWorker, start_worker
from ...utils.FilterHelpers.FilterHelper import FilterHelper
from ...modules.Settings.SettinsUtils.SettingsLogic import SettingsLogic
from ...Logs.switch_logger import SwitchLogger


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

        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 2, 4, 2)
        layout.setSpacing(1)

        self.combo = QgsCheckableComboBox(self)
        self.combo.setObjectName(object_name)
        self.combo.setMaxVisibleItems(12)
        layout.addWidget(self.combo)

        self.all_cb = SelectAllCheckBox(self)
        self.all_cb.setTristate(True)
        self.all_cb.setObjectName("SelectAllCheckbox")
        self.all_cb.setToolTip(self._lang.translate(TranslationKeys.SELECT_ALL))
        self.all_cb.setEnabled(False)
        self.all_cb.stateChanged.connect(self._on_all_cb_state_changed)
        layout.addWidget(self.all_cb)

        if variant:
            self.all_cb.setProperty("variant", variant)

        self.combo.setToolTip(label_text)
        self.combo.setDefaultText(label_text)


        self.combo.checkedItemsChanged.connect(self._emit_selection_change)  # type: ignore[attr-defined]
        if self._auto_load:
            QTimer.singleShot(0, self.reload)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def reload(self) -> None:
        self._loaded = False
        self._load_request_id += 1
        self.combo.clear()
        self._set_all_cb_state(Qt.Unchecked, enabled=False)
        self.combo.setEnabled(False)
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

    def is_loaded(self) -> bool:
        return self._loaded

    def is_loading(self) -> bool:
        return self._worker_thread is not None

    def clear_data(self) -> None:
        """Clear combo data to free memory; safe to call on deactivate."""
        try:
            FilterHelper.cancel_pending_load(self, invalidate_request=True)
            self.combo.clear()
            self.combo.setEnabled(False)
            self._set_all_cb_state(Qt.Unchecked, enabled=False)
            self._loaded = False
        except Exception as exc:
            print(f"[{self.__class__.__name__}] clear_data failed: {exc}")

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _emit_selection_change(self) -> None:
        if self._suppress_emit:
            return
        texts = FilterHelper.selected_texts(self)
        ids = FilterHelper.selected_ids(self)
        self._sync_all_checkbox_state()
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
        if request_id != self._load_request_id:
            return
        if not self._is_token_active(token):
            SwitchLogger.log(
                "filter_ignored_inactive_token",
                module=str(self._module),
                extra={"token": token},
            )
            return
        self.combo.clear()
        for label, value in payload:
            self.combo.addItem(label, value)
        self.combo.setEnabled(True)
        self._loaded = True
        self.all_cb.setEnabled(True)
        saved_ids = self._settings_logic.load_module_preference_ids(
            self._module,
            support_key=self._support_key,
        )
        if saved_ids:
            FilterHelper.set_selected_ids(self, list(saved_ids), emit=False)
        self._sync_all_checkbox_state()
        self.loadFinished.emit(True)

    def _handle_load_error(self, message: str, token: int | None, request_id: int) -> None:
        if request_id != self._load_request_id:
            return
        if not self._is_token_active(token):
            SwitchLogger.log(
                "filter_ignored_inactive_token",
                module=str(self._module),
                extra={"token": token},
            )
            return
        self.combo.clear()
        self.combo.addItem(f"{self._lang.translate(TranslationKeys.ERROR)}: {message[:60]}…")
        self.combo.setEnabled(False)
        self.all_cb.setEnabled(False)
        self._loaded = False
        self.loadFinished.emit(False)

    def _cleanup_worker(self) -> None:
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
        self.selectionChanged.emit(texts, ids)

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
        parent = self.parent()
        while parent is not None:
            if hasattr(parent, "_active_token"):
                return getattr(parent, "_active_token", None)
            parent = parent.parent()
        return None

    def _is_token_active(self, token: int | None) -> bool:
        if token is None:
            return True
        parent = self.parent()
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


class SelectAllCheckBox(QCheckBox):
    """Tri-state checkbox that never allows user-clicked PartiallyChecked state."""

    def nextCheckState(self) -> None:  # type: ignore[override]
        current = self.checkState()
        if current == Qt.Checked:
            self.setCheckState(Qt.Unchecked)
        else:
            self.setCheckState(Qt.Checked)
