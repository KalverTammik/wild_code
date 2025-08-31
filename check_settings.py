#!/usr/bin/env python3
"""
Quick test to check current settings state
"""

import sys
import os

# Add the plugin root to the path
plugin_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, plugin_root)

try:
    from qgis.core import QgsSettings
    from widgets.theme_manager import ThemeManager

    print("🔍 Settings State Check")
    print("=" * 50)

    # Check QGIS settings directly
    settings = QgsSettings()

    # Check module settings
    module_names = ["ProjectsModule", "ContractModule", "projects", "contracts"]

    for module in module_names:
        key = f"wild_code/modules/{module}/show_numbers"
        value = settings.value(key, "NOT_FOUND")
        print(f"QGIS Setting [{key}]: {value}")

        # Also check ThemeManager
        try:
            tm_value = ThemeManager.load_module_setting(module, "show_numbers", "TM_NOT_FOUND")
            print(f"ThemeManager [{module}]: {tm_value}")
        except Exception as e:
            print(f"ThemeManager [{module}]: ERROR - {e}")

        print()

    # Check all wild_code settings
    print("All wild_code settings:")
    settings.beginGroup("wild_code")
    for key in settings.allKeys():
        value = settings.value(key)
        print(f"  {key}: {value}")
    settings.endGroup()

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
