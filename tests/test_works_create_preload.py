from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
if os.environ.get("QGIS_PREFIX_PATH"):
    sys.path.append(str(Path(os.environ["QGIS_PREFIX_PATH"]) / "python" / "plugins"))

from Kavitro_dev.modules.works import works_create_controller as controller_module
from Kavitro_dev.python import api_actions as actions_module
from Kavitro_dev.python.api_actions import APIModuleActions

PRIORITY_OPTIONS = [{"value": "", "label": "-"}, {"value": "HIGH", "label": "High"}]


class WorksCreatePreloadTest(unittest.TestCase):
    def setUp(self) -> None:
        self.controller = controller_module.WorksCreateController(lang_manager=Mock())

    def _fetch_payload(self, **priority_lookup) -> dict:
        with (
            patch.object(controller_module.FilterHelper, "get_filter_edges_by_key_and_module", return_value=[]),
            patch.object(APIModuleActions, "get_assignable_users", return_value=[{"id": "1", "name": "U"}]),
            patch.object(APIModuleActions, "get_current_user_id", return_value="1"),
            patch.object(APIModuleActions, "get_module_status_options", return_value=[]),
            patch.object(APIModuleActions, "get_task_priority_options", **priority_lookup),
        ):
            return self.controller._fetch_preload_payload()

    def test_worker_fetches_the_priority_options(self) -> None:
        payload = self._fetch_payload(return_value=PRIORITY_OPTIONS)

        self.assertEqual(payload["priority_options"], PRIORITY_OPTIONS)

    def test_failed_priority_lookup_keeps_the_rest_of_the_payload(self) -> None:
        payload = self._fetch_payload(side_effect=RuntimeError("offline"))

        self.assertEqual(payload["priority_options"], [])
        self.assertEqual(payload["default_responsible_id"], "1")

    def test_finished_preload_sends_no_request_on_the_gui_thread(self) -> None:
        # A slow GUI-thread request opens a modal wait, and a map click during it is lost.
        self.controller._preload_request_id = 7

        with patch.object(APIModuleActions, "get_task_priority_options") as lookup:
            self.controller._handle_preload_success({"priority_options": PRIORITY_OPTIONS}, 7)
            resolved = self.controller._resolve_priority_options()

        lookup.assert_not_called()
        self.assertEqual(resolved, PRIORITY_OPTIONS)


class TaskPriorityLookupTest(unittest.TestCase):
    def setUp(self) -> None:
        cache = patch.object(APIModuleActions, "_task_priority_values_cache", None)
        cache.start()
        self.addCleanup(cache.stop)

    def test_refused_lookup_is_sent_once_and_uses_the_defaults(self) -> None:
        client = Mock()
        client.send_query.side_effect = Exception("[WC-API][graphql] GraphQL introspection is not allowed")

        with (
            patch.object(actions_module, "APIClient", return_value=client),
            patch.object(actions_module, "GraphQLQueryLoader"),
            patch.object(actions_module.PythonFailLogger, "log_exception") as log_exception,
        ):
            results = [APIModuleActions.get_task_priority_values() for _ in range(3)]

        self.assertEqual(client.send_query.call_count, 1)
        log_exception.assert_called_once()
        self.assertEqual(results, [list(APIModuleActions._TASK_PRIORITY_DEFAULTS)] * 3)


if __name__ == "__main__":
    unittest.main()
