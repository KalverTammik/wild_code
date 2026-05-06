from __future__ import annotations

import os
from typing import Optional

from qgis.PyQt.QtCore import QVariant
from qgis.core import QgsField, QgsFields, QgsProject, QgsVectorLayer, QgsWkbTypes

from ...constants.settings_keys import SettingsService
from ...engines.LayerCreationEngine import MailablGroupFolders
from ...utils.MapTools.MapHelpers import MapHelpers
from ...utils.mapandproperties.ArchiveLayerHandler import GPKGHelpers
from ...utils.url_manager import Module
from ...Logs.python_fail_logger import PythonFailLogger


class WorksTempLayerHelper:
    DEFAULT_LAYER_NAME = "Works_Temp"

    @staticmethod
    def default_standalone_gpkg_path(
        reference_layer: Optional[QgsVectorLayer],
        layer_name: str,
    ) -> str:
        reference_path = WorksTempLayerHelper.gpkg_path_for_layer(reference_layer)
        if reference_path:
            base_dir = os.path.dirname(reference_path)
        else:
            base_dir = os.path.expanduser("~")

        safe_name = "".join(
            character if character not in '<>:"/\\|?*' else "_"
            for character in str(layer_name or "").strip()
        ).strip(" ._") or WorksTempLayerHelper.DEFAULT_LAYER_NAME
        return os.path.join(base_dir, f"{safe_name}.gpkg")

    @staticmethod
    def _normalize_gpkg_path(gpkg_path: str) -> str:
        path = str(gpkg_path or "").strip()
        if not path:
            return ""

        if os.path.splitext(path)[1].lower() != ".gpkg":
            path = f"{path}.gpkg"

        return os.path.normcase(os.path.abspath(path))

    @staticmethod
    def _find_loaded_layer(layer_name: str, gpkg_path: str) -> Optional[QgsVectorLayer]:
        normalized_path = WorksTempLayerHelper._normalize_gpkg_path(gpkg_path)
        if not normalized_path:
            return None

        for layer in QgsProject.instance().mapLayersByName(layer_name):
            if not isinstance(layer, QgsVectorLayer) or not layer.isValid():
                continue
            if WorksTempLayerHelper._normalize_gpkg_path(WorksTempLayerHelper.gpkg_path_for_layer(layer)) == normalized_path:
                return layer
        return None

    @staticmethod
    def _remove_loaded_layers_for_gpkg(gpkg_path: str) -> None:
        normalized_path = WorksTempLayerHelper._normalize_gpkg_path(gpkg_path)
        if not normalized_path:
            return

        project = QgsProject.instance()
        for layer in list(project.mapLayers().values()):
            if not isinstance(layer, QgsVectorLayer) or not layer.isValid():
                continue
            layer_path = WorksTempLayerHelper._normalize_gpkg_path(WorksTempLayerHelper.gpkg_path_for_layer(layer))
            if layer_path == normalized_path:
                project.removeMapLayer(layer.id())

    @staticmethod
    def resolve_reference_layer(preferred_layer: Optional[QgsVectorLayer] = None) -> Optional[QgsVectorLayer]:
        preferred = preferred_layer if isinstance(preferred_layer, QgsVectorLayer) and preferred_layer.isValid() else None
        if WorksTempLayerHelper.gpkg_path_for_layer(preferred):
            return preferred

        try:
            property_identifier = SettingsService().module_main_layer_name(Module.PROPERTY.value) or ""
            property_layer = MapHelpers.resolve_layer(property_identifier)
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module=Module.WORKS.value,
                event="works_temp_reference_layer_failed",
            )
            property_layer = None

        if isinstance(property_layer, QgsVectorLayer) and property_layer.isValid() and WorksTempLayerHelper.gpkg_path_for_layer(property_layer):
            return property_layer
        return preferred or property_layer

    @staticmethod
    def gpkg_path_for_layer(layer: Optional[QgsVectorLayer]) -> str:
        if not isinstance(layer, QgsVectorLayer) or not layer.isValid():
            return ""
        try:
            uri = layer.dataProvider().dataSourceUri() or ""
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module=Module.WORKS.value,
                event="works_temp_reference_uri_failed",
            )
            return ""

        gpkg_path = (uri.split("|")[0] if uri else "").strip()
        if not gpkg_path or os.path.splitext(gpkg_path)[1].lower() != ".gpkg":
            return ""
        return gpkg_path

    @staticmethod
    def create_or_load_layer(
        reference_layer: QgsVectorLayer,
        layer_name: str,
        *,
        gpkg_path: Optional[str] = None,
        overwrite_file: bool = False,
        group_name: str = MailablGroupFolders.SANDBOXING,
    ) -> tuple[Optional[QgsVectorLayer], str]:
        normalized_name = str(layer_name or "").strip()
        if not normalized_name:
            return None, "Layer name is empty"

        if not isinstance(reference_layer, QgsVectorLayer) or not reference_layer.isValid():
            return None, "Reference layer is invalid"

        target_gpkg_path = WorksTempLayerHelper._normalize_gpkg_path(
            gpkg_path or WorksTempLayerHelper.gpkg_path_for_layer(reference_layer)
        )
        if not target_gpkg_path:
            return None, "GeoPackage path is empty"

        existing_loaded = WorksTempLayerHelper._find_loaded_layer(normalized_name, target_gpkg_path)
        if existing_loaded is not None and not overwrite_file:
            return existing_loaded, ""

        try:
            parent_dir = os.path.dirname(target_gpkg_path)
            if parent_dir:
                os.makedirs(parent_dir, exist_ok=True)

            if overwrite_file and os.path.exists(target_gpkg_path):
                WorksTempLayerHelper._remove_loaded_layers_for_gpkg(target_gpkg_path)
                os.remove(target_gpkg_path)

            if not overwrite_file and GPKGHelpers.gpkg_layer_exists(target_gpkg_path, normalized_name):
                loaded = GPKGHelpers.load_layer_from_gpkg(
                    target_gpkg_path,
                    normalized_name,
                    group_name=group_name,
                )
                if loaded is not None and loaded.isValid():
                    return loaded, ""
                return None, "Could not load the existing layer from the GeoPackage"

            created = GPKGHelpers.create_empty_gpkg_layer(
                gpkg_path=target_gpkg_path,
                layer_name=normalized_name,
                geometry_type=QgsWkbTypes.Point,
                crs=reference_layer.crs(),
                fields=WorksTempLayerHelper._build_fields(),
                overwrite=False,
            )
            if not created:
                return None, "Could not create the layer inside the GeoPackage"

            loaded = GPKGHelpers.load_layer_from_gpkg(
                target_gpkg_path,
                normalized_name,
                group_name=group_name,
            )
            if loaded is None or not loaded.isValid():
                return None, "Layer was created but could not be loaded into the project"
            return loaded, ""
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module=Module.WORKS.value,
                event="works_temp_layer_create_failed",
                extra={"layer": normalized_name},
            )
            return None, str(exc)

    @staticmethod
    def _build_fields() -> QgsFields:
        fields = QgsFields()
        integer_type = getattr(QVariant, "LongLong", QVariant.Int)

        fields.append(QgsField("ext_job_id", integer_type))
        fields.append(QgsField("ext_job_name", QVariant.String))
        fields.append(QgsField("ext_job_type", integer_type))
        fields.append(QgsField("ext_job_state", integer_type))
        fields.append(QgsField("detailed", QVariant.String))
        fields.append(QgsField("active", QVariant.Bool))
        fields.append(QgsField("begin_date", QVariant.DateTime))
        fields.append(QgsField("end_date", QVariant.DateTime))
        fields.append(QgsField("added_by", QVariant.String))
        fields.append(QgsField("added_date", QVariant.DateTime))
        fields.append(QgsField("updated_by", QVariant.String))
        fields.append(QgsField("update_date", QVariant.DateTime))
        return fields