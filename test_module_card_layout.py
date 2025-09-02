#!/usr/bin/env python3
"""
Test script demonstrating side-by-side layer configuration layout concept.
"""

import sys
from PyQt5.QtWidgets import QApplication, QVBoxLayout, QWidget, QLabel, QFrame, QHBoxLayout, QGroupBox

class TestWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Side-by-Side Layer Configuration Demo")
        self.setGeometry(100, 100, 1200, 600)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)

        # Instructions
        instructions = QLabel("Demonstrating side-by-side layer configurations:")
        instructions.setStyleSheet("font-weight: bold; color: #333;")
        layout.addWidget(instructions)

        # Create demo layout structure
        self.create_demo_layout(layout)

        # Layout description
        layout_desc = QLabel("Layout Structure:\n"
                           "• Row 1: Main Layer + Archive Layer (side by side)\n"
                           "• Row 2: Display Options + Status Preferences (side by side)\n"
                           "• Each group: Control + Explanation (side by side)\n"
                           "• Better space utilization and visual organization")
        layout_desc.setStyleSheet("color: #666; font-size: 11px; padding: 10px; background: #f9f9f9; border-radius: 5px;")
        layout_desc.setWordWrap(True)
        layout.addWidget(layout_desc)

    def create_demo_layout(self, parent_layout):
        """Create a demo layout showing the side-by-side concept."""

        # Layer configurations container - arrange main and archive side by side
        layers_container = QFrame()
        layers_container.setObjectName("LayersContainer")
        layers_container.setStyleSheet("QFrame { border: 1px solid #ddd; border-radius: 5px; padding: 5px; }")
        layers_layout = QHBoxLayout(layers_container)
        layers_layout.setSpacing(8)

        # Main layer group
        main_group = QGroupBox("Modules main layer")
        main_layout = QHBoxLayout(main_group)
        main_layout.setContentsMargins(4, 4, 4, 4)
        main_layout.setSpacing(6)

        # Demo LayerTreePicker (simulated)
        main_picker = QLabel("🔽 LayerTreePicker\n180px × 20px")
        main_picker.setStyleSheet("background: #f0f0f0; border: 1px solid #ccc; padding: 2px 8px; border-radius: 3px; min-width: 140px; min-height: 20px;")
        main_layout.addWidget(main_picker, 2)

        # Explanation text
        main_explanation = QLabel("See on teie mooduli põhikiht. Valige kiht, mis sisaldab peamisi andmeid...")
        main_explanation.setWordWrap(True)
        main_explanation.setStyleSheet("color: #888; font-size: 11px; padding: 4px 0px;")
        main_explanation.setMinimumWidth(200)
        main_layout.addWidget(main_explanation, 1)

        layers_layout.addWidget(main_group)

        # Archive layer group
        archive_group = QGroupBox("Archive layer")
        archive_layout = QHBoxLayout(archive_group)
        archive_layout.setContentsMargins(4, 4, 4, 4)
        archive_layout.setSpacing(6)

        # Demo LayerTreePicker (simulated)
        archive_picker = QLabel("🔽 LayerTreePicker\n180px × 20px")
        archive_picker.setStyleSheet("background: #f0f0f0; border: 1px solid #ccc; padding: 2px 8px; border-radius: 3px; min-width: 140px; min-height: 20px;")
        archive_layout.addWidget(archive_picker, 2)

        # Explanation text
        archive_explanation = QLabel("See valikuline arhiivikiht salvestab ajaloolisi või varukoopia andmeid...")
        archive_explanation.setWordWrap(True)
        archive_explanation.setStyleSheet("color: #888; font-size: 11px; padding: 4px 0px;")
        archive_explanation.setMinimumWidth(200)
        archive_layout.addWidget(archive_explanation, 1)

        layers_layout.addWidget(archive_group)

        parent_layout.addWidget(layers_container)

        # Options container - arrange display and status preferences side by side
        options_container = QFrame()
        options_container.setObjectName("OptionsContainer")
        options_container.setStyleSheet("QFrame { border: 1px solid #ddd; border-radius: 5px; padding: 5px; }")
        options_layout = QHBoxLayout(options_container)
        options_layout.setSpacing(8)

        # Display options group
        display_group = QGroupBox("Display Options")
        display_layout = QHBoxLayout(display_group)
        display_layout.setContentsMargins(4, 4, 4, 4)
        display_layout.setSpacing(6)

        # Settings container
        settings_container = QFrame()
        settings_layout = QVBoxLayout(settings_container)
        settings_layout.setContentsMargins(0, 0, 0, 0)

        # Checkbox simulation
        checkbox = QLabel("☐ Show project numbers")
        checkbox.setStyleSheet("padding: 2px;")
        settings_layout.addWidget(checkbox)

        display_layout.addWidget(settings_container, 2)

        # Explanation text
        display_explanation = QLabel("When enabled, project/contract numbers will be displayed in item cards...")
        display_explanation.setWordWrap(True)
        display_explanation.setStyleSheet("color: #888; font-size: 11px; padding: 4px 0px;")
        display_explanation.setMinimumWidth(200)
        display_layout.addWidget(display_explanation, 1)

        options_layout.addWidget(display_group)

        # Status preferences group
        status_group = QGroupBox("Status Preferences")
        status_layout = QHBoxLayout(status_group)
        status_layout.setContentsMargins(4, 4, 4, 4)
        status_layout.setSpacing(6)

        # Status filter simulation
        status_container = QFrame()
        status_layout_inner = QVBoxLayout(status_container)
        status_layout_inner.setContentsMargins(0, 0, 0, 0)

        status_filter = QLabel("Status Filter Widget\n[Multiple selection]")
        status_filter.setStyleSheet("background: #f8f8f8; border: 1px solid #ddd; padding: 10px; border-radius: 3px;")
        status_layout_inner.addWidget(status_filter)

        status_layout.addWidget(status_container, 2)

        # Explanation text
        status_explanation = QLabel("Select statuses you want to prioritize for this module...")
        status_explanation.setWordWrap(True)
        status_explanation.setStyleSheet("color: #888; font-size: 11px; padding: 4px 0px;")
        status_explanation.setMinimumWidth(200)
        status_layout.addWidget(status_explanation, 1)

        options_layout.addWidget(status_group)

        parent_layout.addWidget(options_container)

def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    window = TestWindow()
    window.show()

    print("Side-by-side layer configuration demo opened.")
    print("Features demonstrated:")
    print("- Main Layer and Archive Layer side by side")
    print("- Display Options and Status Preferences side by side")
    print("- Each group has control + explanation horizontally")
    print("- Better space utilization and visual organization")
    print("- 180px wide LayerTreePicker widgets with proper content filling")

    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
