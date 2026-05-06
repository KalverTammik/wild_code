from __future__ import annotations

import re
from typing import Optional

from PyQt5.QtCore import QDate, QDateTime, Qt
from PyQt5.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDateEdit,
    QDateTimeEdit,
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)
from qgis.PyQt.QtCore import QVariant
from qgis.core import Qgis, QgsCoordinateTransform, QgsFeature, QgsProject, QgsVectorLayer
from qgis.gui import QgsMapLayerComboBox

from ...Logs.python_fail_logger import PythonFailLogger
from ...languages.translation_keys import TranslationKeys
from ...utils.messagesHelper import ModernMessageDialog
from ...utils.url_manager import Module


class _DefaultValueEditor(QWidget):
    def __init__(self, field, *, lang_manager, parent=None):
        super().__init__(parent)
        self._field = field
        self._lang = lang_manager
        self._mode = "text"
        self._line_edit: Optional[QLineEdit] = None
        self._bool_combo: Optional[QComboBox] = None
        self._enable_checkbox: Optional[QCheckBox] = None
        self._date_edit: Optional[QDateEdit] = None
        self._datetime_edit: Optional[QDateTimeEdit] = None

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        field_type = self._field.type() if self._field is not None else None

        if field_type == QVariant.Bool:
            self._mode = "bool"
            combo = QComboBox(self)
            combo.addItem(self._lang.translate(TranslationKeys.GEOSPATIAL_LAYER_MAPPER_NO_DEFAULT), None)
            combo.addItem("False", False)
            combo.addItem("True", True)
            self._bool_combo = combo
            layout.addWidget(combo)
            return

        if field_type == QVariant.Date:
            self._mode = "date"
            enable = QCheckBox(self._lang.translate(TranslationKeys.GEOSPATIAL_LAYER_MAPPER_USE_DEFAULT), self)
            edit = QDateEdit(self)
            edit.setCalendarPopup(True)
            edit.setDate(QDate.currentDate())
            edit.setEnabled(False)
            enable.toggled.connect(edit.setEnabled)
            self._enable_checkbox = enable
            self._date_edit = edit
            layout.addWidget(enable)
            layout.addWidget(edit)
            return

        if field_type == QVariant.DateTime:
            self._mode = "datetime"
            enable = QCheckBox(self._lang.translate(TranslationKeys.GEOSPATIAL_LAYER_MAPPER_USE_DEFAULT), self)
            edit = QDateTimeEdit(self)
            edit.setCalendarPopup(True)
            edit.setDateTime(QDateTime.currentDateTime())
            edit.setEnabled(False)
            enable.toggled.connect(edit.setEnabled)
            self._enable_checkbox = enable
            self._datetime_edit = edit
            layout.addWidget(enable)
            layout.addWidget(edit)
            return

        line_edit = QLineEdit(self)
        line_edit.setPlaceholderText(self._lang.translate(TranslationKeys.GEOSPATIAL_LAYER_MAPPER_OPTIONAL_DEFAULT))
        self._line_edit = line_edit
        layout.addWidget(line_edit)

    def has_value(self) -> bool:
        if self._mode == "bool":
            return self._bool_combo is not None and self._bool_combo.currentData() is not None
        if self._mode == "date":
            return bool(self._enable_checkbox and self._enable_checkbox.isChecked() and self._date_edit is not None)
        if self._mode == "datetime":
            return bool(self._enable_checkbox and self._enable_checkbox.isChecked() and self._datetime_edit is not None)
        return bool(self._line_edit and str(self._line_edit.text() or "").strip())

    def value(self):
        if self._mode == "bool":
            return self._bool_combo.currentData() if self._bool_combo is not None else None
        if self._mode == "date":
            return self._date_edit.date() if self.has_value() and self._date_edit is not None else None
        if self._mode == "datetime":
            return self._datetime_edit.dateTime() if self.has_value() and self._datetime_edit is not None else None
        return str(self._line_edit.text() or "").strip() if self._line_edit is not None else ""


class GeospatialLayerMapperDialog(QDialog):
    _INTERNAL_FIELD_NAMES = {"fid", "id", "geom"}
    _IDENTITY_CANDIDATES = {
        Module.WORKS.value: ("ext_job_id",),
        Module.ASBUILT.value: ("ext_job_id",),
        Module.PROJECT.value: ("ext_project_id",),
        Module.EASEMENT.value: ("ext_easement_id", "ext_job_id"),
    }

    def __init__(self, *, lang_manager, module_name: str, target_layer: QgsVectorLayer, parent=None):
        super().__init__(parent)
        self._lang = lang_manager
        self._module_name = str(module_name or "").strip().lower()
        self._target_layer = target_layer
        self._source_combo: Optional[QgsMapLayerComboBox] = None
        self._table: Optional[QTableWidget] = None
        self._target_fields: list = []
        self._source_field_combos: dict[str, QComboBox] = {}
        self._default_editors: dict[str, _DefaultValueEditor] = {}

        self.setWindowTitle(self._lang.translate(TranslationKeys.GEOSPATIAL_LAYER_MAPPER_DIALOG_TITLE))
        self.resize(980, 640)
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)

        description = QLabel(
            self._lang.translate(TranslationKeys.GEOSPATIAL_LAYER_MAPPER_DIALOG_DESCRIPTION).format(
                module=self._module_name,
                target=self._layer_label(self._target_layer),
            ),
            self,
        )
        description.setWordWrap(True)
        layout.addWidget(description)

        source_row = QHBoxLayout()
        source_label = QLabel(self._lang.translate(TranslationKeys.GEOSPATIAL_LAYER_MAPPER_SOURCE_LAYER), self)
        source_row.addWidget(source_label)
        source_combo = QgsMapLayerComboBox(self)
        source_combo.setAllowEmptyLayer(True, self._lang.translate(TranslationKeys.SELECT_LAYER))
        source_combo.setShowCrs(False)
        source_combo.setFilters(Qgis.LayerFilter.HasGeometry)
        source_combo.layerChanged.connect(self._rebuild_mapping_rows)
        self._source_combo = source_combo
        source_row.addWidget(source_combo, 1)
        layout.addLayout(source_row)

        self._table = QTableWidget(0, 3, self)
        self._table.setHorizontalHeaderLabels(
            [
                self._lang.translate(TranslationKeys.GEOSPATIAL_LAYER_MAPPER_TARGET_FIELD),
                self._lang.translate(TranslationKeys.GEOSPATIAL_LAYER_MAPPER_SOURCE_FIELD),
                self._lang.translate(TranslationKeys.GEOSPATIAL_LAYER_MAPPER_DEFAULT_VALUE),
            ]
        )
        header = self._table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        self._table.verticalHeader().setVisible(False)
        layout.addWidget(self._table, 1)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, parent=self)
        run_button = button_box.button(QDialogButtonBox.Ok)
        if run_button is not None:
            run_button.setText(self._lang.translate(TranslationKeys.GEOSPATIAL_LAYER_MAPPER_RUN_BUTTON))
        button_box.accepted.connect(self._on_accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

        self._rebuild_mapping_rows()

    def _rebuild_mapping_rows(self) -> None:
        if self._table is None:
            return

        source_layer = self._source_combo.currentLayer() if self._source_combo is not None else None
        source_fields = self._list_mappable_fields(source_layer)
        source_names = [field.name() for field in source_fields]
        source_fields_by_name = {field.name(): field for field in source_fields}

        self._target_fields = self._list_mappable_fields(self._target_layer)
        self._source_field_combos.clear()
        self._default_editors.clear()
        self._table.setRowCount(len(self._target_fields))

        for row_index, field in enumerate(self._target_fields):
            field_name = field.name()
            item = QTableWidgetItem(field_name)
            item.setFlags(item.flags() & ~Qt.ItemIsEditable)
            item.setToolTip(self._field_type_label(field.type()))
            self._table.setItem(row_index, 0, item)

            source_combo = QComboBox(self._table)
            source_combo.addItem(self._lang.translate(TranslationKeys.GEOSPATIAL_LAYER_MAPPER_NONE_OPTION), "")
            for source_name in source_names:
                source_combo.addItem(source_name, source_name)
            guessed_match = self._guess_source_field(field, source_fields_by_name)
            if guessed_match:
                source_combo.setCurrentIndex(max(0, source_combo.findData(guessed_match)))
            self._table.setCellWidget(row_index, 1, source_combo)
            self._source_field_combos[field_name] = source_combo

            default_editor = _DefaultValueEditor(field, lang_manager=self._lang, parent=self._table)
            self._table.setCellWidget(row_index, 2, default_editor)
            self._default_editors[field_name] = default_editor

    def _on_accept(self) -> None:
        source_layer = self._source_combo.currentLayer() if self._source_combo is not None else None
        if not isinstance(source_layer, QgsVectorLayer) or not source_layer.isValid():
            ModernMessageDialog.show_warning(
                self._lang.translate(TranslationKeys.ERROR),
                self._lang.translate(TranslationKeys.GEOSPATIAL_LAYER_MAPPER_SOURCE_REQUIRED),
                parent=self,
            )
            return

        mapping_rows = self._collect_mapping_rows()
        feature_count = int(source_layer.featureCount()) if source_layer is not None else 0
        confirmed = ModernMessageDialog.ask_yes_no(
            self._lang.translate(TranslationKeys.GEOSPATIAL_LAYER_MAPPER_CONFIRM_TITLE),
            self._lang.translate(TranslationKeys.GEOSPATIAL_LAYER_MAPPER_CONFIRM_BODY).format(
                source=self._layer_label(source_layer),
                target=self._layer_label(self._target_layer),
                count=feature_count,
            ),
            yes_label=self._lang.translate(TranslationKeys.OK),
            no_label=self._lang.translate(TranslationKeys.CANCEL_BUTTON),
            default=self._lang.translate(TranslationKeys.OK),
        )
        if not confirmed:
            return

        inserted, updated, skipped, errors = self._transfer_features(source_layer, mapping_rows)
        if errors:
            ModernMessageDialog.show_warning(
                self._lang.translate(TranslationKeys.ERROR),
                self._lang.translate(TranslationKeys.GEOSPATIAL_LAYER_MAPPER_RESULT_WITH_ERRORS).format(
                    inserted=inserted,
                    updated=updated,
                    skipped=skipped,
                    errors="\n".join(errors[:5]),
                ),
                parent=self,
            )
            return

        ModernMessageDialog.show_info(
            self._lang.translate(TranslationKeys.SUCCESS),
            self._lang.translate(TranslationKeys.GEOSPATIAL_LAYER_MAPPER_RESULT_SUCCESS).format(
                inserted=inserted,
                updated=updated,
                skipped=skipped,
            ),
        )
        self.accept()

    def _collect_mapping_rows(self) -> list[dict[str, object]]:
        rows: list[dict[str, object]] = []
        for field in self._target_fields:
            field_name = field.name()
            source_combo = self._source_field_combos.get(field_name)
            default_editor = self._default_editors.get(field_name)
            rows.append(
                {
                    "target": field_name,
                    "source": str(source_combo.currentData() or "").strip() if source_combo is not None else "",
                    "has_default": bool(default_editor and default_editor.has_value()),
                    "default": default_editor.value() if default_editor is not None else None,
                }
            )
        return rows

    def _transfer_features(self, source_layer: QgsVectorLayer, mapping_rows: list[dict[str, object]]) -> tuple[int, int, int, list[str]]:
        target_layer = self._target_layer
        target_field_map = {field.name().lower(): field.name() for field in target_layer.fields()}
        source_field_map = {field.name().lower(): field.name() for field in source_layer.fields()}

        candidates = self._IDENTITY_CANDIDATES.get(self._module_name, tuple())
        target_identity = self._resolve_first_field(target_field_map, candidates)
        source_identity = self._resolve_first_field(source_field_map, candidates)
        existing_by_identity: dict[str, int] = {}
        if target_identity and source_identity:
            for feature in target_layer.getFeatures():
                key = self._identity_key(feature.attribute(target_identity))
                if key:
                    existing_by_identity[key] = int(feature.id())

        transform = self._build_geometry_transform(source_layer, target_layer)
        inserted = 0
        updated = 0
        skipped = 0
        errors: list[str] = []

        started_edit = False
        already_editable = bool(target_layer.isEditable())
        try:
            if not already_editable:
                started_edit = bool(target_layer.startEditing())
                if not started_edit:
                    return 0, 0, 0, [self._lang.translate(TranslationKeys.GEOSPATIAL_LAYER_MAPPER_EDIT_START_FAILED)]

            for source_feature in source_layer.getFeatures():
                identity_value = self._identity_key(source_feature.attribute(source_identity)) if source_identity else ""
                target_feature_id = existing_by_identity.get(identity_value) if identity_value else None
                geometry = self._transformed_geometry(source_feature.geometry(), transform)

                if target_feature_id is not None:
                    changed = False
                    if geometry is not None and not geometry.isEmpty():
                        if target_layer.changeGeometry(target_feature_id, geometry):
                            changed = True

                    for row in mapping_rows:
                        actual_target = target_field_map.get(str(row.get("target") or "").lower())
                        if not actual_target:
                            continue
                        target_index = target_layer.fields().indexFromName(actual_target)
                        if target_index < 0:
                            continue
                        has_value, value = self._mapped_value_for_feature(source_feature, row)
                        if not has_value:
                            continue
                        coerced = self._coerce_value_for_field(target_layer.fields()[target_index], value)
                        if target_layer.changeAttributeValue(target_feature_id, target_index, coerced):
                            changed = True

                    if changed:
                        updated += 1
                    else:
                        skipped += 1
                    continue

                new_feature = QgsFeature(target_layer.fields())
                if geometry is not None and not geometry.isEmpty():
                    new_feature.setGeometry(geometry)

                assigned_any = False
                for row in mapping_rows:
                    actual_target = target_field_map.get(str(row.get("target") or "").lower())
                    if not actual_target:
                        continue
                    target_index = target_layer.fields().indexFromName(actual_target)
                    if target_index < 0:
                        continue
                    has_value, value = self._mapped_value_for_feature(source_feature, row)
                    if not has_value:
                        continue
                    coerced = self._coerce_value_for_field(target_layer.fields()[target_index], value)
                    new_feature.setAttribute(actual_target, coerced)
                    assigned_any = True

                if not assigned_any and (geometry is None or geometry.isEmpty()):
                    skipped += 1
                    continue

                if target_layer.addFeature(new_feature):
                    inserted += 1
                else:
                    errors.append(self._lang.translate(TranslationKeys.GEOSPATIAL_LAYER_MAPPER_ADD_FEATURE_FAILED))

            if already_editable:
                target_layer.updateFields()
                target_layer.triggerRepaint()
                return inserted, updated, skipped, errors

            if not target_layer.commitChanges():
                commit_errors = "; ".join(target_layer.commitErrors() or [])
                target_layer.rollBack()
                return 0, 0, 0, [commit_errors or self._lang.translate(TranslationKeys.GEOSPATIAL_LAYER_MAPPER_COMMIT_FAILED)]

            target_layer.updateFields()
            target_layer.triggerRepaint()
            return inserted, updated, skipped, errors
        except Exception as exc:
            try:
                if started_edit and target_layer.isEditable():
                    target_layer.rollBack()
            except Exception:
                pass
            PythonFailLogger.log_exception(
                exc,
                module=Module.SETTINGS.value,
                event="geospatial_layer_mapper_transfer_failed",
                extra={"module_name": self._module_name},
            )
            return 0, 0, 0, [str(exc)]

    @staticmethod
    def _resolve_first_field(field_map: dict[str, str], candidates: tuple[str, ...]) -> str:
        for candidate in candidates:
            actual = field_map.get(str(candidate).lower())
            if actual:
                return actual
        return ""

    @staticmethod
    def _identity_key(value) -> str:
        return str(value or "").strip()

    def _mapped_value_for_feature(self, source_feature, row: dict[str, object]) -> tuple[bool, object]:
        source_name = str(row.get("source") or "").strip()
        if source_name:
            value = source_feature.attribute(source_name)
            if not self._is_empty(value):
                return True, value

        if row.get("has_default"):
            return True, row.get("default")

        return False, None

    @staticmethod
    def _is_empty(value) -> bool:
        if value is None:
            return True
        if isinstance(value, str):
            return not value.strip()
        return False

    @staticmethod
    def _build_geometry_transform(source_layer: QgsVectorLayer, target_layer: QgsVectorLayer):
        try:
            source_crs = source_layer.crs()
            target_crs = target_layer.crs()
            if not source_crs.isValid() or not target_crs.isValid() or source_crs == target_crs:
                return None
            return QgsCoordinateTransform(source_crs, target_crs, QgsProject.instance().transformContext())
        except Exception:
            return None

    @staticmethod
    def _transformed_geometry(geometry, transform):
        if geometry is None or geometry.isEmpty() or transform is None:
            return geometry
        copied = geometry
        try:
            copied.transform(transform)
        except Exception:
            return geometry
        return copied

    @classmethod
    def _list_mappable_fields(cls, layer: Optional[QgsVectorLayer]) -> list:
        if not isinstance(layer, QgsVectorLayer) or not layer.isValid():
            return []
        return [field for field in layer.fields() if str(field.name() or "").strip().lower() not in cls._INTERNAL_FIELD_NAMES]

    @staticmethod
    def _normalize_name(value: str) -> str:
        return re.sub(r"[^a-z0-9]", "", str(value or "").lower())

    @classmethod
    def _guess_source_field(cls, target_field, source_fields_by_name: dict[str, object]) -> str:
        target_name = target_field.name() if target_field is not None else ""
        target_normalized = cls._normalize_name(target_name)
        if not target_normalized:
            return ""

        exact = {
            cls._normalize_name(name): name
            for name, field in source_fields_by_name.items()
            if cls._field_types_compatible(target_field, field)
        }
        if target_normalized in exact:
            return exact[target_normalized]

        candidates = [
            name
            for name, field in source_fields_by_name.items()
            if cls._field_types_compatible(target_field, field)
            and (target_normalized in cls._normalize_name(name) or cls._normalize_name(name) in target_normalized)
        ]
        if candidates:
            return sorted(candidates, key=lambda name: len(cls._normalize_name(name)))[0]
        return ""

    @staticmethod
    def _field_types_compatible(target_field, source_field) -> bool:
        if target_field is None or source_field is None:
            return False
        try:
            target_type = target_field.type()
            source_type = source_field.type()
        except Exception:
            return False

        integer_types = {
            QVariant.Int,
            getattr(QVariant, "LongLong", QVariant.Int),
            getattr(QVariant, "UInt", QVariant.Int),
            getattr(QVariant, "ULongLong", QVariant.Int),
        }
        if target_type in integer_types:
            return source_type in integer_types
        if target_type == QVariant.Bool:
            return source_type == QVariant.Bool
        if target_type == QVariant.DateTime:
            return source_type in {QVariant.DateTime, QVariant.Date, QVariant.String}
        if target_type == QVariant.Date:
            return source_type in {QVariant.Date, QVariant.DateTime, QVariant.String}
        if target_type == QVariant.String:
            return True
        return target_type == source_type

    @staticmethod
    def _field_type_label(field_type) -> str:
        integer_types = {
            QVariant.Int,
            getattr(QVariant, "LongLong", QVariant.Int),
            getattr(QVariant, "UInt", QVariant.Int),
            getattr(QVariant, "ULongLong", QVariant.Int),
        }
        if field_type in integer_types:
            return "Integer"
        if field_type == QVariant.String:
            return "Text"
        if field_type == QVariant.Bool:
            return "Boolean"
        if field_type == QVariant.DateTime:
            return "DateTime"
        if field_type == QVariant.Date:
            return "Date"
        return str(field_type)

    @staticmethod
    def _coerce_value_for_field(field, value):
        if field is None:
            return value
        try:
            field_type = field.type()
        except Exception:
            field_type = None

        integer_types = {
            QVariant.Int,
            getattr(QVariant, "LongLong", QVariant.Int),
            getattr(QVariant, "UInt", QVariant.Int),
            getattr(QVariant, "ULongLong", QVariant.Int),
        }
        if field_type == QVariant.Bool:
            if isinstance(value, bool):
                return value
            text = str(value or "").strip().lower()
            if text in {"true", "1", "yes", "y"}:
                return True
            if text in {"false", "0", "no", "n"}:
                return False
            return value

        if field_type in integer_types:
            try:
                return int(str(value or "").strip())
            except Exception:
                return None

        if field_type == QVariant.DateTime:
            return value if isinstance(value, QDateTime) else value

        if field_type == QVariant.Date:
            return value if isinstance(value, QDate) else value

        return value

    @staticmethod
    def _layer_label(layer: Optional[QgsVectorLayer]) -> str:
        if not isinstance(layer, QgsVectorLayer):
            return "-"
        try:
            return str(layer.name() or "").strip() or "-"
        except Exception:
            return "-"

    @classmethod
    def open_for_module(cls, *, lang_manager, module_name: str, target_layer: Optional[QgsVectorLayer], parent=None) -> bool:
        if not isinstance(target_layer, QgsVectorLayer) or not target_layer.isValid():
            ModernMessageDialog.show_warning(
                lang_manager.translate(TranslationKeys.ERROR),
                lang_manager.translate(TranslationKeys.GEOSPATIAL_LAYER_MAPPER_TARGET_REQUIRED),
                parent=parent,
            )
            return False

        target_fields = cls._list_mappable_fields(target_layer)
        if not target_fields:
            ModernMessageDialog.show_warning(
                lang_manager.translate(TranslationKeys.ERROR),
                lang_manager.translate(TranslationKeys.GEOSPATIAL_LAYER_MAPPER_NO_TARGET_FIELDS),
                parent=parent,
            )
            return False

        dialog = cls(
            lang_manager=lang_manager,
            module_name=module_name,
            target_layer=target_layer,
            parent=parent,
        )
        return dialog.exec_() == QDialog.Accepted