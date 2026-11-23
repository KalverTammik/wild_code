"""A GUI-thread request slow enough to open the modal wait window is logged with its
operation and the plugin functions that sent it, so those flows can be moved to a worker."""
from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
PLUGIN_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLUGIN_ROOT.parent))
if os.environ.get("QGIS_PREFIX_PATH"):
    sys.path.append(str(Path(os.environ["QGIS_PREFIX_PATH"]) / "python" / "plugins"))

from qgis.core import QgsApplication

from Kavitro_dev.Logs.switch_logger import SwitchLogger
from Kavitro_dev.python import api_client as client_module
from Kavitro_dev.python.api_client import APIClient, graphql_operation_name, plugin_callers

_APP = QgsApplication.instance() or QgsApplication([], False)


def _ok_response():
    response = Mock(status_code=200)
    response.json.return_value = {"data": {}}
    return response


class OperationNameTest(unittest.TestCase):
    def test_named_and_anonymous_operations(self):
        self.assertEqual(graphql_operation_name("query property(\n  $id: ID!\n) { property(id: $id) { id } }"), "property")
        self.assertEqual(graphql_operation_name("mutation createTask($input: CreateTaskInput!) {"), "createTask")
        self.assertEqual(graphql_operation_name("  {\n me { id } }"), "me")
        self.assertEqual(graphql_operation_name("subquery x"), "?")
        self.assertEqual(graphql_operation_name(None), "?")


class CallerTest(unittest.TestCase):
    def test_nearest_plugin_frames_outside_the_api_layer(self):
        def flow_step():
            return plugin_callers(limit=2)

        callers = flow_step()
        self.assertEqual(
            callers,
            "tests/test_api_gui_thread_wait_log.py:flow_step < "
            "tests/test_api_gui_thread_wait_log.py:test_nearest_plugin_frames_outside_the_api_layer",
        )


class WaitLogTest(unittest.TestCase):
    QUERY = "query tasks($first: Int) { tasks(first: $first) { edges { node { id } } } }"

    def setUp(self):
        self.log = patch.object(SwitchLogger, "log").start()
        self.addCleanup(patch.stopall)
        self.send = patch.object(client_module, "send_api_request", return_value=_ok_response()).start()
        self.client = APIClient(session_manager=Mock())

    def run_request(self, seconds, *, main_thread=True):
        with patch.object(client_module.time, "monotonic", side_effect=[100.0, 100.0 + seconds]):
            return self.client._execute(
                self.QUERY, lambda url, headers: None,
                require_auth=False, attempts=1, json_body=True, is_main_thread=main_thread,
            )

    def test_slow_gui_thread_request_is_logged(self):
        self.run_request(0.5)
        self.log.assert_called_once()
        args, kwargs = self.log.call_args
        self.assertEqual(args, ("api_gui_thread_wait",))
        self.assertEqual(kwargs["module"], "api")
        self.assertEqual(kwargs["extra"]["operation"], "tasks")
        self.assertEqual(kwargs["extra"]["seconds"], "0.50")
        self.assertIn("tests/test_api_gui_thread_wait_log.py:run_request", kwargs["extra"]["caller"])
        self.assertNotIn("python/", kwargs["extra"]["caller"])

    def test_fast_or_worker_requests_are_not_logged(self):
        self.run_request(0.39)
        self.run_request(5.0, main_thread=False)
        self.log.assert_not_called()

    def test_a_failed_slow_request_is_logged_too(self):
        self.send.side_effect = RuntimeError("cancelled")
        with self.assertRaises(Exception):
            self.run_request(2.0)
        self.assertEqual(self.log.call_args.kwargs["extra"]["seconds"], "2.00")

    def test_the_log_carries_no_token_or_variables(self):
        with patch.object(client_module.time, "monotonic", side_effect=[0.0, 1.0]):
            self.client._execute(
                'mutation updateTask($input: UpdateTaskInput! = {name: "secret"}) { updateTask(input: $input) { id } }',
                lambda url, headers: None, require_auth=False, attempts=1, json_body=True, is_main_thread=True,
            )
        line = repr(self.log.call_args)
        self.assertIn("updateTask", line)
        self.assertNotIn("secret", line)
        self.assertNotIn("Bearer", line)


if __name__ == "__main__":
    unittest.main()
