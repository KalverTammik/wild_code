

from typing import List
from qgis.core import QgsProject

from ...constants.settings_keys import SettingsService
from ...constants.cadastral_fields import Katastriyksus
from ...constants.layer_constants import IMPORT_PROPERTY_TAG
from ...utils.MapTools.MapHelpers import MapHelpers
from ...utils.mapandproperties.PropertyTableManager import PropertyTableManager

from ...utils.url_manager import Module
from .MapHelpers import MapHelpers
#Provides tools to select elements from map or from tables and show on map


class PropertiesSelectors:
    @staticmethod
    def show_connected_properties_on_map(values, module=None, use_shp: bool=False) -> None:
        """Goal: select and zoom cadastral features; 
        values: List[str], layer_type: str; 
        Returns: None."""

        if use_shp:
            shp_layer = MapHelpers._get_layer_by_tag(IMPORT_PROPERTY_TAG)
            layer = shp_layer

        else:
            if module == None:
                module = Module.PROPERTY.value
            active_layer_name = SettingsService().module_main_layer_name(module)
            layer = MapHelpers.find_layer_by_name(active_layer_name)
        
        if not layer:
            return

        MapHelpers.ensure_layer_visible(layer, make_active=True)
        layer.removeSelection()

        features = MapHelpers.find_features_by_fields_and_values(layer, Katastriyksus.tunnus, values)
        feature_ids = [feature.id() for feature in features]
        if not feature_ids:
            return layer

        MapHelpers._zoom_to_features_in_layer(features, layer, select=True)
        return layer        

    @staticmethod
    def show_connected_properties_on_map_from_table(table, module=None, use_shp: bool=False) -> None:
        """Goal: select and zoom cadastral features; 
        values: List[str], layer_type: str; 
        Returns: None."""

        if use_shp:
            shp_layer = MapHelpers._get_layer_by_tag(IMPORT_PROPERTY_TAG)
            layer = shp_layer

        else:
            if module == None:
                module = Module.PROPERTY.value
            active_layer_name = SettingsService().module_main_layer_name(module)
            layer = MapHelpers.find_layer_by_name(active_layer_name)
        
        if not layer:
            return


        MapHelpers.ensure_layer_visible(layer, make_active=True)
        layer.removeSelection()

        features = PropertyTableManager().get_selected_features(table)

        MapHelpers._zoom_to_features_in_layer(features, layer, select=True)
        return layer        