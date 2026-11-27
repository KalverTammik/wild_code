"""One value conversion for every module layer service, and the record of values a save had to leave empty.

Before this file the four services each had their own copy; the comments name what each copy did differently.
"""
from __future__ import annotations

import os
import sys
import unittest
from datetime import date, datetime
from functools import partial
from pathlib import Path
from unittest.mock import Mock, patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
if os.environ.get("QGIS_PREFIX_PATH"):
    sys.path.append(str(Path(os.environ["QGIS_PREFIX_PATH"]) / "python" / "plugins"))

from qgis.core import NULL, QgsApplication, QgsFeature, QgsField, QgsGeometry, QgsPointXY, QgsVectorLayer
from qgis.PyQt.QtCore import QCoreApplication, QDate, QDateTime, QEvent, QTime, QVariant
from qgis.PyQt.QtWidgets import QLineEdit, QWidget

from Kavitro_dev.languages.language_manager import LanguageManager
from Kavitro_dev.Logs.python_fail_logger import PythonFailLogger
from Kavitro_dev.modules.asbuilt.asbuilt_layer_service import AsBuiltLayerService
from Kavitro_dev.modules.easements.easement_layer_service import EasementLayerService
from Kavitro_dev.modules.projects.projects_layer_service import ProjectsLayerService
from Kavitro_dev.modules.works.works_layer_service import WorksLayerService
from Kavitro_dev.utils.layers.module_layer_service_base import FieldValueProblem, ModuleLayerServiceBase
from Kavitro_dev.ui.messages_helper import ModernMessageDialog
from Kavitro_dev.widgets.form_value_check import FormValueCheck

SERVICES = (AsBuiltLayerService, EasementLayerService, ProjectsLayerService, WorksLayerService)
INTEGER, NUMBER, YES_NO = FieldValueProblem.INTEGER, FieldValueProblem.NUMBER, FieldValueProblem.YES_NO
DATE, DATE_TIME = FieldValueProblem.DATE, FieldValueProblem.DATE_TIME

# (field type, input, stored value, expected kind of the recorded problem or None)
TABLE = (
    # Integer fields. Before: projects passed text through; works gave None for "3,0"/3.0;
    # easement rounded "2,5" to 2; as-built and easement passed "abc" through (a GeoPackage then refused the save).
    (QVariant.Int, "3", 3, None),
    (QVariant.Int, " 12 ", 12, None),
    (QVariant.Int, "3,0", 3, None),
    (QVariant.Int, 3.0, 3, None),
    (QVariant.Int, "1 250", 1250, None),
    (QVariant.Int, "1 250", 1250, None),
    (QVariant.Int, True, 1, None),
    (QVariant.Int, "2,5", None, INTEGER),
    (QVariant.Int, 2.5, None, INTEGER),
    (QVariant.Int, "abc", None, INTEGER),
    (QVariant.Int, float("inf"), None, INTEGER),
    (QVariant.Int, 2**31, None, INTEGER),
    (QVariant.LongLong, "12345678901234567", 12345678901234567, None),
    (QVariant.UInt, -1, None, INTEGER),
    (QVariant.ULongLong, "2,5", None, INTEGER),
    # Double fields. Before: only easement read the decimal comma; the others passed the text through.
    (QVariant.Double, "2,5", 2.5, None),
    (QVariant.Double, "1 250,40", 1250.4, None),
    (QVariant.Double, "1 250,4", 1250.4, None),
    (QVariant.Double, 3, 3.0, None),
    (QVariant.Double, True, 1.0, None),
    (QVariant.Double, "1,5 m", None, NUMBER),
    (QVariant.Double, float("nan"), None, NUMBER),
    # Bool fields. Before: as-built made any unknown text True; projects and works knew no "jah", "ei", "t", "f".
    (QVariant.Bool, True, True, None),
    (QVariant.Bool, False, False, None),
    (QVariant.Bool, "jah", True, None),
    (QVariant.Bool, "EI", False, None),
    (QVariant.Bool, " Yes ", True, None),
    (QVariant.Bool, "t", True, None),
    (QVariant.Bool, "f", False, None),
    (QVariant.Bool, 1, True, None),
    (QVariant.Bool, 0, False, None),
    (QVariant.Bool, "maybe", None, YES_NO),
    # Date fields. Before: projects had no date rule; as-built read only yyyy-MM-dd and passed datetimes through.
    (QVariant.Date, QDate(2026, 1, 2), QDate(2026, 1, 2), None),
    (QVariant.Date, QDateTime(2026, 1, 2, 10, 5), QDate(2026, 1, 2), None),
    (QVariant.Date, date(2026, 1, 2), QDate(2026, 1, 2), None),
    (QVariant.Date, datetime(2026, 1, 2, 10, 5), QDate(2026, 1, 2), None),
    (QVariant.Date, "2026-01-02", QDate(2026, 1, 2), None),
    (QVariant.Date, "2026-01-02 10:05:00", QDate(2026, 1, 2), None),
    # Estonian notation, as the user types it in a form.
    (QVariant.Date, "02.01.2026", QDate(2026, 1, 2), None),
    (QVariant.Date, "1.5.2024", QDate(2024, 5, 1), None),
    (QVariant.Date, " 01.05.2024 10:05 ", QDate(2024, 5, 1), None),
    (QVariant.Date, "31.02.2024", None, DATE),
    (QVariant.Date, "32.01.2024", None, DATE),
    (QVariant.Date, "01.13.2024", None, DATE),
    (QVariant.Date, "01.05.24", None, DATE),
    (QVariant.Date, "abc", None, DATE),
    # DateTime fields. Before: all four agreed, except unreadable text was passed through.
    (QVariant.DateTime, QDateTime(2026, 1, 2, 10, 5), QDateTime(2026, 1, 2, 10, 5), None),
    (QVariant.DateTime, QDate(2026, 1, 2), QDateTime(QDate(2026, 1, 2), QTime(0, 0)), None),
    (QVariant.DateTime, datetime(2026, 1, 2, 10, 5, 7, 999), QDateTime(2026, 1, 2, 10, 5, 7), None),
    (QVariant.DateTime, date(2026, 1, 2), QDateTime(2026, 1, 2, 0, 0, 0), None),
    (QVariant.DateTime, "2026-01-02 10:05:07", QDateTime(2026, 1, 2, 10, 5, 7), None),
    (QVariant.DateTime, "2026-01-02", QDateTime(2026, 1, 2, 0, 0, 0), None),
    (QVariant.DateTime, "01.05.2024", QDateTime(2024, 5, 1, 0, 0, 0), None),
    (QVariant.DateTime, "1.5.2024 9:05", QDateTime(2024, 5, 1, 9, 5, 0), None),
    (QVariant.DateTime, "01.05.2024 10:05:07", QDateTime(2024, 5, 1, 10, 5, 7), None),
    (QVariant.DateTime, "31.02.2024 10:05", None, DATE_TIME),
    (QVariant.DateTime, "01.05.2024 25:00", None, DATE_TIME),
    (QVariant.DateTime, "abc", None, DATE_TIME),
    # Text fields. Before: as-built and easement passed objects through unchanged.
    (QVariant.String, {"a": "ä"}, '{"a": "ä"}', None),
    (QVariant.String, [1, 2], "[1, 2]", None),
    (QVariant.String, "abc", "abc", None),
    (QVariant.String, 5, 5, None),
    (QVariant.String, "", "", None),
    # Field types without a rule keep the value.
    (QVariant.Time, "10:00", "10:00", None),
)
CONVERTED_TYPES = (QVariant.Int, QVariant.UInt, QVariant.LongLong, QVariant.ULongLong, QVariant.Double,
                   QVariant.Bool, QVariant.Date, QVariant.DateTime)


def is_null(value) -> bool:
    return value is None or (isinstance(value, QVariant) and value.isNull())


def field_of(field_type, name="f"):
    return QgsField(name, field_type)


class _Case(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QgsApplication.instance() or QgsApplication([], False)

    def setUp(self) -> None:
        for name, target in (("log", "log"), ("log_exception", "log_exception")):
            patcher = patch.object(PythonFailLogger, target)
            setattr(self, name, patcher.start())
            self.addCleanup(patcher.stop)
        for name in ("show_warning", "show_info"):
            dialog_patcher = patch.object(ModernMessageDialog, name)
            dialog_patcher.start()
            self.addCleanup(dialog_patcher.stop)


class SharedConversionTableTest(_Case):
    def test_every_service_converts_each_value_the_same_way(self) -> None:
        for service in SERVICES:
            for field_type, raw, stored, problem_kind in TABLE:
                with self.subTest(service=service.__name__, field_type=field_type, raw=raw):
                    problems: list[FieldValueProblem] = []
                    value = service.coerce_value_for_field(field_of(field_type), raw, problems)
                    self.assertEqual(value, stored)
                    self.assertEqual(type(value), type(stored))
                    self.assertEqual([problem.expected for problem in problems], [problem_kind] if problem_kind else [])

    def test_no_service_keeps_its_own_copy(self) -> None:
        for service in SERVICES:
            for name in ("coerce_value_for_field", "coerce_field_value", "parse_number_text"):
                with self.subTest(service=service.__name__, name=name):
                    self.assertNotIn(name, vars(service))
                    self.assertIn(name, vars(ModuleLayerServiceBase))

    def test_nothing_and_blank_are_empty_without_a_problem(self) -> None:
        for field_type in CONVERTED_TYPES:
            for raw in (None, "", "   ", NULL):
                with self.subTest(field_type=field_type, raw=raw):
                    self.assertEqual(ModuleLayerServiceBase.coerce_field_value(field_of(field_type), raw), (None, None))

    def test_field_without_a_readable_type_keeps_the_value(self) -> None:
        for error in (RuntimeError("deleted"), AttributeError("no type")):
            field = Mock()
            field.type.side_effect = error
            self.assertEqual(ModuleLayerServiceBase.coerce_field_value(field, "abc"), ("abc", None))
        self.assertEqual(ModuleLayerServiceBase.coerce_field_value(None, "abc"), ("abc", None))

    def test_text_field_falls_back_to_str_for_what_json_cannot_write(self) -> None:
        circular: dict = {}
        circular["self"] = circular
        for raw in (circular, {"value": object()}, {"set": {1, 2}}):
            with self.subTest(raw=type(raw)):
                self.assertEqual(ModuleLayerServiceBase.coerce_field_value(field_of(QVariant.String), raw), (str(raw), None))

    def test_parse_number_text_keeps_its_contract_for_the_easement_form(self) -> None:
        # The easement form asks this before it closes, through the easement service.
        for raw, expected in (("2,5", 2.5), ("1 250,40", 1250.4), (3, 3.0), ("", None), ("2 meetrit", None),
                              ("inf", None), (True, None)):
            with self.subTest(raw=raw):
                self.assertEqual(EasementLayerService.parse_number_text(raw), expected)


class FieldValueProblemRecordTest(_Case):
    def test_problem_names_the_field_its_label_the_value_and_what_was_expected(self) -> None:
        layer = QgsVectorLayer("Point?crs=EPSG:3301&field=scale:integer", "x", "memory")
        layer.setFieldAlias(0, "Mõõtkava")
        problems: list[FieldValueProblem] = []

        AsBuiltLayerService.coerce_value_for_field(layer.fields()[0], "1:500", problems)

        self.assertEqual(
            problems,
            [FieldValueProblem(field_name="scale", field_label="Mõõtkava", raw_value="1:500", value_type="str",
                               expected=INTEGER)],
        )

    def test_label_is_the_name_when_the_field_has_no_alias(self) -> None:
        _value, problem = ModuleLayerServiceBase.coerce_field_value(field_of(QVariant.Bool, "Vesi"), "maybe")
        self.assertEqual((problem.field_name, problem.field_label), ("Vesi", "Vesi"))

    def test_long_value_is_cut_in_the_record(self) -> None:
        _value, problem = ModuleLayerServiceBase.coerce_field_value(field_of(QVariant.Double), "x" * 500)
        self.assertEqual(len(problem.raw_value), FieldValueProblem.MAX_VALUE_LENGTH)
        self.assertTrue(problem.raw_value.endswith("…"))

    def test_rejected_value_is_logged_under_the_module(self) -> None:
        modules = {AsBuiltLayerService: "asbuilt", EasementLayerService: "easement",
                   ProjectsLayerService: "project", WorksLayerService: "works"}
        for service, module in modules.items():
            with self.subTest(service=service.__name__):
                self.log.reset_mock()
                service.coerce_value_for_field(field_of(QVariant.Date, "kpv"), "31.02.2026")
                self.log.assert_called_once_with(
                    f"{module}_field_value_rejected",
                    module=module,
                    extra={"field": "kpv", "value_type": "str", "value": "31.02.2026", "expected": DATE},
                )

    def test_accepted_value_is_not_logged_or_recorded(self) -> None:
        problems: list[FieldValueProblem] = []
        WorksLayerService.coerce_value_for_field(field_of(QVariant.Int), "3", problems)
        self.assertEqual(problems, [])
        self.log.assert_not_called()


class SaveGoesOnWithAnEmptyFieldTest(_Case):
    """A wrong value reaches the layer as NULL, the save succeeds, and the caller gets the problem."""

    @staticmethod
    def _polygon_layer(fields: str) -> tuple[QgsVectorLayer, int]:
        layer = QgsVectorLayer(f"Polygon?crs=EPSG:3301&{fields}", "kiht", "memory")
        feature = QgsFeature(layer.fields())
        feature.setGeometry(QgsGeometry.fromWkt("POLYGON((0 0, 10 0, 10 10, 0 10, 0 0))"))
        layer.dataProvider().addFeature(feature)
        return layer, next(layer.getFeatures()).id()

    def _assert_saved_empty(self, ok, message, layer, feature_id, field_name, problems, expected) -> None:
        self.assertTrue(ok, message)
        self.assertTrue(is_null(layer.getFeature(feature_id)[field_name]))
        self.assertEqual([(p.field_name, p.expected) for p in problems], [(field_name, expected)])

    def test_asbuilt_scale_text_in_a_number_field(self) -> None:
        layer, feature_id = self._polygon_layer("field=Mõõtkava:integer&field=Vesi:boolean")
        problems: list[FieldValueProblem] = []
        with patch.object(AsBuiltLayerService, "current_username", return_value="kasutaja"):
            ok, message = AsBuiltLayerService.attach_backend_item_to_feature(
                layer=layer, feature_id=feature_id, item_id="7",
                item_data={"name": "Töö", "_asbuilt_geometry_form": {"Mõõtkava": "1:500", "Vesi": True}},
                value_problems=problems,
            )
        self._assert_saved_empty(ok, message, layer, feature_id, "Mõõtkava", problems, INTEGER)
        self.assertIs(layer.getFeature(feature_id)["Vesi"], True)

    def test_easement_width_with_a_unit(self) -> None:
        layer, feature_id = self._polygon_layer("field=Kaitsevööndi laius:double&field=Talumistasu:double")
        problems: list[FieldValueProblem] = []
        with patch.object(EasementLayerService, "current_username", return_value="kasutaja"):
            ok, message = EasementLayerService.attach_backend_item_to_feature(
                layer=layer, feature_id=feature_id, item_id="1",
                item_data={"id": "1", "_easement_geometry_form": {"Kaitsevööndi laius": "2 m", "Talumistasu": "1 250,40"}},
                value_problems=problems,
            )
        self._assert_saved_empty(ok, message, layer, feature_id, "Kaitsevööndi laius", problems, NUMBER)
        self.assertEqual(layer.getFeature(feature_id)["Talumistasu"], 1250.4)

    def test_easement_final_cut_keeps_the_problem_too(self) -> None:
        layer, _feature_id = self._polygon_layer("field=Kaitsevööndi laius:double")
        final = QgsVectorLayer("Polygon?crs=EPSG:3301", "lopp", "memory")
        cut = QgsFeature(final.fields())
        cut.setGeometry(QgsGeometry.fromWkt("POLYGON((0 0, 20 0, 20 20, 0 20, 0 0))"))
        final.dataProvider().addFeature(cut)
        problems: list[FieldValueProblem] = []
        with patch.object(EasementLayerService, "current_username", return_value="kasutaja"):
            ok, message = EasementLayerService.upsert_final_cut_feature(
                layer=layer, final_layer=final, item_id="1", item_data={"id": "1", "number": "S-1"},
                form_values={"Kaitsevööndi laius": "lai"}, value_problems=problems,
            )
        self.assertTrue(ok, message)
        self.assertEqual([(p.field_name, p.expected) for p in problems], [("Kaitsevööndi laius", NUMBER)])

    def test_project_number_text_in_a_number_field(self) -> None:
        layer, feature_id = self._polygon_layer("field=ext_project_number:integer")
        problems: list[FieldValueProblem] = []
        with patch.object(ProjectsLayerService, "current_username", return_value="kasutaja"):
            ok, message = ProjectsLayerService.attach_backend_item_to_feature(
                layer=layer, feature_id=feature_id, item_id="p-1",
                item_data={"name": "Projekt", "projectNumber": "P-12"}, value_problems=problems,
            )
        self._assert_saved_empty(ok, message, layer, feature_id, "ext_project_number", problems, INTEGER)

    def test_works_begin_date_that_does_not_exist(self) -> None:
        layer = QgsVectorLayer("Point?crs=EPSG:3301&field=ext_job_id:long&field=begin_date:datetime", "tood", "memory")
        problems: list[FieldValueProblem] = []
        with patch.object(WorksLayerService, "current_username", return_value="kasutaja"):
            ok, message = WorksLayerService.insert_work_feature(
                layer=layer, point=QgsPointXY(1, 1), task_id="5", title="Töö",
                begin_date="31.02.2026", value_problems=problems,
            )
        self.assertTrue(ok, message)
        saved = next(layer.getFeatures())
        self.assertEqual(saved["ext_job_id"], 5)
        self.assertTrue(is_null(saved["begin_date"]))
        self.assertEqual([(p.field_name, p.expected) for p in problems], [("begin_date", DATE_TIME)])

    def test_save_without_a_collector_still_logs(self) -> None:
        layer, feature_id = self._polygon_layer("field=ext_project_number:integer")
        with patch.object(ProjectsLayerService, "current_username", return_value="kasutaja"):
            ok, message = ProjectsLayerService.attach_backend_item_to_feature(
                layer=layer, feature_id=feature_id, item_id="p-1", item_data={"projectNumber": "P-12"},
            )
        self.assertTrue(ok, message)
        self.assertEqual([c.args[0] for c in self.log.call_args_list], ["project_field_value_rejected"])


class EstonianDateNotationTest(_Case):
    """A date typed as dd.mm.yyyy reached the layer empty; only the ISO form was read."""

    def test_every_service_reads_it_and_still_refuses_a_day_that_does_not_exist(self) -> None:
        for service in SERVICES:
            for raw, expected in (
                ("01.05.2024", datetime(2024, 5, 1)),
                ("1.5.2024", datetime(2024, 5, 1)),
                ("01.05.2024 10:05", datetime(2024, 5, 1, 10, 5)),
                ("01.05.2024 10:05:07", datetime(2024, 5, 1, 10, 5, 7)),
                ("31.02.2024", None),
                ("29.02.2023", None),
                ("01.05.2024 10", None),
            ):
                with self.subTest(service=service.__name__, raw=raw):
                    self.assertEqual(service.parse_backend_datetime(raw), expected)

    def test_works_begin_date_in_estonian_notation_is_saved(self) -> None:
        layer = QgsVectorLayer("Point?crs=EPSG:3301&field=ext_job_id:long&field=begin_date:datetime", "tood", "memory")
        problems: list[FieldValueProblem] = []
        with patch.object(WorksLayerService, "current_username", return_value="kasutaja"):
            ok, message = WorksLayerService.insert_work_feature(
                layer=layer, point=QgsPointXY(1, 1), task_id="5", title="Töö",
                begin_date="31.12.2026", value_problems=problems,
            )
        self.assertTrue(ok, message)
        self.assertEqual(next(layer.getFeatures())["begin_date"], QDateTime(2026, 12, 31, 0, 0, 0))
        self.assertEqual(problems, [])

    def test_the_form_check_accepts_the_same_notation(self) -> None:
        # The form and the save share one conversion, so the form must not mark what the save now stores.
        window = QWidget()
        self.addCleanup(self._delete, window)
        field_input = QLineEdit(window)
        layer = QgsVectorLayer("Polygon?crs=EPSG:3301&field=Kehtestamise kuupäev:date", "servituudid", "memory")
        check = FormValueCheck(
            partial(EasementLayerService.geometry_form_value_problems, layer),
            {"Kehtestamise kuupäev": (field_input, "Kehtestamise kuupäev")},
            LanguageManager(language="et"),
        )
        for text, invalid in (("01.05.2024", []), ("1.5.2024", []), ("31.02.2024", ["Kehtestamise kuupäev"])):
            with self.subTest(text=text):
                field_input.setText(text)
                self.assertEqual(check.check_all(), invalid)
                self.assertEqual(field_input.property(FormValueCheck.STATE_PROPERTY),
                                 FormValueCheck.STATE_ERROR if invalid else "")

    @staticmethod
    def _delete(window: QWidget) -> None:
        window.hide()
        window.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)


if __name__ == "__main__":
    unittest.main()
