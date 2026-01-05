import os
from typing import Optional

from PyQt5.QtCore import pyqtSignal, Qt, QTimer
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QLabel,
    QPushButton, QHBoxLayout, QCheckBox, QProgressBar
)

from ..modules.Property.FlowControllers.MainAddProperties import MainAddPropertiesFlow
from ..modules.Property.FlowControllers.BackendVerifyController import BackendVerifyController
from ..modules.Property.FlowControllers.MainLayerCheckController import MainLayerCheckController
from ..modules.Property.FlowControllers.AttentionDisplayRules import AttentionDisplayRules
from ..utils.mapandproperties.PropertyTableManager import PropertyTableManager, PropertyTableWidget

from ..utils.mapandproperties.PropertyDataLoader import PropertyDataLoader
from .theme_manager import ThemeManager

from ..constants.button_props import ButtonVariant, ButtonSize
from ..constants.file_paths import QssPaths
from ..languages.language_manager import LanguageManager
from ..languages.translation_keys import TranslationKeys
from ..utils.MapTools.item_selector_tools import PropertiesSelectors
from ..constants.layer_constants import IMPORT_PROPERTY_TAG
from ..utils.MapTools.MapHelpers import MapHelpers, ActiveLayersHelper
from ..constants.cadastral_fields import Katastriyksus
from ..widgets.DateHelpers import DateHelpers

from .LocationFilterWidget import LocationFilterWidget, LocationFilterHelper




class AddPropertyDialog(QDialog):
    """
    Dialog for adding new properties with a smart list view
    """
    propertyAdded = pyqtSignal(dict)  # Signal emitted when property is added

    def __init__(self, parent=None):
        super().__init__(parent)

        # Always define these so we can use direct `self.` access everywhere.
        self.properties_table_widget = None
        self.properties_table = None

        # Location filter widget + combos (set in _create_ui)
        self.location_filter_widget = None
        self.county_combo = None
        self.municipality_combo = None
        self.city_combo = None
        self._location_filter_helper: Optional[LocationFilterHelper] = None

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

        # Debounce map updates triggered by rapid table selection changes
        self._map_update_timer = QTimer(self)
        self._map_update_timer.setSingleShot(True)
        self._map_update_timer.setInterval(150)
        self._map_update_timer.timeout.connect(
            lambda: PropertiesSelectors.show_connected_properties_on_map_from_table(self.properties_table, use_shp=True)
        )

        # Location filter controller
        self._location_filter_helper = LocationFilterHelper(
            county_combo=self.county_combo,
            municipality_combo=self.municipality_combo,
            city_combo=self.city_combo,
            properties_table=self.properties_table,
            after_table_update=self._after_table_update,
            stop_checks=lambda clear_attention: self._stop_attention_checks(clear_attention=clear_attention),
            update_add_button_state=lambda count: self._update_add_button_state(selected_count=count),
            zoom_map=self._map_update_timer.start,
            parent=self,
        )
        self._location_filter_helper.load_counties(self.property_layer)

        self._setup_connections()

        # --- Progressive Attention checks (borrowed from SignalTest patterns) ---
        self._backend_verify_controller = BackendVerifyController(self)
        self._backend_verify_controller.rowResult.connect(self._on_backend_verify_row_result)
        self._backend_verify_controller.finished.connect(self._on_backend_verify_finished)

        self._main_check_controller = MainLayerCheckController(self)
        self._main_check_controller.rowResult.connect(self._on_main_check_row_result)
        self._main_check_controller.finished.connect(self._on_main_check_finished)

        self._checks_running = False
        self._rows_for_verify_by_row = {}
        self._backend_compare_causes_by_row = {}
        self._main_compare_causes_by_row = {}
        self._backend_checked_rows = set()
        self._main_checked_rows = set()
        self._total_rows_for_checks = 0
        self._main_layer_for_verify = None

        # Track whether the table is currently filtered down to attention-only rows.
        self._table_filtered_to_attention = False

        # Debounce starting checks after table repopulation
        self._checks_start_timer = QTimer(self)
        self._checks_start_timer.setSingleShot(True)
        self._checks_start_timer.setInterval(250)
        self._checks_start_timer.timeout.connect(self._start_attention_checks_from_timer)
        self._pending_checks_source = "add_property_dialog"

        self.show()

        # Block until done
        self.exec_()


    def _on_dialog_finished(self, _result: int) -> None:
        self._stop_attention_checks()
        if self._location_filter_helper is not None:
            self._location_filter_helper.stop_pending_city_reload()
        import_layer = MapHelpers._get_layer_by_tag(IMPORT_PROPERTY_TAG)
        if import_layer:
            MapHelpers.clear_layer_filter(import_layer)
        # Ensure parent window is restored if dialog is closed directly
        if self._restore_parent_on_close and self._parent_window is not None:
            self._parent_window.showNormal()
            self._parent_window.raise_()
            self._parent_window.activateWindow()

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
        self.location_filter_widget = LocationFilterWidget(self.lang_manager)
        layout.addWidget(self.location_filter_widget)

        # Keep legacy attribute names used across this dialog + coordinators.
        self.county_combo = self.location_filter_widget.county_combo
        self.municipality_combo = self.location_filter_widget.municipality_combo
        self.city_combo = self.location_filter_widget.city_combo

        self.properties_table_widget, self.properties_table = PropertyTableWidget._create_properties_table()
        layout.addWidget(self.properties_table_widget)
        # Selection info and buttons
        self._create_selection_controls(layout)

    def _create_selection_controls(self, parent_layout):
        """Create selection info and control buttons"""
        # Selection info
        self.selection_info = QLabel(self.lang_manager.translate(TranslationKeys.SELECTED_PROPERTIES_COUNT))
        self.selection_info.setObjectName("SelectionInfo")
        parent_layout.addWidget(self.selection_info)

        # Progress bar for checks (done/total)
        self.check_progress_bar = QProgressBar()
        self.check_progress_bar.setObjectName("CheckProgressBar")
        self.check_progress_bar.setTextVisible(True)
        self.check_progress_bar.setRange(0, 1)
        self.check_progress_bar.setValue(0)
        self.check_progress_bar.setVisible(False)
        parent_layout.addWidget(self.check_progress_bar)

        # Default UX: focus only on rows that need attention after checks finish.
        self.attention_only_checkbox = QCheckBox("Show only attention")
        self.attention_only_checkbox.setChecked(True)
        self.attention_only_checkbox.setObjectName("SelectionInfo")
        parent_layout.addWidget(self.attention_only_checkbox)

        # Buttons
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(10)

        # Selection buttons
        self.select_all_btn = QPushButton(self.lang_manager.translate(TranslationKeys.SELECT_ALL))
        self.select_all_btn.setObjectName("SelectAllButton")
        self.select_all_btn.setProperty("variant", ButtonVariant.GHOST)
        self.select_all_btn.setProperty("btnSize", ButtonSize.SMALL)
        buttons_layout.addWidget(self.select_all_btn)

        self.clear_selection_btn = QPushButton(self.lang_manager.translate(TranslationKeys.CLEAR_SELECTION))
        self.clear_selection_btn.setObjectName("ClearSelectionButton")
        self.clear_selection_btn.setProperty("variant", ButtonVariant.GHOST)
        self.clear_selection_btn.setProperty("btnSize", ButtonSize.SMALL)
        buttons_layout.addWidget(self.clear_selection_btn)

        buttons_layout.addStretch()

        # Action buttons
        self.cancel_button = QPushButton(self.lang_manager.translate(TranslationKeys.CANCEL))
        self.cancel_button.setObjectName("CancelButton")
        self.cancel_button.setProperty("variant", ButtonVariant.GHOST)
        buttons_layout.addWidget(self.cancel_button)

        self.add_button = QPushButton(self.lang_manager.translate(TranslationKeys.ADD_SELECTED))
        self.add_button.setObjectName("AddButton")
        self.add_button.setEnabled(False)  # Disabled until properties are selected
        self.add_button.setProperty("variant", ButtonVariant.PRIMARY)
        buttons_layout.addWidget(self.add_button)

        parent_layout.addLayout(buttons_layout)

        # Add button is gated by selection + checks, so we manage it locally.

    def _setup_connections(self):
        """Set up signal connections"""

        # Dropdown connections are owned by LocationFilterHelper
        if self._location_filter_helper is not None:
            self._location_filter_helper.connect_signals()

        self.properties_table.itemSelectionChanged.connect(self._on_table_selection_changed)

        self.attention_only_checkbox.stateChanged.connect(self._on_attention_only_changed)

    
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

    def _on_attention_only_changed(self, _state: int) -> None:
        # If user turns it off after filtering, reload full table from current filters.
        checked = bool(self.attention_only_checkbox.isChecked())

        if not checked:
            if self._table_filtered_to_attention:
                self._table_filtered_to_attention = False
                if self._location_filter_helper is not None:
                    self._location_filter_helper.reload_current_table_from_filters(zoom=True)
            return

        # If checks already finished, apply immediately.
        if not self._checks_running:
            self._apply_attention_only_filter_if_ready()

    def _on_table_selection_changed(self):
        self._refresh_selection_info(update_map=True)

    def _refresh_selection_info(self, *, update_map: bool) -> int:
        """Refresh selected-count label.

        During table reloads (e.g. city filter) the table may block signals, so
        `itemSelectionChanged` won't fire even if rows get selected programmatically.
        """

        table = self.properties_table
        if table is None:
            return 0

        selected_features = set()
        try:
            for index in table.selectionModel().selectedRows():
                item = table.item(index.row(), 0)  # always column 0
                if item is None:
                    continue
                feature = item.data(Qt.UserRole)
                if feature:
                    selected_features.add(feature)
        except Exception:
            selected_features = set()

        count = len(selected_features)
        try:
            self.selection_info.setText(
                self.lang_manager.translate(TranslationKeys.SELECTED_COUNT_TEMPLATE).format(count=count)
            )
        except Exception:
            pass

        self._update_add_button_state(selected_count=count)

        if update_map:
            self._map_update_timer.start()

        return count


    # ---------------------------------------------------------------------
    # Attention checks + status
    # ---------------------------------------------------------------------

    def _after_table_update(self, _table) -> None:
        """Called after PropertyUpdateFlowCoordinator repopulates + selects the table."""

        self._stop_attention_checks(clear_attention=True)

        table = self.properties_table
        if table is None:
            return

        if table.rowCount() <= 0:
            self._update_add_button_state()
            return

        # Keep the selection count correct after programmatic reload/selection.
        self._refresh_selection_info(update_map=False)

        if self._location_filter_helper is not None:
            self._location_filter_helper.handle_after_table_update()

        # Start checks only after a short quiet period (user may still be narrowing selections).
        self._pending_checks_source = "add_property_dialog"
        try:
            self._checks_start_timer.start()
        except Exception:
            self._start_attention_checks(source=self._pending_checks_source)

    def _start_attention_checks_from_timer(self) -> None:
        self._start_attention_checks(source=self._pending_checks_source)

    def _stop_attention_checks(self, *, clear_attention: bool = False) -> None:
        self._checks_start_timer.stop()
        self._backend_verify_controller.stop()
        self._main_check_controller.stop()

        self._checks_running = False
        self._rows_for_verify_by_row = {}
        self._backend_compare_causes_by_row = {}
        self._main_compare_causes_by_row = {}
        self._backend_checked_rows = set()
        self._main_checked_rows = set()
        self._total_rows_for_checks = 0
        self._main_layer_for_verify = None

        self._set_check_progress(0, 0)

        self._table_filtered_to_attention = False

        if clear_attention:
            table = self.properties_table
            if table is not None:
                for row_idx in range(table.rowCount()):
                    PropertyTableManager.set_cell_text(table, row_idx, PropertyTableWidget._COL_ATTENTION, "")

        self._update_add_button_state()

    def _start_attention_checks(self, *, source: str) -> None:
        table = self.properties_table
        if table is None:
            return

        self._stop_attention_checks(clear_attention=False)

        date_helpers = DateHelpers()
        rows = []
        rows_for_verify_by_row = {}
        for row_idx in range(table.rowCount()):
            tunnus = PropertyTableManager.get_cell_text(table, row_idx, PropertyTableWidget._COL_CADASTRAL_ID)
            if not tunnus:
                continue

            import_muudet = PropertyTableManager.get_payload_field_text(
                table,
                row_idx,
                PropertyTableWidget._COL_CADASTRAL_ID,
                Katastriyksus.muudet,
                normalizer=date_helpers.date_to_iso_string,
            )

            rows.append((row_idx, tunnus, import_muudet))
            rows_for_verify_by_row[int(row_idx)] = (tunnus, import_muudet)

        self._rows_for_verify_by_row = rows_for_verify_by_row
        self._total_rows_for_checks = len(rows)
        self._checks_running = bool(rows)

        self._set_check_progress(0, self._total_rows_for_checks)

        # Gate Add button while checks are running.
        self._update_add_button_state()

        if not rows:
            self._set_check_progress(0, 0)
            return

        # Cache MAIN layer once per run (UI-thread access).
        self._main_layer_for_verify = ActiveLayersHelper.resolve_main_property_layer(silent=False)

        self._main_check_controller.configure(
            rows_for_verify_by_row=self._rows_for_verify_by_row,
            main_layer=self._main_layer_for_verify,
            checked_rows=self._main_checked_rows,
        )
 
        # Mark in-progress in the Attention column.
        table.setUpdatesEnabled(False)
        for row_idx, _tunnus, _import_muudet in rows:
            PropertyTableManager.set_cell_text(table, row_idx, PropertyTableWidget._COL_ATTENTION, "Võrdlen andmeid...")
        table.setUpdatesEnabled(True)
 
        self._update_check_status_label()

        try:
            self._backend_verify_controller.start(rows, source=source)
        except Exception:
            # If backend verify cannot start, fall back to running MAIN checks only.
            # Mark backend as "done" for all rows so completion is driven by MAIN checks.
            self._backend_checked_rows = set(self._rows_for_verify_by_row.keys())
            remaining = list(self._rows_for_verify_by_row.keys())
            self._main_check_controller.start_pending(remaining, batch_size=50, interval_ms=0)


    def _on_backend_verify_row_result(self, row: int, _tunnus: str, result: dict) -> None:
        row_idx = int(row)
 
        causes = []
        try:
            causes_raw = result.get("causes") if isinstance(result, dict) else []
            if isinstance(causes_raw, list):
                causes = [str(c).strip() for c in causes_raw if str(c).strip()]
        except Exception:
            causes = []

        self._backend_compare_causes_by_row[row_idx] = causes
        self._backend_checked_rows.add(row_idx)

        # Run MAIN check for this row now (keeps UI responsive).
        self._main_check_controller.ensure_row(row_idx)

        self._update_row_attention_display(row_idx)
        self._update_check_status_label()

    def _on_backend_verify_finished(self, _summary: dict) -> None:
        # Ensure remaining MAIN rows finish in batches.
        try:
            remaining = [r for r in self._rows_for_verify_by_row.keys() if r not in self._main_checked_rows]
        except Exception:
            remaining = []

        if remaining:
            self._main_check_controller.start_pending(remaining, batch_size=50, interval_ms=0)

        # If MAIN is already done, finalize now.
        self._maybe_finish_checks()

    def _on_main_check_row_result(self, row: int, causes: list) -> None:
        row_idx = int(row)

        self._main_compare_causes_by_row[row_idx] = [str(c).strip() for c in (causes or []) if str(c).strip()]

        self._main_checked_rows.add(row_idx)
        self._update_row_attention_display(row_idx)
        self._update_check_status_label()
        self._maybe_finish_checks()

    def _on_main_check_finished(self) -> None:
        self._maybe_finish_checks()

    def _update_row_attention_display(self, row_idx: int) -> None:
        main_causes = self._main_compare_causes_by_row.get(row_idx) or []
        backend_causes = self._backend_compare_causes_by_row.get(row_idx) or []

        main_done = row_idx in self._main_checked_rows
        backend_done = row_idx in self._backend_checked_rows

        text = AttentionDisplayRules.build_attention_text(
            main_causes,
            backend_causes,
            main_done=main_done,
            backend_done=backend_done,
        )
        PropertyTableManager.set_cell_text(self.properties_table, row_idx, PropertyTableWidget._COL_ATTENTION, text)

    def _maybe_finish_checks(self) -> None:
        if not self._checks_running:
            return

        total = int(self._total_rows_for_checks or 0)
        if total <= 0:
            self._checks_running = False
            self._update_add_button_state()
            self._set_check_progress(0, 0)
            return

        # Consider a row "done" only when both backend + MAIN finished for that row.
        done_rows = 0
        for row_idx in self._rows_for_verify_by_row.keys():
            if row_idx in self._backend_checked_rows and row_idx in self._main_checked_rows:
                done_rows += 1

        if done_rows < total:
            return

        self._checks_running = False
        self._update_add_button_state()

        self._set_check_progress(total, total)

        # Summarize attention count.
        attention = 0
        for row_idx in self._rows_for_verify_by_row.keys():
            combined = AttentionDisplayRules.combined_causes(
                self._main_compare_causes_by_row.get(row_idx) or [],
                self._backend_compare_causes_by_row.get(row_idx) or [],
            )
            if combined:
                attention += 1

        # Hide the progress bar once finished.
        self._set_check_progress(0, 0)

        # If enabled, reduce the table to only rows that need attention and sync map selection.
        self._apply_attention_only_filter_if_ready()

    def _apply_attention_only_filter_if_ready(self) -> None:
        if not bool(self.attention_only_checkbox.isChecked()):
            return

        # Only apply after at least one completed run.
        if int(self._total_rows_for_checks or 0) <= 0:
            return

        # Only filter when there is something to focus on.
        attention_rows = self._get_attention_row_indices()
        if not attention_rows:
            return

        # Avoid re-filtering.
        if self._table_filtered_to_attention is True:
            return

        self._apply_attention_only_filter(attention_rows)

    def _get_attention_row_indices(self) -> list[int]:
        rows: list[int] = []
        for row_idx in self._rows_for_verify_by_row.keys():
            combined = AttentionDisplayRules.combined_causes(
                self._main_compare_causes_by_row.get(row_idx) or [],
                self._backend_compare_causes_by_row.get(row_idx) or [],
            )
            if combined:
                rows.append(int(row_idx))

        return sorted(set(rows))

    def _apply_attention_only_filter(self, attention_rows: list[int]) -> None:
        table = self.properties_table
        if table is None:
            return

        keep = {int(r) for r in (attention_rows or [])}
        if not keep:
            return

        # Remove non-attention rows (from bottom up so indices stay valid).
        table.setUpdatesEnabled(False)
        table.blockSignals(True)
        table.clearSelection()

        for row_idx in range(table.rowCount() - 1, -1, -1):
            if row_idx not in keep:
                table.removeRow(row_idx)

        table.blockSignals(False)
        table.setUpdatesEnabled(True)

        # Select remaining rows so map highlights only attention items.
        if table.rowCount() > 0:
            table.selectAll()

        # Clear map selection first, then zoom/select from the table.
        import_layer = MapHelpers._get_layer_by_tag(IMPORT_PROPERTY_TAG)
        if import_layer is not None:
            import_layer.removeSelection()

        self._table_filtered_to_attention = True

        # Refresh selection count + trigger debounced map update.
        self._on_table_selection_changed()

    def _update_check_status_label(self) -> None:
        total = int(self._total_rows_for_checks or 0)
        if not self._checks_running or total <= 0:
            self._set_check_progress(0, 0)
            return

        done_rows = 0
        for row_idx in self._rows_for_verify_by_row.keys():
            if row_idx in self._backend_checked_rows and row_idx in self._main_checked_rows:
                done_rows += 1

        self._set_check_progress(done_rows, total)

    def _set_check_progress(self, done: int, total: int) -> None:
        bar = self.check_progress_bar
        if bar is None:
            return

        total_i = int(total or 0)
        done_i = int(done or 0)

        if total_i <= 0:
            bar.setVisible(False)
            bar.setRange(0, 1)
            bar.setValue(0)
            bar.setFormat("")
            return

        if done_i < 0:
            done_i = 0
        if done_i > total_i:
            done_i = total_i

        bar.setVisible(True)
        bar.setRange(0, total_i)
        bar.setValue(done_i)
        bar.setFormat("%v/%m")


    def _update_add_button_state(self, *, selected_count: Optional[int] = None) -> None:
        if selected_count is None:
            selected_count = len(self.properties_table.selectionModel().selectedRows() or [])
        can_add = bool(selected_count and int(selected_count) > 0 and not self._checks_running)
        self.add_button.setEnabled(can_add)

