"""
Centralized Settings Manager for utility-specific settings.

This module provides a centralized way to manage settings that don't fit into
the specialized categories (theme, preferred module, module-specific settings).

All settings use the "wild_code/" prefix for consistency with the existing architecture.
"""

from typing import Any, Optional
from qgis.core import QgsSettings


class SettingsManager:
    """
    Centralized settings manager for utility-specific settings.

    Provides a consistent API for saving and loading settings across the application.
    All settings automatically use the "wild_code/" prefix for consistency.
    """

    @staticmethod
    def save_setting(key: str, value: Any) -> bool:
        """
        Save a setting value.

        Args:
            key: Settings key (should include "wild_code/" prefix)
            value: Value to save

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            settings = QgsSettings()
            settings.setValue(key, value)
            return True
        except Exception:
            return False

    @staticmethod
    def load_setting(key: str, default_value: Any = None) -> Any:
        """
        Load a setting value.

        Args:
            key: Settings key (should include "wild_code/" prefix)
            default_value: Default value if key doesn't exist

        Returns:
            The setting value or default_value if not found
        """
        try:
            settings = QgsSettings()
            return settings.value(key, default_value)
        except Exception:
            return default_value

    @staticmethod
    def remove_setting(key: str) -> bool:
        """
        Remove a setting.

        Args:
            key: Settings key to remove

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            settings = QgsSettings()
            settings.remove(key)
            return True
        except Exception:
            return False

    @staticmethod
    def has_setting(key: str) -> bool:
        """
        Check if a setting exists.

        Args:
            key: Settings key to check

        Returns:
            bool: True if the setting exists, False otherwise
        """
        try:
            settings = QgsSettings()
            # Try to get the value - if it returns the default, check if it was actually set
            value = settings.value(key, "__NOT_SET__")
            return value != "__NOT_SET__"
        except Exception:
            return False





