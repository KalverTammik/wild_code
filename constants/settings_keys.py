"""Setting keys of the plugin. The reading and writing lives in utils/settings_service.py."""

PLUGIN = "kavitro"
MODULE_SETTINGS_BASE = f"{PLUGIN}/modules"

# Plugin-wide setting keys
THEME = f"{PLUGIN}/theme"
LANGUAGE = f"{PLUGIN}/language"
PREFERRED_MODULE = f"{PLUGIN}/preferred_module"
MAIN_PROPERTY_LAYER_ID = f"{PLUGIN}/main_property_layer_id"
PLUGIN_DIALOG_GEOMETRY = f"{PLUGIN}/plugin_dialog/geometry"
GEOSPATIAL_SETUP_MODE = f"{PLUGIN}/geospatial/setup_mode"
MAP_CANVAS_GLASS_ACTION_BAR_ENABLED = f"{PLUGIN}/map_canvas/glass_action_bar_enabled"
MAP_CANVAS_SEARCH_BAR_ENABLED = f"{PLUGIN}/map_canvas/search_bar_enabled"
INDICATOR_DESIGN = "indicator/design"  # the toolbar indicator of the modules
INDICATOR_PALETTE = "indicator/palette"

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
