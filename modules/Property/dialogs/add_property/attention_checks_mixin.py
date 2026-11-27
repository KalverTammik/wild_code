from math import ceil
from typing import Optional
from qgis.PyQt.QtCore import Qt, QCoreApplication
from ...FlowControllers.attention_display_rules import AttentionDisplayRules
from .....widgets.property_table.PropertyTableManager import PropertyTableManager, PropertyTableWidget
from .....utils.property.PropertyDataLoader import PropertyDataLoader
from ...FlowControllers.property_check_run import CheckRow, PropertyCheckRun, main_check_batch_params
from .....widgets.DelayHelpers.glow_progress_bar import GlowProgressBar
from .....languages.translation_keys import TranslationKeys
from .....constants.layer_constants import IMPORT_PROPERTY_TAG
from .....utils.MapTools.MapHelpers import MapHelpers, ActiveLayersHelper
from .....ui.messages_helper import ModernMessageDialog
from .....constants.cadastral_fields import Katastriyksus
from .....utils.date_helpers import DateHelpers
from .....Logs.python_fail_logger import PythonFailLogger


class PropertyAttentionChecksMixin:
    """The attention checks of the table's rows (backend and MAIN layer), their progress,
    the attention-only filter and the status icons. Mixed into AddPropertyDialog, whose
    __init__ creates the controllers and state used here.
    """

    def _on_attention_only_changed(self, _state: int) -> None:
        # If user turns it off after filtering, reload full table from current filters.
        checked = bool(self.attention_only_checkbox.isChecked())

        if not checked:
            # Showing the hidden rows again is all this takes. Reloading the table
            # instead used to throw away the finished check and its decisions (b6).
            if self._table_filtered_to_attention:
                self._clear_attention_filter()
                self._on_table_selection_changed()
            return

        # If checks already finished, apply immediately.
        if not self._checks_running:
            self._apply_attention_only_filter_if_ready()

    def _on_run_checks_clicked(self) -> None:
        self._start_attention_checks(source="manual_button")

    def _cancel_attention_checks(self) -> None:
        run = self._check_run
        done, total = self._checks_done_count(), (run.total if run is not None else 0)
        self._stop_attention_checks(clear_attention=False)
        self.add_progress_label.setText(self.lang_manager.translate(
            TranslationKeys.PROPERTY_CHECK_CANCELLED).format(done=done, total=total))
        self.add_progress_label.show()

    def _stop_check_controllers(self) -> None:
        self._backend_verify_controller.stop()
        self._main_check_controller.stop()

    def _stop_attention_checks(self, *, clear_attention: bool = False) -> None:
        self._stop_check_controllers()

        # The run is cancelled before it is dropped, so a controller signal that was
        # already queued cannot record anything on its way out.
        run, self._check_run = self._check_run, None
        if run is not None:
            run.cancel()

        self._checks_running = False
        self._checks_completed_for_scope = False
        if not self._decisions_from_import:
            self._deferred_additions = []
            self._refresh_review_button()
        self._missing_from_import = set()
        self._archive_backend_plan = {}
        self._archive_map_plan = {}

        self._set_check_progress(0, 0)
        if not self._add_in_progress:
            self._hide_detail_label()

        self._clear_attention_filter()

        if clear_attention:
            columns = (PropertyTableWidget._COL_BACKEND_ATTENTION, PropertyTableWidget._COL_MAIN_ATTENTION,
                       PropertyTableWidget._COL_ARCHIVE_BACKEND, PropertyTableWidget._COL_ARCHIVE_MAP)
            for row_idx in range(PropertyTableManager.row_count(self.properties_table)):
                for col in columns:
                    self._set_icon_cell(row_idx, col, "pending")

        self._update_add_button_state()
        self._update_run_checks_button()

    def _resolve_main_layer_cached(self):
        layer = self._main_layer_cached

        try:
            if layer is not None and not layer.isValid():
                layer = None
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module="property",
                event="add_property_layer_valid_check_failed",
            )
            layer = None

        if layer is None:
            layer = ActiveLayersHelper.resolve_main_property_layer(dialogs=ModernMessageDialog)
            self._main_layer_cached = layer

        return layer

    def _build_main_layer_lookup(self, layer, tunnus_set: set[str]) -> Optional[dict]:
        """The run's one read of the MAIN layer, or None when that read never happened.

        None is not an empty result. An empty result means the layer was asked about
        every tunnus and holds none of them; None means nothing can be concluded, and
        the check has to look rows up one at a time after all.
        """

        if not layer or not tunnus_set:
            return None
        try:
            return PropertyDataLoader.read_features_by_field_values(layer, Katastriyksus.tunnus, tunnus_set)
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module="property",
                event="add_property_build_lookup_failed",
            )
            return None

    def _start_attention_checks(self, *, source: str) -> None:
        table = self.properties_table
        if table is None:
            return

        if self._checks_running:
            return

        date_helpers = DateHelpers()
        entries = []
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

            entries.append(CheckRow(
                row=int(row_idx),
                tunnus=tunnus,
                import_muudet=import_muudet,
                # The run keeps the payload itself: the decisions it offers are
                # collected once the attention filter may already have changed the table.
                feature=PropertyTableManager.get_cell_data(table, row_idx, 0, role=Qt.ItemDataRole.UserRole),
            ))
            event_counter += 1
            if event_counter % self._rows_process_events_every == 0:
                QCoreApplication.processEvents()
        if event_counter and event_counter % self._rows_process_events_every != 0:
            QCoreApplication.processEvents()

        self._stop_attention_checks(clear_attention=False)

        self._check_run_seq += 1
        run = PropertyCheckRun(entries, run_id=self._check_run_seq)
        self._check_run = run
        self._checks_running = bool(entries)

        self._update_run_checks_button()

        self._set_check_progress(0, run.total)

        # Gate Add button while checks are running.
        self._update_add_button_state()

        if not entries:
            self._set_check_progress(0, 0)
            return

        # Cache MAIN layer once per run (UI-thread access).
        run.main_layer = self._resolve_main_layer_cached()
        lookup = self._build_main_layer_lookup(run.main_layer, run.tunnused())
        run.main_layer_lookup = lookup or {}
        run.lookup_is_complete = lookup is not None
        import_context = {}
        for entry in run.rows:
            main = run.main_layer_lookup.get(entry.tunnus)
            main_date = (date_helpers.date_to_iso_string(main[Katastriyksus.muudet])
                         if main is not None and main.fields().lookupField(Katastriyksus.muudet) >= 0 else None)
            import_context[entry.tunnus] = {
                'data': {'cadastralUnit': {'number': entry.tunnus},
                         'address': PropertyDataLoader.build_import_address(entry.feature)},
                'main_date': main_date,
            }

        batch_size, interval_ms = main_check_batch_params(run.total)

        # A fresh run has nothing checked yet, so the controller starts from empty.
        self._main_check_controller.configure(
            rows_for_verify_by_row=run.rows_for_verify_by_row(),
            main_layer=run.main_layer,
            main_layer_lookup=run.main_layer_lookup,
            lookup_is_complete=run.lookup_is_complete,
        )

        # Kick off a small synchronous batch to surface early results while backend checks spin up.
        for r in run.row_indices()[:10]:
            try:
                self._main_check_controller.ensure_row(r)
            except Exception as exc:
                PythonFailLogger.log_exception(
                    exc,
                    module="property",
                    event="add_property_main_check_row_failed",
                )

        self._update_run_checks_button()
        self._main_check_controller.start_pending(
            run.row_indices(),
            batch_size=batch_size,
            interval_ms=interval_ms,
        )

        # Mark in-progress in the Attention column.
        table.setUpdatesEnabled(False)
        for entry in run.rows:
            self._set_attention_row(
                entry.row,
                tunnus=entry.tunnus,
                main_causes=[],
                backend_causes=[],
                main_done=False,
                backend_done=False,
            )
        table.setUpdatesEnabled(True)

        self._update_check_status_label()

        try:
            self._backend_verify_controller.start(run.controller_rows(), source=source,
                                                 import_context_by_tunnus=import_context)
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module="property",
                event="add_property_backend_verify_start_failed",
            )
            # If backend verify cannot start, fall back to running MAIN checks only.
            # Mark backend as "done" for all rows so completion is driven by MAIN checks.
            run.mark_backend_all_checked()
            remaining = run.unchecked_main_rows()
            batch_size, interval_ms = main_check_batch_params(len(remaining))
            self._main_check_controller.start_pending(remaining, batch_size=batch_size, interval_ms=interval_ms)

    def _on_backend_verify_row_result(self, row: int, _tunnus: str, result: dict) -> None:
        row_idx = int(row)

        causes = []
        try:
            causes_raw = result.get("causes") if isinstance(result, dict) else []
            if isinstance(causes_raw, list):
                causes = [str(c).strip() for c in causes_raw if str(c).strip()]
        except Exception as exc:  # slot: a malformed worker result must not escape
            PythonFailLogger.log_exception(
                exc,
                module="property",
                event="add_property_backend_verify_causes_failed",
            )
            causes = []

        decision = result.get("decision") if isinstance(result, dict) else None
        run = self._check_run
        if run is None or not run.record_backend(row_idx, causes, decision):
            return

        # Run MAIN check for this row now (keeps UI responsive).
        self._main_check_controller.ensure_row(row_idx)

        self._update_row_attention_display(row_idx)
        self._update_check_status_label()

    def _on_backend_verify_waiting(self, seconds: float, reason: str) -> None:
        if self._checks_running:
            self._show_request_wait(seconds, reason)

    def _show_request_wait(self, seconds: float, reason: str) -> None:
        # The progress bar keeps its count; the pause is shown beneath it.
        if seconds <= 0:
            self._hide_detail_label()
            return
        key = (TranslationKeys.API_REQUEST_RATE_WAIT if reason == 'rate_limit'
               else TranslationKeys.API_REQUEST_PACING_WAIT)
        self.add_detail_label.setText(self.lang_manager.translate(key).format(seconds=ceil(seconds)))
        self.add_detail_label.show()

    def _on_backend_verify_finished(self, _summary: dict) -> None:
        """The backend run ended; only MAIN can still be outstanding.

        Every MAIN row is already queued by the time the backend run starts, so there is
        nothing left to kick off here: the backend finishing can only mean that the whole
        check is now done, or that MAIN is still working through its batches.
        """

        self._maybe_finish_checks()

    def _on_main_check_row_result(self, row: int, causes: list) -> None:
        row_idx = int(row)

        run = self._check_run
        if run is None or not run.record_main(row_idx, causes):
            return

        self._update_row_attention_display(row_idx)
        self._update_check_status_label()
        self._maybe_finish_checks()

    def _on_main_check_finished(self) -> None:
        self._maybe_finish_checks()

    def _update_row_attention_display(self, row_idx: int) -> None:
        table = self.properties_table
        if table is None:
            return

        run = self._check_run
        if run is None:
            return

        main_causes, backend_causes = run.causes_for_row(row_idx)
        main_done, backend_done = run.done_for_row(row_idx)

        self._set_attention_row(
            row_idx,
            tunnus=run.tunnus_for_row(row_idx),
            main_causes=main_causes,
            backend_causes=backend_causes,
            main_done=main_done,
            backend_done=backend_done,
        )

    def _maybe_finish_checks(self) -> None:
        if not self._checks_running:
            return

        run = self._check_run
        total = run.total if run is not None else 0
        if total <= 0:
            self._checks_running = False
            self._checks_completed_for_scope = False
            self._update_add_button_state()
            self._set_check_progress(0, 0)
            return

        if not run.is_complete:
            return

        # Exactly one call gets to announce this run as finished.
        if not run.mark_finished():
            return

        self._checks_running = False
        self._checks_completed_for_scope = True
        self._update_add_button_state()
        self._update_run_checks_button()

        self._set_check_progress(total, total)

        self._missing_from_import = self._compute_missing_from_import_set()
        self._archive_map_plan = {tunnus: True for tunnus in self._missing_from_import}
        # Candidate backend records are checked separately immediately before the
        # user reviews the archive plan. Missing properties have no import-table
        # row, so the regular row checks cannot safely decide this value.
        self._archive_backend_plan = {tunnus: False for tunnus in self._missing_from_import}
        if self._archive_scope_blocked_reason and self.add_progress_label is not None:
            self.add_progress_label.setText(
                self.lang_manager.translate(TranslationKeys.PROPERTY_ARCHIVE_SCOPE_SKIPPED)
            )
            self.add_progress_label.setVisible(True)
        elif self._archive_moved_elsewhere and self.add_progress_label is not None:
            self.add_progress_label.setText(
                self.lang_manager.translate(
                    TranslationKeys.PROPERTY_ARCHIVE_MOVED_EXCLUDED
                ).format(count=len(self._archive_moved_elsewhere))
            )
            self.add_progress_label.setVisible(True)

        # Offer the undecided properties now, before anything is written. The run carries
        # its own payloads, so the attention filter below cannot take them away.
        self._deferred_additions = self._collect_check_decisions()
        self._decisions_from_import = False
        self._refresh_review_button()

        # Hide the progress bar once finished.
        self._set_check_progress(0, 0)

        # If enabled, reduce the table to only rows that need attention and sync map selection.
        self._apply_attention_only_filter_if_ready()

    def _apply_attention_only_filter_if_ready(self) -> None:
        if not bool(self.attention_only_checkbox.isChecked()):
            return

        # Only apply after at least one completed run.
        run = self._check_run
        if run is None or run.total <= 0:
            return

        # Only filter when there is something to focus on.
        attention_rows = self._get_attention_row_indices()
        if not attention_rows:
            return

        # Avoid re-filtering.
        if self._table_filtered_to_attention is True:
            return

        self._apply_attention_only_filter(attention_rows)

    def _clear_attention_filter(self) -> None:
        """Show every row again. The filter is a view, so this decides nothing."""
        PropertyTableManager.show_all_rows(self.properties_table)
        self._table_filtered_to_attention = False

    def _get_attention_row_indices(self) -> list[int]:
        run = self._check_run
        if run is None:
            return []

        rows: list[int] = []
        for row_idx in run.row_indices():
            if AttentionDisplayRules.combined_causes(*run.causes_for_row(row_idx)):
                rows.append(int(row_idx))

        return sorted(set(rows))

    def _apply_attention_only_filter(self, attention_rows: list[int]) -> None:
        table = self.properties_table
        if table is None:
            return

        keep = {int(r) for r in (attention_rows or [])}
        if not keep:
            return

        # Hide the other rows rather than removing them: a removed row takes its
        # check result with it, and the result is what the user came here to act on.
        table.setUpdatesEnabled(False)
        table.blockSignals(True)
        table.clearSelection()
        PropertyTableManager.show_only_rows(table, keep)
        table.blockSignals(False)
        table.setUpdatesEnabled(True)

        # Clear map selection first, then zoom/select from the table.
        import_layer = MapHelpers.get_layer_by_tag(IMPORT_PROPERTY_TAG)
        if import_layer is not None:
            import_layer.removeSelection()

        self._table_filtered_to_attention = True

        # Refresh selection count + trigger debounced map update.
        self._on_table_selection_changed()

    def _update_check_status_label(self) -> None:
        run = self._check_run
        total = run.total if run is not None else 0
        if not self._checks_running or total <= 0:
            self._set_check_progress(0, 0)
            return

        self._set_check_progress(self._checks_done_count(), total)
        self._update_run_checks_button()

    def _checks_done_count(self) -> int:
        run = self._check_run
        return run.done_count() if run is not None else 0

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

        self.add_progress_bar.hide()
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
        bar.setState(GlowProgressBar.RUNNING if done_i < total_i else GlowProgressBar.IDLE)
        self._last_progress_total = total_i
        self._last_progress_done = done_i

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

    def _column_tooltip(self, causes: list, done: bool, ok_key: str, issues_key: str) -> str:
        """Each column explains itself: only its own reasons, or why it has none."""
        translate = self.lang_manager.translate
        if not done:
            return translate(TranslationKeys.PROPERTY_TOOLTIP_PENDING)
        reasons = AttentionDisplayRules.causes_text(causes, translate=translate)
        return translate(issues_key).format(causes=reasons) if reasons else translate(ok_key)

    def _set_attention_row(self, row_idx: int, *, tunnus: str, main_causes: list, backend_causes: list,
                           main_done: bool, backend_done: bool) -> None:
        translate = self.lang_manager.translate
        self._set_icon_cell(
            row_idx, PropertyTableWidget._COL_BACKEND_ATTENTION,
            self._attention_state(backend_causes, backend_done),
            tooltip=self._column_tooltip(backend_causes, backend_done,
                                         TranslationKeys.PROPERTY_TOOLTIP_BACKEND_OK,
                                         TranslationKeys.PROPERTY_TOOLTIP_BACKEND_ISSUES))
        self._set_icon_cell(
            row_idx, PropertyTableWidget._COL_MAIN_ATTENTION,
            self._attention_state(main_causes, main_done),
            tooltip=self._column_tooltip(main_causes, main_done,
                                         TranslationKeys.PROPERTY_TOOLTIP_MAIN_OK,
                                         TranslationKeys.PROPERTY_TOOLTIP_MAIN_ISSUES))

        # Archive plans per tunnus (set after checks finish).
        t = (tunnus or "").strip()
        archive_backend = self._archive_backend_plan.get(t, False)
        archive_map = self._archive_map_plan.get(t, False)

        backend_causes_lower = [c.lower() for c in (backend_causes or [])]
        backend_missing = any("missing in backend" in c for c in backend_causes_lower)
        backend_lookup_failed = any("backend lookup failed" in c for c in backend_causes_lower)

        if not (main_done and backend_done):
            backend_plan_state = map_plan_state = "pending"
            backend_plan_tip = map_plan_tip = translate(TranslationKeys.PROPERTY_TOOLTIP_PENDING)
        else:
            if backend_missing or backend_lookup_failed:
                backend_plan_state = "skip"
                backend_plan_tip = translate(TranslationKeys.PROPERTY_TOOLTIP_ARCHIVE_BACKEND_SKIP)
            elif archive_backend:
                backend_plan_state = "warning"
                backend_plan_tip = translate(TranslationKeys.PROPERTY_TOOLTIP_ARCHIVE_BACKEND_PLANNED)
            else:
                backend_plan_state = "ok"
                backend_plan_tip = translate(TranslationKeys.PROPERTY_TOOLTIP_ARCHIVE_NONE)
            map_plan_state = "warning" if archive_map else "ok"
            map_plan_tip = translate(TranslationKeys.PROPERTY_TOOLTIP_ARCHIVE_MAP_PLANNED if archive_map
                                     else TranslationKeys.PROPERTY_TOOLTIP_ARCHIVE_NONE)

        self._set_icon_cell(row_idx, PropertyTableWidget._COL_ARCHIVE_BACKEND, backend_plan_state,
                            tooltip=backend_plan_tip)
        self._set_icon_cell(row_idx, PropertyTableWidget._COL_ARCHIVE_MAP, map_plan_state, tooltip=map_plan_tip)
