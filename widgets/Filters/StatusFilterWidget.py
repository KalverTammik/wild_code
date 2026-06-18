# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Callable, List, Optional, Sequence, Union

from PyQt5.QtCore import QTimer, pyqtSignal
from PyQt5.QtWidgets import QHBoxLayout, QWidget

from ...Logs.python_fail_logger import PythonFailLogger
from ...languages.language_manager import LanguageManager
from ...languages.translation_keys import TranslationKeys
from ...modules.Settings.SettinsUtils.SettingsLogic import SettingsLogic
from ...python.api_actions import APIModuleActions
from ...python.workers import FunctionWorker, start_worker
from ...utils.FilterHelpers.FilterHelper import FilterHelper
from ...utils.url_manager import ModuleSupports
from ..status_select_widget import StatusMultiSelectWidget


class StatusFilterWidget(QWidget):
    """Status-specific filter backed by the custom status multi-select."""

    selectionChanged = pyqtSignal(list, list)
    loadFinished = pyqtSignal(bool)

    def __init__(
        self,
        module_name: Union[str, object],
        parent: Optional[QWidget] = None,
        *,
        auto_load: bool = True,
        settings_logic: Optional[SettingsLogic] = None,
        lang_manager: Optional[LanguageManager] = None,
        label_text: Optional[str] = None,
        selected_ids_loader: Optional[Callable[[], Sequence[str]]] = None,
        object_name: str = "StatusFilterCombo",
    ) -> None:
        super().__init__(parent)
        self._module = getattr(module_name, "value", module_name)
        self._lang = lang_manager or LanguageManager()
        self._settings_logic = settings_logic or SettingsLogic()
        self._selected_ids_loader = selected_ids_loader
        self._loaded = False
        self._worker = None
        self._worker_thread = None
        self._auto_load = auto_load
        self._load_request_id = 0
        self._pending_selected_ids: Optional[List[str]] = None
        self._suppress_emit = False

        label = label_text or self._lang.translate(TranslationKeys.STATUS_FILTER)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 2, 4, 2)
        layout.setSpacing(1)

        self.selector = StatusMultiSelectWidget(
            self,
            placeholder=label,
            lang_manager=self._lang,
        )
        self.selector.setObjectName(object_name)
        self.selector.setToolTip(label)
        self.selector.selectionChanged.connect(self._emit_selection_change)
        layout.addWidget(self.selector)

        if self._auto_load:
            QTimer.singleShot(0, self.reload)

    def retheme(self) -> None:
        self.selector.retheme()
        self.style().unpolish(self)
        self.style().polish(self)

    def reload(self) -> None:
        self._loaded = False
        self._load_request_id += 1
        self.selector.clear()
        loading_text = self._lang.translate(TranslationKeys.LOADING)
        self.selector.set_loading(f"{loading_text}...")
        self._start_async_load()

    def ensure_loaded(self) -> None:
        if not self._loaded:
            self.reload()

    def selected_ids(self) -> List[str]:
        return list(self.selector.selected_ids())

    def selected_texts(self) -> List[str]:
        return list(self.selector.selected_texts())

    def set_selected_ids(self, ids: Sequence[str], emit: bool = True) -> None:
        normalized = self._normalize_ids(ids)
        if not self._loaded:
            self._pending_selected_ids = normalized
            return
        self.selector.set_selected_ids(normalized, emit=emit)

    def is_loaded(self) -> bool:
        return self._loaded

    def is_loading(self) -> bool:
        return self._worker_thread is not None

    def clear_data(self) -> None:
        try:
            FilterHelper.cancel_pending_load(self, invalidate_request=True)
            self.selector.clear()
            self.selector.setEnabled(False)
            self._loaded = False
            self._pending_selected_ids = None
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module="filter",
                event="status_filter_clear_data_failed",
            )

    def _emit_selection_change(self, texts=None, ids=None) -> None:
        if self._suppress_emit:
            return
        selected_texts = list(self.selector.selected_texts() if texts is None else texts)
        selected_ids = list(self.selector.selected_ids() if ids is None else ids)
        self.selectionChanged.emit(selected_texts, selected_ids)

    def _start_async_load(self) -> None:
        FilterHelper.cancel_pending_load(self, invalidate_request=False)
        token = self._current_token()
        request_id = self._load_request_id

        worker = FunctionWorker(lambda: APIModuleActions.get_module_status_options(str(self._module or "")))
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
        payload: List[dict[str, object]],
        token: int | None,
        request_id: int,
    ) -> None:
        if not self._is_widget_alive():
            return
        if request_id != self._load_request_id:
            return
        if not self._is_token_active(token):
            return

        status_options = [entry for entry in (payload or []) if isinstance(entry, dict)]
        selected_ids = self._initial_selected_ids()

        self.selector.set_options(status_options, selected_ids=selected_ids)
        self.selector.setEnabled(bool(status_options))
        self._loaded = True
        self._pending_selected_ids = None
        self.loadFinished.emit(True)

    def _handle_load_error(self, message: str, token: int | None, request_id: int) -> None:
        if not self._is_widget_alive():
            return
        if request_id != self._load_request_id:
            return
        if not self._is_token_active(token):
            return
        error_text = self._lang.translate(TranslationKeys.ERROR)
        self.selector.set_error(f"{error_text}: {str(message or '')[:60]}...")
        self._loaded = False
        self.loadFinished.emit(False)

    def _cleanup_worker(self) -> None:
        if not self._is_widget_alive():
            return
        self._worker = None
        self._worker_thread = None

    def _initial_selected_ids(self) -> List[str]:
        if self._pending_selected_ids is not None:
            return list(self._pending_selected_ids)

        if callable(self._selected_ids_loader):
            try:
                return self._normalize_ids(self._selected_ids_loader() or [])
            except Exception as exc:
                PythonFailLogger.log_exception(
                    exc,
                    module="filter",
                    event="status_filter_selected_ids_loader_failed",
                )
                return []

        ids = self._settings_logic.load_module_preference_ids(
            self._module,
            support_key=ModuleSupports.STATUSES.value,
        )
        return self._normalize_ids(ids)

    @staticmethod
    def _normalize_ids(ids: Sequence[str]) -> List[str]:
        normalized: List[str] = []
        seen: set[str] = set()
        for value in ids or []:
            text = str(value or "").strip()
            if not text or text in seen:
                continue
            seen.add(text)
            normalized.append(text)
        return normalized

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
