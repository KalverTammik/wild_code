import gc
import os
from datetime import datetime
from typing import Optional, Tuple

from PyQt5.QtCore import QVariant
from qgis.core import (
    QgsField, QgsFields, QgsVectorFileWriter, QgsWkbTypes,
    QgsCoordinateReferenceSystem, QgsProject, QgsVectorLayer
)
from osgeo import ogr
from ...constants.file_paths import QmlPaths
from ...Logs.python_fail_logger import PythonFailLogger
from ..url_manager import Module

from ...engines.LayerCreationEngine import MailablGroupFolders


class LayerSchemas:
    @staticmethod
    def _extract_layer_schema(layer: QgsVectorLayer) -> Tuple[QgsFields, QgsWkbTypes.Type, QgsCoordinateReferenceSystem]:
        """
        Extracts the schema (fields, geometry type, CRS) from a given vector layer.

        Args:
            layer (QgsVectorLayer): The source layer.

        Returns:
            Tuple[QgsFields, QgsWkbTypes.Type, QgsCoordinateReferenceSystem]: 
                A tuple containing (fields, geometry_type, crs).
        """
        if not layer.isValid():
            raise ValueError("Layer is not valid.")

        fields = layer.fields()
        geometry_type = layer.wkbType()
        crs = layer.crs()

        return fields, geometry_type, crs



class GPKGHelpers:
    @staticmethod
    def gpkg_layer_exists(gpkg_path: str, layer_name: str) -> bool:
        normalized_path = os.path.abspath(str(gpkg_path or "").strip())
        if not normalized_path or not os.path.exists(normalized_path):
            return False

        try:
            ds = ogr.Open(normalized_path, 0)  # read-only
        except Exception:
            return False

        if not ds:
            return False

        try:
            return layer_name in [ds.GetLayerByIndex(i).GetName() for i in range(ds.GetLayerCount())]
        except Exception:
            return False
    @staticmethod
    def load_layer_from_gpkg(gpkg_path: str, layer_name: str, group_name: str = "") -> Optional[QgsVectorLayer]:
        """
        Safely loads a layer from a GeoPackage into the QGIS project and places it in a group if specified.
        """
        uri = f"{gpkg_path}|layername={layer_name}"
        layer = QgsVectorLayer(uri, layer_name, "ogr")

        if not layer.isValid():
            PythonFailLogger.log("gpkg_layer_load_failed", module=Module.PROPERTY.value, extra={"layer": layer_name})
            return None

        QgsProject.instance().addMapLayer(layer, False)

        if group_name:
            root = QgsProject.instance().layerTreeRoot()
            group = root.findGroup(group_name) or root.addGroup(group_name)
            group.addLayer(layer)  # ✅ This is safe
        else:
            QgsProject.instance().layerTreeRoot().insertLayer(0, layer)

        return layer
    @staticmethod
    def delete_layer_from_gpkg(gpkg_path: str, layer_name: str) -> bool:
        """
        Deletes a specific layer from a GeoPackage file using OGR,
        and removes it from the current QGIS project if loaded.

        Args:
            gpkg_path (str): Path to the GeoPackage.
            layer_name (str): Name of the layer to delete.

        Returns:
            bool: True if deletion from GPKG succeeded, False otherwise.
        """
        if not os.path.exists(gpkg_path):
            PythonFailLogger.log("gpkg_file_missing", module=Module.PROPERTY.value, extra={"layer": layer_name})
            return False

        # 🧹 First: remove from project if loaded
        project_layers = QgsProject.instance().mapLayersByName(layer_name)
        if project_layers:
            for lyr in project_layers:
                QgsProject.instance().removeMapLayer(lyr.id())

        # 🧹 Then: remove from GeoPackage
        ds = ogr.Open(gpkg_path, update=1)
        if not ds:
            PythonFailLogger.log("gpkg_open_failed", module=Module.PROPERTY.value, extra={"layer": layer_name})
            return False

        try:
            layer_index = next(
                (
                    index
                    for index in range(ds.GetLayerCount())
                    if ds.GetLayerByIndex(index).GetName() == layer_name
                ),
                -1,
            )
            if layer_index < 0:
                PythonFailLogger.log("gpkg_layer_missing", module=Module.PROPERTY.value, extra={"layer": layer_name})
                return False
            ds.DeleteLayer(layer_index)
            return True
        except Exception as e:
            PythonFailLogger.log_exception(e, module=Module.PROPERTY.value, event="gpkg_layer_delete_failed")
            return False

    @staticmethod
    def create_empty_gpkg_layer(
        gpkg_path: str,
        layer_name: str,
        geometry_type: QgsWkbTypes.Type,
        crs: QgsCoordinateReferenceSystem,
        fields: QgsFields,
        overwrite: bool = True,
        encoding: str = "UTF-8"
    ) -> bool:
        """
        Creates an empty vector layer in a GeoPackage.

        Args:
            gpkg_path (str): Path to the GeoPackage file.
            layer_name (str): Name of the new layer.
            geometry_type (QgsWkbTypes.Type): Geometry type (e.g., QgsWkbTypes.Polygon).
            crs (QgsCoordinateReferenceSystem): Coordinate reference system.
            fields (QgsFields): Field definitions for the new layer.
            overwrite (bool): Whether to overwrite an existing layer of the same name.
            encoding (str): File encoding (default: UTF-8).

        Returns:
            bool: True if successful, False otherwise.
        """
        normalized_path = os.path.abspath(str(gpkg_path or "").strip())

        parent_dir = os.path.dirname(normalized_path)
        if parent_dir:
            os.makedirs(parent_dir, exist_ok=True)

        options = QgsVectorFileWriter.SaveVectorOptions()
        options.driverName = "GPKG"
        options.layerName = layer_name
        options.fileEncoding = encoding
        create_or_overwrite_file = getattr(
            QgsVectorFileWriter,
            "CreateOrOverwriteFile",
            QgsVectorFileWriter.CreateOrOverwriteLayer,
        )
        options.actionOnExistingFile = (
            QgsVectorFileWriter.CreateOrOverwriteLayer
            if os.path.exists(normalized_path) and not overwrite
            else create_or_overwrite_file
        )
        transform_context = QgsProject.instance().transformContext()

        writer = QgsVectorFileWriter.create(
            normalized_path,
            fields,
            geometry_type,
            crs,
            transform_context,
            options
        )

        try:
            ok = bool(writer is not None and int(writer.hasError()) == int(QgsVectorFileWriter.NoError))
            if ok:
                return True
            try:
                msg = writer.errorMessage() if writer is not None else ""
            except Exception:
                msg = ""
            PythonFailLogger.log("gpkg_layer_create_failed", module=Module.PROPERTY.value, extra={"layer": layer_name, "error": msg})
            return False
        finally:
            try:
                del writer
            except Exception as e:
                PythonFailLogger.log_exception(e, module=Module.PROPERTY.value, event="gpkg_writer_release_failed")


class ArchiveLayerHandler:
    ARCHIVE_DATE_FIELD = "backup_date"

    @staticmethod
    def archive_fields_for_layer(source_layer: QgsVectorLayer) -> QgsFields:
        fields, _geometry_type, _crs = LayerSchemas._extract_layer_schema(source_layer)
        archive_fields = QgsFields()
        for field in fields:
            archive_fields.append(QgsField(field))

        existing_names = {field.name().strip().lower() for field in archive_fields}
        if ArchiveLayerHandler.ARCHIVE_DATE_FIELD.lower() not in existing_names:
            archive_fields.append(
                QgsField(ArchiveLayerHandler.ARCHIVE_DATE_FIELD, QVariant.String, len=16)
            )
        return archive_fields

    @staticmethod
    def current_archive_timestamp() -> str:
        return datetime.now().astimezone().strftime("%Y-%m-%d %H:%M")

    @staticmethod
    def resolve_or_create_archive_layer(source_layer: QgsVectorLayer, archive_layer_name: str) -> Optional[QgsVectorLayer]:
        """
        Ensures the archive layer exists (in project or GPKG). Loads or creates it as needed.

        Args:
            source_layer (QgsVectorLayer): The reference layer used to copy schema if creation is needed.
            archive_layer_name (str): The name of the archive layer.

        Returns:
            QgsVectorLayer or None if failed.
        """
        # 1. Check if it's already in project
        existing = QgsProject.instance().mapLayersByName(archive_layer_name)
        if existing:
            return existing[0]

        # 2. Check in GPKG
        uri = source_layer.dataProvider().dataSourceUri()
        gpkg_path = uri.split("|")[0]

        if GPKGHelpers.gpkg_layer_exists(gpkg_path, archive_layer_name):
            return GPKGHelpers.load_layer_from_gpkg(gpkg_path, archive_layer_name, group_name=MailablGroupFolders.ARCHIVE)

        # 3. Create new layer in GPKG
        archive_fields = ArchiveLayerHandler.archive_fields_for_layer(source_layer)

        created = GPKGHelpers.create_empty_gpkg_layer(
            gpkg_path=gpkg_path,
            layer_name=archive_layer_name,
            geometry_type=source_layer.wkbType(),
            crs=source_layer.crs(),
            fields=archive_fields,
            overwrite=False
        )

        if not created:
            PythonFailLogger.log("archive_layer_create_failed", module=Module.PROPERTY.value, extra={"layer": archive_layer_name})
            return None

        new_layer = GPKGHelpers.load_layer_from_gpkg(gpkg_path, archive_layer_name, group_name=MailablGroupFolders.ARCHIVE)
        if new_layer is not None:
            try:
                style_path = QmlPaths.PROPERTIES_ARCHIVED
                new_layer.loadNamedStyle(style_path)
            except Exception as e:
                PythonFailLogger.log_exception(e, module=Module.PROPERTY.value, event="archive_layer_style_failed")
        gc.collect()
        return new_layer
