"""Geometry crosses the Kavitro boundary in EPSG:3301, whatever coordinate system the layer uses."""
from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from qgis.core import QgsApplication, QgsCoordinateReferenceSystem, QgsGeometry, QgsPointXY, QgsVectorLayer

from Kavitro_dev.modules.projects.projects_layer_service import ProjectsLayerService
from Kavitro_dev.modules.works.works_create_controller import WorksCreateController
from Kavitro_dev.modules.works.works_layer_service import WorksLayerService
from Kavitro_dev.utils.geometry_payload import GeometryPayloadService

_APP = QgsApplication.instance() or QgsApplication([], False)
X, Y = 630385.62, 6457752.98
ESTONIA = QgsGeometry.fromPointXY(QgsPointXY(X, Y))
WGS84 = QgsCoordinateReferenceSystem("EPSG:4326")


def in_wgs84(geometry: QgsGeometry) -> QgsGeometry:
    return GeometryPayloadService.transformed(geometry, GeometryPayloadService.kavitro_crs(), WGS84)


class OutgoingGeometryTest(unittest.TestCase):
    def assertEstonian(self, coordinates) -> None:
        self.assertAlmostEqual(coordinates[0], X, places=2)
        self.assertAlmostEqual(coordinates[1], Y, places=2)

    def test_a_layer_in_another_system_is_converted(self) -> None:
        layer = QgsVectorLayer("Point?crs=EPSG:4326", "p", "memory")
        geometry = in_wgs84(ESTONIA)
        before = geometry.asWkt()

        payload = ProjectsLayerService.backend_geometry_payload_from_geometry(geometry, layer)

        self.assertEstonian(payload["coordinates"])
        self.assertEqual(geometry.asWkt(), before, "the layer geometry itself must stay as it was")

    def test_a_kavitro_system_layer_is_sent_as_it_is(self) -> None:
        layer = QgsVectorLayer("Point?crs=EPSG:3301", "p", "memory")

        payload = ProjectsLayerService.backend_geometry_payload_from_geometry(ESTONIA, layer)

        self.assertEqual(payload["coordinates"], [X, Y])

    def test_nothing_is_sent_from_a_layer_without_a_system(self) -> None:
        layer = QgsVectorLayer("Point?crs=EPSG:3301", "p", "memory")
        layer.setCrs(QgsCoordinateReferenceSystem())

        with patch("Kavitro_dev.utils.geometry_payload.PythonFailLogger"):
            self.assertIsNone(ProjectsLayerService.backend_geometry_payload_from_geometry(ESTONIA, layer))

    def test_a_work_point_is_converted_too(self) -> None:
        layer = QgsVectorLayer("Point?crs=EPSG:4326", "w", "memory")
        on_map = in_wgs84(ESTONIA).asPoint()

        with patch.object(WorksLayerService, "_point_in_layer_crs", return_value=on_map):
            payload = WorksCreateController._backend_point_geometry_payload(on_map, layer, status_color="00ff00")

        self.assertEstonian(payload["coordinates"])
        self.assertIn("iconColor", payload)


class IncomingGeometryTest(unittest.TestCase):
    def test_what_was_sent_returns_to_the_same_place_on_the_layer(self) -> None:
        layer = QgsVectorLayer("Point?crs=EPSG:4326", "w", "memory")
        original = in_wgs84(ESTONIA)
        sent = WorksLayerService.backend_geometry_payload_from_geometry(original, layer)

        received = WorksLayerService.geometry_for_layer(sent, layer)

        self.assertAlmostEqual(received.asPoint().x(), original.asPoint().x(), places=8)
        self.assertAlmostEqual(received.asPoint().y(), original.asPoint().y(), places=8)


if __name__ == "__main__":
    unittest.main()
