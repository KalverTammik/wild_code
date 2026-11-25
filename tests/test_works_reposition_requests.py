"""Moving a work on the map sends one Kavitro request, not two.

Found 2026-11-22 (wait-time measurement): after the layer commit the Works sync read the whole task only for its
status colour (the icon colour at the location) and then sent the location. The card already has that colour,
so the move hands it over and the read is left out. Without a colour the sync still reads the task.
"""
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

from qgis.core import QgsApplication, QgsFeature, QgsGeometry, QgsPointXY, QgsVectorLayer

from Kavitro_dev.modules.works import works_card_actions as card_module
from Kavitro_dev.modules.works import works_reposition_controller as reposition_module
from Kavitro_dev.modules.works.works_layer_service import WorksLayerService
from Kavitro_dev.modules.works.works_sync_service import WorksSyncService
from Kavitro_dev.python.api_actions import APIModuleActions

_APP = QgsApplication.instance() or QgsApplication([], False)


class RepositionRequestsTest(unittest.TestCase):
    def setUp(self) -> None:
        self.layer = QgsVectorLayer("Point?crs=EPSG:3301&field=ext_job_id:string", "Tööd", "memory")
        feature = QgsFeature(self.layer.fields())
        feature.setAttributes(["7"])
        feature.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(1, 1)))
        self.layer.dataProvider().addFeatures([feature])
        self.feature_id = next(self.layer.getFeatures()).id()
        for target, name, value in (
            (WorksLayerService, "resolve_main_layer", self.layer),
            (APIModuleActions, "get_task_data", {"id": "7", "status": {"color": "00ff00"}}),
            (APIModuleActions, "update_task_geometry", True),
        ):
            patcher = patch.object(target, name, return_value=value)
            setattr(self, name, patcher.start())
            self.addCleanup(patcher.stop)
        logger = patch.object(reposition_module, "PythonFailLogger")
        logger.start()
        self.addCleanup(logger.stop)
        self.sync = WorksSyncService()
        self.assertIs(self.sync.attach(), self.layer)
        self.addCleanup(self.sync.detach)
        self.addCleanup(WorksSyncService._known_status_colors.clear)

    def move(self, status_color: str) -> tuple[bool, str]:
        controller = reposition_module.WorksRepositionController()
        controller._layer, controller._feature_id, controller._task_id = self.layer, self.feature_id, "7"
        controller._status_color = status_color
        return controller._apply_new_geometry(QgsPointXY(50, 60))

    def sent_icon_color(self) -> str:
        payload = self.update_task_geometry.call_args.args[1]
        return str(payload)

    def test_a_known_status_colour_sends_only_the_location(self) -> None:
        self.assertEqual(self.move("ff0000"), (True, ""))

        self.get_task_data.assert_not_called()
        self.update_task_geometry.assert_called_once()
        self.assertEqual(self.update_task_geometry.call_args.args[0], "7")
        self.assertIn("ff0000", self.sent_icon_color().lower())
        self.assertEqual(WorksSyncService._known_status_colors, {})

    def test_without_a_colour_the_task_is_read_first(self) -> None:
        self.assertEqual(self.move(""), (True, ""))

        self.get_task_data.assert_called_once_with("7")
        self.assertIn("00ff00", self.sent_icon_color().lower())

    def test_a_failed_commit_leaves_no_colour_behind(self) -> None:
        with patch.object(self.layer, "commitChanges", return_value=False):
            ok, _error = self.move("ff0000")
        self.assertFalse(ok)
        self.assertEqual(WorksSyncService._known_status_colors, {})

    def test_the_card_passes_its_status_colour(self) -> None:
        host = Mock(item_data={"id": "7", "status": {"id": "1", "color": "abcdef"}})
        actions = card_module.WorksCardActions.__new__(card_module.WorksCardActions)
        actions._host = host
        actions._reposition_controller = Mock()

        actions.reposition_on_map()

        self.assertEqual(actions._reposition_controller.start_reposition.call_args.kwargs["status_color"], "abcdef")


if __name__ == "__main__":
    unittest.main()
