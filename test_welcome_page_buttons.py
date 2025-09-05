#!/usr/bin/env python3
"""
WelcomePage Layer Creation Test

Demonstrates the new layer creation buttons added to the WelcomePage.

Usage:
1. Open your QGIS plugin
2. Navigate to the Welcome/Home page (Avaleht)
3. You should see two new buttons:
   - "Loo Mailabl grupp kiht" (Create Mailabl Group Layer)
   - "Eemalda grupp kiht" (Remove Group Layer)
4. Click the buttons to test layer creation and removal

Author: Wild Code Plugin Team
Date: September 3, 2025
"""

def test_welcome_page_buttons():
    """
    Test function to verify the WelcomePage buttons are working.

    This function can be called from QGIS Python console to test
    the layer creation functionality without opening the full UI.
    """
    print("=== WelcomePage Layer Creation Test ===")

    try:
        from widgets.WelcomePage import WelcomePage
        from engines.LayerCreationEngine import get_layer_engine, MailablGroupFolders

        # Create a WelcomePage instance (without showing it)
        welcome_page = WelcomePage()

        # Get the layer engine
        engine = get_layer_engine()

        print("✓ WelcomePage and LayerCreationEngine initialized")

        # Test creating a layer
        print("\n--- Testing Layer Creation ---")
        layer_name = "WelcomePageTestLayer"
        result = engine.copy_virtual_layer_for_properties(
            layer_name,
            MailablGroupFolders.MAILABL_MAIN
        )

        if result:
            print(f"✓ Layer '{result}' created successfully")
        else:
            print("✗ Failed to create layer")

        # Check available groups
        groups = engine.get_available_groups()
        print(f"Available groups: {groups}")

        # Check layers in the main group
        layers = engine.get_layers_in_group(MailablGroupFolders.MAILABL_MAIN)
        print(f"Layers in '{MailablGroupFolders.MAILABL_MAIN}': {[l.name() for l in layers]}")

        print("\n=== Test Complete ===")
        print("You can now test the buttons in the WelcomePage UI!")

    except Exception as e:
        print(f"✗ Test error: {e}")
        import traceback
        traceback.print_exc()


# For direct execution in QGIS Python console

# For direct execution in QGIS Python console
if __name__ == "__main__":
    test_welcome_page_buttons()
