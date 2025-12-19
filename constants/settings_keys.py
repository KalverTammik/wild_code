from typing import Optional

from qgis.core import QgsSettings
from ..utils.url_manager import ModuleSupports


PLUGIN = "wild_code"
MODULE_SETTINGS_BASE = f"{PLUGIN}/modules"

# Plugin-wide setting keys
THEME = f"{PLUGIN}/theme"
PREFERRED_MODULE = f"{PLUGIN}/preferred_module"
MAIN_PROPERTY_LAYER_ID = f"{PLUGIN}/main_property_layer_id"
PLUGIN_DIALOG_GEOMETRY = f"{PLUGIN}/plugin_dialog/geometry"

# Per-module suffix constants
MODULE_SETTING_MAIN_LAYER = "element_layer_id"
MODULE_SETTING_ARCHIVE_LAYER = "archive_layer_id"
MODULE_SETTING_SHOW_NUMBERS = "show_numbers"
MODULE_SETTING_PREFERRED_STATUSES = "preferred_statuses"
MODULE_SETTING_PREFERRED_TYPES = "preferred_types"
MODULE_SETTING_PREFERRED_TAGS = "preferred_tags"
MODULE_SETTING_LABEL_PREFIX = "labels"


def module_setting_key(module_name: str, suffix: str) -> str:
    """Build the fully-qualified key for a module-scoped setting."""
    normalized = (module_name or "").strip().lower()
    return f"{MODULE_SETTINGS_BASE}/{normalized}/{suffix}"


_UNSET = object()


class SettingsService:
    """Central engine for every persistent setting the plugin touches."""

    def __init__(self, settings: Optional[QgsSettings] = None):
        self._settings = settings or QgsSettings()

    # --- Low level primitives -------------------------------------------------
    def get_setting(self, key: str, default=None):
        return self._settings.value(key, default)

    def set_setting(self, key: str, value):
        self._settings.setValue(key, value)

    def clear_setting(self, key: str):
        self._settings.remove(key)

    # --- Generic helpers ------------------------------------------------------
    def plugin_setting(self, suffix: str, value=_UNSET, *, clear: bool = False, default=None):
        key = f"{PLUGIN}/{suffix.lstrip('/')}"

        if clear:
            self.clear_setting(key)
            return None

        if value is _UNSET:
            return self.get_setting(key, default)

        self.set_setting(key, value)
        return value

    def module_setting(
        self,
        module_name: str,
        suffix: str,
        value=_UNSET,
        *,
        clear: bool = False,
        default=None,
    ):
        key = module_setting_key(module_name, suffix)

        if clear:
            self.clear_setting(key)
            return None

        if value is _UNSET:
            return self.get_setting(key, default)

        self.set_setting(key, value)
        return value

    # --- Named helpers --------------------------------------------------------
    def preferred_module(self, value=_UNSET, *, clear: bool = False, default: str = ""):
        return self.plugin_setting(PREFERRED_MODULE, value=value, clear=clear, default=default)

    def main_property_layer_id(self, value=_UNSET, *, clear: bool = False, default: str = ""):
        return self.plugin_setting(MAIN_PROPERTY_LAYER_ID, value=value, clear=clear, default=default)

    def module_preferred_statuses(self, module_name: str, value=_UNSET, *, clear: bool = False):
        return self.module_setting(
            module_name,
            MODULE_SETTING_PREFERRED_STATUSES,
            value=value,
            clear=clear,
            default="",
        )

    def module_preferred_types(self, module_name: str, value=_UNSET, *, clear: bool = False):
        return self.module_setting(
            module_name,
            MODULE_SETTING_PREFERRED_TYPES,
            value=value,
            clear=clear,
            default="",
        )

    def module_preferred_tags(self, module_name: str, value=_UNSET, *, clear: bool = False):
        return self.module_setting(
            module_name,
            MODULE_SETTING_PREFERRED_TAGS,
            value=value,
            clear=clear,
            default="",
        )

    def module_main_layer_name(self, module_name: str, value=_UNSET, *, clear: bool = False):
        return self.module_setting(
            module_name,
            MODULE_SETTING_MAIN_LAYER,
            value=value,
            clear=clear,
            default="",
        )

    def module_archive_layer_id(self, module_name: str, value=_UNSET, *, clear: bool = False):
        return self.module_setting(
            module_name,
            MODULE_SETTING_ARCHIVE_LAYER,
            value=value,
            clear=clear,
            default="",
        )

    @staticmethod
    def _normalize_label_key(label_key: str) -> str:
        raw = (label_key or "").strip().lower()
        return "".join(ch if ch.isalnum() or ch in {"-", "_", "."} else "_" for ch in raw)

    def module_label_value(self, module_name: str, label_key: str, value=_UNSET, *, clear: bool = False, default: str = ""):
        """Instance helper for module label storage (mirrors other module_* helpers)."""
        if not label_key:
            return default
        normalized_key = SettingsService._normalize_label_key(label_key)
        suffix = f"{MODULE_SETTING_LABEL_PREFIX}/{normalized_key}"
        return self.module_setting(
            module_name,
            suffix,
            value=value,
            clear=clear,
            default=default,
        )



    @staticmethod
    def load_preferred_ids_by_key(key, module) -> None:
        loaders = {
            ModuleSupports.TAGS.value: SettingsService().module_preferred_tags,
            ModuleSupports.STATUSES.value: SettingsService().module_preferred_statuses,
            ModuleSupports.TYPES.value: SettingsService().module_preferred_types,
        }
        loader = loaders.get(key)
        if not loader:
            return

        preferred_raw = loader(module) or ""
        ids = [token.strip() for token in str(preferred_raw).split(",") if token.strip()]
        return ids

    @staticmethod
    def save_preferred_ids_by_key(key, module, ids) -> None:
        service = SettingsService()
        writers = {
            ModuleSupports.TAGS.value: service.module_preferred_tags,
            ModuleSupports.STATUSES.value: service.module_preferred_statuses,
            ModuleSupports.TYPES.value: service.module_preferred_types,
        }
        writer = writers.get(key)
        if not writer:
            return

        try:
            cleaned = sorted({str(v).strip() for v in (ids or []) if str(v).strip()})
            if cleaned:
                writer(module, value=",".join(cleaned))
            else:
                writer(module, clear=True)
        except Exception:
            pass
    

    


# Utility-specific settings ----------------------------------------------------
class UtilitySettings:
    """Settings keys for utility classes and tools that still use raw paths."""

    @staticmethod
    def shp_last_file_path(target_group: str) -> str:
        return f"wild_code/last_shp_file_{target_group}"

    @staticmethod
    def shp_layer_name_mapping(layer_name: str) -> str:
        return f"wild_code/layer_name_{layer_name}"




