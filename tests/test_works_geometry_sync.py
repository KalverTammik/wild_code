from __future__ import annotations

import json
import os
import sys
import threading
import unittest
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
if os.environ.get("QGIS_PREFIX_PATH"):
    sys.path.append(str(Path(os.environ["QGIS_PREFIX_PATH"]) / "python" / "plugins"))

from property_fixtures import wait_until
from qgis.core import QgsApplication, QgsFeature, QgsGeometry, QgsPointXY, QgsVectorLayer, QgsWkbTypes

from Kavitro_dev.modules.works import works_sync_service as sync_module
from Kavitro_dev.modules.works.works_layer_service import WorksLayerService
from Kavitro_dev.modules.works.works_sync_service import WorksSyncService
from Kavitro_dev.python.api_actions import APIModuleActions
from Kavitro_dev.utils.geometry_payload import GeometryPayloadService

X, Y = 630385.62, 6457752.97
MOVED_X = X + 25.0


def point_payload(x: float, y: float, **style) -> dict:
    return {"type": "Point", "coordinates": [x, y], **style}


class _QgisTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QgsApplication.instance() or QgsApplication([], False)
        QgsApplication.initQgis()


class GeometryPayloadTest(_QgisTest):
    def _parse(self, payload):
        return GeometryPayloadService.to_qgs_geometry(payload, module="works", error_event="test")

    def test_styled_point_becomes_a_geometry(self) -> None:
        geometry = self._parse(point_payload(X, Y, color="transparent", icon="fa6-solid:person-digging"))

        self.assertTrue(geometry.equals(QgsGeometry.fromPointXY(QgsPointXY(X, Y))))

    def test_json_text_is_accepted(self) -> None:
        geometry = self._parse(json.dumps(point_payload(X, Y)))

        self.assertTrue(geometry.equals(QgsGeometry.fromPointXY(QgsPointXY(X, Y))))

    def test_what_the_plugin_sends_reads_back_unchanged(self) -> None:
        original = QgsGeometry.fromPointXY(QgsPointXY(630385.6212345678, 6457752.9798765432))
        sent = GeometryPayloadService.from_qgs_geometry(original, module="works", error_event="test")

        self.assertTrue(self._parse(json.loads(json.dumps(sent))).equals(original))

    def test_payload_that_is_not_a_geometry_gives_none(self) -> None:
        with patch("Kavitro_dev.utils.geometry_payload.PythonFailLogger.log_exception") as log_exception:
            for payload in (None, "{nonsense", "null", {}, {"type": "Feature"}, {"type": "Point", "coordinates": []}):
                with self.subTest(payload=payload):
                    self.assertIsNone(self._parse(payload))

        log_exception.assert_not_called()


class GeometryForLayerTest(_QgisTest):
    def test_location_in_the_layer_crs_is_accepted(self) -> None:
        layer = QgsVectorLayer("Point?crs=EPSG:3301", "works", "memory")

        geometry = WorksLayerService.geometry_for_layer(point_payload(X, Y), layer)

        self.assertTrue(geometry.equals(QgsGeometry.fromPointXY(QgsPointXY(X, Y))))

    def test_longitude_latitude_cannot_land_on_a_projected_layer(self) -> None:
        layer = QgsVectorLayer("Point?crs=EPSG:3301", "works", "memory")

        self.assertIsNone(WorksLayerService.geometry_for_layer(point_payload(26.5, 58.2), layer))

    def test_longitude_latitude_is_a_location_on_a_geographic_layer(self) -> None:
        layer = QgsVectorLayer("Point?crs=EPSG:4326", "works", "memory")

        self.assertIsNotNone(WorksLayerService.geometry_for_layer(point_payload(26.5, 58.2), layer))

    def test_other_geometry_type_is_refused(self) -> None:
        layer = QgsVectorLayer("Point?crs=EPSG:3301", "works", "memory")
        line = {"type": "LineString", "coordinates": [[X, Y], [MOVED_X, Y]]}

        self.assertIsNone(WorksLayerService.geometry_for_layer(line, layer))

    def test_point_is_converted_for_a_multipoint_layer(self) -> None:
        layer = QgsVectorLayer("MultiPoint?crs=EPSG:3301", "works", "memory")

        geometry = WorksLayerService.geometry_for_layer(point_payload(X, Y), layer)

        self.assertEqual(QgsWkbTypes.flatType(geometry.wkbType()), QgsWkbTypes.MultiPoint)


class WorksLocationSyncTest(_QgisTest):
    def _prepare(self, uri: str, start: QgsGeometry, task: dict) -> None:
        self.layer = QgsVectorLayer(f"{uri}?crs=EPSG:3301&field=ext_job_id:string&field=ext_job_name:string", "w", "memory")
        feature = QgsFeature(self.layer.fields())
        feature.setAttributes(["1", "Original"])
        feature.setGeometry(start)
        self.layer.dataProvider().addFeatures([feature])
        self.feature_id = next(self.layer.getFeatures()).id()

        self.commits = []
        self.layer.committedGeometriesChanges.connect(lambda _layer_id, changed: self.commits.append(dict(changed)))
        for active in (
            patch.object(WorksLayerService, "resolve_main_layer", return_value=self.layer),
            patch.object(APIModuleActions, "get_tasks_by_ids", return_value={"1": {"id": "1", "name": "From server", **task}}),
        ):
            active.start()
            self.addCleanup(active.stop)
        write = patch.object(APIModuleActions, "update_task_geometry")
        self.write_back = write.start()
        self.addCleanup(write.stop)
        log = patch.object(sync_module.PythonFailLogger, "log")
        self.log = log.start()
        self.addCleanup(log.stop)

        self.service = WorksSyncService()
        self.addCleanup(self.service.detach)

    def _sync(self) -> QgsFeature:
        done = threading.Event()
        self.service._request.finished.connect(lambda _result: done.set())
        self.service.sync_from_backend()
        wait_until(self, lambda: done.is_set() and not self.service._request.busy, attempts=150, message="sync did not finish")
        self.app.processEvents()
        return self.layer.getFeature(self.feature_id)

    def _logged(self, event: str) -> list:
        return [call for call in self.log.call_args_list if call.args[0] == event]

    def test_location_changed_in_kavitro_moves_the_work_and_keeps_the_old_one_in_the_log(self) -> None:
        start = QgsGeometry.fromPointXY(QgsPointXY(X, Y))
        self._prepare("Point", start, {"geometry": point_payload(MOVED_X, Y, icon="x")})

        feature = self._sync()

        self.assertAlmostEqual(feature.geometry().asPoint().x(), MOVED_X)
        moved = self._logged("works_sync_location_moved")
        self.assertEqual(len(moved), 1)
        self.assertEqual(moved[0].kwargs["extra"]["previous"], start.asWkt())

    def test_move_from_kavitro_is_not_sent_back_to_kavitro(self) -> None:
        self._prepare("Point", QgsGeometry.fromPointXY(QgsPointXY(X, Y)), {"geometry": point_payload(MOVED_X, Y)})

        self._sync()

        self.assertEqual(len(self.commits), 1)
        self.write_back.assert_not_called()

    def test_same_location_writes_nothing_to_the_layer(self) -> None:
        for uri, start in (
            ("Point", QgsGeometry.fromPointXY(QgsPointXY(X, Y))),
            ("MultiPoint", QgsGeometry.fromWkt(f"MultiPoint(({X} {Y}))")),
        ):
            with self.subTest(uri=uri):
                self._prepare(uri, start, {"geometry": point_payload(X, Y)})

                feature = self._sync()

                self.assertEqual(self.commits, [])
                self.assertEqual(self._logged("works_sync_location_moved"), [])
                self.assertTrue(feature.geometry().equals(start))

    def test_foreign_coordinates_leave_the_location_but_still_update_the_fields(self) -> None:
        start = QgsGeometry.fromPointXY(QgsPointXY(X, Y))
        self._prepare("Point", start, {"geometry": point_payload(26.5, 58.2)})

        feature = self._sync()

        self.assertTrue(feature.geometry().equals(start))
        self.assertEqual(feature["ext_job_name"], "From server")
        skipped = self._logged("works_sync_geometry_skipped")
        self.assertEqual(skipped[0].kwargs["extra"]["sample"], "1")

    def test_task_without_a_location_logs_no_skip(self) -> None:
        self._prepare("Point", QgsGeometry.fromPointXY(QgsPointXY(X, Y)), {"geometry": None})

        self._sync()

        self.assertEqual(self._logged("works_sync_geometry_skipped"), [])


if __name__ == "__main__":
    unittest.main()
