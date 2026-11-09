from __future__ import annotations

import json
from datetime import datetime
from typing import Optional

from qgis.PyQt.QtCore import QVariant, QDateTime
from qgis.core import (
    QgsFeature,
    QgsField,
    QgsVectorLayer,
    QgsWkbTypes,
)

from ...languages.translation_keys import TranslationKeys
from ...utils.layers.module_layer_service_base import AttachableLayerServiceBase
from ...utils.url_manager import Module
from ...Logs.python_fail_logger import PythonFailLogger


class ProjectsLayerService(AttachableLayerServiceBase):
    MODULE = Module.PROJECT
    LAYER_MISSING_KEY = TranslationKeys.PROJECT_LAYER_MISSING
    LAYER_AMBIGUOUS_KEY = TranslationKeys.PROJECT_LAYER_MISSING
    DRAW_START_FAILED_KEY = TranslationKeys.PROJECT_DRAW_NEW_START_FAILED
    REQUIRED_GEOMETRY = QgsWkbTypes.PolygonGeometry
    LAYER_INVALID_GEOMETRY_KEY = TranslationKeys.PROJECT_LAYER_INVALID_GEOMETRY

    EXT_SYSTEM_NAME = "Kavitro"

    FIELD_EXTERNAL_ID = "ext_project_id"
    FIELD_EXTERNAL_SYSTEM = "ext_system"
    FIELD_EXTERNAL_NAME = "ext_project_name"
    FIELD_EXTERNAL_NUMBER = "ext_project_number"
    FIELD_DETAILED = "detailed"
    FIELD_ACTIVE = "active"
    FIELD_ADDED_BY = "added_by"
    FIELD_ADDED_DATE = "added_date"
    FIELD_UPDATED_BY = "updated_by"
    FIELD_UPDATE_DATE = "update_date"

    CUSTOM_FIELDS = (
        (FIELD_EXTERNAL_ID, QVariant.String),
        (FIELD_EXTERNAL_SYSTEM, QVariant.String),
        (FIELD_EXTERNAL_NAME, QVariant.String),
        (FIELD_EXTERNAL_NUMBER, QVariant.String),
        (FIELD_DETAILED, QVariant.String),
        (FIELD_ACTIVE, QVariant.Bool),
        (FIELD_ADDED_BY, QVariant.String),
        (FIELD_ADDED_DATE, QVariant.DateTime),
        (FIELD_UPDATED_BY, QVariant.String),
        (FIELD_UPDATE_DATE, QVariant.DateTime),
    )

    @classmethod
    def _ensure_custom_fields(cls, layer: Optional[QgsVectorLayer]) -> tuple[bool, str]:
        if not isinstance(layer, QgsVectorLayer) or not layer.isValid():
            return False, "Invalid Projects layer"

        existing = cls._field_map(layer)
        missing_fields = [QgsField(name, field_type) for name, field_type in cls.CUSTOM_FIELDS if name.lower() not in existing]
        if not missing_fields:
            return True, ""

        started_edit = False
        try:
            if not layer.isEditable():
                started_edit = bool(layer.startEditing())
                if not started_edit:
                    return False, "Could not start editing Projects layer to add external fields"

            provider = layer.dataProvider()
            if provider is None or not provider.addAttributes(missing_fields):
                if started_edit:
                    layer.rollBack()
                return False, "Could not add external project fields to layer"

            layer.updateFields()
            if started_edit and not layer.commitChanges():
                errors = "; ".join(layer.commitErrors() or [])
                layer.rollBack()
                return False, errors or "Could not commit new Projects layer fields"
            return True, ""
        except Exception as exc:
            try:
                if started_edit and layer.isEditable():
                    layer.rollBack()
            except Exception:
                pass
            PythonFailLogger.log_exception(
                exc,
                module=Module.PROJECT.value,
                event="project_layer_ensure_fields_failed",
            )
            return False, str(exc)

    @staticmethod
    def active_from_project(project: Optional[dict]):
        if not isinstance(project, dict):
            return None

        raw_active = project.get("active")
        if isinstance(raw_active, bool):
            return raw_active
        if raw_active not in (None, ""):
            text = str(raw_active).strip().lower()
            if text in ("true", "1", "yes", "y"):
                return True
            if text in ("false", "0", "no", "n"):
                return False

        status_payload = project.get("status") or {}
        if isinstance(status_payload, dict):
            status_type = str(status_payload.get("type") or "").strip().upper()
            if status_type == "CLOSED":
                return False
            if status_type == "OPEN":
                return True
        return None

    @staticmethod
    def detailed_from_project(project: Optional[dict]):
        if not isinstance(project, dict):
            return None

        detailed = project.get("detailed")
        if detailed not in (None, ""):
            return detailed

        status_payload = project.get("status") or {}
        if not isinstance(status_payload, dict):
            status_payload = {}
        return {
            "status": {
                "id": status_payload.get("id"),
                "name": status_payload.get("name"),
                "type": status_payload.get("type"),
            },
            "updatedAt": project.get("updatedAt"),
        }

    @staticmethod
    def coerce_value_for_field(field, value):
        if field is None or value is None:
            return value
        try:
            field_type = field.type()
        except Exception:
            field_type = None

        if field_type == QVariant.Bool:
            if isinstance(value, bool):
                return value
            text = str(value or "").strip().lower()
            if text in ("true", "1", "yes", "y"):
                return True
            if text in ("false", "0", "no", "n"):
                return False
            return value

        if field_type == QVariant.String and isinstance(value, (dict, list)):
            try:
                return json.dumps(value, ensure_ascii=False)
            except (TypeError, ValueError):
                return str(value)

        if field_type == QVariant.DateTime:
            if isinstance(value, QDateTime):
                return value
            parsed = value if isinstance(value, datetime) else ProjectsLayerService.parse_backend_datetime(value)
            if isinstance(parsed, datetime):
                return QDateTime(parsed.year, parsed.month, parsed.day, parsed.hour, parsed.minute, parsed.second)
        return value

    @classmethod
    def find_feature(cls, layer: Optional[QgsVectorLayer], *, item_id: str, item_number: str = "", item_name: str = ""):
        if not isinstance(layer, QgsVectorLayer) or not layer.isValid():
            return None

        id_field = cls._resolve_first_field_name(layer, (cls.FIELD_EXTERNAL_ID,))
        number_field = cls._resolve_first_field_name(layer, (cls.FIELD_EXTERNAL_NUMBER,))
        name_field = cls._resolve_first_field_name(layer, (cls.FIELD_EXTERNAL_NAME,))
        item_id_text = str(item_id or "").strip()
        item_number_text = str(item_number or "").strip()
        item_name_text = str(item_name or "").strip()

        try:
            for feature in layer.getFeatures():
                if id_field and item_id_text:
                    current_id = str(feature.attribute(id_field) or "").strip()
                    if current_id == item_id_text:
                        return feature
                if number_field and item_number_text:
                    current_number = str(feature.attribute(number_field) or "").strip()
                    if current_number == item_number_text:
                        return feature
                if name_field and item_name_text:
                    current_name = str(feature.attribute(name_field) or "").strip()
                    if current_name == item_name_text:
                        return feature
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module=Module.PROJECT.value,
                event="project_layer_find_feature_failed",
                extra={"item_id": item_id_text, "item_number": item_number_text},
            )
        return None

    @classmethod
    def attach_backend_item_to_feature(
        cls,
        *,
        layer: QgsVectorLayer,
        feature_id: int,
        item_id: str,
        item_data: Optional[dict] = None,
    ) -> tuple[bool, str]:
        if not isinstance(layer, QgsVectorLayer) or not layer.isValid():
            return False, "Invalid Projects layer"

        ok_fields, field_error = cls._ensure_custom_fields(layer)
        if not ok_fields:
            return False, field_error

        item_payload = item_data if isinstance(item_data, dict) else {}
        item_id_text = str(item_id or "").strip()
        if not item_id_text:
            return False, "Missing backend project id"

        try:
            feature = cls._feature_by_id(layer, int(feature_id))
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module=Module.PROJECT.value,
                event="project_attach_feature_load_failed",
                extra={"feature_id": int(feature_id)},
            )
            feature = None

        if feature is None:
            return False, "Selected project area feature was not found"

        item_name = str(item_payload.get("name") or item_payload.get("title") or "").strip()
        item_number = str(item_payload.get("projectNumber") or item_payload.get("number") or "").strip()
        username = cls.current_username()
        created_date = cls.parse_backend_datetime(item_payload.get("createdAt")) or datetime.now()
        updated_date = cls.parse_backend_datetime(item_payload.get("updatedAt")) or created_date

        cls._set_attr_if_present(feature, layer=layer, candidates=(cls.FIELD_EXTERNAL_ID,), value=item_id_text)
        cls._set_attr_if_present(feature, layer=layer, candidates=(cls.FIELD_EXTERNAL_SYSTEM,), value=cls.EXT_SYSTEM_NAME)
        cls._set_attr_if_present(feature, layer=layer, candidates=(cls.FIELD_EXTERNAL_NAME,), value=item_name)
        cls._set_attr_if_present(feature, layer=layer, candidates=(cls.FIELD_EXTERNAL_NUMBER,), value=item_number)
        cls._set_attr_if_present(feature, layer=layer, candidates=(cls.FIELD_DETAILED,), value=cls.detailed_from_project(item_payload))
        cls._set_attr_if_present(feature, layer=layer, candidates=(cls.FIELD_ACTIVE,), value=cls.active_from_project(item_payload))
        cls._set_attr_if_present(feature, layer=layer, candidates=(cls.FIELD_UPDATED_BY,), value=username)
        cls._set_attr_if_present(feature, layer=layer, candidates=(cls.FIELD_UPDATE_DATE,), value=updated_date)

        added_by_field = cls._resolve_first_field_name(layer, (cls.FIELD_ADDED_BY,))
        added_date_field = cls._resolve_first_field_name(layer, (cls.FIELD_ADDED_DATE,))
        try:
            if added_by_field and not str(feature.attribute(added_by_field) or "").strip():
                cls._set_attr_if_present(feature, layer=layer, candidates=(cls.FIELD_ADDED_BY,), value=username)
            if added_date_field and not feature.attribute(added_date_field):
                cls._set_attr_if_present(feature, layer=layer, candidates=(cls.FIELD_ADDED_DATE,), value=created_date)
        except Exception:
            pass

        started_edit = False
        try:
            if not layer.isEditable():
                started_edit = bool(layer.startEditing())
                if not started_edit:
                    return False, "Could not start editing Projects layer"

            if not layer.updateFeature(feature):
                if started_edit:
                    layer.rollBack()
                return False, "Could not update selected Projects feature"

            if started_edit and not layer.commitChanges():
                errors = "; ".join(layer.commitErrors() or [])
                layer.rollBack()
                return False, errors or "Could not commit Projects layer changes"

            cls._refresh_saved_layer(layer)
            verified_feature = cls.find_feature(layer, item_id=item_id_text, item_number=item_number, item_name=item_name)
            if verified_feature is None:
                return False, "Updated project area feature could not be verified on the configured main layer"
            return True, cls._layer_target_label(layer)
        except Exception as exc:
            try:
                if started_edit and layer.isEditable():
                    layer.rollBack()
            except Exception:
                pass
            PythonFailLogger.log_exception(
                exc,
                module=Module.PROJECT.value,
                event="project_attach_existing_save_failed",
                extra={"item_id": item_id_text, "feature_id": int(feature_id)},
            )
            return False, str(exc)

    @classmethod
    def upsert_generated_area_feature(
        cls,
        *,
        layer: QgsVectorLayer,
        preview_layer: QgsVectorLayer,
        item_id: str,
        item_data: Optional[dict] = None,
    ) -> tuple[bool, str]:
        if not isinstance(layer, QgsVectorLayer) or not layer.isValid():
            return False, "Invalid Projects layer"
        if not isinstance(preview_layer, QgsVectorLayer) or not preview_layer.isValid():
            return False, "Invalid project preview layer"

        ok_fields, field_error = cls._ensure_custom_fields(layer)
        if not ok_fields:
            return False, field_error

        item_payload = item_data if isinstance(item_data, dict) else {}
        item_id_text = str(item_id or "").strip()
        if not item_id_text:
            return False, "Missing backend project id"

        item_name = str(item_payload.get("name") or item_payload.get("title") or "").strip()
        item_number = str(item_payload.get("projectNumber") or item_payload.get("number") or "").strip()
        created_date = cls.parse_backend_datetime(item_payload.get("createdAt")) or datetime.now()
        updated_date = cls.parse_backend_datetime(item_payload.get("updatedAt")) or created_date
        username = cls.current_username()

        try:
            preview_feature = next(preview_layer.getFeatures(), None)
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module=Module.PROJECT.value,
                event="project_preview_feature_read_failed",
                extra={"item_id": item_id_text},
            )
            preview_feature = None

        if preview_feature is None:
            return False, "Project preview layer has no geometry"

        geometry = preview_feature.geometry()
        if geometry is None or geometry.isEmpty():
            return False, "Project preview geometry is empty"

        target_geometry = cls._geometry_in_layer_crs(
            geometry,
            source_layer=preview_layer,
            target_layer=layer,
        )

        existing_feature = cls.find_feature(
            layer,
            item_id=item_id_text,
            item_number=item_number,
            item_name=item_name,
        )
        feature = QgsFeature(existing_feature) if existing_feature is not None else QgsFeature(layer.fields())
        feature.setGeometry(target_geometry)

        cls._set_attr_if_present(feature, layer=layer, candidates=(cls.FIELD_EXTERNAL_ID,), value=item_id_text)
        cls._set_attr_if_present(feature, layer=layer, candidates=(cls.FIELD_EXTERNAL_SYSTEM,), value=cls.EXT_SYSTEM_NAME)
        cls._set_attr_if_present(feature, layer=layer, candidates=(cls.FIELD_EXTERNAL_NAME,), value=item_name)
        cls._set_attr_if_present(feature, layer=layer, candidates=(cls.FIELD_EXTERNAL_NUMBER,), value=item_number)
        cls._set_attr_if_present(feature, layer=layer, candidates=(cls.FIELD_DETAILED,), value=cls.detailed_from_project(item_payload))
        cls._set_attr_if_present(feature, layer=layer, candidates=(cls.FIELD_ACTIVE,), value=cls.active_from_project(item_payload))
        cls._set_attr_if_present(feature, layer=layer, candidates=(cls.FIELD_UPDATED_BY,), value=username)
        cls._set_attr_if_present(feature, layer=layer, candidates=(cls.FIELD_UPDATE_DATE,), value=updated_date)

        if existing_feature is None:
            cls._set_attr_if_present(feature, layer=layer, candidates=(cls.FIELD_ADDED_BY,), value=username)
            cls._set_attr_if_present(feature, layer=layer, candidates=(cls.FIELD_ADDED_DATE,), value=created_date)

        started_edit = False
        try:
            if not layer.isEditable():
                started_edit = bool(layer.startEditing())
                if not started_edit:
                    return False, "Could not start editing Projects layer"

            if existing_feature is not None:
                if not layer.updateFeature(feature):
                    if started_edit:
                        layer.rollBack()
                    return False, "Could not update project area feature"
            else:
                if not layer.addFeature(feature):
                    if started_edit:
                        layer.rollBack()
                    return False, "Could not add project area feature"

            if started_edit and not layer.commitChanges():
                errors = "; ".join(layer.commitErrors() or [])
                layer.rollBack()
                return False, errors or "Could not commit Projects layer changes"

            cls._refresh_saved_layer(layer)
            verified_feature = cls.find_feature(
                layer,
                item_id=item_id_text,
                item_number=item_number,
                item_name=item_name,
            )
            if verified_feature is None:
                return False, "Saved project area feature could not be verified on the configured main layer"
            return True, cls._layer_target_label(layer)
        except Exception as exc:
            try:
                if started_edit and layer.isEditable():
                    layer.rollBack()
            except Exception:
                pass
            PythonFailLogger.log_exception(
                exc,
                module=Module.PROJECT.value,
                event="project_generated_area_save_failed",
                extra={"item_id": item_id_text},
            )
            return False, str(exc)
