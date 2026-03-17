

from typing import List
from time import perf_counter
try:
    import sip
except ImportError:
    sip = None
from qgis.core import QgsProject
from qgis.utils import iface

from ...constants.settings_keys import SettingsService
from ...constants.cadastral_fields import Katastriyksus
from ...constants.layer_constants import IMPORT_PROPERTY_TAG
from ...utils.MapTools.MapHelpers import MapHelpers
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
            if hasattr(layer, "isValid") and not layer.isValid():
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
        layer = MapHelpers.find_layer_by_name(property_layer_name)
        if layer:
            return layer

        module_key = str(module or "").strip().lower()
        if module_key and module_key not in (
            Module.PROPERTY.value,
            Module.WORKS.value,
            Module.ASBUILT.value,
            Module.TASK.value,
        ):
            active_layer_name = settings.module_main_layer_name(module_key)
            layer = MapHelpers.find_layer_by_name(active_layer_name)
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
            try:
                PythonFailLogger.log(
                    "property_layer_missing",
                    module=Module.PROPERTY.value,
                    message="Layer not found in show_connected_properties_on_map",
                    extra={"module": module or Module.PROPERTY.value},
                )
            except Exception as exc:
                print(f"[PropertiesSelectors] Failed to log missing layer: {exc}")
            return

        if not PropertiesSelectors._is_layer_valid(layer):
            try:
                PythonFailLogger.log(
                    "property_layer_invalid",
                    module=Module.PROPERTY.value,
                    message="Layer invalid in show_connected_properties_on_map",
                )
            except Exception as exc:
                print(f"[PropertiesSelectors] Failed to log invalid layer: {exc}")
            return

        try:
            features = MapHelpers.find_features_by_fields_and_values(layer, Katastriyksus.tunnus, values)
        except Exception as exc:
            try:
                PythonFailLogger.log_exception(
                    exc,
                    module=Module.PROPERTY.value,
                    event="property_layer_access_error",
                )
            except Exception as log_exc:
                print(f"[PropertiesSelectors] Failed to log access error: {log_exc}")
            return layer
        feature_ids = [feature.id() for feature in features]
        if not feature_ids:
            try:
                PythonFailLogger.log(
                    "property_feature_not_found",
                    module=Module.PROPERTY.value,
                    extra={
                        "layer_name": getattr(layer, "name", lambda: "")(),
                        "layer_id": getattr(layer, "id", lambda: "")(),
                        "cadastral": ",".join([str(v) for v in (values or [])]),
                    },
                )
            except Exception as exc:
                print(f"[PropertiesSelectors] Failed to log feature not found: {exc}")
            return None

        try:
            MapHelpers.ensure_layer_visible(layer, make_active=True)
            layer.removeSelection()
        except Exception as exc:
            try:
                PythonFailLogger.log_exception(
                    exc,
                    module=Module.PROPERTY.value,
                    event="property_layer_access_error",
                )
            except Exception as log_exc:
                print(f"[PropertiesSelectors] Failed to log access error: {log_exc}")
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
            layer.removeSelection()
            layer.selectByIds(feature_ids)

            extent = layer.boundingBoxOfSelected()
            if extent is not None and not extent.isEmpty() and iface is not None:
                extent.scale(1.2)
                canvas = iface.mapCanvas()
                if canvas is not None:
                    canvas.setExtent(extent)
                    canvas.refresh()

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
            try:
                PythonFailLogger.log_exception(
                    exc,
                    module=Module.PROPERTY.value,
                    event="property_layer_access_error",
                )
            except Exception as log_exc:
                print(f"[PropertiesSelectors] Failed to log access error: {log_exc}")
            return layer