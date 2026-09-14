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
        from Kavitro_dev.modules.Property.FlowControllers.checked_add_runner import CheckedAddBatchRunner
        for name in (F.hkood, F.registr, F.muudet):
            self.layer.dataProvider().addAttributes([QgsField(name, QVariant.String)])
        self.layer.updateFields()
        with patch.object(AddPropertyDialog, 'exec_', return_value=0):
            dialog = AddPropertyDialog()
        try:
            self.wait_until(lambda: dialog.county_combo.isEnabled())
            with patch.object(CheckedAddBatchRunner, 'start') as start, \
                    patch.object(dialog, '_run_missing_cleanup_if_any', return_value=True):
                dialog._on_add_clicked()
                start.assert_not_called()
                dialog._checks_completed_for_scope = True
                dialog._on_add_clicked()
                start.assert_called_once()
            self.assertIsInstance(dialog._add_runner, CheckedAddBatchRunner)
            self.assertFalse(dialog.location_filter_widget.isEnabled())
            self.assertFalse(dialog.properties_table.isEnabled())
            runner = dialog._add_runner
            dialog._on_add_progress(0, 2, 'processing', '1')
            runner.waiting.emit(37.0, 'rate_limit')
            self.assertIn('37', dialog.add_progress_label.text())
            self.assertIn('1', dialog.add_progress_label.text())
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
            self.assertEqual(dialog._add_errors_view.toPlainText(), '1: Offline test error')
            self.assertTrue(dialog._add_errors_view.isVisible())
            dialog._on_add_finished({'canceled': True, 'done': 0, 'total': 2, 'succeeded': 0,
                                     'failed': 0, 'pending': 2, 'errors': [],
                                     'unfinished': {'tunnus': '1', 'message': 'Intended uses unfinished'}})
            self.assertEqual(dialog._add_errors_view.toPlainText(), '1: Intended uses unfinished')
            self.assertIn('0/2', dialog.add_progress_label.text())
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


if __name__ == '__main__':
    unittest.main()
