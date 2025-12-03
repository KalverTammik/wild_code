

from typing import List
from qgis.core import QgsProject

from ...constants.settings_keys import SettingsService
from ...constants.cadastral_fields import Katastriyksus
from ...utils.url_manager import Module
from .MapHelpers import MapHelpers
#Provides tools to select elements from map or from tables and show on map


class PropertiesSelectors:
    @staticmethod
    def show_connected_properties_on_map(values):
        """Goal: select and zoom cadastral features; 
        values: List[str], layer_type: str; 
        Returns: None."""

        active_layer_id = SettingsService().module_main_layer_id(Module.PROPERTY.value)
        MapHelpers.resolve_layer(active_layer_id)
        layer = PropertiesSelectors._layer_for_type(active_layer_id)
        if not layer:
            return
        MapHelpers.ensure_layer_visible(layer)
        layer.removeSelection()

        features = MapHelpers.find_features_by_values(layer, Katastriyksus.tunnus, values)
        feature_ids = [feature.id() for feature in features]
        if not feature_ids:
            return

        MapHelpers.select_and_zoom_features(layer, features)
                


    def get_tunnus_value_from_selected_property_features(layer_type: str=None) -> List[str]:
        """Goal: get Tunnus values from selected cadastral features; 
        layer_type: str; 
        Returns: List[str]."""
        settings = SettingsService()
        active_layer_id = settings.module_main_layer_name(Module.PROPERTY.value)
        MapHelpers.resolve_layer(active_layer_id)
        layer = PropertiesSelectors._layer_for_type(active_layer_id)
        if not layer:
            return []
        selected_features = layer.selectedFeatures()
        tunnus_values = [
            feature.attribute(Katastriyksus.tunnus)
            for feature in selected_features
            if feature.hasAttribute(Katastriyksus.tunnus)
        ]
        return tunnus_values



    @staticmethod
    def _layer_for_type(layer_type: str):
        """Goal: resolve a QGIS layer; 
        layer_type:str; 
        Returns: QgsVectorLayer|None."""
        if layer_type == "active":
            layer_name = StoredLayers.users_properties_layer_name()
        elif layer_type == "import":
            layer_name = StoredLayers.import_layer_name()
        elif layer_type == "archived":
            layer_name = StoredLayers.archived_properties_layer_name()
        else:
            layer_name = layer_type
        layers = QgsProject.instance().mapLayersByName(layer_name)
        return layers[0] if layers else None

    @staticmethod
    def bring_dialog_to_front(widget) -> None:
        """Best-effort attempt to bring the widget's top-level window to the foreground."""
        if widget is None:
            return
        try:
            main_dialog = widget.window()
            if not main_dialog:
                return
            main_dialog.showNormal()
            main_dialog.raise_()
            main_dialog.activateWindow()
        except Exception:
            # Not fatal if the window cannot be brought to the foreground
            pass

    