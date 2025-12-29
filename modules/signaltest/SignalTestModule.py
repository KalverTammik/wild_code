from typing import Optional, Sequence

from PyQt5.QtCore import Qt, QItemSelectionModel, QThread, QTimer, QCoreApplication
from PyQt5.QtWidgets import (
    QHBoxLayout,
    QFormLayout,
    QVBoxLayout,
    QLabel,
    QWidget,
    QPushButton,
    QLineEdit,
    QFrame,
)

from ...constants.file_paths import QssPaths
from ...constants.layer_constants import IMPORT_PROPERTY_TAG
from ...constants.cadastral_fields import Katastriyksus
from ...constants.settings_keys import SettingsService
from ...utils.url_manager import Module
from ...widgets.theme_manager import ThemeManager
from ...modules.Property.FlowControllers.MainAddProperties import BackendPropertyVerifier, MainAddPropertiesFlow
from ...modules.Property.FlowControllers.UpdatePropertyData import UpdatePropertyData
from ...modules.Property.FlowControllers.BackendVerifyWorker import BackendVerifyWorker
from ...modules.Property.FlowControllers.MainDeleteProperties import deleteProperty
from ...modules.signaltest.BackendActionPromptDialog import BackendActionPromptDialog
from ...utils.MapTools.MapHelpers import MapHelpers
from ...utils.MapTools.MapHelpers import ActiveLayersHelper
from ...utils.MapTools.map_selection_controller import MapSelectionController
from ...utils.TagsEngines import TagsEngines, TagsHelpers

from ...widgets.DateHelpers import DateHelpers
from ...utils.mapandproperties.PropertyTableManager import PropertyTableManager, PropertyTableWidget

class SignalTestModule(QWidget):
    """Simple viewer for inspecting signals and payloads sent around the plugin.

    Currently focused on showing what SearchResultsWidget emits when the user
    clicks on a search result, but can be reused for other signal payloads.
    """

    def __init__(
        self,
        lang_manager: Optional[object] = None,
        parent: Optional[QWidget] = None,
        qss_files: Optional[Sequence[str]] = None,
    ) -> None:
        super().__init__(parent)

        self._qss_files = qss_files

        self.module_key = Module.SIGNALTEST.name.lower()
        self.name = self.module_key
        self.lang_manager = lang_manager
        self.display_name = "Signaltest"

        ThemeManager.apply_module_style(self, qss_files or [QssPaths.MAIN])

        self._sim_table = None
        self._map_selection_controller = MapSelectionController()
        self._selected_tunnused = []
        self._property_table_manager = PropertyTableManager()
        self.properties_table = None

        self._backend_verify_thread: Optional[QThread] = None
        self._backend_verify_worker: Optional[BackendVerifyWorker] = None
        self._backend_verify_stats: Optional[dict] = None
        self._main_compare_causes_by_row: dict[int, list[str]] = {}
        self._backend_compare_causes_by_row: dict[int, list[str]] = {}
        self._main_checked_rows: set[int] = set()
        self._backend_checked_rows: set[int] = set()
        self._rows_for_verify_by_row: dict[int, tuple[str, str]] = {}
        self._pending_main_check_rows: list[int] = []
        self._main_check_timer: Optional[QTimer] = None
        self._main_layer_for_verify = None

        self._backend_last_updated_by_tunnus: dict[str, str] = {}
        self._import_muudet_override_by_tunnus: dict[str, str] = {}
        self._backend_last_updated_override_by_tunnus: dict[str, str] = {}
        self._main_muudet_override_by_tunnus: dict[str, str] = {}
        self._table_selection_hooked = False

        outer = QVBoxLayout(self)
        outer.setContentsMargins(16, 16, 16, 16)
        outer.setSpacing(12)

        intro = QLabel("Signal tester")
        outer.addWidget(intro)

        self.test_tunnus_label = QLineEdit()
        self.test_tunnus_label.setPlaceholderText("63901:001:1458")

        self.import_muudet_input = QLineEdit()
        self.import_muudet_input.setPlaceholderText("Import muudet (ISO) e.g. 2025-01-31T10:20:30Z")

        self.set_import_muudet_button = QPushButton("Set")
        self.set_import_muudet_button.setToolTip("Apply override for selected row and re-run comparisons")
        self.set_import_muudet_button.clicked.connect(self._apply_import_muudet_override_for_current)

        self.backend_last_updated_input = QLineEdit()
        self.backend_last_updated_input.setPlaceholderText("Backend lastUpdated (ISO) e.g. 2024-12-01T08:00:00Z")

        self.set_backend_last_updated_button = QPushButton("Set")
        self.set_backend_last_updated_button.setToolTip("Apply override for selected row and re-run comparisons")
        self.set_backend_last_updated_button.clicked.connect(self._apply_backend_last_updated_override_for_current)

        self.main_layer_muudet_input = QLineEdit()
        self.main_layer_muudet_input.setPlaceholderText("Main-layer muudet e.g. 2024-12-15")

        self.set_main_muudet_button = QPushButton("Set")
        self.set_main_muudet_button.setToolTip("Apply override for selected row and re-run comparisons")
        self.set_main_muudet_button.clicked.connect(self._apply_main_muudet_override_for_current)

        inputs_frame = QFrame()
        inputs_frame.setObjectName("StatusFrame")
        inputs_layout = QFormLayout(inputs_frame)
        inputs_layout.setContentsMargins(10, 8, 10, 8)
        inputs_layout.setHorizontalSpacing(10)
        inputs_layout.setVerticalSpacing(8)
        inputs_layout.addRow(QLabel("Tunnus"), self.test_tunnus_label)

        import_row = QWidget()
        import_row_layout = QHBoxLayout(import_row)
        import_row_layout.setContentsMargins(0, 0, 0, 0)
        import_row_layout.setSpacing(6)
        import_row_layout.addWidget(self.import_muudet_input, 1)
        import_row_layout.addWidget(self.set_import_muudet_button)
        inputs_layout.addRow(QLabel("Simulate import muudet"), import_row)

        backend_row = QWidget()
        backend_row_layout = QHBoxLayout(backend_row)
        backend_row_layout.setContentsMargins(0, 0, 0, 0)
        backend_row_layout.setSpacing(6)
        backend_row_layout.addWidget(self.backend_last_updated_input, 1)
        backend_row_layout.addWidget(self.set_backend_last_updated_button)
        inputs_layout.addRow(QLabel("Simulate backend lastUpdated"), backend_row)

        main_row = QWidget()
        main_row_layout = QHBoxLayout(main_row)
        main_row_layout.setContentsMargins(0, 0, 0, 0)
        main_row_layout.setSpacing(6)
        main_row_layout.addWidget(self.main_layer_muudet_input, 1)
        main_row_layout.addWidget(self.set_main_muudet_button)
        inputs_layout.addRow(QLabel("Simulate main muudet"), main_row)
        outer.addWidget(inputs_frame)

        table_sim_frame = QFrame()
        table_sim_frame.setObjectName("StatusFrame")
        table_sim_layout = QVBoxLayout(table_sim_frame)
        table_sim_layout.setContentsMargins(10, 8, 10, 8)
        table_sim_layout.setSpacing(8)

        table_sim_buttons = QHBoxLayout()
        self.use_map_selection_button = QPushButton("Use map selection (IMPORT layer)")
        self.use_map_selection_button.setProperty("variant", "primary")
        self.use_map_selection_button.setToolTip(
            "Starts an interactive map selection on the IMPORT layer.\n"
            "Minimizes this window, activates the IMPORT layer, and lets you select one or more features.\n"
            "The selection becomes the simulated table selection."
        )
        self.use_map_selection_button.clicked.connect(self._start_import_layer_map_selector)

        table_sim_buttons.addWidget(self.use_map_selection_button)

        self.clear_table_selection_button = QPushButton("Clear selection")
        self.clear_table_selection_button.setToolTip("Clears the current table row selection")
        self.clear_table_selection_button.clicked.connect(self._clear_table_selection)
        table_sim_buttons.addWidget(self.clear_table_selection_button)

        table_sim_buttons.addStretch(1)
        table_sim_layout.addLayout(table_sim_buttons)

        outer.addWidget(table_sim_frame)

        self.archive_backend_button = QPushButton("Archive backend")
        self.archive_backend_button.setProperty("variant", "danger")
        self.archive_backend_button.setToolTip(
            "Archives backend properties for the selected table rows (by tunnus).\n"
            "Uses BackendPropertyVerifier to resolve a single active backend record and archives it.\n"
            "Warning: affects backend data."
        )
        self.archive_backend_button.clicked.connect(self._archive_backend_selected_rows)

        self.unarchive_backend_button = QPushButton("Unarchive backend")
        self.unarchive_backend_button.setProperty("variant", "danger")
        self.unarchive_backend_button.setToolTip(
            "Unarchives backend properties for the selected table rows (by tunnus).\n"
            "Will only unarchive when there is exactly one archived backend match for the tunnus; otherwise it refuses.\n"
            "Warning: affects backend data."
        )
        self.unarchive_backend_button.clicked.connect(self._unarchive_backend_selected_rows)

        self.delete_backend_button = QPushButton("Delete backend")
        self.delete_backend_button.setProperty("variant", "danger")
        self.delete_backend_button.setToolTip(
            "Deletes backend properties for the selected table rows (by tunnus).\n"
            "Uses the backend verifier to resolve a single backend record id and calls deleteProperty GraphQL.\n"
            "Warning: permanent; affects backend data."
        )
        self.delete_backend_button.clicked.connect(self._prompt_backend_action_for_selected_rows)

        self.remove_from_main_button = QPushButton("Remove from MAIN layer")
        self.remove_from_main_button.setProperty("variant", "danger")
        self.remove_from_main_button.setToolTip(
            "Deletes matching features from the MAIN property layer by tunnus and commits the edit.\n"
            "Uses the top 'Tunnus' field, otherwise the last map-selected tunnus.\n"
            "Warning: affects your QGIS layer data."
        )
        self.remove_from_main_button.clicked.connect(self._remove_feature_from_main_layer)


        self.update_main_muudet_button = QPushButton("Update MAIN muudet")
        self.update_main_muudet_button.setProperty("variant", "danger")
        self.update_main_muudet_button.setToolTip(
            "Updates the MAIN layer 'muudet' field for the given tunnus using 'Simulate main muudet'.\n"
            "Normalizes the value via DateHelpers (e.g. YYYY-MM-DD or ISO datetime).\n"
            "Warning: affects your QGIS layer data."
        )
        self.update_main_muudet_button.clicked.connect(self._update_main_muudet_for_tunnus)

        self.run_start_adding_properties_button = QPushButton("Run start_adding_properties")
        self.run_start_adding_properties_button.setProperty("variant", "primary")
        self.run_start_adding_properties_button.setToolTip(
            "Runs the real MainAddPropertiesFlow.start_adding_properties.\n"
            "If a simulated table is built/selected, it uses that selection; otherwise it relies on the real UI table selection.\n"
            "May prompt the user and may change backend/layers depending on the flow decisions."
        )
        self.run_start_adding_properties_button.clicked.connect(self._run_start_adding_properties)

        section_row = QHBoxLayout()
        section_row.setSpacing(8)

        backend_frame = QFrame()
        backend_frame.setObjectName("StatusFrame")
        backend_layout = QVBoxLayout(backend_frame)
        backend_layout.setContentsMargins(10, 8, 10, 8)
        backend_layout.setSpacing(8)
        backend_layout.addWidget(QLabel("Backend"))
        backend_buttons = QVBoxLayout()
        backend_buttons.setSpacing(8)
        backend_buttons.addWidget(self.archive_backend_button)
        backend_buttons.addWidget(self.unarchive_backend_button)
        backend_buttons.addWidget(self.delete_backend_button)
        backend_buttons.addStretch(1)
        backend_layout.addLayout(backend_buttons)
        section_row.addWidget(backend_frame, 1)

        layers_frame = QFrame()
        layers_frame.setObjectName("StatusFrame")
        layers_layout = QVBoxLayout(layers_frame)
        layers_layout.setContentsMargins(10, 8, 10, 8)
        layers_layout.setSpacing(8)
        layers_layout.addWidget(QLabel("Layers"))
        layers_buttons = QVBoxLayout()
        layers_buttons.setSpacing(8)
        layers_buttons.addWidget(self.remove_from_main_button)
        layers_buttons.addWidget(self.update_main_muudet_button)
        layers_buttons.addStretch(1)
        layers_layout.addLayout(layers_buttons)
        section_row.addWidget(layers_frame, 1)

        flow_frame = QFrame()
        flow_frame.setObjectName("StatusFrame")
        flow_layout = QVBoxLayout(flow_frame)
        flow_layout.setContentsMargins(10, 8, 10, 8)
        flow_layout.setSpacing(8)
        flow_layout.addWidget(QLabel("Flow"))
        flow_buttons = QVBoxLayout()
        flow_buttons.setSpacing(8)
        flow_buttons.addWidget(self.run_start_adding_properties_button)
        flow_buttons.addStretch(1)
        flow_layout.addLayout(flow_buttons)
        section_row.addWidget(flow_frame, 1)

        outer.addLayout(section_row)

        # Properties table (Signal tester uses this as the simulated selection table)
        properties_table_frame, properties_table = PropertyTableWidget._create_properties_table()
        self.properties_table = properties_table
        self._sim_table = self.properties_table
        self._configure_signaltest_properties_table()

        # All relevant state is now shown in the table; no separate Output panel.
        outer.addWidget(properties_table_frame, 1)

    def _stop_async_backend_verify(self) -> None:
        worker = self._backend_verify_worker
        thread = self._backend_verify_thread

        self._backend_verify_worker = None
        self._backend_verify_thread = None

        try:
            if worker is not None:
                worker.stop()
        except Exception:
            pass

        try:
            if thread is not None:
                thread.quit()
        except Exception:
            pass

        try:
            if self._main_check_timer is not None:
                self._main_check_timer.stop()
        except Exception:
            pass
        self._main_check_timer = None
        self._main_layer_for_verify = None

    def _collect_rows_for_backend_verify(self) -> list[tuple[int, str, str]]:
        table = self.properties_table
        if table is None:
            return []

        rows: list[tuple[int, str, str]] = []
        for row in range(table.rowCount()):
            item = table.item(row, self._COL_CADASTRAL_ID)
            tunnus = (item.text() if item is not None else "").strip()
            if not tunnus:
                continue

            import_muudet = ""
            try:
                override_val = self._import_muudet_override_by_tunnus.get(tunnus)
                if override_val is not None:
                    import_muudet = str(override_val)
                    rows.append((row, tunnus, import_muudet))
                    continue

                payload = item.data(Qt.UserRole) if item is not None else None
                if payload is not None:
                    try:
                        muudet_raw = payload[Katastriyksus.muudet]
                    except Exception:
                        muudet_raw = None
                    if muudet_raw is not None:
                        import_muudet = DateHelpers().date_to_iso_string(muudet_raw) or str(muudet_raw)
            except Exception:
                import_muudet = ""

            rows.append((row, tunnus, import_muudet))

        return rows

    def _start_async_backend_verify(self, *, source: str) -> None:
        table = self.properties_table
        if table is None:
            return

        self._stop_async_backend_verify()

        rows = self._collect_rows_for_backend_verify()

        # Reset per-run state; MAIN checks will run progressively (UI-thread) to avoid freezing.
        self._backend_compare_causes_by_row = {}
        self._main_compare_causes_by_row = {}
        self._main_checked_rows = set()
        self._backend_checked_rows = set()
        self._rows_for_verify_by_row = {row_idx: (tunnus, import_muudet) for row_idx, tunnus, import_muudet in rows}
        self._pending_main_check_rows = []

        # Cache MAIN layer once per run (UI-thread access).
        self._main_layer_for_verify = self._get_main_layer(silent=True)

        try:
            if self._main_check_timer is not None:
                self._main_check_timer.stop()
        except Exception:
            pass
        self._main_check_timer = None

        try:
            table.clearSelection()
        except Exception:
            pass

        try:
            # Immediately show progress per row; results will overwrite this.
            for row_idx, _tunnus, _import_muudet in rows:
                self._set_table_cell_text(row_idx, self._COL_ATTENTION, "Võrdlen andmeid...")
        except Exception:
            pass

        thread = QThread(self)
        worker = BackendVerifyWorker(
            rows,
            source=source,
            backend_last_updated_override_by_tunnus=self._backend_last_updated_override_by_tunnus,
        )
        worker.moveToThread(thread)

        thread.started.connect(worker.run)
        worker.rowResult.connect(self._on_backend_verify_row_result)
        worker.finished.connect(self._on_backend_verify_finished)
        worker.finished.connect(thread.quit)
        worker.finished.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)

        self._backend_verify_thread = thread
        self._backend_verify_worker = worker
        self._backend_verify_stats = {"source": source, "rows": len(rows), "attention": 0}

        thread.start()

        # MAIN checks run per-row when backend results arrive (smoother progressive flow).

    def _ensure_main_checked_for_row(self, row_idx: int) -> None:
        if row_idx in self._main_checked_rows:
            return

        tunnus, import_muudet = self._rows_for_verify_by_row.get(int(row_idx), ("", ""))
        if not tunnus:
            self._main_compare_causes_by_row[int(row_idx)] = []
            self._main_checked_rows.add(int(row_idx))
            return

        main_layer = self._main_layer_for_verify
        if not main_layer:
            self._main_compare_causes_by_row[int(row_idx)] = []
            self._main_checked_rows.add(int(row_idx))
            return

        causes: list[str] = []
        try:
            matches = MapHelpers.find_features_by_fields_and_values(main_layer, Katastriyksus.tunnus, [tunnus])
        except Exception:
            matches = []

        if not matches:
            causes.append("missing in main layer")
        else:
            feature = matches[0]
            try:
                main_muudet_raw = feature.attribute(Katastriyksus.muudet)
            except Exception:
                main_muudet_raw = None

            import_dt = DateHelpers.parse_iso(str(import_muudet) if import_muudet is not None else "")
            main_override = self._main_muudet_override_by_tunnus.get(tunnus)
            if main_override is not None:
                main_iso = str(main_override)
            else:
                main_iso = "" if main_muudet_raw is None else (DateHelpers().date_to_iso_string(main_muudet_raw) or str(main_muudet_raw))
            main_dt = DateHelpers.parse_iso(str(main_iso) if main_iso is not None else "")

            if import_dt and main_dt and import_dt > main_dt:
                causes.append("main layer older")

        self._main_compare_causes_by_row[int(row_idx)] = causes
        self._main_checked_rows.add(int(row_idx))

    def _process_main_check_batch(self, main_layer, *, batch_size: int) -> None:
        if not self._pending_main_check_rows:
            try:
                if self._main_check_timer is not None:
                    self._main_check_timer.stop()
            except Exception:
                pass
            self._main_check_timer = None
            return

        processed = 0
        while self._pending_main_check_rows and processed < int(batch_size):
            row_idx = int(self._pending_main_check_rows.pop(0))
            processed += 1

            if row_idx in self._main_checked_rows:
                continue

            tunnus, import_muudet = self._rows_for_verify_by_row.get(row_idx, ("", ""))
            if not tunnus:
                self._main_checked_rows.add(row_idx)
                self._main_compare_causes_by_row[row_idx] = []
                self._update_row_attention_display(row_idx)
                continue

            causes: list[str] = []
            try:
                matches = MapHelpers.find_features_by_fields_and_values(main_layer, Katastriyksus.tunnus, [tunnus])
            except Exception:
                matches = []

            if not matches:
                causes.append("missing in main layer")
            else:
                feature = matches[0]
                try:
                    main_muudet_raw = feature.attribute(Katastriyksus.muudet)
                except Exception:
                    main_muudet_raw = None

                import_dt = DateHelpers.parse_iso(str(import_muudet) if import_muudet is not None else "")
                main_override = self._main_muudet_override_by_tunnus.get(tunnus)
                if main_override is not None:
                    main_iso = str(main_override)
                else:
                    main_iso = "" if main_muudet_raw is None else (DateHelpers().date_to_iso_string(main_muudet_raw) or str(main_muudet_raw))
                main_dt = DateHelpers.parse_iso(str(main_iso) if main_iso is not None else "")

                if import_dt and main_dt and import_dt > main_dt:
                    causes.append("main layer older")

            self._main_compare_causes_by_row[row_idx] = causes
            self._main_checked_rows.add(row_idx)
            self._update_row_attention_display(row_idx)

        # Keep UI responsive between batches.
        try:
            QCoreApplication.processEvents()
        except Exception:
            pass

    def _update_row_attention_display(self, row: int) -> None:
        table = self.properties_table
        if table is None:
            return

        main_causes = self._main_compare_causes_by_row.get(row) or []
        backend_causes = self._backend_compare_causes_by_row.get(row) or []
        combined_causes = [c for c in (list(main_causes) + list(backend_causes)) if str(c).strip()]

        main_done = row in self._main_checked_rows
        backend_done = row in self._backend_checked_rows
        all_done = bool(main_done and backend_done)

        if not all_done:
            text = "Võrdlen andmeid..."
            if combined_causes:
                text += "; " + "; ".join(combined_causes)
        else:
            text = "; ".join(combined_causes) if combined_causes else ""

        self._set_table_cell_text(row, self._COL_ATTENTION, text)

        if combined_causes:
            try:
                sel_model = table.selectionModel()
                if sel_model is not None:
                    idx = table.model().index(row, 0)
                    sel_model.select(idx, QItemSelectionModel.Select | QItemSelectionModel.Rows)
            except Exception:
                pass

    def _on_backend_verify_row_result(self, row: int, tunnus: str, result: dict) -> None:
        table = self.properties_table
        if table is None:
            return

        # Cache backend lastUpdated for the selection-driven test harness.

        try:
            backend_info = result.get("backend_info") if isinstance(result, dict) else None
            if isinstance(backend_info, dict):
                self._backend_last_updated_by_tunnus[tunnus] = str(backend_info.get("LastUpdated") or "")
        except Exception:
            pass

        causes = result.get("causes")
        if not isinstance(causes, list):
            causes = []

        backend_causes = [str(c).strip() for c in causes if str(c).strip()]
        self._backend_compare_causes_by_row[row] = backend_causes
        self._backend_checked_rows.add(int(row))

        # Run MAIN check for this row now (smoother than a full upfront pass).
        try:
            self._ensure_main_checked_for_row(int(row))
        except Exception:
            pass

        # Update display; keep "Võrdlen..." until MAIN check is done too.
        self._update_row_attention_display(int(row))

        if backend_causes:
            try:
                if isinstance(self._backend_verify_stats, dict):
                    self._backend_verify_stats["attention"] = int(self._backend_verify_stats.get("attention") or 0) + 1
            except Exception:
                pass

    def _on_backend_verify_finished(self, summary: dict) -> None:
        try:
            self._backend_verify_worker = None
            self._backend_verify_thread = None
        except Exception:
            pass

        print({"auto_backend_verify_async": {"summary": summary, "stats": self._backend_verify_stats}})

        # If the backend worker was stopped early, finish remaining MAIN checks in small batches.
        try:
            remaining = [r for r in self._rows_for_verify_by_row.keys() if r not in self._main_checked_rows]
        except Exception:
            remaining = []

        if remaining:
            self._pending_main_check_rows = list(remaining)
            main_layer = self._main_layer_for_verify
            if main_layer:
                timer = QTimer(self)
                timer.setSingleShot(False)

                def _tick():
                    try:
                        self._process_main_check_batch(main_layer, batch_size=25)
                    except Exception:
                        try:
                            if self._main_check_timer is not None:
                                self._main_check_timer.stop()
                        except Exception:
                            pass

                timer.timeout.connect(_tick)
                self._main_check_timer = timer
                try:
                    QTimer.singleShot(0, lambda: timer.start(0))
                except Exception:
                    timer.start(0)

    def _compute_main_layer_attention_causes(self, rows: list[tuple[int, str, str]]) -> dict[int, list[str]]:
        """UI-thread MAIN-layer check.

        Rules:
        - If MAIN is missing the feature by `tunnus` => attention.
        - If MAIN has a feature with same `tunnus` and MAIN `muudet` is older than import `muudet` => attention.
        """

        causes_by_row: dict[int, list[str]] = {}

        # QGIS layers/feature access should remain on the UI thread.
        main_layer = self._get_main_layer(silent=True)
        if not main_layer:
            return causes_by_row

        for row_idx, tunnus, import_muudet in rows:
            if not tunnus:
                continue

            matches = MapHelpers.find_features_by_fields_and_values(main_layer, Katastriyksus.tunnus, [tunnus])
            if not matches:
                causes_by_row[row_idx] = ["missing in main layer"]
                continue

            feature = matches[0]
            try:
                main_muudet_raw = feature.attribute(Katastriyksus.muudet)
            except Exception:
                main_muudet_raw = None

            import_dt = DateHelpers.parse_iso(str(import_muudet) if import_muudet is not None else "")
            main_override = self._main_muudet_override_by_tunnus.get(tunnus)
            if main_override is not None:
                main_iso = str(main_override)
            else:
                main_iso = "" if main_muudet_raw is None else (DateHelpers().date_to_iso_string(main_muudet_raw) or str(main_muudet_raw))
            main_dt = DateHelpers.parse_iso(str(main_iso) if main_iso is not None else "")

            if import_dt and main_dt and import_dt > main_dt:
                existing = causes_by_row.get(row_idx) or []
                causes_by_row[row_idx] = list(existing) + ["main layer older"]

        return causes_by_row

    # --- Signal tester table columns ---
    # Keep base columns (0..3) identical to Property UI, and append Signal tester-only columns.
    _COL_CADASTRAL_ID = 0
    _COL_ADDRESS = 1
    _COL_AREA = 2
    _COL_SETTLEMENT = 3
    _COL_ATTENTION = 4

    def _configure_signaltest_properties_table(self) -> None:
        if self.properties_table is None:
            return

        table = self.properties_table

        # Preserve the first 4 translated headers coming from PropertyTableWidget.
        base_headers = []
        for i in range(4):
            try:
                h = table.horizontalHeaderItem(i)
                base_headers.append(h.text() if h else "")
            except Exception:
                base_headers.append("")

        extra_headers = ["Attention"]

        try:
            table.setColumnCount(len(base_headers) + len(extra_headers))
            table.setHorizontalHeaderLabels(base_headers + extra_headers)
        except Exception:
            pass

        if not self._table_selection_hooked:
            try:
                table.itemSelectionChanged.connect(self._sync_inputs_from_current_table_selection)
                self._table_selection_hooked = True
            except Exception:
                pass

    def _get_first_selected_row_index(self) -> Optional[int]:
        table = self.properties_table
        if table is None:
            return None

        selected_rows: set[int] = set()
        for item in table.selectedItems() or []:
            try:
                selected_rows.add(int(item.row()))
            except Exception:
                pass

        if not selected_rows:
            return None
        return sorted(selected_rows)[0]

    def _get_tunnus_for_row(self, row: int) -> str:
        table = self.properties_table
        if table is None:
            return ""
        try:
            cell = table.item(row, self._COL_CADASTRAL_ID)
            return (cell.text() if cell is not None else "").strip()
        except Exception:
            return ""

    def _get_import_muudet_for_row(self, row: int, tunnus: str) -> str:
        override_val = self._import_muudet_override_by_tunnus.get(tunnus)
        if override_val is not None:
            return str(override_val)

        table = self.properties_table
        if table is None:
            return ""
        try:
            item = table.item(row, self._COL_CADASTRAL_ID)
            payload = item.data(Qt.UserRole) if item is not None else None
            if payload is None:
                return ""
            try:
                muudet_raw = payload[Katastriyksus.muudet]
            except Exception:
                muudet_raw = None
            if muudet_raw is None:
                return ""
            return DateHelpers().date_to_iso_string(muudet_raw) or str(muudet_raw)
        except Exception:
            return ""

    def _get_backend_last_updated_for_tunnus(self, tunnus: str) -> str:
        override_val = self._backend_last_updated_override_by_tunnus.get(tunnus)
        if override_val is not None:
            return str(override_val)
        return str(self._backend_last_updated_by_tunnus.get(tunnus) or "")

    def _get_main_muudet_for_tunnus(self, tunnus: str) -> str:
        override_val = self._main_muudet_override_by_tunnus.get(tunnus)
        if override_val is not None:
            return str(override_val)

        main_layer = self._get_main_layer(silent=True)
        if not main_layer:
            return ""

        matches = MapHelpers.find_features_by_fields_and_values(main_layer, Katastriyksus.tunnus, [tunnus])
        if not matches:
            return ""
        feature = matches[0]
        try:
            main_muudet_raw = feature.attribute(Katastriyksus.muudet)
        except Exception:
            main_muudet_raw = None
        if main_muudet_raw is None:
            return ""
        return DateHelpers().date_to_iso_string(main_muudet_raw) or str(main_muudet_raw)

    def _sync_inputs_from_current_table_selection(self) -> None:
        row = self._get_first_selected_row_index()
        if row is None:
            return

        tunnus = self._get_tunnus_for_row(row)
        if not tunnus:
            return

        try:
            self.test_tunnus_label.setText(tunnus)
            self.import_muudet_input.setText(self._get_import_muudet_for_row(row, tunnus))
            self.backend_last_updated_input.setText(self._get_backend_last_updated_for_tunnus(tunnus))
            self.main_layer_muudet_input.setText(self._get_main_muudet_for_tunnus(tunnus))
        except Exception:
            pass

    def _apply_import_muudet_override_for_current(self) -> None:
        tunnus = (self.test_tunnus_label.text() or "").strip()
        if not tunnus:
            print("Select a row first.")
            return
        val = (self.import_muudet_input.text() or "").strip()
        if val:
            self._import_muudet_override_by_tunnus[tunnus] = val
        else:
            self._import_muudet_override_by_tunnus.pop(tunnus, None)
        self._start_async_backend_verify(source="override_import_muudet")

    def _apply_backend_last_updated_override_for_current(self) -> None:
        tunnus = (self.test_tunnus_label.text() or "").strip()
        if not tunnus:
            print("Select a row first.")
            return
        val = (self.backend_last_updated_input.text() or "").strip()
        if val:
            self._backend_last_updated_override_by_tunnus[tunnus] = val
        else:
            self._backend_last_updated_override_by_tunnus.pop(tunnus, None)
        self._start_async_backend_verify(source="override_backend_last_updated")

    def _apply_main_muudet_override_for_current(self) -> None:
        tunnus = (self.test_tunnus_label.text() or "").strip()
        if not tunnus:
            print("Select a row first.")
            return
        val = (self.main_layer_muudet_input.text() or "").strip()
        if val:
            self._main_muudet_override_by_tunnus[tunnus] = val
        else:
            self._main_muudet_override_by_tunnus.pop(tunnus, None)
        self._start_async_backend_verify(source="override_main_muudet")

    def _get_selected_tunnused_from_table(self) -> list[str]:
        table = self.properties_table
        if table is None:
            return []

        selected_rows: set[int] = set()
        for item in table.selectedItems() or []:
            try:
                selected_rows.add(int(item.row()))
            except Exception:
                pass

        tunnused: list[str] = []
        for row in sorted(selected_rows):
            try:
                cell = table.item(row, self._COL_CADASTRAL_ID)
                tunnus = (cell.text() if cell is not None else "").strip()
            except Exception:
                tunnus = ""
            if tunnus:
                tunnused.append(tunnus)

        return tunnused

    def _clear_table_selection(self) -> None:
        table = self.properties_table
        if table is None:
            return
        try:
            table.clearSelection()
        except Exception:
            pass
        try:
            table.setCurrentCell(-1, -1)
        except Exception:
            pass
        try:
            self.test_tunnus_label.setText("")
            self.import_muudet_input.setText("")
            self.backend_last_updated_input.setText("")
            self.main_layer_muudet_input.setText("")
        except Exception:
            pass

    def _archive_backend_selected_rows(self) -> None:
        tunnused = self._get_selected_tunnused_from_table()
        if not tunnused:
            print("Select one or more rows in the table first.")
            return

        self._archive_backend_tunnused(tunnused, source="archive_backend_selected")

    def _archive_backend_tunnused(self, tunnused: list[str], *, source: str) -> None:
        if not tunnused:
            return

        tag_name = TagsEngines.ARHIVEERITUD_TAG_NAME
        module = Module.PROPERTY.name
        tag_id = TagsHelpers.check_if_tag_exists(tag_name=tag_name, module=module)

        for tunnus in tunnused:
            backend_info = BackendPropertyVerifier.verify_properties_by_cadastral_number(tunnus)
            if not isinstance(backend_info, dict) or backend_info.get("exists") is None:
                print({"archive_backend": {"tunnus": tunnus, "ok": False, "reason": "backend_lookup_failed", "backend_info": backend_info}})
                continue

            if not backend_info.get("exists"):
                print({"archive_backend": {"tunnus": tunnus, "ok": False, "reason": "no_active_backend_property"}})
                continue

            active_count = backend_info.get("active_count")
            if isinstance(active_count, int) and active_count > 1:
                print({"archive_backend": {"tunnus": tunnus, "ok": False, "reason": "multiple_active_backend_matches", "active_count": active_count}})
                continue

            prop = backend_info.get("property") if isinstance(backend_info.get("property"), dict) else None
            prop_id = (prop.get("id") if isinstance(prop, dict) else None) if prop else None
            if not prop_id:
                print({"archive_backend": {"tunnus": tunnus, "ok": False, "reason": "missing_property_id"}})
                continue

            ok = UpdatePropertyData._archive_a_propertie(item_id=str(prop_id), archive_tag=tag_id)
            print({"archive_backend": {"tunnus": tunnus, "property_id": str(prop_id), "ok": bool(ok)}})

        self._start_async_backend_verify(source=source)

    def _unarchive_backend_selected_rows(self) -> None:
        tunnused = self._get_selected_tunnused_from_table()
        if not tunnused:
            print("Select one or more rows in the table first.")
            return

        self._unarchive_backend_tunnused(tunnused, source="unarchive_backend_selected")

    def _unarchive_backend_tunnused(self, tunnused: list[str], *, source: str) -> None:
        if not tunnused:
            return

        for tunnus in tunnused:
            backend_info = BackendPropertyVerifier.verify_properties_by_cadastral_number(tunnus)
            if not isinstance(backend_info, dict) or backend_info.get("exists") is None:
                print({"unarchive_backend": {"tunnus": tunnus, "ok": False, "reason": "backend_lookup_failed", "backend_info": backend_info}})
                continue

            archived_ids = backend_info.get("archived_ids") or []
            if isinstance(archived_ids, list):
                archived_ids = [str(i).strip() for i in archived_ids if i]
            else:
                archived_ids = []

            if len(archived_ids) == 0:
                print({"unarchive_backend": {"tunnus": tunnus, "ok": False, "reason": "no_archived_backend_match"}})
                continue
            if len(archived_ids) > 1:
                print({"unarchive_backend": {"tunnus": tunnus, "ok": False, "reason": "multiple_archived_backend_matches", "archived_ids": archived_ids}})
                continue

            prop_id = archived_ids[0]
            ok = UpdatePropertyData._unarchive_property_data(item_id=prop_id)
            print({"unarchive_backend": {"tunnus": tunnus, "property_id": prop_id, "ok": bool(ok)}})

        self._start_async_backend_verify(source=source)

    def _delete_backend_tunnused(self, tunnused: list[str], *, source: str) -> None:
        if not tunnused:
            return

        for tunnus in tunnused:
            backend_info = BackendPropertyVerifier.verify_properties_by_cadastral_number(tunnus)
            if not isinstance(backend_info, dict) or backend_info.get("exists") is None:
                print({"delete_backend": {"tunnus": tunnus, "ok": False, "reason": "backend_lookup_failed", "backend_info": backend_info}})
                continue

            property_ids: list[str] = []

            if backend_info.get("exists"):
                active_count = backend_info.get("active_count")
                if isinstance(active_count, int) and active_count > 1:
                    print({"delete_backend": {"tunnus": tunnus, "ok": False, "reason": "multiple_active_backend_matches", "active_count": active_count}})
                    continue

                prop = backend_info.get("property") if isinstance(backend_info.get("property"), dict) else None
                prop_id = (prop.get("id") if isinstance(prop, dict) else None) if prop else None
                if not prop_id:
                    print({"delete_backend": {"tunnus": tunnus, "ok": False, "reason": "missing_property_id"}})
                    continue
                property_ids = [str(prop_id)]
            else:
                # Allow delete when there is exactly one archived match and no active.
                active_count = backend_info.get("active_count")
                try:
                    if int(active_count or 0) > 0:
                        print({"delete_backend": {"tunnus": tunnus, "ok": False, "reason": "active_backend_exists"}})
                        continue
                except Exception:
                    pass

                archived_ids = backend_info.get("archived_ids") or []
                if isinstance(archived_ids, list):
                    archived_ids = [str(i).strip() for i in archived_ids if i]
                else:
                    archived_ids = []

                if len(archived_ids) == 0:
                    print({"delete_backend": {"tunnus": tunnus, "ok": False, "reason": "no_backend_match"}})
                    continue
                if len(archived_ids) > 1:
                    print({"delete_backend": {"tunnus": tunnus, "ok": False, "reason": "multiple_archived_backend_matches", "archived_ids": archived_ids}})
                    continue
                property_ids = [archived_ids[0]]

            for prop_id in property_ids:
                ok, message = deleteProperty.delete_single_item(str(prop_id))
                print({"delete_backend": {"tunnus": tunnus, "property_id": str(prop_id), "ok": bool(ok), "message": message}})

        self._start_async_backend_verify(source=source)

    def _prompt_backend_action_for_selected_rows(self) -> None:
        table = self.properties_table
        if table is None:
            return

        selected_rows: list[int] = []
        try:
            rows_set: set[int] = set()
            for item in table.selectedItems() or []:
                try:
                    rows_set.add(int(item.row()))
                except Exception:
                    pass
            selected_rows = sorted(rows_set)
        except Exception:
            selected_rows = []

        if not selected_rows:
            print("Select one or more rows in the table first.")
            return

        tunnused = self._get_selected_tunnused_from_table()
        if not tunnused:
            print("Select one or more rows in the table first.")
            return

        # Build a snapshot table using the same factory as the main UI.
        snapshot_frame, snapshot_table = PropertyTableWidget._create_properties_table()

        try:
            headers: list[str] = []
            for c in range(table.columnCount()):
                try:
                    h = table.horizontalHeaderItem(c)
                    headers.append(h.text() if h else "")
                except Exception:
                    headers.append("")
            snapshot_table.setColumnCount(len(headers))
            snapshot_table.setHorizontalHeaderLabels(headers)
        except Exception:
            pass

        # Fill snapshot table directly.
        try:
            from PyQt5.QtWidgets import QTableWidgetItem

            snapshot_table.setRowCount(len(selected_rows))
            for out_row_idx, src_row_idx in enumerate(selected_rows):
                for col in range(table.columnCount()):
                    src_item = table.item(src_row_idx, col)
                    text = src_item.text() if src_item is not None else ""
                    snapshot_table.setItem(out_row_idx, col, QTableWidgetItem(text))
        except Exception:
            pass

        dlg = BackendActionPromptDialog(parent=self, table_frame=snapshot_frame, table=snapshot_table)
        ok = dlg.exec_()
        if not ok:
            return

        action = dlg.action
        if not tunnused or not action:
            return

        if action == "archive":
            self._archive_backend_tunnused(tunnused, source="dialog_archive_backend")
        elif action == "unarchive":
            self._unarchive_backend_tunnused(tunnused, source="dialog_unarchive_backend")
        elif action == "delete":
            self._delete_backend_tunnused(tunnused, source="dialog_delete_backend")

    def _remove_feature_from_main_layer(self) -> None:
        """Delete features from the MAIN property layer by tunnus.

        Uses `test_tunnus_label` if present, otherwise the last map-selected tunnus.
        """
        tunnus = (self.test_tunnus_label.text() or "").strip()
        if not tunnus:
            tunnus = str(self._selected_tunnused[0]) if self._selected_tunnused else ""

        if not tunnus:
            print("Provide a tunnus (top input) or in the table simulator list.")
            return

        # Prefer the shared helper that matches Property UI behaviour.
        main_layer = ActiveLayersHelper._get_active_property_layer()
        if not main_layer:
            # Fallback to name-based resolution (keeps tester usable even if helper shows warnings).
            layer_name = SettingsService().module_main_layer_name(Module.PROPERTY.value) or ""
            main_layer = MapHelpers.find_layer_by_name(layer_name)
        if not main_layer:
            print("Main property layer not configured/found; cannot remove feature.")
            return

        matches = MapHelpers.find_features_by_fields_and_values(main_layer, Katastriyksus.tunnus, [tunnus])
        if not matches:
            print({"remove_from_main": {"tunnus": tunnus, "deleted": 0, "reason": "not_found"}})
            return

        feature_ids = [f.id() for f in matches]
        MapHelpers.ensure_layer_visible(main_layer, make_active=True)

        try:
            if not main_layer.isEditable():
                main_layer.startEditing()
            ok_delete = main_layer.deleteFeatures(feature_ids)
            ok_commit = main_layer.commitChanges() if ok_delete else False
            if not ok_commit:
                try:
                    main_layer.rollBack()
                except Exception:
                    pass
        except Exception as e:
            try:
                main_layer.rollBack()
            except Exception:
                pass
            print({"remove_from_main_exception": str(e)})
            return

        try:
            main_layer.triggerRepaint()
        except Exception:
            pass

        print(
            {
                "remove_from_main": {
                    "layer": main_layer.name(),
                    "tunnus": tunnus,
                    "matched": len(matches),
                    "deleted": len(feature_ids) if ok_commit else 0,
                    "feature_ids": feature_ids,
                    "committed": bool(ok_commit),
                }
            }
        )

    def _get_main_layer(self, *, silent: bool = False):
        if silent:
            layer_name = SettingsService().module_main_layer_name(Module.PROPERTY.value) or ""
            return MapHelpers.find_layer_by_name(layer_name)
        return ActiveLayersHelper._get_active_property_layer()

    def _get_main_feature_by_tunnus(self, tunnus: str):
        main_layer = self._get_main_layer(silent=True)
        if not main_layer:
            return None, None
        matches = MapHelpers.find_features_by_fields_and_values(main_layer, Katastriyksus.tunnus, [tunnus])
        return main_layer, (matches[0] if matches else None)

    def _pull_main_muudet_for_tunnus(self) -> None:
        tunnus = (self.test_tunnus_label.text() or "").strip()
        if not tunnus:
            print("Please provide a cadastral tunnus.")
            return

        main_layer, feature = self._get_main_feature_by_tunnus(tunnus)
        if not main_layer:
            print("Main property layer not configured/found.")
            return
        if not feature:
            self.main_layer_muudet_input.setText("")
            print({"pull_main_muudet": {"tunnus": tunnus, "found": False}})
            return

        try:
            value = feature[Katastriyksus.muudet]
        except Exception:
            value = None

        iso_value = "" if value is None else DateHelpers().date_to_iso_string(value)
        self.main_layer_muudet_input.setText(iso_value)
        print(
            {
                "pull_main_muudet": {
                    "layer": main_layer.name(),
                    "tunnus": tunnus,
                    "found": True,
                    "muudet": iso_value,
                    "raw": "" if value is None else str(value),
                }
            }
        )

    def _update_main_muudet_for_tunnus(self) -> None:
        tunnus = (self.test_tunnus_label.text() or "").strip()
        if not tunnus:
            print("Please provide a cadastral tunnus.")
            return
        raw_muudet = (self.main_layer_muudet_input.text() or "").strip()
        if not raw_muudet:
            print("Please provide a value in 'Simulate main muudet'.")
            return

        new_muudet = DateHelpers().date_to_iso_string(raw_muudet)
        if not new_muudet:
            print(
                "Invalid 'Simulate main muudet' value. Use YYYY-MM-DD, dd.MM.yyyy, or a QDate(...) string."
            )
            return

        main_layer, feature = self._get_main_feature_by_tunnus(tunnus)
        if not main_layer:
            print("Main property layer not configured/found.")
            return
        if not feature:
            print({"update_main_muudet": {"tunnus": tunnus, "updated": False, "reason": "not_found"}})
            return

        MapHelpers.ensure_layer_visible(main_layer, make_active=True)

        try:
            if not main_layer.isEditable():
                main_layer.startEditing()
            feature.setAttribute(Katastriyksus.muudet, new_muudet)
            ok_update = main_layer.updateFeature(feature)
            ok_commit = main_layer.commitChanges() if ok_update else False
            if not ok_commit:
                try:
                    main_layer.rollBack()
                except Exception:
                    pass
        except Exception as e:
            try:
                main_layer.rollBack()
            except Exception:
                pass
            print({"update_main_muudet_exception": str(e)})
            return

        try:
            main_layer.triggerRepaint()
        except Exception:
            pass

        print(
            {
                "update_main_muudet": {
                    "layer": main_layer.name(),
                    "tunnus": tunnus,
                    "muudet": new_muudet,
                    "raw": raw_muudet,
                    "updated": bool(ok_commit),
                }
            }
        )

    def _run_start_adding_properties(self) -> None:
        table = self._sim_table
        if table is None:
            print(
                "Running MainAddPropertiesFlow.start_adding_properties(table=None). This will only work if the real Property table has selections."
            )
        else:
            try:
                selected_count = len(table.selectedItems() or [])
            except Exception:
                selected_count = None
            print(
                f"Running MainAddPropertiesFlow.start_adding_properties(simulated_table). Selected items: {selected_count}" 
            )
            print(
                "Note: if backend has only archived matches for a tunnus, the flow will prompt: Unarchive existing / Create new / Skip."
            )
        try:
            ok = MainAddPropertiesFlow.start_adding_properties(table=table)
        except Exception as e:
            print({"start_adding_properties_exception": str(e)})
            return
        print({"start_adding_properties_result": ok})

    def _set_simulated_table_from_features(self, features, *, source: str) -> None:
        feats = list(features or [])
        tunnused: list[str] = []
        rows = []

        for f in feats:
            try:
                QCoreApplication.processEvents()
            except Exception:
                pass
            try:
                cadastral_id = str(f[Katastriyksus.tunnus])
            except Exception:
                cadastral_id = ""
            try:
                address = str(f[Katastriyksus.l_aadress])
            except Exception:
                address = ""
            try:
                area = str(f[Katastriyksus.pindala])
            except Exception:
                area = ""
            try:
                settlement = str(f[Katastriyksus.ay_nimi])
            except Exception:
                settlement = ""

            # Import-layer muudet (normalize to ISO string where possible)
            try:
                muudet_raw = f[Katastriyksus.muudet]
            except Exception:
                muudet_raw = None
            import_muudet = "" if muudet_raw is None else (DateHelpers().date_to_iso_string(muudet_raw) or str(muudet_raw))

            if cadastral_id:
                tunnused.append(cadastral_id)

            rows.append(
                {
                    "cadastral_id": cadastral_id,
                    "address": address,
                    "area": area,
                    "settlement": settlement,
                    "feature": f,
                }
            )

        self._selected_tunnused = list(tunnused)

        if self.properties_table is None:
            print({"sim_table_built": {"source": source, "selected": len(feats), "tunnused": tunnused, "error": "no_properties_table"}})
            return

        # Ensure the table always reflects the latest selection (avoid stale visual state).
        try:
            self.properties_table.setUpdatesEnabled(False)
        except Exception:
            pass
        try:
            self.properties_table.clearSelection()
        except Exception:
            pass
        try:
            self.properties_table.clearContents()
        except Exception:
            pass
        try:
            self.properties_table.setRowCount(0)
        except Exception:
            pass

        ok = self._property_table_manager.populate_properties_table(rows, properties_table=self.properties_table)
        if ok:
            try:
                # Selection will be set by the post-verify step ("needs attention" rows).
                self.properties_table.clearSelection()
            except Exception:
                pass
            self._sim_table = self.properties_table

            # Clear attention column; it will be filled by the post-verify step.
            try:
                for row_idx in range(self.properties_table.rowCount()):
                    self._set_table_cell_text(row_idx, self._COL_ATTENTION, "")
            except Exception:
                pass

        try:
            self.properties_table.setUpdatesEnabled(True)
        except Exception:
            pass
        try:
            self.properties_table.viewport().update()
            self.properties_table.repaint()
        except Exception:
            pass

        print(
            {
                "sim_table_built": {
                    "source": source,
                    "selected": len(feats),
                    "tunnused": tunnused,
                    "table_populated": bool(ok),
                }
            }
        )

        try:
            QTimer.singleShot(0, self._sync_inputs_from_current_table_selection)
        except Exception:
            pass

    def _set_table_cell_text(self, row: int, col: int, text: str) -> None:
        if self.properties_table is None:
            return
        try:
            item = self.properties_table.item(row, col)
            if item is None:
                from PyQt5.QtWidgets import QTableWidgetItem

                item = QTableWidgetItem("")
                self.properties_table.setItem(row, col, item)
            item.setText(text)
        except Exception:
            pass

    def _auto_verify_backend_and_select_attention_rows(self, *, source: str) -> None:
        """Verify backend existence + freshness and select rows needing attention.

        Attention rules:
        - Backend missing => attention
        - Backend archived-only (no active) => attention
        - Backend exists but import `muudet` is newer than backend `cadastralUnitLastUpdated` => attention
        """

        if self.properties_table is None:
            return

        table = self.properties_table
        row_count = table.rowCount() if table is not None else 0

        # Start from no attention; select only misses.
        try:
            table.clearSelection()
        except Exception:
            pass

        ok_fresh: list[str] = []
        missing_backend: list[str] = []
        archived_only_backend: list[str] = []
        outdated_backend: list[str] = []
        errors: list[dict] = []

        for row in range(row_count):
            item = table.item(row, 0)
            tunnus = (item.text() if item is not None else "")
            tunnus = (tunnus or "").strip()
            if not tunnus:
                continue

            # Pull import-layer muudet from the stored feature payload (UserRole), if present.
            import_muudet = ""
            try:
                payload = item.data(Qt.UserRole) if item is not None else None
                if payload is not None:
                    try:
                        muudet_raw = payload[Katastriyksus.muudet]
                    except Exception:
                        muudet_raw = None
                    if muudet_raw is not None:
                        import_muudet = DateHelpers().date_to_iso_string(muudet_raw) or str(muudet_raw)
            except Exception:
                import_muudet = ""

            try:
                backend_info = BackendPropertyVerifier.verify_properties_by_cadastral_number(tunnus)
            except Exception as e:
                errors.append({"tunnus": tunnus, "error": str(e)})
                continue

            exists_backend_any = False
            exists_backend_active = None
            archived_only_val = None
            backend_last_updated = ""

            if isinstance(backend_info, dict):
                # Primary (flow uses these keys)
                exists_val = backend_info.get("exists")
                archived_only_val = backend_info.get("archived_only")
                backend_last_updated = str(backend_info.get("LastUpdated") or "")

                # Some shapes may omit `exists` but provide counts/property.
                active_count = backend_info.get("active_count")
                archived_count = backend_info.get("archived_count")
                prop = backend_info.get("property")

                if exists_val is not None:
                    exists_backend_active = bool(exists_val)
                    exists_backend_any = bool(exists_val or archived_only_val)
                else:
                    try:
                        exists_backend_any = bool((int(active_count or 0) + int(archived_count or 0)) > 0)
                    except Exception:
                        exists_backend_any = bool(prop)

            # Derive attention decision
            attention = False
            import_newer = False
            attention_causes: list[str] = []

            if isinstance(backend_info, dict) and backend_info.get("exists") is None:
                # backend lookup failure -> attention
                attention = True
                attention_causes.append("backend lookup failed")
            elif not exists_backend_any:
                attention = True
                missing_backend.append(tunnus)
                attention_causes.append("missing in backend")
            elif archived_only_val:
                attention = True
                archived_only_backend.append(tunnus)
                attention_causes.append("archived only")
            else:
                # Freshness check (import vs backend)
                try:
                    import_newer = bool(
                        MainAddPropertiesFlow._is_import_newer(import_muudet, backend_last_updated, None)
                    )
                except Exception:
                    import_newer = False

                if import_newer:
                    attention = True
                    outdated_backend.append(tunnus)
                    attention_causes.append("import newer")
                else:
                    ok_fresh.append(tunnus)

            # Update Attention column (only)
            self._set_table_cell_text(row, self._COL_ATTENTION, "; ".join(attention_causes) if attention else "")

            if attention:
                try:
                    sel_model = table.selectionModel()
                    if sel_model is not None:
                        idx = table.model().index(row, 0)
                        sel_model.select(idx, QItemSelectionModel.Select | QItemSelectionModel.Rows)
                except Exception:
                    pass

        print(
            {
                "auto_backend_verify": {
                    "source": source,
                    "rows": row_count,
                    "ok_fresh": len(ok_fresh),
                    "missing_backend": len(missing_backend),
                    "archived_only": len(archived_only_backend),
                    "outdated_backend": len(outdated_backend),
                    "attention_selected": len(missing_backend) + len(archived_only_backend) + len(outdated_backend),
                    "ok_fresh_tunnused": ok_fresh,
                    "missing_backend_tunnused": missing_backend,
                    "archived_only_tunnused": archived_only_backend,
                    "outdated_tunnused": outdated_backend,
                    "errors": errors,
                }
            }
        )

    def _bring_window_to_front(self) -> None:
        try:
            main_dialog = self.window()
            if not main_dialog:
                return
            main_dialog.showNormal()
            main_dialog.raise_()
            main_dialog.activateWindow()
        except Exception:
            pass

    def _start_import_layer_map_selector(self) -> None:
        import_layer = MapHelpers._get_layer_by_tag(IMPORT_PROPERTY_TAG)
        if not import_layer:
            print("Import layer not found by tag; cannot start map selector.")
            return

        MapHelpers.ensure_layer_visible(import_layer, make_active=True)
        try:
            self.window().showMinimized()
        except Exception:
            pass

        def _on_selected(_layer, features):
            self._set_simulated_table_from_features(features, source=f"map_selector:{import_layer.name()}")

            # Restore window ASAP (let table paint) and then verify backend in the background.
            QTimer.singleShot(0, self._bring_window_to_front)
            QTimer.singleShot(0, lambda: self._start_async_backend_verify(source=f"map_selector:{import_layer.name()}"))

            def _sync_top_fields():
                try:
                    selected_tunnus = None
                    if features:
                        selected_tunnus = str(features[0][Katastriyksus.tunnus])
                    if selected_tunnus:
                        self.test_tunnus_label.setText(selected_tunnus)
                        self._pull_main_muudet_for_tunnus()
                except Exception:
                    pass

            QTimer.singleShot(0, _sync_top_fields)

        started = self._map_selection_controller.start_selection(
            import_layer,
            on_selected=_on_selected,
            selection_tool="rectangle",
            restore_pan=True,
            min_selected=1,
            max_selected=None,
            clear_filter=True,
        )
        if started:
            print(
                f"Map selector started on layer '{import_layer.name()}'. Select one or more features on the map."
            )
        else:
            self._bring_window_to_front()
            print("Failed to start map selector.")

    def activate(self) -> None:
        """Module lifecycle hook (currently unused)."""

    def deactivate(self) -> None:
        """Module lifecycle hook (currently unused)."""

    def get_widget(self) -> QWidget:
        return self

