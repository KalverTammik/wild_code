#!/usr/bin/env python3


import os
from typing import Optional
from PyQt5.QtWidgets import QFileDialog, QMessageBox
from qgis.core import QgsVectorLayer

from ..engines.LayerCreationEngine import get_layer_engine, MailablGroupFolders
from ..languages.language_manager import LanguageManager
from ..constants.layer_constants import PROPERTIES_BACKGROUND_STYLE, IMPORT_PROPERTY_TAG
from ..utils.SettingsManager import SettingsManager


class SHPLayerLoader:
    """
    Clean utility for loading Shapefiles as memory layers in QGIS.

    Provides a simple interface for:
    - File selection dialog
    - Shapefile validation
    - Memory layer creation
    - Group organization
    - Settings persistence
    """

    def __init__(self, parent_widget=None, target_group=None):
        """
        Initialize the SHPLayerLoader.

        Args:
            parent_widget: Parent widget for dialogs
            target_group: Target group name (defaults to NEW_PROPERTIES)
        """
        self.parent = parent_widget
        self.target_group = target_group or MailablGroupFolders.NEW_PROPERTIES
        self.lang_manager = LanguageManager()
        self.engine = get_layer_engine()

    def load_shp_layer(self) -> bool:
        """
        Load a Shapefile as a memory layer with data import.

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Show file dialog for SHP files
            file_path = self._get_shp_file_path()
            if not file_path:
                return False  # User cancelled

            # Validate and load the Shapefile
            layer_name = os.path.splitext(os.path.basename(file_path))[0]
            shp_layer = self._load_shp_layer(file_path, layer_name)

            if not shp_layer:
                 return False

            # Create memory layer and import data
            result = self._create_memory_layer(shp_layer, layer_name)

            if result:

                # Save the last loaded file path for future reference
                SettingsManager.save_shp_file_path(self.target_group, file_path)
                # Save layer name mapping
                SettingsManager.save_shp_layer_mapping(layer_name, file_path)

                # Get feature count for success message
                memory_layer = None
                for layer in self.engine.project.mapLayers().values():
                    if layer.name() == result:
                        memory_layer = layer
                        break

                if memory_layer:
                    # Set the property tag on the newly created layer
                    memory_layer.setCustomProperty(IMPORT_PROPERTY_TAG, "true")

                    # Ensure layer is not in editing mode before applying style
                    if memory_layer.isEditable():
                        memory_layer.commitChanges()

                    # Apply QML style using the engine's centralized method
                    self.engine.apply_qml_style(memory_layer, PROPERTIES_BACKGROUND_STYLE)

                feature_count = memory_layer.featureCount() if memory_layer else 0
                message = (self.lang_manager.translate("Shapefile loaded with data message") or "Shapefile '{name}' on edukalt laaditud grupis 'Uued kinnistud' ({count} objekti imporditud)")
                if feature_count > 0:
                    message = message.format(name=layer_name, count=feature_count)
                else:
                    message = (self.lang_manager.translate("Shapefile loaded message") or "Shapefile '{name}' on edukalt laaditud grupis 'Uued kinnistud'").format(name=layer_name)

                QMessageBox.information(
                    self.parent,
                    self.lang_manager.translate("Shapefile loaded successfully") or "Shapefile edukalt laaditud",
                    message
                )
                return True
            else:
                QMessageBox.warning(self.parent, "Shapefile load failed", "Failed to create memory layer or import data")
                return False

        except Exception as e:
            QMessageBox.critical(self.parent, "Shapefile loading error", f"Error: {str(e)}")
            return False

    def _get_shp_file_path(self) -> Optional[str]:
        """
        Show file dialog and get Shapefile path.

        Returns:
            Optional[str]: Selected file path or None if cancelled
        """
        file_path, _ = QFileDialog.getOpenFileName(
            self.parent,
            self.lang_manager.translate("Select Shapefile") or "Vali Shapefile fail",
            "",
            "SHP files (*.shp);;All files (*.*)"
        )
        return file_path if file_path else None

    def _load_shp_layer(self, file_path: str, layer_name: str) -> Optional[QgsVectorLayer]:
        """
        Load and validate Shapefile.

        Args:
            file_path: Path to Shapefile
            layer_name: Name for the layer

        Returns:
            Optional[QgsVectorLayer]: Loaded layer or None if invalid
        """
        shp_layer = QgsVectorLayer(file_path, layer_name, 'ogr')

        if not shp_layer.isValid():
            QMessageBox.warning(
                self.parent,
                self.lang_manager.translate("Invalid Shapefile") or "Vigane Shapefile",
                self.lang_manager.translate("Invalid Shapefile message") or "Valitud Shapefile fail ei ole kehtiv."
            )
            return None

        return shp_layer

    def _create_memory_layer(self, shp_layer: QgsVectorLayer, layer_name: str) -> Optional[str]:
        """
        Create memory layer from Shapefile using centralized LayerCreationEngine.

        Args:
            shp_layer: Source Shapefile layer
            layer_name: Name for the new memory layer

        Returns:
            Optional[str]: Name of created layer or None if failed
        """
        try:
            # Use the centralized engine method for Shapefile import
            return self.engine.import_shapefile_to_memory_layer(
                shp_layer=shp_layer,
                layer_name=layer_name,
                group_name=self.target_group,
                parent_widget=self.parent
            )

        except Exception as e:
            QMessageBox.critical(self.parent, "Memory layer creation error", f"Error: {str(e)}")
            return None

