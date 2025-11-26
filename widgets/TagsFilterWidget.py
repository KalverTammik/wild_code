# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import List, Optional, Sequence, Union

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import QHBoxLayout, QWidget
from ..constants.settings_keys import SettingsService
from qgis.gui import QgsCheckableComboBox

from ..languages.language_manager import LanguageManager
from ..languages.translation_keys import TranslationKeys
from ..python.GraphQLQueryLoader import GraphQLQueryLoader
from ..python.api_client import APIClient
from ..utils.url_manager import Module


class TagsFilterWidget(QWidget):
    """Simplified tags filter with direct signal forwarding."""

    selectionChanged = pyqtSignal(list, list)

    def __init__(
        self,
        module_name: Union[str, object],
        lang_manager: Optional[LanguageManager] = None,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self._module = getattr(module_name, "value", module_name)
        self._lang = lang_manager or LanguageManager()
        self._loader = GraphQLQueryLoader(self._lang)
        self._api = APIClient()
        self._suppress_emit = False
        self._loaded = False

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
        self.reload()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def reload(self) -> None:
        self._loaded = False
        try:
            self._load_tags()
            self._loaded = True
            self._apply_preffered_tags()
        except Exception as exc:
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
        targets = {str(v) for v in ids or []}
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
    def _load_tags(self) -> None:
        tags_module = Module.TAGS.value
        query = self._loader.load_query_by_module(tags_module, "ListModuleTags.graphql")
        variables = {
            "first": 50,
            "after": None,
            "where": {"column": "MODULE", "value": f"{str(self._module).upper()}S"},
        }
        data = self._api.send_query(query, variables=variables) or {}
        edges = ((data or {}).get("tags") or {}).get("edges") or []

        self.combo.clear()
        for edge in edges:
            node = (edge or {}).get("node") or {}
            tag_id = node.get("id")
            label = node.get("name")
            if tag_id and label:
                self.combo.addItem(label, tag_id)

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
    