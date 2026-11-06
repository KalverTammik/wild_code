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
from qgis.PyQt import sip
from qgis.PyQt.QtCore import QThread, QTimer
from qgis.PyQt.QtWidgets import QDialog
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

    def tearDown(self):
        # Back in the event loop: a wait window left open by the test closes.
        self.app.processEvents()

    def test_gui_stays_alive_during_slow_http_and_transport_runs_off_gui(self):
        pulses, threads, dialogs = [], [], []
        timer = QTimer()
        timer.timeout.connect(lambda: pulses.append(time.monotonic()))
        timer.start(20)
        original_show = api_request_task._RequestDialog.show
        def show_dialog(dialog):
            dialogs.append(dialog.label.text())
            return original_show(dialog)
        def post(*args, **kwargs):
            threads.append(QThread.currentThread())
            time.sleep(0.65)
            return FakeResponse()
        try:
            with patch.object(api_client.requests, 'post', side_effect=post), \
                    patch.object(api_request_task._RequestDialog, 'show', show_dialog):
                result = self.client.send_query('query { properties { id } }')
        finally:
            timer.stop()
        self.assertEqual(result, {'id': 'saved'})
        self.assertGreater(len(pulses), 10)
        self.assertTrue(dialogs)
        self.assertNotEqual(threads[0], self.app.thread())

    def test_gui_cancel_during_429_wait_does_not_send_again(self):
        original_show = api_request_task._RequestDialog.show
        labels = []
        def cancel_dialog(dialog):
            labels.append(dialog.label.text())
            QTimer.singleShot(0, dialog.reject)
            return original_show(dialog)
        with patch.object(api_request_task._RequestDialog, 'show', cancel_dialog), \
                patch.object(api_client.requests, 'post', return_value=FakeResponse(429, {'Retry-After': '30'}, {})) as post:
            with self.assertRaises(api_rate_limit.RequestCancelled):
                self.client.send_query('mutation { createTask { id } }')
        self.assertEqual(post.call_count, 1)
        self.assertTrue(labels)

    def test_rate_limit_retry_can_be_disabled_for_login(self):
        with patch.object(
            api_client.requests,
            'post',
            return_value=FakeResponse(429, {'Retry-After': '30'}, {}),
        ) as post:
            with self.assertRaises(api_rate_limit.ApiRateLimitError):
                self.client.send_query(
                    'mutation Login($input: LoginInput!) { login(input: $input) { accessToken } }',
                    variables={'input': {'username': 'user', 'password': 'password'}},
                    require_auth=False,
                    retry_network=False,
                    retry_rate_limits=False,
                )

        self.assertEqual(post.call_count, 1)

    def test_cancel_waits_for_already_sent_write_and_preserves_its_success(self):
        original_show = api_request_task._RequestDialog.show
        def cancel_dialog(dialog):
            QTimer.singleShot(0, dialog.reject)
            return original_show(dialog)
        def post(*args, **kwargs):
            time.sleep(0.65)
            return FakeResponse()
        with patch.object(api_request_task._RequestDialog, 'show', cancel_dialog), \
                patch.object(api_client.requests, 'post', side_effect=post) as mocked:
            result = self.client.send_query('mutation { createTask { id } }')
        self.assertEqual(result, {'id': 'saved'})
        self.assertEqual(mocked.call_count, 1)

    @staticmethod
    def _is_open(window):
        return not sip.isdeleted(window) and window.isVisible()

    def _shown_windows(self):
        windows = []
        original_show = api_request_task._RequestDialog.show
        def show_dialog(dialog):
            if not any(window is dialog for window in windows):
                windows.append(dialog)
            return original_show(dialog)
        return windows, patch.object(api_request_task._RequestDialog, 'show', show_dialog)

    def test_requests_of_one_flow_share_one_wait_window(self):
        windows, watch_show = self._shown_windows()
        def post(*args, **kwargs):
            time.sleep(0.45)
            return FakeResponse()
        with watch_show, patch.object(api_client.requests, 'post', side_effect=post) as mocked:
            for _ in range(3):
                self.client.send_query('query { properties { id } }')
        self.assertEqual(mocked.call_count, 3)
        self.assertEqual(len(windows), 1)
        self.assertTrue(self._is_open(windows[0]))

        self.app.processEvents()

        self.assertIsNone(api_request_task._RequestDialog.open_window)
        self.assertFalse(self._is_open(windows[0]))

    def test_fast_requests_open_no_wait_window(self):
        windows, watch_show = self._shown_windows()
        with watch_show, patch.object(api_client.requests, 'post', return_value=FakeResponse()):
            for _ in range(3):
                self.client.send_query('query { properties { id } }')
        self.assertEqual(windows, [])

    def test_cancel_also_stops_the_requests_of_the_flow_not_sent_yet(self):
        original_show = api_request_task._RequestDialog.show
        def cancel_dialog(dialog):
            QTimer.singleShot(0, dialog.reject)
            return original_show(dialog)
        def post(*args, **kwargs):
            time.sleep(0.65)
            return FakeResponse()
        with patch.object(api_request_task._RequestDialog, 'show', cancel_dialog), \
                patch.object(api_client.requests, 'post', side_effect=post) as mocked:
            self.assertEqual(self.client.send_query('mutation { createTask { id } }'), {'id': 'saved'})
            with self.assertRaises(api_rate_limit.RequestCancelled):
                self.client.send_query('query { properties { id } }')
        self.assertEqual(mocked.call_count, 1)

        # The flow is over once the event loop runs: a cancel must not outlive its window.
        self.app.processEvents()
        with patch.object(api_client.requests, 'post', return_value=FakeResponse()) as mocked:
            self.assertEqual(self.client.send_query('query { properties { id } }'), {'id': 'saved'})
        self.assertEqual(mocked.call_count, 1)

    def test_message_between_requests_closes_the_wait_window_and_stays_open_itself(self):
        windows, watch_show = self._shown_windows()
        def post(*args, **kwargs):
            time.sleep(0.45)
            return FakeResponse()
        with watch_show, patch.object(api_client.requests, 'post', side_effect=post):
            self.client.send_query('query { properties { id } }')
            message = QDialog()
            during_message = []
            def inspect_then_close():
                during_message.append((self._is_open(windows[0]), message.isVisible()))
                message.accept()
            QTimer.singleShot(30, inspect_then_close)
            message.exec_()
            self.client.send_query('query { properties { id } }')
        self.assertEqual(during_message, [(False, True)])
        self.assertEqual(len(windows), 2)

    def test_new_wait_window_is_not_a_child_of_a_closing_one(self):
        owner = QDialog()
        closing = api_request_task._RequestDialog()
        closing.setParent(owner, closing.windowFlags())
        with patch.object(api_request_task.QApplication, 'activeWindow', return_value=closing):
            window = api_request_task._RequestDialog()
        self.assertIs(window.parentWidget(), owner)
        owner.deleteLater()

    def test_request_finishes_before_an_error_in_the_wait_window_is_raised(self):
        finished = []
        def post(*args, **kwargs):
            time.sleep(0.5)
            finished.append(True)
            return FakeResponse()
        with patch.object(api_request_task._RequestDialog, 'show_window', side_effect=RuntimeError('window gone')), \
                patch.object(api_client.requests, 'post', side_effect=post):
            with self.assertRaises(Exception):
                self.client.send_query('query { properties { id } }')
        self.assertEqual(finished, [True])

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
