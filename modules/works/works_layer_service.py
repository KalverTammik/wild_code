from __future__ import annotations

from datetime import datetime
from typing import Optional

from qgis.core import (
    QgsCoordinateTransform,
    QgsFeature,
    QgsFeatureRequest,
    QgsGeometry,
    QgsPointXY,
    QgsProject,
    QgsRectangle,
    QgsVectorLayer,
    QgsWkbTypes,
)
from qgis.utils import iface

from ...constants.cadastral_fields import Katastriyksus
from ...constants.settings_keys import SettingsService
from ...languages.language_manager import LanguageManager
from ...languages.translation_keys import TranslationKeys
from ...utils.MapTools.MapHelpers import ActiveLayersHelper, MapHelpers
from ...utils.messagesHelper import ModernMessageDialog
from ...utils.url_manager import Module
from ...Logs.python_fail_logger import PythonFailLogger


class WorksLayerService:
    TASK_ID_FIELD_CANDIDATES = ("Mailabl_id", "mailabl_id", "task_id", "taskid")

    @staticmethod
    def resolve_main_layer(*, lang_manager=None, silent: bool = False) -> Optional[QgsVectorLayer]:
        lang = lang_manager or LanguageManager()
        identifier = SettingsService().module_main_layer_name(Module.WORKS.value) or ""
        layer = MapHelpers.resolve_layer(identifier)
        if not isinstance(layer, QgsVectorLayer) or not layer.isValid():
            if not silent:
                ModernMessageDialog.show_warning(
                    lang.translate(TranslationKeys.ERROR),
                    lang.translate(TranslationKeys.WORKS_LAYER_MISSING),
                )
            return None

        if layer.geometryType() != QgsWkbTypes.PointGeometry:
            if not silent:
                ModernMessageDialog.show_warning(
                    lang.translate(TranslationKeys.ERROR),
                    lang.translate(TranslationKeys.WORKS_LAYER_INVALID_GEOMETRY),
                )
            return None

        if WorksLayerService.resolve_task_id_field_name(layer) is None:
            if not silent:
                ModernMessageDialog.show_warning(
                    lang.translate(TranslationKeys.ERROR),
                    lang.translate(TranslationKeys.WORKS_LAYER_ID_FIELD_MISSING),
                )
            return None

        return layer

    @staticmethod
    def resolve_task_id_field_name(layer: Optional[QgsVectorLayer]) -> Optional[str]:
        if not isinstance(layer, QgsVectorLayer) or not layer.isValid():
            return None

        try:
            field_map = {field.name().lower(): field.name() for field in layer.fields()}
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module=Module.WORKS.value,
                event="works_layer_field_map_failed",
            )
            return None

        for candidate in WorksLayerService.TASK_ID_FIELD_CANDIDATES:
            actual = field_map.get(str(candidate).lower())
            if actual:
                return actual
        return None

    @staticmethod
    def find_property_feature_at_point(point: QgsPointXY, *, radius_multiplier: float = 3.0):
        property_layer = ActiveLayersHelper.resolve_main_property_layer(silent=True)
        if not isinstance(property_layer, QgsVectorLayer) or not property_layer.isValid():
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

        layer_point = WorksLayerService._point_in_layer_crs(point, property_layer)

        search_rect = QgsRectangle(
            layer_point.x() - search_radius,
            layer_point.y() - search_radius,
            layer_point.x() + search_radius,
            layer_point.y() + search_radius,
        )
        request = QgsFeatureRequest().setFilterRect(search_rect)

        try:
            return next(property_layer.getFeatures(request), None)
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module=Module.WORKS.value,
                event="works_property_lookup_failed",
            )
            return None

    @staticmethod
    def property_cadastral_number(feature) -> str:
        if feature is None:
            return ""
        try:
            value = feature.attribute(Katastriyksus.tunnus)
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module=Module.WORKS.value,
                event="works_property_tunnus_failed",
            )
            return ""
        return str(value or "").strip()

    @staticmethod
    def property_display_text(feature, *, lang_manager=None) -> str:
        lang = lang_manager or LanguageManager()
        if feature is None:
            return lang.translate(TranslationKeys.WORKS_CREATE_PROPERTY_NONE)

        parts: list[str] = []
        cadastral = WorksLayerService.property_cadastral_number(feature)
        if cadastral:
            parts.append(cadastral)

        for field_name in (
            Katastriyksus.l_aadress,
            Katastriyksus.ay_nimi,
            Katastriyksus.ov_nimi,
            Katastriyksus.mk_nimi,
        ):
            try:
                value = feature.attribute(field_name)
            except Exception:
                value = None
            text = str(value or "").strip()
            if text:
                parts.append(text)

        return " · ".join(parts) if parts else lang.translate(TranslationKeys.WORKS_CREATE_PROPERTY_NONE)

    @staticmethod
    def insert_work_feature(
        *,
        layer: QgsVectorLayer,
        point: QgsPointXY,
        task_id: str,
        title: str,
        description: str,
        type_label: str,
        priority: str,
        has_property: bool,
    ) -> tuple[bool, str]:
        if not isinstance(layer, QgsVectorLayer) or not layer.isValid():
            return False, "Invalid works layer"

        task_id_field = WorksLayerService.resolve_task_id_field_name(layer)
        if not task_id_field:
            return False, "Task id field missing"

        feature = QgsFeature(layer.fields())
        layer_point = WorksLayerService._point_in_layer_crs(point, layer)
        feature.setGeometry(QgsGeometry.fromPointXY(layer_point))

        now = datetime.now()
        field_map = {field.name().lower(): field.name() for field in layer.fields()}

        feature.setAttribute(task_id_field, str(task_id))
        WorksLayerService._set_attr_if_present(feature, field_map, "title", title)
        WorksLayerService._set_attr_if_present(feature, field_map, "description", description)
        WorksLayerService._set_attr_if_present(feature, field_map, "type", type_label)
        WorksLayerService._set_attr_if_present(feature, field_map, "priority", priority)
        WorksLayerService._set_attr_if_present(feature, field_map, "status", True)
        WorksLayerService._set_attr_if_present(feature, field_map, "active", True)
        WorksLayerService._set_attr_if_present(feature, field_map, "affected_properties", bool(has_property))
        WorksLayerService._set_attr_if_present(
            feature,
            field_map,
            "datetime",
            now.strftime("%Y-%m-%d %H:%M"),
        )
        WorksLayerService._set_attr_if_present(feature, field_map, "created_at", now.isoformat())
        WorksLayerService._set_attr_if_present(feature, field_map, "updated_at", now.isoformat())

        started_edit = False
        try:
            if not layer.isEditable():
                started_edit = bool(layer.startEditing())
                if not started_edit:
                    return False, "Could not start editing works layer"

            if not layer.addFeature(feature):
                if started_edit:
                    layer.rollBack()
                return False, "Could not add feature to works layer"

            if started_edit and not layer.commitChanges():
                errors = "; ".join(layer.commitErrors() or [])
                layer.rollBack()
                return False, errors or "Could not commit works layer changes"

            layer.triggerRepaint()
            return True, ""
        except Exception as exc:
            try:
                if layer.isEditable():
                    layer.rollBack()
            except Exception as rollback_exc:
                PythonFailLogger.log_exception(
                    rollback_exc,
                    module=Module.WORKS.value,
                    event="works_layer_rollback_failed",
                )
            PythonFailLogger.log_exception(
                exc,
                module=Module.WORKS.value,
                event="works_layer_insert_failed",
            )
            return False, str(exc)

    @staticmethod
    def _set_attr_if_present(feature: QgsFeature, field_map: dict[str, str], field_name: str, value) -> None:
        actual = field_map.get(str(field_name).lower())
        if not actual:
            return
        feature.setAttribute(actual, value)

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

            transform = QgsCoordinateTransform(
                source_crs,
                target_crs,
                QgsProject.instance().transformContext(),
            )
            return transform.transform(point)
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module=Module.WORKS.value,
                event="works_point_transform_failed",
            )
            return point