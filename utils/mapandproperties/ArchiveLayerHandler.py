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
    def get_layer_uri(target_layer_for_file: QgsVectorLayer, new_layer_name: str):
        uri = target_layer_for_file.dataProvider().dataSourceUri()
        gpkg_path = uri.split("|")[0]
        layer_uri = f"{gpkg_path}|layername={new_layer_name}"
        print("URI:", uri)
        print("GPKG Path:", gpkg_path)
        return layer_uri, gpkg_path
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
            print(f"❌ Failed to load layer '{layer_name}' from {gpkg_path}")
            return None

        QgsProject.instance().addMapLayer(layer, False)

        if group_name:
            root = QgsProject.instance().layerTreeRoot()
            group = root.findGroup(group_name) or root.addGroup(group_name)
            group.addLayer(layer)  # ✅ This is safe
            print(f"✅ Layer '{layer_name}' loaded into group '{group_name}'")
        else:
            QgsProject.instance().layerTreeRoot().insertLayer(0, layer)
            print(f"✅ Layer '{layer_name}' loaded at top level.")

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
        print(f"🧹 Attempting to delete layer '{layer_name}' from GeoPackage: {gpkg_path}")

        if not os.path.exists(gpkg_path):
            print("❌ GeoPackage file not found.")
            return False

        # 🧹 First: remove from project if loaded
        project_layers = QgsProject.instance().mapLayersByName(layer_name)
        if project_layers:
            for lyr in project_layers:
                QgsProject.instance().removeMapLayer(lyr.id())
            print(f"✅ Removed '{layer_name}' from project.")

        # 🧹 Then: remove from GeoPackage
        ds = ogr.Open(gpkg_path, update=1)
        if not ds:
            print("❌ Failed to open GeoPackage.")
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
                print(f"❌ Layer '{layer_name}' was not found in the GeoPackage.")
                return False
            ds.DeleteLayer(layer_index)
            print(f"✅ Layer '{layer_name}' deleted from GeoPackage.")
            return True
        except Exception as e:
            print(f"❌ Error deleting layer '{layer_name}' from GeoPackage: {e}")
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
        print(f"🆕 Creating empty GPKG layer '{layer_name}' at: {normalized_path}")

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
                print(f"✅ Empty layer '{layer_name}' created successfully.")
                return True
            try:
                msg = writer.errorMessage() if writer is not None else ""
            except Exception:
                msg = ""
            print(f"❌ Failed to create layer '{layer_name}': {msg}")
            return False
        finally:
            try:
                del writer
            except Exception as e:
                print(f"⚠️ Failed to release writer: {e}")


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
        print(f"📦 Resolving archive layer: {archive_layer_name}")

        # 1. Check if it's already in project
        existing = QgsProject.instance().mapLayersByName(archive_layer_name)
        if existing:
            print(f"✅ Found archive layer in project.")
            return existing[0]

        # 2. Check in GPKG
        uri = source_layer.dataProvider().dataSourceUri()
        gpkg_path = uri.split("|")[0]

        if GPKGHelpers.gpkg_layer_exists(gpkg_path, archive_layer_name):
            print("✅ Layer exists in GPKG — loading it.")
            return GPKGHelpers.load_layer_from_gpkg(gpkg_path, archive_layer_name, group_name=MailablGroupFolders.ARCHIVE)

        # 3. Create new layer in GPKG
        print("⚠️ Archive layer not found — creating new one.")
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
            print("❌ Failed to create archive layer.")
            return None

        print("✅ New archive layer created. Adding to project.")
        new_layer = GPKGHelpers.load_layer_from_gpkg(gpkg_path, archive_layer_name, group_name=MailablGroupFolders.ARCHIVE)
        if new_layer is not None:
            try:
                style_path = QmlPaths.PROPERTIES_ARCHIVED
                new_layer.loadNamedStyle(style_path)
            except Exception as e:
                print(f"⚠️ Failed to apply archived style: {e}")
        gc.collect()
        return new_layer
