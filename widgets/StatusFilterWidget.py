# -*- coding: utf-8 -*-
from typing import Optional, Union, List

from PyQt5.QtWidgets import QHBoxLayout
from PyQt5.QtCore import Qt, QCoreApplication

from .BaseFilterWidget import BaseFilterWidget
from ..constants.file_paths import STATUS_QUERIES
from ..utils.GraphQLQueryLoader import GraphQLQueryLoader
from ..utils.api_client import APIClient
from ..languages.language_manager import LanguageManager
from ..utils.url_manager import Module



class StatusFilterWidget(BaseFilterWidget):

    def __init__(self, module_name: Union[str, object],  parent=None, debug: Optional[bool] = None):
        super().__init__(parent)
        self._lang = LanguageManager()
        self._api = APIClient()
        self._loader = GraphQLQueryLoader(self._lang)
        self.set_debug(bool(debug))
        self.query_file = "ListModuleStatuses.graphql"
        self._module = module_name
        self.filter_module = "statuses"
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 2, 4, 2)
        layout.setSpacing(1)

        self.combo = self._init_checkable_combo("StatusFilterCombo")

        layout.addWidget(self.combo)
        # Accent shadow
        self._apply_combo_shadow(self.combo)

        # Add tooltip for clarity
        tooltip = LanguageManager().translate("Status Filter")
        self.combo.setToolTip(tooltip)

        # QGIS: kohe emit iga muutusega
        self.combo.checkedItemsChanged.connect(lambda: self.selectionChanged.emit(self.selected_ids()))

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

    def _populate(self) -> None:
        # Use QueryPaths key name, not raw folder constant
        status_module = Module.STATUSES.value
        print(f"[StatusFilterWidget _populate] Loading query for module: {status_module}")
        key_raw = status_module[:-2] if len(status_module) > 2 else status_module
        status_query_key = key_raw.upper()     # "STATUS"
        print(f"[StatusFilterWidget _populate] status_query_key: {status_query_key}")
        try:
            query = self._loader.load_query(status_query_key, self.query_file)
            
            module_plural = self._module.plural(upper=True)
        
            variables = {
                "first": 50,
                "after": None,
                "where": {"column": "MODULE", "value": module_plural},
            }
            
            data = self._api.send_query(query, variables=variables) or {}
    
            statuses: List[dict] = []

            edges = ((data or {}).get(self.filter_module) or {}).get("edges") or []
                    
            for e in edges:
                n = (e or {}).get("node") or {}
                sid = n.get("id")
                name = n.get("name")
                if sid and name:
                    statuses.append({"id": sid, "name": name})
            
            self.combo.clear()
            for s in statuses:
                self.combo.addItem(s["name"], s["id"])
                try:
                    self.combo.setItemCheckState(self.combo.count() - 1, Qt.Unchecked)  # type: ignore[attr-defined]
                except Exception:
                    m = self.combo.model()
                    idx = m.index(self.combo.count() - 1, 0)
                    m.setData(idx, Qt.Unchecked, Qt.CheckStateRole)
            # Adjust popup to show all statuses if few
            self._auto_adjust_combo_popup(self.combo)
            
        except Exception as e:
            # Clear combo and add error message
            self.combo.clear()
            self.combo.addItem(f"Error: {str(e)[:50]}...")
            # Disable the widget
            self.combo.setEnabled(False)
