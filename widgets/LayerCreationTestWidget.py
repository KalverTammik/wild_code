#!/usr/bin/env python3
"""
Layer Creation Test Widget

Temporary widget for testing layer creation functionality.
Provides buttons to test different layer operations using the LayerCreationEngine.

Author: Wild Code Plugin Team
Date: September 3, 2025
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QGroupBox, QTextEdit, QMessageBox, QComboBox, QLineEdit
)
from PyQt5.QtCore import Qt
from qgis.core import QgsProject, QgsVectorLayer
from .LayerCreationEngine import get_layer_engine, MailablGroupFolders


class LayerCreationTestWidget(QWidget):
    """
    Test widget for layer creation engine functionality.

    Provides UI controls to test:
    - Memory layer creation
    - Virtual layer copying
    - GeoPackage persistence
    - Group management
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.engine = get_layer_engine()
        self.setup_ui()
        self.connect_signals()

    def setup_ui(self):
        """Setup the user interface."""
        self.setWindowTitle("Layer Creation Engine Test")
        self.setMinimumWidth(500)
        self.setMinimumHeight(600)

        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)

        # Title
        title = QLabel("Layer Creation Engine Test")
        title.setStyleSheet("font-size: 14px; font-weight: bold; color: #2E7D32;")
        layout.addWidget(title)

        # Description
        desc = QLabel("Test layer creation, management, and persistence operations")
        desc.setStyleSheet("color: #666;")
        layout.addWidget(desc)

        # Layer Operations Group
        operations_group = QGroupBox("Layer Operations")
        operations_layout = QVBoxLayout(operations_group)

        # Layer name input
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("Layer Name:"))
        self.layer_name_input = QLineEdit("TestLayer")
        name_layout.addWidget(self.layer_name_input)
        operations_layout.addLayout(name_layout)

        # Group selection
        group_layout = QHBoxLayout()
        group_layout.addWidget(QLabel("Target Group:"))
        self.group_combo = QComboBox()
        self.group_combo.addItems([
            MailablGroupFolders.NEW_PROPERTIES,
            MailablGroupFolders.SANDBOXING,
            MailablGroupFolders.ARCHIVE,
            MailablGroupFolders.IMPORT,
            MailablGroupFolders.EXPORT,
            MailablGroupFolders.SYNC
        ])
        group_layout.addWidget(self.group_combo)
        operations_layout.addLayout(group_layout)

        # Buttons
        buttons_layout = QHBoxLayout()

        # Create Memory Layer
        self.create_memory_btn = QPushButton("Create Memory Layer")
        self.create_memory_btn.setToolTip("Create a new memory layer in selected group")
        buttons_layout.addWidget(self.create_memory_btn)

        # Copy Virtual Layer
        self.copy_virtual_btn = QPushButton("Copy Virtual Layer")
        self.copy_virtual_btn.setToolTip("Create virtual copy for property operations")
        buttons_layout.addWidget(self.copy_virtual_btn)

        operations_layout.addLayout(buttons_layout)

        # Second row of buttons
        buttons2_layout = QHBoxLayout()

        # Save to GeoPackage
        self.save_geopackage_btn = QPushButton("Save to GeoPackage")
        self.save_geopackage_btn.setToolTip("Save memory layer to GeoPackage file")
        buttons2_layout.addWidget(self.save_geopackage_btn)

        # Create Property Sync Layer
        self.property_sync_btn = QPushButton("Property Sync Layer")
        self.property_sync_btn.setToolTip("Create layer for property synchronization")
        buttons2_layout.addWidget(self.property_sync_btn)

        operations_layout.addLayout(buttons2_layout)

        layout.addWidget(operations_group)

        # Quick Actions Group
        quick_group = QGroupBox("Quick Actions")
        quick_layout = QVBoxLayout(quick_group)

        quick_buttons_layout = QHBoxLayout()

        # Archive Layer
        self.archive_btn = QPushButton("Create Archive Layer")
        self.archive_btn.setToolTip("Create layer for archiving operations")
        quick_buttons_layout.addWidget(self.archive_btn)

        # Import Layer
        self.import_btn = QPushButton("Create Import Layer")
        self.import_btn.setToolTip("Create layer for import operations")
        quick_buttons_layout.addWidget(self.import_btn)

        quick_layout.addLayout(quick_buttons_layout)
        layout.addWidget(quick_group)

        # Information Group
        info_group = QGroupBox("Information")
        info_layout = QVBoxLayout(info_group)

        # Available Groups
        self.groups_info = QTextEdit()
        self.groups_info.setMaximumHeight(80)
        self.groups_info.setReadOnly(True)
        info_layout.addWidget(QLabel("Available Groups:"))
        info_layout.addWidget(self.groups_info)

        # Status
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("color: #2E7D32; font-weight: bold;")
        info_layout.addWidget(self.status_label)

        layout.addWidget(info_group)

        # Refresh button
        refresh_btn = QPushButton("Refresh Information")
        refresh_btn.clicked.connect(self.refresh_info)
        layout.addWidget(refresh_btn)

        # Initial info update
        self.refresh_info()

    def connect_signals(self):
        """Connect button signals to handlers."""
        self.create_memory_btn.clicked.connect(self.create_memory_layer)
        self.copy_virtual_btn.clicked.connect(self.copy_virtual_layer)
        self.save_geopackage_btn.clicked.connect(self.save_to_geopackage)
        self.property_sync_btn.clicked.connect(self.create_property_sync_layer)
        self.archive_btn.clicked.connect(self.create_archive_layer)
        self.import_btn.clicked.connect(self.create_import_layer)

    def refresh_info(self):
        """Refresh information display."""
        try:
            groups = self.engine.get_available_groups()
            if groups:
                self.groups_info.setText("\n".join(f"• {group}" for group in groups))
            else:
                self.groups_info.setText("No groups available")

            self.status_label.setText("Information updated")
            self.status_label.setStyleSheet("color: #2E7D32; font-weight: bold;")
        except Exception as e:
            self.groups_info.setText(f"Error: {str(e)}")
            self.status_label.setText("Error updating info")
            self.status_label.setStyleSheet("color: #FF5722; font-weight: bold;")

    def get_current_layer_name(self) -> str:
        """Get current layer name from input."""
        name = self.layer_name_input.text().strip()
        return name if name else "TestLayer"

    def get_current_group(self) -> str:
        """Get current group from combo box."""
        return self.group_combo.currentText()

    def create_memory_layer(self):
        """Create a memory layer."""
        try:
            layer_name = self.get_current_layer_name()
            group_name = self.get_current_group()

            # Create memory layer
            memory_layer = self.engine.create_memory_layer_from_template(
                layer_name, None, None, None, "Point"
            )

            if memory_layer:
                # Add to group
                group = self.engine.get_or_create_group(group_name)
                group.addLayer(memory_layer)

                self.show_success(f"Memory layer '{layer_name}' created in group '{group_name}'")
                self.refresh_info()
            else:
                self.show_error("Failed to create memory layer")

        except Exception as e:
            self.show_error(f"Error creating memory layer: {str(e)}")

    def copy_virtual_layer(self):
        """Create a virtual copy of a layer."""
        try:
            layer_name = self.get_current_layer_name()
            group_name = self.get_current_group()

            # Try to get a base layer from current project
            base_layer = None
            project_layers = QgsProject.instance().mapLayers().values()
            if project_layers:
                base_layer = list(project_layers)[0]  # Use first available layer

            result = self.engine.copy_virtual_layer_for_properties(
                layer_name, group_name, base_layer
            )

            if result:
                self.show_success(f"Virtual layer '{layer_name}' created in group '{group_name}'")
                self.refresh_info()
            else:
                self.show_error("Failed to create virtual layer")

        except Exception as e:
            self.show_error(f"Error creating virtual layer: {str(e)}")

    def save_to_geopackage(self):
        """Save memory layer to GeoPackage."""
        try:
            layer_name = self.get_current_layer_name()
            group_name = self.get_current_group()

            # Find memory layer
            memory_layer = None
            for layer in QgsProject.instance().mapLayers().values():
                if layer.name() == layer_name and layer.providerType() == 'memory':
                    memory_layer = layer
                    break

            if not memory_layer:
                self.show_error(f"Memory layer '{layer_name}' not found")
                return

            success = self.engine.save_memory_layer_to_geopackage(
                layer_name, f"{layer_name}_saved", group_name
            )

            if success:
                self.show_success(f"Layer saved to GeoPackage and reloaded in group '{group_name}'")
                self.refresh_info()
            else:
                self.show_error("Failed to save layer to GeoPackage")

        except Exception as e:
            self.show_error(f"Error saving to GeoPackage: {str(e)}")

    def create_property_sync_layer(self):
        """Create a property sync layer."""
        try:
            result = self.engine.create_property_sync_layer()
            if result:
                self.show_success(f"Property sync layer '{result}' created")
                self.refresh_info()
            else:
                self.show_error("Failed to create property sync layer")
        except Exception as e:
            self.show_error(f"Error creating property sync layer: {str(e)}")

    def create_archive_layer(self):
        """Create an archive layer."""
        try:
            result = self.engine.create_archive_layer()
            if result:
                self.show_success(f"Archive layer '{result}' created")
                self.refresh_info()
            else:
                self.show_error("Failed to create archive layer")
        except Exception as e:
            self.show_error(f"Error creating archive layer: {str(e)}")

    def create_import_layer(self):
        """Create an import layer."""
        try:
            result = self.engine.create_import_layer()
            if result:
                self.show_success(f"Import layer '{result}' created")
                self.refresh_info()
            else:
                self.show_error("Failed to create import layer")
        except Exception as e:
            self.show_error(f"Error creating import layer: {str(e)}")

    def show_success(self, message: str):
        """Show success message."""
        self.status_label.setText(f"✓ {message}")
        self.status_label.setStyleSheet("color: #2E7D32; font-weight: bold;")
        QMessageBox.information(self, "Success", message)

    def show_error(self, message: str):
        """Show error message."""
        self.status_label.setText(f"✗ {message}")
        self.status_label.setStyleSheet("color: #FF5722; font-weight: bold;")
        QMessageBox.warning(self, "Error", message)
# Factory function for easy instantiation
def create_layer_test_widget(parent=None):
    """Create and return a layer creation test widget."""
    return LayerCreationTestWidget(parent)
