# -*- coding: utf-8 -*-
from typing import Optional, Union, List

from PyQt5.QtWidgets import QHBoxLayout, QListView
from PyQt5.QtCore import Qt, QCoreApplication

from .BaseFilterWidget import BaseFilterWidget
from .theme_manager import ThemeManager
from ..constants.file_paths import QssPaths
from ..utils.GraphQLQueryLoader import GraphQLQueryLoader
from ..utils.api_client import APIClient


class TagsFilterWidget(BaseFilterWidget):
    """
    Moodulipõhised tunnused (tags). Pärib BaseFilterWidget:
    - lazy load, selection API, QGIS/fallback tugi.
    """

    def __init__(self, module_name: Union[str, object], lang_manager=None, parent=None, debug: Optional[bool] = None):
        super().__init__(parent)
        self._module = getattr(module_name, "value", module_name)
        self._lang = lang_manager
        self._api = APIClient(self._lang)
        self._loader = GraphQLQueryLoader(self._lang)
        self.set_debug(bool(debug))

        if self._debug:
            print(f"[TagsFilterWidget] Initialized with module: {self._module}")

        # UI
        layout = QHBoxLayout(self)
        # Add margins so shadow effect around combo is visible
        layout.setContentsMargins(4, 2, 4, 2)
        layout.setSpacing(2)

        # Allow override via class attr MAX_VISIBLE_ITEMS; use base default otherwise
        self.combo, self._uses_qgis = self._init_checkable_combo("TagsFilterCombo")
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
        try:
            # 1) Lae päring
            query = self._loader.load_query("tags", "ListModuleTags.graphql")

            # 2) Muutuja: module plural (for filtering tags by module if needed)
            module_plural = str(self._module).upper()
            if self._debug:
                print(f"[TagsFilterWidget] Converting module '{self._module}' to uppercase: '{module_plural}'")

            if module_plural == "PROJECT":
                module_plural = "PROJECTS"
            elif module_plural == "CONTRACT":
                module_plural = "CONTRACTS"
            elif module_plural == "PROJECTSMODULE":
                module_plural = "PROJECTS"
            elif module_plural == "CONTRACTMODULE":
                module_plural = "CONTRACTS"

            if self._debug:
                print(f"[TagsFilterWidget] Final module_plural: '{module_plural}'")

            # For now, load all tags. Later we can filter by module if the API supports it
            variables = {
                "first": 50,
                "after": None,
                "where": {"column": "MODULE", "value": module_plural},
            }
            if self._debug:
                print(f"[TagsFilterWidget] Sending query with variables: {variables}")

            data = self._api.send_query(query, variables=variables) or {}

            if self._debug:
                print(f"[TagsFilterWidget] API response: {data}")

            # 3) Nopi tunnused
            tags: List[dict] = []
            edges = ((data or {}).get("tags") or {}).get("edges") or []

            if self._debug:
                print(f"[TagsFilterWidget] Found {len(edges)} tag edges")

            for e in edges:
                n = (e or {}).get("node") or {}
                sid = n.get("id")
                name = n.get("name")
                if sid and name:
                    tags.append({"id": sid, "name": name})
                    if self._debug:
                        print(f"[TagsFilterWidget] Added tag: {name} (id: {sid})")

            if self._debug:
                print(f"[TagsFilterWidget] Total tags loaded: {len(tags)}")

            # 4) Täida combo
            self.combo.clear()
            for t in tags:
                self.combo.addItem(t["name"], t["id"])
                # algseis unchecked (QGIS või fallback)
                try:
                    self.combo.setItemCheckState(self.combo.count() - 1, Qt.Unchecked)  # type: ignore[attr-defined]
                except Exception:
                    m = self.combo.model()
                    idx = m.index(self.combo.count() - 1, 0)
                    m.setData(idx, Qt.Unchecked, Qt.CheckStateRole)
            # Adjust popup to show all tags if few
            self._auto_adjust_combo_popup(self.combo)

        except Exception as e:
            if self._debug:
                print(f"[TagsFilterWidget] Error loading tags: {e}")
                import traceback
                print(f"[TagsFilterWidget] Traceback: {traceback.format_exc()}")
            # Clear combo and add error message
            self.combo.clear()
            self.combo.addItem(f"Error: {str(e)[:50]}...")
            # Disable the widget
            self.combo.setEnabled(False)
