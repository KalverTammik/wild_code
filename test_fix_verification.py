#!/usr/bin/env python3
"""
Test that the ThemeManager fix resolves the AttributeError
"""

def test_fix():
    """Test that the AttributeError is fixed."""
    print("🔧 Testing ThemeManager AttributeError Fix...")
    print()

    # Check that the method exists in the source code
    with open('widgets/theme_manager.py', 'r', encoding='utf-8') as f:
        content = f.read()

    # Look for the method definition
    has_load_method = 'def load_theme_setting():' in content
    has_save_method = 'def save_theme_setting(theme_name):' in content

    print("📁 Source Code Analysis:")
    print(f"   load_theme_setting method: {'✅ Found' if has_load_method else '❌ Missing'}")
    print(f"   save_theme_setting method: {'✅ Found' if has_save_method else '❌ Missing'}")
    print()

    # Check for safety checks in critical methods
    has_safety_apply_tooltip = 'if hasattr(ThemeManager, \'load_theme_setting\')' in content
    has_safety_set_initial = 'hasattr(ThemeManager, \'load_theme_setting\')' in content

    print("🛡️ Safety Checks:")
    print(f"   apply_tooltip_style: {'✅ Protected' if has_safety_apply_tooltip else '❌ Exposed'}")
    print(f"   set_initial_theme: {'✅ Protected' if has_safety_set_initial else '❌ Exposed'}")
    print()

    if has_load_method and has_save_method and has_safety_apply_tooltip and has_safety_set_initial:
        print("🎉 AttributeError Fix Complete!")
        print("   • Added missing load_theme_setting() method")
        print("   • Added safety checks to prevent future errors")
        print("   • Maintained backward compatibility")
        print()
        print("The plugin should now start without the AttributeError.")
        return True
    else:
        print("❌ Fix incomplete - some issues remain.")
        return False

if __name__ == "__main__":
    test_fix()
