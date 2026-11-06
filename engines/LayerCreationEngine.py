#!/usr/bin/env python3
"""
Layer Creation Engine for Mailabl QGIS Plugin

This engine provides comprehensive layer management services including:
- Memory layer creation and management
- GeoPackage persistence
- Layer group organization
- Virtual layer copying for properties

"""

import os
from typing import Optional
from qgis.core import (
    QgsProject,
    QgsVectorLayer,
    QgsLayerTreeGroup,
    QgsCoordinateReferenceSystem,
    QgsFields,
    Qgis,
)
from qgis.PyQt.QtWidgets import QWidget
from qgis.PyQt.QtCore import QTimer, QCoreApplication
from qgis.PyQt.QtXml import QDomDocument

# Local imports
from ..constants.file_paths import QmlPaths

from ..constants.layer_constants import DEFAULT_CRS
# Prefer module-level imports for clarity. Kept here to avoid accidental circular imports when possible.
from ..widgets.ProgressDialogModern import ProgressDialogModern

# Global layer engine instance
_layer_engine_instance = None

class MailablGroupFolders:
    """Standard group folder names for Mailabl plugin."""

    MAILABL_MAIN = "Mailabl settings"
    NEW_PROPERTIES = "Uued kinnistud"
    SANDBOXING = "Ajutised kihid"
    ARCHIVE = "Arhiiv"
    IMPORT = "Imporditavad kinnistud"  # Updated to Estonian name
    EXPORT = "Eksport"
    SYNC = "Sünkroonimine"




class LayerCreationEngine:
    """
    Main engine for layer creation and management operations.

    Provides services for:
    - Creating memory layers from templates
    - Managing layer groups
    - Persisting layers to GeoPackage
    - Copying virtual layers for properties
    - Importing Shapefile data to memory layers with batch processing
    """

    def __init__(self):
        """
        Initialize the LayerCreationEngine.

        Sets up project and layer tree references, and initializes language manager for translations.
        """
        self.project = QgsProject.instance()
        self.layer_tree_root = self.project.layerTreeRoot()
        # Initialize language manager for translations
        # Inline import used because LanguageManager is optional functionality that may not be available
        try:
            from ..languages.language_manager import LanguageManager
            self.lang_manager = LanguageManager()
        except ImportError:
            self.lang_manager = None

    def get_or_create_group(self, group_name: str) -> QgsLayerTreeGroup:
        """
        Get existing group or create new one.

        Args:
            group_name: Name of the group to retrieve/create

        Returns:
            QgsLayerTreeGroup: The group object
        """
        # Try to find existing group
        existing_group = self.layer_tree_root.findGroup(group_name)
        if existing_group:
            return existing_group

        # Create new group
        new_group = self.layer_tree_root.addGroup(group_name)

        # If this is the MailablMain group, initialize its structure
        if group_name == MailablGroupFolders.MAILABL_MAIN:
            self.initialize_mailabl_main_structure()

        return new_group

    def get_or_create_subgroup(self, parent_group: QgsLayerTreeGroup, subgroup_name: str) -> QgsLayerTreeGroup:
        """
        Get existing subgroup or create new one within a parent group.

        Args:
            parent_group: Parent group to create subgroup in
            subgroup_name: Name of the subgroup to retrieve/create

        Returns:
            QgsLayerTreeGroup: The subgroup object
        """
        # Try to find existing subgroup
        existing_subgroup = parent_group.findGroup(subgroup_name)
        if existing_subgroup:
            return existing_subgroup

        # Create new subgroup
        new_subgroup = parent_group.addGroup(subgroup_name)
        return new_subgroup

    def initialize_mailabl_main_structure(self) -> bool:
        """
        Initialize the complete MailablMain group structure with all required subgroups.

        Returns:
            bool: True if successful
        """
        # Get or create main group
        main_group = self.get_or_create_group(MailablGroupFolders.MAILABL_MAIN)

        # Define all required subgroups
        subgroups = [
            MailablGroupFolders.NEW_PROPERTIES,
            MailablGroupFolders.SANDBOXING,
            MailablGroupFolders.IMPORT,
            MailablGroupFolders.SYNC,
            MailablGroupFolders.ARCHIVE
        ]

        # Create all subgroups
        for subgroup_name in subgroups:
            self.get_or_create_subgroup(main_group, subgroup_name)

        return True

    def ensure_mailabl_structure_exists(self) -> bool:
        """
        Ensure the complete Mailabl structure exists, creating it if necessary.

        Returns:
            bool: True if structure exists or was created successfully
        """
        main_group = self.layer_tree_root.findGroup(MailablGroupFolders.MAILABL_MAIN)
        if not main_group:
            return self.initialize_mailabl_main_structure()

        # Check if all required subgroups exist
        required_subgroups = [
            MailablGroupFolders.NEW_PROPERTIES,
            MailablGroupFolders.SANDBOXING,
            MailablGroupFolders.IMPORT,
            MailablGroupFolders.SYNC,
            MailablGroupFolders.ARCHIVE
        ]

        missing_subgroups = []
        for subgroup_name in required_subgroups:
            if not main_group.findGroup(subgroup_name):
                missing_subgroups.append(subgroup_name)

        # Create any missing subgroups
        for subgroup_name in missing_subgroups:
            self.get_or_create_subgroup(main_group, subgroup_name)

        return True

    def create_memory_layer_from_template(
        self,
        layer_name: str,
        template_layer: Optional[QgsVectorLayer] = None,
        fields: Optional[QgsFields] = None,
        crs: Optional[QgsCoordinateReferenceSystem] = None,
        geometry_type: str = "Point"
    ) -> Optional[QgsVectorLayer]:
        """
        Create a memory layer from template or specifications.

        Args:
            layer_name: Name for the new layer
            template_layer: Optional template layer to copy from
            fields: Optional fields specification
            crs: Optional CRS specification
            geometry_type: Geometry type if no template

        Returns:
            Optional[QgsVectorLayer]: Created memory layer or None if failed
        """
        # Remove existing layer with same name if it exists
        existing_layer = self.project.mapLayersByName(layer_name)
        for layer in existing_layer:
            if layer.providerType() == 'memory':
                self.project.removeMapLayer(layer.id())

        # Create URI for memory layer
        if template_layer:
            # Create memory layer with proper URI, not template's file URI
            geometry_type = self._get_geometry_type_string(template_layer.geometryType())
            uri = f"{geometry_type}?crs={template_layer.crs().authid()}"
            new_layer = QgsVectorLayer(uri, layer_name, 'memory')

            # Copy fields from template
            if template_layer.fields():
                # Use data provider to set fields for memory layer
                new_layer.dataProvider().addAttributes(template_layer.fields())
                new_layer.updateFields()
            if template_layer.crs():
                new_layer.setCrs(template_layer.crs())

        else:
            # Create from specifications
            uri = f"{geometry_type}?crs={crs.authid() if crs else DEFAULT_CRS}"
            new_layer = QgsVectorLayer(uri, layer_name, 'memory')

            if fields:
                new_layer.dataProvider().addAttributes(fields)
                new_layer.updateFields()

        if not new_layer.isValid():
            return None

        # Add to project
        self.project.addMapLayer(new_layer, False)  # Don't add to legend yet
        return new_layer

    def _get_geometry_type_string(self, geometry_type: Qgis.GeometryType) -> str:
        """
        Convert QGIS geometry type to string for memory layer URI.

        Args:
            geometry_type: QGIS geometry type enum

        Returns:
            str: Geometry type string for URI
        """
        type_map = {
            Qgis.GeometryType.Point: "Point",
            Qgis.GeometryType.Line: "LineString",
            Qgis.GeometryType.Polygon: "Polygon",
            Qgis.GeometryType.Null: "Point",  # Default fallback
        }
        return type_map.get(geometry_type, "Point")

    def copy_virtual_layer_for_properties(
        self,
        new_layer_name: str,
        group_name: str,
        template_layer: Optional[QgsVectorLayer] = None
    ) -> Optional[str]:
        """
        Create a virtual copy of a layer for property operations.

        Args:
            new_layer_name: Name for the new layer
            group_name: Target group name (can be main group or subgroup)
            template_layer: Optional template layer

        Returns:
            Optional[str]: Name of created layer or None if failed
        """
        # Check if the requested group is one of the Mailabl subgroups
        mailabl_subgroups = [
            MailablGroupFolders.NEW_PROPERTIES,
            MailablGroupFolders.SANDBOXING,
            MailablGroupFolders.IMPORT,
            MailablGroupFolders.SYNC,
            MailablGroupFolders.ARCHIVE
        ]

        if group_name in mailabl_subgroups:
            # This is a Mailabl subgroup - ensure the main structure exists
            self.ensure_mailabl_structure_exists()
            main_group = self.layer_tree_root.findGroup(MailablGroupFolders.MAILABL_MAIN)
            subgroup = main_group.findGroup(group_name)
            if subgroup:
                group = subgroup
            else:
                # This shouldn't happen if ensure_mailabl_structure_exists worked
                group = self.get_or_create_subgroup(main_group, group_name)
        else:
            # Check if this is the main group itself
            if group_name == MailablGroupFolders.MAILABL_MAIN:
                group = self.get_or_create_group(group_name)
            else:
                # Create as a top-level group
                group = self.get_or_create_group(group_name)

        # Create memory layer
        memory_layer = self.create_memory_layer_from_template(
            new_layer_name, template_layer
        )
        print(f"[LayerCreationEngine] Created memory layer: {memory_layer}")
        if not memory_layer:
            return None

        # Add to group
        group.addLayer(memory_layer)

        # Apply default QML style for property layers
        self.apply_qml_style(memory_layer, QmlPaths.MAAMET_IMPORT)

        return memory_layer

    def apply_qml_style(self, layer: QgsVectorLayer, style_name) -> bool:
        """
        Apply QML style to a layer using the plugin's standard approach.

        Args:
            layer: The layer to apply style to
            style_name: Name of the style to apply (default: properties_background_new)

        Returns:
            bool: True if style was applied successfully, False otherwise
        """
        # Get the QML style file path
        qml_path = style_name

        if not os.path.exists(qml_path):
            return False

        # Ensure layer is not in editing mode
        if layer.isEditable():
            layer.commitChanges()

        # Apply the QML style
        result = layer.loadNamedStyle(qml_path)

        if not result:
            # If loadNamedStyle failed, try importNamedStyle with QDomDocument
            try:
                with open(qml_path, 'r', encoding='utf-8') as f:
                    qml_content = f.read()
                doc = QDomDocument()
                if doc.setContent(qml_content):
                    result = layer.importNamedStyle(doc)
                else:
                    result = False
            except (IOError, OSError):
                result = False

        if result:
            # Refresh the layer and map canvas
            layer.triggerRepaint()

            # Inline import used because iface is only available when QGIS GUI is running
            from qgis.utils import iface
            if iface and iface.mapCanvas():
                iface.mapCanvas().refresh()

            return True
        else:
            return False

    def import_shapefile_to_memory_layer(
        self,
        shp_layer: QgsVectorLayer,
        layer_name: str,
        group_name: str,
        parent_widget: Optional['QWidget'] = None,
        batch_size: Optional[int] = None,
        progress_update_interval: Optional[int] = None,
    ) -> Optional[QgsVectorLayer]:
        """
        Import Shapefile data to a new memory layer with optimized batch processing.

        Args:
            shp_layer: Source Shapefile layer
            layer_name: Name for the new memory layer
            group_name: Target group name
            parent_widget: Optional parent widget for progress dialog

        Returns:
            Optional[QgsVectorLayer]: Created memory layer or None if failed
        """
        memory_layer_name = f"{layer_name}_memory"

        print(f"[LayerCreationEngine] Import start: layer={layer_name}, group={group_name}")

        # Create memory layer with correct structure using existing method
        result = self.copy_virtual_layer_for_properties(
            memory_layer_name,
            group_name,
            shp_layer
        )
        print(f"[LayerCreationEngine] Memory layer creation result: {result}")
        if result== None:
            return None

        # Get the created memory layer
        memory_layer = None
        for layer in self.project.mapLayers().values():
            if layer.name() == memory_layer_name:
                memory_layer = layer
                break

        if not memory_layer:
            return None

        # Validate it's a memory layer
        if memory_layer.providerType() != "memory":
            return None

        # Get total feature count
        total_features = shp_layer.featureCount()

        print(f"[LayerCreationEngine] Source features: {total_features}")

        if total_features == 0:
            # No features to import, just finalize
            memory_layer.updateExtents()
            return memory_layer

        # Create progress dialog
        progress = None
        progress_title = "Importing Shapefile" 
        progress = ProgressDialogModern(
            title=progress_title,
            maximum=total_features,
            parent=parent_widget,
        )
        progress.show()
        print("[LayerCreationEngine] Progress dialog created")
        # Get data provider for batch operations
        provider = memory_layer.dataProvider()
        if not provider:
            print("[LayerCreationEngine] No data provider for memory layer")
            return None

        # Disable undo stack for bulk operations (still useful for memory management)
        original_undo_stack = memory_layer.undoStack()
        if original_undo_stack:
            memory_layer.setUndoStack(None)

        # For memory layers, we don't need edit mode since we use provider.addFeatures() directly

        # Batch processing setup - configurable for different environments
        batch_size = batch_size if batch_size and batch_size > 0 else 5000
        features_added = 0
        progress_update_interval = progress_update_interval if progress_update_interval and progress_update_interval > 0 else 2000

        print(f"[LayerCreationEngine] Using batch_size={batch_size}, progress_interval={progress_update_interval}")

        # Disable signals during bulk operations for maximum performance
        memory_layer.blockSignals(True)
        try:
            features_batch = []

            for i, feature in enumerate(shp_layer.getFeatures()):
                features_batch.append(feature)

                # Process batch when it reaches the limit
                if len(features_batch) >= batch_size:
                    success = provider.addFeatures(features_batch)
                    if success:
                        features_added += len(features_batch)
                        features_batch.clear()  # More efficient than reassigning []
                    else:
                        print(f"Error: Failed to add features batch of size {len(features_batch)}")
                        memory_layer.blockSignals(False)  # Re-enable signals on error
                        return None

                # Update progress very infrequently to minimize overhead
                if i % progress_update_interval == 0 or i == total_features - 1:
                    if progress:
                        progress_pct = int((i + 1) / total_features * 100)
                        progress.update(
                            value=i + 1,
                            text1=f"Processing features: {i + 1}/{total_features} ({progress_pct}%)",
                            text2=f"Features copied: {features_added}"
                        )
                        QCoreApplication.processEvents()

            # Flush remaining features
            if features_batch:
                success = provider.addFeatures(features_batch)
                if not success:
                    print(f"Error: Failed to flush final features batch of size {len(features_batch)}")
                    memory_layer.blockSignals(False)  # Re-enable signals on error
                    return None
                features_added += len(features_batch)

            print(f"[LayerCreationEngine] Features imported: {features_added}")

            # Update progress to indicate finalization (reuse progress UI instead of a separate dialog)
            if progress:
                final_touches_text = "Adding final touches..." if not self.lang_manager else \
                    (self.lang_manager.translate("Adding final touches...") or "Adding final touches...")
                progress.update(
                    value=total_features,
                    text1=final_touches_text,
                    text2=f"Features copied: {features_added}"
                )
                QCoreApplication.processEvents()

            memory_layer.updateExtents()

            provider.createSpatialIndex()

            style_path = QmlPaths.MAAMET_IMPORT
            memory_layer.loadNamedStyle(style_path)
            print(f"[LayerCreationEngine] Style applied: {style_path}")

            if progress:
                complete_text = "Import complete!" if not self.lang_manager else \
                    (self.lang_manager.translate("Import complete!") or "Import complete!")
                progress.update(
                    value=total_features,
                    text1=complete_text,
                    text2=f"{features_added} features imported"
                )
                # Close progress after a short delay to let user see the final state
                QTimer.singleShot(1200, lambda: progress.close())

            # Restore undo stack
            if original_undo_stack:
                try:
                    memory_layer.setUndoStack(original_undo_stack)
                    print("Undo stack restored successfully")
                except Exception as e:
                    print(f"Warning: Failed to restore undo stack: {e}")

            return memory_layer

        except Exception as e:
            print(f"Unexpected error during Shapefile import: {e}")
            import traceback
            traceback.print_exc()
            # Close any open progress dialog on unexpected error
            if progress:
                progress.close()
            return None
        finally:
            # Always restore signals and undo stack
            memory_layer.blockSignals(False)
            if original_undo_stack:
                memory_layer.setUndoStack(original_undo_stack)
            if progress:
                progress.close()

def get_layer_engine() -> LayerCreationEngine:
    """
    Get the global singleton instance of LayerCreationEngine.

    Returns:
        LayerCreationEngine: The global layer engine instance
    """
    global _layer_engine_instance
    if _layer_engine_instance is None:
        _layer_engine_instance = LayerCreationEngine()
    return _layer_engine_instance
