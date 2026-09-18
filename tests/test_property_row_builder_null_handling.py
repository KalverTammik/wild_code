from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
if os.environ.get('QGIS_PREFIX_PATH'):
    sys.path.append(str(Path(os.environ['QGIS_PREFIX_PATH']) / 'python' / 'plugins'))

from qgis.core import NULL, QgsApplication, QgsFeature, QgsVectorLayer

from Kavitro_dev.constants.cadastral_fields import Katastriyksus as F
from Kavitro_dev.utils.mapandproperties.property_row_builder import PropertyRowBuilder


class PropertyRowBuilderNullHandlingTest(unittest.TestCase):
    """Specification for the one place that turns a raw feature attribute into row text.

    Three raw shapes reach `PropertyRowBuilder` from real cadastral layers: a plain
    Python `None` (a dict-like/mocked feature), the QGIS NULL sentinel (an unset
    attribute on a real `QgsFeature`), and a genuine value with surrounding
    whitespace. None of the three may ever surface as the text "NULL" in the table,
    which is the bug this refactor step removes at its single source.
    """

    @classmethod
    def setUpClass(cls):
        cls.app = QgsApplication.instance() or QgsApplication([], False)
        QgsApplication.initQgis()

    def _feature_with_address(self, value):
        layer = QgsVectorLayer(
            f'Polygon?crs=EPSG:3301&field={F.tunnus}:string&field={F.l_aadress}:string'
            f'&field={F.pindala}:string&field={F.ay_nimi}:string',
            'mem', 'memory')
        feature = QgsFeature(layer.fields())
        feature.setAttribute(F.l_aadress, value)
        return feature

    def test_none_reads_as_empty_text(self):
        self.assertEqual(PropertyRowBuilder.read_value(None), '')

    def test_qgis_null_reads_as_empty_text_not_the_word_null(self):
        feature = self._feature_with_address(NULL)
        self.assertEqual(PropertyRowBuilder.read_field_text(feature, F.l_aadress), '')

    def test_literal_null_text_also_reads_as_empty(self):
        # A source (e.g. an import file) can carry the literal string "NULL" as data;
        # it is indistinguishable from a real null once it reaches the table.
        self.assertEqual(PropertyRowBuilder.read_value('NULL'), '')
        self.assertEqual(PropertyRowBuilder.read_value('null'), '')

    def test_whitespace_padded_value_is_trimmed_but_kept(self):
        self.assertEqual(PropertyRowBuilder.read_value('  Tartu mnt 5  '), 'Tartu mnt 5')

    def test_row_from_feature_never_shows_the_word_null(self):
        feature = self._feature_with_address(NULL)
        row = PropertyRowBuilder.row_from_feature(feature)
        self.assertEqual(row['address'], '')


if __name__ == '__main__':
    unittest.main()
