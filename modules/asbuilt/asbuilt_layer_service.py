from __future__ import annotations

from functools import partial
from datetime import datetime
from typing import Optional

from qgis.PyQt.QtCore import QVariant
from qgis.core import QgsFeature, QgsVectorLayer

from ...Logs.python_fail_logger import PythonFailLogger
from ...languages.translation_keys import TranslationKeys
from ...utils.layers.module_layer_service_base import AttachableLayerServiceBase, FieldValueProblem, LayerEditTexts
from ...constants.module_names import Module


class AsBuiltLayerService(AttachableLayerServiceBase):
    MODULE = Module.ASBUILT
    LAYER_MISSING_KEY = TranslationKeys.ASBUILT_LAYER_MISSING
    LAYER_AMBIGUOUS_KEY = TranslationKeys.ASBUILT_LAYER_MISSING
    DRAW_START_FAILED_KEY = TranslationKeys.ASBUILT_DRAW_NEW_START_FAILED
    INVALID_LAYER_TEXT = "Invalid As-built layer"
    FIELDS_TEXTS = LayerEditTexts(
        start_failed="Could not start editing As-built layer to add external fields",
        change_failed="Could not add external As-built fields to layer",
        commit_failed="Could not commit new As-built layer fields",
        failed_event="asbuilt_layer_ensure_fields_failed",
        rollback_event="asbuilt_layer_ensure_fields_rollback_failed",
    )
    MISSING_ITEM_ID_TEXT = "Missing backend As-built id"
    FEATURE_NOT_FOUND_TEXT = "Selected As-built feature was not found"
    ATTACH_TEXTS = LayerEditTexts(
        start_failed="Could not start editing As-built layer",
        change_failed="Could not update selected As-built feature",
        commit_failed="Could not commit As-built layer changes",
        failed_event="asbuilt_attach_existing_save_failed",
        rollback_event="asbuilt_attach_existing_rollback_failed",
    )
    ATTACH_VERIFY_FAILED_TEXT = "Updated As-built feature could not be verified on the configured main layer"

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
    ID_FIELD_CANDIDATES = (FIELD_EXT_JOB_ID,)

    @classmethod
    def resolve_task_id_field_name(cls, layer: Optional[QgsVectorLayer]) -> Optional[str]:
        return cls._field_map(layer).get(cls.FIELD_EXT_JOB_ID.lower())

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
        value_problems: Optional[list[FieldValueProblem]] = None,
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
            cls._set_attr_if_present(feature, layer=layer, candidates=(field_name,), value=value, value_problems=value_problems)

    @classmethod
    def geometry_form_value_problems(cls, layer: Optional[QgsVectorLayer], values: Optional[dict]) -> dict[str, FieldValueProblem]:
        """The form values this layer's save would leave empty, by form key. Nothing is written or logged.

        Like the save above, each form key is the layer field name its value goes to.
        """
        problems: dict[str, FieldValueProblem] = {}
        try:
            for key, value in (values or {}).items():
                field_name = cls._resolve_first_field_name(layer, (key,))
                if value is None or not field_name:
                    continue
                _value, problem = cls.coerce_field_value(layer.fields().field(field_name), value)
                if problem is not None:
                    problems[key] = problem
        except RuntimeError:  # the layer was deleted while the form was open; its save fails on its own
            return {}
        return problems

    @classmethod
    def find_feature(cls, layer: Optional[QgsVectorLayer], *, item_id: str, item_name: str = ""):
        keys = (
            (cls.resolve_task_id_field_name(layer), item_id),
            (cls._resolve_first_field_name(layer, (cls.FIELD_EXT_JOB_NAME,)), item_name),
        )
        return cls._find_first_feature(layer, keys, log_extra={"item_id": str(item_id or "").strip()})

    @classmethod
    def _write_item_attributes(
        cls,
        feature: QgsFeature,
        *,
        layer: QgsVectorLayer,
        item_id: str,
        item: dict,
        username: str,
        value_problems: Optional[list[FieldValueProblem]],
    ) -> None:
        item_name = str(item.get("name") or item.get("title") or "").strip()
        item_type_name = str(((item.get("type") or {}).get("name") or "")).strip()
        item_status_id = cls.coerce_optional_int(((item.get("status") or {}).get("id") or ""))
        created_date = cls.parse_backend_datetime(item.get("createdAt")) or datetime.now()
        updated_date = cls.parse_backend_datetime(item.get("updatedAt")) or created_date

        set_attr = partial(cls._set_attr_if_present, feature, layer=layer, value_problems=value_problems)
        set_attr(candidates=(cls.FIELD_EXT_JOB_ID,), value=item_id)
        set_attr(candidates=(cls.FIELD_EXT_SYSTEM,), value=cls.EXT_SYSTEM_NAME)
        set_attr(candidates=(cls.FIELD_EXT_JOB_NAME,), value=item_name)
        set_attr(candidates=(cls.FIELD_EXT_JOB_TYPE,), value=item_type_name)
        set_attr(candidates=(cls.FIELD_EXT_JOB_STATE,), value=item_status_id)
        set_attr(candidates=(cls.FIELD_UPDATED_BY,), value=username)
        set_attr(candidates=(cls.FIELD_UPDATE_DATE,), value=updated_date)
        cls._apply_geometry_form_values(
            feature,
            layer=layer,
            values=item.get("_asbuilt_geometry_form"),
            item_payload=item,
            username=username,
            created_date=created_date,
            updated_date=updated_date,
            value_problems=value_problems,
        )
        cls._fill_added_fields_if_empty(
            feature,
            layer=layer,
            by_candidates=(cls.FIELD_ADDED_BY,),
            date_candidates=(cls.FIELD_ADDED_DATE,),
            username=username,
            created=created_date,
            item_id=item_id,
            value_problems=value_problems,
        )

    @classmethod
    def sync_status_from_task(cls, item_id: str, task: Optional[dict], *, lang_manager=None) -> bool:
        """Write the Kavitro status of an as-built onto its map feature (`ext_job_state`); True when it matches.

        Runs after a status change on the card. A layer the user is editing is left alone: committing
        would also save the user's own pending edits.
        """
        item_id_text = str(item_id or "").strip()
        status_id = cls.coerce_optional_int(((task or {}).get("status") or {}).get("id") or "")
        if not item_id_text or status_id is None:
            return False
        layer = cls.resolve_main_layer(lang_manager=lang_manager, dialogs=None)
        if not isinstance(layer, QgsVectorLayer) or not layer.isValid():
            return False
        extra = {"item_id": item_id_text, "layer": layer.name()}
        if layer.isEditable():
            PythonFailLogger.log("asbuilt_status_sync_skipped_layer_editable", module=cls.MODULE.value, extra=extra)
            return False
        field_name = cls._resolve_first_field_name(layer, (cls.FIELD_EXT_JOB_STATE,))
        feature = cls.find_feature(layer, item_id=item_id_text)
        if not field_name or feature is None:
            return False
        field_index = layer.fields().indexOf(field_name)
        if cls.coerce_optional_int(feature.attribute(field_index)) == status_id:
            return True

        started_edit = bool(layer.startEditing())
        if not started_edit:
            PythonFailLogger.log("asbuilt_status_sync_start_failed", module=cls.MODULE.value, extra=extra)
            return False
        try:
            if layer.changeAttributeValue(feature.id(), field_index, status_id) and layer.commitChanges():
                layer.triggerRepaint()
                return True
            errors = "; ".join(layer.commitErrors() or [])
            PythonFailLogger.log(
                "asbuilt_status_sync_failed", module=cls.MODULE.value, extra={**extra, "errors": errors},
            )
        except RuntimeError as exc:  # the layer was deleted meanwhile
            PythonFailLogger.log_exception(exc, module=cls.MODULE.value, event="asbuilt_status_sync_failed", extra=extra)
        cls._rollback_own_edit(layer, started_edit, event="asbuilt_status_sync_rollback_failed")
        return False
