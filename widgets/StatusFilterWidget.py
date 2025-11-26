# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import List, Optional, Sequence, Union

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import QHBoxLayout, QWidget
from ..constants.settings_keys import SettingsService
from qgis.gui import QgsCheckableComboBox

from ..languages.language_manager import LanguageManager
from ..python.GraphQLQueryLoader import GraphQLQueryLoader
from ..python.api_client import APIClient
from ..utils.url_manager import Module


class StatusFilterWidget(QWidget):
    """Standalone status filter backed by a QgsCheckableComboBox."""

    selectionChanged = pyqtSignal(list, list)

    def __init__(self, module_name: Union[str, object], parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._module = getattr(module_name, "value", module_name)
        self._lang = LanguageManager()
        self._api = APIClient()
        self._loader = GraphQLQueryLoader(self._lang)
        self._suppress_emit = False
        self._loaded = False

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
        self.reload()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def reload(self) -> None:
        self._loaded = False
        try:
            self._load_statuses()
            self._loaded = True
            self._apply_prefered_statuses()
        except Exception as exc:  # pragma: no cover - logged for diagnostics
            self.combo.clear()
            self.combo.addItem(f"Error: {str(exc)[:60]}…")
            self.combo.setEnabled(False)
            self._loaded = False

    def ensure_loaded(self) -> None:
        if not self._loaded:
            self.reload()

    def selected_ids(self) -> List[str]:
        return list(self.combo.checkedItemsData() or [])  # type: ignore[attr-defined]

    def selected_texts(self) -> List[str]:
        return list(self.combo.checkedItems() or [])  # type: ignore[attr-defined]

    def set_selected_ids(self, ids: Sequence[str], emit: bool = True) -> None:
        ids_set = {str(v) for v in ids or []}
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
    def _load_statuses(self) -> None:
        key_raw = Module.STATUSES.value
        key = key_raw[:-2].upper() if len(key_raw) > 2 else key_raw.upper()
        query = self._loader.load_query_by_module(key, "ListModuleStatuses.graphql")
        module_plural = f"{str(self._module).upper()}S"
        variables = {
            "first": 50,
            "after": None,
            "where": {"column": "MODULE", "value": module_plural},
        }
        data = self._api.send_query(query, variables=variables) or {}
        edges = ((data or {}).get("statuses") or {}).get("edges") or []

        self.combo.clear()
        for edge in edges:
            node = (edge or {}).get("node") or {}
            sid = node.get("id")
            label = node.get("name")
            if sid and label:
                self.combo.addItem(label, sid)

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
