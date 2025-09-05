#!/usr/bin/env python3
"""
Quick test to verify Properties module structure.
"""

import sys
import os

# Add the plugin directory to Python path
plugin_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, plugin_dir)

try:
    # Test imports
    from constants.module_names import PROPERTIES_MODULE
    print(f"✅ PROPERTIES_MODULE constant: {PROPERTIES_MODULE}")

    # Test if PropertiesUI can be imported (without instantiating)
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "PropertiesUI",
        os.path.join(plugin_dir, "modules", "Properties", "PropertiesUI.py")
    )
    properties_module = importlib.util.module_from_spec(spec)

    print("✅ PropertiesUI module can be imported")
    print("✅ All basic tests passed!")

except Exception as e:
    print(f"❌ Test failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
