from __future__ import annotations

from datetime import datetime
from typing import Optional

from qgis.PyQt.QtCore import QVariant, QDate, QDateTime
from qgis.core import (
    QgsFeature,
    QgsField,
    QgsVectorLayer,
)

from ...languages.translation_keys import TranslationKeys
from ...utils.layers.module_layer_service_base import AttachableLayerServiceBase
from ...utils.url_manager import Module
from ...Logs.python_fail_logger import PythonFailLogger


class AsBuiltLayerService(AttachableLayerServiceBase):
    MODULE = Module.ASBUILT
    LAYER_MISSING_KEY = TranslationKeys.ASBUILT_LAYER_MISSING
    LAYER_AMBIGUOUS_KEY = TranslationKeys.ASBUILT_LAYER_MISSING
    DRAW_START_FAILED_KEY = TranslationKeys.ASBUILT_DRAW_NEW_START_FAILED

    EXT_SYSTEM_NAME = "Kavitro"

    FIELD_EXT_JOB_ID = "ext_job_id"
    FIELD_EXT_SYSTEM = "ext_system"
    FIELD_EXT_JOB_NAME = "ext_job_name"
    FIELD_EXT_JOB_TYPE = "ext_job_type"
    FIELD_EXT_JOB_STATE = "ext_job_state"
    FIELD_ADDED_BY = "added_by"
    FIELD_ADDED_DATE = "added_date"
    FIELD_UPDATED_BY = "updated_by"
    FIELD_UPDATE_DATE = "update_date"

    FIELD_WORK_NUMBER = "Töö nr"
    FIELD_OBJECT = "Objekt"
    FIELD_SURVEY_DATE = "Mõõdistamise kpv"
    FIELD_SURVEYOR = "Mõõdistaja"
    FIELD_CONTACT = "Kontakt"
    FIELD_SURVEYOR_NOTES = "Mõõdistaja, märkused"
    FIELD_DRAWING = "Joonis"
    FIELD_SCALE = "Mõõtkava"
    FIELD_COORDINATE_SYSTEM = "Koordinaatsüsteem"
    FIELD_INPUT_USER = "Sisestaja"
    FIELD_INPUT_DATE = "Sisetus kpv"
    FIELD_MODIFIED_USER = "Muutja"
    FIELD_MODIFIED_DATE = "Muutmis kpv"
    FIELD_NETWORK_AREA = "Võrgu piirkond"
    FIELD_WATER = "Vesi"
    FIELD_SEWER = "Kanal"
    FIELD_RAINWATER = "Sadevesi"
    FIELD_ELECTRICITY = "Elekter ja tänavavalgustus"
    FIELD_GAS = "Gaas"
    FIELD_TELECOM = "Side"
    FIELD_HEIGHT_SYSTEM = "Kõrgussüsteem"

    CUSTOM_FIELDS = (
        (FIELD_EXT_JOB_ID, QVariant.String),
        (FIELD_EXT_SYSTEM, QVariant.String),
        (FIELD_EXT_JOB_NAME, QVariant.String),
        (FIELD_EXT_JOB_TYPE, QVariant.String),
        (FIELD_EXT_JOB_STATE, QVariant.Int),
        (FIELD_ADDED_BY, QVariant.String),
        (FIELD_ADDED_DATE, QVariant.DateTime),
        (FIELD_UPDATED_BY, QVariant.String),
        (FIELD_UPDATE_DATE, QVariant.DateTime),
    )

    @classmethod
    def resolve_task_id_field_name(cls, layer: Optional[QgsVectorLayer]) -> Optional[str]:
        return cls._field_map(layer).get(cls.FIELD_EXT_JOB_ID.lower())

    @classmethod
    def _ensure_custom_fields(cls, layer: Optional[QgsVectorLayer]) -> tuple[bool, str]:
        if not isinstance(layer, QgsVectorLayer) or not layer.isValid():
            return False, "Invalid As-built layer"

        existing = cls._field_map(layer)
        missing_fields = [QgsField(name, field_type) for name, field_type in cls.CUSTOM_FIELDS if name.lower() not in existing]
        if not missing_fields:
            return True, ""

        started_edit = False
        try:
            if not layer.isEditable():
                started_edit = bool(layer.startEditing())
                if not started_edit:
                    return False, "Could not start editing As-built layer to add external fields"

            for field in missing_fields:
                if not layer.addAttribute(field):
                    if started_edit:
                        layer.rollBack()
                    return False, f"Could not add field {field.name()} to As-built layer"

            layer.updateFields()
            if started_edit and not layer.commitChanges():
                errors = "; ".join(layer.commitErrors() or [])
                layer.rollBack()
                return False, errors or "Could not commit new As-built layer fields"
            return True, ""
        except Exception as exc:
            try:
                if started_edit and layer.isEditable():
                    layer.rollBack()
            except Exception:
                pass
            PythonFailLogger.log_exception(
                exc,
                module=Module.ASBUILT.value,
                event="asbuilt_layer_ensure_fields_failed",
            )
            return False, str(exc)

    @staticmethod
    def coerce_value_for_field(field, value):
        if field is None or value is None:
            return value
        try:
            field_type = field.type()
        except Exception:
            field_type = None

        if field_type in (QVariant.Int, QVariant.UInt, QVariant.LongLong, QVariant.ULongLong):
            try:
                return int(value)
            except Exception:
                return value

        if field_type == QVariant.Bool:
            if isinstance(value, bool):
                return value
            text = str(value or "").strip().lower()
            if text in {"1", "true", "t", "yes", "y", "jah"}:
                return True
            if text in {"0", "false", "f", "no", "n", "ei"}:
                return False
            return bool(value)

        if field_type == QVariant.Date:
            if isinstance(value, QDate):
                return value
            text = str(value or "").strip()
            parsed = QDate.fromString(text, "yyyy-MM-dd")
            return parsed if parsed.isValid() else value

        if field_type == QVariant.DateTime:
            if isinstance(value, QDateTime):
                return value
            parsed = value if isinstance(value, datetime) else AsBuiltLayerService.parse_backend_datetime(value)
            if isinstance(parsed, datetime):
                return QDateTime(parsed.year, parsed.month, parsed.day, parsed.hour, parsed.minute, parsed.second)
        return value

    @classmethod
    def _apply_geometry_form_values(
        cls,
        feature: QgsFeature,
        *,
        layer: QgsVectorLayer,
        values: Optional[dict],
        item_payload: dict,
        username: str,
        created_date: datetime,
        updated_date: datetime,
    ) -> None:
        form_values = values if isinstance(values, dict) else {}
        item_name = str(item_payload.get("name") or item_payload.get("title") or "").strip()
        work_number = str(
            form_values.get(cls.FIELD_WORK_NUMBER)
            or item_payload.get("number")
            or item_payload.get("workNumber")
            or item_payload.get("id")
            or ""
        ).strip()
        object_name = str(form_values.get(cls.FIELD_OBJECT) or item_name).strip()

        fields: dict[str, object] = {
            cls.FIELD_WORK_NUMBER: work_number,
            cls.FIELD_OBJECT: object_name,
            cls.FIELD_SURVEY_DATE: form_values.get(cls.FIELD_SURVEY_DATE),
            cls.FIELD_SURVEYOR: form_values.get(cls.FIELD_SURVEYOR),
            cls.FIELD_CONTACT: form_values.get(cls.FIELD_CONTACT),
            cls.FIELD_SURVEYOR_NOTES: form_values.get(cls.FIELD_SURVEYOR_NOTES),
            cls.FIELD_DRAWING: form_values.get(cls.FIELD_DRAWING) or "TJ",
            cls.FIELD_SCALE: form_values.get(cls.FIELD_SCALE) or "500",
            cls.FIELD_COORDINATE_SYSTEM: form_values.get(cls.FIELD_COORDINATE_SYSTEM) or "L-EST97",
            cls.FIELD_HEIGHT_SYSTEM: form_values.get(cls.FIELD_HEIGHT_SYSTEM) or "EH2000",
            cls.FIELD_INPUT_USER: form_values.get(cls.FIELD_INPUT_USER) or username,
            cls.FIELD_INPUT_DATE: form_values.get(cls.FIELD_INPUT_DATE) or created_date,
            cls.FIELD_MODIFIED_USER: form_values.get(cls.FIELD_MODIFIED_USER) or username,
            cls.FIELD_MODIFIED_DATE: form_values.get(cls.FIELD_MODIFIED_DATE) or updated_date,
            cls.FIELD_WATER: form_values.get(cls.FIELD_WATER, False),
            cls.FIELD_SEWER: form_values.get(cls.FIELD_SEWER, False),
            cls.FIELD_RAINWATER: form_values.get(cls.FIELD_RAINWATER, False),
            cls.FIELD_ELECTRICITY: form_values.get(cls.FIELD_ELECTRICITY, False),
            cls.FIELD_GAS: form_values.get(cls.FIELD_GAS, False),
            cls.FIELD_TELECOM: form_values.get(cls.FIELD_TELECOM, False),
        }

        for field_name, value in fields.items():
            if value is None:
                continue
            cls._set_attr_if_present(feature, layer=layer, candidates=(field_name,), value=value)

    @classmethod
    def find_feature(cls, layer: Optional[QgsVectorLayer], *, item_id: str, item_name: str = ""):
        if not isinstance(layer, QgsVectorLayer) or not layer.isValid():
            return None

        id_field = cls.resolve_task_id_field_name(layer)
        name_field = cls._resolve_first_field_name(layer, (cls.FIELD_EXT_JOB_NAME,))
        item_id_text = str(item_id or "").strip()
        item_name_text = str(item_name or "").strip()

        try:
            for feature in layer.getFeatures():
                if id_field and item_id_text:
                    current_id = str(feature.attribute(id_field) or "").strip()
                    if current_id == item_id_text:
                        return feature
                if name_field and item_name_text:
                    current_name = str(feature.attribute(name_field) or "").strip()
                    if current_name == item_name_text:
                        return feature
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module=Module.ASBUILT.value,
                event="asbuilt_layer_find_feature_failed",
                extra={"item_id": item_id_text},
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
            return False, "Invalid As-built layer"

        ok_fields, field_error = cls._ensure_custom_fields(layer)
        if not ok_fields:
            return False, field_error

        item_payload = item_data if isinstance(item_data, dict) else {}
        item_id_text = str(item_id or "").strip()
        if not item_id_text:
            return False, "Missing backend As-built id"

        feature = cls._feature_by_id(layer, int(feature_id))

        if feature is None:
            return False, "Selected As-built feature was not found"

        item_name = str(item_payload.get("name") or item_payload.get("title") or "").strip()
        item_type_name = str(((item_payload.get("type") or {}).get("name") or "")).strip()
        item_status_id = cls.coerce_optional_int(((item_payload.get("status") or {}).get("id") or ""))
        username = cls.current_username()
        created_date = cls.parse_backend_datetime(item_payload.get("createdAt")) or datetime.now()
        updated_date = cls.parse_backend_datetime(item_payload.get("updatedAt")) or created_date

        cls._set_attr_if_present(feature, layer=layer, candidates=(cls.FIELD_EXT_JOB_ID,), value=item_id_text)
        cls._set_attr_if_present(feature, layer=layer, candidates=(cls.FIELD_EXT_SYSTEM,), value=cls.EXT_SYSTEM_NAME)
        cls._set_attr_if_present(feature, layer=layer, candidates=(cls.FIELD_EXT_JOB_NAME,), value=item_name)
        cls._set_attr_if_present(feature, layer=layer, candidates=(cls.FIELD_EXT_JOB_TYPE,), value=item_type_name)
        cls._set_attr_if_present(feature, layer=layer, candidates=(cls.FIELD_EXT_JOB_STATE,), value=item_status_id)
        cls._set_attr_if_present(feature, layer=layer, candidates=(cls.FIELD_UPDATED_BY,), value=username)
        cls._set_attr_if_present(feature, layer=layer, candidates=(cls.FIELD_UPDATE_DATE,), value=updated_date)
        cls._apply_geometry_form_values(
            feature,
            layer=layer,
            values=item_payload.get("_asbuilt_geometry_form"),
            item_payload=item_payload,
            username=username,
            created_date=created_date,
            updated_date=updated_date,
        )

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
                    return False, "Could not start editing As-built layer"

            if not layer.updateFeature(feature):
                if started_edit:
                    layer.rollBack()
                return False, "Could not update selected As-built feature"

            if started_edit and not layer.commitChanges():
                errors = "; ".join(layer.commitErrors() or [])
                layer.rollBack()
                return False, errors or "Could not commit As-built layer changes"

            layer.triggerRepaint()
            verified_feature = cls.find_feature(layer, item_id=item_id_text, item_name=item_name)
            if verified_feature is None or int(verified_feature.id()) != int(feature_id):
                return False, "Updated As-built feature could not be verified on the configured main layer"
            return True, cls._layer_target_label(layer)
        except Exception as exc:
            try:
                if started_edit and layer.isEditable():
                    layer.rollBack()
            except Exception:
                pass
            PythonFailLogger.log_exception(
                exc,
                module=Module.ASBUILT.value,
                event="asbuilt_attach_existing_save_failed",
                extra={"item_id": item_id_text, "feature_id": int(feature_id)},
            )
            return False, str(exc)
