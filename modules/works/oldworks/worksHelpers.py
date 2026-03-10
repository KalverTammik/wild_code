#worksHelpers.py

from .worksTools import worksTools
from ...KeelelisedMuutujad.modules import Module
from ...config.settings import SettingsDataSaveAndLoad
from ...config.settings_new import PluginSettings
from ...widgets.decisionUIs.DecisionMaker import DecisionDialogHelper
from ...app.Animations.AnimatedGradientBorderFrame import AnimatedGradientBorderFrame
from ...KeelelisedMuutujad.messages import Headings, HoiatusTexts

from PyQt5.QtCore import Qt


from qgis.utils import iface
from qgis.core import (
    QgsProject,
    QgsPointXY,
    QgsVectorLayer,
    QgsFeatureRequest,
    QgsGeometry,
    QgsRectangle,
    QgsFeature,    
)


class worksHelpers:
    WORKSFEATURE = None

    def get_feature_tunnus_from_layer( point, canvas, plugin_instance, radius_multiplier=3):
        """Returns the 'tunnus' value from the first feature under the clicked point."""

        properties_layer_name = SettingsDataSaveAndLoad.load_target_cadastral_name(plugin_instance)  # or pass plugin instance if needed

        layer = QgsProject.instance().mapLayersByName(properties_layer_name)[0]
        if not layer:
            raise ValueError(f"No layer found with the name {properties_layer_name}")

        search_radius = canvas.mapUnitsPerPixel() * radius_multiplier
        search_rect = QgsRectangle(
            point.x() - search_radius,
            point.y() - search_radius,
            point.x() + search_radius,
            point.y() + search_radius
        )
        request = QgsFeatureRequest().setFilterRect(search_rect)
        return next(layer.getFeatures(request), None)

    def insert_work_feature(point: QgsPointXY, plugin_instance):

        module = Module.WORKS

        # Get WORKS layer name from plugin settings
        works_layer_name = PluginSettings.load_setting(
            module=module,
            context=PluginSettings.CONTEXT_PREFERRED,
            subcontext=PluginSettings.OPTION_LAYER,
            key_type=PluginSettings.WORKS_LAYER
        )

        works_layer = QgsProject.instance().mapLayersByName(works_layer_name)[0]

        if not works_layer or not isinstance(works_layer, QgsVectorLayer):
            buttons={"keep": "Edasi",}
            ret = DecisionDialogHelper.ask_user(
                title=Headings.inFO_SIMPLE,
                message=f"❌ Kaardikihti nimega '{works_layer_name}' ei leitud.",
                options=buttons,
                parent=None,
                type= AnimatedGradientBorderFrame.WARNING
                    )
            return

        # Create new feature
        feature = QgsFeature(works_layer.fields())
        feature.setGeometry(QgsGeometry.fromPointXY(point))

        # Optional: match "tunnus" from property layer and add it as attribute
        properties_feature = worksHelpers.get_feature_tunnus_from_layer(point, iface.mapCanvas(), plugin_instance)
        if properties_feature:
            feature.setAttribute("affected_properties", True)
        else:
            feature.setAttribute("affected_properties", False)
        # Add the feature to the layer
        
        res = worksTools.load_worksTools(feature, properties_feature)
        
        if res == True:
            works_layer.startEditing()
            works_layer.addFeature(feature)   
            works_layer.commitChanges()
            works_layer.triggerRepaint()
        if res == False:
            works_layer.rollBack()

        plugin_instance.setWindowState(Qt.WindowNoState)
        plugin_instance.raise_()  # brings it to front

        return


