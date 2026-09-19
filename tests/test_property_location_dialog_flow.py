from __future__ import annotations

import os
import sys
import threading
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
if os.environ.get('QGIS_PREFIX_PATH'):
    sys.path.append(str(Path(os.environ['QGIS_PREFIX_PATH']) / 'python' / 'plugins'))

from PyQt5.QtCore import QCoreApplication, QEvent, QThread, QTimer, Qt, QVariant
from PyQt5.QtGui import QFont, QFontDatabase
from PyQt5.QtTest import QTest
from PyQt5.QtWidgets import QDialog, QPushButton, QTableView, QVBoxLayout, QWidget
from qgis.core import (QgsApplication, QgsFeature, QgsField, QgsGeometry, QgsVariantUtils, QgsVectorLayer,
                       QgsVectorLayerFeatureSource)

from Kavitro_dev.constants.cadastral_fields import Katastriyksus as F
from Kavitro_dev.languages.language_manager import LanguageManager
from Kavitro_dev.languages.translation_keys import TranslationKeys as K
from Kavitro_dev.utils.MapTools.MapHelpers import MapHelpers
from Kavitro_dev.utils.mapandproperties.PropertyDataLoader import PropertyDataLoader
from Kavitro_dev.utils.mapandproperties.PropertyTableManager import PropertyTableManager
from Kavitro_dev.utils.mapandproperties.property_dialog_phase import (AddAction, AddMode, CancelTarget,
                                                                      PropertyDialogPhase as P,
                                                                      PropertyDialogState)
from Kavitro_dev.widgets.LocationFilterWidget import LocationFilterHelper, LocationFilterWidget
sys.path.insert(0, str(Path(__file__).resolve().parent))
from property_fixtures import (LocationFilterTestCase, add_fields, add_import_fields,
                               backend_info, close_dialog, dialog_open, make_main_layer,
                               missing_info, open_dialog, unknown_info)


class PropertyLocationDialogFlowTest(LocationFilterTestCase):
    """The add dialog end to end: opening, checks, add and archive flows, cancelling."""

    def test_add_dialog_missing_import_layer_shows_close_only(self):
        """b1: no import layer loaded must not crash the dialog with AttributeError."""
        from Kavitro_dev.widgets.AddUpdatePropertyDialog import AddPropertyDialog
        self.resolve_mock.return_value = None
        dialog = open_dialog(AddPropertyDialog)
        try:
            self.assertIsNone(dialog.property_layer)
            self.assertIsNone(dialog.properties_table)
            close_buttons = [b for b in dialog.findChildren(QPushButton)]
            self.assertEqual(len(close_buttons), 1)
            close_buttons[0].click()
            self.assertEqual(dialog.result(), QDialog.Rejected)
        finally:
            dialog.deleteLater()

    def test_checked_add_dialog_uses_background_runner_and_shows_failures(self):
        from Kavitro_dev.widgets.AddUpdatePropertyDialog import AddPropertyDialog
        from Kavitro_dev.modules.Property.FlowControllers.AddBatchRunner import AddBatchRunner
        self.add_import_fields()
        dialog = open_dialog(AddPropertyDialog)
        try:
            self.wait_until(lambda: dialog.county_combo.isEnabled())
            with patch.object(AddBatchRunner, 'start') as start, \
                    patch.object(dialog, '_run_missing_cleanup_if_any', side_effect=lambda then: then()):
                dialog._on_add_clicked()
                start.assert_not_called()
                dialog._checks_completed_for_scope = True
                dialog._on_add_clicked()
                start.assert_called_once()
            self.assertIsInstance(dialog._add_runner, AddBatchRunner)
            self.assertFalse(dialog.location_filter_widget.isEnabled())
            self.assertFalse(dialog.properties_table.isEnabled())
            runner = dialog._add_runner
            dialog._on_add_progress(0, 2, 'processing', '1')
            runner.waiting.emit(37.0, 'rate_limit')
            self.assertIn('37', dialog.add_detail_label.text())
            self.assertIn('1', dialog.add_detail_label.text())
            self.assertIn('0/2', dialog.add_progress_label.text())
            self.assertTrue(dialog.add_progress_bar.isVisible())
            self.assertEqual(dialog.add_progress_bar.value(), 0)
            self.assertEqual(dialog.add_progress_bar.maximum(), 2)
            self.assertEqual(runner._done, 0)
            self.assertFalse(dialog.add_button.isEnabled())
            runner._in_flight = True
            dialog.reject()
            self.assertTrue(dialog.isVisible())
            self.assertTrue(runner._stop_requested)
            runner._in_flight = False
            runner._done, runner._total = 1, 2
            runner._errors = [{'tunnus': '1', 'message': 'Offline test error'}]
            runner._finish()
            self.assertIsNone(dialog._add_runner)
            self.assertFalse(dialog._checks_completed_for_scope)
            self.assertTrue(dialog.location_filter_widget.isEnabled())
            self.assertTrue(dialog.properties_table.isEnabled())
            self.assertIn('1/2', dialog.add_progress_label.text())
            self.assertEqual(dialog.add_progress_bar.value(), 1)
            self.assertFalse(dialog._add_progress_timer.isActive())
            self.assertFalse(dialog.add_detail_label.isVisible())
            self.assertEqual(dialog._add_errors_view.toPlainText(), '1: Offline test error')
            self.assertTrue(dialog._add_errors_view.isVisible())
            dialog._on_add_finished({'canceled': True, 'done': 0, 'total': 2, 'succeeded': 0,
                                     'failed': 0, 'pending': 2, 'errors': [],
                                     'unfinished': {'tunnus': '1', 'message': 'Intended uses unfinished'}})
            self.assertEqual(dialog._add_errors_view.toPlainText(), '1: Intended uses unfinished')
            self.assertIn('0/2', dialog.add_progress_label.text())
            self.assertEqual(dialog.add_progress_bar.value(), 0)
            # Skipping the preflight must not bypass the protected add runner.
            self.assertFalse(dialog._checks_completed_for_scope)
            with patch.object(AddBatchRunner, 'start') as start:
                dialog._start_batch_add(dialog.properties_table, mode='without_checks')
                start.assert_called_once()
            self.assertIsInstance(dialog._add_runner, AddBatchRunner)
            dialog._add_runner.cancel()
            self.assertIsNone(dialog._add_runner)
        finally:
            dialog.reject()
            self.wait_until(lambda: not dialog._location_filter_helper._loader._request.busy)
            dialog.deleteLater()

    def test_real_precheck_and_import_defer_conflict_then_keep_without_reimporting_successes(self):
        from Kavitro_dev.widgets.AddUpdatePropertyDialog import AddPropertyDialog
        from Kavitro_dev.widgets.property_import_review_dialog import PropertyImportReviewDialog
        from Kavitro_dev.modules.Property.FlowControllers import AddBatchRunner as runner_module
        self.add_import_fields()
        self.layer.dataProvider().changeAttributeValues({feature.id(): {
            self.layer.fields().lookupField(F.muudet): '2025-01-01'} for feature in self.layer.getFeatures()})
        main = make_main_layer()
        lookup = lambda number: (backend_info(number, address='Different')
                                 if number == '1' else missing_info())
        with patch.object(runner_module.BackendPropertyVerifier, 'verify_properties_by_cadastral_number', side_effect=lookup), \
                patch.object(runner_module.ActiveLayersHelper, 'resolve_main_property_layer', return_value=main), \
                patch.object(runner_module.MainAddPropertiesFlow, 'add_single_property_item', return_value='created') as create, \
                patch.object(runner_module.UpdatePropertyData, 'update_single_property_item') as update, \
                patch.object(AddPropertyDialog, 'exec_', return_value=0):
            dialog = AddPropertyDialog()
            try:
                self.wait_until(lambda: dialog.county_combo.isEnabled())
                self.pick(dialog)
                self.wait_until(lambda: PropertyTableManager.row_count(dialog.properties_table) == 2)
                self.assertEqual(PropertyTableManager.get_payload_field_text(dialog.properties_table, 0, 0, F.muudet),
                                 '2025-01-01')
                dialog._on_run_checks_clicked()
                self.wait_until(lambda: dialog._checks_completed_for_scope)
                self.assertIn(K.PROPERTY_ADD_BACKEND_DIFFERS, dialog._check_run.causes_for_row(0)[1])
                with patch.object(dialog, '_run_missing_cleanup_if_any', side_effect=lambda then: then()), \
                        patch.object(PropertyDataLoader, 'prepare_data_for_import_stage1', side_effect=lambda feature: (
                            {'cadastralUnit': {'number': feature[F.tunnus]}, 'address': {'street': 'Address',
                             'houseNumber': feature[F.tunnus]}}, feature[F.tunnus], [], '2025-01-01')):
                    dialog._on_add_clicked()
                    self.wait_until(lambda: dialog._add_runner is None)
                self.assertEqual((dialog._add_summary['done'], dialog._add_summary['succeeded'],
                                  dialog._add_summary['failed']), (2, 1, 0))
                self.assertEqual(len(dialog._deferred_additions), 1)
                self.assertTrue(dialog.review_additions_button.isVisible())
                self.assertIn('Otsust ootab: 1', dialog.add_progress_label.text())
                create.assert_called_once()
                update.assert_not_called()
                with patch.object(PropertyImportReviewDialog, 'exec_', return_value=0):
                    dialog._on_review_additions()
                self.assertEqual(len(dialog._deferred_additions), 1)
                with patch.object(PropertyImportReviewDialog, 'exec_', return_value=1), \
                        patch.object(PropertyImportReviewDialog, 'selected_decisions', return_value={'1': 'keep'}):
                    dialog._on_review_additions()
                self.assertEqual(dialog._deferred_additions, [])
                self.assertEqual(dialog._add_summary['kept'], 1)
                self.assertEqual(dialog._add_summary['succeeded'], 1)
                self.assertIn('Säilitati olemasolev: 1', dialog.add_progress_label.text())
                self.assertFalse(dialog.review_additions_button.isVisible())
                create.assert_called_once()
                update.assert_not_called()
                self.assertEqual(main.featureCount(), 1)
            finally:
                dialog.reject()
                self.wait_until(lambda: not dialog._location_filter_helper._loader._request.busy)
                dialog.deleteLater()

    def test_review_results_merge_into_original_counts_and_only_retry_deferred_property(self):
        from Kavitro_dev.widgets.AddUpdatePropertyDialog import AddPropertyDialog
        from Kavitro_dev.widgets.property_import_review_dialog import PropertyImportReviewDialog
        from Kavitro_dev.modules.Property.FlowControllers.AddBatchRunner import AddBatchRunner
        self.add_import_fields()
        dialog = open_dialog(AddPropertyDialog)
        decision = {'tunnus': '1', 'reason': K.PROPERTY_ADD_BACKEND_DIFFERS, 'backend_info': {},
                    'feature': next(self.layer.getFeatures())}
        try:
            self.wait_until(lambda: dialog.county_combo.isEnabled())
            for outcome in ('success', 'changed', 'error', 'cancelled'):
                with self.subTest(outcome=outcome):
                    initial = {'done': 82, 'total': 82, 'succeeded': 81, 'failed': 0, 'pending': 0,
                               'errors': [], 'canceled': False, 'stopped': False, 'deferred': [decision]}
                    dialog._on_add_finished(initial)
                    with patch.object(PropertyImportReviewDialog, 'exec_', return_value=1), \
                            patch.object(PropertyImportReviewDialog, 'selected_decisions', return_value={'1': 'apply'}), \
                            patch.object(AddBatchRunner, 'start'):
                        dialog._on_review_additions()
                    runner = dialog._add_runner
                    self.assertEqual(set(runner._review_decisions), {'1'})
                    result = {'done': 1, 'total': 1, 'succeeded': int(outcome == 'success'),
                              'failed': int(outcome == 'error'), 'pending': 0,
                              'errors': [{'tunnus': '1', 'message': 'Write failed'}] if outcome == 'error' else [],
                              'canceled': outcome == 'cancelled', 'stopped': outcome == 'error',
                              'deferred': [dict(decision, changed=True)] if outcome == 'changed' else [],
                              'applied': ['1'] if outcome == 'success' else []}
                    runner._dispose_timer()
                    runner.finished.emit(result)
                    self.assertEqual(dialog._add_summary['total'], 82)
                    self.assertEqual(dialog._add_summary['succeeded'], 82 if outcome == 'success' else 81)
                    self.assertEqual(len(dialog._deferred_additions), int(outcome in ('changed', 'cancelled')))
                    self.assertEqual(dialog._add_summary['failed'], int(outcome == 'error'))
                    self.assertIsNone(dialog._add_runner)
        finally:
            dialog.reject()
            self.wait_until(lambda: not dialog._location_filter_helper._loader._request.busy)
            dialog.deleteLater()

    def test_add_progress_stays_visible_during_pauses_and_resets_between_runs(self):
        from Kavitro_dev.widgets.AddUpdatePropertyDialog import AddPropertyDialog
        from Kavitro_dev.modules.Property.FlowControllers.AddBatchRunner import AddBatchRunner
        self.add_import_fields()
        dialog = open_dialog(AddPropertyDialog)
        try:
            self.wait_until(lambda: dialog.county_combo.isEnabled())
            dialog.lang_manager = LanguageManager('et')
            translate = dialog.lang_manager.translate
            with patch('Kavitro_dev.widgets.AddUpdatePropertyDialog.monotonic', return_value=100.0) as clock, \
                    patch.object(AddBatchRunner, 'start'), \
                    patch.object(dialog, '_run_missing_cleanup_if_any', side_effect=lambda then: then()):
                for mode in ('with_checks', 'without_checks'):
                    with self.subTest(mode=mode):
                        clock.return_value = 100.0
                        dialog._checks_completed_for_scope = True
                        dialog._start_batch_add(dialog.properties_table, mode=mode)
                        runner = dialog._add_runner
                        runner.progress.emit(0, 172, 'starting', '')
                        self.assertIn('0/172', dialog.add_progress_label.text())
                        self.assertIn(translate(K.ADD_UPDATE_PROGRESS_ESTIMATING), dialog.add_progress_label.text())
                        self.assertEqual(dialog.add_progress_bar.value(), 0)
                        self.assertFalse(dialog.add_detail_label.isVisible())
                        self.assertTrue(dialog._add_progress_timer.isActive())

                        clock.return_value = 170.0
                        runner.progress.emit(35, 172, 'processing', '34201:001:0462')
                        counts = translate(K.ADD_UPDATE_PROGRESS_COUNTS).format(done=35, total=172, remaining=137)
                        self.assertIn(counts, dialog.add_progress_label.text())
                        self.assertIn(translate(K.ADD_UPDATE_PROGRESS_ESTIMATE).format(duration='0:04:34'), dialog.add_progress_label.text())
                        runner.waiting.emit(2, 'pacing')
                        self.assertIn(counts, dialog.add_progress_label.text())
                        self.assertIn('34201:001:0462', dialog.add_detail_label.text())
                        self.assertEqual(dialog.add_progress_bar.value(), 35)
                        self.assertEqual(dialog.add_progress_bar.maximum(), 172)

                        # A long known server pause must remain visible and bound the ETA.
                        runner.waiting.emit(600, 'rate_limit')
                        self.assertIn(translate(K.ADD_UPDATE_PROGRESS_ESTIMATE).format(duration='0:10:00'), dialog.add_progress_label.text())
                        clock.return_value = 180.0
                        dialog._add_progress_timer.setInterval(20)
                        self.wait_until(lambda: '590' in dialog.add_detail_label.text())
                        self.assertIn(translate(K.ADD_UPDATE_PROGRESS_ELAPSED).format(duration='0:01:20'), dialog.add_progress_label.text())
                        self.assertIn(counts, dialog.add_progress_label.text())

                        # Wrapped messages must fit above the actions at the minimum size.
                        dialog.resize(650, 420)
                        QTest.qWait(30)
                        for label in (dialog.add_progress_label, dialog.add_detail_label):
                            self.assertGreaterEqual(label.height(), label.heightForWidth(label.width()))
                            self.assertLess(label.geometry().bottom(), dialog.cancel_button.geometry().top())
                        self.assertTrue(dialog.add_progress_bar.isVisible())

                        runner.waiting.emit(0, 'rate_limit')
                        self.assertEqual(dialog.add_detail_label.text(), translate(K.ADD_UPDATE_PROGRESS_CURRENT).format(tunnus='34201:001:0462'))
                        runner._in_flight = True
                        dialog._on_cancel_clicked()
                        runner.waiting.emit(10, 'rate_limit')
                        dialog._add_progress_timer.timeout.emit()
                        self.assertIn(counts, dialog.add_progress_label.text())
                        self.assertEqual(dialog.add_detail_label.text(), translate(K.ADD_UPDATE_PROPERTY_DIALOG_CANCELLING))
                        runner._in_flight = False
                        runner._done, runner._total, runner._succeeded = 35, 172, 35
                        runner._finish()
                        final_text = dialog.add_progress_label.text()
                        self.assertIn('35/172', final_text)
                        self.assertIn('137', final_text)
                        self.assertEqual(dialog.add_progress_bar.value(), 35)
                        self.assertFalse(dialog._add_progress_timer.isActive())
                        self.assertFalse(dialog.add_detail_label.isVisible())
                        dialog._on_add_waiting(15, 'rate_limit')
                        dialog._add_progress_timer.timeout.emit()
                        self.assertEqual(dialog.add_progress_label.text(), final_text)

                # Only a fully processed batch reaches 100%; cancellation stays partial.
                dialog._on_add_finished({'canceled': False, 'done': 172, 'total': 172,
                                         'succeeded': 172, 'failed': 0, 'pending': 0, 'errors': []})
                self.assertEqual(dialog.add_progress_bar.value(), dialog.add_progress_bar.maximum())
        finally:
            dialog.reject()
            self.wait_until(lambda: not dialog._location_filter_helper._loader._request.busy)
            dialog.deleteLater()

    def test_real_dialog_captures_archive_scope_only_after_current_village_load(self):
        from Kavitro_dev.widgets.AddUpdatePropertyDialog import AddPropertyDialog
        self.add_import_fields()
        dialog = open_dialog(AddPropertyDialog)
        try:
            self.wait_until(lambda: dialog.county_combo.isEnabled())
            self.pick(dialog)
            dialog.city_combo.setCheckedItems(['First village'])
            self.assertIsNone(dialog._archive_scope_snapshot)
            self.assertFalse(dialog.run_checks_button.isEnabled())
            self.wait_until(lambda: dialog._archive_scope_snapshot is not None)
            self.assertEqual(dialog._archive_scope_snapshot.import_tunnused, frozenset({'1'}))
            self.assertTrue(dialog._archive_scope_snapshot.complete)
            self.assertTrue(dialog.run_checks_button.isEnabled())
            dialog.county_combo.setCurrentIndex(0)
            self.assertIsNone(dialog._archive_scope_snapshot)
            self.assertFalse(dialog.run_checks_button.isEnabled())
        finally:
            dialog.reject()
            self.wait_until(lambda: not dialog._location_filter_helper._loader._request.busy)
            dialog.deleteLater()


    def test_real_dialog_clears_a_finished_import_result_when_the_location_scope_changes(self):
        from Kavitro_dev.widgets.AddUpdatePropertyDialog import AddPropertyDialog
        from Kavitro_dev.modules.Property.FlowControllers import AddBatchRunner as runner_module
        self.add_import_fields()
        main = make_main_layer()
        created = lambda data, uses, raise_on_error=False: (
            'created' if data['cadastralUnit']['number'] == '1' else None)
        with patch.object(runner_module.BackendPropertyVerifier, 'verify_properties_by_cadastral_number',
                          return_value={'exists': False}), \
                patch.object(runner_module.ActiveLayersHelper, 'resolve_main_property_layer', return_value=main), \
                patch.object(runner_module.MainAddPropertiesFlow, 'add_single_property_item', side_effect=created), \
                patch.object(PropertyDataLoader, 'prepare_data_for_import_stage1', side_effect=lambda feature: (
                    {'cadastralUnit': {'number': feature[F.tunnus]}, 'address': {'street': 'Address',
                     'houseNumber': feature[F.tunnus]}}, feature[F.tunnus], [], '2025-01-01')), \
                patch.object(AddPropertyDialog, 'exec_', return_value=0):
            dialog = AddPropertyDialog()
            try:
                self.wait_until(lambda: dialog.county_combo.isEnabled())
                self.pick(dialog)
                self.wait_until(lambda: PropertyTableManager.row_count(dialog.properties_table) == 2)

                dialog._on_add_without_checks()
                self.wait_until(lambda: dialog._add_runner is None)
                self.assertEqual((dialog._add_summary['succeeded'], dialog._add_summary['failed']), (1, 1))
                self.assertTrue(dialog.add_progress_label.text())
                self.assertTrue(dialog.add_progress_label.isVisible())
                self.assertIn('2: ', dialog._add_errors_view.toPlainText())
                self.assertTrue(dialog._add_errors_view.isVisible())

                # A different county means the finished run no longer describes the table.
                dialog.county_combo.setCurrentIndex(dialog.county_combo.findData('B'))
                self.assertEqual(dialog.add_progress_label.text(), '')
                self.assertFalse(dialog.add_progress_label.isVisible())
                self.assertEqual(dialog.add_detail_label.text(), '')
                self.assertFalse(dialog.add_detail_label.isVisible())
                self.assertFalse(dialog._add_errors_view.isVisible())
                self.assertFalse(dialog.add_progress_bar.isVisible())
            finally:
                dialog.reject()
                self.wait_until(lambda: not dialog._location_filter_helper._loader._request.busy)
                dialog.deleteLater()

    def test_real_dialog_archive_plan_uses_background_lookup_and_continues_only_after_clean_apply(self):
        from Kavitro_dev.widgets import AddUpdatePropertyDialog as dialog_module
        from Kavitro_dev.modules.Property.FlowControllers import BackendVerifyWorker as worker_module
        dialog = self.open_dialog_with_village_scope()
        infos = {'7': {'exists': True, 'active_count': 1, 'active_ids': ['p7']},
                 '8': missing_info(),
                 '9': {'exists': None}}
        then = Mock()
        translate = dialog.lang_manager.translate
        try:
            with patch.object(worker_module.BackendPropertyVerifier, 'verify_properties_by_cadastral_number',
                              side_effect=lambda number: infos[number]), \
                    patch.object(dialog, '_archive_scope_is_current', return_value=True), \
                    patch.object(dialog_module.PropertyArchivePlanDialog, 'confirm', return_value=True) as confirm, \
                    patch.object(dialog_module.MainAddPropertiesFlow, 'archive_missing_from_import') as archive, \
                    patch.object(dialog_module.ModernMessageDialog, 'Warning_messages_modern'):
                # A clean apply archives only what the lookup allowed, then continues the add.
                archive.return_value = {'archived_backend': 1, 'moved_map': 3, 'errors': []}
                dialog._missing_from_import = {'7', '8', '9'}
                dialog._run_missing_cleanup_if_any(then)
                self.wait_until(lambda: then.called)
                rows = {row['tunnus']: row for row in confirm.call_args.kwargs['candidates']}
                self.assertEqual({tunnus: row['backend_allowed'] for tunnus, row in rows.items()},
                                 {'7': True, '8': False, '9': False})
                self.assertEqual(rows['8']['backend_label'], translate(K.PROPERTY_ARCHIVE_PLAN_BACKEND_MISSING))
                self.assertEqual(rows['9']['note'], translate(K.PROPERTY_ARCHIVE_PLAN_BACKEND_FAILED))
                archive.assert_called_once_with(['7', '8', '9'], backend_allowed={'7'}, main_layer=None)
                self.assertEqual(dialog._missing_from_import, set())
                self.assertFalse(dialog._add_in_progress)

                # A failed apply keeps its own message, drops the stale plan and does not continue.
                then.reset_mock()
                archive.return_value = {'archived_backend': 0, 'moved_map': 0, 'backend_failed': 1,
                                        'errors': ['boom']}
                dialog._missing_from_import = {'9'}
                dialog._run_missing_cleanup_if_any(then)
                self.wait_until(lambda: archive.call_count == 2)
            self.assertEqual(dialog.add_progress_label.text(), translate(
                K.ARCHIVE_MISSING_PROGRESS_RESULT).format(
                    archived=0, total=1, moved=0,
                    errors_suffix=translate(K.ARCHIVE_MISSING_PROGRESS_ERRORS_SUFFIX)))
            self.assertTrue(dialog.add_progress_label.isVisible())
            self.assertIsNone(dialog._archive_scope_snapshot)
            self.assertEqual(dialog._missing_from_import, set())
            then.assert_not_called()
        finally:
            self.close_dialog(dialog)

    def test_real_dialog_stays_locked_through_the_archive_confirm_and_apply(self):
        # b4: the dialog used to unlock the instant the background lookup finished --
        # before the user even saw the confirmation dialog, and before the archive call
        # that follows it. Both must still see the dialog locked.
        from Kavitro_dev.widgets import AddUpdatePropertyDialog as dialog_module
        from Kavitro_dev.modules.Property.FlowControllers import BackendVerifyWorker as worker_module
        dialog = self.open_dialog_with_village_scope()
        then = Mock()
        locked_at_confirm = []
        locked_at_archive = []

        def confirm_side_effect(**_kwargs):
            locked_at_confirm.append(dialog._add_in_progress and not dialog.location_filter_widget.isEnabled())
            return True

        def archive_side_effect(*_args, **_kwargs):
            locked_at_archive.append(dialog._add_in_progress and not dialog.location_filter_widget.isEnabled())
            return {'archived_backend': 0, 'moved_map': 0, 'errors': []}

        try:
            with patch.object(worker_module.BackendPropertyVerifier, 'verify_properties_by_cadastral_number',
                              return_value=missing_info()), \
                    patch.object(dialog, '_archive_scope_is_current', return_value=True), \
                    patch.object(dialog_module.PropertyArchivePlanDialog, 'confirm',
                                 side_effect=confirm_side_effect), \
                    patch.object(dialog_module.MainAddPropertiesFlow, 'archive_missing_from_import',
                                 side_effect=archive_side_effect), \
                    patch.object(dialog_module.ModernMessageDialog, 'Warning_messages_modern'):
                dialog._missing_from_import = {'8'}
                dialog._run_missing_cleanup_if_any(then)
                self.wait_until(lambda: then.called)

            self.assertEqual(locked_at_confirm, [True])
            self.assertEqual(locked_at_archive, [True])
            self.assertFalse(dialog._add_in_progress)
            self.assertTrue(dialog.location_filter_widget.isEnabled())
        finally:
            self.close_dialog(dialog)

    def test_real_dialog_archive_lookup_shows_progress_and_cancel_changes_nothing(self):
        from PyQt5 import sip
        from Kavitro_dev.widgets import AddUpdatePropertyDialog as dialog_module
        from Kavitro_dev.modules.Property.FlowControllers import BackendVerifyWorker as worker_module
        from Kavitro_dev.python.api_rate_limit import PROCESS_RATE_LIMITER
        dialog = self.open_dialog_with_village_scope()
        then = Mock()
        translate = dialog.lang_manager.translate

        def lookup(number):
            if number == '9':
                PROCESS_RATE_LIMITER._wait(30, 'rate_limit')
            return missing_info()

        try:
            with patch.object(worker_module.BackendPropertyVerifier, 'verify_properties_by_cadastral_number',
                              side_effect=lookup), \
                    patch.object(dialog, '_archive_scope_is_current', return_value=True), \
                    patch.object(dialog_module.PropertyArchivePlanDialog, 'confirm') as confirm, \
                    patch.object(dialog_module.MainAddPropertiesFlow, 'archive_missing_from_import') as archive:
                dialog._missing_from_import = {'8', '9'}
                dialog._run_missing_cleanup_if_any(then)
                # The call returns at once; lookups continue in the background with the add locked.
                self.assertTrue(dialog._add_in_progress)
                self.assertFalse(dialog.location_filter_widget.isEnabled())
                self.assertFalse(dialog.add_without_checks_button.isEnabled())
                self.assertTrue(dialog.cancel_button.isEnabled())
                self.wait_until(lambda: dialog.add_detail_label.isVisible())
                self.assertIn(dialog.add_detail_label.text(),
                              {translate(K.API_REQUEST_RATE_WAIT).format(seconds=s) for s in (29, 30)})
                self.assertEqual(dialog.add_progress_label.text(),
                                 translate(K.PROPERTY_ARCHIVE_LOOKUP_PROGRESS).format(done=1, total=2))
                self.assertEqual((dialog.add_progress_bar.value(), dialog.add_progress_bar.maximum()), (1, 2))
                thread = dialog._archive_lookup_controller._thread

                dialog._on_cancel_clicked()
                self.assertTrue(dialog.isVisible())
                self.assertIsNone(dialog._archive_lookup)
                self.assertFalse(dialog._add_in_progress)
                self.assertTrue(dialog.location_filter_widget.isEnabled())
                self.assertFalse(dialog.add_detail_label.isVisible())
                self.assertFalse(dialog.add_progress_bar.isVisible())
                self.assertEqual(dialog.add_progress_label.text(), translate(K.PROPERTY_ARCHIVE_LOOKUP_CANCELLED))
                # The interrupted pause ends at once instead of holding the request budget for 30 s.
                self.wait_until(lambda: sip.isdeleted(thread) or thread.isFinished())
                QTest.qWait(50)
            # Nothing was reviewed, archived or added; the plan stays available for another try.
            confirm.assert_not_called()
            archive.assert_not_called()
            then.assert_not_called()
            self.assertEqual(dialog._missing_from_import, {'8', '9'})
            self.assertIsNotNone(dialog._archive_scope_snapshot)
        finally:
            self.close_dialog(dialog)

    def test_real_dialog_rechecks_the_archive_scope_after_the_background_lookup(self):
        from Kavitro_dev.widgets import AddUpdatePropertyDialog as dialog_module
        from Kavitro_dev.modules.Property.FlowControllers import BackendVerifyWorker as worker_module
        dialog = self.open_dialog_with_village_scope()
        then = Mock()
        try:
            with patch.object(worker_module.BackendPropertyVerifier, 'verify_properties_by_cadastral_number',
                              return_value={'exists': False}), \
                    patch.object(dialog, '_archive_scope_is_current', side_effect=[True, False]), \
                    patch.object(dialog_module.PropertyArchivePlanDialog, 'confirm') as confirm, \
                    patch.object(dialog_module.MainAddPropertiesFlow, 'archive_missing_from_import') as archive, \
                    patch.object(dialog_module.ModernMessageDialog, 'Warning_messages_modern') as warning:
                dialog._missing_from_import = {'9'}
                dialog._run_missing_cleanup_if_any(then)
                self.wait_until(lambda: warning.called)
            # The import changed while the dialog was usable: warn instead of reviewing an old plan.
            self.assertEqual(warning.call_args.args[0],
                             dialog.lang_manager.translate(K.PROPERTY_ARCHIVE_PLAN_STALE_TITLE))
            confirm.assert_not_called()
            archive.assert_not_called()
            then.assert_not_called()
            self.assertIsNone(dialog._archive_scope_snapshot)
            self.assertFalse(dialog._add_in_progress)
        finally:
            self.close_dialog(dialog)


    def test_real_dialog_shows_check_rate_limit_wait_and_cancel_keeps_the_dialog_open(self):
        from PyQt5 import sip
        from Kavitro_dev.widgets.AddUpdatePropertyDialog import AddPropertyDialog
        from Kavitro_dev.modules.Property.FlowControllers import BackendVerifyWorker as worker_module
        from Kavitro_dev.python.api_rate_limit import PROCESS_RATE_LIMITER
        from Kavitro_dev.utils.MapTools.MapHelpers import ActiveLayersHelper
        self.add_import_fields()
        main = make_main_layer()
        # Every lookup hits a real 30 s rate-limit wait in the shared limiter.
        lookup = lambda number: PROCESS_RATE_LIMITER._wait(30, 'rate_limit') or missing_info()
        with patch.object(worker_module.BackendPropertyVerifier, 'verify_properties_by_cadastral_number',
                          side_effect=lookup), \
                patch.object(ActiveLayersHelper, 'resolve_main_property_layer', return_value=main), \
                patch.object(AddPropertyDialog, 'exec_', return_value=0):
            dialog = AddPropertyDialog()
            try:
                self.wait_until(lambda: dialog.county_combo.isEnabled())
                self.pick(dialog)
                self.wait_until(lambda: PropertyTableManager.row_count(dialog.properties_table) == 2)
                translate = dialog.lang_manager.translate

                dialog._on_run_checks_clicked()
                self.wait_until(lambda: dialog.add_detail_label.isVisible())
                self.assertIn(dialog.add_detail_label.text(),
                              {translate(K.API_REQUEST_RATE_WAIT).format(seconds=s) for s in (29, 30)})
                self.assertTrue(dialog.check_progress_bar.isVisible())
                self.assertFalse(dialog.run_checks_button.isEnabled())
                thread = dialog._backend_verify_controller._thread

                dialog._on_cancel_clicked()
                self.assertTrue(dialog.isVisible())
                self.assertFalse(dialog._checks_running)
                self.assertTrue(dialog.run_checks_button.isEnabled())
                self.assertFalse(dialog.add_button.isEnabled())
                self.assertFalse(dialog.check_progress_bar.isVisible())
                self.assertFalse(dialog.add_detail_label.isVisible())
                self.assertEqual(dialog.add_progress_label.text(),
                                 translate(K.PROPERTY_CHECK_CANCELLED).format(done=0, total=2))
                # The interrupted pause ends at once instead of holding the request budget for 30 s.
                self.wait_until(lambda: sip.isdeleted(thread) or thread.isFinished())
                QTest.qWait(50)
                self.assertFalse(dialog.add_detail_label.isVisible())
                self.assertFalse(dialog._checks_running)
            finally:
                dialog.reject()
                self.wait_until(lambda: not dialog._location_filter_helper._loader._request.busy)
                dialog.deleteLater()

    def test_location_mode_counts_table_rows_without_selection_controls(self):
        dialog = self.open_dialog_with_village_scope()
        count_text = dialog.lang_manager.translate(K.PROPERTY_TABLE_COUNT_TEMPLATE)
        try:
            # Every row is always added, so there is nothing to select.
            self.assertIsNone(dialog.select_all_btn)
            self.assertIsNone(dialog.clear_selection_btn)
            self.assertEqual(dialog.properties_table.selectionMode(), QTableView.NoSelection)
            self.assertEqual(dialog.selection_info.text(), count_text.format(count=1))
            self.assertTrue(dialog.add_without_checks_button.isEnabled())

            # While a new scope loads, the label and add button follow the cleared table.
            dialog.city_combo.setCheckedItems(['First village', 'Second village'])
            self.assertEqual(dialog.selection_info.text(), count_text.format(count=0))
            self.assertFalse(dialog.add_without_checks_button.isEnabled())
            self.wait_until(lambda: PropertyTableManager.row_count(dialog.properties_table) == 2)
            self.assertEqual(dialog.selection_info.text(), count_text.format(count=2))
            self.assertTrue(dialog.add_without_checks_button.isEnabled())
        finally:
            self.close_dialog(dialog)

    # ------------------------------------------------------------------
    # Button rules, captured as they are before they move into one owner
    # ------------------------------------------------------------------

    # (add_in_progress, checks_running, checks_completed) -> (add, add_without_checks, run_checks)
    PHASE_BUTTONS = {
        (False, False, False): (False, True, True),
        (False, False, True): (True, True, True),
        (False, True, False): (False, True, False),
        (False, True, True): (False, True, False),
        (True, False, False): (False, False, False),
        (True, False, True): (False, False, False),
        (True, True, False): (False, False, False),
        (True, True, True): (False, False, False),
    }

    def button_states(self, dialog, *, adding=False, checking=False, checked=False):
        """Put the dialog in one phase and read back what the three action buttons allow."""
        dialog._add_in_progress = adding
        dialog._checks_running = checking
        dialog._checks_completed_for_scope = checked
        dialog._update_add_button_state()
        dialog._update_run_checks_button()
        return (dialog.add_button.isEnabled(),
                dialog.add_without_checks_button.isEnabled(),
                dialog.run_checks_button.isEnabled())

    def test_button_rules_hold_for_every_phase_with_and_without_rows(self):
        dialog = self.open_dialog_with_village_scope()
        try:
            self.assertEqual(PropertyTableManager.row_count(dialog.properties_table), 1)
            for phase, expected in self.PHASE_BUTTONS.items():
                adding, checking, checked = phase
                self.assertEqual(
                    self.button_states(dialog, adding=adding, checking=checking, checked=checked),
                    expected, msg='rows=1 phase=' + str(phase))

            # An empty table leaves nothing to check and nothing to add, in every phase.
            with patch.object(PropertyTableManager, 'row_count', return_value=0):
                for phase in self.PHASE_BUTTONS:
                    adding, checking, checked = phase
                    self.assertEqual(
                        self.button_states(dialog, adding=adding, checking=checking, checked=checked),
                        (False, False, False), msg='rows=0 phase=' + str(phase))
        finally:
            self.close_dialog(dialog)

    def test_import_decisions_send_every_add_path_into_the_review_first(self):
        from Kavitro_dev.modules.Property.FlowControllers.AddBatchRunner import AddBatchRunner
        dialog = self.open_dialog_with_village_scope()
        try:
            dialog._deferred_additions = [{'tunnus': '1'}]
            dialog._decisions_from_import = True
            dialog._checks_completed_for_scope = True
            with patch.object(dialog, '_on_review_additions') as review, \
                    patch.object(AddBatchRunner, 'start') as start:
                dialog._on_add_clicked()
                dialog._on_add_without_checks()
                dialog._start_batch_add(dialog.properties_table, mode='without_checks')
                self.assertEqual(review.call_count, 3)
                start.assert_not_called()
                # The review's own run is the one path allowed past the redirect.
                dialog._start_batch_add(dialog.properties_table, mode='review', review_decisions=[])
                self.assertEqual(review.call_count, 3)
                start.assert_called_once()
            dialog._add_runner.cancel()
            self.wait_until(lambda: dialog._add_runner is None)

            # Decisions left by a check, not by an import, never redirect.
            dialog._deferred_additions = [{'tunnus': '1'}]
            dialog._decisions_from_import = False
            dialog._checks_completed_for_scope = True
            with patch.object(dialog, '_on_review_additions') as review, \
                    patch.object(AddBatchRunner, 'start') as start, \
                    patch.object(dialog, '_run_missing_cleanup_if_any', side_effect=lambda then: then()):
                dialog._on_add_clicked()
                review.assert_not_called()
                start.assert_called_once()
            dialog._add_runner.cancel()
            self.wait_until(lambda: dialog._add_runner is None)
        finally:
            self.close_dialog(dialog)

    def test_add_without_checks_needs_rows_but_not_a_finished_check(self):
        from Kavitro_dev.modules.Property.FlowControllers.AddBatchRunner import AddBatchRunner
        dialog = self.open_dialog_with_village_scope()
        try:
            with patch.object(AddBatchRunner, 'start') as start, \
                    patch.object(dialog, '_run_missing_cleanup_if_any', side_effect=lambda then: then()):
                # No finished check: the checked add is refused, the unchecked one is not.
                dialog._checks_completed_for_scope = False
                dialog._on_add_clicked()
                start.assert_not_called()
                dialog._on_add_without_checks()
                start.assert_called_once()
            dialog._add_runner.cancel()
            self.wait_until(lambda: dialog._add_runner is None)

            with patch.object(AddBatchRunner, 'start') as start, \
                    patch.object(PropertyTableManager, 'row_count', return_value=0), \
                    patch.object(dialog, '_run_missing_cleanup_if_any', side_effect=lambda then: then()):
                # An empty table refuses the add even when a check has finished.
                dialog._checks_completed_for_scope = True
                dialog._on_add_without_checks()
                start.assert_not_called()
        finally:
            dialog._checks_completed_for_scope = False
            self.close_dialog(dialog)

    def test_cancel_stops_the_innermost_running_work_first(self):
        dialog = self.open_dialog_with_village_scope()
        runner = Mock()
        try:
            with patch.object(dialog, '_cancel_archive_lookup') as archive, \
                    patch.object(dialog, '_cancel_attention_checks') as checks, \
                    patch.object(dialog, 'reject') as close:
                counts = lambda: (archive.call_count, checks.call_count,
                                  runner.cancel.call_count, close.call_count)
                dialog._archive_lookup = {'missing': [], 'backend_info': {}, 'then': None}
                dialog._checks_running = True
                dialog._add_runner = runner

                dialog._on_cancel_clicked()
                self.assertEqual(counts(), (1, 0, 0, 0))
                dialog._archive_lookup = None
                dialog._on_cancel_clicked()
                self.assertEqual(counts(), (1, 1, 0, 0))
                dialog._checks_running = False
                dialog._on_cancel_clicked()
                self.assertEqual(counts(), (1, 1, 1, 0))
                dialog._add_runner = None
                dialog._on_cancel_clicked()
                self.assertEqual(counts(), (1, 1, 1, 1))
        finally:
            dialog._add_runner = None
            self.close_dialog(dialog)

    def test_check_offers_decisions_before_adding_and_apply_takes_the_current_layers(self):
        from Kavitro_dev.widgets.AddUpdatePropertyDialog import AddPropertyDialog
        from Kavitro_dev.widgets.property_import_review_dialog import PropertyImportReviewDialog
        from Kavitro_dev.modules.Property.FlowControllers import BackendVerifyWorker as worker_module
        from Kavitro_dev.modules.Property.FlowControllers.AddBatchRunner import AddBatchRunner
        from Kavitro_dev.utils.MapTools.MapHelpers import ActiveLayersHelper
        self.add_import_fields()
        main = make_main_layer()
        lookup = lambda number: backend_info(
            number, address='Muudetud' if number == '1' else 'Address ' + number)
        with patch.object(worker_module.BackendPropertyVerifier, 'verify_properties_by_cadastral_number',
                          side_effect=lookup), \
                patch.object(ActiveLayersHelper, 'resolve_main_property_layer', return_value=main), \
                patch.object(AddPropertyDialog, 'exec_', return_value=0):
            dialog = AddPropertyDialog()
            try:
                self.wait_until(lambda: dialog.county_combo.isEnabled())
                self.pick(dialog)
                self.wait_until(lambda: PropertyTableManager.row_count(dialog.properties_table) == 2)

                dialog._on_run_checks_clicked()
                self.wait_until(lambda: dialog._checks_completed_for_scope)
                # The check alone offers the decision, before anything is written.
                self.assertEqual([item['tunnus'] for item in dialog._deferred_additions], ['1'])
                self.assertEqual(dialog._deferred_additions[0]['reason'], K.PROPERTY_ADD_BACKEND_DIFFERS)
                self.assertTrue(dialog.review_additions_button.isVisible())
                # A check result must not send the add buttons into the review.
                self.assertFalse(dialog._decisions_from_import)

                with patch.object(PropertyImportReviewDialog, 'exec_', return_value=1), \
                        patch.object(PropertyImportReviewDialog, 'selected_decisions', return_value={'1': 'apply'}), \
                        patch.object(AddBatchRunner, 'start'):
                    dialog._on_review_additions()
                item = dialog._add_runner._review_decisions['1']
                # The write needs the layer snapshot the check itself does not keep.
                self.assertEqual((item['source_id'], item['target_id']), (self.layer.id(), main.id()))
                self.assertTrue(item['feature'].isValid())
                dialog._add_runner.cancel()
                self.wait_until(lambda: dialog._add_runner is None)
            finally:
                self.close_dialog(dialog)

    def check_dialog_with_one_attention_row(self):
        """Two loaded rows, of which only '1' needs attention: the backend address differs
        and it is missing from the main layer. '2' agrees with both, so the attention
        filter is the only thing that can drop it."""

        from Kavitro_dev.widgets.AddUpdatePropertyDialog import AddPropertyDialog
        from Kavitro_dev.modules.Property.FlowControllers import BackendVerifyWorker as worker_module
        from Kavitro_dev.utils.MapTools.MapHelpers import ActiveLayersHelper
        self.add_import_fields()
        main = QgsVectorLayer(f'Polygon?crs=EPSG:3301&field={F.tunnus}:string&field={F.l_aadress}:string',
                              'Main', 'memory')
        kept = QgsFeature(main.fields())
        kept.setAttributes(['2', 'Address 2'])
        kept.setGeometry(QgsGeometry.fromWkt('POLYGON((200 0,210 0,210 10,200 10,200 0))'))
        main.dataProvider().addFeatures([kept])
        lookup = lambda number: {
            'exists': True, 'active_count': 1, 'LastUpdated': '2026-01-01',
            'property': {'id': 'p' + number, 'cadastralUnitNumber': number,
                         'displayAddress': 'Muudetud' if number == '1' else 'Address ' + number}}
        patches = [
            patch.object(worker_module.BackendPropertyVerifier, 'verify_properties_by_cadastral_number',
                         side_effect=lookup),
            patch.object(ActiveLayersHelper, 'resolve_main_property_layer', return_value=main),
            patch.object(AddPropertyDialog, 'exec_', return_value=0),
        ]
        for started in patches:
            started.start()
            self.addCleanup(started.stop)

        dialog = AddPropertyDialog()
        self.wait_until(lambda: dialog.county_combo.isEnabled())
        self.pick(dialog)
        self.wait_until(lambda: PropertyTableManager.row_count(dialog.properties_table) == 2)
        return dialog

    def table_ids(self, dialog):
        """What the table is showing, which is not the same as what it holds."""
        return [PropertyTableManager.get_cell_text(dialog.properties_table, row, 0)
                for row in PropertyTableManager.visible_rows(dialog.properties_table)]

    def backend_tip(self, dialog, tunnus):
        """The backend column's tooltip for a property, found by identity rather than by row."""
        from Kavitro_dev.utils.mapandproperties.PropertyTableManager import PropertyTableWidget
        row = self.table_ids(dialog).index(tunnus)
        return PropertyTableManager.get_cell_data(
            dialog.properties_table, row, PropertyTableWidget._COL_BACKEND_ATTENTION, role=Qt.ToolTipRole)

    def test_turning_the_attention_filter_off_keeps_the_finished_check_result(self):
        """b6: unticking "only needs attention" must not throw the finished check away.

        The filter used to remove rows from the model and every result was stored under a
        table row number, so the reload that brought the rows back dropped the finished
        check and the decisions that came with it.
        """

        dialog = self.check_dialog_with_one_attention_row()
        translate = dialog.lang_manager.translate
        differs = translate(K.PROPERTY_TOOLTIP_BACKEND_ISSUES).format(
            causes=translate(K.PROPERTY_ADD_BACKEND_DIFFERS))
        try:
            dialog._on_run_checks_clicked()
            self.wait_until(lambda: dialog._checks_completed_for_scope)

            # The finished check filtered the clean property away and offered a decision.
            self.assertEqual(self.table_ids(dialog), ['1'])
            self.assertTrue(dialog._table_filtered_to_attention)
            self.assertEqual([item['tunnus'] for item in dialog._deferred_additions], ['1'])
            self.assertEqual(self.backend_tip(dialog, '1'), differs)
            self.assertTrue(dialog.add_button.isEnabled())

            # The clean property was only hidden, so it is still there to show again.
            self.assertEqual(PropertyTableManager.row_count(dialog.properties_table), 2)

            # Unticking the box only widens what is shown; it decides nothing, and it
            # needs no reload, so it happens at once.
            dialog.attention_only_checkbox.setChecked(False)
            self.assertEqual(self.table_ids(dialog), ['1', '2'])

            # Everything the check established is still there, for both rows.
            self.assertEqual(self.backend_tip(dialog, '1'), differs)
            self.assertEqual(self.backend_tip(dialog, '2'), translate(K.PROPERTY_TOOLTIP_BACKEND_OK))
            self.assertEqual([item['tunnus'] for item in dialog._deferred_additions], ['1'])
            self.assertTrue(dialog._checks_completed_for_scope)
            self.assertTrue(dialog.add_button.isEnabled())
        finally:
            self.close_dialog(dialog)

    def test_the_attention_filter_narrows_what_gets_added(self):
        """A hidden row is not offered, so it must not quietly end up in the add scope.

        The filter used to delete rows, which narrowed the add scope as a side effect.
        Hiding them has to narrow it on purpose instead.
        """

        dialog = self.check_dialog_with_one_attention_row()
        table = dialog.properties_table
        count_text = dialog.lang_manager.translate(K.PROPERTY_TABLE_COUNT_TEMPLATE)

        def visible_tunnused():
            return [feature[F.tunnus] for feature in PropertyTableManager.get_visible_features(table)]

        try:
            dialog._on_run_checks_clicked()
            self.wait_until(lambda: dialog._checks_completed_for_scope)

            # Both rows are still in the table, but only the filtered one is on offer.
            self.assertEqual(PropertyTableManager.row_count(table), 2)
            self.assertEqual(visible_tunnused(), ['1'])
            self.assertEqual(dialog._current_target_count(), 1)
            self.assertEqual(dialog.selection_info.text(), count_text.format(count=1))

            dialog.attention_only_checkbox.setChecked(False)
            self.assertEqual(visible_tunnused(), ['1', '2'])
            self.assertEqual(dialog._current_target_count(), 2)
            self.assertEqual(dialog.selection_info.text(), count_text.format(count=2))
        finally:
            self.close_dialog(dialog)

    def test_the_visible_count_matches_the_visible_rows_without_walking_them(self):
        """The count is read off the header now, so it must not drift from the rows."""

        from Kavitro_dev.utils.mapandproperties.PropertyTableManager import PropertyTableWidget
        frame, table = PropertyTableWidget.create_properties_table()
        frame.setParent(self.window)
        manager = PropertyTableManager()

        def agrees(expected):
            self.assertEqual(PropertyTableManager.visible_row_count(table),
                             len(PropertyTableManager.visible_rows(table)))
            self.assertEqual(PropertyTableManager.visible_row_count(table), expected)

        manager.populate_properties_table([{'cadastral_id': str(n)} for n in range(50)], table)
        agrees(50)

        PropertyTableManager.show_only_rows(table, range(0, 50, 5))
        agrees(10)

        # A smaller table replacing a filtered one must not inherit its hidden rows.
        manager.populate_properties_table([{'cadastral_id': str(n)} for n in range(3)], table)
        agrees(3)

        PropertyTableManager.show_all_rows(table)
        agrees(3)

    def test_select_all_takes_the_rows_the_table_shows(self):
        """Selection mode is off in location mode, so this is where the rule is checked."""

        from Kavitro_dev.utils.mapandproperties.PropertyTableManager import PropertyTableWidget
        frame, table = PropertyTableWidget.create_properties_table()
        # Parented to the fixture window so it dies with it; a stray top-level widget
        # still pending deletion at interpreter shutdown crashes the run.
        frame.setParent(self.window)
        PropertyTableManager().populate_properties_table(
            [{'cadastral_id': str(number)} for number in (1, 2, 3)], table)
        PropertyTableManager.show_only_rows(table, [0, 2])

        PropertyTableManager.select_all(table)

        self.assertEqual(sorted(index.row() for index in table.selectionModel().selectedRows()), [0, 2])

    def test_check_treats_a_missing_cadastral_address_as_agreement_with_the_settlement(self):
        from qgis.core import NULL
        from Kavitro_dev.widgets.AddUpdatePropertyDialog import AddPropertyDialog
        from Kavitro_dev.modules.Property.FlowControllers import BackendVerifyWorker as worker_module
        from Kavitro_dev.utils.MapTools.MapHelpers import ActiveLayersHelper
        from Kavitro_dev.utils.mapandproperties.PropertyTableManager import PropertyTableWidget
        self.add_import_fields()
        address_index = self.layer.fields().lookupField(F.l_aadress)
        self.layer.dataProvider().changeAttributeValues(
            {feature.id(): {address_index: NULL} for feature in self.layer.getFeatures()})
        main = QgsVectorLayer(f'Polygon?crs=EPSG:3301&field={F.tunnus}:string&field={F.l_aadress}:string',
                              'Main', 'memory')
        kept = QgsFeature(main.fields())
        kept.setAttributes(['2', NULL])
        kept.setGeometry(QgsGeometry.fromWkt('POLYGON((200 0,210 0,210 10,200 10,200 0))'))
        main.dataProvider().addFeatures([kept])
        # Property 1 has no street on either side; property 2 got a street in the backend.
        shown = {'1': 'First village, Shared municipality, A', '2': 'Metsa tee 5, Second village, Shared municipality'}
        lookup = lambda number: {
            'exists': True, 'active_count': 1, 'LastUpdated': '2026-01-01',
            'property': {'id': 'p' + number, 'cadastralUnitNumber': number, 'displayAddress': shown[number]}}
        with patch.object(worker_module.BackendPropertyVerifier, 'verify_properties_by_cadastral_number',
                          side_effect=lookup), \
                patch.object(ActiveLayersHelper, 'resolve_main_property_layer', return_value=main), \
                patch.object(AddPropertyDialog, 'exec_', return_value=0):
            dialog = AddPropertyDialog()
            try:
                self.wait_until(lambda: dialog.county_combo.isEnabled())
                self.pick(dialog)
                self.wait_until(lambda: PropertyTableManager.row_count(dialog.properties_table) == 2)
                translate = dialog.lang_manager.translate

                dialog._on_run_checks_clicked()
                self.wait_until(lambda: dialog._checks_completed_for_scope)
                self.assertEqual([item['tunnus'] for item in dialog._deferred_additions], ['2'])
                decision = dialog._deferred_additions[0]
                self.assertEqual(decision['reason'], K.PROPERTY_IMPORT_ADDRESS_MISSING)
                # An empty main layer address is not shown as the text NULL.
                self.assertEqual(decision['main_address'], '')

                def tip(row):
                    return PropertyTableManager.get_cell_data(
                        dialog.properties_table, row, PropertyTableWidget._COL_BACKEND_ATTENTION, role=Qt.ToolTipRole)

                self.assertEqual(tip(0), translate(K.PROPERTY_TOOLTIP_BACKEND_OK))
                self.assertEqual(tip(1), translate(K.PROPERTY_TOOLTIP_BACKEND_ISSUES).format(
                    causes=translate(K.PROPERTY_IMPORT_ADDRESS_MISSING)))
            finally:
                self.close_dialog(dialog)

    def test_each_status_column_explains_itself_on_hover(self):
        from Kavitro_dev.widgets.AddUpdatePropertyDialog import AddPropertyDialog
        from Kavitro_dev.modules.Property.FlowControllers import BackendVerifyWorker as worker_module
        from Kavitro_dev.utils.MapTools.MapHelpers import ActiveLayersHelper
        from Kavitro_dev.utils.mapandproperties.PropertyTableManager import PropertyTableWidget
        self.add_import_fields()
        main = make_main_layer()
        lookup = lambda number: backend_info(
            number, address='Muudetud' if number == '1' else 'Address ' + number)
        with patch.object(worker_module.BackendPropertyVerifier, 'verify_properties_by_cadastral_number',
                          side_effect=lookup), \
                patch.object(ActiveLayersHelper, 'resolve_main_property_layer', return_value=main), \
                patch.object(AddPropertyDialog, 'exec_', return_value=0):
            dialog = AddPropertyDialog()
            try:
                self.wait_until(lambda: dialog.county_combo.isEnabled())
                self.pick(dialog)
                self.wait_until(lambda: PropertyTableManager.row_count(dialog.properties_table) == 2)
                translate = dialog.lang_manager.translate

                dialog._on_run_checks_clicked()
                self.wait_until(lambda: dialog._checks_completed_for_scope)

                def tip(row, column):
                    return PropertyTableManager.get_cell_data(
                        dialog.properties_table, row, column, role=Qt.ToolTipRole)

                # Each column names only its own reason instead of one shared list.
                self.assertEqual(tip(0, PropertyTableWidget._COL_BACKEND_ATTENTION),
                                 translate(K.PROPERTY_TOOLTIP_BACKEND_ISSUES).format(
                                     causes=translate(K.PROPERTY_ADD_BACKEND_DIFFERS)))
                self.assertEqual(tip(0, PropertyTableWidget._COL_MAIN_ATTENTION),
                                 translate(K.PROPERTY_TOOLTIP_MAIN_ISSUES).format(
                                     causes=translate(K.ATTENTION_CAUSE_MISSING_MAIN_LAYER)))
                self.assertEqual(tip(1, PropertyTableWidget._COL_BACKEND_ATTENTION),
                                 translate(K.PROPERTY_TOOLTIP_BACKEND_OK))
                # The archive columns say why they stay green for a row that is in the import.
                self.assertEqual(tip(0, PropertyTableWidget._COL_ARCHIVE_BACKEND),
                                 translate(K.PROPERTY_TOOLTIP_ARCHIVE_NONE))
                self.assertEqual(tip(0, PropertyTableWidget._COL_ARCHIVE_MAP),
                                 translate(K.PROPERTY_TOOLTIP_ARCHIVE_NONE))
            finally:
                self.close_dialog(dialog)

    def test_archive_plan_tooltips_render_when_a_row_is_flagged(self):
        # _archive_backend_plan/_archive_map_plan and their PLANNED translation keys looked
        # like dead code to an early "step 1" scan; they are read by _set_attention_row and
        # do produce the right icon/tooltip once a tunnus is flagged. This locks that in
        # directly on a row, because the properties table itself never shows a row for an
        # actual archive candidate -- those tunnus values are, by construction, always
        # absent from the import (see _compute_scoped_archive_plan), so nothing end-to-end
        # currently drives a real row through the PLANNED branch.
        from Kavitro_dev.widgets.AddUpdatePropertyDialog import AddPropertyDialog
        from Kavitro_dev.modules.Property.FlowControllers import BackendVerifyWorker as worker_module
        from Kavitro_dev.utils.MapTools.MapHelpers import ActiveLayersHelper
        from Kavitro_dev.utils.mapandproperties.PropertyTableManager import PropertyTableWidget
        self.add_import_fields()
        main = make_main_layer()
        with patch.object(worker_module.BackendPropertyVerifier, 'verify_properties_by_cadastral_number',
                          return_value=backend_info('1')), \
                patch.object(ActiveLayersHelper, 'resolve_main_property_layer', return_value=main), \
                patch.object(AddPropertyDialog, 'exec_', return_value=0):
            dialog = AddPropertyDialog()
            try:
                self.wait_until(lambda: dialog.county_combo.isEnabled())
                self.pick(dialog)
                self.wait_until(lambda: PropertyTableManager.row_count(dialog.properties_table) == 2)
                translate = dialog.lang_manager.translate

                dialog._on_run_checks_clicked()
                self.wait_until(lambda: dialog._checks_completed_for_scope)

                tunnus = PropertyTableManager.get_cell_text(dialog.properties_table, 0, 0)
                dialog._archive_backend_plan = {tunnus: True}
                dialog._archive_map_plan = {tunnus: True}
                dialog._update_row_attention_display(0)

                def tip(column):
                    return PropertyTableManager.get_cell_data(
                        dialog.properties_table, 0, column, role=Qt.ToolTipRole)

                self.assertEqual(tip(PropertyTableWidget._COL_ARCHIVE_BACKEND),
                                 translate(K.PROPERTY_TOOLTIP_ARCHIVE_BACKEND_PLANNED))
                self.assertEqual(tip(PropertyTableWidget._COL_ARCHIVE_MAP),
                                 translate(K.PROPERTY_TOOLTIP_ARCHIVE_MAP_PLANNED))
            finally:
                self.close_dialog(dialog)


if __name__ == '__main__':
    unittest.main()
