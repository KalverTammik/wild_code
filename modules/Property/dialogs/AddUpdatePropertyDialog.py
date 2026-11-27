from dataclasses import replace
from typing import Optional

from qgis.PyQt.QtCore import Qt, QTimer, QCoreApplication, QSignalBlocker
from qgis.PyQt.QtWidgets import (
    QAbstractItemView,
    QDialog,
    QVBoxLayout,
    QLabel,
    QPushButton,
    QHBoxLayout,
    QCheckBox,
    QSizePolicy,
)

from qgis.utils import iface

from ..FlowControllers.backend_verify_controller import BackendVerifyController
from ..FlowControllers.main_layer_check_controller import MainLayerCheckController
from ..FlowControllers.add_batch_runner import AddBatchRunner
from ....widgets.property_table.PropertyTableManager import PropertyTableManager, PropertyTableWidget
from ....utils.property.PropertyDataLoader import PropertyDataLoader
from ..FlowControllers.property_archive_plan import (
    PropertyArchiveScope,
)
from ..FlowControllers.property_check_run import PropertyCheckRun
from ..FlowControllers.property_dialog_phase import (CancelTarget,
                                                     PropertyDialogMode, PropertyDialogState)
from ....utils.property.property_row_builder import PropertyRowBuilder
from ....ui.theme_manager import ThemeManager
from ....widgets.DelayHelpers.glow_progress_bar import GlowProgressBar

from ....constants.button_props import ButtonVariant, ButtonSize
from ....constants.file_paths import QssPaths
from ....languages.language_manager import LanguageManager
from ....languages.translation_keys import TranslationKeys
from ....utils.MapTools.item_selector_tools import PropertiesSelectors
from ....constants.layer_constants import IMPORT_PROPERTY_TAG
from ....utils.MapTools.MapHelpers import MapHelpers
from ....utils.MapTools.MapSelectionOrchestrator import MapSelectionOrchestrator

from ....widgets.LocationFilterWidget import LocationFilterWidget, LocationFilterHelper
from ....Logs.python_fail_logger import PythonFailLogger
from ....ui.window_state.dialog_helpers import DialogHelpers
from .add_property.add_run_mixin import PropertyAddRunMixin
from .add_property.archive_plan_mixin import PropertyArchivePlanMixin
from .add_property.attention_checks_mixin import PropertyAttentionChecksMixin




class AddPropertyDialog(PropertyAddRunMixin, PropertyAttentionChecksMixin, PropertyArchivePlanMixin, QDialog):
    """Add or update properties from the import layer, by location filter or from the map.

    This class owns the state, the widgets, map selection and cancel routing. Adding,
    checks and the archive plan live in the mixins under ``add_property/``.
    """

    def __init__(self, parent=None, *, mode: str = PropertyDialogMode.BY_LOCATION):
        super().__init__(parent)

        self._dialog_mode = mode

        # Every button rule and every add/cancel routing decision is read off this one
        # object; the private flags below are now views into it, so it must exist before
        # anything assigns to them.
        self._state = PropertyDialogState()

        # Always define these so we can use direct `self.` access everywhere.
        self.properties_table_widget = None
        self.properties_table = None
        self.run_checks_button = None

        # Location filter widget + combos (set in _create_ui)
        self.location_filter_widget = None
        self.county_combo = None
        self.municipality_combo = None
        self.city_combo = None
        self._location_filter_helper: Optional[LocationFilterHelper] = None
        self._archive_scope_snapshot: Optional[PropertyArchiveScope] = None
        self._checks_completed_for_scope = False
        self._deferred_additions = []
        # Decisions found by a check may be added over; decisions left by an import may not.
        self._decisions_from_import = False
        self._add_summary = None
        self._archive_scope_blocked_reason = ""
        self._archive_moved_elsewhere: set[str] = set()
        self._archive_preliminary_missing: set[str] = set()
        self._archive_candidate_settlement: dict[str, str] = {}

        # Minimize parent window while this dialog is open (location mode only)
        self._parent_window = None
        self._restore_parent_on_close = False
        try:
            self._parent_window = parent.window() if parent is not None else None
            if self._dialog_mode == PropertyDialogMode.BY_LOCATION:
                parent_window = self._get_safe_parent_window()
                if parent_window is not None and parent_window.isVisible() and not parent_window.isMinimized():
                    DialogHelpers.enter_map_selection_mode(
                        iface_obj=iface,
                        parent_window=parent_window,
                    )
                    self._restore_parent_on_close = True
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module="property",
                event="add_property_map_selection_start_failed",
            )
            self._parent_window = None
            self._restore_parent_on_close = False

        self._import_selection_orchestrator: Optional[MapSelectionOrchestrator] = None
        self.header_label = None

        # Restore parent when dialog closes (accept/reject)
        self.finished.connect(self._on_dialog_finished)

        # Initialize managers
        self.lang_manager = LanguageManager()
        # Initialize helper classes
        self.data_loader = PropertyDataLoader() #in file #PropertyDataLoader.py
        self.table_manager = PropertyTableManager()

        # Controllers and their state must exist before the UI is built (and before any
        # early return below), because `finished` is already connected to
        # `_on_dialog_finished`, which reaches into them unconditionally.
        self._init_check_controllers_and_state()

        # Set up dialog properties
        if self._dialog_mode == PropertyDialogMode.FROM_MAP:
            self.setWindowTitle(self.lang_manager.translate(TranslationKeys.SELECT_FROM_MAP))
            self.setModal(False)
        else:
            self.setWindowTitle(self.lang_manager.translate(TranslationKeys.PROPERTY_MANAGEMENT_BY_LOCATION_TITLE))
            self.setModal(True)
        self.setMinimumSize(650, 420)
        # Eight 100 px table columns, the scrollbar and the frame margins fit without scrolling.
        self.resize(860, 520)
        self.setSizeGripEnabled(True)

        # Apply theme
        ThemeManager.set_initial_theme(
            self,
            None,  # No theme switch button for popup dialogs
            qss_files=[QssPaths.MAIN, QssPaths.COMBOBOX, QssPaths.BUTTONS]
        )

        # The import layer backs every row shown here; without it there is nothing to
        # build a full dialog around.
        self.property_layer = self.data_loader.property_layer
        if self.property_layer is None:
            self._build_missing_import_layer_ui()
            self.show()
            if self._dialog_mode == PropertyDialogMode.BY_LOCATION:
                self.exec()
            return
        MapHelpers.clear_layer_filter(self.property_layer)

        self._create_ui()

        # Debounce map updates triggered by rapid table selection changes
        self._map_update_timer = QTimer(self)
        self._map_update_timer.setSingleShot(True)
        self._map_update_timer.setInterval(150)
        self._map_update_timer.timeout.connect(
            lambda: PropertiesSelectors.show_features_on_map(
                PropertyTableManager.get_selected_features(self.properties_table), use_shp=True)
        )
        self._map_sync_row_limit = 1500
        self._last_map_sync_skip_count = -1

        # Location filter controller (location mode only)
        if self._dialog_mode == PropertyDialogMode.BY_LOCATION:
            self._location_filter_helper = LocationFilterHelper(
                county_combo=self.county_combo,
                municipality_combo=self.municipality_combo,
                city_combo=self.city_combo,
                properties_table=self.properties_table,
                after_table_update=self._after_table_update,
                stop_checks=lambda clear_attention: self._stop_attention_checks(clear_attention=clear_attention),
                invalidate_archive_scope=self._invalidate_archive_scope,
                # Also refreshes the row count label, so a cleared table never shows the old count.
                update_add_button_state=lambda _count: self._refresh_selection_info(update_map=False),
                stop_map_update=self._map_update_timer.stop,
                status_widget=self.location_filter_widget,
                parent=self,
            )
        else:
            self._location_filter_helper = None

        self._setup_connections()

        self.show()

        if self._dialog_mode == PropertyDialogMode.FROM_MAP:
            QTimer.singleShot(0, self._start_import_layer_map_selector)
            return

        # Block until done (location mode)
        self._location_filter_helper.load_counties(self.property_layer)
        self.exec()

    def _init_check_controllers_and_state(self) -> None:
        """Create attention-check controllers and their state fields.

        Must run before the UI (and before any early return in `__init__`), since
        `_on_dialog_finished` is already connected and reaches into all of this.
        """

        # --- Progressive Attention checks (borrowed from SignalTest patterns) ---
        self._backend_verify_controller = BackendVerifyController(self)
        self._backend_verify_controller.rowResult.connect(self._on_backend_verify_row_result)
        self._backend_verify_controller.waiting.connect(self._on_backend_verify_waiting)
        self._backend_verify_controller.finished.connect(self._on_backend_verify_finished)

        # Backend status of properties missing from the import, read before the archive plan opens.
        self._archive_lookup_controller = BackendVerifyController(self)
        self._archive_lookup_controller.rowResult.connect(self._on_archive_lookup_row)
        self._archive_lookup_controller.waiting.connect(self._on_archive_lookup_waiting)
        self._archive_lookup_controller.finished.connect(self._on_archive_lookup_finished)
        self._archive_lookup = None

        self._main_check_controller = MainLayerCheckController(self)
        self._main_check_controller.rowResult.connect(self._on_main_check_row_result)
        self._main_check_controller.finished.connect(self._on_main_check_finished)

        self._checks_running = False
        # One press of "Run checks" is one PropertyCheckRun: its scope, its per-row
        # results, its MAIN-layer context and its completion accounting. None means
        # no run, and stopping a run is dropping it rather than clearing a field list.
        self._check_run: Optional[PropertyCheckRun] = None
        self._check_run_seq = 0
        # Survives a run on purpose: resolving the MAIN layer is the expensive part.
        self._main_layer_cached = None
        self._progress_update_every = 8
        self._last_progress_total = 0
        self._last_progress_done = -1
        self._rows_process_events_every = 15
        self._missing_from_import: set[str] = set()
        self._archive_backend_plan: dict[str, bool] = {}
        self._archive_map_plan: dict[str, bool] = {}

        # Add batches
        self._add_runner = None
        self._add_errors_view = None
        self._add_in_progress = False
        self._add_mode = None  # one of AddMode, or None between runs
        self._add_last_tunnus = ''
        self._add_last_progress = (0, 0)
        self._add_started_at = None
        self._add_wait_until = 0.0
        self._add_wait_reason = None
        self._add_progress_timer = QTimer(self)
        self._add_progress_timer.setInterval(1000)
        self._add_progress_timer.timeout.connect(self._render_add_progress)

        # Track whether the table is currently filtered down to attention-only rows.
        self._table_filtered_to_attention = False

    def _build_missing_import_layer_ui(self) -> None:
        """Minimal dialog shown when the import layer is not loaded (b1)."""

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        error_label = QLabel(self.lang_manager.translate(TranslationKeys.NO_PROPERTY_LAYER_SELECTED))
        error_label.setObjectName("ErrorLabel")
        error_label.setWordWrap(True)
        layout.addWidget(error_label)

        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()
        close_button = QPushButton(self.lang_manager.translate(TranslationKeys.CLOSE))
        close_button.clicked.connect(self.reject)
        buttons_layout.addWidget(close_button)
        layout.addLayout(buttons_layout)

    # ------------------------------------------------------------------
    # Dialog state: the stored flags are views into `_state`, the counts are read live
    # ------------------------------------------------------------------

    @property
    def _add_in_progress(self) -> bool:
        return self._state.add_in_progress

    @_add_in_progress.setter
    def _add_in_progress(self, value) -> None:
        self._state = replace(self._state, add_in_progress=bool(value))

    @property
    def _checks_running(self) -> bool:
        return self._state.checks_running

    @_checks_running.setter
    def _checks_running(self, value) -> None:
        self._state = replace(self._state, checks_running=bool(value))

    @property
    def _checks_completed_for_scope(self) -> bool:
        return self._state.checks_completed_for_scope

    @_checks_completed_for_scope.setter
    def _checks_completed_for_scope(self, value) -> None:
        self._state = replace(self._state, checks_completed_for_scope=bool(value))

    @property
    def _decisions_from_import(self) -> bool:
        return self._state.decisions_from_import

    @_decisions_from_import.setter
    def _decisions_from_import(self, value) -> None:
        self._state = replace(self._state, decisions_from_import=bool(value))

    def _phase_state(self, *, selected_count: Optional[int] = None) -> PropertyDialogState:
        """The stored flags plus everything that has to be counted at decision time.

        The deferred list is mutated in place elsewhere and the add runner is cleared a
        moment after its flag, so neither may be cached into `_state`.
        """

        if selected_count is None:
            selected_count = self._current_target_count()
        return replace(
            self._state,
            deferred_count=len(self._deferred_additions),
            archive_lookup_active=self._archive_lookup is not None,
            has_add_runner=self._add_runner is not None,
            row_count=PropertyTableManager.row_count(self.properties_table),
            selected_count=int(selected_count or 0),
        )

    def _on_dialog_finished(self, _result: int) -> None:
        self._add_progress_timer.stop()
        if self._add_runner is not None:
            self._add_runner.cancel()
        self._archive_lookup = None
        self._archive_lookup_controller.stop()
        # The minimal missing-import-layer dialog never built the check UI, so the full
        # cleanup below (which touches those widgets) would fail; only the controllers
        # need stopping in that case.
        if self.properties_table is not None:
            self._stop_attention_checks()
        else:
            self._stop_check_controllers()
        try:
            if self._import_selection_orchestrator is not None:
                self._import_selection_orchestrator.cancel()
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module="property",
                event="add_property_cancel_selection_failed",
            )
        self._import_selection_orchestrator = None
        if self._location_filter_helper is not None:
            self._location_filter_helper.close()
        import_layer = MapHelpers.get_layer_by_tag(IMPORT_PROPERTY_TAG)
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

        if self._dialog_mode == PropertyDialogMode.FROM_MAP:
            self.header_label = QLabel(
                self.lang_manager.translate(TranslationKeys.SELECT_PROPERTIES_MAP_INSTRUCTION)
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
        self.attention_only_checkbox = QCheckBox(
            self.lang_manager.translate(TranslationKeys.SHOW_ONLY_ATTENTION)
        )
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
        self.selection_info = QLabel("")
        self.selection_info.setObjectName("SelectionInfo")
        controls_row.addWidget(self.selection_info)
        controls_row.addStretch()
        # Location mode always adds every row in the table, so it offers no row selection.
        self.select_all_btn = None
        self.clear_selection_btn = None
        self.reselect_from_map_btn = None
        if self._dialog_mode != PropertyDialogMode.FROM_MAP:
            self.properties_table.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
            self.selection_info.setText(
                self.lang_manager.translate(TranslationKeys.PROPERTY_TABLE_COUNT_TEMPLATE).format(count=0))
        else:
            self.selection_info.setText(self.lang_manager.translate(TranslationKeys.SELECTED_PROPERTIES_COUNT))
            self.select_all_btn = QPushButton(self.lang_manager.translate(TranslationKeys.SELECT_ALL))
            self.select_all_btn.setObjectName("SelectAllButton")
            self.select_all_btn.setProperty("btnSize", ButtonSize.SMALL)
            controls_row.addWidget(self.select_all_btn)
            self.clear_selection_btn = QPushButton(self.lang_manager.translate(TranslationKeys.CLEAR_SELECTION))
            self.clear_selection_btn.setObjectName("ClearSelectionButton")
            self.clear_selection_btn.setProperty("btnSize", ButtonSize.SMALL)
            controls_row.addWidget(self.clear_selection_btn)
            self.reselect_from_map_btn = QPushButton(self.lang_manager.translate(TranslationKeys.RESELECT_FROM_MAP))
            self.reselect_from_map_btn.setObjectName("ConfirmButton")
            self.reselect_from_map_btn.setProperty("variant", ButtonVariant.PRIMARY)
            self.reselect_from_map_btn.setProperty("btnSize", ButtonSize.SMALL)
            controls_row.addWidget(self.reselect_from_map_btn)
        parent_layout.addLayout(controls_row)

        # Give wrapped status text the full width and its required height.
        self.check_progress_bar = GlowProgressBar()
        self.check_progress_bar.setObjectName("CheckProgressBar")
        self.check_progress_bar.setTextVisible(True)
        self.check_progress_bar.setRange(0, 1)
        self.check_progress_bar.setValue(0)
        self.check_progress_bar.setVisible(False)
        parent_layout.addWidget(self.check_progress_bar)
        self.add_progress_label = QLabel("")
        self.add_progress_label.setObjectName("AddProgressLabel")
        self.add_progress_label.setWordWrap(True)
        self.add_progress_label.setTextFormat(Qt.TextFormat.PlainText)
        self.add_progress_label.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)
        self.add_progress_label.setVisible(False)
        parent_layout.addWidget(self.add_progress_label)
        self.add_progress_bar = GlowProgressBar()
        self.add_progress_bar.setObjectName("AddProgressBar")
        self.add_progress_bar.setRange(0, 1)
        self.add_progress_bar.setValue(0)
        self.add_progress_bar.setFormat("%p%")
        self.add_progress_bar.hide()
        parent_layout.addWidget(self.add_progress_bar)
        self.add_detail_label = QLabel("")
        self.add_detail_label.setWordWrap(True)
        self.add_detail_label.setTextFormat(Qt.TextFormat.PlainText)
        self.add_detail_label.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)
        self.add_detail_label.hide()
        parent_layout.addWidget(self.add_detail_label)
        self.review_additions_button = QPushButton(self.lang_manager.translate(
            TranslationKeys.PROPERTY_IMPORT_REVIEW).format(count=0))
        self.review_additions_button.setAutoDefault(False)
        self.review_additions_button.hide()
        self.review_additions_button.clicked.connect(self._on_review_additions)
        parent_layout.addWidget(self.review_additions_button)

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


        # Button connections; selection buttons exist only in map mode.
        if self._dialog_mode == PropertyDialogMode.FROM_MAP:
            self.select_all_btn.clicked.connect(
                lambda: self.table_manager.select_all(self.properties_table))
            self.clear_selection_btn.clicked.connect(
                lambda: self.table_manager.clear_selection(self.properties_table))
            self.reselect_from_map_btn.clicked.connect(self._start_import_layer_map_selector)
        self.cancel_button.clicked.connect(self._on_cancel_clicked)
        if self.add_without_checks_button is not None:
            self.add_without_checks_button.clicked.connect(self._on_add_without_checks)
        self.add_button.clicked.connect(self._on_add_clicked)

    # ---------------------------------------------------------------------
    # Map selection (map mode)
    # ---------------------------------------------------------------------

    def _get_safe_parent_window(self):
        return DialogHelpers.resolve_safe_parent_window(
            self._parent_window,
            iface_obj=iface,
            module="property",
            qgis_main_error_event="add_property_qgis_main_failed",
        )

    def _enter_map_selection_mode(self) -> None:
        parent_window = self._get_safe_parent_window()
        DialogHelpers.enter_map_selection_mode(
            iface_obj=iface,
            parent_window=parent_window,
            dialogs=[self],
        )

    def _exit_map_selection_mode(self, bring_front: bool = True) -> None:
        parent_window = self._get_safe_parent_window()
        DialogHelpers.exit_map_selection_mode(
            iface_obj=iface,
            parent_window=parent_window,
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
            parent_window = self._get_safe_parent_window() or w
            DialogHelpers.exit_map_selection_mode(
                iface_obj=iface,
                parent_window=parent_window,
            )
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

        import_layer = MapHelpers.get_layer_by_tag(IMPORT_PROPERTY_TAG)
        if not import_layer or not import_layer.isValid():
            return

        try:
            if self._import_selection_orchestrator is not None:
                self._import_selection_orchestrator.cancel()
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module="property",
                event="add_property_cancel_selection_failed",
            )
        self._import_selection_orchestrator = None

        try:
            import_layer.setSubsetString("")
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module="property",
                event="add_property_clear_filter_failed",
            )

        orchestrator = MapSelectionOrchestrator(parent=self)
        self._import_selection_orchestrator = orchestrator

        def _on_selected(_layer, features):
            self._set_table_from_features(features)
            QTimer.singleShot(0, self._exit_map_selection_mode)

        started = orchestrator.start_selection_for_layer(
            import_layer,
            on_selected=_on_selected,
            selection_tool="rectangle",
            restore_pan=True,
            min_selected=1,
            max_selected=None,
            clear_filter=True,
            keep_existing_selection=False,
            lightweight_fetch=True,
            fetch_geometry=False,
            before_start=self._enter_map_selection_mode,
            on_abandoned=self._exit_map_selection_mode,
        )

        if not started:
            self._import_selection_orchestrator = None
            self._exit_map_selection_mode()

    def _set_table_from_features(self, feats) -> None:
        features = list(feats or [])
        feature_count = len(features)

        rows = []
        for idx, feature in enumerate(features, start=1):
            rows.append(PropertyRowBuilder.row_from_feature(feature, log_prefix="AddPropertyDialog"))
            if idx % 250 == 0:
                QCoreApplication.processEvents()
        if feature_count and feature_count % 250 != 0:
            QCoreApplication.processEvents()

        PropertyTableManager.reset_and_populate_properties_table(
            self.properties_table,
            rows,
            after_populate=None,
        )

        try:
            if PropertyTableManager.row_count(self.properties_table) > 0:
                selection_model = self.properties_table.selectionModel()
                blocker = QSignalBlocker(selection_model) if selection_model is not None else None
                self.properties_table.selectAll()
                if blocker is not None:
                    blocker.unblock()
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module="property",
                event="add_property_select_all_failed",
            )

        self._after_table_update(self.properties_table)

    def reject(self) -> None:
        if isinstance(self._add_runner, AddBatchRunner) and self._add_in_progress:
            self._on_cancel_clicked()
            return
        super().reject()

    def closeEvent(self, event) -> None:
        if isinstance(self._add_runner, AddBatchRunner) and self._add_in_progress:
            event.ignore()
            self._on_cancel_clicked()
            return
        super().closeEvent(event)

    def _on_cancel_clicked(self) -> None:
        # Running work is cancelled in place, like an add; only an idle dialog closes.
        target = self._phase_state().cancel_target
        if target == CancelTarget.ARCHIVE_LOOKUP:
            self._cancel_archive_lookup()
            return
        if target == CancelTarget.CHECKS:
            self._cancel_attention_checks()
            return

        # Always stop attention checks when cancelling so backend lookups don't keep running.
        self._stop_attention_checks(clear_attention=False)

        if target == CancelTarget.ADD_RUN:
            self._add_wait_reason = 'cancelling'
            self._render_add_progress()
            try:
                self._add_runner.cancel()
            except Exception as exc:
                PythonFailLogger.log_exception(
                    exc,
                    module="property",
                    event="add_property_cancel_runner_failed",
                )

            return

        self.reject()

    def _on_table_selection_changed(self, *_args):
        self._refresh_selection_info(update_map=True)

    def _use_filtered_row_scope(self) -> bool:
        return self._dialog_mode == PropertyDialogMode.BY_LOCATION

    def _current_target_count(self) -> int:
        table = self.properties_table
        if table is None:
            return 0

        if self._use_filtered_row_scope():
            return PropertyTableManager.visible_row_count(table)

        try:
            return len(table.selectionModel().selectedRows() or [])
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module="property",
                event="add_property_selected_count_failed",
            )
            return 0

    def _refresh_selection_info(self, *, update_map: bool) -> int:
        """Refresh selected-count label.

        During table reloads (e.g. city filter) the table may block signals, so
        `itemSelectionChanged` won't fire even if rows get selected programmatically.
        """

        table = self.properties_table
        if table is None:
            return 0

        if self._use_filtered_row_scope():
            count = PropertyTableManager.visible_row_count(table)
            self.selection_info.setText(
                self.lang_manager.translate(TranslationKeys.PROPERTY_TABLE_COUNT_TEMPLATE).format(count=count)
            )
            self._update_add_button_state(selected_count=count)
            self._update_run_checks_button()
            self._map_update_timer.stop()
            return count

        selected_features = set()
        try:
            for index in table.selectionModel().selectedRows():
                feature = PropertyTableManager.get_cell_data(table, index.row(), 0, role=Qt.ItemDataRole.UserRole)
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
            if count <= self._map_sync_row_limit:
                self._last_map_sync_skip_count = -1
                self._map_update_timer.start()
            else:
                self._map_update_timer.stop()
                if self._last_map_sync_skip_count != count:
                    self._last_map_sync_skip_count = count

        return count

    # ---------------------------------------------------------------------
    # Shared by the mixins: table scope, detail label and button state
    # ---------------------------------------------------------------------

    def _hide_detail_label(self) -> None:
        self.add_detail_label.clear()
        self.add_detail_label.hide()

    def _after_table_update(self, _table) -> None:
        """Publish the completed table's scope after a location or map-selection load."""

        # Newly populated rows already have pending attention states.
        self._stop_attention_checks(clear_attention=False)
        self._capture_archive_scope_snapshot(load_succeeded=True)

        if self.properties_table is None:
            return

        # Keep the count and buttons correct after programmatic reloads, including an empty
        # result. Attention checks are never started automatically.
        self._refresh_selection_info(update_map=False)

    def _update_add_button_state(self, *, selected_count: Optional[int] = None) -> None:
        state = self._phase_state(selected_count=selected_count)
        self.add_button.setEnabled(state.can_add_with_checks)

        if self.add_without_checks_button is not None:
            self.add_without_checks_button.setEnabled(state.can_add_without_checks)

    def _update_run_checks_button(self) -> None:
        if self.run_checks_button is None:
            return

        self.run_checks_button.setEnabled(self._phase_state().can_run_checks)
