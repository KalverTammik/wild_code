#!/usr/bin/env python3
"""
Debug script to check module number display settings
"""

def debug_module_settings():
    """Debug the module settings to see what's happening."""
    print("🔍 Module Number Display Settings Debugger")
    print("=" * 50)

    # Check if we can import the necessary modules
    try:
        import sys
        import os
        sys.path.insert(0, os.path.dirname(__file__))

        # Try to import ThemeManager
        from widgets.theme_manager import ThemeManager
        print("✅ ThemeManager imported successfully")

        # Check available methods
        has_save = hasattr(ThemeManager, 'save_module_setting')
        has_load = hasattr(ThemeManager, 'load_module_setting')
        print(f"✅ save_module_setting method: {'Available' if has_save else 'Missing'}")
        print(f"✅ load_module_setting method: {'Available' if has_load else 'Missing'}")

        if has_save and has_load:
            print("\n🧪 Testing Settings Operations:")

            # Test with different module names
            test_modules = ["ProjectsModule", "projects", "ContractsModule", "contracts"]

            for module in test_modules:
                try:
                    # Test loading current setting
                    current = ThemeManager.load_module_setting(module, "show_numbers", "DEFAULT")
                    print(f"   {module}: current setting = {current}")

                    # Test saving and reloading
                    ThemeManager.save_module_setting(module, "show_numbers", False)
                    reloaded = ThemeManager.load_module_setting(module, "show_numbers", "DEFAULT")
                    print(f"   {module}: after setting to False = {reloaded}")

                    # Reset to True for testing
                    ThemeManager.save_module_setting(module, "show_numbers", True)
                    reset = ThemeManager.load_module_setting(module, "show_numbers", "DEFAULT")
                    print(f"   {module}: after resetting to True = {reset}")

                except Exception as e:
                    print(f"   {module}: ERROR - {e}")

        print("\n📋 Troubleshooting Tips:")
        print("1. Check that the module name matches exactly (case-sensitive)")
        print("2. Verify that QGIS settings are being saved")
        print("3. Make sure you're looking at newly created cards (not cached ones)")
        print("4. Check the QGIS Settings storage location")

        print("\n🔧 Expected Module Names:")
        print("   ProjectsModule (from ProjectsUi.py)")
        print("   ContractsModule (from ContractsUi.py)")

    except Exception as e:
        print(f"❌ Error during debugging: {e}")
        print("This might be due to import issues or missing dependencies.")

if __name__ == "__main__":
    debug_module_settings()
