"""Standalone dialog to run Maa-amet field comparisons."""

from typing import Optional, Sequence
import json

from PyQt5.QtWidgets import (
    QDialog,
    QLabel,
    QVBoxLayout,
    QPushButton,
    QFileDialog,
    QHBoxLayout,
    QComboBox,
    QFormLayout,
    QTableWidget,
    QTableWidgetItem,
    QCheckBox,
    QGroupBox,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QBrush
from qgis.core import QgsVectorLayer, QgsProject, QgsWkbTypes, QgsFeature

from ...constants.settings_keys import SettingsService
from ...utils.MapTools.MapHelpers import ActiveLayersHelper, MapHelpers
from ...utils.messagesHelper import ModernMessageDialog
from ...utils.maa_amet.Maa_amet_field_comparer import MaaAmetFieldComparer
from ...constants.file_paths import QssPaths
from ...utils.url_manager import Module
from ...widgets.theme_manager import ThemeManager
from ...languages.language_manager import LanguageManager
from ...languages.translation_keys import TranslationKeys


class SignalTestConst:
    MEMORY_LAYER_NAME = "test"
    MEMORY_LAYER_PREFIX = "Memory_"

    STATUS_MAPPED = "mapped"
    STATUS_MISSING = "missing"
    STATUS_UNMAPPED = "unmapped"
    STATUS_EXTRA = "extra"

    NOTE_REQUIRED = "required"
    NOTE_OPTIONAL = "optional"
    NOTE_EXTRA = "only_in_layer"
    NOTE_TARGET_ONLY = "only_in_target_layer"

    LABEL_EXTRA = "<extra>"
    SOURCE_STORED = "stored_mapping"
    SOURCE_AUTO = "auto"

    ARCHIVE_LAYER_DEFAULT = "Archive_Layer"
    ARCHIVE_LAYER_ALT = "Properties_Archive"


class SignalTestDialog(QDialog):
    def __init__(
        self,
        lang_manager: Optional[LanguageManager] = None,
        parent: Optional[QDialog] = None,
        qss_files: Optional[Sequence[str]] = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle(self.lang_manager.translate(TranslationKeys.SIGNALTEST_DIALOG_TITLE))

        self._qss_files = qss_files
        self._last_layer: Optional[QgsVectorLayer] = None
        self._last_missing_required: list[str] = []
        self._last_missing_optional: list[str] = []

        self.lang_manager = lang_manager or LanguageManager()

        ThemeManager.apply_module_style(self, qss_files or [QssPaths.MAIN])

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(8)

        title = QLabel(self.lang_manager.translate(TranslationKeys.SIGNALTEST))
        title.setObjectName("FilterTitle")
        layout.addWidget(title)

        desc = QLabel(self.lang_manager.translate(TranslationKeys.SIGNALTEST_DESC))
        desc.setWordWrap(True)
        layout.addWidget(desc)

        steps = QGroupBox()
        steps_layout = QHBoxLayout(steps)
        steps_layout.setContentsMargins(0, 0, 0, 0)
        steps_layout.setSpacing(12)

        steps_left = QVBoxLayout()
        steps_left.setContentsMargins(0, 0, 0, 0)
        steps_left.setSpacing(4)

        step_load = QCheckBox(self.lang_manager.translate(TranslationKeys.SIGNALTEST_STEP_LOAD))
        step_review = QCheckBox(self.lang_manager.translate(TranslationKeys.SIGNALTEST_STEP_REVIEW))
        step_map = QCheckBox(self.lang_manager.translate(TranslationKeys.SIGNALTEST_STEP_MAP))

        steps_left.addWidget(step_load)
        steps_left.addWidget(step_review)
        steps_left.addWidget(step_map)

        legend_layout = QVBoxLayout()
        legend_layout.setContentsMargins(0, 0, 0, 0)
        legend_layout.setSpacing(4)

        def add_legend_row(text: str, color: QColor) -> None:
            row = QHBoxLayout()
            row.setContentsMargins(0, 0, 0, 0)
            row.setSpacing(6)
            chip = QLabel()
            chip.setFixedSize(16, 16)
            chip.setStyleSheet(
                f"background-color: rgb({color.red()},{color.green()},{color.blue()}); border: 1px solid #666;"
            )
            row.addWidget(chip)
            row.addWidget(QLabel(text))
            row.addStretch(1)
            legend_layout.addLayout(row)

        add_legend_row(
            self.lang_manager.translate(TranslationKeys.SIGNALTEST_LEGEND_MAPPED),
            QColor(220, 255, 220),
        )
        add_legend_row(
            self.lang_manager.translate(TranslationKeys.SIGNALTEST_LEGEND_MISSING_REQUIRED),
            QColor(255, 220, 220),
        )
        add_legend_row(
            self.lang_manager.translate(TranslationKeys.SIGNALTEST_LEGEND_UNMAPPED_OPTIONAL),
            QColor(255, 245, 200),
        )
        add_legend_row(
            self.lang_manager.translate(TranslationKeys.SIGNALTEST_LEGEND_EXTRA),
            QColor(235, 235, 235),
        )

        steps_layout.addLayout(steps_left, 1)
        steps_layout.addLayout(legend_layout, 1)
        layout.addWidget(steps)

        load_btn = QPushButton(self.lang_manager.translate(TranslationKeys.SIGNALTEST_LOAD_BTN))
        load_btn.clicked.connect(self._on_load_shp)
        layout.addWidget(load_btn)

        self._mapper_btn = QPushButton(
            self.lang_manager.translate(TranslationKeys.SIGNALTEST_MAPPER_BTN)
        )
        self._mapper_btn.setEnabled(False)
        self._mapper_btn.clicked.connect(self._on_open_mapper)

        schema_box = QGroupBox(self.lang_manager.translate(TranslationKeys.SIGNALTEST_PANEL_SCHEMA))
        schema_box_layout = QVBoxLayout(schema_box)
        schema_header = QHBoxLayout()
        self._schema_summary = QLabel("")
        schema_header.addWidget(self._schema_summary, 1)
        schema_header.addWidget(self._mapper_btn)
        schema_box_layout.addLayout(schema_header)
        self._schema_table = QTableWidget()
        self._schema_table.setColumnCount(4)
        self._schema_table.setHorizontalHeaderLabels(self._table_headers())
        self._schema_table.horizontalHeader().setStretchLastSection(True)
        schema_box_layout.addWidget(self._schema_table)
        layout.addWidget(schema_box)

        main_box = QGroupBox(self.lang_manager.translate(TranslationKeys.SIGNALTEST_PANEL_MAIN))
        main_box_layout = QVBoxLayout(main_box)
        self._main_summary = QLabel("")
        main_box_layout.addWidget(self._main_summary)
        self._main_table = QTableWidget()
        self._main_table.setColumnCount(4)
        self._main_table.setHorizontalHeaderLabels(self._table_headers())
        self._main_table.horizontalHeader().setStretchLastSection(True)
        main_box_layout.addWidget(self._main_table)
        layout.addWidget(main_box)

        archive_box = QGroupBox(
            self.lang_manager.translate(TranslationKeys.SIGNALTEST_PANEL_ARCHIVE)
        )
        archive_box_layout = QVBoxLayout(archive_box)
        self._archive_summary = QLabel("")
        archive_box_layout.addWidget(self._archive_summary)
        self._archive_table = QTableWidget()
        self._archive_table.setColumnCount(4)
        self._archive_table.setHorizontalHeaderLabels(self._table_headers())
        self._archive_table.horizontalHeader().setStretchLastSection(True)
        archive_box_layout.addWidget(self._archive_table)
        layout.addWidget(archive_box)

        layout.addStretch(1)

    def _table_headers(self) -> list[str]:
        return [
            self.lang_manager.translate(TranslationKeys.SIGNALTEST_TABLE_HEADER_LOGICAL),
            self.lang_manager.translate(TranslationKeys.SIGNALTEST_TABLE_HEADER_LAYER),
            self.lang_manager.translate(TranslationKeys.SIGNALTEST_TABLE_HEADER_STATUS),
            self.lang_manager.translate(TranslationKeys.SIGNALTEST_TABLE_HEADER_NOTE),
        ]

    def _show_rows(self, table: QTableWidget, rows: list[dict]) -> None:
        table.setRowCount(len(rows))
        for r, row in enumerate(rows):
            logical_val = row.get("logical", "")
            if logical_val == SignalTestConst.LABEL_EXTRA:
                logical_val = self.lang_manager.translate(TranslationKeys.SIGNALTEST_LABEL_EXTRA)

            status_code = row.get("status", "")
            note_code = row.get("note", "")
            status_display = self._status_label(status_code)
            note_display = self._note_label(note_code)

            items = [
                QTableWidgetItem(logical_val),
                QTableWidgetItem(row.get("mapped", "")),
                QTableWidgetItem(status_display),
                QTableWidgetItem(note_display),
            ]
            status = status_code
            color = None
            if status == SignalTestConst.STATUS_MAPPED:
                color = QColor(220, 255, 220)
            elif status == SignalTestConst.STATUS_MISSING:
                color = QColor(255, 220, 220)
            elif status == SignalTestConst.STATUS_UNMAPPED:
                color = QColor(255, 245, 200)
            elif status == SignalTestConst.STATUS_EXTRA:
                color = QColor(235, 235, 235)

            for c, it in enumerate(items):
                if color:
                    it.setBackground(QBrush(color))
                table.setItem(r, c, it)
        table.resizeColumnsToContents()

    def _status_label(self, code: str) -> str:
        if code == SignalTestConst.STATUS_MAPPED:
            return self.lang_manager.translate(TranslationKeys.SIGNALTEST_STATUS_MAPPED)
        if code == SignalTestConst.STATUS_MISSING:
            return self.lang_manager.translate(TranslationKeys.SIGNALTEST_STATUS_MISSING)
        if code == SignalTestConst.STATUS_UNMAPPED:
            return self.lang_manager.translate(TranslationKeys.SIGNALTEST_STATUS_UNMAPPED)
        if code == SignalTestConst.STATUS_EXTRA:
            return self.lang_manager.translate(TranslationKeys.SIGNALTEST_STATUS_EXTRA)
        return code

    def _note_label(self, code: str) -> str:
        if code == SignalTestConst.NOTE_REQUIRED:
            return self.lang_manager.translate(TranslationKeys.SIGNALTEST_NOTE_REQUIRED)
        if code == SignalTestConst.NOTE_OPTIONAL:
            return self.lang_manager.translate(TranslationKeys.SIGNALTEST_NOTE_OPTIONAL)
        if code == SignalTestConst.NOTE_EXTRA:
            return self.lang_manager.translate(TranslationKeys.SIGNALTEST_NOTE_EXTRA)
        if code == SignalTestConst.NOTE_TARGET_ONLY:
            return self.lang_manager.translate(TranslationKeys.SIGNALTEST_NOTE_TARGET_ONLY)
        if code == SignalTestConst.SOURCE_STORED:
            return self.lang_manager.translate(TranslationKeys.SIGNALTEST_SOURCE_STORED)
        if code == SignalTestConst.SOURCE_AUTO:
            return self.lang_manager.translate(TranslationKeys.SIGNALTEST_SOURCE_AUTO)
        return code

    def _update_schema_summary(self, missing_required: int, missing_optional: int, rows: list[dict]) -> None:
        extras = sum(1 for r in rows if r.get("status") == SignalTestConst.STATUS_EXTRA)
        self._schema_summary.setText(
            self.lang_manager.translate(TranslationKeys.SIGNALTEST_SUMMARY_TEMPLATE).format(
                missing_required=missing_required,
                missing_optional=missing_optional,
                extras=extras,
            )
        )

    def _update_main_summary(self, missing: int, extras: int) -> None:
        self._main_summary.setText(
            self.lang_manager.translate(TranslationKeys.SIGNALTEST_MAIN_SUMMARY_TEMPLATE).format(
                missing=missing,
                extras=extras,
            )
        )

    def _update_archive_summary(self, missing: int, extras: int, found: bool) -> None:
        if not found:
            self._archive_summary.setText(
                self.lang_manager.translate(TranslationKeys.SIGNALTEST_ARCHIVE_NOT_FOUND)
            )
        else:
            self._archive_summary.setText(
                self.lang_manager.translate(TranslationKeys.SIGNALTEST_ARCHIVE_SUMMARY_TEMPLATE).format(
                    missing=missing,
                    extras=extras,
                )
            )

    def _on_open_mapper(self) -> None:
        if not self._last_layer:
            ModernMessageDialog.show_warning(
                self.lang_manager.translate(TranslationKeys.SIGNALTEST_MSG_NO_LAYER_TITLE),
                self.lang_manager.translate(TranslationKeys.SIGNALTEST_MSG_NO_LAYER_BODY),
            )
            return
        self._ensure_mapping(self._last_layer, self._last_missing_required, self._last_missing_optional)
        logical_required, logical_optional = MaaAmetFieldComparer.logical_fields()
        rows, _, _ = MaaAmetFieldComparer.compare_layer_fields(
            self._last_layer,
            self._load_mapping(self._last_layer),
            logical_required,
            logical_optional,
            label_extra=SignalTestConst.LABEL_EXTRA,
            status_mapped=SignalTestConst.STATUS_MAPPED,
            status_missing=SignalTestConst.STATUS_MISSING,
            status_unmapped=SignalTestConst.STATUS_UNMAPPED,
            status_extra=SignalTestConst.STATUS_EXTRA,
            note_required=SignalTestConst.NOTE_REQUIRED,
            note_optional=SignalTestConst.NOTE_OPTIONAL,
            note_extra=SignalTestConst.NOTE_EXTRA,
            source_stored=SignalTestConst.SOURCE_STORED,
            source_auto=SignalTestConst.SOURCE_AUTO,
        )
        self._show_rows(self._schema_table, rows)
        self._update_schema_summary(0, 0, rows)
        self._mapper_btn.setEnabled(False)

    def _on_load_shp(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            self.lang_manager.translate(TranslationKeys.SIGNALTEST_FILE_DIALOG_TITLE),
            "",
            self.lang_manager.translate(TranslationKeys.SIGNALTEST_FILE_DIALOG_FILTER),
        )
        if not path:
            return

        layer = QgsVectorLayer(path, SignalTestConst.MEMORY_LAYER_NAME, "ogr")
        if not layer.isValid():
            ModernMessageDialog.show_warning(
                self.lang_manager.translate(TranslationKeys.ERROR),
                self.lang_manager.translate(TranslationKeys.SIGNALTEST_MSG_LOAD_FAIL),
            )
            return

        mem_layer = self._copy_to_memory(layer)
        if mem_layer is None:
            ModernMessageDialog.show_warning(
                self.lang_manager.translate(TranslationKeys.ERROR),
                self.lang_manager.translate(TranslationKeys.SIGNALTEST_MSG_COPY_FAIL),
            )
            return

        QgsProject.instance().addMapLayer(mem_layer)

        self._last_layer = mem_layer

        logical_required, logical_optional = MaaAmetFieldComparer.logical_fields()
        rows, missing_required, missing_optional = MaaAmetFieldComparer.compare_layer_fields(
            mem_layer,
            self._load_mapping(mem_layer),
            logical_required,
            logical_optional,
            label_extra=SignalTestConst.LABEL_EXTRA,
            status_mapped=SignalTestConst.STATUS_MAPPED,
            status_missing=SignalTestConst.STATUS_MISSING,
            status_unmapped=SignalTestConst.STATUS_UNMAPPED,
            status_extra=SignalTestConst.STATUS_EXTRA,
            note_required=SignalTestConst.NOTE_REQUIRED,
            note_optional=SignalTestConst.NOTE_OPTIONAL,
            note_extra=SignalTestConst.NOTE_EXTRA,
            source_stored=SignalTestConst.SOURCE_STORED,
            source_auto=SignalTestConst.SOURCE_AUTO,
        )
        self._show_rows(self._schema_table, rows)
        self._last_missing_required = missing_required
        self._last_missing_optional = missing_optional
        self._update_schema_summary(len(missing_required), len(missing_optional), rows)
        self._mapper_btn.setEnabled(bool(missing_required or missing_optional))
        if missing_required or missing_optional:
            self._ensure_mapping(mem_layer, missing_required, missing_optional)
            rows, _, _ = MaaAmetFieldComparer.compare_layer_fields(
                mem_layer,
                self._load_mapping(mem_layer),
                logical_required,
                logical_optional,
                label_extra=SignalTestConst.LABEL_EXTRA,
                status_mapped=SignalTestConst.STATUS_MAPPED,
                status_missing=SignalTestConst.STATUS_MISSING,
                status_unmapped=SignalTestConst.STATUS_UNMAPPED,
                status_extra=SignalTestConst.STATUS_EXTRA,
                note_required=SignalTestConst.NOTE_REQUIRED,
                note_optional=SignalTestConst.NOTE_OPTIONAL,
                note_extra=SignalTestConst.NOTE_EXTRA,
                source_stored=SignalTestConst.SOURCE_STORED,
                source_auto=SignalTestConst.SOURCE_AUTO,
            )
            self._show_rows(self._schema_table, rows)
            self._last_missing_required, self._last_missing_optional = [], []
            self._update_schema_summary(0, 0, rows)
            self._mapper_btn.setEnabled(False)
        ModernMessageDialog.show_info(
            self.lang_manager.translate(TranslationKeys.SIGNALTEST_MSG_COMPARISON_TITLE),
            self.lang_manager.translate(TranslationKeys.SIGNALTEST_MSG_COMPARISON_DONE),
        )

        main_layer = ActiveLayersHelper.resolve_main_property_layer(silent=True)
        if main_layer is not None and main_layer.isValid():
            main_rows, main_missing, main_extras = MaaAmetFieldComparer.compare_against_target(
                mem_layer,
                main_layer,
                self.lang_manager.translate(TranslationKeys.SIGNALTEST_PANEL_MAIN),
                label_extra=SignalTestConst.LABEL_EXTRA,
                status_mapped=SignalTestConst.STATUS_MAPPED,
                status_missing=SignalTestConst.STATUS_MISSING,
                status_extra=SignalTestConst.STATUS_EXTRA,
                note_target_only=SignalTestConst.NOTE_TARGET_ONLY,
            )
            self._show_rows(self._main_table, main_rows)
            self._update_main_summary(main_missing, main_extras)
        else:
            self._show_rows(self._main_table, [])
            self._update_main_summary(0, 0)

        archive_layer = self._resolve_archive_layer()
        if archive_layer is not None and archive_layer.isValid():
            archive_rows, archive_missing, archive_extras = MaaAmetFieldComparer.compare_against_target(
                mem_layer,
                archive_layer,
                self.lang_manager.translate(TranslationKeys.SIGNALTEST_PANEL_ARCHIVE),
                label_extra=SignalTestConst.LABEL_EXTRA,
                status_mapped=SignalTestConst.STATUS_MAPPED,
                status_missing=SignalTestConst.STATUS_MISSING,
                status_extra=SignalTestConst.STATUS_EXTRA,
                note_target_only=SignalTestConst.NOTE_TARGET_ONLY,
            )
            self._show_rows(self._archive_table, archive_rows)
            self._update_archive_summary(archive_missing, archive_extras, True)
        else:
            self._show_rows(self._archive_table, [])
            self._update_archive_summary(0, 0, False)

    def _copy_to_memory(self, src: QgsVectorLayer) -> Optional[QgsVectorLayer]:
        crs = src.crs().authid() or ""
        geom = QgsWkbTypes.displayString(src.wkbType()) or "Polygon"
        mem_layer = QgsVectorLayer(
            f"{geom}?crs={crs}", f"{SignalTestConst.MEMORY_LAYER_PREFIX}{src.name()}", "memory"
        )
        if not mem_layer.isValid():
            return None

        prov = mem_layer.dataProvider()
        prov.addAttributes(list(src.fields()))
        mem_layer.updateFields()

        feats = []
        for f in src.getFeatures():
            nf = QgsFeature(mem_layer.fields())
            nf.setGeometry(f.geometry())
            for idx, fld in enumerate(src.fields()):
                try:
                    nf.setAttribute(idx, f[idx])
                except Exception:
                    continue
            feats.append(nf)

        prov.addFeatures(feats)
        mem_layer.updateExtents()
        return mem_layer

    def _load_mapping(self, layer: QgsVectorLayer) -> dict:
        raw = layer.customProperty("kavitro.field_mapping", "")
        if not raw:
            return {}
        try:
            return json.loads(raw)
        except Exception:
            return {}

    def _save_mapping(self, layer: QgsVectorLayer, mapping: dict) -> None:
        layer.setCustomProperty("kavitro.field_mapping", json.dumps(mapping))

    def _ensure_mapping(self, layer: QgsVectorLayer, missing_required: list[str], missing_optional: list[str]) -> None:
        dialog = FieldMapperDialog(layer, missing_required, missing_optional, self.lang_manager)
        if dialog.exec_() == QDialog.Accepted:
            mapping = dialog.result_mapping
            self._save_mapping(layer, mapping)
            ModernMessageDialog.show_info(
                self.lang_manager.translate(TranslationKeys.SIGNALTEST_MSG_MAPPING_SAVED_TITLE),
                self.lang_manager.translate(TranslationKeys.SIGNALTEST_MSG_MAPPING_SAVED_BODY),
            )
        else:
            ModernMessageDialog.show_warning(
                self.lang_manager.translate(TranslationKeys.SIGNALTEST_MSG_MAPPING_NOT_SAVED_TITLE),
                self.lang_manager.translate(TranslationKeys.SIGNALTEST_MSG_MAPPING_NOT_SAVED_BODY),
            )

    def _resolve_archive_layer(self) -> Optional[QgsVectorLayer]:
        settings = SettingsService()
        identifier = settings.module_archive_layer_name(Module.PROPERTY.value) or ""
        layer = MapHelpers.resolve_layer(identifier)
        if layer and layer.isValid():
            return layer

        candidates = [SignalTestConst.ARCHIVE_LAYER_DEFAULT, SignalTestConst.ARCHIVE_LAYER_ALT]
        for name in candidates:
            layers = QgsProject.instance().mapLayersByName(name)
            if layers:
                lyr = layers[0]
                if lyr and lyr.isValid():
                    return lyr
        return None


class FieldMapperDialog(QDialog):
    def __init__(
        self,
        layer: QgsVectorLayer,
        missing_required: list[str],
        missing_optional: list[str],
        lang_manager: LanguageManager,
    ) -> None:
        super().__init__()
        self.lang_manager = lang_manager
        self.setWindowTitle(self.lang_manager.translate(TranslationKeys.SIGNALTEST_DIALOG_TITLE))
        self.result_mapping: dict[str, str] = {}
        layout = QVBoxLayout(self)
        hint = QLabel(self.lang_manager.translate(TranslationKeys.SIGNALTEST_DIALOG_HINT))
        hint.setWordWrap(True)
        layout.addWidget(hint)
        form = QFormLayout()

        self._combos = {}
        all_fields = [f.name() for f in layer.fields()]
        all_fields_sorted = sorted(all_fields, key=str.lower)

        def add_row(logical: str, required: bool) -> None:
            combo = QComboBox()
            combo.addItem(self.lang_manager.translate(TranslationKeys.SIGNALTEST_NONE_OPTION), "")
            for name in all_fields_sorted:
                combo.addItem(name, name)
                combo.setItemData(
                    combo.count() - 1,
                    self.lang_manager.translate(TranslationKeys.SIGNALTEST_OPTION_TOOLTIP).format(
                        logical=logical, name=name
                    ),
                    role=Qt.ToolTipRole,
                )
            if required and all_fields_sorted:
                guess = next((n for n in all_fields_sorted if n.lower() == logical.lower()), None)
                if guess:
                    combo.setCurrentText(guess)
            label = QLabel(
                f"{logical}{self.lang_manager.translate(TranslationKeys.SIGNALTEST_REQUIRED_SUFFIX) if required else ''}"
            )
            label.setToolTip(
                self.lang_manager.translate(TranslationKeys.SIGNALTEST_LOGICAL_TOOLTIP).format(logical=logical)
            )
            form.addRow(label, combo)
            self._combos[logical] = (combo, required)

        for logical in missing_required:
            add_row(logical, True)
        for logical in missing_optional:
            add_row(logical, False)

        layout.addLayout(form)

        btns = QHBoxLayout()
        save_btn = QPushButton(self.lang_manager.translate(TranslationKeys.SAVE))
        cancel_btn = QPushButton(self.lang_manager.translate(TranslationKeys.CANCEL_BUTTON))
        btns.addStretch(1)
        btns.addWidget(cancel_btn)
        btns.addWidget(save_btn)
        layout.addLayout(btns)

        cancel_btn.clicked.connect(self.reject)
        save_btn.clicked.connect(self._on_save)

    def _on_save(self):
        for logical, (combo, required) in self._combos.items():
            val = combo.currentData()
            if required and not val:
                ModernMessageDialog.show_warning(
                    self.lang_manager.translate(TranslationKeys.SIGNALTEST_MSG_MISSING_FIELD_TITLE),
                    self.lang_manager.translate(TranslationKeys.SIGNALTEST_MSG_MISSING_FIELD_BODY).format(
                        field=logical
                    ),
                )
                return
            if val:
                self.result_mapping[logical] = val
        self.accept()
