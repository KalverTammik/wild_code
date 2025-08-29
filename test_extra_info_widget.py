#!/usr/bin/env python3
"""
Test script to demonstrate the new ExtraInfoWidget with three-column activity overview.
"""

import sys
import os

# Add the plugin root to the path
plugin_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
wild_code_root = os.path.join(plugin_root, 'wild_code')
sys.path.insert(0, wild_code_root)

from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel
from PyQt5.QtCore import Qt

# Import the ExtraInfoWidget
extra_info_path = os.path.join(wild_code_root, 'widgets', 'DataDisplayWidgets')
sys.path.insert(0, extra_info_path)

try:
    from ExtraInfoWidget import ExtraInfoWidget
except ImportError:
    # Try direct import if the path approach fails
    import importlib.util
    extra_info_file = os.path.join(wild_code_root, 'widgets', 'DataDisplayWidgets', 'ExtraInfoWidget.py')
    spec = importlib.util.spec_from_file_location("ExtraInfoWidget", extra_info_file)
    extra_info_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(extra_info_module)
    ExtraInfoWidget = extra_info_module.ExtraInfoWidget

class TestWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ExtraInfoWidget Test")
        self.setGeometry(100, 100, 600, 400)

        layout = QVBoxLayout(self)
        layout.setSpacing(20)

        # Test data
        test_item = {
            "id": "test-item",
            "title": "Test Item"
        }

        # Extra info widget
        extra_info = ExtraInfoWidget(test_item)
        layout.addWidget(QLabel("Activity Overview Widget:"))
        layout.addWidget(extra_info)

        # Instructions
        instructions = QLabel(
            "New ExtraInfoWidget Features:\n"
            "• Three-column layout: Tehtud, Töös, Tegemata\n"
            "• Color-coded columns (Green, Orange, Red)\n"
            "• Activity icons for each item\n"
            "• Hover effects on list items\n"
            "• Professional styling with rounded corners\n"
            "• Single-word Estonian activity names\n"
            "• Responsive column layout"
        )
        instructions.setWordWrap(True)
        layout.addWidget(instructions)

        self.show()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TestWindow()
    sys.exit(app.exec_())
