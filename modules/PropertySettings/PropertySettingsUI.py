from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QTableWidget, QTableWidgetItem, QHeaderView,
    QLineEdit, QTextEdit, QComboBox, QGroupBox, QFormLayout,
    QMessageBox, QSplitter, QScrollArea, QDialog, QDialogButtonBox
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QIcon
from ...languages.language_manager import LanguageManager
from ...widgets.theme_manager import ThemeManager
from ...constants.file_paths import QssPaths
from ...utils.api_client import APIClient
from ...utils.GraphQLQueryLoader import GraphQLQueryLoader

class PropertySettingsUI(QWidget):
    """
    Property Settings module - dedicated interface for users with update permissions
    to add, edit, and manage property data. Integrates with main Kavitro database.
    """

    # Signal to notify when property data is updated
    propertyDataChanged = pyqtSignal()

    def __init__(self, lang_manager=None, theme_manager=None):
        super().__init__()
        self.name = "PropertySettingsModule"

        # Language and API setup
        self.lang_manager = lang_manager or LanguageManager()
        self.api_client = APIClient(self.lang_manager)
        self.query_loader = GraphQLQueryLoader(self.lang_manager)

        # Setup UI
        self.setup_ui()

        # Apply theming
        ThemeManager.apply_module_style(self, [QssPaths.SETUP_CARD])

        # Load initial data
        self.load_property_data()

    def setup_ui(self):
        """Setup the property settings interface with CRUD operations."""
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 20, 20, 20)
        root.setSpacing(15)

        # Header
        header_label = QLabel(self.lang_manager.translate("Property Settings"))
        header_label.setObjectName("ModuleHeader")
        header_label.setAlignment(Qt.AlignCenter)
        root.addWidget(header_label)

        # Description
        desc_label = QLabel(self.lang_manager.translate("Manage property data - add, edit, and update properties"))
        desc_label.setObjectName("ModuleDescription")
        desc_label.setAlignment(Qt.AlignCenter)
        root.addWidget(desc_label)

        # Create splitter for resizable sections
        splitter = QSplitter(Qt.Vertical)
        root.addWidget(splitter)

        # Property list section (top)
        self.create_property_list_section(splitter)

        # Property form section (bottom)
        self.create_property_form_section(splitter)

        # Set initial splitter proportions
        splitter.setSizes([400, 300])

    def create_property_list_section(self, splitter):
        """Create the property list section with table and action buttons."""
        list_frame = QFrame()
        list_layout = QVBoxLayout(list_frame)
        list_layout.setContentsMargins(10, 10, 10, 10)

        # Section title
        list_title = QLabel(self.lang_manager.translate("Property List"))
        list_title.setObjectName("SectionTitle")
        list_layout.addWidget(list_title)

        # Action buttons
        buttons_layout = QHBoxLayout()
        self.btn_add = QPushButton(self.lang_manager.translate("Add Property"))
        self.btn_add.clicked.connect(self.add_property)
        buttons_layout.addWidget(self.btn_add)

        self.btn_edit = QPushButton(self.lang_manager.translate("Edit Selected"))
        self.btn_edit.clicked.connect(self.edit_selected_property)
        buttons_layout.addWidget(self.btn_edit)

        self.btn_delete = QPushButton(self.lang_manager.translate("Delete Selected"))
        self.btn_delete.clicked.connect(self.delete_selected_property)
        self.btn_delete.setStyleSheet("QPushButton { color: red; }")
        buttons_layout.addWidget(self.btn_delete)

        buttons_layout.addStretch()
        list_layout.addLayout(buttons_layout)

        # Property table
        self.property_table = QTableWidget()
        self.property_table.setColumnCount(4)
        self.property_table.setHorizontalHeaderLabels([
            self.lang_manager.translate("ID"),
            self.lang_manager.translate("Name"),
            self.lang_manager.translate("Type"),
            self.lang_manager.translate("Status")
        ])
        self.property_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.property_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.property_table.itemSelectionChanged.connect(self.on_property_selected)
        list_layout.addWidget(self.property_table)

        splitter.addWidget(list_frame)

    def create_property_form_section(self, splitter):
        """Create the property form section for adding/editing properties."""
        form_frame = QFrame()
        form_layout = QVBoxLayout(form_frame)
        form_layout.setContentsMargins(10, 10, 10, 10)

        # Form title
        form_title = QLabel(self.lang_manager.translate("Property Details"))
        form_title.setObjectName("SectionTitle")
        form_layout.addWidget(form_title)

        # Scroll area for form
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        form_widget = QWidget()
        self.form_layout = QFormLayout(form_widget)
        self.form_layout.setSpacing(10)

        # Property ID (read-only for edits)
        self.txt_id = QLineEdit()
        self.txt_id.setReadOnly(True)
        self.txt_id.setPlaceholderText(self.lang_manager.translate("Auto-generated"))
        self.form_layout.addRow(self.lang_manager.translate("Property ID:"), self.txt_id)

        # Property Name
        self.txt_name = QLineEdit()
        self.txt_name.setPlaceholderText(self.lang_manager.translate("Enter property name"))
        self.form_layout.addRow(self.lang_manager.translate("Name:"), self.txt_name)

        # Property Type
        self.cmb_type = QComboBox()
        self.cmb_type.addItems([
            self.lang_manager.translate("Residential"),
            self.lang_manager.translate("Commercial"),
            self.lang_manager.translate("Industrial"),
            self.lang_manager.translate("Agricultural")
        ])
        self.form_layout.addRow(self.lang_manager.translate("Type:"), self.cmb_type)

        # Property Status
        self.cmb_status = QComboBox()
        self.cmb_status.addItems([
            self.lang_manager.translate("Active"),
            self.lang_manager.translate("Inactive"),
            self.lang_manager.translate("Pending"),
            self.lang_manager.translate("Sold")
        ])
        self.form_layout.addRow(self.lang_manager.translate("Status:"), self.cmb_status)

        # Address
        self.txt_address = QLineEdit()
        self.txt_address.setPlaceholderText(self.lang_manager.translate("Enter property address"))
        self.form_layout.addRow(self.lang_manager.translate("Address:"), self.txt_address)

        # Description
        self.txt_description = QTextEdit()
        self.txt_description.setPlaceholderText(self.lang_manager.translate("Enter property description"))
        self.txt_description.setMaximumHeight(100)
        self.form_layout.addRow(self.lang_manager.translate("Description:"), self.txt_description)

        # Area
        self.txt_area = QLineEdit()
        self.txt_area.setPlaceholderText(self.lang_manager.translate("Enter area in m²"))
        self.form_layout.addRow(self.lang_manager.translate("Area (m²):"), self.txt_area)

        # Value
        self.txt_value = QLineEdit()
        self.txt_value.setPlaceholderText(self.lang_manager.translate("Enter property value"))
        self.form_layout.addRow(self.lang_manager.translate("Value:"), self.txt_value)

        scroll.setWidget(form_widget)
        form_layout.addWidget(scroll)

        # Form action buttons
        form_buttons = QHBoxLayout()
        self.btn_save = QPushButton(self.lang_manager.translate("Save"))
        self.btn_save.clicked.connect(self.save_property)
        form_buttons.addWidget(self.btn_save)

        self.btn_cancel = QPushButton(self.lang_manager.translate("Cancel"))
        self.btn_cancel.clicked.connect(self.cancel_edit)
        form_buttons.addWidget(self.btn_cancel)

        form_buttons.addStretch()
        form_layout.addLayout(form_buttons)

        splitter.addWidget(form_frame)

    def load_property_data(self):
        """Load property data from the API."""
        try:
            # Load GraphQL query for properties
            query = self.query_loader.load_query("properties", "ListProperties.graphql")

            # Make API call
            data = self.api_client.send_query(query) or {}

            # Parse response and populate table
            self.populate_property_table(data)

        except Exception as e:
            QMessageBox.warning(
                self,
                self.lang_manager.translate("Error"),
                self.lang_manager.translate("Failed to load property data:") + f" {str(e)}"
            )

    def populate_property_table(self, data):
        """Populate the property table with data from API."""
        properties = (data.get("properties") or {}).get("edges") or []

        self.property_table.setRowCount(len(properties))

        for row, edge in enumerate(properties):
            node = edge.get("node") or {}

            # ID
            id_item = QTableWidgetItem(str(node.get("id", "")))
            self.property_table.setItem(row, 0, id_item)

            # Name
            name_item = QTableWidgetItem(node.get("name", ""))
            self.property_table.setItem(row, 1, name_item)

            # Type
            type_item = QTableWidgetItem(node.get("type", ""))
            self.property_table.setItem(row, 2, type_item)

            # Status
            status_item = QTableWidgetItem(node.get("status", ""))
            self.property_table.setItem(row, 3, status_item)

    def add_property(self):
        """Clear form for adding new property."""
        self.clear_form()
        self.txt_id.setText("")
        self.btn_save.setText(self.lang_manager.translate("Add Property"))

    def edit_selected_property(self):
        """Load selected property data into form for editing."""
        current_row = self.property_table.currentRow()
        if current_row < 0:
            QMessageBox.information(
                self,
                self.lang_manager.translate("No Selection"),
                self.lang_manager.translate("Please select a property to edit.")
            )
            return

        # Get property ID from table
        property_id = self.property_table.item(current_row, 0).text()

        # Load property details (would make API call here)
        # For now, populate with dummy data
        self.load_property_details(property_id)

    def load_property_details(self, property_id):
        """Load property details for editing."""
        # This would make an API call to get property details
        # For now, using placeholder data
        self.txt_id.setText(property_id)
        self.txt_name.setText(f"Property {property_id}")
        self.cmb_type.setCurrentText("Residential")
        self.cmb_status.setCurrentText("Active")
        self.txt_address.setText("Sample Address")
        self.txt_description.setPlainText("Sample description")
        self.txt_area.setText("1000")
        self.txt_value.setText("50000")
        self.btn_save.setText(self.lang_manager.translate("Update Property"))

    def delete_selected_property(self):
        """Delete the selected property."""
        current_row = self.property_table.currentRow()
        if current_row < 0:
            QMessageBox.information(
                self,
                self.lang_manager.translate("No Selection"),
                self.lang_manager.translate("Please select a property to delete.")
            )
            return

        property_name = self.property_table.item(current_row, 1).text()

        reply = QMessageBox.question(
            self,
            self.lang_manager.translate("Confirm Delete"),
            self.lang_manager.translate("Are you sure you want to delete property") + f" '{property_name}'?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            # Make API call to delete property
            self.delete_property(self.property_table.item(current_row, 0).text())

    def delete_property(self, property_id):
        """Delete property via API."""
        try:
            # Load delete mutation
            mutation = self.query_loader.load_query("properties", "DeleteProperty.graphql")

            # Make API call
            variables = {"id": property_id}
            result = self.api_client.send_query(mutation, variables=variables)

            if result and result.get("deleteProperty", {}).get("success"):
                QMessageBox.information(
                    self,
                    self.lang_manager.translate("Success"),
                    self.lang_manager.translate("Property deleted successfully.")
                )
                self.load_property_data()  # Refresh table
                self.propertyDataChanged.emit()
            else:
                raise Exception("Delete operation failed")

        except Exception as e:
            QMessageBox.warning(
                self,
                self.lang_manager.translate("Error"),
                self.lang_manager.translate("Failed to delete property:") + f" {str(e)}"
            )

    def save_property(self):
        """Save property data (add or update)."""
        try:
            property_data = {
                "name": self.txt_name.text(),
                "type": self.cmb_type.currentText(),
                "status": self.cmb_status.currentText(),
                "address": self.txt_address.text(),
                "description": self.txt_description.toPlainText(),
                "area": self.txt_area.text(),
                "value": self.txt_value.text()
            }

            if self.txt_id.text():  # Update existing
                property_data["id"] = self.txt_id.text()
                self.update_property(property_data)
            else:  # Add new
                self.create_property(property_data)

        except Exception as e:
            QMessageBox.warning(
                self,
                self.lang_manager.translate("Error"),
                self.lang_manager.translate("Failed to save property:") + f" {str(e)}"
            )

    def create_property(self, property_data):
        """Create new property via API."""
        try:
            # Load create mutation
            mutation = self.query_loader.load_query("properties", "CreateProperty.graphql")

            # Make API call
            result = self.api_client.send_query(mutation, variables={"input": property_data})

            if result and result.get("createProperty", {}).get("property"):
                QMessageBox.information(
                    self,
                    self.lang_manager.translate("Success"),
                    self.lang_manager.translate("Property created successfully.")
                )
                self.load_property_data()  # Refresh table
                self.clear_form()
                self.propertyDataChanged.emit()
            else:
                raise Exception("Create operation failed")

        except Exception as e:
            QMessageBox.warning(
                self,
                self.lang_manager.translate("Error"),
                self.lang_manager.translate("Failed to create property:") + f" {str(e)}"
            )

    def update_property(self, property_data):
        """Update existing property via API."""
        try:
            # Load update mutation
            mutation = self.query_loader.load_query("properties", "UpdateProperty.graphql")

            # Make API call
            result = self.api_client.send_query(mutation, variables={"input": property_data})

            if result and result.get("updateProperty", {}).get("property"):
                QMessageBox.information(
                    self,
                    self.lang_manager.translate("Success"),
                    self.lang_manager.translate("Property updated successfully.")
                )
                self.load_property_data()  # Refresh table
                self.clear_form()
                self.propertyDataChanged.emit()
            else:
                raise Exception("Update operation failed")

        except Exception as e:
            QMessageBox.warning(
                self,
                self.lang_manager.translate("Error"),
                self.lang_manager.translate("Failed to update property:") + f" {str(e)}"
            )

    def cancel_edit(self):
        """Cancel current edit operation."""
        self.clear_form()

    def clear_form(self):
        """Clear all form fields."""
        self.txt_id.setText("")
        self.txt_name.setText("")
        self.cmb_type.setCurrentIndex(0)
        self.cmb_status.setCurrentIndex(0)
        self.txt_address.setText("")
        self.txt_description.setPlainText("")
        self.txt_area.setText("")
        self.txt_value.setText("")
        self.btn_save.setText(self.lang_manager.translate("Save"))

    def on_property_selected(self):
        """Handle property selection in table."""
        # Could enable/disable buttons based on selection
        current_row = self.property_table.currentRow()
        self.btn_edit.setEnabled(current_row >= 0)
        self.btn_delete.setEnabled(current_row >= 0)

    def activate(self):
        """Called when module becomes active."""
        self.load_property_data()

    def deactivate(self):
        """Called when module becomes inactive."""
        pass
