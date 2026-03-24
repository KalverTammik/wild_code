from __future__ import annotations

from typing import Dict, List, Optional

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)
from qgis.core import Qgis, QgsMapLayer, QgsProject
from qgis.gui import QgsFieldComboBox, QgsMapLayerComboBox

from .SettingsBaseCard import SettingsBaseCard
from ..settings_layer_helper import SettingsLayerHelper
from ....languages.translation_keys import TranslationKeys
from ....utils.project_base_layers import ProjectBaseLayerKeys, ProjectBaseLayersService


class SettingsProjectBaseLayersCard(SettingsBaseCard):
    pendingChanged = pyqtSignal(bool)
    LABEL_WIDTH = 220
    INDENT_WIDTH = 228
    SHARED_SECTION_OFFSET = 24
    TYPE_FIELD_MAX_WIDTH = 360
    MAPPING_KIND_MAX_WIDTH = 420
    MAPPING_IDS_MAX_WIDTH = 140

    LAYER_KEY_TO_TRANSLATION = {
        ProjectBaseLayerKeys.WATERPIPES: TranslationKeys.SETTINGS_BASE_LAYER_WATERPIPES,
        ProjectBaseLayerKeys.SEWERPIPES: TranslationKeys.SETTINGS_BASE_LAYER_SEWERPIPES,
        ProjectBaseLayerKeys.PRESSURE_SEWERPIPES: TranslationKeys.SETTINGS_BASE_LAYER_PRESSURE_SEWERPIPES,
        ProjectBaseLayerKeys.RAINWATERPIPES: TranslationKeys.SETTINGS_BASE_LAYER_RAINWATERPIPES,
    }

    MAPPING_KIND_TO_TRANSLATION = {
        ProjectBaseLayerKeys.SEWER_KIND_SEWER: TranslationKeys.SETTINGS_SHARED_SEWER_KIND_SEWER,
        ProjectBaseLayerKeys.SEWER_KIND_SEWER_PRESSURE: TranslationKeys.SETTINGS_SHARED_SEWER_KIND_SEWER_PRESSURE,
        ProjectBaseLayerKeys.SEWER_KIND_COMBINED: TranslationKeys.SETTINGS_SHARED_SEWER_KIND_COMBINED,
        ProjectBaseLayerKeys.SEWER_KIND_COMBINED_PRESSURE: TranslationKeys.SETTINGS_SHARED_SEWER_KIND_COMBINED_PRESSURE,
        ProjectBaseLayerKeys.SEWER_KIND_RAINWATER: TranslationKeys.SETTINGS_SHARED_SEWER_KIND_RAINWATER,
        ProjectBaseLayerKeys.SEWER_KIND_RAINWATER_PRESSURE: TranslationKeys.SETTINGS_SHARED_SEWER_KIND_RAINWATER_PRESSURE,
        ProjectBaseLayerKeys.SEWER_KIND_DRAINAGE: TranslationKeys.SETTINGS_SHARED_SEWER_KIND_DRAINAGE,
        ProjectBaseLayerKeys.SEWER_KIND_OTHER: TranslationKeys.SETTINGS_SHARED_SEWER_KIND_OTHER,
    }

    def __init__(self, lang_manager):
        super().__init__(
            lang_manager,
            lang_manager.translate(TranslationKeys.SETTINGS_PROJECT_BASE_LAYERS_TITLE),
            None,
        )
        self._service = ProjectBaseLayersService()
        self._layer_combos: Dict[str, QgsMapLayerComboBox] = {}
        self._layer_row_widgets: Dict[str, QWidget] = {}
        self._project_bound = False
        self._layer_signals_connected = False

        self._orig_enabled = False
        self._pend_enabled = False
        self._orig_layers = {key: "" for key in ProjectBaseLayerKeys.ORDER}
        self._pend_layers = dict(self._orig_layers)
        self._orig_sewer_mapping_enabled = False
        self._pend_sewer_mapping_enabled = False
        self._orig_sewer_mapping_field = ""
        self._pend_sewer_mapping_field = ""
        self._orig_sewer_mapping_rows: List[dict[str, str]] = []
        self._pend_sewer_mapping_rows: List[dict[str, str]] = []
        self._mapping_row_items: List[dict[str, object]] = []

        self._build_ui()

    def _build_ui(self) -> None:
        content = self.content_widget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(1, 1, 1, 1)
        layout.setSpacing(8)

        description = QLabel(self.lang_manager.translate(TranslationKeys.SETTINGS_PROJECT_BASE_LAYERS_DESCRIPTION), content)
        description.setWordWrap(True)
        description.setObjectName("SetupCardDescription")
        layout.addWidget(description)

        toggle_row = QHBoxLayout()
        toggle_row.setContentsMargins(0, 0, 0, 0)
        toggle_row.setSpacing(8)
        self._enabled_checkbox = QCheckBox(
            self.lang_manager.translate(TranslationKeys.SETTINGS_EVEL_LAYER_SETUP_ENABLED),
            content,
        )
        self._enabled_checkbox.stateChanged.connect(self._on_enabled_changed)
        toggle_row.addWidget(self._enabled_checkbox)
        toggle_row.addStretch(1)
        layout.addLayout(toggle_row)

        layers_frame = QFrame(content)
        layers_layout = QVBoxLayout(layers_frame)
        layers_layout.setContentsMargins(0, 0, 0, 0)
        layers_layout.setSpacing(6)
        self._layers_layout = layers_layout

        for key in ProjectBaseLayerKeys.ORDER:
            row_widget = QWidget(layers_frame)
            row = QHBoxLayout(row_widget)
            row.setContentsMargins(0, 0, 0, 0)
            row.setSpacing(8)

            label = QLabel(self.lang_manager.translate(self.LAYER_KEY_TO_TRANSLATION[key]), row_widget)
            label.setMinimumWidth(self.LABEL_WIDTH)
            row.addWidget(label)

            combo = self._create_layer_combobox(row_widget)
            combo.layerChanged.connect(lambda layer, layer_key=key: self._on_layer_changed(layer_key, layer))
            row.addWidget(combo, 1)
            self._layer_combos[key] = combo
            self._layer_row_widgets[key] = row_widget

            if key == ProjectBaseLayerKeys.SEWERPIPES:
                self._shared_sewer_checkbox = QCheckBox(
                    self.lang_manager.translate(TranslationKeys.SETTINGS_SHARED_SEWER_MAPPING),
                    row_widget,
                )
                self._shared_sewer_checkbox.stateChanged.connect(self._on_shared_sewer_mapping_changed)
                row.addWidget(self._shared_sewer_checkbox)

            layers_layout.addWidget(row_widget)

        self._shared_sewer_field_row = QWidget(layers_frame)
        field_row = QHBoxLayout(self._shared_sewer_field_row)
        field_row.setContentsMargins(self.SHARED_SECTION_OFFSET, 0, 0, 0)
        field_row.setSpacing(8)

        field_label = QLabel(self.lang_manager.translate(TranslationKeys.SETTINGS_SHARED_SEWER_FIELD), self._shared_sewer_field_row)
        field_label.setMinimumWidth(self.LABEL_WIDTH)
        field_row.addWidget(field_label)

        self._shared_sewer_field_combo = QgsFieldComboBox(self._shared_sewer_field_row)
        self._shared_sewer_field_combo.setMaximumWidth(self.TYPE_FIELD_MAX_WIDTH)
        self._shared_sewer_field_combo.fieldChanged.connect(self._on_shared_sewer_field_changed)
        field_row.addWidget(self._shared_sewer_field_combo)

        self._add_mapping_button = QPushButton(
            self.lang_manager.translate(TranslationKeys.SETTINGS_SHARED_SEWER_ADD_ROW),
            self._shared_sewer_field_row,
        )
        self._add_mapping_button.clicked.connect(self._on_add_mapping_row)
        field_row.addWidget(self._add_mapping_button)

        field_row.addStretch(1)

        layers_layout.addWidget(self._shared_sewer_field_row)

        self._mapping_rows_host = QWidget(layers_frame)
        self._mapping_rows_layout = QVBoxLayout(self._mapping_rows_host)
        self._mapping_rows_layout.setContentsMargins(0, 0, 0, 0)
        self._mapping_rows_layout.setSpacing(6)
        layers_layout.addWidget(self._mapping_rows_host)

        layout.addWidget(layers_frame)
        layout.addStretch(1)

        reset_btn = self.reset_button()
        reset_btn.setToolTip(self.lang_manager.translate(TranslationKeys.RESET_ALL_SETTINGS))
        reset_btn.setVisible(True)
        reset_btn.clicked.connect(self._on_reset_settings)

    def _create_layer_combobox(self, parent: QWidget) -> QgsMapLayerComboBox:
        combo = QgsMapLayerComboBox(parent)
        combo.setObjectName("ModuleLayerCombo")
        combo.setAllowEmptyLayer(True, self.lang_manager.translate(TranslationKeys.SELECT_LAYER))
        combo.setShowCrs(False)
        combo.setFilters(Qgis.LayerFilter.HasGeometry)
        return combo

    def on_settings_activate(self) -> None:
        project = QgsProject.instance() if QgsProject else None
        if project is not None and not self._project_bound:
            for combo in self._layer_combos.values():
                SettingsLayerHelper.set_combo_project(combo, project)
            self._project_bound = True

        if not self._layer_signals_connected:
            self._layer_signals_connected = SettingsLayerHelper.connect_project_layer_signals(
                project=project,
                handler=self._on_project_layers_changed,
            )

        state = self._service.get_state()
        self._orig_enabled = bool(state.get("evel_enabled"))
        self._pend_enabled = self._orig_enabled
        self._orig_layers = {key: str((state.get("layers") or {}).get(key) or "") for key in ProjectBaseLayerKeys.ORDER}
        self._pend_layers = dict(self._orig_layers)
        sewer_mapping = state.get("sewer_mapping") if isinstance(state.get("sewer_mapping"), dict) else {}
        self._orig_sewer_mapping_enabled = bool((sewer_mapping or {}).get("enabled"))
        self._pend_sewer_mapping_enabled = self._orig_sewer_mapping_enabled
        self._orig_sewer_mapping_field = str((sewer_mapping or {}).get("field") or "")
        self._pend_sewer_mapping_field = self._orig_sewer_mapping_field
        rows_state = (sewer_mapping or {}).get("rows") if isinstance((sewer_mapping or {}).get("rows"), list) else []
        self._orig_sewer_mapping_rows = ProjectBaseLayersService.normalize_mapping_rows(rows_state)
        self._pend_sewer_mapping_rows = [dict(row) for row in self._orig_sewer_mapping_rows]
        self._restore_state_to_ui()
        self._update_status()
        self.pendingChanged.emit(False)

    def on_settings_deactivate(self) -> None:
        if self._layer_signals_connected:
            project = QgsProject.instance() if QgsProject else None
            SettingsLayerHelper.disconnect_project_layer_signals(project=project, handler=self._on_project_layers_changed)
            self._layer_signals_connected = False

    def has_pending_changes(self) -> bool:
        return (
            self._pend_enabled != self._orig_enabled
            or self._pend_layers != self._orig_layers
            or self._pend_sewer_mapping_enabled != self._orig_sewer_mapping_enabled
            or self._pend_sewer_mapping_field != self._orig_sewer_mapping_field
            or self._pend_sewer_mapping_rows != self._orig_sewer_mapping_rows
        )

    def apply(self) -> None:
        self._service.save_state(
            evel_enabled=self._pend_enabled,
            layers=self._pend_layers,
            sewer_mapping={
                "enabled": self._pend_sewer_mapping_enabled,
                "field": self._pend_sewer_mapping_field,
                "rows": self._pend_sewer_mapping_rows,
            },
        )
        self._orig_enabled = self._pend_enabled
        self._orig_layers = dict(self._pend_layers)
        self._orig_sewer_mapping_enabled = self._pend_sewer_mapping_enabled
        self._orig_sewer_mapping_field = self._pend_sewer_mapping_field
        self._orig_sewer_mapping_rows = [dict(row) for row in self._pend_sewer_mapping_rows]
        self._restore_state_to_ui()
        self._update_status()
        self.pendingChanged.emit(False)

    def revert(self) -> None:
        self._pend_enabled = self._orig_enabled
        self._pend_layers = dict(self._orig_layers)
        self._pend_sewer_mapping_enabled = self._orig_sewer_mapping_enabled
        self._pend_sewer_mapping_field = self._orig_sewer_mapping_field
        self._pend_sewer_mapping_rows = [dict(row) for row in self._orig_sewer_mapping_rows]
        self._restore_state_to_ui()
        self._update_status()
        self.pendingChanged.emit(False)

    def _restore_state_to_ui(self) -> None:
        self._enabled_checkbox.blockSignals(True)
        self._enabled_checkbox.setChecked(self._pend_enabled)
        self._enabled_checkbox.blockSignals(False)

        self._shared_sewer_checkbox.blockSignals(True)
        self._shared_sewer_checkbox.setChecked(self._pend_sewer_mapping_enabled)
        self._shared_sewer_checkbox.blockSignals(False)

        for key, combo in self._layer_combos.items():
            layer = ProjectBaseLayersService.resolve_layer(
                key,
                state={"evel_enabled": self._pend_enabled, "layers": self._pend_layers},
            )
            combo.blockSignals(True)
            combo.setLayer(layer)
            combo.blockSignals(False)

        self._sync_shared_sewer_field_combo()

        self._rebuild_mapping_rows_ui()

        self._update_controls_enabled()

    def _update_controls_enabled(self) -> None:
        manual_layers_enabled = not bool(self._pend_enabled)
        for key, combo in self._layer_combos.items():
            enabled = manual_layers_enabled
            combo.setEnabled(enabled)

        self._layer_row_widgets[ProjectBaseLayerKeys.PRESSURE_SEWERPIPES].setVisible(
            not self._pend_sewer_mapping_enabled
        )
        self._layer_row_widgets[ProjectBaseLayerKeys.RAINWATERPIPES].setVisible(
            not self._pend_sewer_mapping_enabled
        )

        sewer_layer = self._current_or_resolved_layer(ProjectBaseLayerKeys.SEWERPIPES)
        has_sewer_layer = sewer_layer is not None
        mapping_controls_enabled = self._pend_sewer_mapping_enabled and has_sewer_layer
        available_kind_count = len(
            {
                str(row.get("kind") or "").strip()
                for row in self._pend_sewer_mapping_rows
                if str(row.get("kind") or "").strip()
            }
        ) < len(ProjectBaseLayerKeys.SEWER_MAPPING_KIND_ORDER)

        self._shared_sewer_checkbox.setEnabled(has_sewer_layer)
        self._add_mapping_button.setVisible(self._pend_sewer_mapping_enabled)
        self._add_mapping_button.setEnabled(mapping_controls_enabled and available_kind_count)
        self._shared_sewer_field_row.setVisible(self._pend_sewer_mapping_enabled)
        self._shared_sewer_field_combo.setEnabled(mapping_controls_enabled)
        self._mapping_rows_host.setVisible(self._pend_sewer_mapping_enabled and bool(self._mapping_row_items))

        for row_item in self._mapping_row_items:
            combo = row_item["combo"]
            ids_input = row_item["ids_input"]
            combo.setEnabled(mapping_controls_enabled)
            self._update_mapping_row_input_state(row_item, enable_input=mapping_controls_enabled)

    def _sync_shared_sewer_field_combo(self) -> None:
        sewer_layer = self._current_or_resolved_layer(ProjectBaseLayerKeys.SEWERPIPES)
        self._shared_sewer_field_combo.blockSignals(True)
        self._shared_sewer_field_combo.setLayer(sewer_layer)
        self._shared_sewer_field_combo.setField(self._pend_sewer_mapping_field)
        self._shared_sewer_field_combo.blockSignals(False)

    def _current_or_resolved_layer(self, key: str) -> QgsMapLayer | None:
        combo = self._layer_combos.get(key)
        if combo is not None:
            current_layer = combo.currentLayer()
            if current_layer is not None:
                return current_layer
        return ProjectBaseLayersService.resolve_layer(
            key,
            state={"evel_enabled": self._pend_enabled, "layers": self._pend_layers},
        )

    def _mapping_option_items(self) -> list[tuple[str, str]]:
        return [
            (kind, self.lang_manager.translate(self.MAPPING_KIND_TO_TRANSLATION[kind]))
            for kind in ProjectBaseLayerKeys.SEWER_MAPPING_KIND_ORDER
        ]

    def _default_ids_for_kind(self, kind: str) -> str:
        return str(ProjectBaseLayerKeys.DEFAULT_IDS_BY_KIND.get(kind) or "")

    def _rebuild_mapping_rows_ui(self) -> None:
        while self._mapping_rows_layout.count():
            item = self._mapping_rows_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        self._mapping_row_items = []

        for row_state in self._pend_sewer_mapping_rows:
            row_widget = QWidget(self._mapping_rows_host)
            row = QHBoxLayout(row_widget)
            row.setContentsMargins(self.SHARED_SECTION_OFFSET, 0, 0, 0)
            row.setSpacing(8)
            row.addSpacing(self.INDENT_WIDTH)

            combo = QComboBox(row_widget)
            combo.setObjectName("ModuleLayerCombo")
            combo.setMaximumWidth(self.MAPPING_KIND_MAX_WIDTH)
            for kind, label in self._mapping_option_items():
                combo.addItem(label, kind)

            row_kind = str(row_state.get("kind") or "").strip()
            combo_index = max(0, combo.findData(row_kind))
            combo.setCurrentIndex(combo_index)
            row.addWidget(combo)

            ids_input = QLineEdit(row_widget)
            ids_input.setMaximumWidth(self.MAPPING_IDS_MAX_WIDTH)
            ids_input.setPlaceholderText(self.lang_manager.translate(TranslationKeys.SETTINGS_SHARED_SEWER_IDS_HINT))
            ids_input.setText(str(row_state.get("ids") or ""))
            row.addWidget(ids_input)
            row.addStretch(1)

            row_item = {
                "widget": row_widget,
                "combo": combo,
                "ids_input": ids_input,
                "kind": combo.currentData(),
            }
            combo.currentIndexChanged.connect(
                lambda _idx, item=row_item: self._on_mapping_row_kind_changed(item)
            )
            ids_input.textChanged.connect(lambda _text, item=row_item: self._on_mapping_rows_changed(item))

            self._mapping_row_items.append(row_item)
            self._mapping_rows_layout.addWidget(row_widget)
            self._update_mapping_row_input_state(row_item)

        self._mapping_rows_host.setVisible(self._pend_sewer_mapping_enabled and bool(self._mapping_row_items))

    def _update_mapping_row_input_state(self, row_item: dict[str, object], *, enable_input: Optional[bool] = None) -> None:
        kind = str(row_item["combo"].currentData() or "").strip()
        ids_input = row_item["ids_input"]
        input_enabled = bool(enable_input) if enable_input is not None else True

        if kind == ProjectBaseLayerKeys.SEWER_KIND_OTHER:
            ids_input.blockSignals(True)
            ids_input.setText("")
            ids_input.setPlaceholderText(self.lang_manager.translate(TranslationKeys.SETTINGS_SHARED_SEWER_OTHER_VALUES))
            ids_input.blockSignals(False)
            ids_input.setEnabled(False)
            return

        ids_input.setPlaceholderText(self.lang_manager.translate(TranslationKeys.SETTINGS_SHARED_SEWER_IDS_HINT))
        ids_input.setEnabled(input_enabled)

    def _sync_mapping_rows_from_ui(self) -> None:
        rows: list[dict[str, str]] = []
        for row_item in self._mapping_row_items:
            kind = str(row_item["combo"].currentData() or "").strip()
            if not kind:
                continue
            ids_text = ""
            if kind != ProjectBaseLayerKeys.SEWER_KIND_OTHER:
                ids_text = str(row_item["ids_input"].text() or "").strip()
            rows.append({"kind": kind, "ids": ids_text})
        self._pend_sewer_mapping_rows = ProjectBaseLayersService.normalize_mapping_rows(rows)

    def _on_mapping_row_kind_changed(self, row_item: dict[str, object]) -> None:
        old_kind = str(row_item.get("kind") or "").strip()
        new_kind = str(row_item["combo"].currentData() or "").strip()
        ids_input = row_item["ids_input"]

        previous_default = self._default_ids_for_kind(old_kind)
        if new_kind != ProjectBaseLayerKeys.SEWER_KIND_OTHER:
            current_text = str(ids_input.text() or "").strip()
            if not current_text or current_text == previous_default:
                ids_input.blockSignals(True)
                ids_input.setText(self._default_ids_for_kind(new_kind))
                ids_input.blockSignals(False)

        row_item["kind"] = new_kind
        self._update_mapping_row_input_state(row_item)
        self._sync_mapping_rows_from_ui()
        self._update_status()
        self.pendingChanged.emit(self.has_pending_changes())

    def _on_mapping_rows_changed(self, _row_item: dict[str, object]) -> None:
        self._sync_mapping_rows_from_ui()
        self._update_status()
        self.pendingChanged.emit(self.has_pending_changes())

    def _on_add_mapping_row(self) -> None:
        used_kinds = {str(row.get("kind") or "").strip() for row in self._pend_sewer_mapping_rows}
        next_kind = next(
            (kind for kind in ProjectBaseLayerKeys.SEWER_MAPPING_KIND_ORDER if kind not in used_kinds),
            ProjectBaseLayerKeys.SEWER_KIND_SEWER,
        )
        self._pend_sewer_mapping_rows.append(
            {"kind": next_kind, "ids": self._default_ids_for_kind(next_kind)}
        )
        self._rebuild_mapping_rows_ui()
        self._update_controls_enabled()
        self._update_status()
        self.pendingChanged.emit(self.has_pending_changes())

    def _on_enabled_changed(self, _state: int) -> None:
        self._pend_enabled = bool(self._enabled_checkbox.isChecked())
        if self._pend_enabled:
            self._pend_layers = self._service.detect_evel_layer_ids()
            if not self._pend_sewer_mapping_enabled:
                default_mapping = self._service.default_evel_sewer_mapping_state()
                self._pend_sewer_mapping_enabled = bool(default_mapping.get("enabled"))
                self._pend_sewer_mapping_field = str(default_mapping.get("field") or "")
                rows_state = default_mapping.get("rows") if isinstance(default_mapping.get("rows"), list) else []
                self._pend_sewer_mapping_rows = ProjectBaseLayersService.normalize_mapping_rows(rows_state)
            self._restore_state_to_ui()
        self._update_controls_enabled()
        self._update_status()
        self.pendingChanged.emit(self.has_pending_changes())

    def _on_shared_sewer_mapping_changed(self, _state: int) -> None:
        self._pend_sewer_mapping_enabled = bool(self._shared_sewer_checkbox.isChecked())
        self._sync_shared_sewer_field_combo()
        if self._pend_sewer_mapping_enabled and not self._pend_sewer_mapping_rows:
            self._rebuild_mapping_rows_ui()
        self._update_controls_enabled()
        self._update_status()
        self.pendingChanged.emit(self.has_pending_changes())

    def _on_shared_sewer_field_changed(self, field_name: str) -> None:
        self._pend_sewer_mapping_field = str(field_name or "").strip()
        self._update_status()
        self.pendingChanged.emit(self.has_pending_changes())

    def _on_layer_changed(self, key: str, layer: QgsMapLayer | None) -> None:
        self._pend_layers[key] = layer.id() if layer else ""
        if key == ProjectBaseLayerKeys.SEWERPIPES:
            self._sync_shared_sewer_field_combo()
        self._update_controls_enabled()
        self._update_status()
        self.pendingChanged.emit(self.has_pending_changes())

    def _on_project_layers_changed(self, *args) -> None:
        self._restore_state_to_ui()
        self._update_status()

    def _on_reset_settings(self) -> None:
        self._pend_enabled = False
        self._pend_layers = {key: "" for key in ProjectBaseLayerKeys.ORDER}
        self._pend_sewer_mapping_enabled = False
        self._pend_sewer_mapping_field = ""
        self._pend_sewer_mapping_rows = []
        self._service.clear()
        self._orig_enabled = False
        self._orig_layers = dict(self._pend_layers)
        self._orig_sewer_mapping_enabled = False
        self._orig_sewer_mapping_field = ""
        self._orig_sewer_mapping_rows = []
        self._restore_state_to_ui()
        self._update_status()
        self.pendingChanged.emit(False)

    def _update_status(self) -> None:
        state = {
            "evel_enabled": self._pend_enabled,
            "layers": self._pend_layers,
            "sewer_mapping": {
                "enabled": self._pend_sewer_mapping_enabled,
                "field": self._pend_sewer_mapping_field,
                "rows": self._pend_sewer_mapping_rows,
            },
        }

        parts = []
        include_legacy = True if self._pend_enabled else False

        water_layer = ProjectBaseLayersService.resolve_layer(
            ProjectBaseLayerKeys.WATERPIPES,
            state=state,
            include_legacy=include_legacy,
        )
        if water_layer is not None:
            parts.append(f"{self.lang_manager.translate(self.LAYER_KEY_TO_TRANSLATION[ProjectBaseLayerKeys.WATERPIPES])}: {water_layer.name()}")

        if self._pend_sewer_mapping_enabled:
            sewer_cfg = ProjectBaseLayersService.resolve_layer_config(
                ProjectBaseLayerKeys.SEWERPIPES,
                state=state,
                include_legacy=include_legacy,
            )
            sewer_layer = sewer_cfg.get("layer")
            if sewer_layer is not None:
                mapping_parts = []
                if self._pend_sewer_mapping_field:
                    mapping_parts.append(f"field={self._pend_sewer_mapping_field}")
                for row in self._pend_sewer_mapping_rows[:4]:
                    kind = str(row.get("kind") or "").strip()
                    label_key = self.MAPPING_KIND_TO_TRANSLATION.get(kind)
                    if not label_key:
                        continue
                    label = self.lang_manager.translate(label_key)
                    ids_text = str(row.get("ids") or "").strip()
                    if ids_text:
                        mapping_parts.append(f"{label}={ids_text}")
                    else:
                        mapping_parts.append(label)
                suffix = f" ({'; '.join(mapping_parts)})" if mapping_parts else ""
                parts.append(f"{self.lang_manager.translate(self.LAYER_KEY_TO_TRANSLATION[ProjectBaseLayerKeys.SEWERPIPES])}: {sewer_layer.name()}{suffix}")
        else:
            for key in ProjectBaseLayerKeys.SEWER_TYPE_ORDER:
                layer = ProjectBaseLayersService.resolve_layer(
                    key,
                    state=state,
                    include_legacy=include_legacy,
                )
                if layer is None:
                    continue
                label = self.lang_manager.translate(self.LAYER_KEY_TO_TRANSLATION[key])
                parts.append(f"{label}: {layer.name()}")

        if parts:
            self.set_status_text(" · ".join(parts), True)
            return

        self.set_status_text(self.lang_manager.translate(TranslationKeys.SETTINGS_PROJECT_BASE_LAYERS_EMPTY), True)
