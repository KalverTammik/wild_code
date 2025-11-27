# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import List, Optional, Sequence, Union, Tuple

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import QHBoxLayout, QWidget
from ..constants.settings_keys import SettingsService
from qgis.gui import QgsCheckableComboBox

from ..languages.language_manager import LanguageManager
from ..languages.translation_keys import TranslationKeys
from ..python.GraphQLQueryLoader import GraphQLQueryLoader
from ..python.api_client import APIClient
from ..python.responses import JsonResponseHandler
from ..utils.url_manager import Module
from ..python.workers import FunctionWorker, start_worker


class StatusFilterWidget(QWidget):
    """Standalone status filter backed by a QgsCheckableComboBox."""

    selectionChanged = pyqtSignal(list, list)
    loadFinished = pyqtSignal(bool)

    def __init__(
        self,
        module_name: Union[str, object],
        parent: Optional[QWidget] = None,
        *,
        auto_load: bool = True,
    ) -> None:
        super().__init__(parent)
        self._module = getattr(module_name, "value", module_name)
        self._lang = LanguageManager()
        self._api = APIClient()
        self._loader = GraphQLQueryLoader(self._lang)
        self._suppress_emit = False
        self._loaded = False
        self._worker = None
        self._worker_thread = None
        self._load_request_id = 0
        self._pending_selection_ids: List[str] = []
        self._auto_load = auto_load

        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 2, 4, 2)
        layout.setSpacing(1)

        self.combo = QgsCheckableComboBox(self)
        self.combo.setObjectName("StatusFilterCombo")
        self.combo.setMaxVisibleItems(12)
        layout.addWidget(self.combo)

        tooltip = self._lang.translate("Status Filter") if self._lang else "Status Filter"
        self.filter_title = tooltip
        self.combo.setToolTip(tooltip)

        self.combo.checkedItemsChanged.connect(self._emit_selection_change)  # type: ignore[attr-defined]
        if self._auto_load:
            self.reload()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def reload(self) -> None:
        self._loaded = False
        self.combo.setEnabled(False)
        self.combo.clear()
        self._show_loading_placeholder()
        self._start_async_load()

    def ensure_loaded(self) -> None:
        if not self._loaded:
            self.reload()

    def selected_ids(self) -> List[str]:
        return list(self.combo.checkedItemsData() or [])  # type: ignore[attr-defined]

    def selected_texts(self) -> List[str]:
        return list(self.combo.checkedItems() or [])  # type: ignore[attr-defined]

    def set_selected_ids(self, ids: Sequence[str], emit: bool = True) -> None:
        ids_set = {str(v) for v in ids or []}
        if not self._loaded:
            self._pending_selection_ids = list(ids_set)
            return
        self._suppress_emit = True
        try:
            for row in range(self.combo.count()):
                val = self.combo.itemData(row)
                state = Qt.Checked if str(val) in ids_set else Qt.Unchecked
                self.combo.setItemCheckState(row, state)
        finally:
            self._suppress_emit = False

        if emit:
            self._emit_selection_change()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _load_statuses_payload(self) -> List[Tuple[str, str]]:
        key_raw = Module.STATUSES.value
        key = key_raw[:-2].upper() if len(key_raw) > 2 else key_raw.upper()
        query = self._loader.load_query_by_module(key, "ListModuleStatuses.graphql")
        module_plural = f"{str(self._module).upper()}S"
        variables = {
            "first": 50,
            "after": None,
            "where": {"column": "MODULE", "value": module_plural},
        }
        data = self._api.send_query(query, variables=variables, return_raw=True) or {}
        edges = JsonResponseHandler.get_edges_from_path(data, ["statuses"])

        entries: List[Tuple[str, str]] = []
        for edge in edges:
            node = (edge or {}).get("node") or {}
            sid = node.get("id")
            label = node.get("name")
            if sid and label:
                entries.append((label, sid))
        return entries

    def _apply_prefered_statuses(self) -> None:

        preferred_statuses = SettingsService().module_preferred_statuses(self._module) or ""
        ids = [token.strip() for token in str(preferred_statuses).split(",") if token.strip()]

        if ids:
            self.set_selected_ids(ids, emit=False)

    def _emit_selection_change(self) -> None:
        if self._suppress_emit:
            return
        texts = self.selected_texts()
        ids = self.selected_ids()
        self.selectionChanged.emit(texts, ids)

    # Async helpers --------------------------------------------------
    def _show_loading_placeholder(self) -> None:
        loading_text = self._lang.translate(TranslationKeys.LOADING) if self._lang else "Loading"
        self.combo.addItem(f"{loading_text}…")

    def _start_async_load(self) -> None:
        self.cancel_pending_load(invalidate_request=False)
        self._load_request_id += 1
        request_id = self._load_request_id

        worker = FunctionWorker(self._load_statuses_payload)
        worker.finished.connect(
            lambda payload, rid=request_id: self._handle_load_success(rid, payload)
        )
        worker.error.connect(
            lambda message, rid=request_id: self._handle_load_error(rid, message)
        )
        self._worker = worker
        self._worker_thread = start_worker(worker, on_thread_finished=self._cleanup_worker)

    def _handle_load_success(self, request_id: int, payload: List[Tuple[str, str]]) -> None:
        if request_id != self._load_request_id:
            return
        self.combo.clear()
        for label, value in payload:
            self.combo.addItem(label, value)
        self.combo.setEnabled(True)
        self._loaded = True
        self._apply_prefered_statuses()
        if self._pending_selection_ids:
            self.set_selected_ids(self._pending_selection_ids, emit=False)
            self._pending_selection_ids = []
        self.loadFinished.emit(True)

    def _handle_load_error(self, request_id: int, message: str) -> None:
        if request_id != self._load_request_id:
            return
        self.combo.clear()
        self.combo.addItem(f"Error: {message[:60]}…")
        self.combo.setEnabled(False)
        self._loaded = False
        self.loadFinished.emit(False)

    def _cleanup_worker(self) -> None:
        self._worker = None
        self._worker_thread = None

    # ------------------------------------------------------------------
    # Queue helpers
    # ------------------------------------------------------------------
    def is_loaded(self) -> bool:
        return self._loaded

    def is_loading(self) -> bool:
        return self._worker_thread is not None

    def cancel_pending_load(self, *, invalidate_request: bool = True) -> None:
        if invalidate_request:
            self._load_request_id += 1
        thread = self._worker_thread
        was_running = thread is not None and thread.isRunning()
        self._worker = None
        self._worker_thread = None
        if thread is not None and thread.isRunning():
            try:
                thread.quit()
                thread.wait(50)
            except Exception:
                pass
        if was_running:
            self.loadFinished.emit(False)
