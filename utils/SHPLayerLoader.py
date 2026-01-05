#!/usr/bin/env python3


import os
from typing import Optional
from PyQt5.QtWidgets import QFileDialog
from qgis.core import QgsVectorLayer

from ..engines.LayerCreationEngine import get_layer_engine, MailablGroupFolders
from ..languages.language_manager import LanguageManager
from ..constants.layer_constants import IMPORT_PROPERTY_TAG
from ..constants.file_paths import QmlPaths
from .messagesHelper import ModernMessageDialog


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
        print("[SHPLayerLoader] Starting load_shp_layer")
        # Show file dialog for SHP files
        file_path = self._get_shp_file_path()
        if not file_path:
            print("[SHPLayerLoader] No file selected (cancelled)")
            return False  # User cancelled

        # Validate and load the Shapefile
        layer_name = os.path.splitext(os.path.basename(file_path))[0]
        shp_layer = QgsVectorLayer(file_path, layer_name, 'ogr')

        if not shp_layer.isValid():
            print("[SHPLayerLoader] QgsVectorLayer is not valid")
            return False

        print("[SHPLayerLoader] Importing shapefile to memory layer")
        memory_layer = self.engine.import_shapefile_to_memory_layer(
                shp_layer=shp_layer,
                layer_name=layer_name,
                group_name=self.target_group,
                parent_widget=self.parent
            )
        print(f"[SHPLayerLoader] Import result layer name: {memory_layer}")

        # If engine returns a layer name (str), resolve it to the actual layer object
        if isinstance(memory_layer, str):
            layers = self.engine.project.mapLayersByName(memory_layer)
            memory_layer = layers[0] if layers else None

        if memory_layer:
            print(f"[SHPLayerLoader] Memory layer found; setting tag and applying style. Feature count pre-style: {memory_layer.featureCount()}")
            # Set the property tag on the newly created layer
            memory_layer.setCustomProperty(IMPORT_PROPERTY_TAG, "true")

            # Ensure layer is not in editing mode before applying style
            if memory_layer.isEditable():
                memory_layer.commitChanges()

            # Apply QML style using the engine's centralized method
            self.engine.apply_qml_style(memory_layer, QmlPaths.MAAMET_IMPORT)

        feature_count = memory_layer.featureCount() if memory_layer else 0
        print(f"[SHPLayerLoader] Final feature_count={feature_count}")
        message = (self.lang_manager.translate("Shapefile loaded with data message") or "Shapefile '{name}' on edukalt laaditud grupis 'Uued kinnistud' ({count} objekti imporditud)")
        if feature_count > 0:
            message = message.format(name=layer_name, count=feature_count)
        else:
            message = (self.lang_manager.translate("Shapefile loaded message") or "Shapefile '{name}' on edukalt laaditud grupis 'Uued kinnistud'").format(name=layer_name)

        ModernMessageDialog.show_info(
            self.lang_manager.translate("Shapefile loaded successfully") or "Shapefile edukalt laaditud",
            message,
        )
        return True



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
