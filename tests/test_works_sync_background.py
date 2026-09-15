from __future__ import annotations

import os
import sys
import threading
import unittest
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
if os.environ.get('QGIS_PREFIX_PATH'):
    sys.path.append(str(Path(os.environ['QGIS_PREFIX_PATH']) / 'python' / 'plugins'))

from PyQt5.QtCore import QThread, QTimer
from PyQt5.QtTest import QTest
from qgis.core import QgsApplication, QgsFeature, QgsVectorLayer
from Kavitro_dev.modules.works.works_sync_service import WorksSyncService
from Kavitro_dev.modules.works.works_layer_service import WorksLayerService
from Kavitro_dev.python.api_actions import APIModuleActions


class WorksSyncBackgroundTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QgsApplication.instance() or QgsApplication([], False)
        QgsApplication.initQgis()

    def setUp(self):
        self.layer = QgsVectorLayer('Point?crs=EPSG:3301&field=ext_job_id:string&field=ext_job_name:string', 'offline', 'memory')
        self.assertTrue(self.layer.isValid())
        feature = QgsFeature(self.layer.fields())
        feature.setAttributes(['1', 'Original'])
        self.layer.dataProvider().addFeatures([feature])
        self.feature_id = next(self.layer.getFeatures()).id()
        self.resolve = patch.object(WorksLayerService, 'resolve_main_layer', return_value=self.layer)
        self.resolve_mock = self.resolve.start()
        self.service = WorksSyncService()
        self.gate, self.entered = threading.Event(), threading.Event()
        self.worker_threads = []
        self.fetch = patch.object(APIModuleActions, 'get_tasks_by_ids', side_effect=self.fetch_tasks)
        self.fetch_mock = self.fetch.start()

    def fetch_tasks(self, ids):
        self.assertEqual(ids, ['1'])
        self.worker_threads.append(QThread.currentThread())
        self.entered.set()
        self.gate.wait(3)
        return {'1': {'id': '1', 'name': 'From server'}}

    def wait_until(self, condition):
        for _ in range(150):
            if condition():
                return
            QTest.qWait(10)
        self.fail('Background sync did not complete')

    def tearDown(self):
        self.gate.set()
        self.wait_until(lambda: not self.service._request.busy)
        self.service.detach()
        self.fetch.stop()
        self.resolve.stop()

    def start_sync(self):
        self.service.sync_from_backend()
        self.wait_until(self.entered.is_set)

    def finish_sync(self):
        self.gate.set()
        self.wait_until(lambda: not self.service._request.busy)

    def name(self):
        return self.layer.getFeature(self.feature_id)['ext_job_name']

    def test_slow_sync_fetches_off_thread_and_applies_layer_updates_on_gui(self):
        pulses, apply_threads = [], []
        original_apply = self.service._apply_pending_updates
        def apply(**kwargs):
            apply_threads.append(QThread.currentThread())
            original_apply(**kwargs)
        with patch.object(self.service, '_apply_pending_updates', side_effect=apply):
            self.start_sync()
            QTimer.singleShot(0, lambda: pulses.append(True))
            QTest.qWait(40)
            self.assertEqual(pulses, [True])
            self.assertEqual(self.name(), 'Original')
            self.finish_sync()
        self.assertEqual(self.name(), 'From server')
        self.assertNotEqual(self.worker_threads[0], self.app.thread())
        self.assertEqual(apply_threads, [self.app.thread()])

    def test_failed_geometry_stops_batch_and_only_successes_get_audit_fields(self):
        self.service.attach()
        warnings = []
        self.service.geometry_sync_failed.connect(warnings.append)
        with patch.object(self.service, '_sync_feature_geometry_to_backend', side_effect=[True, False, True]) as sync, \
                patch.object(self.service, '_stamp_geometry_audit_fields') as stamp:
            self.service._on_committed_geometries_changes('offline', {1: None, 2: None, 3: None})
        self.assertEqual(sync.call_count, 2)
        stamp.assert_called_once_with(layer=self.layer, feature_ids=[1])
        self.assertEqual(len(warnings), 1)
        self.assertFalse(self.service._syncing_geometry)

    def test_geometry_helper_propagates_negative_save_response(self):
        from qgis.core import QgsGeometry
        from Kavitro_dev.modules.works import works_sync_service as module
        with patch.object(APIModuleActions, 'get_task_data', return_value={'id': '1'}), \
                patch.object(APIModuleActions, 'update_task_geometry', return_value=False), \
                patch.object(module.PythonFailLogger, 'log_exception') as log:
            result = self.service._sync_feature_geometry_to_backend(
                layer=self.layer, feature_id=self.feature_id,
                geometry=QgsGeometry.fromWkt('POINT(10 20)'), task_id_field='ext_job_id')
        self.assertIs(result, False)
        log.assert_called_once()

    def test_edit_committed_during_request_is_preserved(self):
        self.start_sync()
        self.layer.startEditing()
        self.layer.changeAttributeValue(self.feature_id, 1, 'Local edit')
        self.assertTrue(self.layer.commitChanges())
        self.finish_sync()
        self.assertEqual(self.name(), 'Local edit')

    def test_layer_in_edit_mode_is_not_modified(self):
        self.start_sync()
        self.layer.startEditing()
        self.finish_sync()
        self.assertTrue(self.layer.isEditable())
        self.assertEqual(self.name(), 'Original')
        self.layer.rollBack()

    def test_detach_discards_running_response(self):
        self.start_sync()
        self.service.detach()
        self.finish_sync()
        self.assertEqual(self.name(), 'Original')

    def test_changing_configured_layer_discards_response(self):
        self.start_sync()
        self.resolve_mock.return_value = None
        self.finish_sync()
        self.assertEqual(self.name(), 'Original')


if __name__ == '__main__':
    unittest.main()
