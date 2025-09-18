"""
Centralized settings keys constants for the wild_code plugin.

This module contains all settings keys used throughout the application.
All keys follow the "wild_code/" prefix convention for consistency.
"""

# Theme settings
THEME = "wild_code/theme"

# Preferred module settings
PREFERRED_MODULE = "wild_code/preferred_module"

# Property layer settings
MAIN_PROPERTY_LAYER_ID = "wild_code/main_property_layer_id"

# Plugin dialog geometry
PLUGIN_DIALOG_GEOMETRY = "wild_code/plugin_dialog/geometry"

# Module-specific settings base pattern
# Usage: f"wild_code/modules/{module_name}/{setting_key}"
MODULE_SETTINGS_BASE = "wild_code/modules"

# Utility-specific settings
class UtilitySettings:
    """Settings keys for utility classes and tools."""

    # SHPLayerLoader settings
    @staticmethod
    def shp_last_file_path(target_group: str) -> str:
        """Get the key for storing the last loaded Shapefile path for a target group."""
        return f"wild_code/last_shp_file_{target_group}"

    @staticmethod
    def shp_layer_name_mapping(layer_name: str) -> str:
        """Get the key for storing Shapefile layer name to file path mapping."""
        return f"wild_code/layer_name_{layer_name}"

# Engine settings
TARGET_CADASTRAL_LAYER = "wild_code/target_cadastral_layer"

# Session management
SESSION_TOKEN = "session/token"
SESSION_ACTIVE_USER = "session/active_user"
SESSION_NEEDS_LOGIN = "session/needs_login"

# Authentication
AUTH_ID = "myplugin/auth_id"
AUTH_USERNAME = "myplugin/username"
