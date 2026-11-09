"""What the module layer services (works, as-built, projects, easements) have in common."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from qgis.core import (
    QgsCoordinateTransform,
    QgsFeature,
    QgsFeatureRequest,
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
from ...Logs.python_fail_logger import PythonFailLogger
from ..MapTools.MapHelpers import MapHelpers
from ..SessionManager import SessionManager
from ..geometry_payload import GeometryPayloadService
from ..messagesHelper import ModernMessageDialog
from ..url_manager import Module


class ModuleLayerServiceBase:
    """Helpers every module layer service shares. A service names its module and warning texts below."""

    MODULE: Module
    LAYER_MISSING_KEY: str
    LAYER_AMBIGUOUS_KEY: str
    REQUIRED_GEOMETRY: Optional[QgsWkbTypes.GeometryType] = None
    LAYER_INVALID_GEOMETRY_KEY: str = ""

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
        except (TypeError, ValueError):
            return None

    @classmethod
    def _field_map(cls, layer: Optional[QgsVectorLayer]) -> dict[str, str]:
        if not isinstance(layer, QgsVectorLayer) or not layer.isValid():
            return {}
        try:
            return {field.name().lower(): field.name() for field in layer.fields()}
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module=cls.MODULE.value,
                event=f"{cls.MODULE.value}_layer_field_map_failed",
            )
            return {}

    @classmethod
    def current_username(cls) -> str:
        try:
            session = SessionManager()
            username = str(session.username or "").strip()
            if username:
                return username
            return session.get_username()
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module=cls.MODULE.value,
                event=f"{cls.MODULE.value}_current_user_resolve_failed",
            )
            return ""

    @classmethod
    def _point_in_layer_crs(cls, point: QgsPointXY, layer: QgsVectorLayer) -> QgsPointXY:
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
                module=cls.MODULE.value,
                event=f"{cls.MODULE.value}_point_transform_failed",
            )
            return point

    @classmethod
    def backend_geometry_payload_from_geometry(cls, geometry: Optional[QgsGeometry]) -> Optional[dict[str, object]]:
        return GeometryPayloadService.from_qgs_geometry(
            geometry,
            module=cls.MODULE.value,
            error_event=f"{cls.MODULE.value}_geometry_to_payload_failed",
        )

    @classmethod
    def resolve_main_layer(cls, *, lang_manager=None, silent: bool = False) -> Optional[QgsVectorLayer]:
        lang = lang_manager or LanguageManager()
        identifier = SettingsService().module_main_layer_name(cls.MODULE.value) or ""
        matches = cls._configured_layers(identifier)
        if len(matches) > 1:
            if not silent:
                ModernMessageDialog.show_warning(
                    lang.translate(TranslationKeys.ERROR),
                    lang.translate(cls.LAYER_AMBIGUOUS_KEY),
                )
            return None

        layer = matches[0] if matches else None
        if not isinstance(layer, QgsVectorLayer) or not layer.isValid():
            if not silent:
                ModernMessageDialog.show_warning(
                    lang.translate(TranslationKeys.ERROR),
                    lang.translate(cls.LAYER_MISSING_KEY),
                )
            return None

        try:
            if str(identifier or "").strip() != str(layer.id() or "").strip():
                SettingsService().module_main_layer_name(cls.MODULE.value, value=layer.id())
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module=cls.MODULE.value,
                event=f"{cls.MODULE.value}_layer_setting_id_migrate_failed",
                extra={"identifier": str(identifier or "")},
            )

        if cls.REQUIRED_GEOMETRY is not None and layer.geometryType() != cls.REQUIRED_GEOMETRY:
            if not silent:
                ModernMessageDialog.show_warning(
                    lang.translate(TranslationKeys.ERROR),
                    lang.translate(cls.LAYER_INVALID_GEOMETRY_KEY),
                )
            return None

        return layer if cls._main_layer_is_ready(layer, lang=lang, silent=silent) else None

    @classmethod
    def _main_layer_is_ready(cls, layer: QgsVectorLayer, *, lang, silent: bool) -> bool:
        """The module's own checks on a layer that passed the shared ones."""
        return True

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


class AttachableLayerServiceBase(ModuleLayerServiceBase):
    """A module that attaches backend items to features on one configured layer: as-built, projects, easements.

    A service sets the key below and supplies `_ensure_custom_fields` and `coerce_value_for_field`, whose copies
    still differ between modules.
    """

    DRAW_START_FAILED_KEY: str

    @classmethod
    def _ensure_custom_fields(cls, layer: Optional[QgsVectorLayer]) -> tuple[bool, str]:
        raise NotImplementedError

    @staticmethod
    def coerce_value_for_field(field, value):
        raise NotImplementedError

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
                str(message or lang.translate(cls.DRAW_START_FAILED_KEY)),
            )
        return None, str(message or "")

    @staticmethod
    def _layer_target_label(layer: Optional[QgsMapLayer]) -> str:
        if layer is None:
            return ""
        try:
            return str(layer.name() or "").strip()
        except Exception:
            return ""

    @classmethod
    def _resolve_first_field_name(cls, layer: Optional[QgsVectorLayer], candidates: tuple[str, ...]) -> Optional[str]:
        field_map = cls._field_map(layer)
        for candidate in candidates:
            actual = field_map.get(str(candidate).lower())
            if actual:
                return actual
        return None

    @classmethod
    def _set_attr_if_present(cls, feature: QgsFeature, *, layer: QgsVectorLayer, candidates: tuple[str, ...], value) -> None:
        actual = cls._resolve_first_field_name(layer, candidates)
        if not actual:
            return
        field_index = layer.fields().indexFromName(actual)
        field = layer.fields()[field_index] if field_index >= 0 else None
        feature.setAttribute(actual, cls.coerce_value_for_field(field, value))

    @classmethod
    def _feature_by_id(cls, layer: Optional[QgsVectorLayer], feature_id: int) -> Optional[QgsFeature]:
        if not isinstance(layer, QgsVectorLayer) or not layer.isValid():
            return None

        try:
            feature = next(layer.getFeatures(QgsFeatureRequest(int(feature_id))), None)
            if feature is not None:
                return feature
        except Exception:
            pass

        try:
            target_id = int(feature_id)
            for candidate in layer.getFeatures():
                if int(candidate.id()) == target_id:
                    return candidate
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module=cls.MODULE.value,
                event=f"{cls.MODULE.value}_feature_by_id_failed",
                extra={"feature_id": int(feature_id)},
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
                module=cls.MODULE.value,
                event=f"{cls.MODULE.value}_feature_at_point_failed",
            )
            return None

    @classmethod
    def _geometry_in_layer_crs(cls, geometry: QgsGeometry, *, source_layer: QgsVectorLayer, target_layer: QgsVectorLayer) -> QgsGeometry:
        transformed = QgsGeometry(geometry)
        try:
            if source_layer.crs() != target_layer.crs():
                transform = QgsCoordinateTransform(
                    source_layer.crs(),
                    target_layer.crs(),
                    QgsProject.instance(),
                )
                transformed.transform(transform)
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module=cls.MODULE.value,
                event=f"{cls.MODULE.value}_layer_geometry_transform_failed",
            )
        return transformed

    @staticmethod
    def _refresh_saved_layer(layer: Optional[QgsVectorLayer]) -> None:
        if not isinstance(layer, QgsVectorLayer) or not layer.isValid():
            return
        try:
            layer.updateExtents()
        except Exception:
            pass
        try:
            if not layer.isEditable():
                layer.reload()
        except Exception:
            pass
        try:
            layer.triggerRepaint()
        except Exception:
            pass
        try:
            if iface is not None and iface.mapCanvas() is not None:
                iface.mapCanvas().refresh()
        except Exception:
            pass
