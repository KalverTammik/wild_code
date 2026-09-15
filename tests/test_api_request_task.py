import os
import sys
import threading
import time
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import Mock, patch

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from qgis.core import QgsApplication
from qgis.PyQt.QtCore import QThread, QTimer
from qgis.PyQt.QtGui import QFont, QFontDatabase
from Kavitro_dev.python import api_client, api_rate_limit, api_request_task
from Kavitro_dev.python.latest_request import LatestRequest
from Kavitro_dev.python.workers import _ACTIVE_THREADS
from qgis.PyQt.QtTest import QTest
from tests.test_api_rate_limit import FakeClock, FakeResponse


class ApiRequestTaskTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QgsApplication.instance() or QgsApplication([], False)
        if not QFontDatabase().families():
            QFontDatabase.addApplicationFont('C:/Windows/Fonts/segoeui.ttf')
            cls.app.setFont(QFont('Segoe UI', 9))

    def setUp(self):
        self.enterContext(patch.object(api_rate_limit, 'PROCESS_RATE_LIMITER', api_rate_limit.RateLimitCoordinator()))
        self.client = api_client.APIClient(session_manager=Mock(get_token=Mock(return_value='test-token')))

    def test_gui_stays_alive_during_slow_http_and_transport_runs_off_gui(self):
        pulses, threads, dialogs = [], [], []
        timer = QTimer()
        timer.timeout.connect(lambda: pulses.append(time.monotonic()))
        timer.start(20)
        original_exec = api_request_task._RequestDialog.exec_
        def exec_dialog(dialog):
            dialogs.append(dialog.label.text())
            return original_exec(dialog)
        def post(*args, **kwargs):
            threads.append(QThread.currentThread())
            time.sleep(0.65)
            return FakeResponse()
        try:
            with patch.object(api_client.requests, 'post', side_effect=post), \
                    patch.object(api_request_task._RequestDialog, 'exec_', exec_dialog):
                result = self.client.send_query('query { properties { id } }')
        finally:
            timer.stop()
        self.assertEqual(result, {'id': 'saved'})
        self.assertGreater(len(pulses), 10)
        self.assertTrue(dialogs)
        self.assertNotEqual(threads[0], self.app.thread())

    def test_gui_cancel_during_429_wait_does_not_send_again(self):
        original_exec = api_request_task._RequestDialog.exec_
        labels = []
        def cancel_dialog(dialog):
            labels.append(dialog.label.text())
            QTimer.singleShot(0, dialog.reject)
            return original_exec(dialog)
        with patch.object(api_request_task._RequestDialog, 'exec_', cancel_dialog), \
                patch.object(api_client.requests, 'post', return_value=FakeResponse(429, {'Retry-After': '30'}, {})) as post:
            with self.assertRaises(api_rate_limit.RequestCancelled):
                self.client.send_query('mutation { createTask { id } }')
        self.assertEqual(post.call_count, 1)
        self.assertTrue(labels)

    def test_cancel_waits_for_already_sent_write_and_preserves_its_success(self):
        original_exec = api_request_task._RequestDialog.exec_
        def cancel_dialog(dialog):
            QTimer.singleShot(0, dialog.reject)
            return original_exec(dialog)
        def post(*args, **kwargs):
            time.sleep(0.65)
            return FakeResponse()
        with patch.object(api_request_task._RequestDialog, 'exec_', cancel_dialog), \
                patch.object(api_client.requests, 'post', side_effect=post) as mocked:
            result = self.client.send_query('mutation { createTask { id } }')
        self.assertEqual(result, {'id': 'saved'})
        self.assertEqual(mocked.call_count, 1)

    def test_gui_json_and_uploads_share_budget_and_retry_complete_files(self):
        clock = FakeClock()
        limiter = api_rate_limit.RateLimitCoordinator(clock=clock.now, sleep=clock.sleep)
        attempts, contents = [], []
        def post(*args, **kwargs):
            attempts.append(clock.now())
            if 'files' in kwargs:
                contents.append(kwargs['files']['0'][1].read())
                if len(contents) == 1:
                    return FakeResponse(429, {'Retry-After': '3'}, {})
            return FakeResponse()
        with TemporaryDirectory() as directory, \
                patch.object(api_rate_limit, 'PROCESS_RATE_LIMITER', limiter), \
                patch.object(api_client.requests, 'post', side_effect=post):
            file = Path(directory) / 'upload.txt'
            file.write_bytes(b'entire-file')
            self.client.send_query('mutation { updateTask { id } }')
            self.client.send_multipart_query('mutation { uploadFile { uuid } }', file_variables={'file': str(file)})
        self.assertEqual(attempts, [100, 102, 105])
        self.assertEqual(contents, [b'entire-file', b'entire-file'])

    def test_mutations_and_uploads_do_not_blindly_retry_lost_responses(self):
        # Worker callers previously retried uploads and createTask after a timeout.
        with patch.object(api_client.QThread, 'currentThread', return_value=object()):
            for query in ('mutation { createTask { id } }', 'mutation { updateProperty { id } }'):
                with self.subTest(query=query), patch.object(api_client.requests, 'post',
                        side_effect=api_client.requests_exceptions.Timeout('lost')) as post:
                    with self.assertRaises(Exception):
                        self.client.send_query(query)
                    self.assertEqual(post.call_count, 1)
            with TemporaryDirectory() as directory:
                file = Path(directory) / 'upload.txt'
                file.write_bytes(b'data')
                with patch.object(api_client.requests, 'post', side_effect=api_client.requests_exceptions.Timeout('lost')) as post:
                    with self.assertRaises(Exception):
                        self.client.send_multipart_query('mutation { uploadFile { uuid } }', file_variables={'file': str(file)})
                    self.assertEqual(post.call_count, 1)

    def test_replacing_background_request_cancels_cooldown_and_runs_latest(self):
        request = LatestRequest()
        entered = threading.Event()
        results, errors = [], []
        request.finished.connect(results.append)
        request.error.connect(errors.append)
        def rejected(*args, **kwargs):
            entered.set()
            return FakeResponse(429, {'Retry-After': '60'}, {})
        with patch.object(api_client.requests, 'post', side_effect=rejected) as post:
            request.submit(self.client.send_query, 'query { properties { id } }')
            for _ in range(200):
                if entered.is_set():
                    break
                QTest.qWait(10)
            self.assertTrue(entered.is_set())
            request.submit(lambda: 'latest')
            for _ in range(200):
                if not request.busy and not _ACTIVE_THREADS:
                    break
                QTest.qWait(10)
            self.assertFalse(request.busy)
            self.assertEqual(post.call_count, 1)
        self.assertEqual(results, ['latest'])
        self.assertEqual(errors, [])
        request.deleteLater()


if __name__ == '__main__':
    unittest.main()
