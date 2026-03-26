from __future__ import annotations

from datetime import datetime
from typing import Optional

from qgis.PyQt.QtCore import QVariant, QDateTime
from qgis.core import (
    QgsCoordinateTransform,
    QgsFeature,
    QgsFeatureRequest,
    QgsField,
    QgsGeometry,
    QgsMapLayer,
    QgsPointXY,
    QgsProject,
    QgsRectangle,
    QgsVectorLayer,
    QgsWkbTypes,
)
from qgis.utils import iface

from ...constants.settings_keys import SettingsService
from ...languages.language_manager import LanguageManager
from ...languages.translation_keys import TranslationKeys
from ...utils.MapTools.MapHelpers import MapHelpers
from ...utils.SessionManager import SessionManager
from ...utils.messagesHelper import ModernMessageDialog
from ...utils.url_manager import Module
from ...Logs.python_fail_logger import PythonFailLogger


class AsBuiltLayerService:
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

    @staticmethod
    def _configured_layers(identifier: str) -> list[QgsMapLayer]:
        cleaned = str(identifier or "").strip()
        if not cleaned:
            return []

        direct = MapHelpers.find_layer_by_id(cleaned)
        if direct is not None:
            return [direct]

        project = QgsProject.instance()
        if project is None:
            return []

        target = cleaned.lower()
        matches: list[QgsMapLayer] = []
        for layer in project.mapLayers().values():
            try:
                candidate = str(layer.name() or "").strip()
            except Exception:
                continue
            if candidate and candidate.lower() == target:
                matches.append(layer)
        return matches

    @staticmethod
    def _layer_target_label(layer: Optional[QgsMapLayer]) -> str:
        if layer is None:
            return ""
        try:
            return str(layer.name() or "").strip()
        except Exception:
            return ""

    @classmethod
    def resolve_main_layer(cls, *, lang_manager=None, silent: bool = False) -> Optional[QgsVectorLayer]:
        lang = lang_manager or LanguageManager()
        identifier = SettingsService().module_main_layer_name(Module.ASBUILT.value) or ""
        matches = cls._configured_layers(identifier)
        if len(matches) > 1:
            if not silent:
                ModernMessageDialog.show_warning(
                    lang.translate(TranslationKeys.ERROR),
                    lang.translate(TranslationKeys.ASBUILT_LAYER_MISSING),
                )
            return None

        layer = matches[0] if matches else None
        if not isinstance(layer, QgsVectorLayer) or not layer.isValid():
            if not silent:
                ModernMessageDialog.show_warning(
                    lang.translate(TranslationKeys.ERROR),
                    lang.translate(TranslationKeys.ASBUILT_LAYER_MISSING),
                )
            return None

        try:
            if str(identifier or "").strip() != str(layer.id() or "").strip():
                SettingsService().module_main_layer_name(Module.ASBUILT.value, value=layer.id())
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module=Module.ASBUILT.value,
                event="asbuilt_layer_setting_id_migrate_failed",
                extra={"identifier": str(identifier or "")},
            )

        return layer

    @staticmethod
    def _field_map(layer: Optional[QgsVectorLayer]) -> dict[str, str]:
        if not isinstance(layer, QgsVectorLayer) or not layer.isValid():
            return {}
        try:
            return {field.name().lower(): field.name() for field in layer.fields()}
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module=Module.ASBUILT.value,
                event="asbuilt_layer_field_map_failed",
            )
            return {}

    @classmethod
    def resolve_task_id_field_name(cls, layer: Optional[QgsVectorLayer]) -> Optional[str]:
        return cls._field_map(layer).get(cls.FIELD_EXT_JOB_ID.lower())

    @classmethod
    def _resolve_first_field_name(cls, layer: Optional[QgsVectorLayer], candidates: tuple[str, ...]) -> Optional[str]:
        field_map = cls._field_map(layer)
        for candidate in candidates:
            actual = field_map.get(str(candidate).lower())
            if actual:
                return actual
        return None

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

    @classmethod
    def prepare_layer_for_draw(cls, *, lang_manager=None, silent: bool = False) -> tuple[Optional[QgsVectorLayer], str]:
        layer = cls.resolve_main_layer(lang_manager=lang_manager, silent=silent)
        if layer is None:
            return None, ""

        ok, message = cls._ensure_custom_fields(layer)
        if ok:
            return layer, ""

        lang = lang_manager or LanguageManager()
        if not silent:
            ModernMessageDialog.show_warning(
                lang.translate(TranslationKeys.ERROR),
                str(message or lang.translate(TranslationKeys.ASBUILT_DRAW_NEW_START_FAILED)),
            )
        return None, str(message or "")

    @staticmethod
    def current_username() -> str:
        try:
            session = SessionManager()
            username = str(getattr(session, "username", "") or "").strip()
            if username:
                return username
            session.load_credentials()
            return str(getattr(session, "username", "") or "").strip()
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module=Module.ASBUILT.value,
                event="asbuilt_current_user_resolve_failed",
            )
            return ""

    @staticmethod
    def parse_backend_datetime(value) -> Optional[datetime]:
        text = str(value or "").strip()
        if not text:
            return None
        normalized = text.replace("Z", "+00:00")
        try:
            parsed = datetime.fromisoformat(normalized)
        except Exception:
            parsed = None
        if parsed is None:
            for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
                try:
                    parsed = datetime.strptime(text, fmt)
                    break
                except Exception:
                    continue
        if parsed is None:
            return None
        if parsed.tzinfo is not None:
            try:
                parsed = parsed.astimezone().replace(tzinfo=None)
            except Exception:
                parsed = parsed.replace(tzinfo=None)
        return parsed

    @staticmethod
    def coerce_optional_int(value) -> Optional[int]:
        text = str(value or "").strip()
        if not text:
            return None
        try:
            return int(text)
        except Exception:
            return None

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

        if field_type == QVariant.DateTime:
            if isinstance(value, QDateTime):
                return value
            parsed = value if isinstance(value, datetime) else AsBuiltLayerService.parse_backend_datetime(value)
            if isinstance(parsed, datetime):
                return QDateTime(parsed.year, parsed.month, parsed.day, parsed.hour, parsed.minute, parsed.second)
        return value

    @classmethod
    def _set_attr_if_present(cls, feature: QgsFeature, *, layer: QgsVectorLayer, candidates: tuple[str, ...], value) -> None:
        actual = cls._resolve_first_field_name(layer, candidates)
        if not actual:
            return
        field_index = layer.fields().indexFromName(actual)
        field = layer.fields()[field_index] if field_index >= 0 else None
        feature.setAttribute(actual, cls.coerce_value_for_field(field, value))

    @staticmethod
    def _point_in_layer_crs(point: QgsPointXY, layer: QgsVectorLayer) -> QgsPointXY:
        if not isinstance(layer, QgsVectorLayer) or not layer.isValid():
            return point

        canvas = iface.mapCanvas() if iface is not None else None
        if canvas is None:
            return point

        try:
            source_crs = canvas.mapSettings().destinationCrs()
            target_crs = layer.crs()
            if not source_crs.isValid() or not target_crs.isValid() or source_crs == target_crs:
                return point
            transform = QgsCoordinateTransform(source_crs, target_crs, QgsProject.instance().transformContext())
            return transform.transform(point)
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module=Module.ASBUILT.value,
                event="asbuilt_point_transform_failed",
            )
            return point

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
    def find_feature_at_point(cls, point: QgsPointXY, *, layer: Optional[QgsVectorLayer], radius_multiplier: float = 3.0):
        if not isinstance(layer, QgsVectorLayer) or not layer.isValid():
            return None

        canvas = iface.mapCanvas() if iface is not None else None
        if canvas is None:
            return None

        try:
            search_radius = canvas.mapUnitsPerPixel() * float(radius_multiplier)
        except Exception:
            search_radius = 0.0
        if search_radius <= 0:
            search_radius = 2.0

        layer_point = cls._point_in_layer_crs(point, layer)
        search_rect = QgsRectangle(
            layer_point.x() - search_radius,
            layer_point.y() - search_radius,
            layer_point.x() + search_radius,
            layer_point.y() + search_radius,
        )

        try:
            request = QgsFeatureRequest().setFilterRect(search_rect)
            point_geometry = QgsGeometry.fromPointXY(layer_point)
            closest_feature = None
            closest_distance = float("inf")
            for feature in layer.getFeatures(request):
                geometry = feature.geometry()
                if geometry is None or geometry.isEmpty():
                    continue
                if layer.geometryType() == QgsWkbTypes.PointGeometry:
                    try:
                        distance = geometry.distance(point_geometry)
                    except Exception:
                        continue
                    if distance <= search_radius and distance < closest_distance:
                        closest_feature = feature
                        closest_distance = distance
                    continue
                try:
                    if geometry.contains(point_geometry) or geometry.intersects(point_geometry):
                        return feature
                except Exception:
                    continue
            return closest_feature
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module=Module.ASBUILT.value,
                event="asbuilt_feature_at_point_failed",
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

        try:
            feature = next(layer.getFeatures(QgsFeatureRequest(int(feature_id))), None)
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module=Module.ASBUILT.value,
                event="asbuilt_attach_feature_load_failed",
                extra={"feature_id": int(feature_id)},
            )
            feature = None

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
