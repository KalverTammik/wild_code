from PyQt5.QtCore import QCoreApplication, Qt
from PyQt5.QtWidgets import QTableWidgetItem

from ...languages.translation_keys import TranslationKeys
from ...languages.language_manager import LanguageManager
from PyQt5.QtWidgets import (
    QVBoxLayout, QLabel,
    QFrame,
    QTableWidget, QHeaderView
)
 
class PropertyTableManager:
    """
    Handles table operations for property display and selection.
    Separated for better maintainability.
    """

    def __init__(self,):
        self.lang_manager = LanguageManager()

        self.add_button = None


    def set_add_button(self, button):
        """Optionally wire the add button to toggle when data loads."""
        self.add_button = button

    def populate_properties_table(self, properties, properties_table=None):
        """Populate the properties table with data"""
        if not properties_table:
            return False

        properties_table.setRowCount(len(properties))

        # Enable/disable add button based on data availability
        if self.add_button is not None:
            self.add_button.setEnabled(bool(properties))

        cadastral_ids = []

        for row, property_data in enumerate(properties):
            # Cadastral ID
            cadastral_id = str(property_data.get('cadastral_id', ""))
            cadastral_ids.append(cadastral_id)
            cadastral_item = QTableWidgetItem(cadastral_id)
            properties_table.setItem(row, 0, cadastral_item)

            # Address
            address_item = QTableWidgetItem(str(property_data['address']))
            properties_table.setItem(row, 1, address_item)
            # Area
            area_item = QTableWidgetItem(str(property_data['area']))
            properties_table.setItem(row, 2, area_item)

            # Settlement
            settlement_item = QTableWidgetItem(str(property_data['settlement']))
            properties_table.setItem(row, 3, settlement_item)

            # Store feature data in the row
            feature = property_data['feature']

            # Store feature on all cells so selectedItems() always yields feature payloads.
            try:
                cadastral_item.setData(Qt.UserRole, feature)
            except Exception:
                pass
            try:
                address_item.setData(Qt.UserRole, feature)
            except Exception:
                pass
            try:
                area_item.setData(Qt.UserRole, feature)
            except Exception:
                pass
            try:
                settlement_item.setData(Qt.UserRole, feature)
            except Exception:
                pass
    

            # Process events periodically to keep UI responsive during table population
            if row % 50 == 0:
                QCoreApplication.processEvents()

        return True            
        
    @staticmethod
    def select_all(table=None):
        """Select all properties in the table"""
        if table:
            table.selectAll()

    @staticmethod
    def clear_selection(table=None):
        """Clear all selections in the table"""
        if table:
            table.clearSelection()

    @staticmethod
    def get_selected_features(table=None):
        """Get the selected features from the table"""
        if not table:
            return []
            
        selected_items = table.selectedItems()
        if not selected_items:
            return []

        # Get unique selected features
        selected_features = set()
        for item in selected_items:
            feature = item.data(Qt.UserRole)
            if feature:
                selected_features.add(feature)

        return list(selected_features)
    
    @staticmethod
    def _get_active_rows_column_values(table, index_column=0):
        """
        Get values from a specific column for all selected rows in the table.
        """

        selected_values = []
        for index in table.selectedIndexes():
            if index.column() == index_column:
                value = index.data()
                if value:
                    selected_values.append(str(value))

        if not selected_values:
            return None

        return selected_values

class PropertyTableWidget:
    @staticmethod   
    def _create_properties_table():
        """Create the properties table"""
        # Table section
        lang_manager = LanguageManager()

        table_frame = QFrame()
        table_frame.setObjectName("TableFrame")
        table_frame.setFrameStyle(QFrame.StyledPanel)
        table_layout = QVBoxLayout(table_frame)
        table_layout.setContentsMargins(6, 6, 6, 6)
        table_layout.setSpacing(6)
        
        # Properties table
        properties_table = QTableWidget()
        properties_table.setObjectName("PropertiesTable")
        # Zebra + look
        properties_table.setAlternatingRowColors(True)
        properties_table.setShowGrid(True)                 # or False if you want cleaner blocks
        properties_table.setGridStyle(Qt.SolidLine)

        properties_table.setSelectionBehavior(QTableWidget.SelectRows)
        properties_table.setSelectionMode(QTableWidget.MultiSelection)   # or ExtendedSelection (usually nicer)


        # Make selection/hover feel nicer and avoid “full repaint storms”
        properties_table.setMouseTracking(True)            # enables :hover painting reliably
        properties_table.setSortingEnabled(False)          # avoid selection jumping during fill
        properties_table.setUpdatesEnabled(True)           # ensure stylesheet paints correctly

        # Headers (these matter a lot for the look in your screenshot)
        properties_table.verticalHeader().setVisible(True) # if you want row numbers
        properties_table.horizontalHeader().setStretchLastSection(True)
        properties_table.horizontalHeader().setHighlightSections(False)
        properties_table.verticalHeader().setHighlightSections(False)

        properties_table.verticalHeader().setVisible(False)
        properties_table.setCornerButtonEnabled(False)          # hides the top-left corner button area (sometimes)
        properties_table.horizontalHeader().setStretchLastSection(True)

        header = properties_table.horizontalHeader()
        header.setFixedHeight(24)
        # Optional: more compact / consistent row height
        properties_table.verticalHeader().setDefaultSectionSize(18)



        # Set up table headers
        headers = [
            lang_manager.translate(TranslationKeys.CADASTRAL_ID),
            lang_manager.translate(TranslationKeys.ADDRESS),
            lang_manager.translate(TranslationKeys.AREA),
            lang_manager.translate(TranslationKeys.SETTLEMENT)
        ]
        properties_table.setColumnCount(len(headers))
        properties_table.setHorizontalHeaderLabels(headers)

        # Configure table
        header = properties_table.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(QHeaderView.Interactive)

        table_layout.addWidget(properties_table)
        return table_frame, properties_table