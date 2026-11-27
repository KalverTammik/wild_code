from __future__ import annotations

from typing import Optional

import processing
from qgis.core import (
    QgsCoordinateReferenceSystem,
    QgsMapLayer,
    QgsProcessingFeatureSourceDefinition,
    QgsProject,
    QgsUnitTypes,
    QgsVectorLayer,
)

from ...engines.LayerCreationEngine import MailablGroupFolders
from ...Logs.python_fail_logger import PythonFailLogger
from ..MapTools.MapHelpers import MapHelpers
from .memory_layer_result_service import MemoryLayerResultService


class LayerProcessingService:
    """Shared processing helpers for preview/result memory layers."""

    # L-EST97, Estonia's national grid in metres: the buffer CRS when neither the layer nor the
    # project is in metres.
    METRIC_FALLBACK_CRS = "EPSG:3301"

    @staticmethod
    def metres_in_layer_units(layer: QgsVectorLayer, metres: float) -> Optional[float]:
        """The distance in the layer's own units, or None when its CRS is geographic (degrees).

        A degree is not a fixed length, so no factor converts metres to degrees.
        """
        crs = layer.crs()
        if not crs.isValid() or crs.isGeographic():
            return None
        factor = QgsUnitTypes.fromUnitToUnitFactor(QgsUnitTypes.DistanceUnit.DistanceMeters, crs.mapUnits())
        return float(metres) * float(factor)

    @classmethod
    def metric_crs(cls) -> QgsCoordinateReferenceSystem:
        project_crs = QgsProject.instance().crs()
        if (project_crs.isValid() and not project_crs.isGeographic()
                and project_crs.mapUnits() == QgsUnitTypes.DistanceUnit.DistanceMeters):
            return project_crs
        return QgsCoordinateReferenceSystem(cls.METRIC_FALLBACK_CRS)

    @staticmethod
    def _source_definition(layer: QgsVectorLayer, *, selected_only: bool = False):
        source_ref = ""
        try:
            if QgsProject.instance().mapLayer(layer.id()) is not None:
                source_ref = layer.id()
        except (AttributeError, RuntimeError):  # layer None or already deleted
            source_ref = ""

        if source_ref:
            return QgsProcessingFeatureSourceDefinition(source_ref, bool(selected_only))

        if not selected_only:
            return layer

        try:
            source_ref = layer.source()
        except (AttributeError, RuntimeError):  # layer None or already deleted
            source_ref = ""
        return QgsProcessingFeatureSourceDefinition(source_ref, bool(selected_only))

    @staticmethod
    def _resolve_output_layer(result: object) -> Optional[QgsVectorLayer]:
        if isinstance(result, QgsVectorLayer):
            return result if result.isValid() else None

        if isinstance(result, QgsMapLayer):
            return result if isinstance(result, QgsVectorLayer) and result.isValid() else None

        if isinstance(result, str):
            project = QgsProject.instance()
            layer = project.mapLayer(result)
            if isinstance(layer, QgsVectorLayer) and layer.isValid():
                return layer
            matches = project.mapLayersByName(result)
            for candidate in matches:
                if isinstance(candidate, QgsVectorLayer) and candidate.isValid():
                    return candidate
        return None

    @classmethod
    def run_processing_to_memory(
        cls,
        algorithm_id: str,
        parameters: dict,
        *,
        result_layer_name: str,
        group_name: str = MailablGroupFolders.SANDBOXING,
        style_path: Optional[str] = None,
        replace_existing: bool = True,
        custom_properties: Optional[dict[str, str]] = None,
        make_visible: bool = True,
        make_active: bool = False,
        register_result: bool = True,
    ) -> Optional[QgsVectorLayer]:
        try:
            processing_params = dict(parameters or {})
            processing_params["OUTPUT"] = "memory:"
            output = processing.run(algorithm_id, processing_params).get("OUTPUT")
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module="layers",
                event="layer_processing_run_failed",
                extra={"algorithm": algorithm_id, "layer": result_layer_name},
            )
            return None

        layer = cls._resolve_output_layer(output)
        if not register_result:
            return layer

        return MemoryLayerResultService.prepare_result_layer(
            layer,
            layer_name=result_layer_name,
            group_name=group_name,
            style_path=style_path,
            replace_existing=replace_existing,
            custom_properties=custom_properties,
            make_visible=make_visible,
            make_active=make_active,
        )

    @classmethod
    def _buffer_in_metres(
        cls,
        source_layer: QgsVectorLayer,
        input_definition,
        *,
        distance: float,
        segments: int,
        dissolve: bool,
        end_cap_style: int,
        join_style: int,
        miter_limit: float,
        result_layer_name: str,
        **result_options,
    ) -> Optional[QgsVectorLayer]:
        """Buffer by ``distance`` metres: in the layer's units, or through a metric CRS for degrees."""
        def buffer_parameters(input_value, layer_distance: float) -> dict:
            return {
                "INPUT": input_value,
                "DISTANCE": float(layer_distance),
                "SEGMENTS": int(segments),
                "DISSOLVE": bool(dissolve),
                "END_CAP_STYLE": int(end_cap_style),
                "JOIN_STYLE": int(join_style),
                "MITER_LIMIT": float(miter_limit),
            }

        layer_distance = cls.metres_in_layer_units(source_layer, distance)
        if layer_distance is not None:
            return cls.run_processing_to_memory(
                "native:buffer",
                buffer_parameters(input_definition, layer_distance),
                result_layer_name=result_layer_name,
                **result_options,
            )

        reprojected = cls.run_processing_to_memory(
            "native:reprojectlayer",
            {"INPUT": input_definition, "TARGET_CRS": cls.metric_crs()},
            result_layer_name=result_layer_name,
            register_result=False,
        )
        if reprojected is None:
            return None
        buffered = cls.run_processing_to_memory(
            "native:buffer",
            buffer_parameters(reprojected, distance),
            result_layer_name=result_layer_name,
            register_result=False,
        )
        if buffered is None:
            return None
        return cls.run_processing_to_memory(
            "native:reprojectlayer",
            {"INPUT": buffered, "TARGET_CRS": source_layer.crs()},
            result_layer_name=result_layer_name,
            **result_options,
        )

    @classmethod
    def buffer_selected_features(
        cls,
        source_layer: Optional[QgsVectorLayer],
        *,
        distance: float,
        result_layer_name: str,
        group_name: str = MailablGroupFolders.SANDBOXING,
        style_path: Optional[str] = None,
        replace_existing: bool = True,
        segments: int = 5,
        dissolve: bool = False,
        end_cap_style: int = 0,
        join_style: int = 0,
        miter_limit: float = 2.0,
        custom_properties: Optional[dict[str, str]] = None,
        make_visible: bool = True,
        make_active: bool = False,
    ) -> Optional[QgsVectorLayer]:
        """Buffer the selected features by ``distance`` metres."""
        if source_layer is None or not source_layer.isValid():
            return None

        try:
            selected_count = int(source_layer.selectedFeatureCount() or 0)
        except (AttributeError, RuntimeError):  # layer None or already deleted
            selected_count = 0
        if selected_count <= 0:
            return None

        return cls._buffer_in_metres(
            source_layer,
            cls._source_definition(source_layer, selected_only=True),
            distance=distance,
            segments=segments,
            dissolve=dissolve,
            end_cap_style=end_cap_style,
            join_style=join_style,
            miter_limit=miter_limit,
            result_layer_name=result_layer_name,
            group_name=group_name,
            style_path=style_path,
            replace_existing=replace_existing,
            custom_properties=custom_properties,
            make_visible=make_visible,
            make_active=make_active,
        )

    @classmethod
    def buffer_layer(
        cls,
        source_layer: Optional[QgsVectorLayer],
        *,
        distance: float,
        result_layer_name: str,
        selected_only: bool = False,
        group_name: str = MailablGroupFolders.SANDBOXING,
        style_path: Optional[str] = None,
        replace_existing: bool = True,
        segments: int = 5,
        dissolve: bool = False,
        end_cap_style: int = 0,
        join_style: int = 0,
        miter_limit: float = 2.0,
        custom_properties: Optional[dict[str, str]] = None,
        make_visible: bool = True,
        make_active: bool = False,
        register_result: bool = True,
    ) -> Optional[QgsVectorLayer]:
        """Buffer the layer (or its selection) by ``distance`` metres."""
        if source_layer is None or not source_layer.isValid():
            return None

        if selected_only:
            try:
                selected_count = int(source_layer.selectedFeatureCount() or 0)
            except (AttributeError, RuntimeError):  # layer None or already deleted
                selected_count = 0
            if selected_count <= 0:
                return None

        return cls._buffer_in_metres(
            source_layer,
            cls._source_definition(source_layer, selected_only=selected_only),
            distance=distance,
            segments=segments,
            dissolve=dissolve,
            end_cap_style=end_cap_style,
            join_style=join_style,
            miter_limit=miter_limit,
            result_layer_name=result_layer_name,
            group_name=group_name,
            style_path=style_path,
            replace_existing=replace_existing,
            custom_properties=custom_properties,
            make_visible=make_visible,
            make_active=make_active,
            register_result=register_result,
        )

    @classmethod
    def select_features_intersecting_layer(
        cls,
        source_layer: Optional[QgsVectorLayer],
        overlay_layer: Optional[QgsVectorLayer],
        *,
        predicate: Optional[list[int]] = None,
        method: int = 0,
        make_visible: bool = True,
        make_active: bool = False,
    ) -> int:
        if source_layer is None or overlay_layer is None:
            return 0
        if not source_layer.isValid() or not overlay_layer.isValid():
            return 0

        try:
            processing.run(
                "native:selectbylocation",
                {
                    "INPUT": source_layer,
                    "PREDICATE": list(predicate or [0]),
                    "INTERSECT": overlay_layer,
                    "METHOD": int(method),
                },
            )
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module="layers",
                event="layer_processing_select_by_location_failed",
                extra={
                    "source": source_layer.name(),
                    "overlay": overlay_layer.name(),
                },
            )
            return 0

        if make_visible:
            try:
                MapHelpers.ensure_layer_visible(source_layer, make_active=make_active)
            except Exception as exc:
                PythonFailLogger.log_exception(exc, module="layers", event="layer_ensure_visible_failed")

        try:
            return int(source_layer.selectedFeatureCount() or 0)
        except (AttributeError, RuntimeError):  # layer None or already deleted
            return 0

    @classmethod
    def intersect_layers(
        cls,
        input_layer: Optional[QgsVectorLayer],
        overlay_layer: Optional[QgsVectorLayer],
        *,
        result_layer_name: str,
        input_selected_only: bool = False,
        overlay_selected_only: bool = False,
        group_name: str = MailablGroupFolders.SANDBOXING,
        style_path: Optional[str] = None,
        replace_existing: bool = True,
        custom_properties: Optional[dict[str, str]] = None,
        make_visible: bool = True,
        make_active: bool = False,
    ) -> Optional[QgsVectorLayer]:
        if input_layer is None or overlay_layer is None:
            return None
        if not input_layer.isValid() or not overlay_layer.isValid():
            return None

        return cls.run_processing_to_memory(
            "native:intersection",
            {
                "INPUT": cls._source_definition(input_layer, selected_only=input_selected_only),
                "OVERLAY": cls._source_definition(overlay_layer, selected_only=overlay_selected_only),
                "INPUT_FIELDS": [],
                "OVERLAY_FIELDS": [],
                "OVERLAY_FIELDS_PREFIX": "",
            },
            result_layer_name=result_layer_name,
            group_name=group_name,
            style_path=style_path,
            replace_existing=replace_existing,
            custom_properties=custom_properties,
            make_visible=make_visible,
            make_active=make_active,
        )

    @classmethod
    def merge_layers(
        cls,
        source_layers: list[QgsVectorLayer],
        *,
        result_layer_name: str,
        group_name: str = MailablGroupFolders.SANDBOXING,
        style_path: Optional[str] = None,
        replace_existing: bool = True,
        custom_properties: Optional[dict[str, str]] = None,
        make_visible: bool = True,
        make_active: bool = False,
    ) -> Optional[QgsVectorLayer]:
        valid_layers = [layer for layer in (source_layers or []) if layer is not None and layer.isValid()]
        if not valid_layers:
            return None

        merge_crs = None
        try:
            merge_crs = valid_layers[0].crs()
        except (AttributeError, RuntimeError):  # layer deleted since the isValid() filter
            merge_crs = None

        return cls.run_processing_to_memory(
            "native:mergevectorlayers",
            {
                "LAYERS": valid_layers,
                "CRS": merge_crs,
            },
            result_layer_name=result_layer_name,
            group_name=group_name,
            style_path=style_path,
            replace_existing=replace_existing,
            custom_properties=custom_properties,
            make_visible=make_visible,
            make_active=make_active,
        )

    @classmethod
    def dissolve_layer(
        cls,
        source_layer: Optional[QgsVectorLayer],
        *,
        result_layer_name: str,
        selected_only: bool = False,
        group_name: str = MailablGroupFolders.SANDBOXING,
        style_path: Optional[str] = None,
        replace_existing: bool = True,
        field_names: Optional[list[str]] = None,
        custom_properties: Optional[dict[str, str]] = None,
        make_visible: bool = True,
        make_active: bool = False,
        register_result: bool = True,
    ) -> Optional[QgsVectorLayer]:
        if source_layer is None or not source_layer.isValid():
            return None

        return cls.run_processing_to_memory(
            "native:dissolve",
            {
                "INPUT": cls._source_definition(source_layer, selected_only=selected_only),
                "FIELD": list(field_names or []),
                "SEPARATE_DISJOINT": False,
            },
            result_layer_name=result_layer_name,
            group_name=group_name,
            style_path=style_path,
            replace_existing=replace_existing,
            custom_properties=custom_properties,
            make_visible=make_visible,
            make_active=make_active,
            register_result=register_result,
        )
