"""A feature whose coordinates cannot be transformed to the target CRS is never written and is reported to the user."""
from __future__ import annotations

import math
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from qgis.core import (
    Qgis,
    QgsApplication,
    QgsCoordinateReferenceSystem,
    QgsCoordinateTransform,
    QgsFeature,
    QgsGeometry,
    QgsPointXY,
    QgsProject,
    QgsVectorLayer,
)
from qgis.PyQt.QtCore import QCoreApplication, QEvent
from qgis.PyQt.QtWidgets import QWidget

from Kavitro_dev.Logs.python_fail_logger import PythonFailLogger
from Kavitro_dev.languages.language_manager import LanguageManager
from Kavitro_dev.languages.translation_keys import TranslationKeys
from Kavitro_dev.modules.Settings.GeospatialLayerMapperDialog import GeospatialLayerMapperDialog
from Kavitro_dev.utils.messagesHelper import ModernMessageDialog

OUTSIDE_WGS84 = "POINT(1000000 1000000)"
INSIDE_ESTONIA = "POINT(24 58)"


def _wgs_to_estonian() -> QgsCoordinateTransform:
    return QgsCoordinateTransform(
        QgsCoordinateReferenceSystem("EPSG:4326"),
        QgsCoordinateReferenceSystem("EPSG:3301"),
        QgsProject.instance().transformContext(),
    )


def _layer(crs: str, rows: list[tuple[str, str]]) -> QgsVectorLayer:
    layer = QgsVectorLayer(f"Point?crs={crs}&field=name:string&field=ext_job_id:string", "layer", "memory")
    features = []
    for wkt, name in rows:
        feature = QgsFeature(layer.fields())
        feature.setGeometry(QgsGeometry.fromWkt(wkt))
        feature.setAttribute("name", name)
        feature.setAttribute("ext_job_id", name)
        features.append(feature)
    layer.dataProvider().addFeatures(features)
    return layer


class TransformedGeometryTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QgsApplication.instance() or QgsApplication([], True)
        QgsApplication.initQgis()

    def setUp(self) -> None:
        patcher = patch.object(PythonFailLogger, "log_exception")
        self.log = patcher.start()
        self.addCleanup(patcher.stop)

    def test_coordinates_outside_the_target_crs_give_none_and_leave_the_source_untouched(self) -> None:
        geometry = QgsGeometry.fromWkt(OUTSIDE_WGS84)

        self.assertIsNone(GeospatialLayerMapperDialog._transformed_geometry(geometry, _wgs_to_estonian()))
        self.assertEqual(geometry.asWkt(), "Point (1000000 1000000)")
        self.assertEqual(self.log.call_args.kwargs["event"], "geospatial_mapper_geometry_transform_failed")

    def test_successful_transform_returns_a_copy(self) -> None:
        geometry = QgsGeometry.fromWkt(INSIDE_ESTONIA)

        result = GeospatialLayerMapperDialog._transformed_geometry(geometry, _wgs_to_estonian())

        self.assertAlmostEqual(result.asPoint().x(), 500000.0, delta=1.0)
        self.assertEqual(geometry.asWkt(), "Point (24 58)")
        self.log.assert_not_called()

    def test_a_failure_result_code_gives_none(self) -> None:
        with patch.object(QgsGeometry, "transform", return_value=Qgis.GeometryOperationResult.NothingHappened):
            result = GeospatialLayerMapperDialog._transformed_geometry(QgsGeometry.fromWkt(INSIDE_ESTONIA), _wgs_to_estonian())

        self.assertIsNone(result)
        self.assertEqual(self.log.call_count, 1)

    def test_non_finite_coordinates_after_a_reported_success_give_none(self) -> None:
        broken = QgsGeometry.fromPointXY(QgsPointXY(math.inf, 58.0))
        with patch.object(QgsGeometry, "transform", return_value=Qgis.GeometryOperationResult.Success):
            result = GeospatialLayerMapperDialog._transformed_geometry(broken, _wgs_to_estonian())

        self.assertIsNone(result)


class TransferFeaturesTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QgsApplication.instance() or QgsApplication([], True)
        QgsApplication.initQgis()

    def setUp(self) -> None:
        for name in ("show_warning", "show_info", "ask_yes_no"):
            patcher = patch.object(ModernMessageDialog, name)
            setattr(self, name, patcher.start())
            self.addCleanup(patcher.stop)
        log_patcher = patch.object(PythonFailLogger, "log_exception")
        log_patcher.start()
        self.addCleanup(log_patcher.stop)
        self.lang = LanguageManager("et")
        self.window = QWidget()

    def tearDown(self) -> None:
        self.window.hide()
        self.window.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)

    def _dialog(self, target: QgsVectorLayer) -> GeospatialLayerMapperDialog:
        return GeospatialLayerMapperDialog(lang_manager=self.lang, module_name="works", target_layer=target, parent=self.window)

    @staticmethod
    def _rows() -> list[dict[str, object]]:
        return [
            {"target": "name", "source": "name", "has_default": False, "default": None},
            {"target": "ext_job_id", "source": "ext_job_id", "has_default": False, "default": None},
        ]

    def _expected_error(self, count: int) -> str:
        return self.lang.translate(TranslationKeys.GEOSPATIAL_LAYER_MAPPER_GEOMETRY_TRANSFORM_FAILED).format(count=count)

    def test_untransformable_feature_is_not_inserted_and_is_reported(self) -> None:
        source = _layer("EPSG:4326", [(INSIDE_ESTONIA, "good"), (OUTSIDE_WGS84, "bad")])
        target = _layer("EPSG:3301", [])

        inserted, updated, skipped, errors = self._dialog(target)._transfer_features(source, self._rows())

        self.assertEqual((inserted, updated, skipped), (1, 0, 0))
        self.assertEqual(errors, [self._expected_error(1)])
        names = [feature["name"] for feature in target.getFeatures()]
        self.assertEqual(names, ["good"])
        for feature in target.getFeatures():
            box = feature.geometry().boundingBox()
            self.assertTrue(math.isfinite(box.xMaximum()) and math.isfinite(box.yMaximum()))
        # The source layer keeps its own coordinates.
        self.assertEqual(sorted(f.geometry().asWkt() for f in source.getFeatures()), ["Point (1000000 1000000)", "Point (24 58)"])

    def test_untransformable_feature_does_not_update_an_existing_target(self) -> None:
        source = _layer("EPSG:4326", [(OUTSIDE_WGS84, "job-1")])
        target = _layer("EPSG:3301", [("POINT(500000 6400000)", "job-1")])
        target.dataProvider().changeAttributeValues({next(target.getFeatures()).id(): {0: "old"}})

        inserted, updated, skipped, errors = self._dialog(target)._transfer_features(source, self._rows())

        self.assertEqual((inserted, updated, skipped), (0, 0, 0))
        self.assertEqual(errors, [self._expected_error(1)])
        feature = next(target.getFeatures())
        self.assertEqual(feature["name"], "old")
        self.assertEqual(feature.geometry().asWkt(), "Point (500000 6400000)")

    def test_user_sees_the_transform_failure_in_the_result_warning(self) -> None:
        source = _layer("EPSG:4326", [(OUTSIDE_WGS84, "bad")])
        target = _layer("EPSG:3301", [])
        dialog = self._dialog(target)
        self.ask_yes_no.return_value = True

        with patch.object(dialog._source_combo, "currentLayer", return_value=source):
            dialog._on_accept()

        self.show_info.assert_not_called()
        self.assertIn(self._expected_error(1), self.show_warning.call_args.args[1])
        self.assertEqual(target.featureCount(), 0)


if __name__ == "__main__":
    unittest.main()
