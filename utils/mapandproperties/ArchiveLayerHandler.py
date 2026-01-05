import gc
import os
from typing import Optional, Tuple

from qgis.core import (
    QgsFields, QgsVectorFileWriter, QgsWkbTypes,
    QgsCoordinateReferenceSystem, QgsProject, QgsVectorLayer
)
from osgeo import ogr
from ...constants.file_paths import QmlPaths

from ...engines.LayerCreationEngine import MailablGroupFolders


def _safe_layer_edit_commit(layer: QgsVectorLayer) -> tuple[bool, str]:
    try:
        ok = bool(layer.commitChanges())
        if ok:
            return True, ""
        try:
            err = "; ".join(layer.commitErrors() or [])
        except Exception:
            err = ""
        return False, err
    except Exception as e:
        return False, str(e)


def _layer_rollback_error(layer: QgsVectorLayer) -> str:
    """Attempt rollback; return empty string on success, otherwise error message."""

    try:
        layer.rollBack()
        return ""
    except Exception as e:
        return str(e)


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
        ds = ogr.Open(gpkg_path, 0)  # read-only
        if not ds:
            return False
        return layer_name in [ds.GetLayerByIndex(i).GetName() for i in range(ds.GetLayerCount())]
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
            ds.DeleteLayer(layer_name)
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
        print(f"🆕 Creating empty GPKG layer '{layer_name}' at: {gpkg_path}")

        options = QgsVectorFileWriter.SaveVectorOptions()
        options.driverName = "GPKG"
        options.layerName = layer_name
        options.fileEncoding = encoding
        options.actionOnExistingFile = QgsVectorFileWriter.CreateOrOverwriteLayer
        transform_context = QgsProject.instance().transformContext()

        writer = QgsVectorFileWriter.create(
            gpkg_path,
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
        fields, geometry_type, crs = LayerSchemas._extract_layer_schema(source_layer)

        created = GPKGHelpers.create_empty_gpkg_layer(
            gpkg_path=gpkg_path,
            layer_name=archive_layer_name,
            geometry_type=geometry_type,
            crs=crs,
            fields=fields,
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

    @staticmethod
    def archive_features_by_field_values(
        source_layer: QgsVectorLayer,
        *,
        archive_layer_name: str = "Archive_Layer",
        field_name: str,
        values: list[str],
        delete_from_source: bool = True,
        add_to_archive_group: bool = True,
    ) -> dict:
        """Copy matching features from `source_layer` into an archive GPKG layer.

        Intended as the map-side counterpart to backend archiving.

        Returns a summary dict:
        {
            "ok": bool,
            "archived": int,
            "deleted": int,
            "missing": list[str],
            "errors": list[str],
            "archive_layer": str,
        }
        """

        values = [str(v).strip() for v in (values or []) if str(v).strip()]
        if source_layer is None or not source_layer.isValid():
            return {
                "ok": False,
                "archived": 0,
                "deleted": 0,
                "missing": values,
                "errors": ["source layer missing/invalid"],
                "archive_layer": archive_layer_name,
            }

        if not values:
            return {
                "ok": True,
                "archived": 0,
                "deleted": 0,
                "missing": [],
                "errors": [],
                "archive_layer": archive_layer_name,
            }

        archive_layer = ArchiveLayerHandler.resolve_or_create_archive_layer(source_layer, archive_layer_name)
        if archive_layer is None or not archive_layer.isValid():
            return {
                "ok": False,
                "archived": 0,
                "deleted": 0,
                "missing": values,
                "errors": ["archive layer could not be resolved/created"],
                "archive_layer": archive_layer_name,
            }

        # Optionally ensure it's placed under archive group (even if it existed already).
        if add_to_archive_group:
            try:
                root = QgsProject.instance().layerTreeRoot()
                group = root.findGroup(MailablGroupFolders.ARCHIVE) or root.addGroup(MailablGroupFolders.ARCHIVE)
                # Avoid duplicating if already present.
                if root.findLayer(archive_layer.id()) is None:
                    group.addLayer(archive_layer)
            except Exception as e:
                # Non-fatal; layer may already be in the tree or group ops might fail.
                print(f"⚠️ Failed to add archive layer to group: {e}")

        archived_count = 0
        deleted_count = 0
        missing: list[str] = []
        errors: list[str] = []

        try:
            source_features = list(source_layer.getFeatures())
        except Exception:
            source_features = []

        # Build lookup of source features by field value.
        source_features_by_value: dict[str, object] = {}
        for v in values:
            found = None
            for f in source_features:
                try:
                    if str(f.attribute(field_name)).strip() == v:
                        found = f
                        break
                except Exception:
                    continue

            if found is None:
                missing.append(v)
            else:
                source_features_by_value[v] = found

        if not source_features_by_value:
            return {
                "ok": True,
                "archived": 0,
                "deleted": 0,
                "missing": missing,
                "errors": [],
                "archive_layer": archive_layer.name() if archive_layer else archive_layer_name,
            }

        # Prepare archive features.
        archive_fields = archive_layer.fields()
        try:
            pk_indexes = list(archive_layer.dataProvider().pkAttributeIndexes() or [])
        except Exception:
            pk_indexes = []

        if not pk_indexes:
            # Fallback for common GPKG/OGR conventions.
            name_to_idx = {}
            for i in range(archive_fields.count()):
                try:
                    name_to_idx[str(archive_fields.field(i).name()).strip().lower()] = int(i)
                except Exception:
                    continue
            for candidate in ("fid", "id"):
                if candidate in name_to_idx:
                    pk_indexes = [name_to_idx[candidate]]
                    break

        features_to_add = []
        source_ids_to_delete = []

        for v, src_feat in source_features_by_value.items():
            try:
                from qgis.core import QgsFeature

                new_feat = QgsFeature(archive_fields)
                new_feat.setGeometry(src_feat.geometry())

                # Try direct attribute copy when schemas match.
                try:
                    new_feat.setAttributes(src_feat.attributes())
                except Exception:
                    # Map attributes by field name.
                    attrs = []
                    for i in range(archive_fields.count()):
                        fname = archive_fields.field(i).name()
                        try:
                            attrs.append(src_feat.attribute(fname))
                        except Exception:
                            attrs.append(None)
                    new_feat.setAttributes(attrs)

                # Critical: never carry over PK values (e.g. fid) into the archive layer.
                # Otherwise GeoPackage will fail with UNIQUE constraint errors.
                for pk_idx in pk_indexes:
                    try:
                        new_feat.setAttribute(int(pk_idx), None)
                    except Exception:
                        continue

                features_to_add.append(new_feat)
                try:
                    source_ids_to_delete.append(int(src_feat.id()))
                except Exception as e:
                    errors.append(f"failed to read source feature id for {v}: {e}")
            except Exception as e:
                errors.append(f"failed to prepare feature for {v}: {e}")

        if not features_to_add:
            return {
                "ok": False,
                "archived": 0,
                "deleted": 0,
                "missing": missing,
                "errors": errors or ["no features prepared"],
                "archive_layer": archive_layer.name() if archive_layer else archive_layer_name,
            }

        # Write to archive layer first.
        try:
            if not archive_layer.isEditable():
                archive_layer.startEditing()
            ok_add = bool(archive_layer.addFeatures(features_to_add))
            if not ok_add:
                errors.append("archive_layer.addFeatures() failed")
                rb_err = _layer_rollback_error(archive_layer)
                if rb_err:
                    errors.append(f"archive rollback failed: {rb_err}")
                return {
                    "ok": False,
                    "archived": 0,
                    "deleted": 0,
                    "missing": missing,
                    "errors": errors,
                    "archive_layer": archive_layer.name() if archive_layer else archive_layer_name,
                }

            ok_commit, commit_err = _safe_layer_edit_commit(archive_layer)
            if not ok_commit:
                if commit_err:
                    errors.append(f"archive commit failed: {commit_err}")
                rb_err = _layer_rollback_error(archive_layer)
                if rb_err:
                    errors.append(f"archive rollback failed: {rb_err}")
                return {
                    "ok": False,
                    "archived": 0,
                    "deleted": 0,
                    "missing": missing,
                    "errors": errors,
                    "archive_layer": archive_layer.name() if archive_layer else archive_layer_name,
                }

            archived_count = len(features_to_add)
        except Exception as e:
            errors.append(f"archive write exception: {e}")
            rb_err = _layer_rollback_error(archive_layer)
            if rb_err:
                errors.append(f"archive rollback failed: {rb_err}")
            return {
                "ok": False,
                "archived": 0,
                "deleted": 0,
                "missing": missing,
                "errors": errors,
                "archive_layer": archive_layer.name() if archive_layer else archive_layer_name,
            }

        # Delete from source layer after successful archive.
        if delete_from_source and source_ids_to_delete:
            try:
                if not source_layer.isEditable():
                    source_layer.startEditing()
                ok_del = bool(source_layer.deleteFeatures(source_ids_to_delete))
                if not ok_del:
                    errors.append("source_layer.deleteFeatures() failed")
                    rb_err = _layer_rollback_error(source_layer)
                    if rb_err:
                        errors.append(f"source rollback failed: {rb_err}")
                else:
                    ok_commit, commit_err = _safe_layer_edit_commit(source_layer)
                    if not ok_commit:
                        if commit_err:
                            errors.append(f"source commit failed: {commit_err}")
                        rb_err = _layer_rollback_error(source_layer)
                        if rb_err:
                            errors.append(f"source rollback failed: {rb_err}")
                    else:
                        deleted_count = len(source_ids_to_delete)
            except Exception as e:
                errors.append(f"source delete exception: {e}")
                rb_err = _layer_rollback_error(source_layer)
                if rb_err:
                    errors.append(f"source rollback failed: {rb_err}")

        return {
            "ok": bool(archived_count > 0 and (not delete_from_source or deleted_count == archived_count)),
            "archived": archived_count,
            "deleted": deleted_count,
            "missing": missing,
            "errors": errors,
            "archive_layer": archive_layer.name() if archive_layer else archive_layer_name,
        }
