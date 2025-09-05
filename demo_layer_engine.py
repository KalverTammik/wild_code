#!/usr/bin/env python3
"""
Layer Creation Engine Demo Script

Demonstrates how to use the LayerCreationEngine and LayerCreationTestWidget.

Usage:
1. Run this script in QGIS Python console
2. Or import and use the functions in your code

Author: Wild Code Plugin Team
Date: September 3, 2025
"""

# Example usage of LayerCreationEngine
def demo_layer_engine():
    """
    Demonstrate basic layer creation engine usage.
    """
    print("=== Layer Creation Engine Demo ===")

    # Import the engine
    from engines.LayerCreationEngine import get_layer_engine, MailablGroupFolders

    # Get engine instance
    engine = get_layer_engine()
    print("✓ Layer engine initialized")

    # Create a memory layer
    layer_name = "DemoMemoryLayer"
    group_name = MailablGroupFolders.SANDBOXING

    memory_layer = engine.create_memory_layer_from_template(
        layer_name, None, None, None, "Point"
    )

    if memory_layer:
        print(f"✓ Memory layer '{layer_name}' created")

        # Add to group
        group = engine.get_or_create_group(group_name)
        group.addLayer(memory_layer)
        print(f"✓ Layer added to group '{group_name}'")
    else:
        print("✗ Failed to create memory layer")

    # Show available groups
    groups = engine.get_available_groups()
    print(f"Available groups: {groups}")

    print("=== Demo Complete ===")


def demo_test_widget():
    """
    Demonstrate how to create and show the test widget.
    """
    print("=== Test Widget Demo ===")

    try:
        from widgets.LayerCreationTestWidget import create_layer_test_widget
        from PyQt5.QtWidgets import QApplication

        # Create QApplication if it doesn't exist
        app = QApplication.instance()
        if app is None:
            app = QApplication([])

        # Create test widget
        test_widget = create_layer_test_widget()
        print("✓ Test widget created")

        # Show widget
        test_widget.show()
        print("✓ Test widget displayed")

        print("=== Test Widget Demo Complete ===")
        print("Close the widget window to continue...")

        # Note: In a real QGIS plugin, you would add this to a dialog or dock widget

    except ImportError as e:
        print(f"✗ Import error: {e}")
        print("Make sure you're running this in QGIS environment")
    except Exception as e:
        print(f"✗ Error: {e}")


def demo_quick_operations():
    """
    Demonstrate quick layer creation operations.
    """
    print("=== Quick Operations Demo ===")

    from engines.LayerCreationEngine import get_layer_engine

    engine = get_layer_engine()

    # Create different types of layers
    operations = [
        ("Property Sync Layer", engine.create_property_sync_layer),
        ("Archive Layer", engine.create_archive_layer),
        ("Import Layer", engine.create_import_layer),
    ]

    for name, operation in operations:
        print(f"Creating {name}...")
        result = operation()
        if result:
            print(f"✓ {name} created: {result}")
        else:
            print(f"✗ Failed to create {name}")

    print("=== Quick Operations Demo Complete ===")


# Main demo function
def run_all_demos():
    """
    Run all demonstration functions.
    """
    print("🚀 Starting Layer Creation Engine Demos")
    print("=" * 50)

    try:
        demo_layer_engine()
        print()
        demo_quick_operations()
        print()
        demo_test_widget()

    except Exception as e:
        print(f"✗ Demo error: {e}")
        import traceback
        traceback.print_exc()

    print("=" * 50)
    print("🎉 All demos completed!")



# For direct execution in QGIS Python console
if __name__ == "__main__":
    run_all_demos()
