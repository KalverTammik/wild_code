import os
from typing import Optional

from PyQt5.QtCore import pyqtSignal, Qt, QTimer, QCoreApplication
from PyQt5.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QLabel,
    QPushButton,
    QHBoxLayout,
    QCheckBox,
    QProgressBar,
)

from qgis.core import QgsFeatureRequest
from qgis.utils import iface

from ..modules.Property.FlowControllers.MainAddProperties import MainAddPropertiesFlow
from ..modules.Property.FlowControllers.BackendVerifyController import BackendVerifyController
from ..modules.Property.FlowControllers.MainLayerCheckController import MainLayerCheckController
from ..modules.Property.FlowControllers.AddBatchRunner import AddBatchRunner
from ..modules.Property.FlowControllers.AttentionDisplayRules import AttentionDisplayRules
from ..utils.mapandproperties.PropertyTableManager import PropertyTableManager, PropertyTableWidget
from ..utils.mapandproperties.PropertyDataLoader import PropertyDataLoader
from ..utils.mapandproperties.property_row_builder import PropertyRowBuilder
from .theme_manager import ThemeManager

from ..constants.button_props import ButtonVariant, ButtonSize
from ..constants.file_paths import QssPaths
from ..languages.language_manager import LanguageManager
from ..languages.translation_keys import TranslationKeys
from ..utils.MapTools.item_selector_tools import PropertiesSelectors
from ..constants.layer_constants import IMPORT_PROPERTY_TAG
from ..utils.MapTools.MapHelpers import MapHelpers, ActiveLayersHelper
from ..utils.MapTools.map_selection_controller import MapSelectionController
from ..constants.cadastral_fields import Katastriyksus
from ..widgets.DateHelpers import DateHelpers

from .LocationFilterWidget import LocationFilterWidget, LocationFilterHelper
from ..Logs.python_fail_logger import PythonFailLogger
from ..ui.window_state.DialogCoordinator import get_dialog_coordinator




class PropertyDialogMode:
    BY_LOCATION = "by_location"
    FROM_MAP = "from_map"


class AddPropertyDialog(QDialog):
    """
    Dialog for adding new properties with a smart list view
    """
    propertyAdded = pyqtSignal(dict)  # Signal emitted when property is added

    def __init__(self, parent=None, *, mode: str = PropertyDialogMode.BY_LOCATION):
        super().__init__(parent)

        self._dialog_mode = mode

        # Always define these so we can use direct `self.` access everywhere.
        self.properties_table_widget = None
        self.properties_table = None

        # Location filter widget + combos (set in _create_ui)
        self.location_filter_widget = None
        self.county_combo = None
        self.municipality_combo = None
        self.city_combo = None
        self._location_filter_helper: Optional[LocationFilterHelper] = None

        # Minimize parent window while this dialog is open (location mode only)
        self._parent_window = None
        self._restore_parent_on_close = False
        try:
            self._parent_window = parent.window() if parent is not None else None
            if self._dialog_mode == PropertyDialogMode.BY_LOCATION:
                parent_window = self._get_safe_parent_window()
                if parent_window is not None and parent_window.isVisible() and not parent_window.isMinimized():
                    coordinator = get_dialog_coordinator(iface)
                    coordinator.enter_map_selection_mode(parent=parent_window)
                    self._restore_parent_on_close = True
        except Exception:
            self._parent_window = None
            self._restore_parent_on_close = False

        self._import_selection_controller: Optional[MapSelectionController] = None
        self.header_label = None

        # Restore parent when dialog closes (accept/reject)
        self.finished.connect(self._on_dialog_finished)

        # Initialize managers
        self.lang_manager = LanguageManager()
        # Initialize helper classes
        self.data_loader = PropertyDataLoader() #in file #PropertyDataLoader.py
        self.table_manager = PropertyTableManager()


        # Set up dialog properties
        if self._dialog_mode == PropertyDialogMode.FROM_MAP:
            self.setWindowTitle(self.lang_manager.translate(TranslationKeys.SELECT_FROM_MAP) or "Add properties from map")
            self.setModal(False)
        else:
            self.setWindowTitle(self.lang_manager.translate(TranslationKeys.PROPERTY_MANAGEMENT))
            self.setModal(True)
        self.setMinimumSize(650, 420)
        self.resize(700, 520)
        self.setSizeGripEnabled(True)

        # Apply theme
        ThemeManager.set_initial_theme(
            self,
            None,  # No theme switch button for popup dialogs
            qss_files=[QssPaths.MAIN, QssPaths.COMBOBOX, QssPaths.BUTTONS]
        )

        self._create_ui()

        # Debounce map updates triggered by rapid table selection changes
        self._map_update_timer = QTimer(self)
        self._map_update_timer.setSingleShot(True)
        self._map_update_timer.setInterval(150)
        self._map_update_timer.timeout.connect(
            lambda: PropertiesSelectors.show_connected_properties_on_map_from_table(self.properties_table, use_shp=True)
        )

        # Location filter controller (location mode only)
        if self._dialog_mode == PropertyDialogMode.BY_LOCATION:
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
        else:
            self._location_filter_helper = None

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
        self._main_layer_cached = None
        self._main_layer_for_verify = None
        self._main_checks_started = False
        self._last_rows_signature = None
        self._progress_update_every = 8
        self._last_progress_total = 0
        self._last_progress_done = -1
        self._rows_process_events_every = 15
        self._missing_from_import: set[str] = set()
        self._archive_backend_plan: dict[str, bool] = {}
        self._archive_map_plan: dict[str, bool] = {}

        # Add batches
        self._add_runner = None
        self._add_in_progress = False
        self._add_mode = None  # "with_checks" | "without_checks"

        # Track whether the table is currently filtered down to attention-only rows.
        self._table_filtered_to_attention = False

        # Add-without-checks button reference
        self.add_without_checks_button = None

        self.show()

        if self._dialog_mode == PropertyDialogMode.FROM_MAP:
            QTimer.singleShot(0, self._start_import_layer_map_selector)
            return

        # Block until done (location mode)
        self.exec_()


    def _on_dialog_finished(self, _result: int) -> None:
        self._stop_attention_checks()
        try:
            if self._import_selection_controller is not None:
                self._import_selection_controller.cancel_selection()
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module="property",
                event="add_property_cancel_selection_failed",
            )
        self._import_selection_controller = None
        if self._location_filter_helper is not None:
            self._location_filter_helper.stop_pending_city_reload()
        import_layer = MapHelpers._get_layer_by_tag(IMPORT_PROPERTY_TAG)
        if import_layer:
            MapHelpers.clear_layer_filter(import_layer)
        # Ensure parent window is restored if dialog is closed directly
        if self._restore_parent_on_close and self._parent_window is not None:
            self._restore_parent_window()

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

        if self._dialog_mode == PropertyDialogMode.FROM_MAP:
            self.header_label = QLabel(
                "Select properties from the map (IMPORT layer).\n"
                "When selection is done, review the table and click Add."
            )
            self.header_label.setWordWrap(True)
            self.header_label.setObjectName("FilterTitle")
            layout.addWidget(self.header_label)

        # Hierarchical selection section (location mode only)
        if self._dialog_mode == PropertyDialogMode.BY_LOCATION:
            self.location_filter_widget = LocationFilterWidget(self.lang_manager)
            layout.addWidget(self.location_filter_widget)

            # Keep legacy attribute names used across this dialog + coordinators.
            self.county_combo = self.location_filter_widget.county_combo
            self.municipality_combo = self.location_filter_widget.municipality_combo
            self.city_combo = self.location_filter_widget.city_combo
        else:
            self.location_filter_widget = None
            self.county_combo = None
            self.municipality_combo = None
            self.city_combo = None

        # Attention toggle row (top-right above table)
        attention_row = QHBoxLayout()
        attention_row.addStretch()
        self.attention_only_checkbox = QCheckBox("Show only attention")
        self.attention_only_checkbox.setChecked(True)
        self.attention_only_checkbox.setObjectName("SelectionInfo")
        attention_row.addWidget(self.attention_only_checkbox)
        layout.addLayout(attention_row)

        self.properties_table_widget, self.properties_table = PropertyTableWidget._create_properties_table()
        layout.addWidget(self.properties_table_widget)
        # Selection info and buttons
        self._create_selection_controls(layout)

    def _create_selection_controls(self, parent_layout):
        """Create selection info and control buttons"""
        # Table controls row (selection info + selection helpers)
        controls_row = QHBoxLayout()
        controls_row.setSpacing(10)
        self.selection_info = QLabel(self.lang_manager.translate(TranslationKeys.SELECTED_PROPERTIES_COUNT))
        self.selection_info.setObjectName("SelectionInfo")
        controls_row.addWidget(self.selection_info)
        controls_row.addStretch()
        self.select_all_btn = QPushButton(self.lang_manager.translate(TranslationKeys.SELECT_ALL))
        self.select_all_btn.setObjectName("SelectAllButton")
        self.select_all_btn.setProperty("btnSize", ButtonSize.SMALL)
        controls_row.addWidget(self.select_all_btn)
        self.clear_selection_btn = QPushButton(self.lang_manager.translate(TranslationKeys.CLEAR_SELECTION))
        self.clear_selection_btn.setObjectName("ClearSelectionButton")
        self.clear_selection_btn.setProperty("btnSize", ButtonSize.SMALL)
        controls_row.addWidget(self.clear_selection_btn)
        self.reselect_from_map_btn = None
        if self._dialog_mode == PropertyDialogMode.FROM_MAP:
            self.reselect_from_map_btn = QPushButton(self.lang_manager.translate(TranslationKeys.RESELECT_FROM_MAP))
            self.reselect_from_map_btn.setObjectName("ConfirmButton")
            self.reselect_from_map_btn.setProperty("variant", ButtonVariant.PRIMARY)
            self.reselect_from_map_btn.setProperty("btnSize", ButtonSize.SMALL)
            controls_row.addWidget(self.reselect_from_map_btn)
        parent_layout.addLayout(controls_row)

        # Progress widget row (checks/add progress)
        progress_row = QHBoxLayout()
        progress_row.setSpacing(8)
        self.check_progress_bar = QProgressBar()
        self.check_progress_bar.setObjectName("CheckProgressBar")
        self.check_progress_bar.setTextVisible(True)
        self.check_progress_bar.setRange(0, 1)
        self.check_progress_bar.setValue(0)
        self.check_progress_bar.setVisible(False)
        progress_row.addWidget(self.check_progress_bar, 1)
        self.add_progress_label = QLabel("")
        self.add_progress_label.setObjectName("AddProgressLabel")
        self.add_progress_label.setVisible(False)
        progress_row.addWidget(self.add_progress_label, 0, Qt.AlignLeft | Qt.AlignVCenter)
        parent_layout.addLayout(progress_row)

        # Footer with main actions
        footer_layout = QHBoxLayout()
        footer_layout.setSpacing(10)
        self.cancel_button = QPushButton(self.lang_manager.translate(TranslationKeys.CANCEL_BUTTON))
        self.cancel_button.setObjectName("CancelButton")
        self.cancel_button.setProperty("btnSize", ButtonSize.SMALL)
        self.cancel_button.setProperty("variant", ButtonVariant.WARNING)
        footer_layout.addWidget(self.cancel_button)

        footer_layout.addStretch()

        self.add_without_checks_button = QPushButton(self.lang_manager.translate(TranslationKeys.ADD_WITHOUT_CHECKS))
        self.add_without_checks_button.setObjectName("AddWithoutChecksButton")
        self.add_without_checks_button.setProperty("variant", ButtonVariant.WARNING)
        self.add_without_checks_button.setProperty("btnSize", ButtonSize.SMALL)
        footer_layout.addWidget(self.add_without_checks_button)

        self.run_checks_button = QPushButton(self.lang_manager.translate(TranslationKeys.RUN_ATTENTION_CHECKS))
        self.run_checks_button.setObjectName("RunChecksButton")
        self.run_checks_button.setProperty("variant", ButtonVariant.PRIMARY)
        self.run_checks_button.setProperty("btnSize", ButtonSize.SMALL)
        footer_layout.addWidget(self.run_checks_button)

        self.add_button = QPushButton(self.lang_manager.translate(TranslationKeys.ADD_SELECTED))
        self.add_button.setObjectName("AddButton")
        self.add_button.setEnabled(False)  # Disabled until properties are selected
        self.add_button.setProperty("variant", ButtonVariant.SUCCESS)
        footer_layout.addWidget(self.add_button)

        parent_layout.addLayout(footer_layout)

        # Add button is gated by selection + checks, so we manage it locally.

    def _setup_connections(self):
        """Set up signal connections"""

        # Dropdown connections are owned by LocationFilterHelper
        if self._location_filter_helper is not None:
            self._location_filter_helper.connect_signals()

        if self.properties_table.selectionModel() is not None:
            self.properties_table.selectionModel().selectionChanged.connect(self._on_table_selection_changed)

        self.attention_only_checkbox.stateChanged.connect(self._on_attention_only_changed)
        self.run_checks_button.clicked.connect(self._on_run_checks_clicked)

    
        # Button connections
        self.select_all_btn.clicked.connect(
            lambda: self.table_manager.select_all(self.properties_table))
        self.clear_selection_btn.clicked.connect(
            lambda: self.table_manager.clear_selection(self.properties_table))
        if self.reselect_from_map_btn is not None:
            self.reselect_from_map_btn.clicked.connect(self._start_import_layer_map_selector)
        self.cancel_button.clicked.connect(self._on_cancel_clicked)
        if self.add_without_checks_button is not None:
            self.add_without_checks_button.clicked.connect(self._on_add_without_checks)
        self.add_button.clicked.connect(self._on_add_clicked)

    # ---------------------------------------------------------------------
    # Map selection (map mode)
    # ---------------------------------------------------------------------

    def _minimize_parent_window_if_safe(self) -> None:
        self._enter_map_selection_mode()

    def _get_safe_parent_window(self):
        w = self._parent_window
        if w is None:
            return None

        try:
            qgis_main = iface.mainWindow() if iface is not None else None
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module="property",
                event="add_property_qgis_main_failed",
            )
            qgis_main = None

        if qgis_main is not None and w is qgis_main:
            return None
        return w

    def _enter_map_selection_mode(self) -> None:
        coordinator = get_dialog_coordinator(iface)
        parent_window = self._get_safe_parent_window()
        coordinator.enter_map_selection_mode(parent=parent_window, dialogs=[self])

    def _exit_map_selection_mode(self, bring_front: bool = True) -> None:
        coordinator = get_dialog_coordinator(iface)
        parent_window = self._get_safe_parent_window()
        coordinator.exit_map_selection_mode(
            parent=parent_window,
            dialogs=[self],
            bring_front=bring_front,
        )

    def _restore_parent_window(self) -> None:
        if not self._restore_parent_on_close:
            return

        w = self._parent_window
        if w is None:
            return

        try:
            coordinator = get_dialog_coordinator(iface)
            parent_window = self._get_safe_parent_window() or w
            coordinator.exit_map_selection_mode(parent=parent_window)
            self._restore_parent_on_close = False
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module="property",
                event="add_property_restore_parent_failed",
            )

    def _start_import_layer_map_selector(self) -> None:
        if self._dialog_mode != PropertyDialogMode.FROM_MAP:
            return

        import_layer = MapHelpers._get_layer_by_tag(IMPORT_PROPERTY_TAG)
        if not import_layer or not import_layer.isValid():
            return

        try:
            if self._import_selection_controller is not None:
                self._import_selection_controller.cancel_selection()
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module="property",
                event="add_property_cancel_selection_failed",
            )
        self._import_selection_controller = None

        try:
            if hasattr(import_layer, "subsetString") and hasattr(import_layer, "setSubsetString"):
                import_layer.setSubsetString("")
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module="property",
                event="add_property_clear_filter_failed",
            )

        self._minimize_parent_window_if_safe()

        controller = MapSelectionController()
        self._import_selection_controller = controller

        def _on_selected(_layer, features):
            self._set_table_from_features(features)
            QTimer.singleShot(0, self._restore_window_after_selection)

        started = controller.start_selection(
            import_layer,
            on_selected=_on_selected,
            selection_tool="rectangle",
            restore_pan=True,
            min_selected=1,
            max_selected=None,
            clear_filter=True,
        )

        if not started:
            self._import_selection_controller = None
            self._exit_map_selection_mode()

    def _restore_window_after_selection(self) -> None:
        self._exit_map_selection_mode()

    def _set_table_from_features(self, feats) -> None:
        features = list(feats or [])

        rows = PropertyRowBuilder.rows_from_features(features, log_prefix="AddPropertyDialog")

        def _after_populate() -> None:
            try:
                self.properties_table.clearSelection()
            except Exception as exc:
                PythonFailLogger.log_exception(
                    exc,
                    module="property",
                    event="add_property_clear_selection_failed",
                )
            try:
                for row_idx in range(PropertyTableManager.row_count(self.properties_table)):
                    tunnus = PropertyTableManager.get_cell_text(
                        self.properties_table,
                        row_idx,
                        PropertyTableWidget._COL_CADASTRAL_ID,
                    )
                    self._set_attention_row(
                        row_idx,
                        tunnus=tunnus,
                        main_causes=[],
                        backend_causes=[],
                        main_done=False,
                        backend_done=False,
                        text="",
                    )
            except Exception as exc:
                PythonFailLogger.log_exception(
                    exc,
                    module="property",
                    event="add_property_init_attention_rows_failed",
                )

        PropertyTableManager.reset_and_populate_properties_table(
            self.properties_table,
            rows,
            after_populate=_after_populate,
        )

        try:
            if PropertyTableManager.row_count(self.properties_table) > 0:
                self.properties_table.selectAll()
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module="property",
                event="add_property_select_all_failed",
            )

        self._after_table_update(self.properties_table)

    def _on_add_without_checks(self) -> None:
        table = self.properties_table
        if table is None:
            return

        if self._add_in_progress:
            return

        try:
            selected_count = len(table.selectionModel().selectedRows() or [])
        except Exception:
            selected_count = 0

        if selected_count <= 0:
            return

        self._stop_attention_checks(clear_attention=False)
        self._checks_running = False
        self._update_add_button_state(selected_count=selected_count)

        self._start_batch_add(table, mode="without_checks")

    def _on_add_clicked(self) -> None:
        self._start_batch_add(self.properties_table, mode="with_checks")

    def _start_batch_add(self, table, *, mode: str) -> None:
        if self._add_in_progress:
            return

        if table is None:
            return

        if mode == "with_checks":
            self._run_missing_cleanup_if_any()

        runner = AddBatchRunner(table, parent=self)
        self._add_runner = runner
        self._add_in_progress = True
        self._add_mode = mode

        runner.progress.connect(self._on_add_progress)
        runner.finished.connect(self._on_add_finished)

        if self.add_progress_label is not None:
            label_prefix = self.lang_manager.translate(TranslationKeys.ADD_UPDATE_PROGRESS_PREFIX)
            if mode == "without_checks":
                label_prefix = self.lang_manager.translate(TranslationKeys.ADD_UPDATE_PROGRESS_PREFIX_NO_CHECKS)
            template = self.lang_manager.translate(TranslationKeys.ADD_UPDATE_PROGRESS_TEMPLATE)
            self.add_progress_label.setVisible(True)
            self.add_progress_label.setText(template.format(prefix=label_prefix, done=0, total=0))

        self._set_add_ui_state(active=True)
        runner.start()

    def _on_cancel_clicked(self) -> None:
        # Always stop attention checks when cancelling so backend lookups don't keep running.
        self._stop_attention_checks(clear_attention=False)

        if self._add_runner is not None:
            try:
                self._add_runner.cancel()
            except Exception as exc:
                PythonFailLogger.log_exception(
                    exc,
                    module="property",
                    event="add_property_cancel_runner_failed",
                )

            self.add_progress_label.setVisible(True)
            self.add_progress_label.setText(self.lang_manager.translate(TranslationKeys.ADD_UPDATE_PROPERTY_DIALOG_CANCELLING))
            return

        self.reject()

    def _on_add_progress(self, done: int, total: int, phase: str, last_tunnus: str) -> None:
        label = self.add_progress_label
        if label is None:
            return

        label.setVisible(True)

        if total <= 0:
            label.clear()
            return

        prefix = self.lang_manager.translate(TranslationKeys.ADD_UPDATE_PROGRESS_PREFIX)
        if self._add_mode == "without_checks":
            prefix = self.lang_manager.translate(TranslationKeys.ADD_UPDATE_PROGRESS_PREFIX_NO_CHECKS)
        template = self.lang_manager.translate(TranslationKeys.ADD_UPDATE_PROGRESS_TEMPLATE)
        label.setText(template.format(prefix=prefix, done=done, total=total))

    def _on_add_finished(self, summary: dict) -> None:
        try:
            canceled = bool(summary.get("canceled")) if isinstance(summary, dict) else False
            done = int(summary.get("done") or 0) if isinstance(summary, dict) else 0
            total = int(summary.get("total") or 0) if isinstance(summary, dict) else 0
        except Exception:
            canceled = False
            done = 0
            total = 0

        if self._add_runner is not None:
            try:
                self._add_runner.deleteLater()
            except Exception as exc:
                PythonFailLogger.log_exception(
                    exc,
                    module="property",
                    event="add_property_runner_delete_failed",
                )
        self._add_runner = None
        self._add_in_progress = False

        if total > 0:
            prefix = self.lang_manager.translate(TranslationKeys.ADD_UPDATE_PROGRESS_FINISHED)
            if self._add_mode == "without_checks":
                prefix = self.lang_manager.translate(TranslationKeys.ADD_UPDATE_PROGRESS_FINISHED_NO_CHECKS)

            if canceled:
                template = self.lang_manager.translate(TranslationKeys.ADD_UPDATE_PROGRESS_CANCELLED_TEMPLATE)
                self.add_progress_label.setText(template.format(prefix=prefix, done=done, total=total))
                # Auto-close dialog after a cancel completes so user doesn't need to click Cancel again.
                try:
                    self.reject()
                    return
                except Exception as exc:
                    PythonFailLogger.log_exception(
                        exc,
                        module="property",
                        event="add_property_reject_failed",
                    )
            else:
                template = self.lang_manager.translate(TranslationKeys.ADD_UPDATE_PROGRESS_TEMPLATE)
                self.add_progress_label.setText(template.format(prefix=prefix, done=done, total=total))
            self.add_progress_label.setVisible(True)
        else:
            self.add_progress_label.setVisible(False)

        self._set_add_ui_state(active=False)
        self._add_mode = None

    def _set_add_ui_state(self, *, active: bool) -> None:
        self._add_in_progress = bool(active)

        # Lock down selection + add buttons while batch is running.
        self.select_all_btn.setEnabled(not active)
        self.clear_selection_btn.setEnabled(not active)
        self.attention_only_checkbox.setEnabled(not active)

        if self.add_without_checks_button is not None:
            self.add_without_checks_button.setEnabled(not active)

        if not active:
            self._update_add_button_state()
        else:
            self.add_button.setEnabled(False)

        if self.add_progress_label is not None:
            self.add_progress_label.setVisible(active or bool(self.add_progress_label.text()))

        self._update_run_checks_button()

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

    def _on_table_selection_changed(self, *_args):
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
                feature = PropertyTableManager.get_cell_data(table, index.row(), 0, role=Qt.UserRole)
                if feature:
                    selected_features.add(feature)
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module="property",
                event="add_property_selection_read_failed",
            )
            selected_features = set()

        count = len(selected_features)
        self.selection_info.setText(
            self.lang_manager.translate(TranslationKeys.SELECTED_COUNT_TEMPLATE).format(count=count)
        )


        self._update_add_button_state(selected_count=count)
        self._update_run_checks_button()

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

        if PropertyTableManager.row_count(table) <= 0:
            self._update_add_button_state()
            self._update_run_checks_button()
            return

        # Keep the selection count correct after programmatic reload/selection.
        self._refresh_selection_info(update_map=False)

        self._update_run_checks_button()

        if self._location_filter_helper is not None:
            self._location_filter_helper.handle_after_table_update()

        # Do not auto-run attention checks; user can trigger manually.
        self._update_run_checks_button()

    def _on_run_checks_clicked(self) -> None:
        self._start_attention_checks(source="manual_button")

    def _stop_attention_checks(self, *, clear_attention: bool = False) -> None:
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
        self._main_layer_lookup = {}
        self._missing_from_import = set()
        self._archive_backend_plan = {}
        self._archive_map_plan = {}

        self._set_check_progress(0, 0)

        self._table_filtered_to_attention = False

        if clear_attention:
            table = self.properties_table
            if table is not None:
                for row_idx in range(PropertyTableManager.row_count(table)):
                    tunnus = self._rows_for_verify_by_row.get(row_idx, ("", ""))[0]
                    self._set_attention_row(row_idx, tunnus=tunnus, main_causes=[], backend_causes=[], main_done=False, backend_done=False, text="")

        self._update_add_button_state()
        self._update_run_checks_button()

    def _resolve_main_layer_cached(self):
        layer = self._main_layer_cached

        try:
            if layer is not None and hasattr(layer, "isValid") and callable(layer.isValid):
                if not layer.isValid():
                    layer = None
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module="property",
                event="add_property_layer_valid_check_failed",
            )
            layer = None

        if layer is None:
            layer = ActiveLayersHelper.resolve_main_property_layer(silent=False)
            self._main_layer_cached = layer

        self._main_layer_for_verify = layer
        return layer

    def _build_main_layer_lookup(self, layer, tunnus_set: set[str]) -> dict:
        lookup = {}
        if not layer or not tunnus_set:
            return lookup
        try:
            for feat in layer.getFeatures():
                val = feat.attribute(Katastriyksus.tunnus)
                key = str(val).strip() if val is not None else ""
                if not key:
                    continue
                if key in tunnus_set and key not in lookup:
                    lookup[key] = feat
                    if len(lookup) == len(tunnus_set):
                        break
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module="property",
                event="add_property_build_lookup_failed",
            )
        return lookup

    def _main_check_batch_params(self, total_rows: int) -> tuple[int, int]:
        if total_rows >= 200:
            return (50, 5)
        if total_rows >= 50:
            return (50, 0)
        return (30, 0)

    def _start_attention_checks(self, *, source: str) -> None:
        table = self.properties_table
        if table is None:
            return

        if self._checks_running:
            return

        date_helpers = DateHelpers()
        rows = []
        rows_for_verify_by_row = {}
        event_counter = 0
        for row_idx in range(PropertyTableManager.row_count(table)):
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
            event_counter += 1
            if event_counter % self._rows_process_events_every == 0:
                QCoreApplication.processEvents()
        if event_counter and event_counter % self._rows_process_events_every != 0:
            QCoreApplication.processEvents()
        rows_signature = tuple((int(r[0]), str(r[1]), str(r[2] or "")) for r in rows)

        if rows_signature == self._last_rows_signature:
            self._checks_running = False
            self._set_check_progress(0, len(rows))
            self._update_add_button_state()
            return

        self._last_rows_signature = rows_signature

        self._stop_attention_checks(clear_attention=False)

        self._rows_for_verify_by_row = rows_for_verify_by_row
        self._total_rows_for_checks = len(rows)
        self._checks_running = bool(rows)

        self._update_run_checks_button()

        self._set_check_progress(0, self._total_rows_for_checks)

        # Gate Add button while checks are running.
        self._update_add_button_state()

        if not rows:
            self._set_check_progress(0, 0)
            return

        # Cache MAIN layer once per run (UI-thread access).
        self._main_layer_for_verify = self._resolve_main_layer_cached()
        tunnus_set = {t for (_row_idx, t, _muudet) in rows}
        self._main_layer_lookup = self._build_main_layer_lookup(self._main_layer_for_verify, tunnus_set)

        batch_size, interval_ms = self._main_check_batch_params(len(rows))

        self._main_check_controller.configure(
            rows_for_verify_by_row=self._rows_for_verify_by_row,
            main_layer=self._main_layer_for_verify,
            checked_rows=self._main_checked_rows,
            main_layer_lookup=self._main_layer_lookup,
        )

        # Kick off a small synchronous batch to surface early results while backend checks spin up.
        initial_rows = list(self._rows_for_verify_by_row.keys())[: min(10, len(self._rows_for_verify_by_row))]
        for r in initial_rows:
            try:
                self._main_check_controller.ensure_row(r)
            except Exception as exc:
                PythonFailLogger.log_exception(
                    exc,
                    module="property",
                    event="add_property_main_check_row_failed",
                )

        self._main_checks_started = True
        self._update_run_checks_button()
        self._main_check_controller.start_pending(
            self._rows_for_verify_by_row.keys(),
            batch_size=batch_size,
            interval_ms=interval_ms,
        )
 
        # Mark in-progress in the Attention column.
        table.setUpdatesEnabled(False)
        for row_idx, tunnus, _import_muudet in rows:
            self._set_attention_row(row_idx, tunnus=tunnus, main_causes=[], backend_causes=[], main_done=False, backend_done=False, text="Võrdlen andmeid...")
        table.setUpdatesEnabled(True)
 
        self._update_check_status_label()

        try:
            self._backend_verify_controller.start(rows, source=source)
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module="property",
                event="add_property_backend_verify_start_failed",
            )
            # If backend verify cannot start, fall back to running MAIN checks only.
            # Mark backend as "done" for all rows so completion is driven by MAIN checks.
            self._backend_checked_rows = set(self._rows_for_verify_by_row.keys())
            remaining = list(self._rows_for_verify_by_row.keys())
            batch_size, interval_ms = self._main_check_batch_params(len(remaining))
            self._main_check_controller.start_pending(remaining, batch_size=batch_size, interval_ms=interval_ms)


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
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module="property",
                event="add_property_remaining_rows_failed",
            )
            remaining = []

        if remaining and not self._main_checks_started:
            self._main_checks_started = True
            batch_size, interval_ms = self._main_check_batch_params(len(remaining))
            self._main_check_controller.start_pending(remaining, batch_size=batch_size, interval_ms=interval_ms)

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
        table = self.properties_table
        if table is None:
            return

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
        tunnus = self._rows_for_verify_by_row.get(row_idx, ("", ""))[0]
        self._set_attention_row(
            row_idx,
            tunnus=tunnus,
            main_causes=main_causes,
            backend_causes=backend_causes,
            main_done=main_done,
            backend_done=backend_done,
            text=text,
        )

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
        self._update_run_checks_button()

        self._set_check_progress(total, total)

        self._missing_from_import = self._compute_missing_from_import_set()

        # Build archive plans per row/tunnus using known causes.
        archive_map_plan: dict[str, bool] = {}
        archive_backend_plan: dict[str, bool] = {}

        for row_idx, (tunnus, _muudet) in self._rows_for_verify_by_row.items():
            t = (tunnus or "").strip()
            in_missing = t in self._missing_from_import

            backend_causes = [c.lower() for c in (self._backend_compare_causes_by_row.get(row_idx) or [])]
            backend_missing = any("missing in backend" in c for c in backend_causes)
            backend_lookup_failed = any("backend lookup failed" in c for c in backend_causes)

            archive_map_plan[t] = bool(in_missing)
            # Only archive in backend if we plan map-archive AND backend exists/was reachable.
            archive_backend_plan[t] = bool(in_missing and not backend_missing and not backend_lookup_failed)

        self._archive_map_plan = archive_map_plan
        self._archive_backend_plan = archive_backend_plan

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

        model = table.model() if table is not None else None
        for row_idx in range(PropertyTableManager.row_count(table) - 1, -1, -1):
            if row_idx not in keep:
                if model is not None:
                    model.removeRow(row_idx)

        table.blockSignals(False)
        table.setUpdatesEnabled(True)

        # Select remaining rows so map highlights only attention items.
        if PropertyTableManager.row_count(table) > 0:
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
        self._update_run_checks_button()

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
            self._last_progress_total = 0
            self._last_progress_done = -1
            return

        if done_i < 0:
            done_i = 0
        if done_i > total_i:
            done_i = total_i

        total_changed = total_i != self._last_progress_total
        done_delta = done_i - self._last_progress_done
        should_update = (
            total_changed
            or done_i in (0, total_i)
            or done_delta >= self._progress_update_every
        )

        if not should_update:
            return

        bar.setVisible(True)
        bar.setRange(0, total_i)
        bar.setValue(done_i)
        bar.setFormat("%v/%m")
        self._last_progress_total = total_i
        self._last_progress_done = done_i


    def _update_add_button_state(self, *, selected_count: Optional[int] = None) -> None:
        table = self.properties_table
        if selected_count is None:
            try:
                selected_count = len(table.selectionModel().selectedRows() or []) if table is not None else 0
            except Exception as exc:
                PythonFailLogger.log_exception(
                    exc,
                    module="property",
                    event="add_property_selected_count_failed",
                )
                selected_count = 0

        can_add = bool(selected_count and int(selected_count) > 0 and not self._checks_running and not self._add_in_progress)
        self.add_button.setEnabled(can_add)

        if self.add_without_checks_button is not None:
            self.add_without_checks_button.setEnabled(bool(selected_count and int(selected_count) > 0 and not self._add_in_progress))

    def _update_run_checks_button(self) -> None:
        if not hasattr(self, "run_checks_button") or self.run_checks_button is None:
            return

        table = self.properties_table
        row_count = PropertyTableManager.row_count(table)
        self.run_checks_button.setEnabled(bool(row_count > 0 and not self._checks_running and not self._add_in_progress))

    # ------------------------------------------------------------------
    # Attention rendering helpers (icons)
    # ------------------------------------------------------------------
    def _set_icon_cell(self, row: int, col: int, state: str, tooltip: str = "") -> None:
        table = self.properties_table
        if table is None:
            return
        try:
            PropertyTableManager.set_status(table, row, col, state=state, tooltip=tooltip)
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module="property",
                event="add_property_set_status_failed",
            )

    def _attention_state(self, causes: list, done: bool) -> str:
        if not done:
            return "pending"
        if causes:
            return "error"
        return "ok"

    def _set_attention_row(self, row_idx: int, *, tunnus: str, main_causes: list, backend_causes: list, main_done: bool, backend_done: bool, text: str) -> None:
        backend_state = self._attention_state(backend_causes, backend_done)
        main_state = self._attention_state(main_causes, main_done)
        self._set_icon_cell(row_idx, PropertyTableWidget._COL_BACKEND_ATTENTION, backend_state, tooltip=text)
        self._set_icon_cell(row_idx, PropertyTableWidget._COL_MAIN_ATTENTION, main_state, tooltip=text)

        # Archive plans per tunnus (set after checks finish).
        t = (tunnus or "").strip()
        archive_backend = self._archive_backend_plan.get(t, False)
        archive_map = self._archive_map_plan.get(t, False)

        backend_causes_lower = [c.lower() for c in (backend_causes or [])]
        backend_missing = any("missing in backend" in c for c in backend_causes_lower)
        backend_lookup_failed = any("backend lookup failed" in c for c in backend_causes_lower)

        if main_done and backend_done:
            if backend_missing or backend_lookup_failed:
                backend_plan_state = "skip"
            else:
                backend_plan_state = "warning" if archive_backend else "ok"
            map_plan_state = "warning" if archive_map else "ok"
        else:
            backend_plan_state = "pending"
            map_plan_state = "pending"

        self._set_icon_cell(row_idx, PropertyTableWidget._COL_ARCHIVE_BACKEND, backend_plan_state)
        self._set_icon_cell(row_idx, PropertyTableWidget._COL_ARCHIVE_MAP, map_plan_state)

    def _compute_missing_from_import_set(self) -> set[str]:
        try:
            import_set = {str(t).strip() for (_r, (t, _m)) in self._rows_for_verify_by_row.items() if str(t).strip()}
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module="property",
                event="add_property_import_set_failed",
            )
            import_set = set()

        main_layer = self._main_layer_for_verify or self._resolve_main_layer_cached()
        if not main_layer or not import_set:
            return set()

        missing: set[str] = set()
        counter = 0
        try:
            for feat in main_layer.getFeatures():
                val = feat.attribute(Katastriyksus.tunnus)
                tunnus = str(val).strip() if val is not None else ""
                if not tunnus:
                    continue
                if tunnus not in import_set:
                    missing.add(tunnus)
                counter += 1
                if counter % 200 == 0:
                    QCoreApplication.processEvents()
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module="property",
                event="add_property_missing_scan_failed",
            )
            return missing
        return missing

    def _run_missing_cleanup_if_any(self) -> None:
        missing = sorted({t for t, flag in self._archive_map_plan.items() if flag})
        if not missing:
            return

        backend_allowed = {t for t, flag in self._archive_backend_plan.items() if flag}

        label = self.add_progress_label
        if label is not None:
            label.setVisible(True)
            label.setText(f"Archiving missing ({len(missing)}) before add...")

        try:
            summary = MainAddPropertiesFlow.archive_missing_from_import(missing, backend_allowed=backend_allowed)
            archived = int(summary.get("archived_backend") or 0)
            moved = int(summary.get("moved_map") or 0)
            errors = summary.get("errors") or []
            if label is not None:
                label.setText(
                    f"Archived missing: backend {archived}/{len(missing)}, moved {moved}" +
                    (" (errors)" if errors else "")
                )
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module="property",
                event="add_property_archive_missing_failed",
            )
            if label is not None:
                label.setText(f"Archiving missing ({len(missing)}) encountered an error")

        # Run once per check cycle.
        self._missing_from_import = set()

