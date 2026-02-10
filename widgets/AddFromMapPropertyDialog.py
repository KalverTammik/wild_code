from typing import Optional

from qgis.utils import iface

from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QColor, QBrush
from PyQt5.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QLabel,
    QPushButton,
    QHBoxLayout,
    QCheckBox,
    QProgressBar,
    QTableWidgetItem,
)

from ..constants.button_props import ButtonVariant, ButtonSize
from ..constants.cadastral_fields import Katastriyksus
from ..constants.file_paths import QssPaths
from ..constants.layer_constants import IMPORT_PROPERTY_TAG
from ..languages.language_manager import LanguageManager
from ..languages.translation_keys import TranslationKeys
from ..modules.Property.FlowControllers.AttentionDisplayRules import AttentionDisplayRules
from ..modules.Property.FlowControllers.BackendVerifyController import BackendVerifyController
from ..modules.Property.FlowControllers.MainAddProperties import MainAddPropertiesFlow
from ..modules.Property.FlowControllers.MainLayerCheckController import MainLayerCheckController
from qgis.core import QgsFeatureRequest
from ..utils.MapTools.MapHelpers import MapHelpers, ActiveLayersHelper
from ..utils.MapTools.map_selection_controller import MapSelectionController
from ..utils.mapandproperties.PropertyTableManager import PropertyTableManager, PropertyTableWidget
from ..utils.mapandproperties.property_row_builder import PropertyRowBuilder
from ..widgets.DateHelpers import DateHelpers
from .theme_manager import ThemeManager
from ..Logs.python_fail_logger import PythonFailLogger
from ..ui.window_state.DialogCoordinator import get_dialog_coordinator




class AddFromMapPropertyDialog(QDialog):
    """Add properties by selecting features on the map."""

    def __init__(self, parent=None):
        super().__init__(parent)

        self.lang_manager = LanguageManager()

        # If opened from plugin UI, minimize that window during map selection (but never minimize QGIS itself).
        self._parent_window = None
        self._restore_parent_on_close = False
        try:
            self._parent_window = parent.window() if parent is not None else None
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module="property",
                event="add_from_map_parent_window_failed",
            )
            self._parent_window = None

        self._import_selection_controller: Optional[MapSelectionController] = None

        self.properties_table_widget = None
        self.properties_table = None

        # Attention checks + status
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
        self._main_layer_lookup = {}
        self._main_layer_lookup = {}
        self._table_filtered_to_attention = False
        self._archive_backend_plan: dict[str, bool] = {}
        self._archive_map_plan: dict[str, bool] = {}

        self._checks_start_timer = QTimer(self)
        self._checks_start_timer.setSingleShot(True)
        self._checks_start_timer.setInterval(250)
        self._checks_start_timer.timeout.connect(lambda: self._start_attention_checks(source="add_from_map_dialog"))

        self._map_update_timer = QTimer(self)
        self._map_update_timer.setSingleShot(True)
        self._map_update_timer.setInterval(150)

        self.setWindowTitle(self.lang_manager.translate(TranslationKeys.PROPERTY_MANAGEMENT))
        self.setModal(False)
        self.setMinimumSize(770, 540)
        """Legacy wrapper retained for compatibility.
        
        Use `AddPropertyDialog` with `PropertyDialogMode.FROM_MAP`.
        """
        from .AddUpdatePropertyDialog import AddPropertyDialog, PropertyDialogMode
        super().__init__(parent, mode=PropertyDialogMode.FROM_MAP)

        w = self._parent_window
        if w is None:
            return

        try:
            coordinator = get_dialog_coordinator(iface)
            coordinator.bring_to_front(w)
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module="property",
                event="add_from_map_restore_window_failed",
            )


    # ---------------------------------------------------------------------
    # UI
    # ---------------------------------------------------------------------

    def _create_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        header = QLabel(
            "Select properties from the map (IMPORT layer).\n"
            "When selection is done, review the table and click Add."
        )
        header.setWordWrap(True)
        header.setObjectName("FilterTitle")
        layout.addWidget(header)

        # Attention toggle row (top-right above table)
        attention_row = QHBoxLayout()
        attention_row.addStretch()
        self.attention_only_checkbox = QCheckBox("Show only attention")
        self.attention_only_checkbox.setChecked(True)
        self.attention_only_checkbox.setObjectName("SelectionInfo")
        attention_row.addWidget(self.attention_only_checkbox)
        layout.addLayout(attention_row)

        self.properties_table_widget, self.properties_table = PropertyTableWidget._create_properties_table()
        layout.addWidget(self.properties_table_widget, 1)

        # Table controls row (counter + selection helpers)
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
        self._btn_reselect = QPushButton(self.lang_manager.translate(TranslationKeys.RESELECT_FROM_MAP))
        self._btn_reselect.setObjectName("ConfirmButton")
        self._btn_reselect.setProperty("variant", ButtonVariant.PRIMARY)
        controls_row.addWidget(self._btn_reselect)
        layout.addLayout(controls_row)

        # Progress widget row
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
        layout.addLayout(progress_row)

        # Footer with main actions
        footer_layout = QHBoxLayout()
        footer_layout.setSpacing(10)
        self.cancel_button = QPushButton(self.lang_manager.translate(TranslationKeys.CANCEL_BUTTON))
        self.cancel_button.setObjectName("CancelButton")
        footer_layout.addWidget(self.cancel_button)

        footer_layout.addStretch(1)

        self.add_button = QPushButton(self.lang_manager.translate(TranslationKeys.ADD_SELECTED))
        self.add_button.setObjectName("AddButton")
        self.add_button.setEnabled(False)
        self.add_button.setProperty("variant", ButtonVariant.PRIMARY)
        footer_layout.addWidget(self.add_button)

        layout.addLayout(footer_layout)

    def _setup_connections(self):
        self.properties_table.itemSelectionChanged.connect(self._on_table_selection_changed)
        self.attention_only_checkbox.stateChanged.connect(self._on_attention_only_changed)

        self.select_all_btn.clicked.connect(lambda: PropertyTableManager.select_all(self.properties_table))
        self.clear_selection_btn.clicked.connect(lambda: PropertyTableManager.clear_selection(self.properties_table))
        self._btn_reselect.clicked.connect(self._start_import_layer_map_selector)

        self.cancel_button.clicked.connect(self.reject)
        self.add_button.clicked.connect(lambda: self._run_add_flow_from_table())

    # ---------------------------------------------------------------------
    # Selection
    # ---------------------------------------------------------------------

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
                event="add_from_map_qgis_main_failed",
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

    def _start_import_layer_map_selector(self) -> None:
        import_layer = MapHelpers._get_layer_by_tag(IMPORT_PROPERTY_TAG)
        if not import_layer or not import_layer.isValid():
            return

        # Cancel any previous selection session
        try:
            if self._import_selection_controller is not None:
                self._import_selection_controller.cancel_selection()
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module="property",
                event="add_from_map_cancel_selection_failed",
            )
        self._import_selection_controller = None

        # Clear any subset string so selection behaves predictably.
        # (MapSelectionController can do this too, but import layer might be filtered elsewhere.)
        try:
            if hasattr(import_layer, "subsetString") and hasattr(import_layer, "setSubsetString"):
                import_layer.setSubsetString("")
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module="property",
                event="add_from_map_clear_filter_failed",
            )

        # Minimize plugin window + this dialog so user can see the map.
        self._enter_map_selection_mode()

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

        rows = PropertyRowBuilder.rows_from_features(features, log_prefix="AddFromMapPropertyDialog")

        def _after_populate() -> None:
            try:
                self.properties_table.clearSelection()
            except Exception as exc:
                PythonFailLogger.log_exception(
                    exc,
                    module="property",
                    event="add_from_map_clear_selection_failed",
                )
            try:
                for row_idx in range(self.properties_table.rowCount()):
                    tunnus = PropertyTableManager.get_cell_text(self.properties_table, row_idx, PropertyTableWidget._COL_CADASTRAL_ID)
                    self._set_attention_row(row_idx, tunnus=tunnus, main_causes=[], backend_causes=[], main_done=False, backend_done=False, text="")
            except Exception as exc:
                PythonFailLogger.log_exception(
                    exc,
                    module="property",
                    event="add_from_map_init_attention_rows_failed",
                )

        PropertyTableManager.reset_and_populate_properties_table(
            self.properties_table,
            rows,
            after_populate=_after_populate,
        )

        # Default: select all rows so user can just hit Add.
        try:
            if self.properties_table.rowCount() > 0:
                self.properties_table.selectAll()
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module="property",
                event="add_from_map_select_all_failed",
            )

        self._stop_attention_checks(clear_attention=True)
        self._refresh_selection_info(update_map=False)

        # Start checks after a short quiet period (same as AddPropertyDialog).
        try:
            self._checks_start_timer.start()
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module="property",
                event="add_from_map_start_checks_timer_failed",
            )
            self._start_attention_checks(source="add_from_map_dialog")

    # ---------------------------------------------------------------------
    # Add flow
    # ---------------------------------------------------------------------

    def _run_add_flow_from_table(self) -> None:
        if self.properties_table is None:
            return

        self._run_missing_cleanup_if_any()

        MainAddPropertiesFlow.start_adding_properties(self.properties_table)
        self.accept()

    # ---------------------------------------------------------------------
    # Selection info / gating
    # ---------------------------------------------------------------------

    def _on_table_selection_changed(self):
        self._refresh_selection_info(update_map=False)

    def _refresh_selection_info(self, *, update_map: bool) -> int:
        table = self.properties_table
        if table is None:
            return 0

        selected_features = set()
        try:
            for index in table.selectionModel().selectedRows():
                item = table.item(index.row(), 0)
                if item is None:
                    continue
                feature = item.data(Qt.UserRole)
                if feature:
                    selected_features.add(feature)
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module="property",
                event="add_from_map_selection_read_failed",
            )
            selected_features = set()

        count = len(selected_features)
        try:
            self.selection_info.setText(
                self.lang_manager.translate(TranslationKeys.SELECTED_COUNT_TEMPLATE).format(count=count)
            )
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module="property",
                event="add_from_map_update_selection_label_failed",
            )

        self._update_add_button_state(selected_count=count)

        if update_map:
            self._map_update_timer.start()

        return count

    def _update_add_button_state(self, *, selected_count: Optional[int] = None) -> None:
        if selected_count is None:
            try:
                selected_count = len(self.properties_table.selectionModel().selectedRows() or [])
            except Exception:
                selected_count = 0
        can_add = bool(selected_count and int(selected_count) > 0 and not self._checks_running)
        try:
            self.add_button.setEnabled(can_add)
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module="property",
                event="add_from_map_set_add_button_failed",
            )

    # ---------------------------------------------------------------------
    # Attention checks (copied from AddPropertyDialog with minimal changes)
    # ---------------------------------------------------------------------

    def _on_attention_only_changed(self, _state: int) -> None:
        checked = bool(self.attention_only_checkbox.isChecked())

        if not checked:
            if self._table_filtered_to_attention:
                self._table_filtered_to_attention = False
            return

        if not self._checks_running:
            self._apply_attention_only_filter_if_ready()

    def _stop_attention_checks(self, *, clear_attention: bool = False) -> None:
        try:
            self._checks_start_timer.stop()
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module="property",
                event="add_from_map_stop_checks_timer_failed",
            )

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
        self._archive_backend_plan = {}
        self._archive_map_plan = {}

        if clear_attention:
            table = self.properties_table
            if table is not None:
                for row_idx in range(table.rowCount()):
                    tunnus = PropertyTableManager.get_cell_text(table, row_idx, PropertyTableWidget._COL_CADASTRAL_ID)
                    self._set_attention_row(row_idx, tunnus=tunnus, main_causes=[], backend_causes=[], main_done=False, backend_done=False, text="")

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
        self._update_add_button_state()

        if not rows:
            self._set_check_progress(0, 0)
            return

        self._main_layer_for_verify = ActiveLayersHelper.resolve_main_property_layer(silent=False)

        tunnus_set = {t for (_row_idx, t, _muudet) in rows}
        self._main_layer_lookup = self._build_main_layer_lookup(self._main_layer_for_verify, tunnus_set)

        self._main_check_controller.configure(
            rows_for_verify_by_row=self._rows_for_verify_by_row,
            main_layer=self._main_layer_for_verify,
            checked_rows=self._main_checked_rows,
            main_layer_lookup=self._main_layer_lookup,
        )

        table.setUpdatesEnabled(False)
        for row_idx, tunnus, _import_muudet in rows:
            self._set_attention_row(row_idx, tunnus=tunnus, main_causes=[], backend_causes=[], main_done=False, backend_done=False, text="Võrdlen andmeid...")
        table.setUpdatesEnabled(True)

        try:
            self._backend_verify_controller.start(rows, source=source)
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module="property",
                event="add_from_map_backend_verify_start_failed",
            )
            self._backend_checked_rows = set(self._rows_for_verify_by_row.keys())
            remaining = list(self._rows_for_verify_by_row.keys())
            self._main_check_controller.start_pending(remaining, batch_size=50, interval_ms=0)

    def _build_main_layer_lookup(self, layer, tunnus_set: set[str]) -> dict:
        lookup = {}
        if not layer or not tunnus_set:
            return lookup
        try:
            req = QgsFeatureRequest().setSubsetOfAttributes([Katastriyksus.tunnus], layer.fields())
            for feat in layer.getFeatures(req):
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
                event="add_from_map_build_lookup_failed",
            )
        return lookup

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

        self._main_check_controller.ensure_row(row_idx)

        self._update_row_attention_display(row_idx)
        self._update_check_status_label()

    def _on_backend_verify_finished(self, _summary: dict) -> None:
        try:
            remaining = [r for r in self._rows_for_verify_by_row.keys() if r not in self._main_checked_rows]
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module="property",
                event="add_from_map_remaining_rows_failed",
            )
            remaining = []

        if remaining:
            self._main_check_controller.start_pending(remaining, batch_size=50, interval_ms=0)

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
        self._set_attention_row(
            row_idx,
            tunnus=self._rows_for_verify_by_row.get(row_idx, ("", ""))[0],
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

        done_rows = 0
        for row_idx in self._rows_for_verify_by_row.keys():
            if row_idx in self._backend_checked_rows and row_idx in self._main_checked_rows:
                done_rows += 1

        if done_rows < total:
            return

        self._checks_running = False
        self._update_add_button_state()

        self._set_check_progress(total, total)

        # Build archive plans: map archive for items missing from main layer; backend archive only if backend exists/lookup succeeded.
        archive_map_plan: dict[str, bool] = {}
        archive_backend_plan: dict[str, bool] = {}

        missing_set = set()
        try:
            main_layer = ActiveLayersHelper.resolve_main_property_layer(silent=True)
            tunnus_set = {t for (_row_idx, t, _m) in self._rows_for_verify_by_row.items()}
            if main_layer:
                for feat in main_layer.getFeatures():
                    val = feat.attribute(Katastriyksus.tunnus)
                    t = str(val).strip() if val is not None else ""
                    if not t:
                        continue
                    if t not in tunnus_set:
                        missing_set.add(t)
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module="property",
                event="add_from_map_missing_scan_failed",
            )
            missing_set = set()

        for row_idx, (tunnus, _muudet) in self._rows_for_verify_by_row.items():
            t = (tunnus or "").strip()
            in_missing = t in missing_set
            backend_causes = [c.lower() for c in (self._backend_compare_causes_by_row.get(row_idx) or [])]
            backend_missing = any("missing in backend" in c for c in backend_causes)
            backend_lookup_failed = any("backend lookup failed" in c for c in backend_causes)
            archive_map_plan[t] = bool(in_missing)
            archive_backend_plan[t] = bool(in_missing and not backend_missing and not backend_lookup_failed)

        self._archive_map_plan = archive_map_plan
        self._archive_backend_plan = archive_backend_plan

        for row_idx in self._rows_for_verify_by_row.keys():
            self._update_row_attention_display(row_idx)

        # Hide the progress bar once finished.
        self._set_check_progress(0, 0)

        self._apply_attention_only_filter_if_ready()

    def _run_missing_cleanup_if_any(self) -> None:
        missing = sorted({t for t, flag in self._archive_map_plan.items() if flag})
        if not missing:
            return

        backend_allowed = {t for t, flag in self._archive_backend_plan.items() if flag}

        try:
            MainAddPropertiesFlow.archive_missing_from_import(missing, backend_allowed=backend_allowed)
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module="property",
                event="add_from_map_archive_missing_failed",
            )

    def _apply_attention_only_filter_if_ready(self) -> None:
        if not bool(self.attention_only_checkbox.isChecked()):
            return

        if int(self._total_rows_for_checks or 0) <= 0:
            return

        attention_rows = self._get_attention_row_indices()
        if not attention_rows:
            return

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

        table.setUpdatesEnabled(False)
        table.blockSignals(True)
        table.clearSelection()

        for row_idx in range(table.rowCount() - 1, -1, -1):
            if row_idx not in keep:
                table.removeRow(row_idx)

        table.blockSignals(False)
        table.setUpdatesEnabled(True)

        if table.rowCount() > 0:
            table.selectAll()

        import_layer = MapHelpers._get_layer_by_tag(IMPORT_PROPERTY_TAG)
        if import_layer is not None:
            import_layer.removeSelection()

        self._table_filtered_to_attention = True

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

    # ------------------------------------------------------------------
    # Attention rendering helpers (icons + text)
    # ------------------------------------------------------------------
    def _set_icon_cell(self, row: int, col: int, symbol: str, color_name: str) -> None:
        table = self.properties_table
        if table is None:
            return
        try:
            item = table.item(row, col)
            if item is None:
                item = QTableWidgetItem("")
                table.setItem(row, col, item)
            item.setText(symbol)
            item.setTextAlignment(Qt.AlignCenter)
            if color_name:
                item.setData(Qt.ForegroundRole, QBrush(QColor(color_name)))
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module="property",
                event="add_from_map_set_icon_failed",
            )

    def _attention_symbol(self, causes: list, done: bool) -> tuple[str, str]:
        if not done:
            return "…", "gray"
        if causes:
            return "✗", "firebrick"
        return "✓", "darkgreen"

    def _set_attention_row(self, row_idx: int, *, tunnus: str, main_causes: list, backend_causes: list, main_done: bool, backend_done: bool, text: str) -> None:
        backend_symbol, backend_color = self._attention_symbol(backend_causes, backend_done)
        main_symbol, main_color = self._attention_symbol(main_causes, main_done)
        self._set_icon_cell(row_idx, PropertyTableWidget._COL_BACKEND_ATTENTION, backend_symbol, backend_color)
        self._set_icon_cell(row_idx, PropertyTableWidget._COL_MAIN_ATTENTION, main_symbol, main_color)

        # Keep the detail as tooltips on the attention cells (column removed from UI).
        try:
            item_backend = self.properties_table.item(row_idx, PropertyTableWidget._COL_BACKEND_ATTENTION)
            if item_backend:
                item_backend.setToolTip(text)
            item_main = self.properties_table.item(row_idx, PropertyTableWidget._COL_MAIN_ATTENTION)
            if item_main:
                item_main.setToolTip(text)
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module="property",
                event="add_from_map_set_tooltip_failed",
            )

        t = (tunnus or "").strip()
        archive_backend = self._archive_backend_plan.get(t, False)
        archive_map = self._archive_map_plan.get(t, False)

        if main_done and backend_done:
            backend_causes_lower = [c.lower() for c in (backend_causes or [])]
            backend_missing = any("missing in backend" in c for c in backend_causes_lower)
            backend_lookup_failed = any("backend lookup failed" in c for c in backend_causes_lower)

            if backend_missing or backend_lookup_failed:
                backend_symbol_plan, backend_color_plan = ("–", "gray")
            else:
                backend_symbol_plan, backend_color_plan = (("✗", "firebrick") if archive_backend else ("✓", "darkgreen"))

            map_symbol_plan, map_color_plan = (("✗", "firebrick") if archive_map else ("✓", "darkgreen"))
        else:
            backend_symbol_plan, backend_color_plan = ("…", "gray")
            map_symbol_plan, map_color_plan = ("…", "gray")

        self._set_icon_cell(row_idx, PropertyTableWidget._COL_ARCHIVE_BACKEND, backend_symbol_plan, backend_color_plan)
        self._set_icon_cell(row_idx, PropertyTableWidget._COL_ARCHIVE_MAP, map_symbol_plan, map_color_plan)

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


# ------------------------------------------------------------------
# Deprecated shim (dialog consolidated into AddPropertyDialog)
# ------------------------------------------------------------------
from .AddUpdatePropertyDialog import AddPropertyDialog, PropertyDialogMode


class AddFromMapPropertyDialog(AddPropertyDialog):
    """Deprecated: use AddPropertyDialog(mode=PropertyDialogMode.FROM_MAP)."""

    def __init__(self, parent=None):
        super().__init__(parent, mode=PropertyDialogMode.FROM_MAP)
