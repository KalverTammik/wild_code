#!/usr/bin/env python3
"""
Test script to demonstrate the compact InfoCardHeader design.
"""

import sys
import os

# Add the plugin root to the path
plugin_root = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, plugin_root)

from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QHBoxLayout
from PyQt5.QtCore import Qt

# Import the InfoCardHeader
sys.path.insert(0, os.path.join(plugin_root, 'widgets', 'DataDisplayWidgets'))
from InfoCardHeader import InfocardHeaderFrame

class TestWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Compact Header Test")
        self.setGeometry(100, 100, 600, 400)

        layout = QVBoxLayout(self)
        layout.setSpacing(20)

        # Test data
        test_item = {
            "name": "Sample Project with a Long Name",
            "number": "123",
            "client": {"displayName": "Test Client Company"},
            "isPublic": False,
            "tags": [
                {"name": "urgent", "color": "#ff4444"},
                {"name": "review", "color": "#44ff44"}
            ]
        }

        # Regular header
        regular_header = InfocardHeaderFrame(test_item, compact=False)
        layout.addWidget(QLabel("Regular Header:"))
        layout.addWidget(regular_header)

        # Compact header
        compact_header = InfocardHeaderFrame(test_item, compact=True)
        layout.addWidget(QLabel("Compact Header:"))
        layout.addWidget(compact_header)

        # Instructions
        instructions = QLabel(
            "Compare the two headers:\n"
            "• Smaller fonts (13px → 12px in compact)\n"
            "• Tighter spacing (6px → 4px)\n"
            "• Smaller number badges (24px → 20px min width)\n"
            "• Smaller icons (16px → 14px)\n"
            "• Reduced vertical spacing\n"
            "• More professional, space-efficient look"
        )
        instructions.setWordWrap(True)
        layout.addWidget(instructions)

        self.show()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TestWindow()
    sys.exit(app.exec_())
