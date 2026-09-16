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
from Kavitro_dev.modules.Property.FlowControllers import AddBatchRunner as module
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
        self.runner = module.AddBatchRunner(None)
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

    def test_permanent_create_failure_stops_batch_without_copying_or_skipping(self):
        self.create.side_effect = [None, 'second-id']
        result = self.run_batch(self.features)
        self.assertEqual((result['done'], result['succeeded'], result['failed']), (1, 0, 1))
        self.assertEqual(result['pending'], 1)
        self.assertTrue(result['stopped'])
        self.assertEqual(result['errors'][0]['tunnus'], '1')
        self.assertEqual(self.target.featureCount(), 0)
        self.create.assert_called_once()

    def test_existing_backend_updates_instead_of_duplicate_create(self):
        self.lookup.return_value = {'exists': True, 'property': {
            'id': 'known', 'cadastralUnitNumber': '1', 'displayAddress': 'Example'}}
        module.apply_reviewed_backend(self.data, [], None, None)
        self.create.assert_not_called()
        self.update.assert_called_once_with('known', self.data, [], raise_on_error=True)

    def test_update_failure_is_reported(self):
        self.lookup.return_value = {'exists': True, 'property': {
            'id': 'known', 'cadastralUnitNumber': '1', 'displayAddress': 'Example'}}
        self.update.return_value = False
        self.assertEqual(self.run_batch()['failed'], 1)
        self.assertEqual(self.target.featureCount(), 0)

    def test_partial_save_with_house_number_and_equal_dates_retries_intended_uses(self):
        self.data['address']['houseNumber'] = '12'
        self.lookup.return_value = {'exists': True, 'LastUpdated': '2026-01-01', 'property': {
            'id': 'known', 'cadastralUnitNumber': '1', 'displayAddress': 'Example 12'}}
        module.apply_reviewed_backend(self.data, [], '2026-01-01', None)
        self.update.assert_called_once_with('known', self.data, [], raise_on_error=True)
        self.create.assert_not_called()

    def test_different_newer_backend_is_not_reported_as_fully_saved(self):
        self.lookup.return_value = {'exists': True, 'LastUpdated': '2026-01-01', 'property': {
            'id': 'known', 'cadastralUnitNumber': '1', 'displayAddress': 'Changed by user'}}
        decision = module.apply_reviewed_backend(self.data, [], '2025-01-01', None)
        self.assertEqual(decision['action'], 'needs_decision')
        self.update.assert_not_called()
        self.create.assert_not_called()

    def test_archived_and_duplicate_records_require_separate_review(self):
        for info in ({'exists': False, 'archived_only': True}, {'exists': True, 'active_count': 2}):
            with self.subTest(info=info):
                self.lookup.return_value = info
                self.assertEqual(module.apply_reviewed_backend(self.data, [], None, None)['action'],
                                 'needs_decision')
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
        def slow_create(*args, **kwargs):
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

    def test_cancelling_retry_wait_leaves_current_and_following_properties_unfinished(self):
        waits, pulses = [], []
        self.runner.waiting.connect(lambda seconds, reason: waits.append((seconds, reason)))
        def waiting_backend(*args, **kwargs):
            self.runner.waiting.emit(30.0, 'rate_limit')
            self.runner._cancel_event.wait(3)
            raise module.RequestCancelled()
        with patch.object(module, 'apply_reviewed_backend', side_effect=waiting_backend):
            self.runner._queue = list(self.features)
            self.runner._total = 2
            self.runner._tick()
            self.wait_until(lambda: bool(waits))
            self.assertEqual(self.runner._done, 0)
            self.assertEqual(self.results, [])
            QTimer.singleShot(0, lambda: pulses.append(True))
            self.wait_until(lambda: bool(pulses))
            self.runner.cancel()
            self.wait_until(lambda: bool(self.results))
        result = self.results[0]
        self.assertEqual((result['done'], result['succeeded'], result['failed'], result['pending']), (0, 0, 0, 2))
        self.assertTrue(result['canceled'])
        self.assertEqual(result['unfinished']['tunnus'], '1')
        self.assertTrue(result['unfinished']['message'])
        self.create.assert_not_called()
        self.assertEqual(self.target.featureCount(), 0)

    def conflict_info(self, address='Changed by user'):
        return {'exists': True, 'active_count': 1, 'LastUpdated': '2026-01-01', 'property': {
            'id': 'known', 'cadastralUnitNumber': '1', 'displayAddress': address}}

    def review_batch(self, decisions):
        self.runner.deleteLater()
        self.results.clear()
        self.runner = module.AddBatchRunner(None, review_decisions=decisions)
        self.runner.finished.connect(self.results.append)
        self.runner.start()
        self.wait_until(lambda: bool(self.results))
        return self.results[0]

    def test_prechecked_conflict_is_deferred_and_remaining_81_properties_import(self):
        from Kavitro_dev.modules.Property.FlowControllers.BackendVerifyWorker import BackendVerifyWorker
        from Kavitro_dev.languages.translation_keys import TranslationKeys as K
        for number in range(3, 83):
            feature = QgsFeature(self.source.fields())
            feature.setAttributes([str(number)])
            feature.setGeometry(QgsGeometry.fromWkt('POINT(10 20)'))
            self.source.dataProvider().addFeatures([feature])
        self.lookup.side_effect = lambda number: self.conflict_info() if number == '1' else {'exists': False}
        check = BackendVerifyWorker([(0, '1', '2025-01-01')], source='test',
            import_context_by_tunnus={'1': {'data': self.data, 'main_date': None}})
        checked = []
        check.rowResult.connect(lambda row, number, result: checked.append(result))
        check.run()
        self.assertEqual(checked[0]['decision']['action'], 'needs_decision')
        self.assertIn(K.PROPERTY_ADD_BACKEND_DIFFERS, checked[0]['causes'])
        result = self.run_batch(list(self.source.getFeatures()))
        self.assertEqual((result['done'], result['total'], result['succeeded'], result['failed'],
                          result['pending']), (82, 82, 81, 0, 0))
        self.assertFalse(result['stopped'])
        self.assertEqual([item['tunnus'] for item in result['deferred']], ['1'])
        self.assertEqual(self.target.featureCount(), 81)
        self.assertEqual(self.create.call_count, 81)
        self.update.assert_not_called()

    def test_check_controller_interrupts_rate_limit_wait_and_ignores_a_replaced_run(self):
        from PyQt5 import sip
        from Kavitro_dev.modules.Property.FlowControllers.BackendVerifyController import BackendVerifyController
        from Kavitro_dev.python.api_rate_limit import PROCESS_RATE_LIMITER
        in_flight, release = threading.Event(), threading.Event()

        def lookup(number):
            if number == 'wait':
                PROCESS_RATE_LIMITER._wait(30, 'rate_limit')
            elif number == 'flight':
                in_flight.set()
                release.wait(5)
            return {'exists': False}

        self.lookup.side_effect = lookup
        context = {'data': self.data, 'main_date': None}
        controller = BackendVerifyController()
        rows, waits, finished, guard_on_main = [], [], [], []
        forward = controller._forward
        controller._forward = lambda *args: (
            guard_on_main.append(threading.current_thread() is threading.main_thread()), forward(*args))
        controller.rowResult.connect(lambda row, number, result: rows.append(number))
        controller.waiting.connect(lambda seconds, reason: waits.append((seconds, reason)))
        controller.finished.connect(finished.append)
        stopped = lambda thread: sip.isdeleted(thread) or thread.isFinished()
        try:
            # A normal run forwards every row; the stale-run guard itself runs on the GUI thread.
            controller.start([(0, '1', ''), (1, '2', '')], source='test',
                             import_context_by_tunnus={'1': context, '2': context})
            self.wait_until(lambda: bool(finished))
            self.assertEqual(rows, ['1', '2'])
            self.assertFalse(finished[0]['stopped'])
            self.assertTrue(guard_on_main and all(guard_on_main))
            self.assertIsNone(controller._worker)

            # Stopping interrupts a 30 s server pause instead of waiting it out.
            rows.clear()
            finished.clear()
            controller.start([(0, 'wait', '')], source='test', import_context_by_tunnus={'wait': context})
            self.wait_until(lambda: bool(waits))
            self.assertGreater(waits[0][0], 29)
            self.assertEqual(waits[0][1], 'rate_limit')
            thread = controller._thread
            controller.stop()
            self.wait_until(lambda: stopped(thread))
            QTest.qWait(50)
            self.assertEqual((len(waits), rows, finished), (1, [], []))

            # A replaced run's late response is neither shown nor able to detach its replacement.
            waits.clear()
            controller.start([(0, 'flight', '')], source='test', import_context_by_tunnus={'flight': context})
            self.assertTrue(in_flight.wait(5))
            old_thread = controller._thread
            controller.stop()
            controller.start([(0, 'wait', '')], source='test', import_context_by_tunnus={'wait': context})
            replacement = controller._worker
            release.set()
            self.wait_until(lambda: stopped(old_thread))
            QTest.qWait(50)
            self.assertIs(controller._worker, replacement)
            self.assertEqual((rows, finished), ([], []))
        finally:
            release.set()
            thread = controller._thread
            controller.stop()
            if thread is not None:
                self.wait_until(lambda: stopped(thread))
            controller.deleteLater()

    def test_check_controller_survives_owner_deletion_during_a_request_or_a_pause(self):
        from PyQt5 import sip
        from PyQt5.QtCore import QObject, Qt
        from Kavitro_dev.modules.Property.FlowControllers.BackendVerifyController import BackendVerifyController
        from Kavitro_dev.python.api_rate_limit import PROCESS_RATE_LIMITER
        gate, busy, release = threading.Event(), threading.Event(), threading.Event()
        requested = []

        def lookup(number):
            requested.append(number)
            if number == 'pause':
                gate.wait(5)
                PROCESS_RATE_LIMITER._wait(30, 'rate_limit')
            else:
                busy.set()
                release.wait(5)
            return {'exists': False}

        self.lookup.side_effect = lookup
        context = {'data': self.data, 'main_date': None}
        for first in ('request', 'pause'):
            with self.subTest(first=first):
                for event in (gate, busy, release):
                    event.clear()
                requested.clear()
                owner = QObject()
                controller = BackendVerifyController(owner)
                controller.start([(0, first, ''), (1, 'next', '')], source='test',
                                 import_context_by_tunnus={first: context, 'next': context})
                thread = controller._thread
                if first == 'pause':
                    # Proceed only once the pause was reported, so its notices reach a deleted controller.
                    controller._worker.waiting.connect(lambda *_: busy.set(), type=Qt.DirectConnection)
                    gate.set()
                try:
                    self.assertTrue(busy.wait(5))
                    # A deleted dialog or reloaded plugin removes the owner mid-request or mid-pause.
                    sip.delete(owner)
                    self.assertTrue(sip.isdeleted(controller))
                    self.assertFalse(sip.isdeleted(thread))
                finally:
                    gate.set()
                    release.set()
                self.wait_until(lambda: thread not in _ACTIVE_THREADS)
                QTest.qWait(50)
                # Deleting the owner also cancelled the run: the next property was never requested.
                self.assertEqual(requested, [first])

    def test_archived_and_ambiguous_matches_do_not_stop_following_properties(self):
        self.lookup.side_effect = [{'exists': False, 'archived_only': True},
                                   {'exists': True, 'active_count': 2}]
        result = self.run_batch(self.features)
        self.assertEqual((result['done'], result['failed'], len(result['deferred'])), (2, 0, 2))
        self.assertFalse(result['stopped'])
        self.create.assert_not_called()
        self.update.assert_not_called()
        self.assertEqual(self.target.featureCount(), 0)

    def test_technical_error_after_conflict_stops_and_retains_decision(self):
        self.lookup.side_effect = [self.conflict_info(), {'exists': None}]
        result = self.run_batch(self.features)
        self.assertEqual((len(result['deferred']), result['failed']), (1, 1))
        self.assertTrue(result['stopped'])
        self.assertEqual(self.target.featureCount(), 0)

    def test_only_explicitly_reviewed_conflict_is_updated_and_copied(self):
        self.lookup.return_value = self.conflict_info()
        initial = self.run_batch()
        self.update.assert_not_called()
        result = self.review_batch(initial['deferred'])
        self.update.assert_called_once()
        self.assertEqual((result['succeeded'], result['failed'], result['deferred']), (1, 0, []))
        self.assertEqual(self.target.featureCount(), 1)

    def test_changed_backend_requires_new_decision_without_writing(self):
        self.lookup.return_value = self.conflict_info()
        initial = self.run_batch()
        self.lookup.return_value = self.conflict_info('Changed again')
        result = self.review_batch(initial['deferred'])
        self.update.assert_not_called()
        self.assertEqual(result['succeeded'], 0)
        self.assertTrue(result['deferred'][0]['changed'])
        self.assertEqual(result['deferred'][0]['backend_address'], 'Changed again')
        self.assertEqual(self.target.featureCount(), 0)

    def test_changed_source_geometry_requires_new_decision(self):
        self.lookup.return_value = self.conflict_info()
        initial = self.run_batch()
        self.source.dataProvider().changeGeometryValues({self.features[0].id(): QgsGeometry.fromWkt('POINT(30 40)')})
        result = self.review_batch(initial['deferred'])
        self.assertTrue(result['deferred'][0]['changed'])
        self.update.assert_not_called()
        self.assertEqual(self.target.featureCount(), 0)

    def test_precheck_uses_main_date_as_well_as_backend_date(self):
        from Kavitro_dev.modules.Property.FlowControllers.property_import_decisions import classify_property_import
        decision = classify_property_import(self.data, '2026-02-01', '2026-03-01', self.conflict_info())
        self.assertEqual(decision['action'], 'needs_decision')
        self.assertFalse(decision['import_newer'])

    def test_unknown_and_timezone_dates_do_not_turn_conflicts_into_technical_failures(self):
        from Kavitro_dev.modules.Property.FlowControllers.property_import_decisions import classify_property_import
        info = self.conflict_info()
        info['LastUpdated'] = '2026-01-01T10:00:00Z'
        for date in (None, '', 'unreadable', '2026-01-01'):
            with self.subTest(date=date):
                self.assertEqual(classify_property_import(self.data, date, None, info)['action'], 'needs_decision')
        self.assertEqual(classify_property_import(self.data, '2026-01-02', None, info)['action'], 'update')

    def test_review_dialog_defaults_to_later_and_never_offers_ambiguous_overwrite(self):
        from Kavitro_dev.widgets.property_import_review_dialog import PropertyImportReviewDialog
        from Kavitro_dev.languages.language_manager import LanguageManager
        self.lookup.side_effect = [self.conflict_info(), {'exists': True, 'active_count': 2}]
        result = self.run_batch(self.features)
        dialog = PropertyImportReviewDialog(result['deferred'], lang_manager=LanguageManager('et'))
        try:
            dialog.show()
            self.app.processEvents()
            self.assertFalse(dialog.confirm.isEnabled())
            self.assertEqual(dialog.selected_decisions(), {})
            self.assertEqual(dialog.choices[0].findData('apply'), 2)
            self.assertEqual(dialog.choices[1].findData('apply'), -1)
            self.assertIn('Changed by user', dialog.details.toPlainText())
            self.assertIn('Puudub või teadmata', dialog.details.toPlainText())
            dialog.choices[0].setCurrentIndex(2)
            self.assertTrue(dialog.confirm.isEnabled())
            self.assertEqual(dialog.selected_decisions(), {'1': 'apply'})
        finally:
            dialog.close()
            dialog.deleteLater()


if __name__ == '__main__':
    unittest.main()
