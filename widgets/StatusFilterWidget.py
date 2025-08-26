# -*- coding: utf-8 -*-
from typing import Optional, Union, List

from PyQt5.QtWidgets import QHBoxLayout, QListView
from PyQt5.QtCore import Qt, QCoreApplication

from .BaseFilterWidget import BaseFilterWidget
from .theme_manager import ThemeManager
from ..constants.file_paths import QssPaths
from ..utils.GraphQLQueryLoader import GraphQLQueryLoader
from ..utils.api_client import APIClient


class StatusFilterWidget(BaseFilterWidget):
    """
    Moodulipõhised staatused (PROJECTS/CONTRACTS). Pärib BaseFilterWidget:
    - lazy load, selection API, QGIS/fallback tugi.
    """

    def __init__(self, module_name: Union[str, object], lang_manager=None, parent=None, debug: Optional[bool] = None):
        super().__init__(parent)
        self._module = getattr(module_name, "value", module_name)
        self._lang = lang_manager
        self._api = APIClient(self._lang)
        self._loader = GraphQLQueryLoader(self._lang)
        self.set_debug(bool(debug))

        # UI
        layout = QHBoxLayout(self)
        # Add margins so shadow effect around combo is visible
        layout.setContentsMargins(4, 2, 4, 2)
        layout.setSpacing(2)

        # Allow override via class attr MAX_VISIBLE_ITEMS; use base default otherwise
        self.combo, self._uses_qgis = self._init_checkable_combo("StatusFilterCombo")
        layout.addWidget(self.combo)
        # Accent shadow
        try:
            self._apply_combo_shadow(self.combo)
        except Exception:
            pass

        # QGIS: kohe emit iga muutusega
        if self._uses_qgis and hasattr(self.combo, 'checkedItemsChanged'):
            self.combo.checkedItemsChanged.connect(lambda: self.selectionChanged.emit(self.selected_ids()))
        else:
            # Fallback: popupi list on checkable – ühendame pressi peale
            self.combo.setView(QListView(self.combo))
            self.combo.view().pressed.connect(self._on_item_pressed)

        # Initial theming now handled centrally by BaseFilterWidget.__init__ via retheme().
        self._loaded = False

    # --- fallback klikk ---
    def _on_item_pressed(self, index):
        # Toggle CheckStateRole
        m = self.combo.model()
        cur = m.data(index, Qt.CheckStateRole)
        nxt = Qt.Checked if cur in (None, Qt.Unchecked) else Qt.Unchecked
        m.setData(index, nxt, Qt.CheckStateRole)
        QCoreApplication.processEvents()
        self.selectionChanged.emit(self.selected_ids())

    # --- laadimine ---
    def _populate(self) -> None:
    # ...existing code...

        # 1) Lae päring
        query = self._loader.load_query("statuses", "ListModuleStatuses.graphql")

        
        # 2) Muutuja: plural
        module_plural = str(self._module).upper()
        if module_plural == "PROJECT":
            module_plural = "PROJECTS"
        elif module_plural == "CONTRACT":
            module_plural = "CONTRACTS"

        variables = {
            "first": 50,
            "after": None,
            "where": {"column": "MODULE", "value": module_plural},
        }
        data = self._api.send_query(query, variables=variables) or {}

        # 3) Nopi staatused
        statuses: List[dict] = []
        edges = ((data or {}).get("statuses") or {}).get("edges") or []
        for e in edges:
            n = (e or {}).get("node") or {}
            sid = n.get("id")
            name = n.get("name")
            if sid and name:
                statuses.append({"id": sid, "name": name})

        # 4) Täida combo
        self.combo.clear()
        for s in statuses:
            self.combo.addItem(s["name"], s["id"])
            # algseis unchecked (QGIS või fallback)
            try:
                self.combo.setItemCheckState(self.combo.count() - 1, Qt.Unchecked)  # type: ignore[attr-defined]
            except Exception:
                m = self.combo.model()
                idx = m.index(self.combo.count() - 1, 0)
                m.setData(idx, Qt.Unchecked, Qt.CheckStateRole)
        # Adjust popup to show all statuses if few
        self._auto_adjust_combo_popup(self.combo)

