
import processing

from qgis.utils import iface
from qgis.core import QgsProcessingFeatureSourceDefinition, QgsProject, QgsFeature, edit

from PyQt5.QtCore import QCoreApplication
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
        settings = SettingsService()
        active_layer_id = settings.module_main_layer_id(Module.PROPERTY.value)
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
        
        
    @staticmethod
    def show_AND_copy_connected_cadasters_for_sync_process_dev(values, memory_layer_name):
        """Goal: select import-layer cadasters and copy them; 
        values: List[str], memory_layer_name: str; 
        Returns: None.
        """
        input_layer = PropertiesSelectors._layer_for_type("import")
        if not input_layer:
            return
        target_layer = QgsProject.instance().mapLayersByName(memory_layer_name)[0]
        MapHelpers.ensure_layer_visible(input_layer)
        input_layer.removeSelection()

        features = MapHelpers.find_features_by_values(input_layer, Katastriyksus.tunnus, values)
        feature_ids = [feature.id() for feature in features]
        MapHelpers.select_features_by_ids(input_layer, feature_ids, zoom=False)
        PropertiesSelectors._update_selection_metadata(input_layer, feature_ids)
        iface.mapCanvas().refresh()

        if not feature_ids:
            print(f"values not found in import process: {values}")
            return

        with edit(target_layer):
            for feature in features:
                target_layer.addFeature(QgsFeature(feature))
        target_layer.commitChanges()
        target_layer.triggerRepaint()
        target_layer.updateExtents()
        input_layer.removeSelection()
        

    @staticmethod
    def For_Base_layer_show_connected_cadasters(layer_type, values, selected_feature_ids):
        """Goal: select cadasters on base layer; 
        layer_type:str, values:List[str], selected_feature_ids:List[int]; 
        Returns: str|None.
        """
        layer = PropertiesSelectors._layer_for_type(layer_type)
        if not layer:
            return None
        features = MapHelpers.find_features_by_values(layer, Katastriyksus.tunnus, values)
        feature_ids = [feature.id() for feature in features]
        selected_feature_ids.extend(feature_ids)
        MapHelpers.select_and_zoom_features(layer, features)
        PropertiesSelectors._update_selection_metadata(layer, feature_ids)
        QCoreApplication.processEvents()
        return layer.name()


    def create_mapView_of_county(self, layer_type, selected_county_item_text):
        """Goal: filter layer by county and zoom; 
        layer_type:str, selected_county_item_text:str; 
        Returns: None."""
        layer = PropertiesSelectors._layer_for_type(layer_type)
        if not layer:
            return
        layer.removeSelection()
        MapHelpers.ensure_layer_visible(layer)
        county_name_field = Katastriyksus.mk_nimi #'MK_NIMI'
        #county_restriction = "', '".join(selected_county_item_text)
        expression = f"{county_name_field} IN ('{selected_county_item_text}')"
        print(f"Expression: {expression}")
        layer.setSubsetString(expression)
        layer.triggerRepaint()

        # Zoom to the full extent of the layer
        iface.mapCanvas().setExtent(layer.extent())
        iface.mapCanvas().refresh()
        QCoreApplication.processEvents()
        
        
    def create_mapView_of_state(self, layer_type, selected_state_item_text):
        """Goal: filter layer by state and zoom; 
        layer_type:str, selected_state_item_text:str; 
        Returns: None."""
        layer = PropertiesSelectors._layer_for_type(layer_type)
        if not layer:
            return
        layer.removeSelection()
        MapHelpers.ensure_layer_visible(layer)
        state_name_field = Katastriyksus.ov_nimi
        #state_restriction = "', '".join(selected_state_item_text)
        expression = f"{state_name_field} IN ('{selected_state_item_text}')"
        print(f"Expression: {expression}")
        layer.setSubsetString(expression)
        layer.triggerRepaint()

        # Zoom to the full extent of the layer
        iface.mapCanvas().setExtent(layer.extent())
        iface.mapCanvas().refresh()
        QCoreApplication.processEvents()

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

   
        
class CadasterSelector:
    def projects_return_cadasters(self, table):
        """Goal: read cadaster text from table row;
          table:QTableView; 
          Returns: str.
          """
        table_view = table
        selected_item = table_view.selectedIndexes()
        
        if not selected_item:
            return ""
        id_column_index = selected_item[0].sibling(selected_item[0].row(), 5)
        cadasters = table_view.model().data(id_column_index)
        if not cadasters:
            return ""
        cadasters_list = ['"' + value + '"' for value in cadasters.split(", ")]
        cadasters_str = ", ".join(cadasters_list)
        return cadasters_str

class UseQGISNative:
    def select_elements_from_layer(layer, reference_layer, widget):
        """Goal: select features within buffer; 
        layer:str, reference_layer:str, widget:QWidget; 
        Returns: list.
        """
        # Find and select all features in the input layer
        
        print(f"select elements from '{layer}' layer")
        input_layer = QgsProject.instance().mapLayersByName(layer)
        if not input_layer:
            #print(f"Missing elements from '{input_layer}' layers")
            return

        reference = QgsProject.instance().mapLayersByName(reference_layer)
        if not reference:
            #print(f"Input layer '{reference_layer}' not found")
            return
        
        dial_value = widget.dPuhvriSuurus.value()
        puhver = dial_value / 10
        distance = round(puhver * 2) / 2

        # Run select within distance algorithm
        result = processing.run("native:selectwithindistance", {
            'INPUT': layer,
            'REFERENCE': QgsProcessingFeatureSourceDefinition(reference_layer),
            'DISTANCE': distance,
            'METHOD': 0, # Use planar distance
        })

        # Get selected features
        selected_features = result['OUTPUT']

        return selected_features
 

    @staticmethod
    def get_diameter_and_Z(selected_features):
        """Goal: extract diameter/z values;
         selected_features:List[QgsFeature]; 
        Returns: Tuple[List, List]."""
        diameters = []
        begin_z_coords = []

        for feature in selected_features:
            diameter = feature.attribute('diameter')
            begin_z_coord = feature.attribute('begin_z_coord')

            # Append the attributes to the respective lists
            diameters.append(diameter)
            begin_z_coords.append(begin_z_coord)

        return diameters, begin_z_coords