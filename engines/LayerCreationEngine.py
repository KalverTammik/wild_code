#!/usr/bin/env python3
"""
Layer Creation Engine for Mailabl QGIS Plugin

This engine provides comprehensive layer management services including:
- Memory layer creation and management
- GeoPackage persistence
- Layer group organization
- Virtual layer copying for properties

Author: Wild Code Plugin Team
Date: September 3, 2025
"""

import os
from typing import Optional, Dict, Any, List
from qgis.core import (
    QgsProject, QgsVectorLayer, QgsLayerTreeGroup,
    QgsVectorFileWriter, QgsCoordinateReferenceSystem, QgsFields,
    QgsFeature, QgsGeometry, Qgis
)
from qgis.PyQt.QtWidgets import QFileDialog, QMessageBox
from qgis.PyQt.QtCore import QTimer

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
    """

    def __init__(self):
        self.project = QgsProject.instance()
        self.layer_tree_root = self.project.layerTreeRoot()

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
        print(f"[LayerEngine] Created new group: {group_name}")

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
        print(f"[LayerEngine] Created subgroup '{subgroup_name}' in '{parent_group.name()}'")
        return new_subgroup

    def initialize_mailabl_main_structure(self) -> bool:
        """
        Initialize the complete MailablMain group structure with all required subgroups.

        Returns:
            bool: True if successful
        """
        try:
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

            print(f"[LayerEngine] Initialized MailablMain structure with {len(subgroups)} subgroups")
            return True

        except Exception as e:
            print(f"[LayerEngine] Error initializing MailablMain structure: {e}")
            return False

    def ensure_mailabl_structure_exists(self) -> bool:
        """
        Ensure the complete Mailabl structure exists, creating it if necessary.

        Returns:
            bool: True if structure exists or was created successfully
        """
        try:
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

            if missing_subgroups:
                print(f"[LayerEngine] Created missing subgroups: {missing_subgroups}")

            return True

        except Exception as e:
            print(f"[LayerEngine] Error ensuring Mailabl structure: {e}")
            return False

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
        try:
            # Remove existing layer with same name if it exists
            existing_layer = self.project.mapLayersByName(layer_name)
            for layer in existing_layer:
                if layer.providerType() == 'memory':
                    self.project.removeMapLayer(layer.id())
                    print(f"[LayerEngine] Removed existing memory layer: {layer_name}")

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
                uri = f"{geometry_type}?crs={crs.authid() if crs else 'EPSG:3301'}"
                new_layer = QgsVectorLayer(uri, layer_name, 'memory')

                if fields:
                    new_layer.dataProvider().addAttributes(fields)
                    new_layer.updateFields()

            if not new_layer.isValid():
                print(f"[LayerEngine] Failed to create valid memory layer: {layer_name}")
                return None

            # Add to project
            self.project.addMapLayer(new_layer, False)  # Don't add to legend yet
            print(f"[LayerEngine] Created memory layer: {layer_name}")
            return new_layer

        except Exception as e:
            print(f"[LayerEngine] Error creating memory layer: {e}")
            return None

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
        try:
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

            if not memory_layer:
                return None

            # Add to group
            group.addLayer(memory_layer)
            print(f"[LayerEngine] Added layer '{new_layer_name}' to group '{group_name}'")

            # Apply default QML style for property layers
            self.apply_qml_style(memory_layer, "properties_background_new")

            return new_layer_name

        except Exception as e:
            print(f"[LayerEngine] Error copying virtual layer: {e}")
            return None

    def save_memory_layer_to_geopackage(
        self,
        memory_layer_name: str,
        new_layer_name: str,
        group_name: str,
        save_directory: Optional[str] = None
    ) -> bool:
        """
        Save memory layer to GeoPackage and reload into project.

        Args:
            memory_layer_name: Name of memory layer to save
            new_layer_name: Name for saved layer
            group_name: Target group name
            save_directory: Optional save directory

        Returns:
            bool: True if successful
        """
        try:
            # Find memory layer
            memory_layer = None
            for layer in self.project.mapLayers().values():
                if layer.name() == memory_layer_name and layer.providerType() == 'memory':
                    memory_layer = layer
                    break

            if not memory_layer:
                print(f"[LayerEngine] Memory layer not found: {memory_layer_name}")
                return False

            # Get save directory
            if not save_directory:
                save_directory = QFileDialog.getExistingDirectory(
                    None, "Vali salvestuskataloog", os.path.expanduser("~")
                )
                if not save_directory:
                    return False

            # Create file path
            file_path = os.path.join(save_directory, f"{new_layer_name}.gpkg")

            # Handle existing file
            if os.path.exists(file_path):
                reply = QMessageBox.question(
                    None, "Fail on olemas",
                    f"Fail '{file_path}' on juba olemas. Kas kirjutada üle?",
                    QMessageBox.Yes | QMessageBox.No
                )
                if reply == QMessageBox.No:
                    return False
                os.remove(file_path)

            # Save to GeoPackage
            options = QgsVectorFileWriter.SaveVectorOptions()
            options.driverName = "GPKG"
            options.layerName = new_layer_name

            error = QgsVectorFileWriter.writeAsVectorFormatV3(
                memory_layer, file_path, self.project.transformContext(), options
            )

            if error[0] != Qgis.NoError:
                print(f"[LayerEngine] Error saving to GeoPackage: {error[1]}")
                return False

            print(f"[LayerEngine] Saved layer to: {file_path}")

            # Reload the saved layer
            saved_layer = QgsVectorLayer(file_path, new_layer_name, "ogr")
            if saved_layer.isValid():
                self.project.addMapLayer(saved_layer, False)

                # Add to group
                group = self.get_or_create_group(group_name)
                group.addLayer(saved_layer)

                # Remove memory layer
                self.project.removeMapLayer(memory_layer.id())

                print(f"[LayerEngine] Reloaded layer '{new_layer_name}' into group '{group_name}'")
                return True
            else:
                print(f"[LayerEngine] Failed to reload saved layer: {file_path}")
                return False

        except Exception as e:
            print(f"[LayerEngine] Error saving memory layer: {e}")
            return False

    def create_property_sync_layer(self, base_layer: Optional[QgsVectorLayer] = None) -> Optional[str]:
        """
        Create a layer specifically for property synchronization.

        Args:
            base_layer: Optional base layer to copy from

        Returns:
            Optional[str]: Name of created layer
        """
        layer_name = "PropertySync_Layer"
        group_name = MailablGroupFolders.SYNC

        return self.copy_virtual_layer_for_properties(layer_name, group_name, base_layer)

    def create_archive_layer(self, base_layer: Optional[QgsVectorLayer] = None) -> Optional[str]:
        """
        Create a layer for archiving operations.

        Args:
            base_layer: Optional base layer to copy from

        Returns:
            Optional[str]: Name of created layer
        """
        layer_name = "Archive_Layer"
        group_name = MailablGroupFolders.ARCHIVE

        return self.copy_virtual_layer_for_properties(layer_name, group_name, base_layer)

    def get_available_groups(self) -> List[str]:
        """
        Get list of available layer groups.

        Returns:
            List[str]: List of group names
        """
        groups = []
        for child in self.layer_tree_root.children():
            if isinstance(child, QgsLayerTreeGroup):
                groups.append(child.name())
        return groups

    def get_layers_in_group(self, group_name: str) -> List[QgsVectorLayer]:
        """
        Get all layers in a specific group.

        Args:
            group_name: Name of the group

        Returns:
            List[QgsVectorLayer]: List of layers in the group
        """
        group = self.layer_tree_root.findGroup(group_name)
        if not group:
            return []

        layers = []
        for child in group.children():
            if hasattr(child, 'layer') and child.layer():
                layers.append(child.layer())

        return layers

    def get_all_layers_in_mailabl_groups(self) -> List[QgsVectorLayer]:
        """
        Get all layers from all Mailabl subgroups.

        Returns:
            List[QgsVectorLayer]: List of all layers in Mailabl groups
        """
        all_layers = []

        # Get main group
        main_group = self.layer_tree_root.findGroup(MailablGroupFolders.MAILABL_MAIN)
        if not main_group:
            return []

        # Get layers from all subgroups
        subgroups = [
            MailablGroupFolders.NEW_PROPERTIES,
            MailablGroupFolders.SANDBOXING,
            MailablGroupFolders.IMPORT,
            MailablGroupFolders.SYNC,
            MailablGroupFolders.ARCHIVE
        ]

        for subgroup_name in subgroups:
            subgroup = main_group.findGroup(subgroup_name)
            if subgroup:
                for child in subgroup.children():
                    if hasattr(child, 'layer') and child.layer():
                        all_layers.append(child.layer())

        return all_layers

    def remove_group_if_empty(self, group_name: str) -> bool:
        """
        Remove a group if it contains no layers.

        Args:
            group_name: Name of the group to remove

        Returns:
            bool: True if group was removed, False otherwise
        """
        try:
            group = self.layer_tree_root.findGroup(group_name)
            if not group:
                print(f"[LayerEngine] Group '{group_name}' not found")
                return False

            # Check if group has any children (layers or subgroups)
            if group.children():
                print(f"[LayerEngine] Group '{group_name}' is not empty, cannot remove")
                return False

            # Remove the empty group
            parent = group.parent()
            if parent:
                parent.removeChildNode(group)
                print(f"[LayerEngine] Removed empty group: {group_name}")
                return True
            else:
                print(f"[LayerEngine] Cannot remove group '{group_name}' - no parent found")
                return False

        except Exception as e:
            print(f"[LayerEngine] Error removing group '{group_name}': {e}")
            return False

    def apply_qml_style(self, layer: QgsVectorLayer, style_name: str = "properties_background_new") -> bool:
        """
        Apply QML style to a layer using the plugin's standard approach.

        Args:
            layer: The layer to apply style to
            style_name: Name of the style to apply (default: properties_background_new)

        Returns:
            bool: True if style was applied successfully, False otherwise
        """
        try:
            # Import here to avoid circular imports
            from ..constants.file_paths import get_style

            # Get the QML style file path
            qml_path = get_style(style_name)
            print(f"[LayerEngine] Applying style '{style_name}' from: {qml_path}")

            if not os.path.exists(qml_path):
                print(f"[LayerEngine] Style file not found: {qml_path}")
                return False

            # Ensure layer is not in editing mode
            if layer.isEditable():
                layer.commitChanges()

            # Apply the QML style
            result = layer.loadNamedStyle(qml_path)
            print(f"[LayerEngine] loadNamedStyle result: {result}")

            if not result[0]:
                print(f"[LayerEngine] loadNamedStyle failed, trying importNamedStyle")
                result = layer.importNamedStyle(qml_path)
                print(f"[LayerEngine] importNamedStyle result: {result}")

            if result[0]:
                print(f"[LayerEngine] Successfully applied QML style '{style_name}' to layer: {layer.name()}")

                # Refresh the layer and map canvas
                layer.triggerRepaint()

                from qgis.utils import iface
                if iface and iface.mapCanvas():
                    iface.mapCanvas().refresh()
                    print("[LayerEngine] Map canvas refreshed")

                return True
            else:
                print(f"[LayerEngine] Failed to apply QML style '{style_name}': {result[1]}")
                return False

        except Exception as e:
            print(f"[LayerEngine] Error applying QML style '{style_name}': {e}")
            return False

def get_layer_engine() -> LayerCreationEngine:
    """Get global layer engine instance."""
    global _layer_engine_instance
    if _layer_engine_instance is None:
        _layer_engine_instance = LayerCreationEngine()
    return _layer_engine_instance
