

from time import perf_counter
try:
    import sip
except ImportError:
    sip = None

from ...constants.settings_keys import SettingsService
from ...constants.cadastral_fields import Katastriyksus
from ...constants.layer_constants import IMPORT_PROPERTY_TAG
from ...utils.mapandproperties.PropertyTableManager import PropertyTableManager

from ...utils.url_manager import Module
from .MapHelpers import MapHelpers
from ...Logs.python_fail_logger import PythonFailLogger
#Provides tools to select elements from map or from tables and show on map


class PropertiesSelectors:
    @staticmethod
    def _is_layer_valid(layer) -> bool:
        if layer is None:
            return False
        if sip:
            try:
                if sip.isdeleted(layer):
                    return False
            except Exception as exc:
                PythonFailLogger.log_exception(
                    exc,
                    module=Module.PROPERTY.value,
                    event="property_layer_sip_check_failed",
                )
                return False
        try:
            if not layer.isValid():
                return False
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module=Module.PROPERTY.value,
                event="property_layer_valid_check_failed",
            )
            return False
        return True

    @staticmethod
    def _resolve_property_layer(*, module=None, use_shp: bool = False):
        if use_shp:
            return MapHelpers.get_layer_by_tag(IMPORT_PROPERTY_TAG)

        settings = SettingsService()
        property_layer_name = settings.module_main_layer_name(Module.PROPERTY.value)
        layer = MapHelpers.resolve_layer(property_layer_name)
        return layer

    @staticmethod
    def show_connected_properties_on_map(values, module=None, use_shp: bool=False) -> None:
        """Goal: select and zoom cadastral features; 
        values: List[str], layer_type: str; 
        Returns: None."""

        if module is None:
            module = Module.PROPERTY.value

        layer = PropertiesSelectors._resolve_property_layer(module=module, use_shp=use_shp)
        
        if not layer:
            PythonFailLogger.log(
                "property_layer_missing",
                module=Module.PROPERTY.value,
                message="Layer not found in show_connected_properties_on_map",
                extra={"module": module or Module.PROPERTY.value},
            )
            return

        if not PropertiesSelectors._is_layer_valid(layer):
            PythonFailLogger.log(
                "property_layer_invalid",
                module=Module.PROPERTY.value,
                message="Layer invalid in show_connected_properties_on_map",
            )
            return

        try:
            features = MapHelpers.find_features_by_fields_and_values(layer, Katastriyksus.tunnus, values)
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module=Module.PROPERTY.value,
                event="property_layer_access_error",
            )
            return layer
        feature_ids = [feature.id() for feature in features]
        if not feature_ids:
            PythonFailLogger.log(
                "property_feature_not_found",
                module=Module.PROPERTY.value,
                extra={
                    "layer_name": layer.name(),
                    "layer_id": layer.id(),
                    "cadastral": ",".join([str(v) for v in (values or [])]),
                },
            )
            return None

        try:
            MapHelpers.ensure_layer_visible(layer, make_active=True)
            layer.removeSelection()
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module=Module.PROPERTY.value,
                event="property_layer_access_error",
            )
            return None

        MapHelpers._zoom_to_features_in_layer(features, layer, select=True)
        return layer        

    @staticmethod
    def show_connected_properties_on_map_from_table(table, module=None, use_shp: bool=False) -> None:
        """Goal: select and zoom cadastral features; 
        values: List[str], layer_type: str; 
        Returns: None."""

        if module is None:
            module = Module.PROPERTY.value

        layer = PropertiesSelectors._resolve_property_layer(module=module, use_shp=use_shp)
        
        if not layer:
            return


        try:
            started = perf_counter()
            features = PropertyTableManager().get_selected_features(table)
            feature_ids = []
            seen_ids = set()
            for feature in features or []:
                try:
                    fid = int(feature.id())
                except Exception:
                    continue
                if fid in seen_ids:
                    continue
                seen_ids.add(fid)
                feature_ids.append(fid)

            if not feature_ids:
                return layer

            MapHelpers.ensure_layer_visible(layer, make_active=True)
            MapHelpers.select_features_by_ids(layer, feature_ids, zoom=True)

            try:
                PythonFailLogger.log(
                    "property_map_sync_from_table",
                    module=Module.PROPERTY.value,
                    extra={
                        "selected": len(feature_ids),
                        "ms": int((perf_counter() - started) * 1000),
                    },
                )
            except Exception:
                pass
            return layer
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module=Module.PROPERTY.value,
                event="property_layer_access_error",
            )
            return layer