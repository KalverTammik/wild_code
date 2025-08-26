# -*- coding: utf-8 -*-
from typing import Dict, List, Optional, Union, Any

from PyQt5.QtWidgets import QHBoxLayout, QComboBox, QListView, QSizePolicy
from PyQt5.QtCore import Qt, QCoreApplication

from .BaseFilterWidget import BaseFilterWidget
from .theme_manager import ThemeManager
from ..constants.file_paths import QssPaths
from ..utils.GraphQLQueryLoader import GraphQLQueryLoader
from ..utils.api_client import APIClient
from ..utils.filter_helpers import build_group_map


class TypeFilterWidget(BaseFilterWidget):
    # Unified control over popup height for both group and type combos
    MAX_VISIBLE_ITEMS = 12
    """
    Kahe rippmenüüga Type filter:
      - Grupid (tri-state): grupi märkimine (ON/OFF) -> märgib/mahavõtab kõik grupi tüübid.
      - Tüübid (multi-select): tegelik filtriallikas; selectionChanged emiteerib TYYPIDE ID-d.
    Pärib BaseFilterWidgetist: lazy load, selection API, QGIS/fallback tugi.
    """
    # NB: selectionChanged pärit baasist

    _TYPE_META: Dict[str, Dict[str, str]] = {
        "CONTRACT": {
            "dir": "CONTRACT",
            "file": "contract_types.graphql",
            "response_key": "contractTypes",
        },
        # vajadusel lisa PROJECT vms
    }

    def __init__(self, module_name: Union[str, object], lang_manager=None, parent=None, debug: Optional[bool] = None):
        super().__init__(parent)
        self._module = (getattr(module_name, "value", module_name) or "CONTRACT").upper()
        self._lang = lang_manager
        self._api = APIClient(self._lang)
        self._loader = GraphQLQueryLoader(self._lang)
        self.set_debug(bool(debug))

        self._uses_qgis_types = False
        self._group_to_type_ids: Dict[str, List[str]] = {}

        # UI
        layout = QHBoxLayout(self)
        # Add margins so shadows on both combos are visible
        layout.setContentsMargins(4, 2, 4, 2)
        layout.setSpacing(2)

            # Grupid (always fallback QComboBox, tri-state)
        self.group_combo = QComboBox(self)
        self.group_combo.setView(QListView(self.group_combo))
        self.group_combo.setSizeAdjustPolicy(QComboBox.AdjustToContents)
        try:
            self.group_combo.setMaxVisibleItems(self.MAX_VISIBLE_ITEMS)
        except Exception:
            pass
        layout.addWidget(self.group_combo)

        # Tüübid (QGIS checkable kui saadaval)
        self.type_combo, self._uses_qgis_types = self._init_checkable_combo("TypeFilterCombo", max_visible=self.MAX_VISIBLE_ITEMS)
        layout.addWidget(self.type_combo)
        # Accent shadows
        try:
            self._apply_combo_shadow(self.group_combo)
            self._apply_combo_shadow(self.type_combo)
        except Exception:
            pass

        # Fallback: tee type_combo popup checkable (toggle handler)
        if not self._uses_qgis_types:
            self.type_combo.setView(QListView(self.type_combo))
            self.type_combo.view().pressed.connect(self._on_type_pressed)
        else:
            # QGIS: iga muutus -> sünkroniseeri grupid + emit
            if hasattr(self.type_combo, "checkedItemsChanged"):
                self.type_combo.checkedItemsChanged.connect(self._on_type_selection_changed_qgis)  # type: ignore

        # Tri-state grupi toggle
        self.group_combo.view().pressed.connect(self._on_group_pressed)

        # Kompaktne “pill”
        self.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Preferred)

        # Initial theming now handled centrally by BaseFilterWidget.__init__ via retheme().
        self._loaded = False

    # --- laadimine ---
    def _meta(self) -> Dict[str, str]:
        info = self._TYPE_META.get(self._module)
        if not info:
            raise RuntimeError(f"No type mapping for module '{self._module}'")
        return info

    def _extract_edges(self, payload: Dict[str, Any], meta: Dict[str, str]) -> list:
        # Lubame nii {"data": {...}} kui ka lamedat dicti
        top = (payload.get("data") if isinstance(payload.get("data"), dict) else None) or payload
        root = top.get(meta["response_key"])
        edges = (root or {}).get("edges")
        return edges if isinstance(edges, list) else []

    def _populate(self) -> None:
        meta = self._meta()
        gql = self._loader.load_query(meta["dir"], meta["file"])
        data = self._api.send_query(gql, variables={"first": 50}) or {}
        edges = self._extract_edges(data, meta)

        # Tühjuse korral viisakas puhastus
        if not edges:
            try:
                self.type_combo.clear()
                self.group_combo.clear()
                if hasattr(self.type_combo, "setEditText"):
                    self.type_combo.setEditText("No types")
                if hasattr(self.group_combo, "setEditText"):
                    self.group_combo.setEditText("No groups")
            except Exception:
                pass
            return

        # (label,id) list + sort
        items: List[tuple] = []
        for e in edges:
            n = (e or {}).get("node") or {}
            label = n.get("name") or n.get("id") or "?"
            _id = n.get("id")
            items.append((label.lower(), label, _id))
        items.sort(key=lambda t: t[0])

        # Täida TÜÜBID (algseis unchecked)
        self.type_combo.clear()
        for _, label, _id in items:
            self.type_combo.addItem(label, _id)
            try:
                self.type_combo.setItemCheckState(self.type_combo.count() - 1, Qt.Unchecked)  # type: ignore[attr-defined]
            except Exception:
                m = self.type_combo.model()
                idx = m.index(self.type_combo.count() - 1, 0)
                m.setData(idx, Qt.Unchecked, Qt.CheckStateRole)

        # Täida GRUPID (tri-state)
        self._group_to_type_ids = build_group_map(edges)  # { group_name: [type_id,...] }
        self.group_combo.clear()
        for g in sorted(self._group_to_type_ids.keys(), key=lambda s: s.lower()):
            self.group_combo.addItem(g, g)
            idx = self.group_combo.model().index(self.group_combo.count() - 1, 0)
            self.group_combo.model().setData(idx, Qt.Unchecked, Qt.CheckStateRole)

        # Sünkrooni tri-state
        self._recompute_group_states()
        # Adjust popups for small lists (types & groups)
        self._auto_adjust_combo_popup(self.type_combo)
        self._auto_adjust_combo_popup(self.group_combo)

    # --- selection loogika ---
    def _get_type_row_by_id(self, type_id: str) -> int:
        for row in range(self.type_combo.count()):
            if self.type_combo.itemData(row) == type_id:
                return row
        return -1

    def _set_type_state(self, row: int, state: int) -> None:
        if row < 0:
            return
        try:
            self.type_combo.setItemCheckState(row, state)  # type: ignore[attr-defined]
        except Exception:
            m = self.type_combo.model()
            idx = m.index(row, 0)
            m.setData(idx, state, Qt.CheckStateRole)

    def _recompute_group_states(self) -> None:
        m = self.group_combo.model()
        for row in range(self.group_combo.count()):
            gname = self.group_combo.itemData(row)
            tids = self._group_to_type_ids.get(gname, [])
            if not tids:
                m.setData(m.index(row, 0), Qt.Unchecked, Qt.CheckStateRole)
                continue
            total = len(tids)
            sel = 0
            for tid in tids:
                trow = self._get_type_row_by_id(tid)
                if trow >= 0 and self._row_is_checked(self.type_combo, trow):
                    sel += 1
            if sel == 0:
                st = Qt.Unchecked
            elif sel == total:
                st = Qt.Checked
            else:
                st = Qt.PartiallyChecked
            m.setData(m.index(row, 0), st, Qt.CheckStateRole)

    def _row_is_checked(self, combo: QComboBox, row: int) -> bool:
        try:
            m = combo.model()
            idx = m.index(row, 0)
            return m.data(idx, Qt.CheckStateRole) == Qt.Checked
        except Exception:
            return False

    # --- handlers ---
    def _on_group_pressed(self, index):
        m = self.group_combo.model()
        cur = m.data(index, Qt.CheckStateRole)
        turning_on = (cur in (None, Qt.Unchecked, Qt.PartiallyChecked))
        m.setData(index, Qt.Checked if turning_on else Qt.Unchecked, Qt.CheckStateRole)

        gname = self.group_combo.itemData(index.row())
        tids = self._group_to_type_ids.get(gname, [])
        for tid in tids:
            row = self._get_type_row_by_id(tid)
            self._set_type_state(row, Qt.Checked if turning_on else Qt.Unchecked)

        self._recompute_group_states()
        self.selectionChanged.emit(self.selected_ids())

    def _on_type_pressed(self, _index):
        QCoreApplication.processEvents()
        self._recompute_group_states()
        self.selectionChanged.emit(self.selected_ids())

    def _on_type_selection_changed_qgis(self):
        self._recompute_group_states()
        self.selectionChanged.emit(self.selected_ids())

    # --- theming ---
    def retheme(self):
        try:
            ThemeManager.apply_module_style(self, [QssPaths.MAIN, QssPaths.COMBOBOX])
        except Exception:
            pass

    # Lazy load
    def showEvent(self, e):
        try:
            self.ensure_loaded()
        except Exception:
            pass
        super().showEvent(e)
