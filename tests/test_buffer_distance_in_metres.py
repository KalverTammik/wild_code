"""Buffer distances and easement areas are metres whatever the layer CRS.

Found 2026-11-23: the project and easement previews passed the "m" value of the dialog straight to
native:buffer, which reads it in the layer's units (2 m became 2 degrees in EPSG:4326), and the
easement main layer area was geometry.area() in the layer's square units.
"""
import math
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
if os.environ.get("QGIS_PREFIX_PATH"):
    sys.path.append(str(Path(os.environ["QGIS_PREFIX_PATH"]) / "python" / "plugins"))

from qgis.core import (
    QgsApplication,
    QgsCoordinateReferenceSystem,
    QgsFeature,
    QgsGeometry,
    QgsPointXY,
    QgsProject,
    QgsVectorLayer,
)

from Kavitro_dev.modules.easements.easement_property_edges import measure_geometry_area_sqm
from Kavitro_dev.utils.layers.layer_processing_service import LayerProcessingService

_APP = QgsApplication.instance() or QgsApplication([], False)


def _point_layer(crs: str, x: float, y: float) -> QgsVectorLayer:
    layer = QgsVectorLayer(f"Point?crs={crs}", "points", "memory")
    feature = QgsFeature(layer.fields())
    feature.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(x, y)))
    layer.dataProvider().addFeatures([feature])
    return layer


class MetresInLayerUnitsTest(unittest.TestCase):
    def test_metres_feet_and_degrees(self):
        self.assertAlmostEqual(LayerProcessingService.metres_in_layer_units(_point_layer("EPSG:3301", 0, 0), 2), 2.0)
        # NAD83 / Pennsylvania South (ftUS)
        self.assertAlmostEqual(LayerProcessingService.metres_in_layer_units(_point_layer("EPSG:2272", 0, 0), 1),
                               3.2808, places=3)
        self.assertIsNone(LayerProcessingService.metres_in_layer_units(_point_layer("EPSG:4326", 24, 59), 2))

    def test_the_metric_crs_is_the_project_crs_only_when_it_is_in_metres(self):
        project = QgsProject.instance()
        original = project.crs()
        self.addCleanup(project.setCrs, original)
        project.setCrs(QgsCoordinateReferenceSystem("EPSG:3857"))
        self.assertEqual(LayerProcessingService.metric_crs().authid(), "EPSG:3857")
        project.setCrs(QgsCoordinateReferenceSystem("EPSG:4326"))
        self.assertEqual(LayerProcessingService.metric_crs().authid(), "EPSG:3301")


class BufferPipelineTest(unittest.TestCase):
    def run_buffer(self, layer):
        calls = []

        def run(algorithm, parameters, **options):
            calls.append((algorithm, parameters, options))
            return layer

        with patch.object(LayerProcessingService, "run_processing_to_memory", side_effect=run):
            LayerProcessingService.buffer_layer(layer, distance=2.0, result_layer_name="r", make_visible=False)
        return calls

    def test_a_metric_layer_is_buffered_once_in_its_own_units(self):
        calls = self.run_buffer(_point_layer("EPSG:3301", 540000, 6580000))
        self.assertEqual([c[0] for c in calls], ["native:buffer"])
        self.assertEqual(calls[0][1]["DISTANCE"], 2.0)
        self.assertFalse(calls[0][2]["make_visible"])

    def test_a_layer_in_degrees_is_buffered_in_a_metric_crs_and_brought_back(self):
        layer = _point_layer("EPSG:4326", 24.7, 59.4)
        calls = self.run_buffer(layer)
        self.assertEqual([c[0] for c in calls], ["native:reprojectlayer", "native:buffer", "native:reprojectlayer"])
        self.assertEqual(calls[0][1]["TARGET_CRS"].authid(), LayerProcessingService.metric_crs().authid())
        self.assertEqual(calls[1][1]["DISTANCE"], 2.0)  # metres, in the metric CRS
        self.assertEqual(calls[2][1]["TARGET_CRS"], layer.crs())
        # Only the last step registers the result with the caller's options.
        self.assertFalse(calls[0][2]["register_result"])
        self.assertFalse(calls[1][2]["register_result"])
        self.assertFalse(calls[2][2]["make_visible"])


class RealBufferTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            from processing.core.Processing import Processing
            from qgis.analysis import QgsNativeAlgorithms
            Processing.initialize()
            if not QgsApplication.processingRegistry().providerById("native"):
                QgsApplication.processingRegistry().addProvider(QgsNativeAlgorithms())
        except Exception as exc:  # noqa: BLE001 - no processing in this environment
            raise unittest.SkipTest(f"QGIS processing unavailable: {exc}") from exc

    def test_a_100_m_buffer_in_degrees_is_100_m(self):
        layer = _point_layer("EPSG:4326", 24.7, 59.4)
        result = LayerProcessingService.buffer_layer(layer, distance=100.0, result_layer_name="t", register_result=False)
        self.assertIsNotNone(result)
        self.assertEqual(result.crs().authid(), "EPSG:4326")
        geometry = next(result.getFeatures()).geometry()
        area = measure_geometry_area_sqm(geometry, result)
        self.assertAlmostEqual(area / (math.pi * 100 ** 2), 1.0, delta=0.05)


class AreaInSquareMetresTest(unittest.TestCase):
    def test_area_in_degrees_layer_is_square_metres(self):
        layer = QgsVectorLayer("Polygon?crs=EPSG:4326", "a", "memory")
        # Roughly 100 m x 100 m at 59.4° N.
        dx, dy = 100 / (111320 * math.cos(math.radians(59.4))), 100 / 111320
        geometry = QgsGeometry.fromPolygonXY([[QgsPointXY(24.7, 59.4), QgsPointXY(24.7 + dx, 59.4),
                                               QgsPointXY(24.7 + dx, 59.4 + dy), QgsPointXY(24.7, 59.4 + dy)]])
        self.assertAlmostEqual(measure_geometry_area_sqm(geometry, layer) / 10000, 1.0, delta=0.02)


if __name__ == "__main__":
    unittest.main()
