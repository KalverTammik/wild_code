import os
from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QListWidget, QListWidgetItem,
    QPushButton, QHBoxLayout, QMessageBox, QComboBox, QFrame,
    QTableWidget, QTableWidgetItem, QHeaderView, QSplitter
)

from .theme_manager import ThemeManager
from ..constants.file_paths import QssPaths
from ..languages.language_manager import LanguageManager
from ..constants.cadastral_fields import Katastriyksus

class AddPropertyDialog(QDialog):
    """
    Dialog for adding new properties with a smart list view
    """
    propertyAdded = pyqtSignal(dict)  # Signal emitted when property is added

    def __init__(self, parent=None):
        super().__init__(parent)

        # Initialize managers
        self.lang_manager = LanguageManager()

        # Get the selected property layer from parent (SettingsUI)
        self.property_layer = None
        if hasattr(parent, 'get_selected_property_layer'):
            self.property_layer = parent.get_selected_property_layer()

        # Set up dialog properties
        self.setWindowTitle(self.lang_manager.translate("Add New Property") or "Lisa uus kinnistu")
        self.setModal(True)
        self.setFixedSize(800, 600)  # Made larger for the new UI

        # Apply theme
        self._apply_theme()

        self._create_ui()
        self._setup_connections()
        self._load_layer_data()

    def _apply_theme(self):
        """Apply theme to the dialog"""
        try:
            theme_base_dir = os.path.join(os.path.dirname(__file__), '..', 'styles')
            ThemeManager.set_initial_theme(
                self,
                None,  # No theme switch button for popup dialogs
                theme_base_dir,
                qss_files=[QssPaths.MAIN, QssPaths.SETUP_CARD]
            )
        except Exception as e:
            print(f"Theme application failed: {e}")

    def _create_ui(self):
        """Create the user interface with hierarchical selection"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Title
        title_label = QLabel(self.lang_manager.translate("Select Properties") or "Vali kinnistud")
        title_label.setObjectName("DialogTitle")
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)

        # Check if we have a property layer
        if not self.property_layer:
            error_label = QLabel(self.lang_manager.translate("No property layer selected. Please select a property layer first.") or
                               "Kinnistute kihti pole valitud. Palun valige esmalt kinnistute kiht.")
            error_label.setObjectName("ErrorLabel")
            error_label.setWordWrap(True)
            layout.addWidget(error_label)

            # Add close button
            buttons_layout = QHBoxLayout()
            buttons_layout.addStretch()
            close_button = QPushButton(self.lang_manager.translate("Close") or "Sulge")
            close_button.clicked.connect(self.reject)
            buttons_layout.addWidget(close_button)
            layout.addLayout(buttons_layout)
            return

        # Hierarchical selection section
        self._create_hierarchical_selection(layout)

        # Properties table section
        self._create_properties_table(layout)

        # Selection info and buttons
        self._create_selection_controls(layout)

    def _create_hierarchical_selection(self, parent_layout):
        """Create county and municipality dropdowns"""
        # Filter section frame
        filter_frame = QFrame()
        filter_frame.setObjectName("FilterFrame")
        filter_frame.setFrameStyle(QFrame.StyledPanel)
        filter_layout = QVBoxLayout(filter_frame)
        filter_layout.setContentsMargins(10, 10, 10, 10)
        filter_layout.setSpacing(10)

        # Filter title
        filter_title = QLabel(self.lang_manager.translate("Filter by Location") or "Filtreeri asukoha järgi")
        filter_title.setObjectName("FilterTitle")
        filter_layout.addWidget(filter_title)

        # County and Municipality row
        location_layout = QHBoxLayout()
        location_layout.setSpacing(15)

        # County dropdown
        county_layout = QVBoxLayout()
        county_label = QLabel(self.lang_manager.translate("County") or "Maakond")
        county_label.setObjectName("CountyLabel")
        county_layout.addWidget(county_label)

        self.county_combo = QComboBox()
        self.county_combo.setObjectName("CountyCombo")
        self.county_combo.addItem(self.lang_manager.translate("Select County") or "Vali maakond", "")
        county_layout.addWidget(self.county_combo)

        location_layout.addLayout(county_layout)

        # Municipality dropdown
        municipality_layout = QVBoxLayout()
        municipality_label = QLabel(self.lang_manager.translate("Municipality") or "Omavalitsus")
        municipality_label.setObjectName("MunicipalityLabel")
        municipality_layout.addWidget(municipality_label)

        self.municipality_combo = QComboBox()
        self.municipality_combo.setObjectName("MunicipalityCombo")
        self.municipality_combo.addItem(self.lang_manager.translate("Select Municipality") or "Vali omavalitsus", "")
        self.municipality_combo.setEnabled(False)  # Disabled until county is selected
        municipality_layout.addWidget(self.municipality_combo)

        location_layout.addLayout(municipality_layout)
        location_layout.addStretch()

        filter_layout.addLayout(location_layout)
        parent_layout.addWidget(filter_frame)

    def _create_properties_table(self, parent_layout):
        """Create the properties table"""
        # Table section
        table_frame = QFrame()
        table_frame.setObjectName("TableFrame")
        table_frame.setFrameStyle(QFrame.StyledPanel)
        table_layout = QVBoxLayout(table_frame)
        table_layout.setContentsMargins(10, 10, 10, 10)
        table_layout.setSpacing(10)

        # Table title
        table_title = QLabel(self.lang_manager.translate("Properties") or "Kinnistud")
        table_title.setObjectName("TableTitle")
        table_layout.addWidget(table_title)

        # Properties table
        self.properties_table = QTableWidget()
        self.properties_table.setObjectName("PropertiesTable")
        self.properties_table.setAlternatingRowColors(True)
        self.properties_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.properties_table.setSelectionMode(QTableWidget.MultiSelection)

        # Set up table headers
        headers = [
            self.lang_manager.translate("Cadastral ID") or "Katastritunnus",
            self.lang_manager.translate("Address") or "Aadress",
            self.lang_manager.translate("Area (m²)") or "Pindala (m²)",
            self.lang_manager.translate("Settlement") or "Asustusüksus"
        ]
        self.properties_table.setColumnCount(len(headers))
        self.properties_table.setHorizontalHeaderLabels(headers)

        # Configure table
        header = self.properties_table.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(QHeaderView.Interactive)

        table_layout.addWidget(self.properties_table)
        parent_layout.addWidget(table_frame)

    def _create_selection_controls(self, parent_layout):
        """Create selection info and control buttons"""
        # Selection info
        self.selection_info = QLabel(self.lang_manager.translate("Selected: 0 properties") or "Valitud: 0 kinnistut")
        self.selection_info.setObjectName("SelectionInfo")
        parent_layout.addWidget(self.selection_info)

        # Buttons
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(10)

        # Selection buttons
        self.select_all_btn = QPushButton(self.lang_manager.translate("Select All") or "Vali kõik")
        self.select_all_btn.setObjectName("SelectAllButton")
        buttons_layout.addWidget(self.select_all_btn)

        self.clear_selection_btn = QPushButton(self.lang_manager.translate("Clear Selection") or "Tühjenda valik")
        self.clear_selection_btn.setObjectName("ClearSelectionButton")
        buttons_layout.addWidget(self.clear_selection_btn)

        buttons_layout.addStretch()

        # Action buttons
        self.cancel_button = QPushButton(self.lang_manager.translate("Cancel") or "Tühista")
        self.cancel_button.setObjectName("CancelButton")
        buttons_layout.addWidget(self.cancel_button)

        self.add_button = QPushButton(self.lang_manager.translate("Add Selected") or "Lisa valitud")
        self.add_button.setObjectName("AddButton")
        self.add_button.setEnabled(False)  # Disabled until properties are selected
        buttons_layout.addWidget(self.add_button)

        parent_layout.addLayout(buttons_layout)

    def _setup_connections(self):
        """Set up signal connections"""
        # Dropdown connections
        self.county_combo.currentTextChanged.connect(self._on_county_changed)
        self.municipality_combo.currentTextChanged.connect(self._on_municipality_changed)

        # Table connections
        self.properties_table.itemSelectionChanged.connect(self._on_table_selection_changed)

        # Button connections
        self.select_all_btn.clicked.connect(self._on_select_all_clicked)
        self.clear_selection_btn.clicked.connect(self._on_clear_selection_clicked)
        self.cancel_button.clicked.connect(self.reject)
        self.add_button.clicked.connect(self._on_add_selected_clicked)

    def _load_layer_data(self):
        """Load data from the property layer"""
        if not self.property_layer:
            return

        try:
            # Load counties
            self._load_counties()

        except Exception as e:
            print(f"Error loading layer data: {e}")
            QMessageBox.warning(
                self,
                self.lang_manager.translate("Data Loading Error") or "Andmete laadimise viga",
                self.lang_manager.translate("Failed to load property data from layer.") or
                f"Andmete laadimine kihist ebaõnnestus: {str(e)}"
            )

    def _load_counties(self):
        """Load unique counties from the property layer"""
        if not self.property_layer:
            return

        try:
            counties = set()

            # Get the field index for county name
            county_field = None
            for field in self.property_layer.fields():
                if field.name() in Katastriyksus.mk_nimi:
                    county_field = field.name()
                    break

            if not county_field:
                QMessageBox.warning(
                    self,
                    self.lang_manager.translate("Field Not Found") or "Välja ei leitud",
                    self.lang_manager.translate("County field (mk_nimi) not found in layer.") or
                    f"Maakonna väli ({Katastriyksus.mk_nimi}) kihist ei leitud."
                )
                return

            # Extract unique county values
            for feature in self.property_layer.getFeatures():
                county_value = feature[county_field]
                if county_value and str(county_value).strip():
                    counties.add(str(county_value).strip())

            # Populate county dropdown
            self.county_combo.clear()
            self.county_combo.addItem(self.lang_manager.translate("Select County") or "Vali maakond", "")

            for county in sorted(counties):
                self.county_combo.addItem(county, county)

            print(f"Loaded {len(counties)} counties from layer")

        except Exception as e:
            print(f"Error loading counties: {e}")

    def _on_county_changed(self, county_name):
        """Handle county selection change"""
        if not county_name or county_name == (self.lang_manager.translate("Select County") or "Vali maakond"):
            # Clear municipality dropdown
            self.municipality_combo.clear()
            self.municipality_combo.addItem(self.lang_manager.translate("Select Municipality") or "Vali omavalitsus", "")
            self.municipality_combo.setEnabled(False)
            # Clear properties table
            self.properties_table.setRowCount(0)
            return

        # Load municipalities for selected county
        self._load_municipalities_for_county(county_name)
        self.municipality_combo.setEnabled(True)

    def _load_municipalities_for_county(self, county_name):
        """Load municipalities for the selected county"""
        if not self.property_layer:
            return

        try:
            municipalities = set()

            # Get field indices
            county_field = None
            municipality_field = None

            for field in self.property_layer.fields():
                field_name = field.name().lower()
                if field_name in [Katastriyksus.mk_nimi.lower(), 'maakond', 'county']:
                    county_field = field.name()
                elif field_name in [Katastriyksus.ov_nimi.lower(), 'omavalitsus', 'municipality']:
                    municipality_field = field.name()

            if not county_field or not municipality_field:
                print("Required fields not found")
                return

            # Extract municipalities for selected county
            for feature in self.property_layer.getFeatures():
                if str(feature[county_field]).strip() == county_name:
                    municipality_value = feature[municipality_field]
                    if municipality_value and str(municipality_value).strip():
                        municipalities.add(str(municipality_value).strip())

            # Populate municipality dropdown
            self.municipality_combo.clear()
            self.municipality_combo.addItem(self.lang_manager.translate("Select Municipality") or "Vali omavalitsus", "")

            for municipality in sorted(municipalities):
                self.municipality_combo.addItem(municipality, municipality)

            print(f"Loaded {len(municipalities)} municipalities for county: {county_name}")

        except Exception as e:
            print(f"Error loading municipalities: {e}")

    def _on_municipality_changed(self, municipality_name):
        """Handle municipality selection change"""
        if not municipality_name or municipality_name == (self.lang_manager.translate("Select Municipality") or "Vali omavalitsus"):
            # Clear properties table
            self.properties_table.setRowCount(0)
            return

        # Load properties for selected municipality
        county_name = self.county_combo.currentData()
        self._load_properties_for_municipality(county_name, municipality_name)

    def _load_properties_for_municipality(self, county_name, municipality_name):
        """Load properties for the selected municipality"""
        if not self.property_layer:
            return

        try:
            properties = []

            # Get field indices
            county_field = None
            municipality_field = None
            cadastral_field = None
            address_field = None
            area_field = None
            settlement_field = None

            for field in self.property_layer.fields():
                field_name = field.name().lower()
                if field_name in [Katastriyksus.mk_nimi.lower(), 'maakond', 'county']:
                    county_field = field.name()
                elif field_name in [Katastriyksus.ov_nimi.lower(), 'omavalitsus', 'municipality']:
                    municipality_field = field.name()
                elif field_name in [Katastriyksus.tunnus.lower(), 'katastritunnus', 'cadastral_id']:
                    cadastral_field = field.name()
                elif field_name in [Katastriyksus.l_aadress.lower(), 'address']:
                    address_field = field.name()
                elif field_name in [Katastriyksus.pindala.lower(), 'area']:
                    area_field = field.name()
                elif field_name in [Katastriyksus.ay_nimi.lower(), 'asustusuksus', 'settlement']:
                    settlement_field = field.name()

            # Extract properties for selected municipality
            for feature in self.property_layer.getFeatures():
                if (str(feature[county_field]).strip() == county_name and
                    str(feature[municipality_field]).strip() == municipality_name):

                    property_data = {
                        'cadastral_id': feature[cadastral_field] if cadastral_field else '',
                        'address': feature[address_field] if address_field else '',
                        'area': feature[area_field] if area_field else '',
                        'settlement': feature[settlement_field] if settlement_field else '',
                        'feature': feature
                    }
                    properties.append(property_data)

            # Populate properties table
            self._populate_properties_table(properties)
            print(f"Loaded {len(properties)} properties for municipality: {municipality_name}")

        except Exception as e:
            print(f"Error loading properties: {e}")

    def _populate_properties_table(self, properties):
        """Populate the properties table with data"""
        self.properties_table.setRowCount(len(properties))

        for row, property_data in enumerate(properties):
            # Cadastral ID
            cadastral_item = QTableWidgetItem(str(property_data['cadastral_id']))
            self.properties_table.setItem(row, 0, cadastral_item)

            # Address
            address_item = QTableWidgetItem(str(property_data['address']))
            self.properties_table.setItem(row, 1, address_item)

            # Area
            area_item = QTableWidgetItem(str(property_data['area']))
            self.properties_table.setItem(row, 2, area_item)

            # Settlement
            settlement_item = QTableWidgetItem(str(property_data['settlement']))
            self.properties_table.setItem(row, 3, settlement_item)

            # Store feature data in the row
            cadastral_item.setData(Qt.UserRole, property_data['feature'])

    def _on_table_selection_changed(self):
        """Handle table selection changes"""
        selected_rows = set()
        for item in self.properties_table.selectedItems():
            selected_rows.add(item.row())

        selected_count = len(selected_rows)
        self.selection_info.setText(
            self.lang_manager.translate("Selected: {count} properties").format(count=selected_count) or
            f"Valitud: {selected_count} kinnistut"
        )

        # Enable/disable add button based on selection
        self.add_button.setEnabled(selected_count > 0)

    def _on_select_all_clicked(self):
        """Select all properties in the table"""
        self.properties_table.selectAll()

    def _on_clear_selection_clicked(self):
        """Clear all selections in the table"""
        self.properties_table.clearSelection()

    def _on_add_selected_clicked(self):
        """Handle adding selected properties"""
        selected_items = self.properties_table.selectedItems()
        if not selected_items:
            return

        # Get unique selected features
        selected_features = set()
        for item in selected_items:
            feature = item.data(Qt.UserRole)
            if feature:
                selected_features.add(feature)

        if selected_features:
            # Emit signal with selected properties
            selected_data = {
                'selected_features': list(selected_features),
                'county': self.county_combo.currentData(),
                'municipality': self.municipality_combo.currentData(),
                'count': len(selected_features)
            }

            self.propertyAdded.emit(selected_data)
            self.accept()
        else:
            QMessageBox.warning(
                self,
                self.lang_manager.translate("No Selection") or "Valikut pole",
                self.lang_manager.translate("Please select at least one property.") or
                "Palun valige vähemalt üks kinnistu."
            )
