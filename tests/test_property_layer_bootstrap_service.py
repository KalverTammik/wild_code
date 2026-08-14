from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from PyQt5.QtCore import QVariant
from qgis.core import (
    QgsApplication,
    QgsFeature,
    QgsField,
    QgsFields,
    QgsGeometry,
    QgsProject,
    QgsVectorLayer,
    QgsWkbTypes,
)

from Kavitro_dev.constants.cadastral_fields import Katastriyksus
from Kavitro_dev.constants.settings_keys import SettingsService
from Kavitro_dev.utils.maa_amet.Maa_amet_field_comparer import MaaAmetFieldComparer
from Kavitro_dev.utils.MapTools.MapHelpers import FeatureActions
from Kavitro_dev.utils.mapandproperties.ArchiveLayerHandler import (
    ArchiveLayerHandler,
    GPKGHelpers,
)
from Kavitro_dev.utils.mapandproperties.property_layer_bootstrap_service import (
    PropertyLayerBootstrapService,
)
from Kavitro_dev.utils.url_manager import Module


class PropertyLayerBootstrapServiceTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.qgis_app = QgsApplication([], False)
        cls.qgis_app.initQgis()

    @classmethod
    def tearDownClass(cls) -> None:
        QgsProject.instance().clear()
        cls.qgis_app.exitQgis()

    def setUp(self) -> None:
        QgsProject.instance().clear()
        self.settings = SettingsService()
        self.previous_main = self.settings.module_main_layer_name(Module.PROPERTY.value) or ""
        self.previous_archive = self.settings.module_archive_layer_name(Module.PROPERTY.value) or ""
        self.temp_dir = tempfile.TemporaryDirectory(prefix="kavitro_property_bootstrap_")

    def tearDown(self) -> None:
        QgsProject.instance().clear()
        if self.previous_main:
            self.settings.module_main_layer_name(Module.PROPERTY.value, value=self.previous_main)
        else:
            self.settings.module_main_layer_name(Module.PROPERTY.value, clear=True)
        if self.previous_archive:
            self.settings.module_archive_layer_name(Module.PROPERTY.value, value=self.previous_archive)
        else:
            self.settings.module_archive_layer_name(Module.PROPERTY.value, clear=True)
        self.temp_dir.cleanup()

    def test_creates_main_and_archive_with_generated_fields(self) -> None:
        source_layer = self._source_layer()
        target_path = os.path.join(self.temp_dir.name, "properties.gpkg")

        result = PropertyLayerBootstrapService.create_layers(source_layer, target_path)

        self.assertTrue(result.ok, result.details)
        self.assertGreaterEqual(result.main_layer.fields().lookupField(Katastriyksus.search_field), 0)
        self.assertGreaterEqual(
            result.archive_layer.fields().lookupField(ArchiveLayerHandler.ARCHIVE_DATE_FIELD),
            0,
        )
        self.assertEqual(
            self.settings.module_main_layer_name(Module.PROPERTY.value),
            PropertyLayerBootstrapService.DEFAULT_MAIN_LAYER_NAME,
        )
        self.assertEqual(
            self.settings.module_archive_layer_name(Module.PROPERTY.value),
            PropertyLayerBootstrapService.DEFAULT_ARCHIVE_LAYER_NAME,
        )

        self.assertTrue(result.main_layer.startEditing())
        copied, error = FeatureActions.copy_feature_to_layer(
            next(source_layer.getFeatures()),
            result.main_layer,
        )
        self.assertTrue(copied, error)
        self.assertTrue(result.main_layer.commitChanges())
        main_feature = next(result.main_layer.getFeatures())
        self.assertIn("12345:678:9012", main_feature.attribute(Katastriyksus.search_field))
        self.assertIn("Testi 1", main_feature.attribute(Katastriyksus.search_field))

        self.assertTrue(result.archive_layer.startEditing())
        copied, error = FeatureActions.copy_feature_to_layer(
            main_feature,
            result.archive_layer,
            attribute_overrides={
                ArchiveLayerHandler.ARCHIVE_DATE_FIELD:
                    ArchiveLayerHandler.current_archive_timestamp(),
            },
        )
        self.assertTrue(copied, error)
        self.assertTrue(result.archive_layer.commitChanges())
        archive_feature = next(result.archive_layer.getFeatures())
        self.assertTrue(archive_feature.attribute(ArchiveLayerHandler.ARCHIVE_DATE_FIELD))

    def test_preserves_unrelated_layers_in_existing_geopackage(self) -> None:
        source_layer = self._source_layer()
        target_path = os.path.join(self.temp_dir.name, "existing.gpkg")
        unrelated_fields = QgsFields()
        unrelated_fields.append(QgsField("name", QVariant.String))
        self.assertTrue(
            GPKGHelpers.create_empty_gpkg_layer(
                target_path,
                "Unrelated",
                QgsWkbTypes.Point,
                source_layer.crs(),
                unrelated_fields,
                overwrite=False,
            )
        )

        result = PropertyLayerBootstrapService.create_layers(source_layer, target_path)

        self.assertTrue(result.ok, result.details)
        self.assertTrue(GPKGHelpers.gpkg_layer_exists(target_path, "Unrelated"))

    def test_rejects_source_missing_required_fields_without_creating_file(self) -> None:
        source_layer = self._source_layer()
        source_layer.dataProvider().deleteAttributes(
            [source_layer.fields().lookupField(Katastriyksus.tunnus)]
        )
        source_layer.updateFields()
        target_path = os.path.join(self.temp_dir.name, "invalid.gpkg")

        result = PropertyLayerBootstrapService.create_layers(source_layer, target_path)

        self.assertFalse(result.ok)
        self.assertEqual(
            result.error_code,
            PropertyLayerBootstrapService.ERROR_MISSING_FIELDS,
        )
        self.assertIn(Katastriyksus.tunnus, result.details)
        self.assertFalse(os.path.exists(target_path))

    def test_removes_new_geopackage_when_archive_creation_fails(self) -> None:
        source_layer = self._source_layer()
        target_path = os.path.join(self.temp_dir.name, "failed.gpkg")

        with patch.object(
            ArchiveLayerHandler,
            "resolve_or_create_archive_layer",
            return_value=None,
        ):
            result = PropertyLayerBootstrapService.create_layers(source_layer, target_path)

        self.assertFalse(result.ok)
        self.assertEqual(
            result.error_code,
            PropertyLayerBootstrapService.ERROR_CREATE_ARCHIVE,
        )
        self.assertFalse(os.path.exists(target_path))
        self.assertEqual(
            self.settings.module_main_layer_name(Module.PROPERTY.value) or "",
            self.previous_main,
        )
        self.assertEqual(
            self.settings.module_archive_layer_name(Module.PROPERTY.value) or "",
            self.previous_archive,
        )

    @staticmethod
    def _source_layer() -> QgsVectorLayer:
        layer = QgsVectorLayer("Polygon?crs=EPSG:3301", "maa_amet_source", "memory")
        required_fields, optional_fields = MaaAmetFieldComparer.logical_fields()
        for field_name in required_fields + optional_fields:
            layer.dataProvider().addAttributes([QgsField(field_name, QVariant.String)])
        layer.updateFields()

        feature = QgsFeature(layer.fields())
        feature.setGeometry(
            QgsGeometry.fromWkt("POLYGON((500000 6500000,500010 6500000,500010 6500010,500000 6500010,500000 6500000))")
        )
        feature.setAttribute(Katastriyksus.tunnus, "12345:678:9012")
        feature.setAttribute(Katastriyksus.l_aadress, "Testi 1")
        feature.setAttribute(Katastriyksus.ay_nimi, "Testiküla")
        feature.setAttribute(Katastriyksus.ov_nimi, "Testivald")
        feature.setAttribute(Katastriyksus.mk_nimi, "Testimaa")
        added, _features = layer.dataProvider().addFeatures([feature])
        if not added:
            raise AssertionError("Could not prepare source feature")
        return layer


if __name__ == "__main__":
    unittest.main()
