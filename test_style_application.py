#!/usr/bin/env python3
"""
Test script for SHPLayerLoader style application.
Tests the style application functionality in isolation.
"""

import sys
import os

# Add the plugin path to sys.path
sys.path.insert(0, r"c:\Users\Kalver\AppData\Roaming\QGIS\QGIS3\profiles\default\python\plugins\wild_code")

def test_style_application():
    """Test style application on an existing layer."""
    try:
        from qgis.core import QgsProject, QgsVectorLayer
        from utils.SHPLayerLoader import SHPLayerLoader

        # Get the current project
        project = QgsProject.instance()
        print(f"Current project: {project.fileName()}")

        # Find a memory layer to test with
        test_layer = None
        for layer in project.mapLayers().values():
            if "memory" in layer.name().lower():
                test_layer = layer
                break

        if not test_layer:
            print("No memory layer found for testing")
            return

        print(f"Found test layer: {test_layer.name()}")

        # Create SHPLayerLoader instance
        loader = SHPLayerLoader()

        # Test style application
        print("Testing style application...")
        result = loader._apply_qml_style(test_layer)
        print(f"Style application result: {result}")

    except Exception as e:
        print(f"Error in test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_style_application()
