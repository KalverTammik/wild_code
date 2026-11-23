from datetime import timedelta
from math import ceil
from time import monotonic
from PyQt5.QtWidgets import QDialog, QPlainTextEdit
from ...FlowControllers.add_batch_runner import AddBatchRunner
from ...FlowControllers.property_dialog_phase import AddAction, AddMode
from .....utils.property.property_row_builder import PropertyRowBuilder
from .....widgets.DelayHelpers.glow_progress_bar import GlowProgressBar
from .....languages.translation_keys import TranslationKeys
from .....constants.layer_constants import IMPORT_PROPERTY_TAG
from .....utils.MapTools.MapHelpers import MapHelpers, ActiveLayersHelper
from .....constants.cadastral_fields import Katastriyksus
from ..property_import_review_dialog import PropertyImportReviewDialog
from .....Logs.python_fail_logger import PythonFailLogger


class PropertyAddRunMixin:
    """Adding the table's rows: the batch run, its progress, its summary and the review of
    undecided rows. Mixed into AddPropertyDialog, whose __init__ creates the state used here.
    """

    def _on_add_without_checks(self) -> None:
        selected_count = self._current_target_count()
        action = self._phase_state(selected_count=selected_count).add_action(with_checks=False)
        if action == AddAction.REVIEW:
            self._on_review_additions()
            return

        table = self.properties_table
        if action != AddAction.START or table is None:
            return

        def start_add() -> None:
            self._stop_attention_checks(clear_attention=True)
            self._update_add_button_state(selected_count=selected_count)
            self._start_batch_add(table, mode=AddMode.WITHOUT_CHECKS)

        # If the user already ran checks and archive plans exist, apply that plan first
        # before resetting check state for the add run. A running check has no plan yet.
        self._run_missing_cleanup_if_any(start_add)

    def _on_add_clicked(self) -> None:
        action = self._phase_state().add_action(with_checks=True)
        if action == AddAction.REVIEW:
            self._on_review_additions()
            return
        if action != AddAction.START:
            return
        self._run_missing_cleanup_if_any(
            lambda: self._start_batch_add(self.properties_table, mode=AddMode.WITH_CHECKS))

    def _start_batch_add(self, table, *, mode: str, review_decisions=None) -> None:
        if table is None:
            return

        action = self._phase_state().batch_add_action(mode=mode)
        if action == AddAction.REVIEW:
            self._on_review_additions()
            return

        if action != AddAction.START:
            return

        runner = AddBatchRunner(
            table,
            parent=self,
            use_filtered_rows=self._use_filtered_row_scope(),
            review_decisions=review_decisions,
        )
        self._add_runner = runner
        self._add_in_progress = True
        self._add_mode = mode
        self._add_started_at = monotonic()
        self._add_last_progress = (0, 0)
        self._add_last_tunnus = ''
        self._add_wait_until = 0.0
        self._add_wait_reason = None
        if self._add_errors_view is not None:
            self._add_errors_view.hide()

        runner.progress.connect(self._on_add_progress)
        runner.finished.connect(self._on_add_finished)
        runner.waiting.connect(self._on_add_waiting)

        self.check_progress_bar.hide()
        prefix_key = (TranslationKeys.ADD_UPDATE_PROGRESS_PREFIX_NO_CHECKS if mode == AddMode.WITHOUT_CHECKS
                      else TranslationKeys.ADD_UPDATE_PROGRESS_PREFIX)
        self.add_progress_bar.setAccessibleName(self.lang_manager.translate(prefix_key))
        self.add_progress_bar.setState(GlowProgressBar.RUNNING)
        self._render_add_progress()
        self._add_progress_timer.start()
        self._set_add_ui_state(active=True)
        runner.start()

    def _on_add_progress(self, done: int, total: int, phase: str, last_tunnus: str) -> None:
        self._add_last_tunnus = last_tunnus
        self._add_last_progress = (done, total)
        if self._add_wait_reason != 'cancelling':
            self._add_wait_reason = None
            self._add_wait_until = 0.0
        self._render_add_progress()

    def _on_add_waiting(self, seconds: float, reason: str) -> None:
        if not self._add_in_progress or self._add_wait_reason == 'cancelling':
            return
        self._add_wait_reason = reason if seconds > 0 else None
        self._add_wait_until = monotonic() + max(0.0, seconds)
        self._render_add_progress()

    def _render_add_progress(self) -> None:
        if not self._add_in_progress:
            return
        done, total = self._add_last_progress
        remaining = max(0, total - done)
        now = monotonic()
        elapsed = max(0.0, now - self._add_started_at)
        wait_seconds = max(0, ceil(self._add_wait_until - now))
        translate = self.lang_manager.translate
        estimate = translate(TranslationKeys.ADD_UPDATE_PROGRESS_ESTIMATING)
        if done > 0:
            # Wall time includes completed request pauses, so the estimate follows
            # actual throughput. Never predict finishing before a known cooldown.
            seconds = max(ceil(elapsed / done * remaining), wait_seconds) if remaining else 0
            estimate = translate(TranslationKeys.ADD_UPDATE_PROGRESS_ESTIMATE).format(
                duration=str(timedelta(seconds=seconds)))
        if self._add_wait_reason == 'cancelling':
            estimate = ''
        counts = translate(TranslationKeys.ADD_UPDATE_PROGRESS_COUNTS).format(
            done=done, total=total, remaining=remaining)
        timing = translate(TranslationKeys.ADD_UPDATE_PROGRESS_ELAPSED).format(
            duration=str(timedelta(seconds=int(elapsed))))
        self.add_progress_label.setText(counts + '\n' + timing + (' · ' + estimate if estimate else ''))
        self.add_progress_label.show()
        self.add_progress_bar.setRange(0, max(1, total))
        self.add_progress_bar.setValue(done)
        self.add_progress_bar.show()

        detail = ''
        if self._add_wait_reason == 'cancelling':
            detail = translate(TranslationKeys.ADD_UPDATE_PROPERTY_DIALOG_CANCELLING)
        elif wait_seconds > 0:
            key = (TranslationKeys.PROPERTY_ADD_RATE_WAIT if self._add_wait_reason == 'rate_limit'
                   else TranslationKeys.PROPERTY_ADD_PACING_WAIT)
            detail = translate(key).format(tunnus=self._add_last_tunnus, seconds=wait_seconds)
        elif self._add_last_tunnus:
            detail = translate(TranslationKeys.ADD_UPDATE_PROGRESS_CURRENT).format(tunnus=self._add_last_tunnus)
        self.add_detail_label.setText(detail)
        self.add_detail_label.setVisible(bool(detail))

    def _on_add_finished(self, summary: dict) -> None:
        if self._add_mode == AddMode.REVIEW:
            previous = self._add_summary
            replaced = set(summary.get('applied', [])) | {item['tunnus'] for item in summary['errors']}
            refreshed = {item['tunnus']: item for item in summary.get('deferred', [])}
            self._deferred_additions = [refreshed.pop(item['tunnus'], item)
                                       for item in self._deferred_additions if item['tunnus'] not in replaced]
            self._deferred_additions.extend(refreshed.values())
            # A review started from a check has no earlier run to merge counts into.
            if previous is not None:
                summary = dict(previous, succeeded=previous['succeeded'] + summary['succeeded'],
                               failed=previous['failed'] + summary['failed'],
                               errors=previous['errors'] + summary['errors'],
                               canceled=summary['canceled'], stopped=previous['stopped'] or summary['stopped'],
                               unfinished=summary.get('unfinished'), deferred=self._deferred_additions)
        else:
            self._deferred_additions = list(summary.get('deferred') or [])
        self._decisions_from_import = True
        self._add_summary = summary
        try:
            canceled = bool(summary.get("canceled")) if isinstance(summary, dict) else False
            done = int(summary.get("done") or 0) if isinstance(summary, dict) else 0
            total = int(summary.get("total") or 0) if isinstance(summary, dict) else 0
        except (TypeError, ValueError):  # non-numeric counters
            canceled = False
            done = 0
            total = 0

        if self._add_runner is not None:
            try:
                self._add_runner.deleteLater()
            except RuntimeError as exc:
                PythonFailLogger.log_exception(
                    exc,
                    module="property",
                    event="add_property_runner_delete_failed",
                )
        self._add_runner = None
        self._add_in_progress = False
        self._add_progress_timer.stop()
        self._add_wait_reason = None
        self._add_last_progress = (done, total)
        self.add_detail_label.hide()
        self.add_progress_bar.setRange(0, max(1, total))
        self.add_progress_bar.setValue(done)
        self.add_progress_bar.setState(GlowProgressBar.ERROR if summary.get('stopped') and not canceled
                                       else GlowProgressBar.IDLE)
        self.add_progress_bar.setVisible(total > 0)

        if total > 0:
            prefix = self.lang_manager.translate(TranslationKeys.ADD_UPDATE_PROGRESS_FINISHED)
            if self._add_mode == AddMode.WITHOUT_CHECKS:
                prefix = self.lang_manager.translate(TranslationKeys.ADD_UPDATE_PROGRESS_FINISHED_NO_CHECKS)

            if canceled:
                template = self.lang_manager.translate(TranslationKeys.ADD_UPDATE_PROGRESS_CANCELLED_TEMPLATE)
                self.add_progress_label.setText(template.format(prefix=prefix, done=done, total=total))
                # Reviewed runs keep their results visible, including any completed writes.
                try:
                    if 'succeeded' not in summary:
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
        if 'succeeded' in summary:
            self._checks_completed_for_scope = False
            self._update_add_button_state()
            self._show_add_summary()
        self._add_mode = None

    def _show_add_summary(self):
        summary = self._add_summary
        canceled = summary.get('canceled', False)
        done, total = summary['done'], summary['total']
        result_key = TranslationKeys.PROPERTY_ADD_CANCELLED_RESULT if canceled else TranslationKeys.PROPERTY_ADD_RESULT
        if summary.get('stopped') and not canceled:
            result_key = TranslationKeys.PROPERTY_ADD_STOPPED_RESULT
        self.add_progress_label.setText(self.lang_manager.translate(result_key).format(
            done=done, total=total, succeeded=summary['succeeded'], failed=summary['failed'],
            pending=summary.get('pending', total - done)) + '\n' + self.lang_manager.translate(
                TranslationKeys.PROPERTY_IMPORT_SUMMARY).format(
                    deferred=len(self._deferred_additions), kept=summary.get('kept', 0)))
        self.add_progress_label.setWordWrap(True)
        self.add_progress_label.show()
        details = list(summary.get('errors') or [])
        if summary.get('unfinished'):
            details.append(summary['unfinished'])
        if details:
            if self._add_errors_view is None:
                self._add_errors_view = QPlainTextEdit(self)
                self._add_errors_view.setReadOnly(True)
                self._add_errors_view.setMaximumHeight(110)
                self.layout().addWidget(self._add_errors_view)
            self._add_errors_view.setPlainText('\n'.join(
                f"{item['tunnus']}: {item['message']}" for item in details))
            self._add_errors_view.show()
        elif self._add_errors_view is not None:
            self._add_errors_view.hide()
        self._refresh_review_button()

    def _refresh_review_button(self) -> None:
        count = len(self._deferred_additions)
        self.review_additions_button.setText(self.lang_manager.translate(
            TranslationKeys.PROPERTY_IMPORT_REVIEW).format(count=count))
        self.review_additions_button.setVisible(count > 0)

    def _collect_check_decisions(self) -> list:
        """Undecided rows of the finished check, in the shape the review dialog expects."""
        run = self._check_run
        if run is None:
            return []

        decisions = []
        for _row_idx, decision, feature in run.decisions_in_row_order():
            if not isinstance(decision, dict) or decision.get('action') != 'needs_decision':
                continue
            tunnus = str(decision.get('tunnus') or '')
            main = run.main_layer_lookup.get(tunnus)
            decisions.append(dict(
                decision,
                fid=feature.id() if feature is not None else None,
                main_address=('' if main is None or main.fields().lookupField(Katastriyksus.l_aadress) < 0
                              else PropertyRowBuilder.read_field_text(main, Katastriyksus.l_aadress)),
            ))
        return decisions

    def _review_items_for_apply(self, decisions: list) -> list:
        """A check result carries no layer snapshot yet; take the current one before writing."""
        ready = [item for item in decisions if item.get('feature') is not None]
        pending = [item for item in decisions if item.get('feature') is None]
        if not pending:
            return ready

        source = MapHelpers.get_layer_by_tag(IMPORT_PROPERTY_TAG)
        target = ActiveLayersHelper.resolve_main_property_layer(dialogs=None)
        if source is None or target is None or not source.isValid() or not target.isValid():
            return ready

        for item in pending:
            feature = source.getFeature(item['fid']) if item.get('fid') is not None else None
            if feature is None or not feature.isValid():
                continue
            ready.append(dict(
                item,
                feature=feature,
                main_features=AddBatchRunner._matches(target, item['tunnus']),
                source_id=source.id(), source_uri=source.source(),
                target_id=target.id(), target_uri=target.source(),
            ))
        return ready

    def _on_review_additions(self):
        if not self._phase_state().can_review_additions:
            return
        dialog = PropertyImportReviewDialog(self._deferred_additions, lang_manager=self.lang_manager, parent=self)
        try:
            if dialog.exec_() != QDialog.Accepted:
                return
            choices = dialog.selected_decisions()
        finally:
            dialog.deleteLater()
        kept = {tunnus for tunnus, action in choices.items() if action == 'keep'}
        self._deferred_additions = [item for item in self._deferred_additions if item['tunnus'] not in kept]
        if self._add_summary is not None:
            self._add_summary['kept'] = self._add_summary.get('kept', 0) + len(kept)
            self._add_summary['deferred'] = self._deferred_additions
            self._show_add_summary()
        else:
            self._refresh_review_button()
        apply = [item for item in self._deferred_additions if choices.get(item['tunnus']) == 'apply']
        if apply:
            self._start_batch_add(self.properties_table, mode=AddMode.REVIEW,
                                  review_decisions=self._review_items_for_apply(apply))

    def _set_add_ui_state(self, *, active: bool) -> None:
        self._add_in_progress = bool(active)
        state = self._phase_state()

        # Everything that picks or changes the scope is frozen while a batch runs.
        self.review_additions_button.setEnabled(state.scope_controls_enabled)
        for button in (self.select_all_btn, self.clear_selection_btn):
            if button is not None:
                button.setEnabled(state.scope_controls_enabled)
        self.attention_only_checkbox.setEnabled(state.scope_controls_enabled)
        self.properties_table.setEnabled(state.scope_controls_enabled)
        if self.location_filter_widget is not None:
            self.location_filter_widget.setEnabled(state.scope_controls_enabled)

        self._update_add_button_state()

        if self.add_progress_label is not None:
            self.add_progress_label.setVisible(active or bool(self.add_progress_label.text()))

        self._update_run_checks_button()

    def _clear_add_result(self) -> None:
        """Drop the finished run's counts, errors and detail; they describe the old scope.

        Deferred decisions deliberately survive here: they stay reviewable until the
        dialog closes, so the review button keeps its own count.
        """

        if self._add_in_progress:
            return

        self.add_progress_bar.hide()
        self._add_last_progress = (0, 0)
        self.add_progress_label.clear()
        self.add_progress_label.hide()
        self._hide_detail_label()
        if self._add_errors_view is not None:
            self._add_errors_view.clear()
            self._add_errors_view.hide()
