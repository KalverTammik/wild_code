"""An empty field is NULL or None, depending on the QGIS version and the provider; neither is a value."""
import unittest
from unittest.mock import patch

from qgis.core import NULL, QgsApplication, QgsFeature, QgsVectorLayer

from Kavitro_dev.constants.cadastral_fields import Katastriyksus
from Kavitro_dev.modules.easements.easement_layer_service import EasementLayerService
from Kavitro_dev.utils.MapTools.MapHelpers import FeatureActions

_APP = QgsApplication.instance() or QgsApplication([], False)


class EmptyLayerValueTest(unittest.TestCase):
    def _layer(self, field: str, kind: str, values: list) -> QgsVectorLayer:
        layer = QgsVectorLayer(f"None?field={field}:{kind}", "values", "memory")
        features = []
        for value in values:
            feature = QgsFeature(layer.fields())
            if value is not Ellipsis:  # Ellipsis: the attribute is never set
                feature.setAttributes([value])
            features.append(feature)
        self.assertTrue(layer.dataProvider().addFeatures(features)[0])
        return layer

    def test_an_empty_status_is_not_offered_as_a_status(self) -> None:
        layer = self._layer("seisund", "string", [..., NULL, "Kehtiv", "  ", "Kavandatav"])

        with patch.object(EasementLayerService, "resolve_status_field_name", return_value="seisund"):
            options = EasementLayerService.layer_status_value_options(layer)

        self.assertEqual(options, ["Kavandatav", "Kehtiv"])

    def test_an_empty_feature_number_does_not_stop_the_next_free_one(self) -> None:
        layer = self._layer(Katastriyksus.fid, "integer", [..., NULL, 1])

        self.assertEqual(FeatureActions.next_free_fid_int_value(layer), 2)


if __name__ == "__main__":
    unittest.main()
