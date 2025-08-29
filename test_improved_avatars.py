#!/usr/bin/env python3
"""
Test script to demonstrate the improved AvatarBubble styling.
"""

import sys
import os

# Add the plugin root to the path
plugin_root = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, plugin_root)

from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QHBoxLayout
from PyQt5.QtCore import Qt

# Import the MembersView
members_view_path = os.path.join(plugin_root, 'widgets', 'DataDisplayWidgets')
sys.path.insert(0, members_view_path)

try:
    from MembersView import MembersView, AvatarBubble
except ImportError:
    # Try direct import if the path approach fails
    import importlib.util
    members_view_file = os.path.join(plugin_root, 'widgets', 'DataDisplayWidgets', 'MembersView.py')
    spec = importlib.util.spec_from_file_location("MembersView", members_view_file)
    members_view_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(members_view_module)
    MembersView = members_view_module.MembersView
    AvatarBubble = members_view_module.AvatarBubble

# Import the MembersView
sys.path.insert(0, os.path.join(plugin_root, 'widgets', 'DataDisplayWidgets'))

# Direct import
import MembersView
MembersViewClass = MembersView.MembersView
AvatarBubbleClass = MembersView.AvatarBubble

class TestWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Improved Avatar Bubbles Test")
        self.setGeometry(100, 100, 500, 300)

        layout = QVBoxLayout(self)
        layout.setSpacing(20)

        # Test data with multiple participants and responsible members
        test_item = {
            "members": {
                "edges": [
                    {
                        "isResponsible": True,
                        "node": {"displayName": "John Smith", "active": True}
                    },
                    {
                        "isResponsible": True,
                        "node": {"displayName": "Sarah Manager", "active": True}
                    },
                    {
                        "isResponsible": False,
                        "node": {"displayName": "Alice Johnson", "active": True}
                    },
                    {
                        "isResponsible": False,
                        "node": {"displayName": "Bob Wilson", "active": True}
                    },
                    {
                        "isResponsible": False,
                        "node": {"displayName": "Carol Brown", "active": True}
                    },
                    {
                        "isResponsible": False,
                        "node": {"displayName": "David Lee", "active": True}
                    }
                ]
            }
        }

        # Regular members view
        regular_view = MembersViewClass(test_item, compact=False)
        layout.addWidget(QLabel("Regular Members View:"))
        layout.addWidget(regular_view)

        # Compact members view
        compact_view = MembersViewClass(test_item, compact=True)
        layout.addWidget(QLabel("Compact Members View:"))
        layout.addWidget(compact_view)

        # Individual avatar bubbles demo with card stacking
        avatar_layout = QHBoxLayout()
        avatar_layout.setSpacing(0)  # No spacing for card stacking
        test_names = ["John Smith", "Alice Johnson", "Bob Wilson", "Carol Brown", "David Lee"]
        overlap_amount = int(36 * 0.8)  # 80% overlap
        for i, name in enumerate(test_names):
            bubble = AvatarBubbleClass(name, size=36, first=(i==0), salt="demo")
            if i > 0:  # Apply overlap to non-first bubbles
                bubble.setContentsMargins(-overlap_amount, 0, 0, 0)
            avatar_layout.addWidget(bubble)
        avatar_layout.addStretch()
        layout.addWidget(QLabel("Card Stacked Avatar Bubbles (36px, 80% overlap):"))
        layout.addLayout(avatar_layout)

        # Instructions
        instructions = QLabel(
            "Enhanced Card Stacking Avatar Improvements:\n"
            "• Responsible members shown as centered avatar bubbles at top\n"
            "• Star icon (★) at bottom-right corner of responsible avatars\n"
            "• Responsible avatars match participant size (32px/28px)\n"
            "• Pronounced 80% overlap for authentic card stacking effect\n"
            "• Zero spacing between participant bubbles using QWidget margins\n"
            "• Enhanced shadow depth (16px blur, 4px offset)\n"
            "• Increased scale effect (1.08x) on hover for better interaction\n"
            "• Bolder font weight (700) for improved readability\n"
            "• Increased padding (3px) for better letter spacing\n"
            "• Theme-aware shadows for better integration\n"
            "• Optimized letter spacing (-0.3px) for cleaner text\n"
            "• QWidget contents margins for reliable overlap control"
        )
        instructions.setWordWrap(True)
        layout.addWidget(instructions)

        self.show()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TestWindow()
    sys.exit(app.exec_())
