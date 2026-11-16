"""Plugin unload stops background work and forgets its pending login listener.

A worker answering after unload reaches deleted widgets (RuntimeError or a QGIS
crash); a login listener left behind opens the window of an unloaded plugin.
"""
from __future__ import annotations

import os
import sys
import threading
import time
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
if os.environ.get("QGIS_PREFIX_PATH"):
    sys.path.append(str(Path(os.environ["QGIS_PREFIX_PATH"]) / "python" / "plugins"))

from PyQt5.QtCore import QCoreApplication
from qgis.core import QgsApplication

from Kavitro_dev import main as main_module
from Kavitro_dev.python import workers
from Kavitro_dev.python.api_rate_limit import RateLimitCoordinator
from Kavitro_dev.python.workers import FunctionWorker
from Kavitro_dev.utils.SessionManager import SessionManager


def flush_events() -> None:
    """Deliver the queued signals and the thread cleanup to the main thread."""
    for _ in range(5):
        QCoreApplication.processEvents()
        time.sleep(0.01)


def wait_for(condition, timeout: float = 3.0) -> bool:
    deadline = time.monotonic() + timeout
    while not condition():
        if time.monotonic() > deadline:
            return False
        QCoreApplication.processEvents()
        time.sleep(0.01)
    return True


class WorkerCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QgsApplication.instance() or QgsApplication([], False)

    def setUp(self) -> None:
        self.assertEqual(dict(workers._ACTIVE_THREADS), {}, "a worker of an earlier test is still running")
        self.addCleanup(self.finish_leftover_threads)

    def finish_leftover_threads(self) -> None:
        for gate in getattr(self, "gates", []):
            gate.set()
        wait_for(lambda: not workers._ACTIVE_THREADS and not getattr(workers, "_STOPPED_THREADS", ()), timeout=8.0)
        flush_events()

    def rate_limited_request(self):
        """Like a request held by the rate limiter: cancel ends the wait at once."""
        started = threading.Event()

        def request():
            started.set()
            RateLimitCoordinator()._wait(5.0, "pacing")  # raises RequestCancelled on cancel
            return "late answer"

        return started, request

    def unstoppable_request(self):
        """Like a request already on the wire: cancel cannot shorten it."""
        started, gate = threading.Event(), threading.Event()
        self.gates = getattr(self, "gates", []) + [gate]

        def request():
            started.set()
            gate.wait(10.0)
            return "late answer"

        return started, gate, request

    def start(self, request, **kwargs):
        worker = FunctionWorker(request)
        received, failed = Mock(name="finished"), Mock(name="error")
        worker.finished.connect(received)
        worker.error.connect(failed)
        thread = workers.start_worker(worker, **kwargs)
        return thread, received, failed


class WorkerRegistryTest(WorkerCase):
    def test_registry_forgets_a_worker_after_its_normal_finish(self) -> None:
        thread, received, failed = self.start(lambda: "answer")

        self.assertTrue(wait_for(lambda: thread not in workers._ACTIVE_THREADS))

        received.assert_called_once_with("answer")
        failed.assert_not_called()
        self.assertEqual(dict(workers._ACTIVE_THREADS), {})

    def test_stop_with_an_empty_registry_does_nothing(self) -> None:
        with patch.object(workers.SwitchLogger, "log") as log:
            workers.stop_all_workers()

        log.assert_not_called()
        self.assertEqual(dict(workers._ACTIVE_THREADS), {})
        self.assertEqual(workers._STOPPED_THREADS, set())


class StopAllWorkersTest(WorkerCase):
    def test_a_waiting_request_is_stopped_and_its_outcome_never_arrives(self) -> None:
        started, request = self.rate_limited_request()
        thread, received, failed = self.start(request)
        self.assertTrue(started.wait(3.0))

        workers.stop_all_workers(timeout_ms=2000)

        self.assertFalse(thread.isRunning(), "the cancelled wait should have ended the thread")
        self.assertEqual(dict(workers._ACTIVE_THREADS), {})
        flush_events()
        received.assert_not_called()
        failed.assert_not_called()
        self.assertNotIn(thread, workers._STOPPED_THREADS)

    def test_an_answer_arriving_after_the_wait_timeout_is_dropped(self) -> None:
        started, gate, request = self.unstoppable_request()
        owner_callback = Mock(name="on_thread_finished")
        thread, received, failed = self.start(request, on_thread_finished=owner_callback)
        self.assertTrue(started.wait(3.0))

        workers.stop_all_workers(timeout_ms=50)

        self.assertTrue(thread.isRunning(), "an answer on the wire cannot be cut short")
        self.assertEqual(dict(workers._ACTIVE_THREADS), {})
        self.assertIn(thread, workers._STOPPED_THREADS, "a running thread must stay referenced")

        gate.set()
        self.assertTrue(thread.wait(3000))
        flush_events()
        received.assert_not_called()
        failed.assert_not_called()
        owner_callback.assert_not_called()
        self.assertNotIn(thread, workers._STOPPED_THREADS)

    def test_the_wait_is_bounded_for_all_threads_together(self) -> None:
        for _ in range(3):
            started, _gate, request = self.unstoppable_request()  # the gate opens in finish_leftover_threads
            self.start(request)
            self.assertTrue(started.wait(3.0))

        begun = time.monotonic()
        workers.stop_all_workers(timeout_ms=150)
        elapsed = time.monotonic() - begun

        self.assertLess(elapsed, 0.4, "three threads must share one deadline, not wait 150 ms each")
        self.assertEqual(dict(workers._ACTIVE_THREADS), {})


class PluginUnloadTest(WorkerCase):
    def setUp(self) -> None:
        super().setUp()
        self.plugin = main_module.WildCodePlugin(Mock(name="iface"))
        self.plugin._crash_logger = Mock()
        self.start_patch(patch.object(main_module.PluginDialog, "get_instance", return_value=None))
        self.addCleanup(SessionManager.set_login_prompt, None)

    def start_patch(self, patcher):
        patcher.start()
        self.addCleanup(patcher.stop)

    def register_pending_login(self) -> Mock:
        """What run() does when no session is valid: wait for the login to show the window."""
        listener = Mock(name="_on_session_valid")
        self.plugin._pending_login_listener = listener
        SessionManager.register_listener(listener)
        self.addCleanup(SessionManager.unregister_listener, listener)
        return listener

    def test_unload_removes_the_pending_login_listener(self) -> None:
        listener = self.register_pending_login()

        self.plugin.unload()

        self.assertNotIn(listener, SessionManager._listeners)
        self.assertIsNone(self.plugin._pending_login_listener)
        SessionManager.notify_session_changed()
        listener.assert_not_called()

    def test_unload_stops_the_running_worker(self) -> None:
        started, request = self.rate_limited_request()
        thread, received, failed = self.start(request)
        self.assertTrue(started.wait(3.0))

        self.plugin.unload()

        self.assertFalse(thread.isRunning())
        self.assertEqual(dict(workers._ACTIVE_THREADS), {})
        flush_events()
        received.assert_not_called()
        failed.assert_not_called()

    def test_unload_twice_is_safe(self) -> None:
        self.register_pending_login()
        with patch.object(main_module, "QAction") as action_class:
            self.plugin.initGui()
            self.plugin.unload()
            self.plugin.unload()

        self.plugin.iface.removeToolBarIcon.assert_called_once_with(action_class.return_value)
        self.assertIsNone(self.plugin.action)
        self.assertIsNone(self.plugin._pending_login_listener)
        self.assertIsNone(SessionManager._login_prompt)
        self.assertEqual(self.plugin._crash_logger.stop.call_count, 2)


if __name__ == "__main__":
    unittest.main()
