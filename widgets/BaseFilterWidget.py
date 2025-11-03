# -*- coding: utf-8 -*-
from typing import List, Optional, Sequence
from PyQt5.QtWidgets import QWidget, QComboBox, QListView, QSizePolicy, QHBoxLayout
from qgis.gui import QgsCheckableComboBox  
from PyQt5.QtCore import Qt, QCoreApplication, pyqtSignal
from PyQt5.QtWidgets import QGraphicsDropShadowEffect
from PyQt5.QtGui import QColor

import os
from ..widgets.theme_manager import ThemeManager
from ..constants.file_paths import QssPaths
from PyQt5.QtWidgets import QWidget, QComboBox, QListView, QSizePolicy, QHBoxLayout
from PyQt5.QtWidgets import QGraphicsDropShadowEffect
from PyQt5.QtWidgets import QPushButton  # NEW



# --- helpers: combo inits ---
DEFAULT_MAX_VISIBLE_ITEMS = 12

class BaseFilterWidget(QWidget):
    """Baasklass moodulipõhiste filter-widget'ite jaoks.
    - Pakub lazy load, selection API, QGIS/fallback tugi.
    - Alamklassid täidavad combod _populate() meetodis.
    """
    selectionChanged = pyqtSignal(list)

    # --- ctor ---
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._loaded = False
        self._debug = False
        self.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Preferred)
        ThemeManager.apply_module_style(self, [QssPaths.MAIN, QssPaths.COMBOBOX])


    def retheme(self) -> None:

        ThemeManager.apply_module_style(self, [QssPaths.MAIN, QssPaths.COMBOBOX])


    # --- lazy load ---
    def ensure_loaded(self) -> None:
        if not self._loaded:
            self.reload()

    def reload(self) -> None:
        """Lae sisu uuesti, märgi laadituks ja emiteeri kehtiv valik."""
        if hasattr(self, "_populate"):
            self._populate()  # alamklass täidab combod
        self._loaded = True
        self.selectionChanged.emit(self.selected_ids())

    # --- debug ---
    def set_debug(self, enabled: bool) -> None:
        self._debug = bool(enabled)

    def _init_checkable_combo(self, object_name: str = "", max_visible: int = None):

        """Loo ja tagasta checkable combo, eelistatult QgsCheckableComboBox.
        - Määrab objectName ja maxVisibleItems (kui antud)."""

        combo = QgsCheckableComboBox(self)
        if object_name:
            combo.setObjectName(object_name)
        mv = max_visible if max_visible is not None else DEFAULT_MAX_VISIBLE_ITEMS
        combo.setMaxVisibleItems(int(mv))
        combo.view().setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        return combo

    def _set_row_checkstate(self, combo: QComboBox, row: int, state: int) -> None:
        try:
            # QGIS combo (pakub meetodi)
            combo.setItemCheckState(row, state)  # type: ignore[attr-defined]
        except Exception:
            # Fallback mudel: CheckStateRole
            m = combo.model()
            idx = m.index(row, 0)
            m.setData(idx, state, Qt.CheckStateRole)

    def _row_checkstate(self, combo: QComboBox, row: int) -> int:
        try:
            m = combo.model()
            idx = m.index(row, 0)
            st = m.data(idx, Qt.CheckStateRole)
            return Qt.Unchecked if st is None else int(st)
        except Exception:
            return Qt.Unchecked
    
    # --- selection api (universaalne) ---
    def selected_ids(self) -> List[str]:
        """
        Tagastab valitud ID-d. Otsib esmalt 'type_combo', siis 'combo' atribuuti.
        - QGIS variandis loeb checkedItems() tekstid ja mapib id-deks.
        - Fallbackis loeb CheckStateRole.
        """
        combo = getattr(self, 'type_combo', getattr(self, 'combo', None))
        res: List[str] = []
        if combo is None:
            return res

        # QGIS checkedItems (tekstide nimekiri)
        if hasattr(combo, "checkedItems"):
            try:
                checked_texts = set(combo.checkedItems())  # type: ignore[attr-defined]
                for row in range(combo.count()):
                    if combo.itemText(row) in checked_texts:
                        res.append(combo.itemData(row))
                return res
            except Exception:
                pass

        # Fallback: CheckStateRole
        m = combo.model()
        for row in range(combo.count()):
            idx = m.index(row, 0)
            if m.data(idx, Qt.CheckStateRole) == Qt.Checked:
                res.append(combo.itemData(row))
        if self._debug:
            pass  # Debug print removed
        return res

    def set_selected_ids(self, ids: Sequence[str]) -> None:
        """Märgi antud id-d valituks (vastavalt QGIS/fallback combole) ja emiteeri selectionChanged."""
        ids_set = set(ids or [])
        combo = getattr(self, 'type_combo', getattr(self, 'combo', None))
        if combo is None:
            self.selectionChanged.emit(list(ids_set))
            return

        try:
            for row in range(combo.count()):
                val = combo.itemData(row)
                state = Qt.Checked if val in ids_set else Qt.Unchecked
                self._set_row_checkstate(combo, row, state)
                QCoreApplication.processEvents()
        except Exception:
            pass

        self.selectionChanged.emit(list(ids_set))

    def _apply_combo_shadow(self, combo: QComboBox) -> None:
        shadow = QGraphicsDropShadowEffect(combo)
        combo.setGraphicsEffect(shadow)
        shadow.setBlurRadius(14)
        shadow.setXOffset(0)
        shadow.setYOffset(1)
        shadow.setColor(QColor(9, 144, 143, 60))

    def _auto_adjust_combo_popup(self, combo: QComboBox) -> None:
        """Adjust combo popup height to fit all items if within DEFAULT_MAX_VISIBLE_ITEMS,
        otherwise limit to DEFAULT_MAX_VISIBLE_ITEMS with scrollbar."""

        count = combo.count() 
        view = combo.view()
        if count and count <= DEFAULT_MAX_VISIBLE_ITEMS:
            combo.setMaxVisibleItems(count)
            row_h = view.sizeHintForRow(0)
            if row_h <= 0:
                row_h = 24
            extra = 8
            margins = view.contentsMargins()
            extra += margins.top() + margins.bottom()
            view.setMinimumHeight(row_h * count + extra)
            view.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        else:
            combo.setMaxVisibleItems(DEFAULT_MAX_VISIBLE_ITEMS)
            row_h = view.sizeHintForRow(0)
            if row_h <= 0:
                row_h = 24
            extra = 8
            margins = view.contentsMargins()
            extra += margins.top() + margins.bottom()
            view.setMinimumHeight(row_h * DEFAULT_MAX_VISIBLE_ITEMS + extra)
            view.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)



class FilterRefreshHelper:
    """
    Shared helper that creates a refresh button widget and handles its click.
    Pass the module (owner) so we can clear filters and trigger reload.
    """
    def __init__(self, owner: QWidget):
        self._owner = owner  # expected to have toolbar_area, reset_feed_session, feed_load_engine/process_next_batch

    def make_filter_refresh_button(self, parent: Optional[QWidget] = None) -> QWidget:
        """
        Returns a QWidget container holding a styled round refresh QPushButton.
        Safe to add into layouts that accept only widgets.
        """
        container = QWidget(parent)
        layout = QHBoxLayout(container)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(0)

        btn = QPushButton("✖", container)
        btn.setObjectName("FeedRefreshButton")
        btn.setAutoDefault(False)
        btn.setDefault(False)
        size_px = 28
        btn.setFixedSize(size_px, size_px)
        btn.setStyleSheet(
            "color: #b0b0b0; font-size: 14px; background: transparent; border: 0px;"
            f"border-radius: {int(size_px/2)}px; padding: 0px;"
        )
        btn.clicked.connect(self._on_refresh_clicked)  # type: ignore[attr-defined]
        
        layout.addWidget(btn)
        return container

    def _on_refresh_clicked(self):
        """Hard refresh: reset session, clear filters, and trigger a fresh load."""
        owner = self._owner
        # Clear filters first
        try:
            toolbar = getattr(owner, 'toolbar_area', None)
            if toolbar and hasattr(toolbar, 'filter_widgets'):
                for _name, widget in list(toolbar.filter_widgets.items()):
                    try:
                        if hasattr(widget, 'set_selected_ids'):
                            widget.set_selected_ids([])  # type: ignore[attr-defined]
                    except Exception:
                        pass
        except Exception:
            pass

        # Reset preference flags if present
        for flag in ('_status_preferences_loaded', '_type_preferences_loaded', '_tags_preferences_loaded'):
            if hasattr(owner, flag):
                try:
                    setattr(owner, flag, False)
                except Exception:
                    pass

        # Reset feed session
        try:
            if hasattr(owner, 'reset_feed_session') and callable(owner.reset_feed_session):
                owner.reset_feed_session()
        except Exception:
            pass

        # Trigger engine schedule or fallback batch
        try:
            eng = getattr(owner, 'feed_load_engine', None)
            if eng and hasattr(eng, 'schedule_load'):
                eng.schedule_load()
            else:
                if hasattr(owner, 'process_next_batch') and callable(owner.process_next_batch):
                    owner.process_next_batch()
        except Exception:
            pass