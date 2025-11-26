# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Dict, List, Optional, Sequence

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import QHBoxLayout, QWidget
from ..constants.settings_keys import SettingsService
from qgis.gui import QgsCheckableComboBox

from ..languages.language_manager import LanguageManager
from ..languages.translation_keys import TranslationKeys
from ..python.GraphQLQueryLoader import GraphQLQueryLoader
from ..python.api_client import APIClient
from ..utils.filter_helpers import group_key


class TypeFilterWidget(QWidget):
    """Simple group/type multi-select without shared base class."""

    selectionChanged = pyqtSignal(list, list)
    _PAGE_SIZE = 50

    def __init__(self, module_name: str, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._module = module_name
        self._lang = LanguageManager()
        self._loader = GraphQLQueryLoader(self._lang)
        self._api = APIClient()
        self._group_map: Dict[str, List[str]] = {}
        self._suppress_group_emit = False
        self._suppress_type_emit = False
        self._loaded = False


        self.filter_title = self._lang.translate(TranslationKeys.TYPE_FILTER)
        
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

        self.reload()

    # ------------------------------------------------------------------
    def reload(self) -> None:
        self._loaded = False
        try:
            self._load_types()
            self._loaded = True
            self._apply_preferred_types()
        except Exception as exc:
            self.group_combo.clear()
            self.type_combo.clear()
            self.group_combo.addItem(f"Error: {str(exc)[:40]}…")
            self.group_combo.setEnabled(False)
            self.type_combo.setEnabled(False)
            self._loaded = False

    def ensure_loaded(self) -> None:
        if not self._loaded:
            self.reload()

    def selected_ids(self) -> List[str]:
        return list(self.type_combo.checkedItemsData() or [])  # type: ignore[attr-defined]

    def selected_texts(self) -> List[str]:
        return list(self.type_combo.checkedItems() or [])  # type: ignore[attr-defined]

    def set_selected_ids(self, ids: Sequence[str], emit: bool = True) -> None:
        targets = {str(v) for v in ids or []}
        self._apply_type_selection(targets, emit)

    # ------------------------------------------------------------------
    def _load_types(self) -> None:
        query_name = "TYPE"
        query_file = f"{self._module}_types.graphql"
        query = self._loader.load_query_by_module(query_name, query_file)

        edges = []
        after: Optional[str] = None
        while True:
            variables = {"first": self._PAGE_SIZE, "after": after}
            data = self._api.send_query(query, variables=variables) or {}
            connection = (data or {}).get(f"{self._module}Types") or {}
            page_edges = connection.get("edges") or []
            edges.extend(page_edges)

            page_info = connection.get("pageInfo") or {}
            has_next = bool(page_info.get("hasNextPage"))
            after = page_info.get("endCursor") if has_next else None
            if not has_next or not after:
                break

        self.type_combo.clear()
        self.group_combo.clear()
        self._group_map.clear()

        for edge in edges:
            node = (edge or {}).get("node") or {}
            type_id = node.get("id")
            label = node.get("name")
            group_name = (node.get("group") or {}).get("name") if isinstance(node.get("group"), dict) else None
            if not group_name:
                group_name = group_key(label)
            if type_id and label:
                self.type_combo.addItem(label, type_id)
                if group_name:
                    self._group_map.setdefault(group_name, []).append(type_id)

        for group_name in sorted(self._group_map.keys(), key=str.lower):
            self.group_combo.addItem(group_name, group_name)

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
        preferred_types = SettingsService().module_preferred_types(self._module) or ""
        ids = [token.strip() for token in str(preferred_types).split(",") if token.strip()]
        if ids:
            self.set_selected_ids(ids, emit=False)




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
