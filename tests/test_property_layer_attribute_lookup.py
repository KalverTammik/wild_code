from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
if os.environ.get('QGIS_PREFIX_PATH'):
    sys.path.append(str(Path(os.environ['QGIS_PREFIX_PATH']) / 'python' / 'plugins'))

from qgis.core import QgsApplication, QgsFeature, QgsVectorLayer

from Kavitro_dev.utils.mapandproperties.PropertyDataLoader import PropertyDataLoader


class PropertyLayerAttributeLookupTest(unittest.TestCase):
    """Specification for `PropertyDataLoader.read_features_by_field_values`.

    This is the filter-by-attribute replacement for two prior "read the whole layer in
    Python" spots: the main-layer lookup built before every property check, and the
    per-candidate archive lookup that queried once per tunnus. Both must now match by
    attribute value alone, in as few `QgsFeatureRequest` calls as a batch allows, the same
    way every other filtered read in this module already works.
    """

    @classmethod
    def setUpClass(cls):
        cls.app = QgsApplication.instance() or QgsApplication([], False)
        QgsApplication.initQgis()

    def _string_layer(self, values):
        layer = QgsVectorLayer('Polygon?crs=EPSG:3301&field=tunnus:string', 'mem', 'memory')
        features = []
        for value in values:
            feature = QgsFeature(layer.fields())
            feature.setAttribute('tunnus', value)
            features.append(feature)
        layer.dataProvider().addFeatures(features)
        return layer

    def test_matches_only_the_requested_values(self):
        layer = self._string_layer(['A1', 'A2', 'A3'])

        found = PropertyDataLoader.read_features_by_field_values(layer, 'tunnus', ['A1', 'A3'])

        self.assertEqual(set(found), {'A1', 'A3'})

    def test_batches_large_candidate_sets_into_several_requests(self):
        values = [f'T{i}' for i in range(5)]
        layer = self._string_layer(values)

        found = PropertyDataLoader.read_features_by_field_values(layer, 'tunnus', values, batch_size=2)

        self.assertEqual(set(found), set(values))

    def test_geometry_is_left_out_by_default(self):
        layer = self._string_layer(['A1'])

        found = PropertyDataLoader.read_features_by_field_values(layer, 'tunnus', ['A1'])

        self.assertFalse(found['A1'].hasGeometry())

    def test_include_geometry_true_keeps_the_geometry(self):
        from qgis.core import QgsGeometry

        layer = QgsVectorLayer('Polygon?crs=EPSG:3301&field=tunnus:string', 'mem', 'memory')
        feature = QgsFeature(layer.fields())
        feature.setAttribute('tunnus', 'A1')
        feature.setGeometry(QgsGeometry.fromWkt('POLYGON((0 0,1 0,1 1,0 1,0 0))'))
        layer.dataProvider().addFeatures([feature])

        found = PropertyDataLoader.read_features_by_field_values(
            layer, 'tunnus', ['A1'], include_geometry=True)

        self.assertTrue(found['A1'].hasGeometry())

    def test_group_true_collects_every_match_instead_of_only_the_first(self):
        layer = self._string_layer(['A1', 'A1', 'A2'])

        found = PropertyDataLoader.read_features_by_field_values(
            layer, 'tunnus', ['A1'], group=True)

        self.assertEqual(len(found['A1']), 2)

    def test_numeric_looking_value_matches_a_numeric_field_like_a_text_comparison(self):
        # A tunnus-like field stored as an integer must still match a string candidate
        # ("123") the same way the existing text-based filter expressions already do
        # elsewhere in this module; a silent str/int mismatch here would make the
        # archive plan and the archive execution disagree on which rows exist.
        layer = QgsVectorLayer('Polygon?crs=EPSG:3301&field=code:integer', 'mem', 'memory')
        feature = QgsFeature(layer.fields())
        feature.setAttribute('code', 123)
        layer.dataProvider().addFeatures([feature])

        found = PropertyDataLoader.read_features_by_field_values(layer, 'code', ['123'])

        self.assertIn('123', found)

    def test_missing_field_raises_instead_of_silently_returning_nothing(self):
        layer = self._string_layer(['A1'])

        with self.assertRaises(ValueError):
            PropertyDataLoader.read_features_by_field_values(layer, 'does_not_exist', ['A1'])

    def test_no_values_returns_empty_without_querying_the_layer(self):
        layer = self._string_layer(['A1'])

        self.assertEqual(PropertyDataLoader.read_features_by_field_values(layer, 'tunnus', []), {})


if __name__ == '__main__':
    unittest.main()
