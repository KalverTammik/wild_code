from __future__ import annotations

from functools import partial
from datetime import datetime
from typing import Optional

from qgis.PyQt.QtCore import QVariant
from qgis.core import (
    QgsFeature,
    QgsGeometry,
    QgsVectorLayer,
    QgsWkbTypes,
)

from ...languages.translation_keys import TranslationKeys
from ...utils.layers.module_layer_service_base import AttachableLayerServiceBase, FieldValueProblem, LayerEditTexts
from ...constants.module_names import Module
from ...Logs.python_fail_logger import PythonFailLogger


class ProjectsLayerService(AttachableLayerServiceBase):
    MODULE = Module.PROJECT
    LAYER_MISSING_KEY = TranslationKeys.PROJECT_LAYER_MISSING
    LAYER_AMBIGUOUS_KEY = TranslationKeys.PROJECT_LAYER_MISSING
    DRAW_START_FAILED_KEY = TranslationKeys.PROJECT_DRAW_NEW_START_FAILED
    REQUIRED_GEOMETRY = QgsWkbTypes.PolygonGeometry
    LAYER_INVALID_GEOMETRY_KEY = TranslationKeys.PROJECT_LAYER_INVALID_GEOMETRY
    INVALID_LAYER_TEXT = "Invalid Projects layer"
    FIELDS_TEXTS = LayerEditTexts(
        start_failed="Could not start editing Projects layer to add external fields",
        change_failed="Could not add external project fields to layer",
        commit_failed="Could not commit new Projects layer fields",
        failed_event="project_layer_ensure_fields_failed",
        rollback_event="project_layer_ensure_fields_rollback_failed",
    )
    MISSING_ITEM_ID_TEXT = "Missing backend project id"
    FEATURE_NOT_FOUND_TEXT = "Selected project area feature was not found"
    ATTACH_TEXTS = LayerEditTexts(
        start_failed="Could not start editing Projects layer",
        change_failed="Could not update selected Projects feature",
        commit_failed="Could not commit Projects layer changes",
        failed_event="project_attach_existing_save_failed",
        rollback_event="project_attach_rollback_failed",
    )
    ATTACH_VERIFY_FAILED_TEXT = "Updated project area feature could not be verified on the configured main layer"

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
    ID_FIELD_CANDIDATES = (FIELD_EXTERNAL_ID,)

    AREA_REPLACE = "replace"
    AREA_ADD_PART = "add_part"

    @classmethod
    def item_feature_ids(cls, layer: Optional[QgsVectorLayer], item_id: str) -> list[int]:
        """Ids of every feature carrying this project's Kavitro id."""
        field_name = cls._resolve_first_field_name(layer, (cls.FIELD_EXTERNAL_ID,))
        item_id_text = str(item_id or "").strip()
        if not field_name or not item_id_text:
            return []
        try:
            return [
                int(feature.id())
                for feature in layer.getFeatures()
                if str(feature.attribute(field_name) or "").strip() == item_id_text
            ]
        except RuntimeError:  # the layer was deleted
            return []

    @staticmethod
    def allows_multi_part(layer: Optional[QgsVectorLayer]) -> bool:
        try:
            return bool(QgsWkbTypes.isMultiType(layer.wkbType()))
        except (AttributeError, RuntimeError):
            return False

    @classmethod
    def fold_existing_areas(
        cls, layer: QgsVectorLayer, *, keep_feature_id: int, item_id: str, mode: str
    ) -> tuple[bool, str]:
        """Leave the project one area: the drawn feature replaces the older ones or takes them in as parts.

        Works in the open edit session; the draw flow commits it, or rolls all of it back on failure.
        """
        keep_id = int(keep_feature_id)
        others = [feature_id for feature_id in cls.item_feature_ids(layer, item_id) if feature_id != keep_id]
        if not others or mode not in (cls.AREA_REPLACE, cls.AREA_ADD_PART):
            return True, ""
        if mode == cls.AREA_ADD_PART:
            if not cls.allows_multi_part(layer):
                return False, "The Projects layer does not allow multi-part features"
            kept = cls._feature_by_id(layer, keep_id)
            if kept is None:
                return False, cls.FEATURE_NOT_FOUND_TEXT
            combined = QgsGeometry(kept.geometry())
            for feature_id in others:
                older = cls._feature_by_id(layer, feature_id)
                if older is not None and not older.geometry().isEmpty():
                    combined = combined.combine(older.geometry())
            if combined.isNull() or combined.isEmpty():
                return False, "Could not join the drawn part to the project area"
            combined.convertToMultiType()
            if not layer.changeGeometry(keep_id, combined):
                return False, "Could not join the drawn part to the project area"
        for feature_id in others:
            if not layer.deleteFeature(feature_id):
                return False, "Could not remove the older project area"
        PythonFailLogger.log(
            "project_area_folded",
            module=cls.MODULE.value,
            extra={"item_id": str(item_id or ""), "mode": mode, "removed": len(others)},
        )
        return True, ""

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
    def _item_name(item: dict) -> str:
        return str(item.get("name") or item.get("title") or "").strip()

    @staticmethod
    def _item_number(item: dict) -> str:
        return str(item.get("projectNumber") or item.get("number") or "").strip()

    @classmethod
    def find_feature(cls, layer: Optional[QgsVectorLayer], *, item_id: str, item_number: str = "", item_name: str = ""):
        keys = (
            (cls._resolve_first_field_name(layer, (cls.FIELD_EXTERNAL_ID,)), item_id),
            (cls._resolve_first_field_name(layer, (cls.FIELD_EXTERNAL_NUMBER,)), item_number),
            (cls._resolve_first_field_name(layer, (cls.FIELD_EXTERNAL_NAME,)), item_name),
        )
        log_extra = {"item_id": str(item_id or "").strip(), "item_number": str(item_number or "").strip()}
        return cls._find_first_feature(layer, keys, log_extra=log_extra)

    @classmethod
    def _write_project_attributes(
        cls,
        feature: QgsFeature,
        *,
        layer: QgsVectorLayer,
        item_id: str,
        item: dict,
        username: str,
        updated_date: datetime,
        value_problems: Optional[list[FieldValueProblem]],
    ) -> None:
        set_attr = partial(cls._set_attr_if_present, feature, layer=layer, value_problems=value_problems)
        set_attr(candidates=(cls.FIELD_EXTERNAL_ID,), value=item_id)
        set_attr(candidates=(cls.FIELD_EXTERNAL_SYSTEM,), value=cls.EXT_SYSTEM_NAME)
        set_attr(candidates=(cls.FIELD_EXTERNAL_NAME,), value=cls._item_name(item))
        set_attr(candidates=(cls.FIELD_EXTERNAL_NUMBER,), value=cls._item_number(item))
        set_attr(candidates=(cls.FIELD_DETAILED,), value=cls.detailed_from_project(item))
        set_attr(candidates=(cls.FIELD_ACTIVE,), value=cls.active_from_project(item))
        set_attr(candidates=(cls.FIELD_UPDATED_BY,), value=username)
        set_attr(candidates=(cls.FIELD_UPDATE_DATE,), value=updated_date)

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
        created_date = cls.parse_backend_datetime(item.get("createdAt")) or datetime.now()
        updated_date = cls.parse_backend_datetime(item.get("updatedAt")) or created_date
        cls._write_project_attributes(
            feature,
            layer=layer,
            item_id=item_id,
            item=item,
            username=username,
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
    def upsert_generated_area_feature(
        cls,
        *,
        layer: QgsVectorLayer,
        preview_layer: QgsVectorLayer,
        item_id: str,
        item_data: Optional[dict] = None,
        value_problems: Optional[list[FieldValueProblem]] = None,
    ) -> tuple[bool, str]:
        if not isinstance(layer, QgsVectorLayer) or not layer.isValid():
            return False, cls.INVALID_LAYER_TEXT
        if not isinstance(preview_layer, QgsVectorLayer) or not preview_layer.isValid():
            return False, "Invalid project preview layer"

        ok_fields, field_error = cls._ensure_custom_fields(layer)
        if not ok_fields:
            return False, field_error

        item_payload = item_data if isinstance(item_data, dict) else {}
        item_id_text = str(item_id or "").strip()
        if not item_id_text:
            return False, cls.MISSING_ITEM_ID_TEXT

        item_name = cls._item_name(item_payload)
        item_number = cls._item_number(item_payload)
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

        cls._write_project_attributes(
            feature,
            layer=layer,
            item_id=item_id_text,
            item=item_payload,
            username=username,
            updated_date=updated_date,
            value_problems=value_problems,
        )
        if existing_feature is None:
            set_attr = partial(cls._set_attr_if_present, feature, layer=layer, value_problems=value_problems)
            set_attr(candidates=(cls.FIELD_ADDED_BY,), value=username)
            set_attr(candidates=(cls.FIELD_ADDED_DATE,), value=created_date)

        def check_saved(saved_id: Optional[int]) -> tuple[bool, str]:
            if not cls._verify_attached(layer, feature_id=saved_id, item_id=item_id_text, item=item_payload):
                return False, "Saved project area feature could not be verified on the configured main layer"
            return True, cls._layer_target_label(layer)

        adding = existing_feature is None
        texts = LayerEditTexts(
            start_failed="Could not start editing Projects layer",
            change_failed="Could not add project area feature" if adding else "Could not update project area feature",
            commit_failed="Could not commit Projects layer changes",
            failed_event="project_generated_area_save_failed",
            rollback_event="project_generated_area_rollback_failed",
        )
        return cls._write_feature(
            layer, feature, add=adding, texts=texts, log_extra={"item_id": item_id_text}, check_saved=check_saved
        )
