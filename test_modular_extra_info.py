#!/usr/bin/env python3
"""
Test script to demonstrate the new modular ExtraInfoWidget system.
Shows different configurations for project, contract, and document modules.
"""

import sys
import os

# Add the plugin root to the path
plugin_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
wild_code_root = os.path.join(plugin_root, 'wild_code')
sys.path.insert(0, wild_code_root)

from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QHBoxLayout, QPushButton, QGroupBox
from PyQt5.QtCore import Qt

# Import the modular ExtraInfoWidget
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


class ModuleTestWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Modular ExtraInfoWidget Test")
        self.setGeometry(100, 100, 1000, 700)

        layout = QVBoxLayout(self)

        # Title
        title = QLabel("Modular ExtraInfoWidget System Test")
        title.setStyleSheet("font-weight: bold; font-size: 16px; color: #333; margin-bottom: 20px;")
        layout.addWidget(title)

        # Module selection buttons
        button_layout = QHBoxLayout()

        self.project_btn = QPushButton("Project Module")
        self.contract_btn = QPushButton("Contract Module")
        self.document_btn = QPushButton("Document Module")

        for btn in [self.project_btn, self.contract_btn, self.document_btn]:
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #2196F3;
                    color: white;
                    border: none;
                    padding: 10px 20px;
                    border-radius: 5px;
                    font-weight: bold;
                    font-size: 12px;
                }
                QPushButton:hover {
                    background-color: #1976D2;
                }
            """)
            button_layout.addWidget(btn)

        layout.addLayout(button_layout)

        # Container for the widget
        self.widget_container = QWidget()
        self.widget_container.setStyleSheet("""
            QWidget {
                border: 2px solid #ddd;
                border-radius: 8px;
                background-color: #f9f9f9;
                padding: 10px;
            }
        """)
        container_layout = QVBoxLayout(self.widget_container)

        # Placeholder label
        self.placeholder = QLabel("Select a module type to see its ExtraInfoWidget")
        self.placeholder.setStyleSheet("font-size: 14px; color: #666; text-align: center;")
        self.placeholder.setAlignment(Qt.AlignCenter)
        container_layout.addWidget(self.placeholder)

        layout.addWidget(self.widget_container)

        # Connect buttons
        self.project_btn.clicked.connect(lambda: self.show_module_widget("project"))
        self.contract_btn.clicked.connect(lambda: self.show_module_widget("contract"))
        self.document_btn.clicked.connect(lambda: self.show_module_widget("document"))

        # Info section
        info_group = QGroupBox("System Information")
        info_layout = QVBoxLayout(info_group)

        info_text = QLabel("""
        <b>Modular ExtraInfoWidget System</b><br><br>
        This system uses a Factory Pattern + Configuration approach:<br>
        • <b>ModuleConfig:</b> Defines layout and content for each module type<br>
        • <b>ModuleConfigFactory:</b> Creates appropriate configurations<br>
        • <b>ExtraInfoWidget:</b> Uses configuration to build UI dynamically<br><br>
        <b>Benefits:</b><br>
        ✓ Easy to add new module types<br>
        ✓ Centralized configuration management<br>
        ✓ Consistent UI patterns across modules<br>
        ✓ Future-proof for shared features<br>
        ✓ Maintains separation of concerns
        """)
        info_text.setWordWrap(True)
        info_text.setTextFormat(Qt.RichText)
        info_layout.addWidget(info_text)

        layout.addWidget(info_group)

    def show_module_widget(self, module_type):
        """Show the ExtraInfoWidget for the selected module type."""
        # Clear existing widget
        for i in reversed(range(self.widget_container.layout().count())):
            widget = self.widget_container.layout().itemAt(i).widget()
            if widget is not None:
                widget.setParent(None)

        # Create sample data for the module
        sample_data = {
            'module_type': module_type,
            'id': f'sample_{module_type}_123',
            'name': f'Sample {module_type.title()} Item'
        }

        # Create and add the widget
        widget = ExtraInfoWidget(sample_data, module_type)
        self.widget_container.layout().addWidget(widget)

        # Update button styles
        self.project_btn.setStyleSheet(self.project_btn.styleSheet().replace("#2196F3", "#2196F3"))
        self.contract_btn.setStyleSheet(self.contract_btn.styleSheet().replace("#2196F3", "#2196F3"))
        self.document_btn.setStyleSheet(self.document_btn.styleSheet().replace("#2196F3", "#2196F3"))

        # Highlight selected button
        if module_type == "project":
            self.project_btn.setStyleSheet(self.project_btn.styleSheet().replace("#2196F3", "#4CAF50"))
        elif module_type == "contract":
            self.contract_btn.setStyleSheet(self.contract_btn.styleSheet().replace("#2196F3", "#4CAF50"))
        elif module_type == "document":
            self.document_btn.setStyleSheet(self.document_btn.styleSheet().replace("#2196F3", "#4CAF50"))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ModuleTestWindow()
    window.show()
    sys.exit(app.exec_())
