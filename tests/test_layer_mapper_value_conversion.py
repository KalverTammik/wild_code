"""The layer mapper converts values with the layer services' rules; a value that does not fit is reported.

A new feature gets an empty field, an updated feature keeps its previous value.

Before, the mapper had its own copy: "1 250", "3,0" and 3.0 were silently emptied in whole-number fields, "ei" was stored
as yes, and one wrong number or date failed the commit of the whole transfer.
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

from qgis.core import NULL, QgsApplication, QgsFeature, QgsField, QgsGeometry, QgsVectorLayer
from qgis.PyQt.QtCore import QCoreApplication, QDate, QEvent, QVariant
from qgis.PyQt.QtWidgets import QWidget

from Kavitro_dev.Logs.python_fail_logger import PythonFailLogger
from Kavitro_dev.languages.language_manager import LanguageManager
from Kavitro_dev.modules.Settings.GeospatialLayerMapperDialog import GeospatialLayerMapperDialog
from Kavitro_dev.utils.layers.module_layer_service_base import FieldValueProblem
from Kavitro_dev.utils.messagesHelper import ModernMessageDialog

TARGET_FIELDS = "field=kogus:integer&field=laius:double&field=vesi:boolean&field=kuupaev:date&field=nimi:string"
SOURCE_FIELDS = "field=kogus:string&field=laius:string&field=vesi:string&field=kuupaev:string&field=ext_job_id:string"


def _target(rows: tuple[dict, ...] = ()) -> QgsVectorLayer:
    layer = QgsVectorLayer(f"Point?crs=EPSG:3301&{TARGET_FIELDS}&field=ext_job_id:string", "siht", "memory")
    layer.setFieldAlias(layer.fields().indexFromName("kogus"), "Kogus")
    _add(layer, rows)
    return layer


def _source(rows: tuple[dict, ...]) -> QgsVectorLayer:
    layer = QgsVectorLayer(f"Point?crs=EPSG:3301&{SOURCE_FIELDS}", "lähe", "memory")
    _add(layer, rows)
    return layer


def _add(layer: QgsVectorLayer, rows: tuple[dict, ...]) -> None:
    features = []
    for values in rows:
        feature = QgsFeature(layer.fields())
        feature.setGeometry(QgsGeometry.fromWkt("POINT(500000 6500000)"))
        for name, value in values.items():
            feature.setAttribute(name, value)
        features.append(feature)
    layer.dataProvider().addFeatures(features)


def _row(target: str, source: str = "", default=None) -> dict[str, object]:
    return {"target": target, "source": source, "has_default": default is not None, "default": default}


MAPPED = [_row(name, name) for name in ("kogus", "laius", "vesi", "kuupaev", "ext_job_id")]


class MapperValueConversionTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QgsApplication.instance() or QgsApplication([], False)

    def setUp(self) -> None:
        for name in ("show_warning", "show_info", "ask_yes_no"):
            patcher = patch.object(ModernMessageDialog, name)
            setattr(self, name, patcher.start())
            self.addCleanup(patcher.stop)
        for name in ("log", "log_exception"):
            patcher = patch.object(PythonFailLogger, name)
            setattr(self, name, patcher.start())
            self.addCleanup(patcher.stop)
        self.lang = LanguageManager("et")
        self.window = QWidget()

    def tearDown(self) -> None:
        self.window.hide()
        self.window.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)

    def _transfer(self, target: QgsVectorLayer, source: QgsVectorLayer, rows=MAPPED):
        dialog = GeospatialLayerMapperDialog(lang_manager=self.lang, module_name="works", target_layer=target, parent=self.window)
        return dialog._transfer_features(source, rows)

    @staticmethod
    def _values(layer: QgsVectorLayer, field: str) -> list:
        return [feature[field] for feature in layer.getFeatures()]

    def test_comma_number_goes_into_a_double_field(self) -> None:
        target = _target()

        result = self._transfer(target, _source(({"laius": "1 250,4"}, {"laius": "2,5"})))

        self.assertEqual(result, (2, 0, 0, []))
        self.assertEqual(self._values(target, "laius"), [1250.4, 2.5])
        self.log.assert_not_called()

    def test_whole_numbers_written_with_a_comma_or_space_are_kept(self) -> None:
        # The old copy emptied these without telling anyone.
        target = _target()

        result = self._transfer(target, _source(({"kogus": "1 250"}, {"kogus": "3,0"})))

        self.assertEqual(result, (2, 0, 0, []))
        self.assertEqual(self._values(target, "kogus"), [1250, 3])

    def test_fraction_in_an_integer_field_is_left_empty_and_reported(self) -> None:
        target = _target()

        inserted, updated, skipped, errors = self._transfer(target, _source(({"kogus": "2,5", "laius": "4"},)))

        self.assertEqual((inserted, updated, skipped), (1, 0, 0))
        self.assertEqual(self._values(target, "kogus"), [NULL])
        self.assertEqual(self._values(target, "laius"), [4.0])
        self.assertEqual(len(errors), 1)
        self.assertIn("• Kogus: „2,5“ – peab olema täisarv", errors[0])

    def test_unknown_yes_no_is_left_empty_and_estonian_no_is_no(self) -> None:
        target = _target()

        _i, _u, _s, errors = self._transfer(target, _source(({"vesi": "ei"}, {"vesi": "jah"}, {"vesi": "võib-olla"})))

        # The old copy passed "ei" through and the layer stored it as yes.
        self.assertEqual(self._values(target, "vesi"), [False, True, NULL])
        self.assertIn("• vesi: „võib-olla“ – peab olema jah/ei", errors[0])

    def test_yes_and_no_from_the_default_combo_are_written_as_they_are(self) -> None:
        target = _target()

        result = self._transfer(target, _source(({"ext_job_id": "a"},)), [_row("vesi", default=False)])

        self.assertEqual(result, (1, 0, 0, []))
        self.assertEqual(self._values(target, "vesi"), [False])

    def test_date_text_is_parsed_and_an_unreadable_date_does_not_fail_the_transfer(self) -> None:
        target = _target()

        inserted, _u, _s, errors = self._transfer(target, _source(({"kuupaev": "2024-05-01"}, {"kuupaev": "kolmapäev"})))

        # The old copy passed the text on and the commit of the whole transfer failed.
        self.assertEqual(inserted, 2)
        self.assertEqual(self._values(target, "kuupaev"), [QDate(2024, 5, 1), NULL])
        self.assertIn("• kuupaev: „kolmapäev“ – peab olema kuupäev", errors[0])

    def test_update_with_a_wrong_value_keeps_the_previous_value_and_reports_it(self) -> None:
        target = _target(({"ext_job_id": "J-1", "laius": 9.5, "kogus": 1},))

        inserted, updated, skipped, errors = self._transfer(
            target, _source(({"ext_job_id": "J-1", "laius": "lai", "kogus": "4"},))
        )

        self.assertEqual((inserted, updated, skipped), (0, 1, 0))
        # Before, the wrong value emptied the field and the feature lost its old width.
        self.assertEqual(self._values(target, "laius"), [9.5])
        self.assertEqual(self._values(target, "kogus"), [4])
        self.assertIn("• laius: „lai“ – peab olema arv", errors[0])

    def test_a_null_source_value_gets_the_default(self) -> None:
        # Guide 06: the default is used when the source field of that feature is empty.
        target = _target()
        rows = [_row("laius", "laius", default="7,5"), _row("ext_job_id", "ext_job_id")]

        result = self._transfer(target, _source(({"ext_job_id": "a"}, {"ext_job_id": "b", "laius": "2"})), rows)

        self.assertEqual(result, (2, 0, 0, []))
        self.assertEqual(self._values(target, "laius"), [7.5, 2.0])

    def test_update_with_a_null_source_value_and_no_default_keeps_the_previous_value(self) -> None:
        target = _target(({"ext_job_id": "J-1", "laius": 9.5},))

        result = self._transfer(target, _source(({"ext_job_id": "J-1"},)))

        self.assertEqual(result, (0, 1, 0, []))
        self.assertEqual(self._values(target, "laius"), [9.5])

    def test_note_counts_every_value_and_lists_the_first_five_distinct_ones(self) -> None:
        rows = tuple({"kogus": f"x{index}"} for index in range(7)) + ({"kogus": "x0"},)
        target = _target()

        inserted, _u, _s, errors = self._transfer(target, _source(rows))

        self.assertEqual(inserted, 8)
        lines = errors[0].split("\n")
        self.assertEqual(lines[0], "Sihtvälja tüübiga sobimatuid väärtusi: 8. Uutel objektidel jäi väli tühjaks, uuendatud objektidel jäi alles endine väärtus:")
        self.assertEqual(lines[1:6], [f"• Kogus: „x{index}“ – peab olema täisarv" for index in range(4)]
                         + ["• Kogus: „x4“ – peab olema täisarv … (+2 veel)"])
        self.assertEqual(lines[6], "Paranda need väärtused sihtkihi atribuutide tabelis.")
        # One log line for the transfer, not one per value.
        self.assertEqual(self.log.call_count, 1)
        self.assertEqual(self.log.call_args.args[0], "geospatial_layer_mapper_values_left_empty")
        self.assertEqual(self.log.call_args.kwargs["extra"]["count"], 8)
        self.assertEqual(self.log.call_args.kwargs["extra"]["fields"], ["kogus"])

    def test_user_sees_how_many_values_were_left_empty_in_the_result_warning(self) -> None:
        target = _target()
        source = _source(({"kogus": "2,5", "laius": "1,5"}, {"kogus": "7", "laius": "lai"}))
        dialog = GeospatialLayerMapperDialog(lang_manager=self.lang, module_name="works", target_layer=target, parent=self.window)
        self.ask_yes_no.return_value = True

        with patch.object(dialog._source_combo, "currentLayer", return_value=source), \
                patch.object(dialog, "_collect_mapping_rows", return_value=MAPPED):
            dialog._on_accept()

        self.show_info.assert_not_called()
        self.assertEqual(
            self.show_warning.call_args.args[1],
            "Migratsioon lõpetati vigadega. Lisatud: 2, uuendatud: 0, muutmata: 0.\n\nVead:\n"
            "Sihtvälja tüübiga sobimatuid väärtusi: 2. Uutel objektidel jäi väli tühjaks, uuendatud objektidel jäi alles endine väärtus:\n"
            "• Kogus: „2,5“ – peab olema täisarv\n"
            "• laius: „lai“ – peab olema arv\n"
            "Paranda need väärtused sihtkihi atribuutide tabelis.",
        )
        self.assertEqual(target.featureCount(), 2)


class MapperCoerceHelperTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QgsApplication.instance() or QgsApplication([], False)

    def test_helper_collects_the_problem_and_returns_none(self) -> None:
        problems: list[FieldValueProblem] = []

        self.assertEqual(GeospatialLayerMapperDialog._coerce_value_for_field(QgsField("n", QVariant.Int), " 12 ", problems), 12)
        self.assertIsNone(GeospatialLayerMapperDialog._coerce_value_for_field(QgsField("n", QVariant.Int), "abc", problems))
        self.assertEqual([problem.expected for problem in problems], [FieldValueProblem.INTEGER])

    def test_field_without_a_readable_type_keeps_the_value(self) -> None:
        field = Mock()
        field.type.side_effect = AttributeError("no type")
        problems: list[FieldValueProblem] = []

        self.assertEqual(GeospatialLayerMapperDialog._coerce_value_for_field(field, "abc", problems), "abc")
        self.assertEqual(problems, [])


if __name__ == "__main__":
    unittest.main()
