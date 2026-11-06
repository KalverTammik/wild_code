from __future__ import annotations

import os
import sys
import time
import unittest
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
if os.environ.get("QGIS_PREFIX_PATH"):
    sys.path.append(str(Path(os.environ["QGIS_PREFIX_PATH"]) / "python" / "plugins"))

from qgis.core import QgsApplication, QgsPointXY

from Kavitro_dev.languages.language_manager import LanguageManager
from Kavitro_dev.modules.works import works_create_controller as controller_module
from Kavitro_dev.python import api_client, api_rate_limit, api_request_task
from Kavitro_dev.utils.SessionManager import SessionManager
from tests.test_api_rate_limit import FakeClock

REQUEST_SECONDS = 0.42
TASK = {"id": "77", "name": "Avarii", "status": {"id": "s", "color": "4FBF6B"}, "members": {"edges": []}}


class _Response:
    status_code = 200
    headers: dict = {}

    def __init__(self, data: dict) -> None:
        self._data = data

    def json(self) -> dict:
        return {"data": self._data}


class _FormDialog:
    Accepted = 1

    def __init__(self, **_kwargs) -> None:
        pass

    def exec_(self) -> int:
        return self.Accepted

    title_text = staticmethod(lambda: "Avarii")
    description_text = staticmethod(lambda: "")
    priority_value = staticmethod(lambda: "")
    selected_type_id = staticmethod(lambda: "t")
    selected_status_id = staticmethod(lambda: "s")
    selected_status_color = staticmethod(lambda: "4FBF6B")
    selected_responsible_id = staticmethod(lambda: "1")
    selected_responsible_label = staticmethod(lambda: "U")


class WorksCreateWaitWindowTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QgsApplication.instance() or QgsApplication([], False)

    def setUp(self) -> None:
        self.sent: list[str] = []
        self.windows: list = []
        self.messages: list[str] = []
        clock = FakeClock()
        service = controller_module.WorksLayerService
        original_show = api_request_task._RequestDialog.show

        def show_window(window):
            if not any(known is window for known in self.windows):
                self.windows.append(window)
            return original_show(window)

        def message(kind):
            return lambda _title, text, **_kwargs: self.messages.append(f"{kind}: {text}")

        for active in (
            patch.object(api_rate_limit, "PROCESS_RATE_LIMITER", api_rate_limit.RateLimitCoordinator(clock=clock.now, sleep=clock.sleep)),
            patch.object(api_request_task._RequestDialog, "show", show_window),
            patch.object(api_client.requests, "post", side_effect=self._post),
            patch.object(SessionManager, "get_token", return_value="token"),
            patch.object(controller_module, "WorksCreateDialog", _FormDialog),
            patch.object(controller_module, "iface", None),
            patch.object(controller_module.DialogHelpers, "exit_map_selection_mode"),
            patch.object(controller_module.ModernMessageDialog, "show_info", message("info")),
            patch.object(controller_module.ModernMessageDialog, "show_warning", message("warning")),
            patch.object(service, "resolve_main_layer", return_value=object()),
            patch.object(service, "insert_work_feature", return_value=(True, "")),
            patch.object(controller_module.WorksDescriptionService, "build_task_description", return_value=""),
            patch.object(service, "find_property_feature_at_point", return_value=object()),
            patch.object(service, "property_cadastral_number", return_value="66601:008:0138"),
            patch.object(controller_module.WorksCreateController, "_backend_point_geometry_payload", return_value={"type": "Point"}),
        ):
            active.start()
            self.addCleanup(active.stop)

        self.controller = controller_module.WorksCreateController(lang_manager=LanguageManager(language="et"))
        self.controller._cached_type_options = [{"id": "t", "label": "Avarii"}]
        self.controller._cached_assignable_users = [{"id": "1", "displayName": "U"}]
        self.controller._cached_priority_options = [{"value": "", "label": "-"}]
        self.controller._cached_default_responsible_id = "1"
        self.controller._cached_status_options = [{"id": "s", "name": "S", "color": "4FBF6B", "isDefault": True}]
        self.controller._cached_default_status_id = "s"
        self.controller._cached_default_status_color = "4FBF6B"

    def tearDown(self) -> None:
        self.app.processEvents()

    def _post(self, _url, json=None, headers=None, timeout=None) -> _Response:
        query = (json or {}).get("query", "")
        time.sleep(REQUEST_SECONDS)
        for name, data in (
            ("createTask", {"createTask": {"id": "77"}}),
            ("updateTask", {"updateTask": {"id": "77"}}),
            ("task(", {"task": TASK}),
            ("properties", {"properties": {"edges": [{"node": {"id": "p1", "cadastralUnitNumber": "66601:008:0138"}}]}}),
        ):
            if name in query:
                self.sent.append(name)
                return _Response(data)
        self.sent.append("?")
        return _Response({})

    def test_adding_a_work_shows_one_wait_window(self) -> None:
        self.controller._handle_point_selected(QgsPointXY(630385.62, 6457752.97))

        self.assertEqual([name for name in self.sent if name != "?"], ["createTask", "task(", "properties", "updateTask"])
        self.assertEqual(len(self.windows), 1)
        self.assertEqual(len(self.messages), 1, self.messages)
        self.assertTrue(self.messages[0].startswith("info: "), self.messages)


if __name__ == "__main__":
    unittest.main()
