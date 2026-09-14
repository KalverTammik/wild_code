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

from PyQt5.QtCore import QThread, QTimer
from PyQt5.QtGui import QFont, QFontDatabase
from PyQt5.QtTest import QTest
from qgis.core import QgsApplication, QgsFeature, QgsGeometry, QgsVectorLayer
from Kavitro_dev.modules.Property.FlowControllers import checked_add_runner as module
from Kavitro_dev.python.workers import _ACTIVE_THREADS


class CheckedPropertyAddTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QgsApplication.instance() or QgsApplication([], False)
        QgsApplication.initQgis()
        if not QFontDatabase().families():
            QFontDatabase.addApplicationFont('C:/Windows/Fonts/segoeui.ttf')
            cls.app.setFont(QFont('Segoe UI', 9))

    def setUp(self):
        self.data = {'cadastralUnit': {'number': '1'}, 'address': {'street': 'Example'}}
        self.lookup = self.enterContext(patch.object(module.BackendPropertyVerifier,
            'verify_properties_by_cadastral_number', return_value={'exists': False}))
        self.create = self.enterContext(patch.object(module.MainAddPropertiesFlow,
            'add_single_property_item', return_value='backend-id'))
        self.update = self.enterContext(patch.object(module.UpdatePropertyData,
            'update_single_property_item', return_value=True))
        self.enterContext(patch.object(module.PythonFailLogger, 'log_exception'))
        self.source = QgsVectorLayer('Point?crs=EPSG:3301&field=tunnus:string', 'Import', 'memory')
        self.target = QgsVectorLayer('Point?crs=EPSG:3301&field=tunnus:string', 'Main', 'memory')
        for number in ('1', '2'):
            feature = QgsFeature(self.source.fields())
            feature.setAttributes([number])
            feature.setGeometry(QgsGeometry.fromWkt('POINT(10 20)'))
            self.source.dataProvider().addFeatures([feature])
        self.features = list(self.source.getFeatures())
        self.enterContext(patch.object(module.MapHelpers, 'get_layer_by_tag', return_value=self.source))
        self.enterContext(patch.object(module.ActiveLayersHelper, 'resolve_main_property_layer', return_value=self.target))
        loader = self.enterContext(patch.object(module, 'PropertyDataLoader'))
        loader._eq_expr.side_effect = lambda field, value: f'"{field}" = \'{value}\''
        loader.return_value.prepare_data_for_import_stage1.side_effect = lambda feature: (
            {'cadastralUnit': {'number': feature['tunnus']}, 'address': {'street': 'Example'}},
            feature['tunnus'], [], None)
        self.runner = module.CheckedAddBatchRunner(None, rest_ms=0)
        self.results = []
        self.runner.finished.connect(self.results.append)

    def tearDown(self):
        self.wait_until(lambda: not _ACTIVE_THREADS)
        self.runner.cancel()
        self.runner.deleteLater()
        self.app.processEvents()

    def wait_until(self, condition):
        for _ in range(500):
            if condition():
                return
            QTest.qWait(10)
        self.fail('Timed out waiting for worker')

    def run_batch(self, features=None):
        self.runner._queue = list(features if features is not None else self.features[:1])
        self.runner._total = len(self.runner._queue)
        self.runner._tick()
        self.wait_until(lambda: bool(self.results))
        return self.results[0]

    def test_existing_map_missing_backend_created_once_without_map_edits(self):
        self.target.dataProvider().addFeatures([self.features[0]])
        before = list(self.target.getFeatures())
        result = self.run_batch()
        self.create.assert_called_once()
        self.update.assert_not_called()
        self.assertEqual(result['succeeded'], 1)
        self.assertEqual(list(self.target.getFeatures()), before)
        self.assertFalse(self.target.isEditable())

    def test_missing_map_gets_complete_geometry_on_gui_thread(self):
        original = module.FeatureActions.copy_feature_to_layer
        threads = []
        def copy(feature, target):
            threads.append(QThread.currentThread())
            return original(feature, target)
        with patch.object(module.FeatureActions, 'copy_feature_to_layer', side_effect=copy):
            result = self.run_batch()
        self.assertEqual(result['succeeded'], 1)
        self.assertEqual(threads, [self.app.thread()])
        self.assertEqual(next(self.target.getFeatures()).geometry().asWkt(), 'Point (10 20)')

    def test_lookup_failure_does_not_create_or_copy(self):
        self.lookup.return_value = {'exists': None, 'error': 'offline'}
        result = self.run_batch()
        self.assertEqual((result['succeeded'], result['failed']), (0, 1))
        self.create.assert_not_called()
        self.assertEqual(self.target.featureCount(), 0)

    def test_create_failure_does_not_copy_and_batch_continues(self):
        self.create.side_effect = [None, 'second-id']
        result = self.run_batch(self.features)
        self.assertEqual((result['done'], result['succeeded'], result['failed']), (2, 1, 1))
        self.assertEqual(result['errors'][0]['tunnus'], '1')
        self.assertEqual([f['tunnus'] for f in self.target.getFeatures()], ['2'])

    def test_existing_backend_updates_instead_of_duplicate_create(self):
        self.lookup.return_value = {'exists': True, 'property': {
            'id': 'known', 'cadastralUnitNumber': '1', 'displayAddress': 'Example'}}
        module.apply_reviewed_backend(self.data, [], None, None)
        self.create.assert_not_called()
        self.update.assert_called_once_with('known', self.data, [])

    def test_update_failure_is_reported(self):
        self.lookup.return_value = {'exists': True, 'property': {
            'id': 'known', 'cadastralUnitNumber': '1', 'displayAddress': 'Example'}}
        self.update.return_value = False
        self.assertEqual(self.run_batch()['failed'], 1)
        self.assertEqual(self.target.featureCount(), 0)

    def test_archived_and_duplicate_records_require_separate_review(self):
        for info in ({'exists': False, 'archived_only': True}, {'exists': True, 'active_count': 2}):
            with self.subTest(info=info):
                self.lookup.return_value = info
                with self.assertRaises(RuntimeError):
                    module.apply_reviewed_backend(self.data, [], None, None)
        self.create.assert_not_called()
        self.update.assert_not_called()

    def test_map_copy_failure_rolls_back_and_reports_failure(self):
        with patch.object(module.FeatureActions, 'copy_feature_to_layer', return_value=(False, 'error')):
            result = self.run_batch()
        self.assertEqual(result['failed'], 1)
        self.assertFalse(self.target.isEditable())
        self.assertEqual(self.target.featureCount(), 0)

    def test_map_commit_failure_rolls_back_and_reports_failure(self):
        with patch.object(self.target, 'commitChanges', return_value=False):
            result = self.run_batch()
        self.assertEqual(result['failed'], 1)
        self.assertFalse(self.target.isEditable())
        self.assertEqual(self.target.featureCount(), 0)

    def test_create_request_does_not_retry_after_lost_response(self):
        from Kavitro_dev.python import api_client
        client = api_client.APIClient(session_manager=Mock())
        with patch.object(api_client.QThread, 'currentThread', return_value=object()), \
                patch.object(api_client.requests, 'post', side_effect=api_client.requests_exceptions.Timeout('lost')) as post:
            with self.assertRaises(Exception):
                client.send_query('mutation { createProperty { id } }', require_auth=False, retry_network=False)
        self.assertEqual(post.call_count, 1)

    def test_cancel_waits_for_active_mutation_and_keeps_gui_responsive(self):
        entered, release = threading.Event(), threading.Event()
        threads, pulses = [], []
        def slow_create(*args):
            threads.append(QThread.currentThread())
            entered.set()
            release.wait(3)
            return 'created'
        self.create.side_effect = slow_create
        self.runner._queue = list(self.features)
        self.runner._total = 2
        try:
            self.runner._tick()
            self.wait_until(entered.is_set)
            QTimer.singleShot(0, lambda: pulses.append(True))
            self.wait_until(lambda: bool(pulses))
            self.runner.cancel()
            self.assertEqual(self.results, [])
            self.assertNotEqual(threads[0], self.app.thread())
        finally:
            release.set()
        self.wait_until(lambda: bool(self.results))
        self.runner.cancel()
        self.assertEqual(len(self.results), 1)
        self.assertEqual((self.results[0]['canceled'], self.results[0]['done'], self.results[0]['succeeded']),
                         (True, 1, 1))
        self.create.assert_called_once()
        self.assertEqual(self.target.featureCount(), 1)


if __name__ == '__main__':
    unittest.main()
