from PyQt5.QtCore import QCoreApplication, Qt
from PyQt5.QtWidgets import QTableWidgetItem


class PropertyTableManager:
    """
    Handles table operations for property display and selection.
    Separated for better maintainability.
    """

    def __init__(self, properties_table, lang_manager):
        self.properties_table = properties_table
        self.lang_manager = lang_manager
        self.selection_changed_callback = None

    def set_selection_changed_callback(self, callback):
        """Set callback for selection changes"""
        self.selection_changed_callback = callback

    def populate_properties_table(self, properties):
        """Populate the properties table with data"""
        if not self.properties_table:
            return
            
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

            # Process events periodically to keep UI responsive during table population
            if row % 50 == 0:
                QCoreApplication.processEvents()

    def on_table_selection_changed(self):
        """Handle table selection changes"""
        if not self.properties_table:
            return 0
            
        selected_rows = set()
        for item in self.properties_table.selectedItems():
            selected_rows.add(item.row())

        selected_count = len(selected_rows)

        # Call the callback if set
        if self.selection_changed_callback:
            self.selection_changed_callback(selected_count)

        return selected_count

    def select_all(self):
        """Select all properties in the table"""
        if self.properties_table:
            self.properties_table.selectAll()

    def clear_selection(self):
        """Clear all selections in the table"""
        if self.properties_table:
            self.properties_table.clearSelection()

    def get_selected_features(self):
        """Get the selected features from the table"""
        if not self.properties_table:
            return []
            
        selected_items = self.properties_table.selectedItems()
        if not selected_items:
            return []

        # Get unique selected features
        selected_features = set()
        for item in selected_items:
            feature = item.data(Qt.UserRole)
            if feature:
                selected_features.add(feature)

        return list(selected_features)