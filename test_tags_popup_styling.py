#!/usr/bin/env python3
"""
Test script to verify TagsPopup styling is working correctly.
"""

import sys
import os

# Add the plugin root to the path
plugin_root = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, plugin_root)

from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QPushButton
from PyQt5.QtCore import Qt

# Import the TagPopup class
sys.path.insert(0, os.path.join(plugin_root, 'widgets', 'DataDisplayWidgets'))
from InfoCardHeader import TagPopup

class TestWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("TagsPopup Styling Test")
        self.setGeometry(100, 100, 400, 300)

        layout = QVBoxLayout(self)

        # Test data
        test_item = {
            "tags": [
                {"name": "urgent", "color": "#ff4444"},
                {"name": "review", "color": "#44ff44"},
                {"name": "pending", "color": "#4444ff"},
                {"name": "completed", "color": "#ffff44"},
                {"name": "high-priority", "color": "#ff44ff"}
            ]
        }

        # Create test button
        test_btn = QPushButton("Test TagsPopup Styling")
        test_btn.clicked.connect(lambda: self.show_tags_popup(test_item))
        layout.addWidget(test_btn)

        # Instructions
        instructions = QLabel("Click the button to test the TagsPopup styling.\n"
                            "You should see:\n"
                            "• Light blue border (rgba(9, 144, 143, 0.4))\n"
                            "• Rounded corners (8px)\n"
                            "• Shadow effects\n"
                            "• Dark background with transparency")
        instructions.setWordWrap(True)
        layout.addWidget(instructions)

        self.show()

    def show_tags_popup(self, item_data):
        popup = TagPopup(item_data, self)
        popup.show_near(self)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TestWindow()
    sys.exit(app.exec_())
