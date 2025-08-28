#!/usr/bin/env python3
"""
Test ThemeManager methods availability
"""

def test_theme_manager_methods():
    """Test that ThemeManager has the required methods."""
    try:
        # Add current directory to path for imports
        import sys
        import os
        sys.path.insert(0, os.path.dirname(__file__))

        # Import ThemeManager
        from widgets.theme_manager import ThemeManager

        # Check methods exist
        has_load = hasattr(ThemeManager, 'load_theme_setting')
        has_save = hasattr(ThemeManager, 'save_theme_setting')
        has_save_module = hasattr(ThemeManager, 'save_module_setting')
        has_load_module = hasattr(ThemeManager, 'load_module_setting')

        print("✅ ThemeManager Methods Check:")
        print(f"   load_theme_setting: {'✅' if has_load else '❌'}")
        print(f"   save_theme_setting: {'✅' if has_save else '❌'}")
        print(f"   save_module_setting: {'✅' if has_save_module else '❌'}")
        print(f"   load_module_setting: {'✅' if has_load_module else '❌'}")

        if all([has_load, has_save, has_save_module, has_load_module]):
            print("\n🎉 All ThemeManager methods are available!")
            return True
        else:
            print("\n❌ Some methods are missing!")
            return False

    except Exception as e:
        print(f"❌ Error testing ThemeManager: {e}")
        return False

if __name__ == "__main__":
    test_theme_manager_methods()
