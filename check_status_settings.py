#!/usr/bin/env python3
"""
Check status preferences in QGIS settings
"""

import sys
import os

# Add the plugin root to the path
plugin_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, plugin_root)

try:
    from qgis.core import QgsSettings

    print("🔍 Status Preferences Check")
    print("=" * 50)

    # Check QGIS settings directly
    settings = QgsSettings()

    # Check module status preferences
    module_names = ["ProjectsModule", "ContractModule"]

    for module in module_names:
        key = f"wild_code/modules/{module}/preferred_statuses"
        value = settings.value(key, "NOT_FOUND")
        print(f"QGIS Setting [{key}]: {value}")
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
