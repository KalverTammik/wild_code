from typing import Any, Callable, Optional

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QVBoxLayout,
    QFrame,
    QHeaderView, QTableView
)

from ...languages.translation_keys import TranslationKeys
from ...languages.language_manager import LanguageManager

from .property_table_model import PropertyTableModel
from ...Logs.python_fail_logger import PythonFailLogger
 
class PropertyTableManager:
    """
    Handles table operations for property display and selection.
    Separated for better maintainability.
    """

    def __init__(self,):
        self.lang_manager = LanguageManager()

        self.add_button = None


    def populate_properties_table(self, properties, properties_table=None):
        """Populate the properties table with data"""
        if not properties_table:
            return False

        model = properties_table.model()
        if not isinstance(model, PropertyTableModel):
            headers = PropertyTableWidget._headers()
            model = PropertyTableModel(headers, parent=properties_table)
            properties_table.setModel(model)

        model.set_rows(properties)

        if self.add_button is not None:
            self.add_button.setEnabled(bool(properties))

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

        selected_rows = table.selectionModel().selectedRows() if table.selectionModel() else []
        selected_features = set()
        for index in selected_rows:
            feature = PropertyTableManager.get_cell_data(table, index.row(), 0, role=Qt.UserRole)
            if feature:
                selected_features.add(feature)
        return list(selected_features)

    @staticmethod
    def get_cadastral_ids(table) -> set[str]:
        if table is None:
            return set()
        model = table.model()
        return model.cadastral_ids() if isinstance(model, PropertyTableModel) else set()

    @staticmethod
    def get_all_features(table=None):
        """Get all feature payloads currently visible in the table."""
        if not table:
            return []

        features = []
        seen = set()

        def _feature_key(feature):
            try:
                return ("fid", int(feature.id()))
            except Exception:
                return ("obj", id(feature))

        for row in range(PropertyTableManager.row_count(table)):
            feature = PropertyTableManager.get_cell_data(table, row, 0, role=Qt.UserRole)
            if not feature:
                continue
            key = _feature_key(feature)
            if key in seen:
                continue
            seen.add(key)
            features.append(feature)

        return features

    @staticmethod
    def get_cell_text(table, row: int, col: int) -> str:
        if table is None:
            return ""
        try:
            model = table.model()
            if model is None:
                return ""
            return str(model.data(model.index(int(row), int(col)), Qt.DisplayRole) or "").strip()
        except Exception:
            return ""

    @staticmethod
    def get_cell_data(table, row: int, col: int, *, role=Qt.UserRole) -> Any:
        if table is None:
            return None
        try:
            model = table.model()
            if model is None:
                return None
            return model.data(model.index(int(row), int(col)), role)
        except Exception:
            return None

    @staticmethod
    def set_status(table, row: int, col: int, *, state: str, tooltip: str = "") -> bool:
        if table is None:
            return False

        try:
            model = table.model()
            if isinstance(model, PropertyTableModel):
                return bool(model.set_status(int(row), int(col), state=state, tooltip=tooltip))
        except Exception:
            return False
        return False

    @staticmethod
    def row_count(table) -> int:
        if table is None:
            return 0
        try:
            model = table.model()
            return int(model.rowCount()) if model is not None else 0
        except Exception:
            return 0

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
    def reset_and_populate_properties_table(table, rows, *, after_populate=None) -> bool:
        """Reset table contents and repopulate via the shared PropertyTableManager."""

        if table is None:
            return False

        table.setUpdatesEnabled(False)
        table.clearSelection()

        try:
            ok = bool(PropertyTableManager().populate_properties_table(rows, table))
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module="ui",
                event="property_table_populate_failed",
            )
            ok = False

        if ok and after_populate is not None:
            after_populate()

        table.setUpdatesEnabled(True)

        try:
            table.viewport().update()
            table.repaint()
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module="ui",
                event="property_table_repaint_failed",
            )

        return ok

class PropertyTableWidget:

    _COL_CADASTRAL_ID = 0
    _COL_ADDRESS = 1
    _COL_AREA = 2
    _COL_SETTLEMENT = 3
    _COL_BACKEND_ATTENTION = 4
    _COL_MAIN_ATTENTION = 5
    _COL_ARCHIVE_BACKEND = 6
    _COL_ARCHIVE_MAP = 7



    @staticmethod   
    def _headers():
        lang_manager = LanguageManager()
        return [
            lang_manager.translate(TranslationKeys.CADASTRAL_ID),
            lang_manager.translate(TranslationKeys.ADDRESS),
            lang_manager.translate(TranslationKeys.AREA),
            lang_manager.translate(TranslationKeys.SETTLEMENT),
            lang_manager.translate(TranslationKeys.PROPERTY_COLUMN_BACKEND),
            lang_manager.translate(TranslationKeys.PROPERTY_COLUMN_MAIN_LAYER),
            lang_manager.translate(TranslationKeys.PROPERTY_COLUMN_ARCHIVE_BACKEND),
            lang_manager.translate(TranslationKeys.PROPERTY_COLUMN_ARCHIVE_MAP),
        ]

    @staticmethod
    def create_properties_table():
        return PropertyTableWidget._create_properties_table()

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
        properties_table = QTableView()
        properties_table.setObjectName("PropertiesTable")
        # Zebra + look
        properties_table.setAlternatingRowColors(True)
        try:
            properties_table.setShowGrid(True)                 # or False if you want cleaner blocks
            properties_table.setGridStyle(Qt.SolidLine)
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module="ui",
                event="property_table_grid_failed",
            )

        properties_table.setSelectionBehavior(QTableView.SelectRows)
        properties_table.setSelectionMode(QTableView.MultiSelection)   # or ExtendedSelection (usually nicer)


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
        try:
            properties_table.setCornerButtonEnabled(False)          # hides the top-left corner button area (sometimes)
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module="ui",
                event="property_table_corner_button_failed",
            )
        properties_table.horizontalHeader().setStretchLastSection(True)

        header = properties_table.horizontalHeader()
        header.setFixedHeight(24)
        # Optional: more compact / consistent row height
        properties_table.verticalHeader().setDefaultSectionSize(18)



        # Set up table headers / model
        headers = PropertyTableWidget._headers()
        model = PropertyTableModel(headers, parent=properties_table)
        properties_table.setModel(model)

        # Configure table
        header = properties_table.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(QHeaderView.Interactive)

        table_layout.addWidget(properties_table)
        return table_frame, properties_table
