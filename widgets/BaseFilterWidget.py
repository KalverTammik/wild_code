# -*- coding: utf-8 -*-
from typing import Iterable, List, Optional, Sequence, Tuple
from PyQt5.QtWidgets import QWidget, QComboBox, QListView, QSizePolicy, QHBoxLayout
from PyQt5.QtCore import Qt, QCoreApplication, pyqtSignal
import os
from ..widgets.theme_manager import ThemeManager
from ..constants.file_paths import QssPaths, StylePaths

class BaseFilterWidget(QWidget):
    """
    Ühine baasklass kõigile filter-widgetidele (Status, Type, Tags ...).

    Ühtlustab:
    - lazy load: ensure_loaded() → reload() → _populate()
    - selection API: selected_ids(), set_selected_ids(ids)
    - QGIS QgsCheckableComboBox tugi + fallback QComboBox checkable mudel.
    - kompaktsed pillid (Maximum x Preferred) ja AdjustToContents fallback-combodele.
    """
    selectionChanged = pyqtSignal(list)

    # --- ctor ---
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._loaded = False
        self._debug = False
        self.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Preferred)
        # Apply initial theme (MAIN + COMBOBOX) so subclasses do not need
        # to duplicate ThemeManager calls in their __init__.
        try:
            self.retheme()
        except Exception:
            pass

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

    # --- helpers: combo inits ---
    DEFAULT_MAX_VISIBLE_ITEMS = 12

    def _init_checkable_combo(self, object_name: str = "", max_visible: int = None):
        """
    Eelistab QGIS QgsCheckableComboBox'i; fallback on tavaline QComboBox, mille popup on checkable.
    Stiil rakendub läbi `ThemeManager` ja `main.qss`; vältime otse QSS-failide lugemist siin.
    Tagastab (combo, uses_qgis: bool).
        """
    # Styling is applied via ThemeManager.apply_module_style and the
    # widget's retheme() method; do not read QSS files here.
        try:
            from qgis.gui import QgsCheckableComboBox  # type: ignore
            combo = QgsCheckableComboBox(self)
            if object_name:
                combo.setObjectName(object_name)
            mv = max_visible if max_visible is not None else getattr(self, 'MAX_VISIBLE_ITEMS', self.DEFAULT_MAX_VISIBLE_ITEMS)
            try:
                combo.setMaxVisibleItems(int(mv))
            except Exception:
                pass
            combo.view().setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
            # Styling is applied globally via ThemeManager.apply_module_style and
            # the widget's retheme() method; avoid per-combo stylesheet overrides here.
            return combo, True
        except Exception:
            combo = QComboBox(self)
            if object_name:
                combo.setObjectName(object_name)
            combo.setView(QListView(combo))
            combo.view().setAlternatingRowColors(True)
            combo.setInsertPolicy(QComboBox.NoInsert)
            combo.setEditable(False)
            try:
                combo.setSizeAdjustPolicy(QComboBox.AdjustToContents)
            except Exception:
                pass
            mv = max_visible if max_visible is not None else getattr(self, 'MAX_VISIBLE_ITEMS', self.DEFAULT_MAX_VISIBLE_ITEMS)
            try:
                combo.setMaxVisibleItems(int(mv))
            except Exception:
                pass
            combo.view().setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
            # Styling is applied globally via ThemeManager.apply_module_style and
            # the widget's retheme() method; avoid per-combo stylesheet overrides here.
            return combo, False

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

    # --- popup sizing helper ---
    def _auto_adjust_combo_popup(self, combo: QComboBox) -> None:
        """Ensure small combos show all items without an unnecessary scrollbar.
        - If total items <= DEFAULT_MAX_VISIBLE_ITEMS: expand view height, disable scrollbar.
        - Else: restore normal policy.
        Safe no-op on errors.
        """
        try:
            count = combo.count()
            default_cap = getattr(self, 'DEFAULT_MAX_VISIBLE_ITEMS', 12)
            view = combo.view()
            if count and count <= default_cap:
                try:
                    combo.setMaxVisibleItems(count)
                except Exception:
                    pass
                # Compute row height (fallback 24)
                try:
                    row_h = view.sizeHintForRow(0)
                    if row_h <= 0:
                        row_h = 24
                except Exception:
                    row_h = 24
                extra = 8
                try:
                    margins = view.contentsMargins()
                    extra += margins.top() + margins.bottom()
                except Exception:
                    pass
                view.setMinimumHeight(row_h * count + extra)
                try:
                    view.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
                except Exception:
                    pass
            else:
                # Restore defaults for larger lists
                try:
                    combo.setMaxVisibleItems(default_cap)
                except Exception:
                    pass
                try:
                    view.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
                except Exception:
                    pass
        except Exception:
            pass

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

    def retheme(self) -> None:
        """
        Re-apply the module main QSS and refresh any combo widgets so they pick up
        the new theme at runtime. This method is called by PluginDialog's
        `_retheme_dynamic_children()` sweep when the user toggles theme.
        """
        try:
            # Reapply both main (for general style) and centralized combobox styling
            ThemeManager.apply_module_style(self, [QssPaths.MAIN, QssPaths.COMBOBOX])
        except Exception:
            pass
        # Re-apply accent glow to existing combos
        try:
            self._apply_combo_shadows()
        except Exception:
            pass
        # Ensure padding so shadow isn't clipped
        try:
            self._ensure_shadow_padding()
        except Exception:
            pass

    # --- visual enhancement: accent shadow (matches HeaderWidget search field) ---
    def _apply_combo_shadow(self, combo: QComboBox) -> None:
        try:
            from PyQt5.QtWidgets import QGraphicsDropShadowEffect
            from PyQt5.QtGui import QColor
            # Avoid stacking multiple effects: reuse if already shadow
            eff = combo.graphicsEffect()
            if eff and hasattr(eff, 'setBlurRadius') and isinstance(eff, QGraphicsDropShadowEffect):
                shadow = eff  # reuse
            else:
                shadow = QGraphicsDropShadowEffect(combo)
                combo.setGraphicsEffect(shadow)
            # Unified accent color (teal) with subtle alpha; same as HeaderWidget searchEdit
            shadow.setBlurRadius(14)
            shadow.setXOffset(0)
            shadow.setYOffset(1)
            shadow.setColor(QColor(9, 144, 143, 60))
        except Exception:
            pass

    def _apply_combo_shadows(self) -> None:
        try:
            for combo in self.findChildren(QComboBox):
                self._apply_combo_shadow(combo)
        except Exception:
            pass

    def _ensure_shadow_padding(self) -> None:
        """Guarantee minimal margins so drop shadows are visible (not tightly clipped)."""
        lay = self.layout()
        if isinstance(lay, QHBoxLayout):
            l, t, r, b = lay.getContentsMargins()
            # Desired minimal shadow margins
            min_l, min_t, min_r, min_b = 4, 2, 4, 2
            if l < min_l or t < min_t or r < min_r or b < min_b:
                lay.setContentsMargins(max(l, min_l), max(t, min_t), max(r, min_r), max(b, min_b))
