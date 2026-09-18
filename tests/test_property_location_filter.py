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


class PropertyLocationFilterTest(LocationFilterTestCase):
    """County, municipality and settlement choices: what they load, cache and cancel."""

    def test_hierarchy_is_scoped_and_cached_between_choices(self):
        with patch.object(PropertyDataLoader, 'read_counties', wraps=PropertyDataLoader.read_counties) as counties:
            self.load_index()
            self.choose_municipality()
            self.wait_until(lambda: self.ids() == {'1', '2'})
            self.assertEqual(self.widget.city_combo.count(), 2)
            self.choose_municipality('B')
            self.wait_until(lambda: self.ids() == {'3'})
            self.assertEqual(self.widget.city_combo.count(), 1)
            # A county that was already read offers its municipalities at once.
            self.widget.county_combo.setCurrentIndex(self.widget.county_combo.findData('A'))
            self.assertGreaterEqual(self.widget.municipality_combo.findData('Shared municipality'), 0)
        self.assertEqual(counties.call_count, 1)

    def test_counties_come_from_distinct_values_without_a_background_read(self):
        with patch.object(PropertyDataLoader, 'read_location_scope') as scope_read:
            self.load_index()
        combo = self.widget.county_combo
        self.assertEqual([combo.itemData(index) for index in range(1, combo.count())], ['A', 'B'])
        self.assertFalse(self.widget.municipality_combo.isEnabled())
        scope_read.assert_not_called()

    def test_slow_county_choices_keep_gui_running_and_show_busy_state(self):
        entered, release = threading.Event(), threading.Event()
        read = PropertyDataLoader.read_location_scope
        threads, pulses = [], []

        def delayed(source, cancelled, scope, include_properties):
            if not scope[1]:
                threads.append(QThread.currentThread())
                entered.set()
                release.wait(2)
            return read(source, cancelled, scope, include_properties)

        self.load_index()
        with patch.object(PropertyDataLoader, 'read_location_scope', side_effect=delayed):
            try:
                self.widget.county_combo.setCurrentIndex(self.widget.county_combo.findData('A'))
                self.wait_until(entered.is_set)
                QTimer.singleShot(0, lambda: pulses.append(True))
                QTest.qWait(40)
                self.assertEqual(pulses, [True])
                self.assertFalse(self.widget.municipality_combo.isEnabled())
                self.assertTrue(self.widget.loading_indicator.isVisible())
                self.assertIn('valikuid', self.widget.status_label.text())
                self.assertNotEqual(threads[0], self.app.thread())
            finally:
                release.set()
            self.wait_until(lambda: self.widget.municipality_combo.isEnabled())
        self.assertGreaterEqual(self.widget.municipality_combo.findData('Shared municipality'), 0)
        self.assertTrue(self.widget.loading_indicator.isHidden())

    def test_failed_county_choices_show_retry_and_retry_loads_them(self):
        self.load_index()
        original = PropertyDataLoader.read_location_scope
        attempts = []

        def failing_once(source, cancelled, scope, include_properties):
            if not scope[1] and not attempts:
                attempts.append(scope)
                raise RuntimeError('Cannot read source')
            return original(source, cancelled, scope, include_properties)

        with patch.object(PropertyDataLoader, 'read_location_scope', side_effect=failing_once):
            self.widget.county_combo.setCurrentIndex(self.widget.county_combo.findData('A'))
            self.wait_until(lambda: self.widget.retry_button.isVisible())
            self.assertFalse(self.widget.municipality_combo.isEnabled())
            self.widget.retry_button.click()
            self.wait_until(lambda: self.widget.municipality_combo.findData('Shared municipality') >= 0)
        self.assertTrue(self.widget.municipality_combo.isEnabled())

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

    def test_refresh_keeps_scope_and_reads_new_rows_without_reloading_counties(self):
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
        with patch.object(PropertyDataLoader, 'read_counties') as counties_read:
            self.widget.refresh_button.click()
            self.assertEqual(self.ids(), set())
            self.assertEqual(self.helper._scope(), scope)
            self.wait_until(lambda: self.ids() == {'1', '4'})
            counties_read.assert_not_called()
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
            if scope[0] == 'A' and scope[1]:
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
        original = PropertyDataLoader.read_location_scope

        def failing(source, cancelled, scope, include_properties):
            if scope[1]:
                raise RuntimeError('Cannot read source')
            return original(source, cancelled, scope, include_properties)

        with patch.object(PropertyDataLoader, 'read_location_scope', side_effect=failing):
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
            if scope[1]:
                entered.set()
                cancelled.wait(2)
            return original(source, cancelled, scope, include_properties)
        with patch.object(PropertyDataLoader, 'read_location_scope', side_effect=slow):
            self.choose_municipality()
            self.wait_until(entered.is_set)
            # The county preview already ran before the municipality read; only that read is in flight.
            previews = self.preview_mock.call_count
            self.helper.close()
            self.wait_until(lambda: not self.helper._loader._request.busy)
        self.assertEqual(self.ids(), set())
        self.completed.assert_not_called()
        self.assertEqual(self.preview_mock.call_count, previews)

    def test_replaced_import_layer_cannot_receive_old_result(self):
        self.load_index()
        entered, release = threading.Event(), threading.Event()
        original = PropertyDataLoader.read_location_scope
        def slow(source, cancelled, scope, include_properties):
            if scope[1]:
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


if __name__ == '__main__':
    unittest.main()
