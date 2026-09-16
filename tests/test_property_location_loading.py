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
from PyQt5.QtWidgets import QTableView, QVBoxLayout, QWidget
from qgis.core import QgsApplication, QgsFeature, QgsField, QgsGeometry, QgsVectorLayer, QgsVectorLayerFeatureSource

from Kavitro_dev.constants.cadastral_fields import Katastriyksus as F
from Kavitro_dev.languages.language_manager import LanguageManager
from Kavitro_dev.languages.translation_keys import TranslationKeys as K
from Kavitro_dev.utils.MapTools.MapHelpers import MapHelpers
from Kavitro_dev.utils.mapandproperties.PropertyDataLoader import PropertyDataLoader
from Kavitro_dev.utils.mapandproperties.PropertyTableManager import PropertyTableManager
from Kavitro_dev.widgets.LocationFilterWidget import LocationFilterHelper, LocationFilterWidget


class PropertyLocationLoadingTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QgsApplication.instance() or QgsApplication([], False)
        QgsApplication.initQgis()
        if not QFontDatabase().families():
            QFontDatabase.addApplicationFont('C:/Windows/Fonts/segoeui.ttf')
            cls.app.setFont(QFont('Segoe UI', 9))

    def setUp(self):
        fields = [F.mk_nimi, F.ov_nimi, F.ay_nimi, F.tunnus, F.l_aadress, F.pindala]
        uri = 'Polygon?crs=EPSG:3301' + ''.join('&field=' + field + ':string' for field in fields)
        self.layer = QgsVectorLayer(uri, 'Offline location test', 'memory')
        self.assertTrue(self.layer.isValid())
        entries = [('A', 'Shared municipality', 'First village', '1'),
                   ('A', 'Shared municipality', 'Second village', '2'),
                   ('B', 'Shared municipality', 'First village', '3')]
        features = []
        for county, municipality, village, cadastral in entries:
            feature = QgsFeature(self.layer.fields())
            feature.setAttributes([county, municipality, village, cadastral, 'Address ' + cadastral, '100'])
            offset = int(cadastral) * 100
            feature.setGeometry(QgsGeometry.fromWkt(f'POLYGON(({offset} 0,{offset + 10} 0,{offset + 10} 10,{offset} 10,{offset} 0))'))
            features.append(feature)
        self.layer.dataProvider().addFeatures(features)
        self.window = QWidget()
        layout = QVBoxLayout(self.window)
        self.widget = LocationFilterWidget(LanguageManager('et'))
        layout.addWidget(self.widget)
        self.table = QTableView()
        layout.addWidget(self.table)
        self.completed, self.invalidated, self.stopped = Mock(), Mock(), Mock()
        self.helper = LocationFilterHelper(
            county_combo=self.widget.county_combo, municipality_combo=self.widget.municipality_combo,
            city_combo=self.widget.city_combo, properties_table=self.table,
            after_table_update=self.completed, stop_checks=self.stopped,
            invalidate_archive_scope=self.invalidated, update_add_button_state=Mock(),
            stop_map_update=Mock(), status_widget=self.widget, parent=self.window)
        self.helper.connect_signals()
        self.resolve = patch.object(MapHelpers, 'get_layer_by_tag', return_value=self.layer)
        self.resolve_mock = self.resolve.start()
        self.preview = patch.object(MapHelpers, 'apply_scope_preview')
        self.preview_mock = self.preview.start()
        self.window.resize(700, 450)
        self.window.show()

    def tearDown(self):
        self.helper.close()
        self.wait_until(lambda: not self.helper._loader._request.busy)
        self.window.close()
        self.window.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)
        self.preview.stop()
        self.resolve.stop()

    def wait_until(self, condition):
        for _ in range(200):
            if condition():
                return
            QTest.qWait(10)
        self.fail('Location read did not complete')

    def load_index(self):
        self.helper.load_counties(self.layer)
        self.wait_until(lambda: self.widget.county_combo.isEnabled())

    def choose_municipality(self, county='A'):
        self.widget.county_combo.setCurrentIndex(self.widget.county_combo.findData(county))
        combo = self.widget.municipality_combo
        combo.setCurrentIndex(combo.findData('Shared municipality'))

    def ids(self):
        return {PropertyTableManager.get_cell_text(self.table, row, 0)
                for row in range(PropertyTableManager.row_count(self.table))}

    def click_village(self, row):
        combo = self.widget.city_combo
        combo.showPopup()
        QTest.qWait(10)
        view = combo.view()
        QTest.mouseClick(view.viewport(), Qt.LeftButton, pos=view.visualRect(view.model().index(row, 0)).center())
        combo.hidePopup()

    def test_hierarchy_is_scoped_and_cached_between_choices(self):
        with patch.object(PropertyDataLoader, 'read_location_index', wraps=PropertyDataLoader.read_location_index) as read:
            self.load_index()
            self.choose_municipality()
            self.wait_until(lambda: self.ids() == {'1', '2'})
            self.assertEqual(self.widget.city_combo.count(), 2)
            self.choose_municipality('B')
            self.wait_until(lambda: self.ids() == {'3'})
            self.assertEqual(self.widget.city_combo.count(), 1)
        self.assertEqual(read.call_count, 1)

    def test_slow_index_keeps_gui_running_and_shows_busy_state(self):
        entered, release = threading.Event(), threading.Event()
        read = PropertyDataLoader.read_location_index
        threads, pulses = [], []
        def delayed(source, cancelled):
            threads.append(QThread.currentThread())
            entered.set()
            release.wait(2)
            return read(source, cancelled)
        with patch.object(PropertyDataLoader, 'read_location_index', side_effect=delayed):
            try:
                self.helper.load_counties(self.layer)
                self.wait_until(entered.is_set)
                QTimer.singleShot(0, lambda: pulses.append(True))
                QTest.qWait(40)
                self.assertEqual(pulses, [True])
                self.assertFalse(self.widget.county_combo.isEnabled())
                self.assertTrue(self.widget.loading_indicator.isVisible())
                self.assertIn('valikuid', self.widget.status_label.text())
                self.assertNotEqual(threads[0], self.app.thread())
            finally:
                release.set()
            self.wait_until(lambda: self.widget.county_combo.isEnabled())
        self.assertTrue(self.widget.loading_indicator.isHidden())

    def test_village_results_keep_full_scope_and_map_uses_precomputed_ids_and_bounds(self):
        self.load_index()
        self.choose_municipality()
        self.widget.city_combo.setCheckedItems(['First village'])
        self.wait_until(lambda: self.ids() == {'1'})
        self.assertEqual(self.preview_mock.call_args.kwargs, {'select': True})
        layer, ids, extent = self.preview_mock.call_args.args
        self.assertIs(layer, self.layer)
        self.assertEqual(len(ids), 1)
        self.assertEqual((extent.xMinimum(), extent.xMaximum()), (100, 110))
        feature = PropertyTableManager.get_all_features(self.table)[0]
        self.assertFalse(feature.hasGeometry())
        self.assertEqual(feature[F.mk_nimi], 'A')
        self.assertIn('1', self.widget.status_label.text())

    def test_fast_village_changes_are_debounced(self):
        self.load_index()
        self.choose_municipality()
        self.wait_until(lambda: self.ids() == {'1', '2'})
        with patch.object(PropertyDataLoader, 'read_location_scope', wraps=PropertyDataLoader.read_location_scope) as read:
            self.widget.city_combo.setCheckedItems(['First village'])
            self.widget.city_combo.setCheckedItems(['First village', 'Second village'])
            self.click_village(0)
            self.assertEqual(self.ids(), set())
            self.wait_until(lambda: self.ids() == {'2'})
            self.assertEqual(read.call_count, 1)

    def test_unchecking_last_village_reloads_municipality_with_current_behavior(self):
        self.load_index()
        self.choose_municipality()
        self.widget.city_combo.setCheckedItems(['First village'])
        self.wait_until(lambda: self.ids() == {'1'})
        self.click_village(0)
        self.assertEqual(self.ids(), set())
        self.wait_until(lambda: self.ids() == {'1', '2'})

    def test_keyboard_village_check_updates_table(self):
        self.load_index()
        self.choose_municipality()
        self.wait_until(lambda: self.ids() == {'1', '2'})
        combo = self.widget.city_combo
        combo.showPopup()
        view = combo.view()
        view.setCurrentIndex(view.model().index(0, 0))
        QTest.keyClick(view, Qt.Key_Space)
        self.assertEqual(combo.checkedItems(), ['First village'])
        combo.hidePopup()
        self.wait_until(lambda: self.ids() == {'1'})
        combo.showPopup()
        view.setCurrentIndex(view.model().index(0, 0))
        QTest.keyClick(view, Qt.Key_Space)
        self.assertEqual(combo.checkedItems(), [])
        combo.hidePopup()
        self.wait_until(lambda: self.ids() == {'1', '2'})

    def test_refresh_keeps_scope_and_reads_new_rows_without_rebuilding_whole_index(self):
        self.load_index()
        self.choose_municipality()
        self.widget.city_combo.setCheckedItems(['First village'])
        self.wait_until(lambda: self.ids() == {'1'})
        scope = self.helper._scope()
        feature = QgsFeature(self.layer.fields())
        feature.setAttributes(['A', 'Shared municipality', 'First village', '4', 'New address', '100'])
        feature.setGeometry(QgsGeometry.fromWkt('POLYGON((400 0,410 0,410 10,400 10,400 0))'))
        self.layer.dataProvider().addFeatures([feature])
        self.assertEqual(self.ids(), {'1'})
        before = self.invalidated.call_count
        with patch.object(PropertyDataLoader, 'read_location_index') as index_read:
            self.widget.refresh_button.click()
            self.assertEqual(self.ids(), set())
            self.assertEqual(self.helper._scope(), scope)
            self.wait_until(lambda: self.ids() == {'1', '4'})
            index_read.assert_not_called()
        self.assertGreater(self.invalidated.call_count, before)
        self.assertFalse(self.widget.refresh_button.icon().isNull())
        self.assertTrue(self.widget.refresh_button.accessibleName())

    def test_refresh_replaces_in_flight_read_with_current_scope(self):
        self.load_index()
        self.choose_municipality()
        self.wait_until(lambda: self.ids() == {'1', '2'})
        entered = threading.Event()
        read = PropertyDataLoader.read_location_scope
        calls = []
        def delayed(source, cancelled, scope, include_properties):
            calls.append(scope)
            if len(calls) == 1:
                entered.set()
                cancelled.wait(2)
            return read(source, cancelled, scope, include_properties)
        with patch.object(PropertyDataLoader, 'read_location_scope', side_effect=delayed):
            self.widget.city_combo.setCheckedItems(['First village'])
            self.wait_until(entered.is_set)
            self.widget.refresh_button.click()
            self.assertTrue(self.widget.loading_indicator.isVisible())
            self.wait_until(lambda: self.ids() == {'1'})
        self.assertEqual(calls, [self.helper._scope(), self.helper._scope()])

    def test_data_changes_invalidate_index_table_and_archive_scope(self):
        self.load_index()
        self.choose_municipality()
        self.wait_until(lambda: bool(self.ids()))
        previous = self.invalidated.call_count
        self.layer.dataChanged.emit()
        self.assertEqual(self.ids(), set())
        self.assertGreater(self.invalidated.call_count, previous)
        self.wait_until(lambda: self.widget.county_combo.isEnabled())
        self.assertEqual(self.widget.county_combo.currentData(), '')

    def test_new_scope_cancels_slow_read_and_never_publishes_partial_rows(self):
        self.load_index()
        entered = threading.Event()
        original = PropertyDataLoader.read_location_scope
        def slow(source, cancelled, scope, include_properties):
            if scope[0] == 'A':
                entered.set()
                cancelled.wait(2)
            return original(source, cancelled, scope, include_properties)
        with patch.object(PropertyDataLoader, 'read_location_scope', side_effect=slow):
            self.choose_municipality()
            self.wait_until(entered.is_set)
            self.assertEqual(self.ids(), set())
            self.completed.assert_not_called()
            self.choose_municipality('B')
            self.wait_until(lambda: self.ids() == {'3'})
        self.assertEqual(self.completed.call_count, 1)
        self.assertTrue(self.invalidated.called)

    def test_reset_county_clears_descendants_and_invalidates_completed_scope(self):
        self.load_index()
        self.choose_municipality()
        self.wait_until(lambda: bool(self.ids()))
        before = self.completed.call_count
        self.widget.county_combo.setCurrentIndex(0)
        QTest.qWait(30)
        self.assertEqual(self.ids(), set())
        self.assertFalse(self.widget.municipality_combo.isEnabled())
        self.assertFalse(self.widget.city_combo.isEnabled())
        self.assertEqual(self.completed.call_count, before)

    def test_loading_error_is_visible_and_retry_works(self):
        self.load_index()
        with patch.object(PropertyDataLoader, 'read_location_scope', side_effect=RuntimeError('Cannot read source')):
            self.choose_municipality()
            self.wait_until(lambda: self.widget.retry_button.isVisible())
        self.assertEqual(self.ids(), set())
        self.completed.assert_not_called()
        self.assertTrue(self.widget.loading_indicator.isHidden())
        self.assertEqual(self.widget.status_label.text(), self.widget.lang_manager.translate(K.LOCATION_LOAD_FAILED))
        self.widget.retry_button.click()
        self.wait_until(lambda: self.ids() == {'1', '2'})
        self.assertFalse(self.widget.retry_button.isVisible())

    def test_close_while_loading_cancels_result(self):
        self.load_index()
        entered = threading.Event()
        original = PropertyDataLoader.read_location_scope
        def slow(source, cancelled, scope, include_properties):
            entered.set()
            cancelled.wait(2)
            return original(source, cancelled, scope, include_properties)
        with patch.object(PropertyDataLoader, 'read_location_scope', side_effect=slow):
            self.choose_municipality()
            self.wait_until(entered.is_set)
            self.helper.close()
            self.wait_until(lambda: not self.helper._loader._request.busy)
        self.assertEqual(self.ids(), set())
        self.completed.assert_not_called()
        self.preview_mock.assert_not_called()

    def test_replaced_import_layer_cannot_receive_old_result(self):
        self.load_index()
        entered, release = threading.Event(), threading.Event()
        original = PropertyDataLoader.read_location_scope
        def slow(source, cancelled, scope, include_properties):
            entered.set()
            release.wait(2)
            return original(source, cancelled, scope, include_properties)
        with patch.object(PropertyDataLoader, 'read_location_scope', side_effect=slow):
            try:
                self.choose_municipality()
                self.wait_until(entered.is_set)
                self.resolve_mock.return_value = None
            finally:
                release.set()
            self.wait_until(lambda: self.widget.retry_button.isVisible())
        self.assertEqual(self.ids(), set())
        self.completed.assert_not_called()
        replacement = self.layer.clone()
        self.resolve_mock.return_value = replacement
        self.widget.retry_button.click()
        self.wait_until(lambda: self.widget.county_combo.isEnabled())
        self.assertIs(self.helper._layer, replacement)
        self.assertEqual(self.widget.county_combo.currentData(), '')

    def test_snapshot_is_created_on_gui_and_result_applied_on_gui(self):
        original = QgsVectorLayerFeatureSource
        threads = []
        def snapshot(layer):
            threads.append(QThread.currentThread())
            return original(layer)
        self.completed.side_effect = lambda _table: threads.append(QThread.currentThread())
        with patch('Kavitro_dev.utils.mapandproperties.PropertyUpdateFlowCoordinator.QgsVectorLayerFeatureSource', side_effect=snapshot):
            self.load_index()
            self.choose_municipality()
            self.wait_until(lambda: bool(self.ids()))
        self.assertGreaterEqual(len(threads), 3)
        self.assertTrue(all(thread == self.app.thread() for thread in threads))

    def test_checked_add_dialog_uses_background_runner_and_shows_failures(self):
        from Kavitro_dev.widgets.AddUpdatePropertyDialog import AddPropertyDialog
        from Kavitro_dev.modules.Property.FlowControllers.AddBatchRunner import AddBatchRunner
        for name in (F.hkood, F.registr, F.muudet):
            self.layer.dataProvider().addAttributes([QgsField(name, QVariant.String)])
        self.layer.updateFields()
        with patch.object(AddPropertyDialog, 'exec_', return_value=0):
            dialog = AddPropertyDialog()
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
        for name in (F.hkood, F.registr, F.muudet):
            self.layer.dataProvider().addAttributes([QgsField(name, QVariant.String)])
        self.layer.updateFields()
        self.layer.dataProvider().changeAttributeValues({feature.id(): {
            self.layer.fields().lookupField(F.muudet): '2025-01-01'} for feature in self.layer.getFeatures()})
        main = QgsVectorLayer('Polygon?crs=EPSG:3301&field=tunnus:string', 'Main', 'memory')
        lookup = lambda number: ({'exists': True, 'active_count': 1, 'LastUpdated': '2026-01-01',
            'property': {'id': 'known', 'cadastralUnitNumber': number, 'displayAddress': 'Different'}}
            if number == '1' else {'exists': False})
        with patch.object(runner_module.BackendPropertyVerifier, 'verify_properties_by_cadastral_number', side_effect=lookup), \
                patch.object(runner_module.ActiveLayersHelper, 'resolve_main_property_layer', return_value=main), \
                patch.object(runner_module.MainAddPropertiesFlow, 'add_single_property_item', return_value='created') as create, \
                patch.object(runner_module.UpdatePropertyData, 'update_single_property_item') as update, \
                patch.object(AddPropertyDialog, 'exec_', return_value=0):
            dialog = AddPropertyDialog()
            try:
                self.wait_until(lambda: dialog.county_combo.isEnabled())
                dialog.county_combo.setCurrentIndex(dialog.county_combo.findData('A'))
                combo = dialog.municipality_combo
                combo.setCurrentIndex(combo.findData('Shared municipality'))
                self.wait_until(lambda: PropertyTableManager.row_count(dialog.properties_table) == 2)
                self.assertEqual(PropertyTableManager.get_payload_field_text(dialog.properties_table, 0, 0, F.muudet),
                                 '2025-01-01')
                dialog._on_run_checks_clicked()
                self.wait_until(lambda: dialog._checks_completed_for_scope)
                self.assertIn(K.PROPERTY_ADD_BACKEND_DIFFERS, dialog._backend_compare_causes_by_row[0])
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
        for name in (F.hkood, F.registr, F.muudet):
            self.layer.dataProvider().addAttributes([QgsField(name, QVariant.String)])
        self.layer.updateFields()
        with patch.object(AddPropertyDialog, 'exec_', return_value=0):
            dialog = AddPropertyDialog()
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
        for name in (F.hkood, F.registr, F.muudet):
            self.layer.dataProvider().addAttributes([QgsField(name, QVariant.String)])
        self.layer.updateFields()
        with patch.object(AddPropertyDialog, 'exec_', return_value=0):
            dialog = AddPropertyDialog()
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
        for name in (F.hkood, F.registr, F.muudet):
            self.layer.dataProvider().addAttributes([QgsField(name, QVariant.String)])
        self.layer.updateFields()
        with patch.object(AddPropertyDialog, 'exec_', return_value=0):
            dialog = AddPropertyDialog()
        try:
            self.wait_until(lambda: dialog.county_combo.isEnabled())
            dialog.county_combo.setCurrentIndex(dialog.county_combo.findData('A'))
            dialog.municipality_combo.setCurrentIndex(dialog.municipality_combo.findData('Shared municipality'))
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
        for name in (F.hkood, F.registr, F.muudet):
            self.layer.dataProvider().addAttributes([QgsField(name, QVariant.String)])
        self.layer.updateFields()
        main = QgsVectorLayer('Polygon?crs=EPSG:3301&field=tunnus:string', 'Main', 'memory')
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
                dialog.county_combo.setCurrentIndex(dialog.county_combo.findData('A'))
                combo = dialog.municipality_combo
                combo.setCurrentIndex(combo.findData('Shared municipality'))
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

    def open_dialog_with_village_scope(self):
        from Kavitro_dev.widgets.AddUpdatePropertyDialog import AddPropertyDialog
        for name in (F.hkood, F.registr, F.muudet):
            self.layer.dataProvider().addAttributes([QgsField(name, QVariant.String)])
        self.layer.updateFields()
        with patch.object(AddPropertyDialog, 'exec_', return_value=0):
            dialog = AddPropertyDialog()
        self.wait_until(lambda: dialog.county_combo.isEnabled())
        dialog.county_combo.setCurrentIndex(dialog.county_combo.findData('A'))
        dialog.municipality_combo.setCurrentIndex(dialog.municipality_combo.findData('Shared municipality'))
        dialog.city_combo.setCheckedItems(['First village'])
        self.wait_until(lambda: dialog._archive_scope_snapshot is not None)
        return dialog

    def close_dialog(self, dialog):
        dialog.reject()
        self.wait_until(lambda: not dialog._location_filter_helper._loader._request.busy)
        dialog.deleteLater()

    def test_real_dialog_archive_plan_uses_background_lookup_and_continues_only_after_clean_apply(self):
        from Kavitro_dev.widgets import AddUpdatePropertyDialog as dialog_module
        from Kavitro_dev.modules.Property.FlowControllers import BackendVerifyWorker as worker_module
        dialog = self.open_dialog_with_village_scope()
        infos = {'7': {'exists': True, 'active_count': 1, 'active_ids': ['p7']},
                 '8': {'exists': False},
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
                archive.assert_called_once_with(['7', '8', '9'], backend_allowed={'7'})
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
            return {'exists': False}

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
        for name in (F.hkood, F.registr, F.muudet):
            self.layer.dataProvider().addAttributes([QgsField(name, QVariant.String)])
        self.layer.updateFields()
        main = QgsVectorLayer('Polygon?crs=EPSG:3301&field=tunnus:string', 'Main', 'memory')
        # Every lookup hits a real 30 s rate-limit wait in the shared limiter.
        lookup = lambda number: PROCESS_RATE_LIMITER._wait(30, 'rate_limit') or {'exists': False}
        with patch.object(worker_module.BackendPropertyVerifier, 'verify_properties_by_cadastral_number',
                          side_effect=lookup), \
                patch.object(ActiveLayersHelper, 'resolve_main_property_layer', return_value=main), \
                patch.object(AddPropertyDialog, 'exec_', return_value=0):
            dialog = AddPropertyDialog()
            try:
                self.wait_until(lambda: dialog.county_combo.isEnabled())
                dialog.county_combo.setCurrentIndex(dialog.county_combo.findData('A'))
                combo = dialog.municipality_combo
                combo.setCurrentIndex(combo.findData('Shared municipality'))
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

    def test_check_offers_decisions_before_adding_and_apply_takes_the_current_layers(self):
        from Kavitro_dev.widgets.AddUpdatePropertyDialog import AddPropertyDialog
        from Kavitro_dev.widgets.property_import_review_dialog import PropertyImportReviewDialog
        from Kavitro_dev.modules.Property.FlowControllers import BackendVerifyWorker as worker_module
        from Kavitro_dev.modules.Property.FlowControllers.AddBatchRunner import AddBatchRunner
        from Kavitro_dev.utils.MapTools.MapHelpers import ActiveLayersHelper
        for name in (F.hkood, F.registr, F.muudet):
            self.layer.dataProvider().addAttributes([QgsField(name, QVariant.String)])
        self.layer.updateFields()
        main = QgsVectorLayer('Polygon?crs=EPSG:3301&field=tunnus:string', 'Main', 'memory')
        lookup = lambda number: {
            'exists': True, 'active_count': 1, 'LastUpdated': '2026-01-01',
            'property': {'id': 'known', 'cadastralUnitNumber': number,
                         'displayAddress': 'Muudetud' if number == '1' else 'Address ' + number}}
        with patch.object(worker_module.BackendPropertyVerifier, 'verify_properties_by_cadastral_number',
                          side_effect=lookup), \
                patch.object(ActiveLayersHelper, 'resolve_main_property_layer', return_value=main), \
                patch.object(AddPropertyDialog, 'exec_', return_value=0):
            dialog = AddPropertyDialog()
            try:
                self.wait_until(lambda: dialog.county_combo.isEnabled())
                dialog.county_combo.setCurrentIndex(dialog.county_combo.findData('A'))
                combo = dialog.municipality_combo
                combo.setCurrentIndex(combo.findData('Shared municipality'))
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

    def test_import_review_sets_the_same_decision_for_every_property(self):
        from Kavitro_dev.widgets.property_import_review_dialog import PropertyImportReviewDialog
        decisions = [{'tunnus': '1', 'reason': K.PROPERTY_ADD_BACKEND_DIFFERS, 'backend_info': {}},
                     {'tunnus': '2', 'reason': K.PROPERTY_ADD_BACKEND_DIFFERS, 'backend_info': {}},
                     {'tunnus': '3', 'reason': K.ATTENTION_CAUSE_ARCHIVED_ONLY, 'backend_info': {}}]
        dialog = PropertyImportReviewDialog(decisions, lang_manager=LanguageManager('et'))
        try:
            self.assertFalse(dialog.confirm.isEnabled())

            # Overwriting is offered only for address conflicts; the archived match keeps its choice.
            dialog.bulk_choice.setCurrentIndex(dialog.bulk_choice.findData('apply'))
            dialog._set_all()
            self.assertEqual(dialog.selected_decisions(), {'1': 'apply', '2': 'apply'})
            self.assertTrue(dialog.confirm.isEnabled())
            self.assertIn('1', dialog.bulk_note.text())

            # Keeping the existing record is available for every row.
            dialog.bulk_choice.setCurrentIndex(dialog.bulk_choice.findData('keep'))
            dialog._set_all()
            self.assertEqual(dialog.selected_decisions(), {'1': 'keep', '2': 'keep', '3': 'keep'})
            self.assertEqual(dialog.bulk_note.text(), '')
        finally:
            dialog.deleteLater()

    def test_property_table_headers_come_from_translations_in_both_languages(self):
        from Kavitro_dev.languages import en as en_module
        from Kavitro_dev.languages import et as et_module
        from Kavitro_dev.utils.mapandproperties.PropertyTableManager import PropertyTableWidget

        keys = (K.CADASTRAL_ID, K.ADDRESS, K.AREA, K.SETTLEMENT, K.PROPERTY_COLUMN_BACKEND,
                K.PROPERTY_COLUMN_MAIN_LAYER, K.PROPERTY_COLUMN_ARCHIVE_BACKEND, K.PROPERTY_COLUMN_ARCHIVE_MAP)
        lang = LanguageManager()
        self.assertEqual(PropertyTableWidget._headers(), [lang.translate(key) for key in keys])
        # Strict lookup raises on a missing key, so every language must carry all of them.
        for translations in (et_module.TRANSLATIONS, en_module.TRANSLATIONS):
            self.assertEqual([key for key in keys if key not in translations], [])


if __name__ == '__main__':
    unittest.main()
