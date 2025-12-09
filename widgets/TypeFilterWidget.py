# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Dict, List, Optional, Sequence

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import QHBoxLayout, QWidget
from qgis.gui import QgsCheckableComboBox

from ..languages.language_manager import LanguageManager
from ..languages.translation_keys import TranslationKeys
from ..python.GraphQLQueryLoader import GraphQLQueryLoader
from ..python.api_client import APIClient
from ..python.workers import FunctionWorker, start_worker
from ..utils.url_manager import  ModuleSupports
from ..utils.FilterHelpers.FilterHelper import FilterHelper
from ..modules.Settings.SettinsUtils.SettingsLogic import SettingsLogic
class TypeFilterWidget(QWidget):
    """Simple group/type multi-select without shared base class."""

    selectionChanged = pyqtSignal(list, list)
    loadFinished = pyqtSignal(bool)
    _PAGE_SIZE = 50

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
        self._loader = GraphQLQueryLoader()
        self._api = APIClient()
        self._group_map: Dict[str, List[str]] = {}
        self._suppress_group_emit = False
        self._suppress_type_emit = False
        self._loaded = False
        self._worker = None
        self._worker_thread = None
        self._load_request_id = 0
        self._pending_type_ids: List[str] = []
        self._auto_load = auto_load
        self._settings_logic = settings_logic or SettingsLogic()

        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(2)

        self.group_combo = QgsCheckableComboBox(self)
        self.group_combo.setObjectName("GroupFilterCombo")
        layout.addWidget(self.group_combo)

        self.type_combo = QgsCheckableComboBox(self)
        self.type_combo.setObjectName("TypeFilterCombo")
        layout.addWidget(self.type_combo)

        self.group_combo.setToolTip(self._lang.translate(TranslationKeys.TYPE_GROUP_FILTER))
        self.type_combo.setToolTip(self._lang.translate(TranslationKeys.TYPE_FILTER))

        self.group_combo.checkedItemsChanged.connect(self._on_group_selection_changed)  # type: ignore[attr-defined]
        self.type_combo.checkedItemsChanged.connect(self._on_type_selection_changed)  # type: ignore[attr-defined]

        if self._auto_load:
            self.reload()

    # ------------------------------------------------------------------
    def reload(self) -> None:
        self._loaded = False
        self.group_combo.clear()
        self.type_combo.clear()
        self.group_combo.setEnabled(False)
        self.type_combo.setEnabled(False)
        self._show_loading_placeholder()
        self._start_async_load()

    def ensure_loaded(self) -> None:
        if not self._loaded:
            self.reload()

    def selected_ids(self) -> List[str]:
        return list(self.type_combo.checkedItemsData() or [])  # type: ignore[attr-defined]

    def selected_texts(self) -> List[str]:
        return list(self.type_combo.checkedItems() or [])  # type: ignore[attr-defined]

    def set_selected_ids(self, ids: Sequence[str], emit: bool = True) -> None:
        targets = {str(v) for v in ids or []}
        if not self._loaded:
            self._pending_type_ids = list(targets)
            return
        self._apply_type_selection(targets, emit)


    def _on_group_selection_changed(self) -> None:
        if self._suppress_group_emit:
            return
        selected_groups = set(self.group_combo.checkedItemsData() or [])  # type: ignore[attr-defined]
        target_ids: set[str] = set()
        for group in selected_groups:
            target_ids.update(self._group_map.get(group, []))
        self._apply_type_selection(target_ids, emit=False)
        self._emit_selection_change()

    def _on_type_selection_changed(self) -> None:
        if self._suppress_type_emit:
            return
        self._sync_groups_to_types()
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
        self._load_request_id += 1
        request_id = self._load_request_id

        key = ModuleSupports.TYPES.value
        worker = FunctionWorker(lambda: FilterHelper.get_filter_edges_by_key_and_module(key, self._module))
        worker.finished.connect(
            lambda payload, rid=request_id: self._handle_types_loaded(rid, payload)
        )
        worker.error.connect(
            lambda message, rid=request_id: self._handle_types_failed(rid, message)
        )
        self._worker = worker
        self._worker_thread = start_worker(worker, on_thread_finished=self._cleanup_worker)

    def _handle_types_loaded(self, request_id: int, payload: List[Dict[str, Optional[str]]]) -> None:
        if request_id != self._load_request_id:
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
        self._apply_preferred_types()
        if self._pending_type_ids:
            self.set_selected_ids(self._pending_type_ids, emit=False)
            self._pending_type_ids = []
        self.loadFinished.emit(True)

    def _handle_types_failed(self, request_id: int, message: str) -> None:
        if request_id != self._load_request_id:
            return
        self.group_combo.clear()
        self.type_combo.clear()
        self.group_combo.addItem(f"Error: {message[:40]}…")
        self.group_combo.setEnabled(False)
        self.type_combo.setEnabled(False)
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

