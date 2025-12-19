import os
from PyQt5.QtCore import pyqtSignal, Qt, QTimer
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QLabel,
    QPushButton, QHBoxLayout, QComboBox, QFrame
)
from qgis.gui import QgsCheckableComboBox

from ..utils.mapandproperties.PropertyUpdateFlowCoordinator import PropertyUpdateFlowCoordinator
from ..modules.Property.FlowControllers.MainAddProperties import MainAddPropertiesFlow
from ..utils.mapandproperties.PropertyTableManager import PropertyTableManager, PropertyTableWidget

from ..utils.mapandproperties.PropertyDataLoader import PropertyDataLoader
from .theme_manager import ThemeManager

from ..constants.file_paths import QssPaths
from ..languages.language_manager import LanguageManager
from ..languages.translation_keys import TranslationKeys
from ..utils.MapTools.item_selector_tools import PropertiesSelectors
from ..constants.layer_constants import IMPORT_PROPERTY_TAG
from ..utils.MapTools.MapHelpers import MapHelpers




class AddPropertyDialog(QDialog):
    """
    Dialog for adding new properties with a smart list view
    """
    propertyAdded = pyqtSignal(dict)  # Signal emitted when property is added

    def __init__(self, parent=None):
        super().__init__(parent)

        # Minimize parent window while this dialog is open
        self._parent_window = None
        self._restore_parent_on_close = False
        try:
            self._parent_window = parent.window() if parent is not None else None
            if self._parent_window is not None and self._parent_window.isVisible() and not self._parent_window.isMinimized():
                self._parent_window.showMinimized()
                self._restore_parent_on_close = True
        except Exception:
            self._parent_window = None
            self._restore_parent_on_close = False

        # Restore parent when dialog closes (accept/reject)
        self.finished.connect(self._on_dialog_finished)

        # Initialize managers
        self.lang_manager = LanguageManager()
        # Initialize helper classes
        self.data_loader = PropertyDataLoader() #in file #PropertyDataLoader.py
        self.table_manager = PropertyTableManager()


        # Set up dialog properties
        self.setWindowTitle(self.lang_manager.translate(TranslationKeys.ADD_NEW_PROPERTY))
        self.setModal(True)
        self.setFixedSize(600, 400)  

        # Apply theme
        ThemeManager.set_initial_theme(
            self,
            None,  # No theme switch button for popup dialogs
            qss_files=[QssPaths.MAIN, QssPaths.SETUP_CARD, QssPaths.COMBOBOX]
        )

        self._create_ui()
        # Kick off data loading (may take time for first combo)

        self._setup_connections()

        # Debounce map updates triggered by rapid table selection changes
        self._map_update_timer = QTimer(self)
        self._map_update_timer.setSingleShot(True)
        self._map_update_timer.setInterval(150)
        self._map_update_timer.timeout.connect(self._update_map_from_table_selection)

        self.show()

        # Block until done
        self.exec_()


    def _on_dialog_finished(self, _result: int) -> None:
        import_layer = MapHelpers._get_layer_by_tag(IMPORT_PROPERTY_TAG)
        if import_layer:
            MapHelpers.clear_layer_filter(import_layer)
        # Ensure parent window is restored if dialog is closed directly
        if self._restore_parent_on_close and self._parent_window is not None:
            try:
                self._parent_window.showNormal()
                self._parent_window.raise_()
                self._parent_window.activateWindow()
            except Exception:
                pass

    def _create_ui(self):
        """Create the user interface with hierarchical selection"""
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        import_layer = MapHelpers._get_layer_by_tag(IMPORT_PROPERTY_TAG)
        if import_layer:
            MapHelpers.clear_layer_filter(import_layer)
        # Check if we have a property layer
        self.property_layer = self.data_loader.property_layer
        MapHelpers.clear_layer_filter(self.property_layer)
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
        self._create_combo_widget(layout)

        self.properties_table_widget, self.properties_table = PropertyTableWidget._create_properties_table()
        layout.addWidget(self.properties_table_widget)
        # Selection info and buttons
        self._create_selection_controls(layout)
        PropertyUpdateFlowCoordinator.load_county_combo(self.county_combo, self.property_layer)

    def _create_combo_widget(self, parent_layout):
        """Create county and municipality dropdowns"""
        # Filter section frame
        filter_frame = QFrame()
        filter_frame.setObjectName("FilterFrame")
        filter_frame.setFrameStyle(QFrame.StyledPanel)
        filter_layout = QVBoxLayout(filter_frame)
        filter_layout.setContentsMargins(6, 6, 6, 6)
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

        # Wire add button into table manager once created
        self.table_manager.set_add_button(self.add_button)

    def _setup_connections(self):
        """Set up signal connections"""
            
        # Dropdown connections - use selection handler
        self.county_combo.currentTextChanged.connect(
            lambda text: PropertyUpdateFlowCoordinator.on_county_changed(
                text, 
                self.municipality_combo, 
                self.properties_table
            )
        )
        self.municipality_combo.currentTextChanged.connect(
            lambda text: PropertyUpdateFlowCoordinator.on_municipality_changed(
                text, 
                self.county_combo, 
                self.municipality_combo, 
                self.city_combo, 
                self.properties_table
            )
        )
        self.city_combo.checkedItemsChanged.connect(
            lambda: PropertyUpdateFlowCoordinator.on_city_changed(
                self.properties_table,
                self.county_combo,
                self.municipality_combo,
                self.city_combo
            )
        )

        self.properties_table.itemSelectionChanged.connect(self._on_table_selection_changed)

    
        # Button connections
        self.select_all_btn.clicked.connect(
            lambda: self.table_manager.select_all(self.properties_table))
        self.clear_selection_btn.clicked.connect(
            lambda: self.table_manager.clear_selection(self.properties_table))
        self.cancel_button.clicked.connect(self.reject)
        self.add_button.clicked.connect(
            #lambda: PropertyUpdateFlowCoordinator.start_adding_properties(self.properties_table)
            lambda: MainAddPropertiesFlow.start_adding_properties(self.properties_table)
        )


    def _on_table_selection_changed(self):
        #print("Table selection changed")
        count = len(self.properties_table.selectionModel().selectedRows())

        self.selection_info.setText(
            self.lang_manager.translate(TranslationKeys.SELECTED_COUNT_TEMPLATE).format(count=count)
        )
        # Enable/disable add button based on selection
        self.add_button.setEnabled(count > 0)
        # Update map to show selected features

        # Debounced map update to avoid spamming selectionChanged/zoom operations
        self._map_update_timer.start()


    def _update_map_from_table_selection(self):
        PropertiesSelectors.show_connected_properties_on_map_from_table(self.properties_table, use_shp=True)
    
  