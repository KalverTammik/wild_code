import os
from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QListWidget, QListWidgetItem,
    QPushButton, QHBoxLayout, QMessageBox, QComboBox, QFrame,
    QTableWidget, QHeaderView, QSplitter
)
from qgis.gui import QgsCheckableComboBox

from ..utils.mapandproperties.PropertyUpdateFlowCoordinator import PropertyUpdateFlowCoordinator

from ..utils.mapandproperties.PropertyTableManager import PropertyTableManager

from ..utils.mapandproperties.PropertyDataLoader import PropertyDataLoader
from .theme_manager import ThemeManager

from ..constants.file_paths import QssPaths
from ..languages.language_manager import LanguageManager
from ..languages.translation_keys import TranslationKeys
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
        
        # Initialize helper classes
        self.data_loader = PropertyDataLoader(self.lang_manager)
        self.table_manager = PropertyTableManager(None, self.lang_manager)  # Will be set after UI creation
        self.selection_handler = PropertyUpdateFlowCoordinator(
            self.data_loader, self.table_manager, None, None, None, self.lang_manager
        )  # Combos will be set after UI creation

        # Set up dialog properties
        self.setWindowTitle(self.lang_manager.translate(TranslationKeys.ADD_NEW_PROPERTY))
        self.setModal(True)
        self.setFixedSize(800, 600)  # Made larger for the new UI

        # Apply theme
        self._apply_theme()

        self._create_ui()
        self._setup_connections()
        self._load_layer_data()

        # Set up helper classes with UI references (only if UI was fully created)
        if hasattr(self, 'properties_table') and self.properties_table:
            self.table_manager.properties_table = self.properties_table
        if hasattr(self, 'county_combo') and self.county_combo:
            self.selection_handler.county_combo = self.county_combo
        if hasattr(self, 'municipality_combo') and self.municipality_combo:
            self.selection_handler.municipality_combo = self.municipality_combo
        if hasattr(self, 'city_combo') and self.city_combo:
            self.selection_handler.city_combo = self.city_combo

    def _apply_theme(self):
        """Apply theme to the dialog"""
        try:
            theme_base_dir = os.path.join(os.path.dirname(__file__), '..', 'styles')
            ThemeManager.set_initial_theme(
                self,
                None,  # No theme switch button for popup dialogs
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
        title_label = QLabel(self.lang_manager.translate(TranslationKeys.SELECT_PROPERTIES))
        title_label.setObjectName("DialogTitle")
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)

        # Check if we have a property layer
        self.property_layer = self.data_loader.property_layer
        if not self.property_layer:
            error_label = QLabel(self.lang_manager.translate(TranslationKeys.NO_PROPERTY_LAYER_SELECTED))
            error_label.setObjectName("ErrorLabel")
            error_label.setWordWrap(True)
            layout.addWidget(error_label)

            # Add close button
            buttons_layout = QHBoxLayout()
            buttons_layout.addStretch()
            close_button = QPushButton(self.lang_manager.translate(TranslationKeys.CLOSE))
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

        # Set up helper classes with UI references
        self.table_manager.properties_table = self.properties_table
        self.selection_handler.county_combo = self.county_combo
        self.selection_handler.municipality_combo = self.municipality_combo
        self.selection_handler.city_combo = self.city_combo

    def _create_hierarchical_selection(self, parent_layout):
        """Create county and municipality dropdowns"""
        # Filter section frame
        filter_frame = QFrame()
        filter_frame.setObjectName("FilterFrame")
        filter_frame.setFrameStyle(QFrame.StyledPanel)
        filter_layout = QVBoxLayout(filter_frame)
        filter_layout.setContentsMargins(10, 10, 10, 10)
        filter_layout.setSpacing(6)

        # Filter title
        filter_title = QLabel(self.lang_manager.translate(TranslationKeys.FILTER_BY_LOCATION))
        filter_title.setObjectName("FilterTitle")
        filter_layout.addWidget(filter_title)

        # County and Municipality row
        location_layout = QHBoxLayout()
        location_layout.setSpacing(6)

        # County dropdown
        county_layout = QVBoxLayout()
        county_label = QLabel(f"{self.lang_manager.translate(TranslationKeys.COUNTY)}:")
        county_label.setObjectName("CountyLabel")
        county_layout.addWidget(county_label)

        self.county_combo = QComboBox()
        self.county_combo.setObjectName("CountyCombo")
        self.county_combo.addItem(self.lang_manager.translate(TranslationKeys.SELECT_COUNTY), "")
        county_layout.addWidget(self.county_combo)

        location_layout.addLayout(county_layout)

        # Municipality dropdown
        municipality_layout = QVBoxLayout()
        municipality_label = QLabel(f"{self.lang_manager.translate(TranslationKeys.MUNICIPALITY)}:")
        municipality_label.setObjectName("MunicipalityLabel")
        municipality_layout.addWidget(municipality_label)

        self.municipality_combo = QComboBox()
        self.municipality_combo.setObjectName("MunicipalityCombo")
        self.municipality_combo.addItem(self.lang_manager.translate(TranslationKeys.SELECT_MUNICIPALITY), "")
        self.municipality_combo.setEnabled(False)  # Disabled until county is selected
        municipality_layout.addWidget(self.municipality_combo)

        location_layout.addLayout(municipality_layout)

        city_layout = QVBoxLayout()
        city_label = QLabel(f"{self.lang_manager.translate(TranslationKeys.SETTLEMENT)}:")
        city_label.setObjectName("CityLabel")
        city_layout.addWidget(city_label)

        self.city_combo = QgsCheckableComboBox()
        self.city_combo.setObjectName("CityCombo")
        self.city_combo.setPlaceholderText(self.lang_manager.translate(TranslationKeys.SELECT_SETTLEMENTS))
        self.city_combo.setEnabled(False)  # Disabled until municipality is selected
        city_layout.addWidget(self.city_combo)

        location_layout.addLayout(city_layout)

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
        table_title = QLabel(self.lang_manager.translate(TranslationKeys.PROPERTIES))
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
            self.lang_manager.translate(TranslationKeys.CADASTRAL_ID),
            self.lang_manager.translate(TranslationKeys.ADDRESS),
            self.lang_manager.translate(TranslationKeys.AREA),
            self.lang_manager.translate(TranslationKeys.SETTLEMENT)
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
        self.selection_info = QLabel(self.lang_manager.translate(TranslationKeys.SELECTED_PROPERTIES_COUNT))
        self.selection_info.setObjectName("SelectionInfo")
        parent_layout.addWidget(self.selection_info)

        # Buttons
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(10)

        # Selection buttons
        self.select_all_btn = QPushButton(self.lang_manager.translate(TranslationKeys.SELECT_ALL))
        self.select_all_btn.setObjectName("SelectAllButton")
        buttons_layout.addWidget(self.select_all_btn)

        self.clear_selection_btn = QPushButton(self.lang_manager.translate(TranslationKeys.CLEAR_SELECTION))
        self.clear_selection_btn.setObjectName("ClearSelectionButton")
        buttons_layout.addWidget(self.clear_selection_btn)

        buttons_layout.addStretch()

        # Action buttons
        self.cancel_button = QPushButton(self.lang_manager.translate(TranslationKeys.CANCEL))
        self.cancel_button.setObjectName("CancelButton")
        buttons_layout.addWidget(self.cancel_button)

        self.add_button = QPushButton(self.lang_manager.translate(TranslationKeys.ADD_SELECTED))
        self.add_button.setObjectName("AddButton")
        self.add_button.setEnabled(False)  # Disabled until properties are selected
        buttons_layout.addWidget(self.add_button)

        parent_layout.addLayout(buttons_layout)

    def _setup_connections(self):
        """Set up signal connections"""
        # Only set up connections if UI was fully created
        if not hasattr(self, 'county_combo') or not self.county_combo:
            return
            
        # Dropdown connections - use selection handler
        self.county_combo.currentTextChanged.connect(self.selection_handler.on_county_changed)
        self.municipality_combo.currentTextChanged.connect(self.selection_handler.on_municipality_changed)
        if hasattr(self, 'city_combo') and self.city_combo is not None:
            self.city_combo.checkedItemsChanged.connect(self.selection_handler.on_city_changed)

        # Table connections - use table manager
        self.properties_table.itemSelectionChanged.connect(self.table_manager.on_table_selection_changed)
        self.table_manager.set_selection_changed_callback(self._on_selection_count_changed)

        # Button connections
        self.select_all_btn.clicked.connect(self.table_manager.select_all)
        self.clear_selection_btn.clicked.connect(self.table_manager.clear_selection)
        self.cancel_button.clicked.connect(self.reject)
        self.add_button.clicked.connect(self._start_adding_properties)

    def _on_selection_count_changed(self, selected_count):
        """Handle selection count changes from table manager"""
        self.selection_info.setText(
            self.lang_manager.translate(TranslationKeys.SELECTED_COUNT_TEMPLATE).format(count=selected_count)
        )
        # Enable/disable add button based on selection
        self.add_button.setEnabled(selected_count > 0)
        
        # Update map to show selected features
        self._update_map_for_selected_rows()

    def _update_map_for_selected_rows(self):
        """Update map display based on currently selected table rows"""
        selected_features = self.selection_handler.collect_active_selections_from_table()
        
        if not selected_features:
            # No selection - clear any existing filter and selection
            from ..constants.layer_constants import IMPORT_PROPERTY_TAG
            layer = self.data_loader._get_layer_by_tag(IMPORT_PROPERTY_TAG)
            if layer:
                from ..utils.MapTools.MapHelpers import MapHelpers
                MapHelpers.clear_layer_filter(layer)
                layer.removeSelection()
            return
        
        # Update map with selected features
        from ..constants.layer_constants import IMPORT_PROPERTY_TAG
        from ..utils.MapTools.MapHelpers import MapHelpers
        layer = self.data_loader._get_layer_by_tag(IMPORT_PROPERTY_TAG)
        
        if layer and selected_features:
            # Select features on map and zoom to them, filter layer to show only selected
            MapHelpers._zoom_to_features_in_layer(selected_features, layer, select=True, filter_layer=True)

    def _load_layer_data(self):
        """Load data from the property layer"""
        if not self.property_layer or not hasattr(self, 'county_combo') or not self.county_combo:
            return

        try:
            # Load counties using data loader
            counties = self.data_loader.load_counties()

            # Populate county dropdown
            self.county_combo.clear()
            self.county_combo.addItem(self.lang_manager.translate("Select County") or "Vali maakond", "")

            for county in counties:
                self.county_combo.addItem(county, county)

        except Exception as e:
            print(f"Error loading layer data: {e}")
            QMessageBox.warning(
                self,
                self.lang_manager.translate(TranslationKeys.DATA_LOADING_ERROR),
                self.lang_manager.translate(TranslationKeys.FAILED_TO_LOAD_PROPERTY_DATA) + f" {str(e)}"
            )


    def _start_adding_properties(self):
        """Handle adding selected properties"""
        selected_features = self.selection_handler.collect_active_selections_from_table()

        if selected_features:
            print(f"Emitting {len(selected_features)} selected features")
            for feature in selected_features:
                print(f" - Feature ID: {feature.id()}")
            
            self.accept()  # Close the dialog
            
            # Clear the layer filter to show all features again
            from ..constants.layer_constants import IMPORT_PROPERTY_TAG
            from ..utils.MapTools.MapHelpers import MapHelpers
            layer = self.data_loader._get_layer_by_tag(IMPORT_PROPERTY_TAG)
            if layer:
                MapHelpers.clear_layer_filter(layer)
                #layer.removeSelection()

            QMessageBox.information(
                self,
                self.lang_manager.translate(TranslationKeys.PROPERTIES_ADDED),
                self.lang_manager.translate(TranslationKeys.SELECTED_PROPERTIES_ADDED)
            )
        else:
            QMessageBox.warning(
                self,
                self.lang_manager.translate(TranslationKeys.NO_SELECTION),
                self.lang_manager.translate(TranslationKeys.PLEASE_SELECT_AT_LEAST_ONE_PROPERTY)
            )
