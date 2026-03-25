from __future__ import annotations

from typing import Optional

import processing
from qgis.core import QgsMapLayer, QgsProcessingFeatureSourceDefinition, QgsProject, QgsVectorLayer

from ...engines.LayerCreationEngine import MailablGroupFolders
from ...Logs.python_fail_logger import PythonFailLogger
from ..MapTools.MapHelpers import MapHelpers
from .memory_layer_result_service import MemoryLayerResultService


class LayerProcessingService:
    """Shared processing helpers for preview/result memory layers."""

    @staticmethod
    def _source_definition(layer: QgsVectorLayer, *, selected_only: bool = False):
        source_ref = ""
        try:
            if QgsProject.instance().mapLayer(layer.id()) is not None:
                source_ref = layer.id()
        except Exception:
            source_ref = ""

        if not source_ref:
            try:
                source_ref = layer.source()
            except Exception:
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
        if source_layer is None or not source_layer.isValid():
            return None

        try:
            selected_count = int(source_layer.selectedFeatureCount() or 0)
        except Exception:
            selected_count = 0
        if selected_count <= 0:
            return None

        return cls.run_processing_to_memory(
            "native:buffer",
            {
                "INPUT": cls._source_definition(source_layer, selected_only=True),
                "DISTANCE": float(distance),
                "SEGMENTS": int(segments),
                "DISSOLVE": bool(dissolve),
                "END_CAP_STYLE": int(end_cap_style),
                "JOIN_STYLE": int(join_style),
                "MITER_LIMIT": float(miter_limit),
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
                    "source": getattr(source_layer, "name", lambda: "")(),
                    "overlay": getattr(overlay_layer, "name", lambda: "")(),
                },
            )
            return 0

        if make_visible:
            try:
                MapHelpers.ensure_layer_visible(source_layer, make_active=make_active)
            except Exception:
                pass

        try:
            return int(source_layer.selectedFeatureCount() or 0)
        except Exception:
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
        except Exception:
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
        )
