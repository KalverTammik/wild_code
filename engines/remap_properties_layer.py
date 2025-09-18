from qgis.utils import iface
from qgis.core import QgsVectorLayer, QgsProject, QgsField, QgsSettings
from PyQt5.QtCore import QCoreApplication

from ..utils.UniversalStatusBar import UniversalStatusBar
from ..constants.cadastral_fields import Katastriyksus, OldKatastriyksus, KatasterMappings, Purpose



class RemapPropertiesLayer:
    """Handles remapping and updating of cadastral property layers in QGIS."""

    def __init__(self):
        """Initialize the remapper with the active cadastral layer."""
        self.active_layer_name = self._get_target_cadastral_name()
        self.layer = self.get_layer_by_name(self.active_layer_name)
        self.field_mapping = KatasterMappings.field_mapping

    def _get_target_cadastral_name(self) -> str:
        """Get the target cadastral layer name from QGIS settings."""
        try:
            settings = QgsSettings()
            layer_name = settings.value("wild_code/target_cadastral_layer", "katastriyksus")
            return layer_name or "katastriyksus"
        except Exception:
            return "katastriyksus"

    def _save_target_cadastral_name(self, layer_name: str):
        """Save the target cadastral layer name to QGIS settings."""
        try:
            settings = QgsSettings()
            settings.setValue("wild_code/target_cadastral_layer", layer_name)
        except Exception:
            pass

    def get_layer_by_name(self, layer_name):
        """Retrieve a layer by name from the current QGIS project."""
        layer = QgsProject.instance().mapLayersByName(layer_name)
        if not layer:
            raise ValueError(f"No layer found with the name {layer_name}")
        return layer[0]

    def validate_layer(self):
        """Validate that the layer is a vector layer."""
        if not isinstance(self.layer, QgsVectorLayer):
            raise ValueError("Expected a QgsVectorLayer object.")

    def update_attribute_table(self):
        """Update the attribute table by renaming fields, processing features, and adding missing fields."""
        
        progress = UniversalStatusBar(title="Andmestruktuuri uuendamine", initial_value=0, maximum=3)
        progress.update(purpose=f"{self.layer.name()} andmete struktuuri uuendateakse", text1="Palun oota...")
        
        self.validate_layer()
        iface.setActiveLayer(self.layer)
        self.layer.startEditing()
        layer_fields = self.layer.fields()
        temp_field_mapping = self.rename_fields_temporarily(layer_fields)
        self.rename_fields_to_final(layer_fields, temp_field_mapping)
        progress.update(value=2)

        # Process features in batches for efficiency
        features = list(self.layer.getFeatures())
        total = len(features)
        progress.update(maximum=total)
        for i, feature in enumerate(features, start=1):
            modified = False

            for field_name in [Katastriyksus.siht1, Katastriyksus.siht2, Katastriyksus.siht3]:
                value = feature[field_name]
                if value is not None:
                    value_str = str(value).upper().replace(" ", "_")
                    if value_str != value:
                        feature[field_name] = value_str
                        modified = True

            if modified:
                self.layer.updateFeature(feature)

            progress.update(value=i, text2=f"{i} / {total}")
            QCoreApplication.processEvents()
            
        try:
            if self.layer.commitChanges():
                pass
            else:
                self.layer.rollBack()
                print("Warning: Failed to commit field name changes")
                progress.close()
                return
        except Exception as e:
            self.layer.rollBack()
            print(f"Error saving changes: {str(e)}")
            progress.close()
            return
        
        self.remove_temp_suffix()
        self.add_missing_fields()
        
        progress.close()


    def rename_fields_temporarily(self, layer_fields):
        """Rename fields temporarily to avoid conflicts during remapping."""
        temp_field_mapping = {}
        for old_field, new_field in self.field_mapping.items():
            if layer_fields.indexFromName(old_field) != -1:
                temp_name = new_field + '_temp'
                idx = layer_fields.indexFromName(old_field)
                self.layer.renameAttribute(idx, temp_name)
                temp_field_mapping[temp_name] = new_field
        return temp_field_mapping

    def rename_fields_to_final(self, layer_fields, temp_field_mapping):
        """Rename temporary fields to their final names."""
        for temp_name, new_field in temp_field_mapping.items():
            if layer_fields.indexFromName(temp_name) != -1:
                idx = layer_fields.indexFromName(temp_name)
                self.layer.renameAttribute(idx, new_field)

    def remove_temp_suffix(self):
        """Remove temporary suffixes from field names."""
        self.validate_layer()

        if not self.layer.isEditable():
            self.layer.startEditing()

        layer_fields = self.layer.fields()

        for field in layer_fields:
            if '_temp' in field.name():
                new_name = field.name().replace('_temp', '')
                idx = layer_fields.indexFromName(field.name())
                self.layer.renameAttribute(idx, new_name)

        try:
            if self.layer.commitChanges():
                pass
            else:
                self.layer.rollBack()
        except Exception as e:
            self.layer.rollBack()
            print(f"Error removing temporary field names: {str(e)}")
