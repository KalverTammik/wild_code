# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import List, Optional, Sequence, Union, Tuple

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import QHBoxLayout, QWidget
from qgis.gui import QgsCheckableComboBox

from ..languages.language_manager import LanguageManager
from ..languages.translation_keys import TranslationKeys
from ..python.GraphQLQueryLoader import GraphQLQueryLoader
from ..python.api_client import APIClient
from ..utils.url_manager import  ModuleSupports
from ..utils.FilterHelpers.FilterHelper import FilterHelper
from ..python.workers import FunctionWorker, start_worker
from ..modules.Settings.SettinsUtils.SettingsLogic import SettingsLogic


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
        settings_logic: Optional[SettingsLogic] = None,
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
        self._settings_logic = settings_logic or SettingsLogic()

        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 2, 4, 2)
        layout.setSpacing(1)

        self.combo = QgsCheckableComboBox(self)
        self.combo.setObjectName("TagsFilterCombo")
        layout.addWidget(self.combo)
        self.combo.setToolTip(self._lang.translate(TranslationKeys.TAGS_FILTER))

        self.combo.checkedItemsChanged.connect(self._emit_selection_change)  # type: ignore[attr-defined]
        if self._auto_load:
            self.reload()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def reload(self) -> None:
        self._loaded = False
        self.combo.clear()
        self._show_loading_placeholder()
        self._start_async_load()

    def ensure_loaded(self) -> None:
        if not self._loaded:
            self.reload()


    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _emit_selection_change(self) -> None:
        if self._suppress_emit:
            return
        texts = FilterHelper.selected_texts(self)
        ids = FilterHelper.selected_ids(self)
        self.selectionChanged.emit(texts, ids)

    # Async helpers --------------------------------------------------
    def _show_loading_placeholder(self) -> None:
        loading_text = self._lang.translate(TranslationKeys.LOADING) if self._lang else "Loading"
        self.combo.addItem(f"{loading_text}…")

    def _start_async_load(self) -> None:
        FilterHelper.cancel_pending_load(self, invalidate_request=False)
        self._load_request_id += 1
        request_id = self._load_request_id

        key = ModuleSupports.TAGS.value
        worker = FunctionWorker(lambda: FilterHelper.get_filter_edges_by_key_and_module(key, self._module))
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
        saved_ids = self._settings_logic.load_module_preference_ids(
            self._module,
            support_key=ModuleSupports.TAGS.value,
        )
        if saved_ids:
            FilterHelper.set_selected_ids(self, list(saved_ids), emit=False)
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


    