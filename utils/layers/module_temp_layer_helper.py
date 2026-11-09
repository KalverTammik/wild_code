"""A module's temporary layer in a GeoPackage: where the file goes, finding the layer again, creating it."""
from __future__ import annotations

import os
from typing import Optional

from qgis.core import QgsFields, QgsProject, QgsVectorLayer, QgsWkbTypes

from ...constants.settings_keys import SettingsService
from ...engines.LayerCreationEngine import MailablGroupFolders
from ...Logs.python_fail_logger import PythonFailLogger
from ..MapTools.MapHelpers import MapHelpers
from ..mapandproperties.ArchiveLayerHandler import GPKGHelpers
from ..url_manager import Module


class ModuleTempLayerHelper:
    """A module names itself, its default layer and geometry below and supplies `_build_fields`."""

    MODULE: Module
    EVENT_PREFIX: str
    DEFAULT_LAYER_NAME: str
    GEOMETRY_TYPE: QgsWkbTypes.Type

    @staticmethod
    def _build_fields() -> QgsFields:
        raise NotImplementedError

    @classmethod
    def default_standalone_gpkg_path(
        cls,
        reference_layer: Optional[QgsVectorLayer],
        layer_name: str,
    ) -> str:
        reference_path = cls.gpkg_path_for_layer(reference_layer)
        if reference_path:
            base_dir = os.path.dirname(reference_path)
        else:
            base_dir = os.path.expanduser("~")

        safe_name = "".join(
            character if character not in '<>:"/\\|?*' else "_"
            for character in str(layer_name or "").strip()
        ).strip(" ._") or cls.DEFAULT_LAYER_NAME
        return os.path.join(base_dir, f"{safe_name}.gpkg")

    @staticmethod
    def _normalize_gpkg_path(gpkg_path: str) -> str:
        path = str(gpkg_path or "").strip()
        if not path:
            return ""

        if os.path.splitext(path)[1].lower() != ".gpkg":
            path = f"{path}.gpkg"

        return os.path.normcase(os.path.abspath(path))

    @classmethod
    def _find_loaded_layer(cls, layer_name: str, gpkg_path: str) -> Optional[QgsVectorLayer]:
        normalized_path = cls._normalize_gpkg_path(gpkg_path)
        if not normalized_path:
            return None

        for layer in QgsProject.instance().mapLayersByName(layer_name):
            if not isinstance(layer, QgsVectorLayer) or not layer.isValid():
                continue
            if cls._normalize_gpkg_path(cls.gpkg_path_for_layer(layer)) == normalized_path:
                return layer
        return None

    @classmethod
    def _remove_loaded_layers_for_gpkg(cls, gpkg_path: str) -> None:
        normalized_path = cls._normalize_gpkg_path(gpkg_path)
        if not normalized_path:
            return

        project = QgsProject.instance()
        for layer in list(project.mapLayers().values()):
            if not isinstance(layer, QgsVectorLayer) or not layer.isValid():
                continue
            layer_path = cls._normalize_gpkg_path(cls.gpkg_path_for_layer(layer))
            if layer_path == normalized_path:
                project.removeMapLayer(layer.id())

    @classmethod
    def resolve_reference_layer(cls, preferred_layer: Optional[QgsVectorLayer] = None) -> Optional[QgsVectorLayer]:
        preferred = preferred_layer if isinstance(preferred_layer, QgsVectorLayer) and preferred_layer.isValid() else None
        if cls.gpkg_path_for_layer(preferred):
            return preferred

        try:
            property_identifier = SettingsService().module_main_layer_name(Module.PROPERTY.value) or ""
            property_layer = MapHelpers.resolve_layer(property_identifier)
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module=cls.MODULE.value,
                event=f"{cls.EVENT_PREFIX}_temp_reference_layer_failed",
            )
            property_layer = None

        if isinstance(property_layer, QgsVectorLayer) and property_layer.isValid() and cls.gpkg_path_for_layer(property_layer):
            return property_layer
        return preferred or property_layer

    @classmethod
    def gpkg_path_for_layer(cls, layer: Optional[QgsVectorLayer]) -> str:
        if not isinstance(layer, QgsVectorLayer) or not layer.isValid():
            return ""
        try:
            uri = layer.dataProvider().dataSourceUri() or ""
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module=cls.MODULE.value,
                event=f"{cls.EVENT_PREFIX}_temp_reference_uri_failed",
            )
            return ""

        gpkg_path = (uri.split("|")[0] if uri else "").strip()
        if not gpkg_path or os.path.splitext(gpkg_path)[1].lower() != ".gpkg":
            return ""
        return gpkg_path

    @classmethod
    def create_or_load_layer(
        cls,
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

        target_gpkg_path = cls._normalize_gpkg_path(
            gpkg_path or cls.gpkg_path_for_layer(reference_layer)
        )
        if not target_gpkg_path:
            return None, "GeoPackage path is empty"

        existing_loaded = cls._find_loaded_layer(normalized_name, target_gpkg_path)
        if existing_loaded is not None and not overwrite_file:
            return existing_loaded, ""

        try:
            parent_dir = os.path.dirname(target_gpkg_path)
            if parent_dir:
                os.makedirs(parent_dir, exist_ok=True)

            if overwrite_file and os.path.exists(target_gpkg_path):
                cls._remove_loaded_layers_for_gpkg(target_gpkg_path)
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
                geometry_type=cls.GEOMETRY_TYPE,
                crs=reference_layer.crs(),
                fields=cls._build_fields(),
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
                module=cls.MODULE.value,
                event=f"{cls.EVENT_PREFIX}_temp_layer_create_failed",
                extra={"layer": normalized_name},
            )
            return None, str(exc)
