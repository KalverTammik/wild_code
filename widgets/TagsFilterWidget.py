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


class TagsFilterWidget(QWidget):
    """Simplified tags filter with direct signal forwarding."""

    selectionChanged = pyqtSignal(list, list)
    loadFinished = pyqtSignal(bool)

    def __init__(
        self,
        module_name: Union[str, object],
        lang_manager: Optional[LanguageManager] = None,
        parent: Optional[QWidget] = None,
        *,
        auto_load: bool = True,
    ) -> None:
        super().__init__(parent)
        self._module = getattr(module_name, "value", module_name)
        self._lang = lang_manager or LanguageManager()
        self._loader = GraphQLQueryLoader()
        self._api = APIClient()
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
        self.combo.setObjectName("TagsFilterCombo")
        layout.addWidget(self.combo)
        title = self._lang.translate(TranslationKeys.TAGS_FILTER)
        self.filter_title = title
        self.combo.setToolTip(title)

        self.combo.checkedItemsChanged.connect(self._emit_selection_change)  # type: ignore[attr-defined]
        if self._auto_load:
            self.reload()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def reload(self) -> None:
        self._loaded = False
        self.combo.clear()
        self.combo.setEnabled(False)
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
        targets = {str(v) for v in ids or []}
        if not self._loaded:
            self._pending_selection_ids = list(targets)
            return
        self._suppress_emit = True
        try:
            for row in range(self.combo.count()):
                val = self.combo.itemData(row)
                state = Qt.Checked if str(val) in targets else Qt.Unchecked
                self.combo.setItemCheckState(row, state)
        finally:
            self._suppress_emit = False

        if emit:
            self._emit_selection_change()

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------
    def _load_tags_payload(self) -> List[Tuple[str, str]]:
        tags_module = Module.TAGS.value
        query = self._loader.load_query_by_module(tags_module, "ListModuleTags.graphql")
        variables = {
            "first": 50,
            "after": None,
            "where": {"column": "MODULE", "value": f"{str(self._module).upper()}S"},
        }
        data = self._api.send_query(query, variables=variables, return_raw=True) or {}
        edges = JsonResponseHandler.get_edges_from_path(data, ["tags"])

        entries: List[Tuple[str, str]] = []
        for edge in edges:
            node = (edge or {}).get("node") or {}
            tag_id = node.get("id")
            label = node.get("name")
            if tag_id and label:
                entries.append((label, tag_id))
        return entries

    def _apply_preffered_tags(self) -> None:
        if not self._loaded:
            return
        preferred_tags = SettingsService().module_preferred_tags(self._module) or ""
        ids = [token.strip() for token in str(preferred_tags).split(",") if token.strip()]
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

        worker = FunctionWorker(self._load_tags_payload)
        worker.finished.connect(
            lambda payload, rid=request_id: self._handle_tags_loaded(rid, payload)
        )
        worker.error.connect(
            lambda message, rid=request_id: self._handle_tags_failed(rid, message)
        )
        self._worker = worker
        self._worker_thread = start_worker(worker, on_thread_finished=self._cleanup_worker)

    def _handle_tags_loaded(self, request_id: int, payload: List[Tuple[str, str]]) -> None:
        if request_id != self._load_request_id:
            return
        self.combo.clear()
        for label, value in payload:
            self.combo.addItem(label, value)
        self.combo.setEnabled(True)
        self._loaded = True
        self._apply_preffered_tags()
        if self._pending_selection_ids:
            self.set_selected_ids(self._pending_selection_ids, emit=False)
            self._pending_selection_ids = []
        self.loadFinished.emit(True)

    def _handle_tags_failed(self, request_id: int, message: str) -> None:
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
    