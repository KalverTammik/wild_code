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
    ) -> tuple[Optional[QgsVectorLayer], str]:
        normalized_name = str(layer_name or "").strip()
        if not normalized_name:
            return None, "Layer name is empty"

        existing = QgsProject.instance().mapLayersByName(normalized_name)
        if existing:
            layer = existing[0]
            if isinstance(layer, QgsVectorLayer) and layer.isValid():
                return layer, ""

        gpkg_path = WorksTempLayerHelper.gpkg_path_for_layer(reference_layer)
        if not gpkg_path:
            return None, "Reference layer is not backed by a GeoPackage"

        try:
            if GPKGHelpers.gpkg_layer_exists(gpkg_path, normalized_name):
                loaded = GPKGHelpers.load_layer_from_gpkg(
                    gpkg_path,
                    normalized_name,
                    group_name=MailablGroupFolders.SANDBOXING,
                )
                if loaded is not None and loaded.isValid():
                    return loaded, ""
                return None, "Could not load the existing layer from the GeoPackage"

            created = GPKGHelpers.create_empty_gpkg_layer(
                gpkg_path=gpkg_path,
                layer_name=normalized_name,
                geometry_type=QgsWkbTypes.Point,
                crs=reference_layer.crs(),
                fields=WorksTempLayerHelper._build_fields(),
                overwrite=False,
            )
            if not created:
                return None, "Could not create the layer inside the GeoPackage"

            loaded = GPKGHelpers.load_layer_from_gpkg(
                gpkg_path,
                normalized_name,
                group_name=MailablGroupFolders.SANDBOXING,
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
        fields.append(QgsField("Mailabl_id", QVariant.String))
        fields.append(QgsField("title", QVariant.String))
        fields.append(QgsField("description", QVariant.String))
        fields.append(QgsField("type", QVariant.String))
        fields.append(QgsField("priority", QVariant.String))
        fields.append(QgsField("responsible_team", QVariant.String))
        fields.append(QgsField("status", QVariant.Bool))
        fields.append(QgsField("active", QVariant.Bool))
        fields.append(QgsField("affected_properties", QVariant.Bool))
        fields.append(QgsField("datetime", QVariant.String))
        fields.append(QgsField("created_at", QVariant.String))
        fields.append(QgsField("updated_at", QVariant.String))
        return fields