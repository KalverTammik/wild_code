# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Dict, List, Optional, Sequence

from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtWidgets import QCheckBox, QHBoxLayout, QWidget
from qgis.gui import QgsCheckableComboBox

from ...languages.language_manager import LanguageManager
from ...languages.translation_keys import TranslationKeys
from ...python.workers import FunctionWorker, start_worker
from ...utils.url_manager import ModuleSupports
from ...utils.FilterHelpers.FilterHelper import FilterHelper
from ...modules.Settings.SettinsUtils.SettingsLogic import SettingsLogic
from ...Logs.switch_logger import SwitchLogger


class TypeFilterWidget(QWidget):
    """Simple group/type multi-select without shared base class."""

    selectionChanged = pyqtSignal(list, list)
    loadFinished = pyqtSignal(bool)

    def __init__(
        self,
        module_name: str,
        parent: Optional[QWidget] = None,
        *,
        auto_load: bool = True,
        settings_logic: Optional[SettingsLogic] = None,
    ) -> None:
        super().__init__(parent)
        self._module = module_name
        self._lang = LanguageManager()
        self._group_map: Dict[str, List[str]] = {}
        self._suppress_group_emit = False
        self._suppress_type_emit = False
        self._loaded = False
        self._worker = None
        self._worker_thread = None
        self._pending_type_ids: List[str] = []
        self._auto_load = auto_load
        self._settings_logic = settings_logic or SettingsLogic()
        self._load_request_id = 0
        self._suppress_all_cb = False

        layout = QHBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(2)

        self.group_combo = QgsCheckableComboBox(self)
        self.group_combo.setObjectName("GroupFilterCombo")
        layout.addWidget(self.group_combo)

        self.type_combo = QgsCheckableComboBox(self)
        self.type_combo.setObjectName("TypeFilterCombo")
        layout.addWidget(self.type_combo)

        self.all_cb = SelectAllCheckBox(self)
        self.all_cb.setTristate(True)
        self.all_cb.setObjectName("SelectAllCheckbox")
        self.all_cb.setToolTip(self._lang.translate(TranslationKeys.SELECT_ALL))
        self.all_cb.setProperty("variant", "type-filter")
        self.all_cb.setEnabled(False)
        self.all_cb.stateChanged.connect(self._on_all_cb_state_changed)
        layout.addWidget(self.all_cb)

        group_label = self._lang.translate(TranslationKeys.TYPE_GROUP_FILTER)
        type_label = self._lang.translate(TranslationKeys.TYPE_FILTER)
        self.group_combo.setToolTip(group_label)
        self.type_combo.setToolTip(type_label)
        try:
            if hasattr(self.group_combo, "setDefaultText"):
                self.group_combo.setDefaultText(group_label)
            if hasattr(self.type_combo, "setDefaultText"):
                self.type_combo.setDefaultText(type_label)
        except Exception:
            pass

        self.group_combo.checkedItemsChanged.connect(self._on_group_selection_changed)  # type: ignore[attr-defined]
        self.type_combo.checkedItemsChanged.connect(self._on_type_selection_changed)  # type: ignore[attr-defined]

        if self._auto_load:
            QTimer.singleShot(0, self.reload)

    # ------------------------------------------------------------------
    def reload(self) -> None:
        self._loaded = False
        self._load_request_id += 1
        self.group_combo.clear()
        self.type_combo.clear()
        self._set_all_cb_state(Qt.Unchecked, enabled=False)
        self.group_combo.setEnabled(False)
        self.type_combo.setEnabled(False)
        self._show_loading_placeholder()
        self._start_async_load()

    def ensure_loaded(self) -> None:
        if not self._loaded:
            self.reload()

    def selected_ids(self) -> List[str]:
        values = list(self.type_combo.checkedItemsData() or [])  # type: ignore[attr-defined]
        return [v for v in values if v]

    def selected_texts(self) -> List[str]:
        values = list(self.type_combo.checkedItems() or [])  # type: ignore[attr-defined]
        return [v for v in values if v]

    def set_selected_ids(self, ids: Sequence[str], emit: bool = True) -> None:
        targets = {str(v) for v in ids or []}
        if not self._loaded:
            self._pending_type_ids = list(targets)
            return
        self._apply_type_selection(targets, emit)

    def _on_group_selection_changed(self) -> None:
        if self._suppress_group_emit:
            return
        selected_groups = {
            g
            for g in (self.group_combo.checkedItemsData() or [])  # type: ignore[attr-defined]
            if g
        }
        target_ids: set[str] = set()
        for group in selected_groups:
            target_ids.update(self._group_map.get(group, []))
        self._apply_type_selection(target_ids, emit=False)
        self._emit_selection_change()

    def _on_type_selection_changed(self) -> None:
        if self._suppress_type_emit:
            return
        self._sync_groups_to_types()
        self._sync_all_checkbox_state()
        self._emit_selection_change()

    def _apply_type_selection(self, target_ids: Sequence[str], emit: bool) -> None:
        targets = {str(v) for v in target_ids or []}
        self._suppress_type_emit = True
        try:
            for row in range(self.type_combo.count()):
                val = self.type_combo.itemData(row)
                state = Qt.Checked if str(val) in targets else Qt.Unchecked
                self.type_combo.setItemCheckState(row, state)
        finally:
            self._suppress_type_emit = False

        self._sync_groups_to_types()
        self._sync_all_checkbox_state()
        if emit:
            self._emit_selection_change()

    def _apply_preferred_types(self) -> None:
        if not self._loaded:
            return
        ids = self._settings_logic.load_module_preference_ids(
            self._module,
            support_key=ModuleSupports.TYPES.value,
        )
        if ids:
            self.set_selected_ids(list(ids), emit=False)

    def _sync_groups_to_types(self) -> None:
        selected_type_ids = set(self.selected_ids())
        self._suppress_group_emit = True
        try:
            for row in range(self.group_combo.count()):
                group_name = self.group_combo.itemData(row)
                if not group_name:
                    continue
                type_ids = self._group_map.get(group_name, [])
                if not type_ids:
                    state = Qt.Unchecked
                else:
                    checked = sum(1 for tid in type_ids if tid in selected_type_ids)
                    if checked == 0:
                        state = Qt.Unchecked
                    elif checked == len(type_ids):
                        state = Qt.Checked
                    else:
                        state = Qt.PartiallyChecked
                self.group_combo.setItemCheckState(row, state)
        finally:
            self._suppress_group_emit = False

    def _emit_selection_change(self) -> None:
        texts = self.selected_texts()
        ids = self.selected_ids()
        self.selectionChanged.emit(texts, ids)

    # Async helpers --------------------------------------------------
    def _show_loading_placeholder(self) -> None:
        loading_text = self._lang.translate(TranslationKeys.LOADING) if self._lang else "Loading"
        placeholder = f"{loading_text}…"
        self.group_combo.addItem(placeholder)
        self.type_combo.addItem(placeholder)

    def _start_async_load(self) -> None:
        FilterHelper.cancel_pending_load(self, invalidate_request=False)
        token = self._current_token()
        request_id = self._load_request_id

        key = ModuleSupports.TYPES.value
        worker = FunctionWorker(lambda: FilterHelper.get_filter_edges_by_key_and_module(key, self._module))
        worker.active_token = token
        worker.finished.connect(
            lambda payload, tok=token, req=request_id: self._handle_types_loaded(payload, tok, req)
        )
        worker.error.connect(
            lambda message, tok=token, req=request_id: self._handle_types_failed(message, tok, req)
        )
        self._worker = worker
        self._worker_thread = start_worker(worker, on_thread_finished=self._cleanup_worker)

    def _handle_types_loaded(
        self,
        payload: List[Dict[str, Optional[str]]],
        token: int | None,
        request_id: int,
    ) -> None:
        if request_id != self._load_request_id:
            return
        if not self._is_token_active(token):
            SwitchLogger.log(
                "type_filter_ignored_inactive_token",
                module=str(self._module),
                extra={"token": token},
            )
            return
        self.type_combo.clear()
        self.group_combo.clear()
        self._group_map.clear()

        for entry in payload:
            type_id = entry.get("id")
            label = entry.get("label")
            group_name = entry.get("group")
            if type_id and label:
                self.type_combo.addItem(label, type_id)
                if group_name:
                    self._group_map.setdefault(group_name, []).append(type_id)

        for group_name in sorted(self._group_map.keys(), key=str.lower):
            self.group_combo.addItem(group_name, group_name)

        self.group_combo.setEnabled(True)
        self.type_combo.setEnabled(True)
        self._loaded = True
        self.all_cb.setEnabled(True)
        self._apply_preferred_types()
        if self._pending_type_ids:
            self.set_selected_ids(self._pending_type_ids, emit=False)
            self._pending_type_ids = []
        self._sync_all_checkbox_state()
        self.loadFinished.emit(True)

    def _handle_types_failed(self, message: str, token: int | None, request_id: int) -> None:
        if request_id != self._load_request_id:
            return
        if not self._is_token_active(token):
            SwitchLogger.log(
                "type_filter_ignored_inactive_token",
                module=str(self._module),
                extra={"token": token},
            )
            return
        self.group_combo.clear()
        self.type_combo.clear()
        self.group_combo.addItem(f"Error: {message[:40]}…")
        self.group_combo.setEnabled(False)
        self.type_combo.setEnabled(False)
        self._set_all_cb_state(Qt.Unchecked, enabled=False)
        self._loaded = False
        self.loadFinished.emit(False)

    def _cleanup_worker(self) -> None:
        self._worker = None
        self._worker_thread = None

    # ------------------------------------------------------------------
    # Queue/cleanup helpers
    # ------------------------------------------------------------------
    def is_loaded(self) -> bool:
        return self._loaded

    def is_loading(self) -> bool:
        return self._worker_thread is not None

    def clear_data(self) -> None:
        """Clear combo data to free memory; safe to call on deactivate."""
        try:
            FilterHelper.cancel_pending_load(self, invalidate_request=True)
            self.group_combo.clear()
            self.type_combo.clear()
            self.group_combo.setEnabled(False)
            self.type_combo.setEnabled(False)
            self._set_all_cb_state(Qt.Unchecked, enabled=False)
            self._group_map.clear()
            self._loaded = False
            self._pending_type_ids = []
        except Exception as exc:
            print(f"[TypeFilterWidget] clear_data failed: {exc}")
    def _apply_select_all(self, checked: bool) -> None:
        if checked and hasattr(self.type_combo, "selectAllOptions"):
            self.type_combo.selectAllOptions()
            return
        if not checked and hasattr(self.type_combo, "deselectAllOptions"):
            self.type_combo.deselectAllOptions()
            return

        target_state = Qt.Checked if checked else Qt.Unchecked
        for i in range(self.type_combo.count()):
            if self.type_combo.itemData(i) is None:
                continue
            self.type_combo.setItemCheckState(i, target_state)

    def _on_all_cb_state_changed(self, state: int) -> None:
        if self._suppress_all_cb:
            return
        self._suppress_type_emit = True
        try:
            self._apply_select_all(state == Qt.Checked)
        finally:
            self._suppress_type_emit = False
        self._sync_groups_to_types()
        self._sync_all_checkbox_state()
        self._emit_selection_change()

    def _sync_all_checkbox_state(self) -> None:
        total = 0
        checked = 0
        for i in range(self.type_combo.count()):
            val = self.type_combo.itemData(i)
            if val is None:
                continue
            total += 1
            if self.type_combo.itemCheckState(i) == Qt.Checked:
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
