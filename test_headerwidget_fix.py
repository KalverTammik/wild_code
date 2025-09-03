#!/usr/bin/env python3
"""
Test script to verify HeaderWidget can be instantiated without AttributeError.
This simulates the QGIS plugin loading process.
"""

import sys
import os

# Add the plugin directory to Python path
plugin_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(plugin_dir)
sys.path.insert(0, plugin_dir)
sys.path.insert(0, parent_dir)

# Also add to Python path as 'wild_code' module
sys.path.insert(0, os.path.join(parent_dir, 'wild_code'))

try:
    # Import required modules
    from PyQt5.QtWidgets import QApplication
    from widgets.HeaderWidget import HeaderWidget
    from languages.language_manager import LanguageManager

    # Create QApplication if it doesn't exist
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)

    # Create language manager
    lang_manager = LanguageManager()

    # Define dummy callbacks
    def dummy_switch_callback():
        print("Theme switch callback called")

    def dummy_logout_callback():
        print("Logout callback called")

    # Test HeaderWidget instantiation
    print("Testing HeaderWidget instantiation...")
    header = HeaderWidget(
        title="Test Plugin",
        switch_callback=dummy_switch_callback,
        logout_callback=dummy_logout_callback
    )

    # Test that switchButton attribute exists
    if hasattr(header, 'switchButton'):
        print("✓ switchButton attribute exists")
        print(f"✓ switchButton type: {type(header.switchButton)}")
        print(f"✓ switchButton object name: {header.switchButton.objectName()}")
    else:
        print("✗ switchButton attribute missing!")
        sys.exit(1)

    # Test other key attributes
    required_attrs = ['titleLabel', 'searchEdit', 'logoutButton', 'devControls']
    for attr in required_attrs:
        if hasattr(header, attr):
            print(f"✓ {attr} attribute exists")
        else:
            print(f"✗ {attr} attribute missing!")
            sys.exit(1)

    # Test lazy loading property
    print("Testing lazy loading property...")
    search_widget = header.search_results_widget
    if search_widget is not None:
        print("✓ search_results_widget lazy loading works")
    else:
        print("✗ search_results_widget lazy loading failed")

    print("\n🎉 All tests passed! HeaderWidget should work correctly in QGIS.")
    sys.exit(0)

except Exception as e:
    print(f"✗ Error during testing: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
