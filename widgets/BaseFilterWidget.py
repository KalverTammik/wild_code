# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import List, Optional, Sequence, Callable, Tuple
from functools import partial

from qgis.gui import QgsCheckableComboBox
from PyQt5.QtCore import Qt, QCoreApplication, QSignalBlocker, pyqtSignal
from ..widgets.theme_manager import ThemeManager, styleExtras, ThemeShadowColors
from ..constants.file_paths import QssPaths
from PyQt5.QtWidgets import QWidget, QComboBox, QSizePolicy


# --- helpers: combo inits ---
DEFAULT_MAX_VISIBLE_ITEMS = 12


def _configure_combo_visibility(combo, max_visible: int | None):
    """Shared config for any combo-like widget."""
    mv = max_visible if max_visible is not None else DEFAULT_MAX_VISIBLE_ITEMS
    combo.setMaxVisibleItems(int(mv))
    print(f"[BaseFilterWidget] _apply_common_combo_config: setMaxVisibleItems to {mv}")
    combo.view().setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)


def _try_apply_shadow(widget: QWidget, *, color, alpha_level, blur_radius=5, x_offset=1, y_offset=1):
    try:
        styleExtras.apply_chip_shadow(
            widget,
            color=color,
            alpha_level=alpha_level,
            blur_radius=blur_radius,
            x_offset=x_offset,
            y_offset=y_offset,
        )
    except Exception:
        # No-op if effect fails (e.g., headless testing)
        pass

class BaseFilterWidget(QWidget):
    """Baasklass moodulipõhiste filter-widget'ite jaoks.
    - Pakub lazy load, selection API, QGIS/fallback tugi.
    - Alamklassid täidavad combod _populate() meetodis.
    """

    selectionChanged = pyqtSignal(list, list)

    # --- ctor ---
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._loaded = False
        self._debug = False
        self._teardown_functions = []  # List of teardown functions for forwarders
        self._combo = None  # The main combo for selection
        self._combo_signal_pairs: List[Tuple[object, Callable[[], None]]] = []
        self.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Preferred)
        ThemeManager.apply_module_style(self, [QssPaths.MAIN, QssPaths.COMBOBOX])

    def retheme(self) -> None:

        ThemeManager.apply_module_style(self, [QssPaths.MAIN, QssPaths.COMBOBOX])

        self._populate()  # alamklass täidab combod


    def _init_checkable_combo(
        self,
        object_name: str = "",
        max_visible: int | None = None,
        with_shadow: bool = False,
        color: "ThemeShadowColors" = ThemeShadowColors.BLUE,
        alpha_level: str = "medium",
        widget_class: type = QgsCheckableComboBox,  # default = checkable everywhere
    ):
        """Generic combo factory. Returns a combo of type widget_class (default: QgsCheckableComboBox)."""
        combo = widget_class(self)
        if object_name:
            combo.setObjectName(object_name)

        _configure_combo_visibility(combo, max_visible)

        if with_shadow:
            _try_apply_shadow(combo, color=color, alpha_level=alpha_level)

        self._register_checkable_combo(combo)

        return combo

    def _register_checkable_combo(self, combo) -> None:
        """Ensure combo emits BaseFilterWidget.selectionChanged events when possible."""
        if not self._is_checkable_combo(combo):
            return

        def _forward():
            self._emit_selection_change(combo)

        try:
            combo.checkedItemsChanged.connect(_forward)  # type: ignore[attr-defined]
            self._combo_signal_pairs.append((combo, _forward))
        except Exception:
            pass

        
    def _set_row_checkstate(self, combo: QComboBox, row: int, state: int) -> None:
        '''Set the checkstate of a given row in the combo, using QGIS method if available, otherwise fallback.'''
        print(f"[BaseFilterWidget _set_row_checkstate] Setting row {row} state to {state} using QGIS combo method")
        combo.setItemCheckState(row, state)  # type: ignore[attr-defined]

    def _row_checkstate(self, combo: QComboBox, row: int) -> int:
        print(f"[BaseFilterWidget _row_checkstate] Getting checkstate for row {row}")
        try:
            m = combo.model()
            print(f"[BaseFilterWidget _row_checkstate] Model obtained: {m}")    
            idx = m.index(row, 0)
            st = m.data(idx, Qt.CheckStateRole)
            return Qt.Unchecked if st is None else int(st)
        except Exception:
            return Qt.Unchecked
    
    # --- selection api (universaalne) ---
    def selected_ids(self, combo: Optional[QComboBox] = None) -> List[str]:
        """
        Tagastab valitud ID-d antud combo jaoks.
        - QGIS variandis loeb checkedItems() tekstid ja mapib id-deks.
        - Fallbackis loeb CheckStateRole.
        """
        target = combo or self.combo
        if target is None:
            return []
        _texts, ids = self._collect_checked_payload(target)
        return [str(i) for i in ids if i not in (None, "")]

    def selected_texts(self, combo: Optional[QComboBox] = None) -> List[str]:
        target = combo or self.combo
        if target is None:
            return []
        texts, _ids = self._collect_checked_payload(target)
        return texts

    def set_selected_ids(self, combo_or_ids, ids: Sequence[str] | None = None, *, emit: bool = True) -> None:
        """Märgi antud id-d valituks (vastavalt QGIS/fallback combole)."""
        combo = combo_or_ids if self._is_combo_widget(combo_or_ids) else self.combo
        payload = ids if self._is_combo_widget(combo_or_ids) else combo_or_ids
        if combo is None:
            return

        ids_set = {str(v) for v in (payload or [])}
        blocker_combo = QSignalBlocker(combo)
        for row in range(combo.count()):
            val = combo.itemData(row)
            state = Qt.Checked if str(val) in ids_set else Qt.Unchecked
            self._set_row_checkstate(combo, row, state)
            QCoreApplication.processEvents()

        del blocker_combo

        if emit:
            self._emit_selection_change(combo)

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

    @property
    def combo(self):
        """Get the main combo widget for selection."""
        return self._combo

    @combo.setter
    def combo(self, value):
        """Set the main combo widget."""
        self._combo = value

    def _is_checkable_combo(self, candidate) -> bool:
        """Return True if the object exposes the checkedItemsChanged signal."""
        return hasattr(candidate, "checkedItemsChanged")

    def _is_combo_widget(self, candidate) -> bool:
        return hasattr(candidate, "model") and hasattr(candidate, "count")

    def _collect_checked_payload(self, combo: QComboBox) -> Tuple[List[str], List[object]]:
        texts: List[str] = []
        ids: List[object] = []

        if combo is None:
            return texts, ids

        if hasattr(combo, "checkedItems"):
            try:
                texts = list(combo.checkedItems())  # type: ignore[attr-defined]
            except Exception:
                texts = []
        if hasattr(combo, "checkedItemsData"):
            try:
                ids = list(combo.checkedItemsData())  # type: ignore[attr-defined]
            except Exception:
                ids = []

        if not ids:
            try:
                model = combo.model()
                for row in range(combo.count()):
                    idx = model.index(row, 0)
                    if model.data(idx, Qt.CheckStateRole) == Qt.Checked:
                        texts.append(combo.itemText(row))
                        ids.append(combo.itemData(row))
            except Exception:
                pass

        return texts, ids

    def _emit_selection_change(self, combo: Optional[QComboBox] = None) -> None:
        target = combo or self.combo
        if target is None:
            return
        texts, ids = self._collect_checked_payload(target)
        try:
            self.selectionChanged.emit(texts, ids)
        except Exception:
            pass

    def _resolve_forwarder_targets(self) -> List[object]:
        """Determine which combo widgets should forward their selection changes."""
        candidates = []
        seen_ids = set()

        for attr_name in ("_combo", "combo", "type_combo", "status_combo", "tags_combo"):
            candidate = getattr(self, attr_name, None)
            if candidate and self._is_checkable_combo(candidate) and id(candidate) not in seen_ids:
                candidates.append(candidate)
                seen_ids.add(id(candidate))

        if not candidates:
            for value in self.__dict__.values():
                if self._is_checkable_combo(value) and id(value) not in seen_ids:
                    candidates.append(value)
                    seen_ids.add(id(value))

        return candidates

    def bind_selection_forwarders(self, target_slot: Callable[[str, List[str], List[str]], None]) -> Callable[[], None]:
        """
        Bind combo checkedItemsChanged signals to forward to target_slot with (name, texts, ids).
        Returns a teardown function to disconnect.
        """
        combos = self._resolve_forwarder_targets()
        if not combos:
            raise ValueError("No combo available to bind forwarders")

        local_teardowns: List[Callable[[], None]] = []

        for combo in combos:
            def make_forwarder(target_combo):
                def _forwarder():
                    texts, ids = self._collect_checked_payload(target_combo)
                    name = getattr(self, 'name', self.__class__.__name__)
                    target_slot(name, texts, ids)
                return _forwarder

            forwarder = make_forwarder(combo)
            combo.checkedItemsChanged.connect(forwarder)  # type: ignore[attr-defined]

            def make_teardown(target_combo, target_forwarder):
                def _teardown():
                    try:
                        target_combo.checkedItemsChanged.disconnect(target_forwarder)  # type: ignore[attr-defined]
                    except Exception:
                        pass
                return _teardown

            local_teardowns.append(make_teardown(combo, forwarder))

        def teardown():
            for td in local_teardowns:
                td()

        self._teardown_functions.append(teardown)
        return teardown

    def deactivate_forwarders(self):
        """Deactivate all bound forwarders."""
        for teardown in self._teardown_functions:
            teardown()
        self._teardown_functions.clear()

    # --- lifecycle helpers ---
    def reload(self) -> None:
        populate = getattr(self, "_populate", None)
        if callable(populate):
            populate()

    def ensure_loaded(self) -> None:
        if getattr(self, "_loaded", False):
            return
        self._loaded = True
        self.reload()