from typing import Any, Callable, Optional

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
            cadastral_item.setData(Qt.UserRole, feature)
            address_item.setData(Qt.UserRole, feature)
            area_item.setData(Qt.UserRole, feature)
            settlement_item.setData(Qt.UserRole, feature)
    

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
    def get_selected_row_indices(table) -> list[int]:
        """Return unique selected row indices in ascending order."""

        if table is None:
            return []

        try:
            rows_set: set[int] = set()
            for item in table.selectedItems() or []:
                rows_set.add(int(item.row()))
            return sorted(rows_set)
        except Exception:
            return []

    @staticmethod
    def get_first_selected_row_index(table) -> Optional[int]:
        """Return the first selected row index, or None if nothing selected."""

        rows = PropertyTableManager.get_selected_row_indices(table)
        return rows[0] if rows else None

    @staticmethod
    def get_cell_text(table, row: int, col: int) -> str:
        if table is None:
            return ""
        try:
            item = table.item(int(row), int(col))
            return (item.text() if item is not None else "").strip()
        except Exception:
            return ""

    @staticmethod
    def set_cell_text(table, row: int, col: int, text: str) -> bool:
        """Ensure a cell exists and set its text.

        Returns True when the cell was updated, False otherwise.
        """

        if table is None:
            return False

        try:
            row_i = int(row)
            col_i = int(col)
        except (TypeError, ValueError):
            return False

        try:
            item = table.item(row_i, col_i)
            if item is None:
                item = QTableWidgetItem("")
                table.setItem(row_i, col_i, item)
            item.setText(str(text or ""))
            return True
        except Exception:
            return False

    @staticmethod
    def get_cell_data(table, row: int, col: int, *, role=Qt.UserRole) -> Any:
        if table is None:
            return None
        try:
            item = table.item(int(row), int(col))
            return item.data(role) if item is not None else None
        except Exception:
            return None

    @staticmethod
    def get_payload_field_value(table, row: int, payload_col: int, field_key: object, *, role=Qt.UserRole) -> Any:
        """Read a field value from the payload stored in a table cell.

        Supports QgsFeature and other dict-like payloads implementing `__getitem__`.
        """

        payload = PropertyTableManager.get_cell_data(table, row, payload_col, role=role)
        if payload is None:
            return None
        try:
            return payload[field_key]
        except Exception:
            return None

    @staticmethod
    def get_payload_field_text(
        table,
        row: int,
        payload_col: int,
        field_key: object,
        *,
        role=Qt.UserRole,
        normalizer: Optional[Callable[[Any], Optional[str]]] = None,
        default: str = "",
    ) -> str:
        value = PropertyTableManager.get_payload_field_value(table, row, payload_col, field_key, role=role)
        if value is None:
            return default

        if normalizer is not None:
            try:
                normalized = normalizer(value)
            except Exception:
                normalized = None
            if normalized:
                return str(normalized)

        try:
            return str(value)
        except Exception:
            return default

    @staticmethod
    def get_selected_column_values(
        table,
        col: int,
        *,
        unique: bool = True,
        include_empty: bool = False,
    ) -> list[str]:
        """Return values from `col` for selected rows.

        Uses `get_selected_row_indices()` so it works regardless of which cells are selected.
        """

        if table is None:
            return []

        values: list[str] = []
        for row in PropertyTableManager.get_selected_row_indices(table):
            value = PropertyTableManager.get_cell_text(table, row, col)
            if not value and not include_empty:
                continue
            values.append(value)

        if not unique:
            return values

        seen: set[str] = set()
        unique_values: list[str] = []
        for value in values:
            if value in seen:
                continue
            seen.add(value)
            unique_values.append(value)
        return unique_values

    @staticmethod
    def create_snapshot_table_from_rows(source_table, rows: list[int], *, table_factory=None):
        """Create a read-only snapshot table for the given source rows.

        `table_factory` should return `(frame, table)` (e.g. `PropertyTableWidget._create_properties_table`).
        """

        if source_table is None:
            return None, None

        if table_factory is None:
            table_factory = PropertyTableWidget._create_properties_table

        frame, snapshot_table = table_factory()

        headers: list[str] = []
        for c in range(source_table.columnCount()):
            try:
                h = source_table.horizontalHeaderItem(c)
                headers.append(h.text() if h else "")
            except Exception:
                headers.append("")

        snapshot_table.setColumnCount(len(headers))
        snapshot_table.setHorizontalHeaderLabels(headers)

        snapshot_table.setRowCount(len(rows))
        for out_row_idx, src_row_idx in enumerate(rows):
            for col in range(source_table.columnCount()):
                src_item = source_table.item(src_row_idx, col)
                text = src_item.text() if src_item is not None else ""
                snapshot_table.setItem(out_row_idx, col, QTableWidgetItem(text))

        snapshot_table.setSelectionMode(QTableWidget.NoSelection)
        snapshot_table.setFocusPolicy(Qt.NoFocus)

        return frame, snapshot_table

    @staticmethod
    def reset_and_populate_properties_table(table, rows, *, after_populate=None) -> bool:
        """Reset table contents and repopulate via the shared PropertyTableManager."""

        if table is None:
            return False

        table.setUpdatesEnabled(False)
        table.clearSelection()
        table.clearContents()
        table.setRowCount(0)

        try:
            ok = bool(PropertyTableManager().populate_properties_table(rows, table))
        except Exception:
            ok = False

        if ok and after_populate is not None:
            after_populate()

        table.setUpdatesEnabled(True)

        table.viewport().update()
        table.repaint()

        return ok

class PropertyTableWidget:

    _COL_CADASTRAL_ID = 0
    _COL_ADDRESS = 1
    _COL_AREA = 2
    _COL_SETTLEMENT = 3
    _COL_ATTENTION = 4



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
            lang_manager.translate(TranslationKeys.SETTLEMENT),
            lang_manager.translate(TranslationKeys.ATTENTION),
        ]
        properties_table.setColumnCount(len(headers))
        properties_table.setHorizontalHeaderLabels(headers)

        # Configure table
        header = properties_table.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(QHeaderView.Interactive)

        table_layout.addWidget(properties_table)
        return table_frame, properties_table