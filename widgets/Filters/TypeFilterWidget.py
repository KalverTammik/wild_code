# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Dict, List, Optional, Sequence

from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QScrollArea, QSizePolicy, QVBoxLayout, QWidget
from qgis.gui import QgsCheckableComboBox

from ...languages.language_manager import LanguageManager
from ...languages.translation_keys import TranslationKeys
from ...python.workers import FunctionWorker, start_worker
from ...utils.url_manager import ModuleSupports
from ...utils.FilterHelpers.FilterHelper import FilterHelper
from ...utils.logger import error
from ...modules.Settings.SettinsUtils.SettingsLogic import SettingsLogic
from ..theme_manager import ThemeManager
from .select_all_checkbox import SelectAllCheckBox


class _TypePickerControl(QFrame):
    clicked = pyqtSignal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("TypePickerControl")
        self.setCursor(Qt.PointingHandCursor)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 4, 8, 4)
        layout.setSpacing(8)
        self._label = QLabel("", self)
        self._label.setObjectName("TypePickerSummary")
        self._label.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self._label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self._arrow = QLabel("v", self)
        self._arrow.setObjectName("TypePickerArrow")
        self._arrow.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        layout.addWidget(self._label, 1)
        layout.addWidget(self._arrow, 0, Qt.AlignVCenter)
        self._apply_style()

    def set_summary(self, text: str) -> None:
        self._label.setText(text)

    def mousePressEvent(self, event) -> None:  # noqa: N802
        if event.button() == Qt.LeftButton and self.isEnabled():
            self.clicked.emit()
            event.accept()
            return
        super().mousePressEvent(event)

    def keyPressEvent(self, event) -> None:  # noqa: N802
        if event.key() in (Qt.Key_Return, Qt.Key_Enter, Qt.Key_Space):
            self.clicked.emit()
            event.accept()
            return
        super().keyPressEvent(event)

    def _apply_style(self) -> None:
        dark = ThemeManager.effective_theme() == "dark"
        if dark:
            bg = "#303a42"
            hover = "#2e2f38"
            border = "#4d4d4d"
            accent = "#1f5d5c"
            text = "#c5c5d2"
        else:
            bg = "#ffffff"
            hover = "#f9fafb"
            border = "#d7dee5"
            accent = "#2188ff"
            text = "#24292e"
        self.setStyleSheet(
            "QFrame#TypePickerControl {"
            f"background: {bg}; border: 1px solid {border}; border-radius: 6px; min-height: 22px;"
            "}"
            "QFrame#TypePickerControl:hover, QFrame#TypePickerControl:focus {"
            f"background: {hover}; border-color: {accent};"
            "}"
            "QLabel#TypePickerSummary {"
            f"color: {text}; font-size: 12px; font-weight: 600;"
            "}"
            "QLabel#TypePickerArrow {"
            f"color: {accent}; font-size: 12px; font-weight: 700;"
            "}"
        )


class _TypePickerPopup(QWidget):
    def __init__(self, owner: "TypeFilterWidget", *, min_width: int, parent=None) -> None:
        super().__init__(parent, flags=Qt.Popup | Qt.FramelessWindowHint)
        self.setObjectName("TypePickerPopup")
        self.setAttribute(Qt.WA_DeleteOnClose, True)
        self._owner = owner
        self._min_width = max(420, min_width)
        self._root = QVBoxLayout(self)
        self._root.setContentsMargins(0, 0, 0, 0)
        self._root.setSpacing(0)
        self._frame = QFrame(self)
        self._frame.setObjectName("TypePickerPopupFrame")
        self._frame.setMinimumWidth(self._min_width)
        self._frame_layout = QVBoxLayout(self._frame)
        self._frame_layout.setContentsMargins(8, 8, 8, 8)
        self._frame_layout.setSpacing(8)
        self._root.addWidget(self._frame)
        self._apply_style()
        self.refresh()

    def refresh(self) -> None:
        self._clear_layout(self._frame_layout)
        actions = QHBoxLayout()
        actions.setSpacing(6)
        select_visible = QPushButton(self._owner._lang.translate(TranslationKeys.SELECT_ALL), self._frame)
        clear = QPushButton(self._owner._lang.translate(TranslationKeys.CLEAR_SELECTION), self._frame)
        for button in (select_visible, clear):
            button.setObjectName("TypePickerActionButton")
            actions.addWidget(button)
        actions.addStretch(1)
        select_visible.clicked.connect(self._owner._select_all_visible_types)
        clear.clicked.connect(self._owner._clear_all_types)
        self._frame_layout.addLayout(actions)

        body = QHBoxLayout()
        body.setSpacing(8)
        self._frame_layout.addLayout(body, 1)

        groups_panel = QFrame(self._frame)
        groups_panel.setObjectName("TypePickerPanel")
        groups_panel.setMinimumWidth(150)
        groups_layout = QVBoxLayout(groups_panel)
        groups_layout.setContentsMargins(6, 6, 6, 6)
        groups_layout.setSpacing(4)
        groups_title = QLabel(self._owner._lang.translate(TranslationKeys.TYPE_GROUP_FILTER), groups_panel)
        groups_title.setObjectName("TypePickerSectionLabel")
        groups_layout.addWidget(groups_title)
        self._add_group_row(groups_layout, None)
        for group_name in sorted(self._owner._group_map.keys(), key=str.lower):
            self._add_group_row(groups_layout, group_name)
        groups_layout.addStretch(1)
        body.addWidget(groups_panel, 0)

        type_panel = QFrame(self._frame)
        type_panel.setObjectName("TypePickerTypePanel")
        type_panel_layout = QVBoxLayout(type_panel)
        type_panel_layout.setContentsMargins(0, 0, 0, 0)
        type_panel_layout.setSpacing(0)

        type_scroll = QScrollArea(type_panel)
        type_scroll.setObjectName("TypePickerScroll")
        type_scroll.setMaximumHeight(320)
        type_scroll.setWidgetResizable(True)
        type_scroll.setFrameShape(QFrame.NoFrame)
        type_content = QWidget(type_scroll)
        type_content.setObjectName("TypePickerContent")
        type_layout = QVBoxLayout(type_content)
        type_layout.setContentsMargins(6, 6, 6, 6)
        type_layout.setSpacing(4)
        type_title = QLabel(self._owner._lang.translate(TranslationKeys.TYPE_FILTER), type_content)
        type_title.setObjectName("TypePickerSectionLabel")
        type_layout.addWidget(type_title)
        for item in self._owner._visible_type_items():
            self._add_type_row(type_layout, item)
        type_layout.addStretch(1)
        type_scroll.setWidget(type_content)
        type_panel_layout.addWidget(type_scroll, 0, Qt.AlignTop)
        type_panel_layout.addStretch(1)
        body.addWidget(type_panel, 1, Qt.AlignTop)

    def _add_group_row(self, layout: QVBoxLayout, group_name: str | None) -> None:
        label = self._owner._group_row_label(group_name)
        row = QPushButton(label, self._frame)
        row.setObjectName("TypePickerGroupRow")
        row.setCheckable(True)
        row.setChecked(self._owner._is_group_filter_active(group_name))
        row.clicked.connect(lambda _checked=False, name=group_name: self._on_group_clicked(name))
        layout.addWidget(row)

    def _add_type_row(self, layout: QVBoxLayout, item: dict[str, str]) -> None:
        type_id = str(item.get("id") or "")
        row = QPushButton(str(item.get("label") or "-"), self._frame)
        row.setObjectName("TypePickerTypeRow")
        row.setCheckable(True)
        row.setChecked(type_id in set(self._owner.selected_ids()))
        row.clicked.connect(lambda checked=False, tid=type_id: self._on_type_clicked(tid, checked))
        layout.addWidget(row)

    def _on_group_clicked(self, group_name: str | None) -> None:
        self._owner._toggle_group_filter(group_name)
        self.refresh()

    def _on_type_clicked(self, type_id: str, checked: bool) -> None:
        self._owner._set_type_checked(type_id, checked)
        self.refresh()

    def _clear_layout(self, layout) -> None:
        while layout.count():
            item = layout.takeAt(0)
            child_layout = item.layout()
            widget = item.widget()
            if child_layout is not None:
                self._clear_layout(child_layout)
            if widget is not None:
                widget.deleteLater()

    def _apply_style(self) -> None:
        dark = ThemeManager.effective_theme() == "dark"
        if dark:
            frame_bg = "#252932"
            panel_bg = "#2e2f38"
            border = "#1f5d5c"
            text = "#c5c5d2"
            muted = "#9aa4b2"
            hover = "#3a3f4b"
            selected = "rgba(9,144,143,0.28)"
            selected_border = "rgb(9,144,143)"
        else:
            frame_bg = "#ffffff"
            panel_bg = "#f9fafb"
            border = "#2188ff"
            text = "#24292e"
            muted = "#6a737d"
            hover = "#eaeef2"
            selected = "rgba(33,136,255,0.14)"
            selected_border = "#2188ff"
        self.setStyleSheet(
            "QFrame#TypePickerPopupFrame {"
            f"background: {frame_bg}; border: 1px solid {border}; border-radius: 8px;"
            "}"
            "QFrame#TypePickerPanel {"
            f"background: {panel_bg}; border: 1px solid rgba(128,128,128,0.20); border-radius: 6px;"
            "}"
            "QLabel#TypePickerSectionLabel {"
            f"color: {muted}; font-size: 10px; font-weight: 800; text-transform: uppercase;"
            "}"
            "QPushButton#TypePickerGroupRow, QPushButton#TypePickerTypeRow {"
            f"background: transparent; color: {text}; border: 1px solid transparent; border-radius: 6px;"
            "padding: 5px 8px; text-align: left; font-size: 12px; font-weight: 600;"
            "}"
            "QPushButton#TypePickerGroupRow:hover, QPushButton#TypePickerTypeRow:hover {"
            f"background: {hover};"
            "}"
            "QPushButton#TypePickerGroupRow:checked, QPushButton#TypePickerTypeRow:checked {"
            f"background: {selected}; border-color: {selected_border};"
            "}"
            "QPushButton#TypePickerActionButton {"
            f"background: {panel_bg}; color: {text}; border: 1px solid rgba(128,128,128,0.30); border-radius: 5px;"
            "padding: 4px 8px; font-size: 11px; font-weight: 700;"
            "}"
            "QPushButton#TypePickerActionButton:hover {"
            f"border-color: {border};"
            "}"
            "QScrollArea#TypePickerScroll { background: transparent; border: none; }"
            "QFrame#TypePickerTypePanel { background: transparent; border: none; }"
            "QWidget#TypePickerContent { background: transparent; }"
        )


class TypeFilterWidget(QWidget):
    """Simple group/type multi-select without shared base class."""

    selectionChanged = pyqtSignal(list, list)
    loadFinished = pyqtSignal(bool)

    def __init__(
        self,
        module_name: str,
        parent: Optional[QWidget] = None,
        *,
        auto_load: bool = True,
        settings_logic: Optional[SettingsLogic] = None,
    ) -> None:
        super().__init__(parent)
        self._module = module_name
        self._lang = LanguageManager()
        self._group_map: Dict[str, List[str]] = {}
        self._all_types_payload: List[Dict[str, str]] = []
        self._suppress_group_emit = False
        self._suppress_type_emit = False
        self._loaded = False
        self._worker = None
        self._worker_thread = None
        self._pending_type_ids: List[str] = []
        self._selected_type_ids: set[str] = set()
        self._auto_load = auto_load
        self._settings_logic = settings_logic or SettingsLogic()
        self._load_request_id = 0
        self._suppress_all_cb = False
        self._active_group_filter: str | None = None
        self._show_all_groups = False
        self._popup: Optional[_TypePickerPopup] = None

        layout = QHBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(2)

        self._control = _TypePickerControl(self)
        self._control.clicked.connect(self._open_type_picker)
        self._control.setEnabled(False)
        layout.addWidget(self._control, 1)

        self.group_combo = QgsCheckableComboBox(self)
        self.group_combo.setObjectName("GroupFilterCombo")
        layout.addWidget(self.group_combo)
        self.group_combo.setVisible(False)

        self.type_combo = QgsCheckableComboBox(self)
        self.type_combo.setObjectName("TypeFilterCombo")
        layout.addWidget(self.type_combo)
        self.type_combo.setVisible(False)

        ThemeManager.apply_checkable_combo_popup_style(self.group_combo)
        ThemeManager.apply_checkable_combo_popup_style(self.type_combo)

        self.all_cb = SelectAllCheckBox(self)
        self.all_cb.setTristate(True)
        self.all_cb.setObjectName("SelectAllCheckbox")
        self.all_cb.setProperty("kavitroSelectAll", True)
        self.all_cb.setToolTip(self._lang.translate(TranslationKeys.SELECT_ALL))
        self.all_cb.setProperty("variant", "type-filter")
        self.all_cb.setEnabled(False)
        self.all_cb.stateChanged.connect(self._on_all_cb_state_changed)
        layout.addWidget(self.all_cb)
        self.all_cb.setVisible(False)

        group_label = self._lang.translate(TranslationKeys.TYPE_GROUP_FILTER)
        type_label = self._lang.translate(TranslationKeys.TYPE_FILTER)
        self.group_combo.setToolTip(group_label)
        self.type_combo.setToolTip(type_label)
        try:
            if hasattr(self.group_combo, "setDefaultText"):
                self.group_combo.setDefaultText(group_label)
            if hasattr(self.type_combo, "setDefaultText"):
                self.type_combo.setDefaultText(type_label)
        except Exception:
            pass

        self.group_combo.checkedItemsChanged.connect(self._on_group_selection_changed)  # type: ignore[attr-defined]
        self.type_combo.checkedItemsChanged.connect(self._on_type_selection_changed)  # type: ignore[attr-defined]

        if self._auto_load:
            QTimer.singleShot(0, self.reload)
        self._update_control_summary()

    def retheme(self) -> None:
        ThemeManager.apply_checkable_combo_popup_style(self.group_combo)
        ThemeManager.apply_checkable_combo_popup_style(self.type_combo)
        self._control._apply_style()
        self.style().unpolish(self)
        self.style().polish(self)
        self.all_cb.style().unpolish(self.all_cb)
        self.all_cb.style().polish(self.all_cb)

    # ------------------------------------------------------------------
    def reload(self) -> None:
        self._loaded = False
        self._load_request_id += 1
        self._all_types_payload = []
        self._selected_type_ids.clear()
        self._active_group_filter = None
        self._show_all_groups = False
        self.group_combo.clear()
        self.type_combo.clear()
        self._set_all_cb_state(Qt.Unchecked, enabled=False)
        self.group_combo.setEnabled(False)
        self.type_combo.setEnabled(False)
        self._control.setEnabled(False)
        self._update_control_summary()
        self._show_loading_placeholder()
        self._start_async_load()

    def ensure_loaded(self) -> None:
        if not self._loaded:
            self.reload()

    def selected_ids(self) -> List[str]:
        return sorted(v for v in self._selected_type_ids if v)

    def selected_texts(self) -> List[str]:
        label_by_id = {str(item.get("id") or ""): str(item.get("label") or "") for item in self._all_types_payload}
        return [label_by_id.get(type_id, type_id) for type_id in self.selected_ids() if type_id]

    def set_selected_ids(self, ids: Sequence[str], emit: bool = True) -> None:
        targets = {str(v) for v in ids or []}
        if not self._loaded:
            self._pending_type_ids = list(targets)
            return
        self._apply_type_selection(targets, emit, source="set_selected_ids")

    def _on_group_selection_changed(self) -> None:
        if self._suppress_group_emit:
            return
        if not self.group_combo.isVisible():
            return
        selected_groups = {
            g
            for g in (self.group_combo.checkedItemsData() or [])  # type: ignore[attr-defined]
            if g
        }
        current_selected_ids = set(self.selected_ids())
        self._rebuild_type_combo(selected_groups if selected_groups else None, preserve_selected_ids=current_selected_ids)
        self._sync_all_checkbox_state()
        self._update_control_summary()
        self._refresh_popup()

    def _on_type_selection_changed(self) -> None:
        if self._suppress_type_emit:
            return
        visible_ids = {str(self.type_combo.itemData(row) or "") for row in range(self.type_combo.count())}
        checked_visible_ids = {
            str(self.type_combo.itemData(row) or "")
            for row in range(self.type_combo.count())
            if self.type_combo.itemCheckState(row) == Qt.Checked
        }
        self._selected_type_ids.difference_update(v for v in visible_ids if v)
        self._selected_type_ids.update(v for v in checked_visible_ids if v)
        self._sync_groups_to_types()
        self._sync_all_checkbox_state()
        self._update_control_summary()
        self._refresh_popup()
        self._emit_selection_change(source="type_combo")

    def _apply_type_selection(self, target_ids: Sequence[str], emit: bool, source: str = "programmatic") -> None:
        targets = {str(v) for v in target_ids or []}
        self._selected_type_ids = set(targets)
        if targets:
            self._show_all_groups = False
        self._rebuild_type_combo(self._visible_groups(), preserve_selected_ids=self._selected_type_ids)
        self._suppress_type_emit = True
        try:
            for row in range(self.type_combo.count()):
                val = self.type_combo.itemData(row)
                state = Qt.Checked if str(val) in targets else Qt.Unchecked
                self.type_combo.setItemCheckState(row, state)
        finally:
            self._suppress_type_emit = False

        self._sync_groups_to_types()
        self._sync_all_checkbox_state()
        self._update_control_summary()
        self._refresh_popup()
        if emit:
            self._emit_selection_change(source=source)

    def _apply_preferred_types(self) -> None:
        if not self._loaded:
            return
        ids = self._settings_logic.load_module_preference_ids(
            self._module,
            support_key=ModuleSupports.TYPES.value,
        )
        if ids:
            self.set_selected_ids(list(ids), emit=False)

    def _sync_groups_to_types(self) -> None:
        selected_type_ids = set(self.selected_ids())
        self._suppress_group_emit = True
        try:
            for row in range(self.group_combo.count()):
                group_name = self.group_combo.itemData(row)
                if not group_name:
                    continue
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

    def _emit_selection_change(self, source: str = "unknown") -> None:
        texts = self.selected_texts()
        ids = self.selected_ids()
        self.selectionChanged.emit(texts, ids)

    def _open_type_picker(self) -> None:
        if not self._loaded or not self._control.isEnabled():
            return
        if self._popup is not None:
            try:
                self._popup.close()
            except Exception:
                pass
            self._popup = None
            return
        popup = _TypePickerPopup(self, min_width=max(self.width(), self._control.width()), parent=self)
        self._popup = popup
        popup.destroyed.connect(lambda *_: setattr(self, "_popup", None))
        popup.move(self._control.mapToGlobal(self._control.rect().bottomLeft()))
        popup.show()

    def _refresh_popup(self) -> None:
        popup = self._popup
        if popup is not None:
            try:
                popup.refresh()
            except RuntimeError:
                self._popup = None

    def _visible_groups(self) -> Optional[set[str]]:
        if self._active_group_filter:
            return {self._active_group_filter}
        if self._show_all_groups:
            return None
        selected_groups = self._selected_groups()
        return selected_groups if selected_groups else None

    def _selected_groups(self) -> set[str]:
        selected_ids = set(self.selected_ids())
        groups: set[str] = set()
        for group_name, type_ids in self._group_map.items():
            if any(str(type_id) in selected_ids for type_id in type_ids):
                groups.add(group_name)
        return groups

    def _visible_type_items(self) -> List[Dict[str, str]]:
        visible_groups = self._visible_groups()
        items: List[Dict[str, str]] = []
        for item in self._all_types_payload:
            group = str(item.get("group") or "")
            if visible_groups and group not in visible_groups:
                continue
            items.append(item)
        return items

    def _is_group_filter_active(self, group_name: str | None) -> bool:
        if group_name is None:
            return self._show_all_groups or not self._visible_groups()
        return group_name == self._active_group_filter

    def _toggle_group_filter(self, group_name: str | None) -> None:
        selected_ids = set(self.selected_ids())
        if group_name is None:
            self._active_group_filter = None
            self._show_all_groups = True
        elif group_name == self._active_group_filter:
            self._active_group_filter = None
            self._show_all_groups = False
        else:
            self._active_group_filter = group_name
            self._show_all_groups = False
        self._rebuild_type_combo(self._visible_groups(), preserve_selected_ids=selected_ids)
        self._sync_groups_to_types()
        self._sync_all_checkbox_state()
        self._update_control_summary()
        self._refresh_popup()

    def _set_type_checked(self, type_id: str, checked: bool) -> None:
        if not type_id:
            return
        current = set(self.selected_ids())
        if checked:
            current.add(str(type_id))
        else:
            current.discard(str(type_id))
        self._apply_type_selection(current, emit=True, source="type_picker")

    def _select_all_visible_types(self) -> None:
        current = set(self.selected_ids())
        for item in self._visible_type_items():
            item_id = str(item.get("id") or "")
            if item_id:
                current.add(item_id)
        self._show_all_groups = False
        self._apply_type_selection(current, emit=True, source="type_picker_select_visible")

    def _clear_all_types(self) -> None:
        self._active_group_filter = None
        self._show_all_groups = True
        self._apply_type_selection([], emit=True, source="type_picker_clear")

    def _group_row_label(self, group_name: str | None) -> str:
        if group_name is None:
            total = len(self._all_types_payload)
            checked = len(self.selected_ids())
            return f"{self._lang.translate(TranslationKeys.TYPE_FILTER_ALL_GROUPS)} ({checked}/{total})"
        type_ids = self._group_map.get(group_name, [])
        selected = set(self.selected_ids())
        checked = sum(1 for type_id in type_ids if type_id in selected)
        marker = "[x]" if checked == len(type_ids) and type_ids else "[~]" if checked else "[ ]"
        return f"{marker} {group_name} ({checked}/{len(type_ids)})"

    def _update_control_summary(self) -> None:
        if not hasattr(self, "_control"):
            return
        if not self._loaded:
            self._control.set_summary(self._lang.translate(TranslationKeys.LOADING))
            return
        active_group = self._active_group_filter or ""
        selected = self.selected_texts()
        if not selected:
            base = self._lang.translate(TranslationKeys.TYPE_FILTER)
            self._control.set_summary(f"{base}: {active_group}" if active_group else base)
            return
        if len(selected) <= 2:
            text = ", ".join(selected)
            self._control.set_summary(f"{active_group}: {text}" if active_group else text)
            return
        count_text = f"{len(selected)} {self._lang.translate(TranslationKeys.TYPE_FILTER).lower()}"
        self._control.set_summary(f"{active_group}: {count_text}" if active_group else count_text)

    # Async helpers --------------------------------------------------
    def _show_loading_placeholder(self) -> None:
        loading_text = self._lang.translate(TranslationKeys.LOADING) if self._lang else "Loading"
        placeholder = f"{loading_text}..."
        self.group_combo.addItem(placeholder)
        self.type_combo.addItem(placeholder)

    def _normalize_group_name(self, label: Optional[str], backend_group: Optional[str]) -> Optional[str]:
        safe_label = (label or "").strip()

        # Global rule for all type-enabled modules:
        # - labels containing " - " are treated as subtypes (group by prefix)
        # - plain labels remain standalone groups
        if " - " in safe_label:
            return safe_label.split(" - ", 1)[0].strip() or safe_label

        if safe_label:
            return safe_label

        safe_backend_group = (backend_group or "").strip()
        return safe_backend_group or None

    def _start_async_load(self) -> None:
        FilterHelper.cancel_pending_load(self, invalidate_request=False)
        token = self._current_token()
        request_id = self._load_request_id

        key = ModuleSupports.TYPES.value
        worker = FunctionWorker(lambda: FilterHelper.get_filter_edges_by_key_and_module(key, self._module))
        worker.active_token = token
        worker.finished.connect(
            lambda payload, tok=token, req=request_id: self._handle_types_loaded(payload, tok, req)
        )
        worker.error.connect(
            lambda message, tok=token, req=request_id: self._handle_types_failed(message, tok, req)
        )
        self._worker = worker
        self._worker_thread = start_worker(worker, on_thread_finished=self._cleanup_worker)

    def _handle_types_loaded(
        self,
        payload: List[Dict[str, Optional[str]]],
        token: int | None,
        request_id: int,
    ) -> None:
        if not self._is_widget_alive():
            return
        if request_id != self._load_request_id:
            return
        if not self._is_token_active(token):
            return
        self.type_combo.clear()
        self.group_combo.clear()
        self._group_map.clear()
        self._all_types_payload = []
        self._selected_type_ids.clear()
        self._active_group_filter = None
        self._show_all_groups = False

        for entry in payload:
            type_id = entry.get("id")
            label = entry.get("label")
            group_name = self._normalize_group_name(label, entry.get("group"))
            if type_id and label:
                self._all_types_payload.append({"id": str(type_id), "label": str(label), "group": str(group_name or "")})
                if group_name:
                    self._group_map.setdefault(group_name, []).append(type_id)

        self._rebuild_type_combo(None)

        for group_name in sorted(self._group_map.keys(), key=str.lower):
            self.group_combo.addItem(group_name, group_name)

        ThemeManager.apply_checkable_combo_popup_style(self.group_combo)
        ThemeManager.apply_checkable_combo_popup_style(self.type_combo)

        self.group_combo.setEnabled(True)
        self.type_combo.setEnabled(True)
        self._control.setEnabled(True)
        self._loaded = True
        self.all_cb.setEnabled(True)
        self._apply_preferred_types()
        if self._pending_type_ids:
            pending_ids = list(self._pending_type_ids)
            self.set_selected_ids(pending_ids, emit=False)
            self._pending_type_ids = []
        self._sync_all_checkbox_state()
        self._update_control_summary()
        self._refresh_popup()
        self.loadFinished.emit(True)

    def _handle_types_failed(self, message: str, token: int | None, request_id: int) -> None:
        if not self._is_widget_alive():
            return
        if request_id != self._load_request_id:
            return
        if not self._is_token_active(token):
            return
        self.group_combo.clear()
        self.type_combo.clear()
        self.group_combo.addItem(f"Error: {message[:40]}...")
        self.group_combo.setEnabled(False)
        self.type_combo.setEnabled(False)
        self._control.setEnabled(False)
        self._set_all_cb_state(Qt.Unchecked, enabled=False)
        self._update_control_summary()
        self._refresh_popup()
        self._loaded = False
        self.loadFinished.emit(False)

    def _cleanup_worker(self) -> None:
        if not self._is_widget_alive():
            return
        self._worker = None
        self._worker_thread = None

    # ------------------------------------------------------------------
    # Queue/cleanup helpers
    # ------------------------------------------------------------------
    def is_loaded(self) -> bool:
        return self._loaded

    def is_loading(self) -> bool:
        return self._worker_thread is not None

    def clear_data(self) -> None:
        """Clear combo data to free memory; safe to call on deactivate."""
        try:
            FilterHelper.cancel_pending_load(self, invalidate_request=True)
            self.group_combo.clear()
            self.type_combo.clear()
            self.group_combo.setEnabled(False)
            self.type_combo.setEnabled(False)
            self._control.setEnabled(False)
            self._set_all_cb_state(Qt.Unchecked, enabled=False)
            self._group_map.clear()
            self._all_types_payload = []
            self._selected_type_ids.clear()
            self._active_group_filter = None
            self._show_all_groups = False
            self._loaded = False
            self._pending_type_ids = []
            self._update_control_summary()
            self._refresh_popup()
        except Exception as exc:
            error(f"[TypeFilterWidget] clear_data failed: {exc}")

    def _rebuild_type_combo(
        self,
        visible_groups: Optional[set],
        preserve_selected_ids: Optional[set] = None,
    ) -> None:
        source_ids = preserve_selected_ids if preserve_selected_ids is not None else self._selected_type_ids
        selected_ids = {str(v) for v in (source_ids or set()) if v}
        self._suppress_type_emit = True
        try:
            self.type_combo.clear()
            for item in self._all_types_payload:
                item_group = str(item.get("group") or "")
                if visible_groups and item_group not in visible_groups:
                    continue
                item_id = str(item.get("id") or "")
                item_label = str(item.get("label") or "")
                if not item_id or not item_label:
                    continue
                self.type_combo.addItem(item_label, item_id)

            for row in range(self.type_combo.count()):
                value = str(self.type_combo.itemData(row) or "")
                self.type_combo.setItemCheckState(
                    row,
                    Qt.Checked if value in selected_ids else Qt.Unchecked,
                )
        finally:
            self._suppress_type_emit = False
    def _apply_select_all(self, checked: bool) -> None:
        if checked and hasattr(self.type_combo, "selectAllOptions"):
            self.type_combo.selectAllOptions()
            return
        if not checked and hasattr(self.type_combo, "deselectAllOptions"):
            self.type_combo.deselectAllOptions()
            return

        target_state = Qt.Checked if checked else Qt.Unchecked
        for i in range(self.type_combo.count()):
            if self.type_combo.itemData(i) is None:
                continue
            self.type_combo.setItemCheckState(i, target_state)

    def _on_all_cb_state_changed(self, state: int) -> None:
        if self._suppress_all_cb:
            return
        self._suppress_type_emit = True
        try:
            self._apply_select_all(state == Qt.Checked)
        finally:
            self._suppress_type_emit = False
        visible_ids = {str(self.type_combo.itemData(row) or "") for row in range(self.type_combo.count())}
        if state == Qt.Checked:
            self._selected_type_ids.update(v for v in visible_ids if v)
        else:
            self._selected_type_ids.difference_update(v for v in visible_ids if v)
        self._sync_groups_to_types()
        self._sync_all_checkbox_state()
        self._update_control_summary()
        self._refresh_popup()
        self._emit_selection_change(source="select_all_checkbox")

    def _sync_all_checkbox_state(self) -> None:
        total = 0
        checked = 0
        for i in range(self.type_combo.count()):
            val = self.type_combo.itemData(i)
            if val is None:
                continue
            total += 1
            if self.type_combo.itemCheckState(i) == Qt.Checked:
                checked += 1
        if total == 0 or checked == 0:
            state = Qt.Unchecked
        elif checked == total:
            state = Qt.Checked
        else:
            state = Qt.PartiallyChecked
        self._set_all_cb_state(state)

    def _set_all_cb_state(self, state: Qt.CheckState, *, enabled: bool | None = None) -> None:
        self._suppress_all_cb = True
        try:
            self.all_cb.setCheckState(state)
            if enabled is not None:
                self.all_cb.setEnabled(enabled)
        finally:
            self._suppress_all_cb = False

    def _current_token(self) -> int | None:
        if not self._is_widget_alive():
            return None
        try:
            parent = self.parent()
        except RuntimeError:
            return None
        while parent is not None:
            if hasattr(parent, "_active_token"):
                return getattr(parent, "_active_token", None)
            parent = parent.parent()
        return None

    def _is_token_active(self, token: int | None) -> bool:
        if not self._is_widget_alive():
            return False
        if token is None:
            return True
        try:
            parent = self.parent()
        except RuntimeError:
            return False
        while parent is not None:
            if hasattr(parent, "is_token_active"):
                try:
                    return bool(parent.is_token_active(token))
                except Exception:
                    return False
            if hasattr(parent, "_active_token"):
                return bool(getattr(parent, "_activated", False)) and token == getattr(parent, "_active_token", None)
            parent = parent.parent()
        return True

    def _is_widget_alive(self) -> bool:
        try:
            import sip
        except Exception:
            sip = None
        try:
            return not bool(sip and sip.isdeleted(self))
        except RuntimeError:
            return False

