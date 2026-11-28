# -*- coding: utf-8 -*-
"""The tags filter: every tag of the module, grouped, with a search field."""
from __future__ import annotations

from typing import List, Optional, Sequence, Union

from qgis.PyQt.QtCore import QTimer, pyqtSignal
from qgis.PyQt.QtWidgets import QHBoxLayout, QWidget

from ...constants.module_names import ModuleSupports
from ...languages.language_manager import LanguageManager
from ...languages.translation_keys import TranslationKeys
from ...Logs.python_fail_logger import PythonFailLogger
from ...python.api_actions import APIModuleActions
from ...python.tag_catalog import TagCatalog
from ...utils.api_error_handling import user_message
from ...utils.FilterHelpers.FilterHelper import FilterHelper
from ...utils.settings_logic import SettingsLogic
from ..Tags.grouped_tag_picker import GroupedTagPicker
from ..Tags.tag_catalog_store import TagCatalogStore
from .filter_widget_parts import FilterLoadingMixin


class TagsFilterWidget(FilterLoadingMixin, QWidget):
    """Used in the list toolbar and for the preferred tags in the settings."""

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
        self._settings_logic = settings_logic or SettingsLogic()
        self._loaded = False
        self._pending_selected_ids: Optional[list[str]] = None  # chosen before the tags arrived
        self._worker = None
        self._worker_thread = None
        self._load_request_id = 0
        self._auto_load = auto_load

        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 2, 4, 2)
        self.picker = GroupedTagPicker(self, placeholder=self._lang.translate(TranslationKeys.TAGS_FILTER))
        self.picker.selectionChanged.connect(self._emit_selection)
        layout.addWidget(self.picker, 1)

        if self._auto_load:
            QTimer.singleShot(0, self.reload)

    def retheme(self) -> None:
        self.picker.retheme()

    def reload(self) -> None:
        self._loaded = False
        self._load_request_id += 1
        self.picker.set_catalog(TagCatalog())
        self.picker.set_status(f"{self._lang.translate(TranslationKeys.LOADING)}…")
        self._start_async_load()

    def selected_ids(self) -> List[str]:
        return self.picker.selected_ids()

    def selected_texts(self) -> List[str]:
        return self.picker.selected_names()

    def set_selected_ids(self, ids: Sequence[str], emit: bool = True) -> None:
        if not self._loaded:
            self._pending_selected_ids = [str(value) for value in ids or []]
            return
        self.picker.set_selected_ids(ids, emit=emit)

    def clear_data(self) -> None:
        """Drop the list to free memory; safe to call on deactivate."""
        try:
            FilterHelper.cancel_pending_load(self, invalidate_request=True)
            self.picker.set_catalog(TagCatalog())
            self.picker.set_selected_ids([])
            self._loaded = False
            self._pending_selected_ids = None
        except Exception as exc:
            PythonFailLogger.log_exception(exc, module=self._module, event="filter_clear_failed")

    def _emit_selection(self, ids: list) -> None:
        self.selectionChanged.emit(self.picker.selected_names(), ids)

    def _fetch_options(self) -> TagCatalog:
        return APIModuleActions.get_module_tag_catalog(self._module)

    def _handle_load_success(self, catalog: TagCatalog, token: int | None, request_id: int) -> None:
        if not self._is_response_current(token, request_id):
            return
        pending, self._pending_selected_ids = self._pending_selected_ids, None
        if pending is None:
            pending = self._settings_logic.load_module_preference_ids(
                self._module, support_key=ModuleSupports.TAGS.value)
        self.picker.set_catalog(catalog)
        self.picker.set_selected_ids(pending or [])
        self._loaded = True
        TagCatalogStore.shared().put(self._module, catalog)
        self.loadFinished.emit(True)

    def _handle_load_error(self, message: str, token: int | None, request_id: int) -> None:
        if not self._is_response_current(token, request_id):
            return
        PythonFailLogger.log(
            "tags_filter_load_failed", module=self._module, message=str(message))
        self.picker.set_catalog(TagCatalog())
        text = f"{self._lang.translate(TranslationKeys.ERROR)}: {user_message(message)}"
        self.picker.set_status(f"{text[:60]}…", tooltip=text)
        self._loaded = False
        self.loadFinished.emit(False)
