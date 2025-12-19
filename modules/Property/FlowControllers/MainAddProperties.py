
from ....languages.translation_keys import TranslationKeys
from ....constants.layer_constants import IMPORT_PROPERTY_TAG
from ....constants.settings_keys import SettingsService
from ....utils.mapandproperties.PropertyTableManager import PropertyTableManager
from ....utils.mapandproperties.PropertyDataLoader import PropertyDataLoader
from ....languages.language_manager import LanguageManager 
from ....utils.MapTools.MapHelpers import MapHelpers
from ....utils.url_manager import Module


class MainAddPropertiesFlow:
    """
    Handles user interaction events and coordinates between data loading and UI updates.
    Separated for better maintainability.
    """
    

    @staticmethod
    def start_adding_properties(table=None):
        """
        Returns True if flow performed actions, False if nothing was selected.
        """
        table_manager = PropertyTableManager()
        selected_features = table_manager.get_selected_features(table)

        if not selected_features:
            return False

        layers = MainAddPropertiesFlow._prepare_layers()
        if layers:
            import_layer, target_layer = layers
            data = PropertyDataLoader().prepare_data_for_import_stage1(selected_features)
            print(f"prepared data for import: {data}")
            return True
        



        return False
    @staticmethod
    def _prepare_layers() -> None:
        # 1) Import layer filtering (optional but explicit)
        import_layer = MapHelpers._get_layer_by_tag(IMPORT_PROPERTY_TAG)
        #set import layer and active layer 
        if import_layer:
            # Choose ONE behavior:
            # A) filter by explicit ids (recommended, deterministic)
            MapHelpers.set_layer_filter_to_selected_features(import_layer)

        # 2) Activate main target layer
        target_layer_name = SettingsService().module_main_layer_name(Module.PROPERTY.value)
        active_layer = MapHelpers.find_layer_by_name(target_layer_name)
        if active_layer:
            MapHelpers.ensure_layer_visible(active_layer, make_active=True)

        return import_layer, active_layer