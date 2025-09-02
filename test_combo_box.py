#!/usr/bin/env python3
"""
Test script for LayerTreePicker combo box appearance.
This demonstrates the new horizontal layout with separate dropdown frame.
"""

import sys
from PyQt5.QtWidgets import QApplication, QVBoxLayout, QWidget, QLabel
from PyQt5.QtCore import Qt

# Add the plugin path to sys.path for imports
sys.path.insert(0, r"c:\Users\Kalver\AppData\Roaming\QGIS\QGIS3\profiles\default\python\plugins\wild_code")

try:
    from widgets.layer_dropdown import LayerTreePicker
except ImportError as e:
    print(f"Import error: {e}")
    sys.exit(1)

class TestWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("LayerTreePicker Combo Box Test")
        self.setGeometry(100, 100, 400, 200)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)

        # Instructions
        instructions = QLabel("Test the new combo box appearance:")
        instructions.setStyleSheet("font-weight: bold; color: #333;")
        layout.addWidget(instructions)

        # Create LayerTreePicker widget
        self.layer_picker = LayerTreePicker(self, placeholder="Select a layer...")
        layout.addWidget(self.layer_picker)

        # Create a standard QComboBox for comparison
        from PyQt5.QtWidgets import QComboBox
        self.standard_combo = QComboBox(self)
        self.standard_combo.addItems(["Option 1", "Option 2", "Option 3"])
        self.standard_combo.setCurrentText("Standard ComboBox")
        layout.addWidget(self.standard_combo)

        # Size comparison label
        self.size_label = QLabel("LayerTreePicker: 180px wide (content fills frame completely) x 20px height")
        self.size_label.setStyleSheet("font-weight: bold; color: #666; margin-top: 10px;")
        layout.addWidget(self.size_label)

        # Status label
        self.status_label = QLabel("Click the dropdown to test the combo box appearance")
        layout.addWidget(self.status_label)

        # Connect signals
        self.layer_picker.layerChanged.connect(self.on_layer_changed)

        # Apply light theme styling
        self.apply_light_theme()

    def apply_light_theme(self):
        """Apply light theme QSS styling."""
        try:
            # Apply QSS from the light theme file
            with open(r"c:\Users\Kalver\AppData\Roaming\QGIS\QGIS3\profiles\default\python\plugins\wild_code\styles\Light\LayerTreePicker.qss", 'r') as f:
                qss_content = f.read()
            self.layer_picker.setStyleSheet(qss_content)
            print("Applied light theme styling")
        except Exception as e:
            print(f"Failed to apply light theme: {e}")

    def on_layer_changed(self, layer):
        """Handle layer selection changes."""
        if layer:
            self.status_label.setText(f"Selected layer: {layer.name()}")
        else:
            self.status_label.setText("No layer selected")

def main():
    app = QApplication(sys.argv)

    # Set application properties for better styling
    app.setStyle("Fusion")

    window = TestWindow()
    window.show()

    print("LayerTreePicker combo box test window opened.")
    print("Features to test:")
    print("- Horizontal layout with separate button and dropdown frame")
    print("- Container-level glow effect")
    print("- Clickable dropdown frame")
    print("- Proper combo box appearance")

    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
