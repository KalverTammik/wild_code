# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import List, Optional, Union, Tuple

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QHBoxLayout, QWidget

from qgis.gui import QgsCheckableComboBox

from ..languages.language_manager import LanguageManager
from ..languages.translation_keys import TranslationKeys
from ..python.GraphQLQueryLoader import GraphQLQueryLoader
from ..python.api_client import APIClient
from ..utils.url_manager import ModuleSupports
from ..utils.FilterHelpers.FilterHelper import FilterHelper
from ..python.workers import FunctionWorker, start_worker
from ..modules.Settings.SettinsUtils.SettingsLogic import SettingsLogic


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
        settings_logic: Optional[SettingsLogic] = None,
    ) -> None:
        super().__init__(parent)
        self._module = getattr(module_name, "value", module_name)
        self._lang = LanguageManager()
        self._api = APIClient()
        self._loader = GraphQLQueryLoader()
        self._settings_logic = settings_logic or SettingsLogic()
        self._suppress_emit = False
        self._loaded = False
        self._worker = None
        self._worker_thread = None
        self._load_request_id = 0
        self._auto_load = auto_load

        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 2, 4, 2)
        layout.setSpacing(1)

        self.combo = QgsCheckableComboBox(self)
        self.combo.setObjectName("StatusFilterCombo")
        self.combo.setMaxVisibleItems(12)
        layout.addWidget(self.combo)

        tooltip = LanguageManager().translate(TranslationKeys.STATUS_FILTER)
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
        self.combo.clear()
        self._show_loading_placeholder()
        self._start_async_load()

    def ensure_loaded(self) -> None:
        if not self._loaded:
            self.reload()


    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _emit_selection_change(self) -> None:
        if self._suppress_emit:
            return
        texts = FilterHelper.selected_texts(self)
        ids = FilterHelper.selected_ids(self)
        self.selectionChanged.emit(texts, ids)

    # Async helpers --------------------------------------------------
    def _show_loading_placeholder(self) -> None:
        loading_text = LanguageManager().translate(TranslationKeys.LOADING)
        self.combo.addItem(f"{loading_text}…")

    def _start_async_load(self) -> None:
        FilterHelper.cancel_pending_load(self, invalidate_request=False)
        self._load_request_id += 1
        request_id = self._load_request_id

        key = ModuleSupports.STATUSES.value
        worker = FunctionWorker(lambda: FilterHelper.get_filter_edges_by_key_and_module(key, self._module))
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
        saved_ids = self._settings_logic.load_module_preference_ids(
            self._module,
            support_key=ModuleSupports.STATUSES.value,
        )
        if saved_ids:
            FilterHelper.set_selected_ids(self, list(saved_ids), emit=False)
        self.loadFinished.emit(True)

    def _handle_load_error(self, request_id: int, message: str) -> None:
        print(f"[StatusFilterWidget] handling load error: {message}")
        if request_id != self._load_request_id:
            return
        self.combo.clear()
        self.combo.addItem(f"{LanguageManager().translate(TranslationKeys.ERROR)}: {message[:60]}…")

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

