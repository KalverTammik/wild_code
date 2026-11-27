"""The geometry forms check each typed value against the real map layer field while the user fills them in.

The check uses the save's own rules, so a value the save would leave empty ("019,98" in a whole-number
"Talumistasu") is marked in the form and cannot be saved, and nothing reaches Kavitro before it is fixed.
"""
from __future__ import annotations

import os
import sys
import unittest
from functools import partial
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
if os.environ.get("QGIS_PREFIX_PATH"):
    sys.path.append(str(Path(os.environ["QGIS_PREFIX_PATH"]) / "python" / "plugins"))

from qgis.core import QgsApplication, QgsFeature, QgsGeometry, QgsPointXY, QgsVectorLayer
from qgis.PyQt.QtCore import QCoreApplication, QEvent
from qgis.PyQt.QtWidgets import QDialog, QLineEdit, QTabWidget

from Kavitro_dev.languages.language_manager import LanguageManager
from Kavitro_dev.languages.translation_keys import TranslationKeys
from Kavitro_dev.modules.asbuilt import asbuilt_feature_map_controller as asbuilt_controller_module
from Kavitro_dev.modules.asbuilt.asbuilt_geometry_form_dialog import AsBuiltGeometryFormDialog as AsBuiltForm
from Kavitro_dev.modules.asbuilt.asbuilt_layer_service import AsBuiltLayerService
from Kavitro_dev.modules.easements import easement_attach_existing_controller as easement_controller_module
from Kavitro_dev.modules.easements import easement_geometry_form_dialog as form_module
from Kavitro_dev.modules.easements.easement_geometry_form_dialog import EasementGeometryFormDialog as Form
from Kavitro_dev.modules.easements.easement_layer_service import EasementLayerService
from Kavitro_dev.utils.layers.module_layer_service_base import FieldValueProblem
from Kavitro_dev.ui.messages_helper import ModernMessageDialog
from Kavitro_dev.widgets.form_value_check import FormValueCheck

ET = LanguageManager(language="et")
PREPARING = {"id": "1", "name": "Ettevalmistamisel", "color": "4FBF6B", "type": "OPEN"}
SIGNED = {"id": "2", "name": "Allkirjastatud", "color": "2188FF", "type": "OPEN"}
STATUSES = [PREPARING, SIGNED]
ERROR = FormValueCheck.STATE_ERROR
STATE = FormValueCheck.STATE_PROPERTY
EASEMENT_FIELDS = (
    "field=Talumistasu:integer&field=Kaitsevööndi laius:double&field=Kehtestamise kuupäev:date"
    "&field=Maja nr:integer&field=Aadress:string&field=ext_easement_id:string"
)


def expected(kind_key: str) -> str:
    return ET.translate(kind_key)


def polygon_layer(fields: str = EASEMENT_FIELDS) -> QgsVectorLayer:
    layer = QgsVectorLayer(f"Polygon?crs=EPSG:3301&{fields}", "servituudid", "memory")
    feature = QgsFeature(layer.fields())
    feature.setGeometry(QgsGeometry.fromWkt("POLYGON((0 0, 10 0, 10 10, 0 10, 0 0))"))
    layer.dataProvider().addFeature(feature)
    return layer


class _Case(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QgsApplication.instance() or QgsApplication([], False)

    def setUp(self) -> None:
        self.warning = self._patch(ModernMessageDialog, "show_warning", return_value=True)
        # Any other message path would open a real window and wait for a click.
        self._patch(ModernMessageDialog, "_create_dialog", side_effect=AssertionError("a message window was opened"))
        self._patch(EasementLayerService, "load_status_mapping_rows", return_value=[])
        self.read = self._patch(form_module.APIModuleActions, "get_item_status", return_value=None)
        self.update = self._patch(form_module.APIModuleActions, "update_item_status", return_value={"id": "1", "status": SIGNED})
        self._patch(form_module.APIModuleActions, "get_module_status_options", return_value=STATUSES)

    def _patch(self, target, name, **kwargs):
        patcher = patch.object(target, name, **kwargs)
        mock = patcher.start()
        self.addCleanup(patcher.stop)
        return mock

    def _keep(self, dialog):
        def delete() -> None:
            dialog.hide()
            dialog.deleteLater()
            QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)

        self.addCleanup(delete)
        return dialog

    def _easement_form(self, layer=None, **kwargs) -> Form:
        validator = partial(EasementLayerService.geometry_form_value_problems, layer) if layer is not None else None
        return self._keep(
            Form(
                item_data={"id": "1", "status": PREPARING},
                status_options=STATUSES,
                value_validator=validator,
                **kwargs,
            )
        )

    @staticmethod
    def _leave(widget: QLineEdit, text: str) -> None:
        # What a user does: type, then move to the next field.
        widget.setText(text)
        widget.editingFinished.emit()

    def assert_marked(self, widget: QLineEdit, expected_key: str) -> None:
        self.assertEqual(widget.property(STATE), ERROR)
        self.assertIn(expected(expected_key), widget.toolTip())

    def assert_not_marked(self, widget: QLineEdit) -> None:
        self.assertNotEqual(widget.property(STATE), ERROR)

    def one_warning(self) -> str:
        self.warning.assert_called_once()
        title, message = self.warning.call_args.args[:2]
        self.assertEqual(title, ET.translate(TranslationKeys.FORM_VALUE_INVALID_TITLE))
        return message


class EasementServiceCheckTest(_Case):
    """The service tells which form values the layer would refuse, without touching the layer."""

    def test_each_field_type_is_checked_by_the_save_rules(self) -> None:
        layer = polygon_layer()
        problems = EasementLayerService.geometry_form_value_problems(
            layer,
            {
                "Talumistasu": "019,98",
                "Kaitsevööndi laius": "kaks",
                "Kehtestamise kuupäev": "2026-13-45",
                "Maja nr": "12",
                "Aadress": "Tee 4",
            },
        )

        self.assertEqual(
            {key: problem.expected for key, problem in problems.items()},
            {
                "Talumistasu": FieldValueProblem.INTEGER,
                "Kaitsevööndi laius": FieldValueProblem.NUMBER,
                "Kehtestamise kuupäev": FieldValueProblem.DATE,
            },
        )
        self.assertFalse(layer.isEditable())
        self.assertFalse(layer.isModified())

    def test_values_that_fit_and_blanks_have_no_problem(self) -> None:
        problems = EasementLayerService.geometry_form_value_problems(
            polygon_layer(),
            {"Talumistasu": "20", "Kaitsevööndi laius": "2,5", "Kehtestamise kuupäev": "2026-11-21", "Maja nr": ""},
        )

        self.assertEqual(problems, {})

    def test_a_field_missing_from_the_layer_is_not_a_problem(self) -> None:
        self.assertEqual(EasementLayerService.geometry_form_value_problems(polygon_layer(), {"Telefon": "abc"}), {})

    def test_check_writes_nothing_to_the_log(self) -> None:
        with patch.object(form_module.EasementLayerService, "coerce_value_for_field") as logging_coerce:
            EasementLayerService.geometry_form_value_problems(polygon_layer(), {"Talumistasu": "019,98"})

        logging_coerce.assert_not_called()


class EasementMappingSharedWithSaveTest(_Case):
    """The form check and the save read one mapping, so they cannot disagree about a field."""

    def _all_integer_layer(self):
        names = sorted({candidates[0] for _key, candidates in EasementLayerService.GEOMETRY_FORM_FIELDS})
        fields = "&".join(f"field={name}:integer" for name in names if name != "ext_easement_id")
        return polygon_layer(f"{fields}&field=ext_easement_id:string")

    def _saved_problem_fields(self, layer, form_values) -> set[str]:
        problems: list[FieldValueProblem] = []
        ok, message = EasementLayerService.attach_backend_item_to_feature(
            layer=layer,
            feature_id=next(layer.getFeatures()).id(),
            item_id="1",
            item_data={"id": "1", "_easement_geometry_form": form_values},
            value_problems=problems,
        )
        self.assertTrue(ok, message)
        return {problem.field_name for problem in problems if problem.raw_value == "x"}

    def test_every_form_key_the_save_rejects_is_rejected_by_the_check(self) -> None:
        layer = self._all_integer_layer()
        form_values = {key: "x" for key, _candidates in EasementLayerService.GEOMETRY_FORM_FIELDS}

        checked = EasementLayerService.geometry_form_value_problems(layer, form_values)
        saved = self._saved_problem_fields(layer, form_values)

        self.assertEqual(set(checked), set(form_values))
        self.assertEqual({problem.field_name for problem in checked.values()}, saved)

    def test_a_new_mapping_entry_reaches_both(self) -> None:
        extended = EasementLayerService.GEOMETRY_FORM_FIELDS + (("Uus", ("Uus väli",)),)
        layer = polygon_layer("field=Uus väli:integer&field=ext_easement_id:string")

        with patch.object(EasementLayerService, "GEOMETRY_FORM_FIELDS", extended):
            checked = EasementLayerService.geometry_form_value_problems(layer, {"Uus": "x"})
            saved = self._saved_problem_fields(layer, {"Uus": "x"})

        self.assertEqual(set(checked), {"Uus"})
        self.assertEqual(saved, {"Uus väli"})

    def test_every_value_of_the_form_is_in_the_mapping(self) -> None:
        mapped = {key for key, _candidates in EasementLayerService.GEOMETRY_FORM_FIELDS}

        self.assertEqual(set(self._easement_form().values()), mapped)

    def test_every_line_edit_of_the_form_is_checked(self) -> None:
        form = self._easement_form()
        checked = {widget for widget, _label in form._text_inputs().values()}

        self.assertEqual(set(form.findChildren(QLineEdit)) - {self._date_line(form)}, checked)

    @staticmethod
    def _date_line(form):
        return form._established_date.findChild(QLineEdit)


class EasementFormCheckTest(_Case):
    def test_users_case_keeps_the_form_open_and_sends_nothing_to_kavitro(self) -> None:
        form = self._easement_form(polygon_layer())
        form._status.set_current_status_id(SIGNED["id"])
        form._compensation.setText("019,98")

        form.accept()

        self.assertNotEqual(form.result(), QDialog.DialogCode.Accepted)
        self.update.assert_not_called()
        self.assert_marked(form._compensation, TranslationKeys.FIELD_VALUE_EXPECTED_INTEGER)
        message = self.one_warning()
        self.assertIn("Talumistasu", message)
        self.assertIn("019,98", message)
        self.assertIn(expected(TranslationKeys.FIELD_VALUE_EXPECTED_INTEGER), message)

    def test_warning_names_every_wrong_field_once(self) -> None:
        form = self._easement_form(polygon_layer())
        form._compensation.setText("99,9")
        form._protection_width.setText("kaks meetrit")

        form.accept()

        message = self.one_warning()
        self.assertEqual(message.count("Talumistasu"), 1)
        self.assertIn(f"„99,9“ – peab olema {expected(TranslationKeys.FIELD_VALUE_EXPECTED_INTEGER)}", message)
        self.assertIn(f"„kaks meetrit“ – peab olema {expected(TranslationKeys.FIELD_VALUE_EXPECTED_NUMBER)}", message)

    def test_value_that_fits_lets_the_form_close_and_saves_the_status(self) -> None:
        form = self._easement_form(polygon_layer())
        form._status.set_current_status_id(SIGNED["id"])
        form._compensation.setText("20")
        form._protection_width.setText("2,5")

        form.accept()

        self.assertEqual(form.result(), QDialog.DialogCode.Accepted)
        self.update.assert_called_once_with("easement", "1", SIGNED["id"])
        self.warning.assert_not_called()

    def test_mark_appears_when_the_field_is_left_and_goes_when_fixed(self) -> None:
        form = self._easement_form(polygon_layer())
        own_tooltip = form._compensation.toolTip()

        form._compensation.setText("019,98")
        self.assert_not_marked(form._compensation)  # not while typing

        form._compensation.editingFinished.emit()
        self.assert_marked(form._compensation, TranslationKeys.FIELD_VALUE_EXPECTED_INTEGER)

        form._compensation.setText("19")  # no need to leave the field again
        self.assert_not_marked(form._compensation)
        self.assertEqual(form._compensation.toolTip(), own_tooltip)

    def test_prefilled_value_that_does_not_fit_is_marked_on_open(self) -> None:
        form = self._easement_form(polygon_layer(), initial_values={Form.FIELD_COMPENSATION: 19.98})

        self.assert_marked(form._compensation, TranslationKeys.FIELD_VALUE_EXPECTED_INTEGER)

    def test_first_wrong_field_gets_the_focus_also_on_the_other_tab(self) -> None:
        form = self._easement_form(polygon_layer())
        form.show()
        self.app.processEvents()
        tabs = form.findChild(QTabWidget)
        self.assertEqual(tabs.currentIndex(), 0)
        form._house_number.setText("4a")

        form.accept()

        self.assertEqual(tabs.currentIndex(), 1)
        self.assertIs(form.focusWidget(), form._house_number)

    def test_prompt_checks_against_the_layer_it_is_given(self) -> None:
        results = []

        def fake_exec(dialog) -> int:
            self._leave(dialog._compensation, "019,98")
            dialog.accept()
            results.append(dialog._compensation.property(STATE))
            return dialog.result()

        with patch.object(Form, "exec", new=fake_exec):
            values = Form.prompt(item_data={"id": "1", "status": PREPARING}, layer=polygon_layer())

        self.assertIsNone(values)
        self.assertEqual(results, [ERROR])

    def test_attach_flow_hands_its_layer_to_the_form(self) -> None:
        layer = polygon_layer()
        controller = easement_controller_module.EasementAttachExistingController.__new__(
            easement_controller_module.EasementAttachExistingController
        )
        controller._on_status_changed = None
        with patch.object(easement_controller_module.EasementGeometryFormDialog, "prompt", return_value=None) as prompt:
            controller._attach_easement_feature_with_form(layer, 1, {"id": "1"})

        self.assertIs(prompt.call_args.kwargs["layer"], layer)


class EasementFormWithoutLayerTest(_Case):
    """Without a layer only the two number fields are checked, as before, and the same way."""

    def test_text_in_a_number_field_is_marked_and_keeps_the_form_open(self) -> None:
        form = self._easement_form()
        self._leave(form._protection_width, "2 meetrit")
        self.assert_marked(form._protection_width, TranslationKeys.FIELD_VALUE_EXPECTED_NUMBER)

        form.accept()

        self.assertNotEqual(form.result(), QDialog.DialogCode.Accepted)
        self.assertIn("Kaitsevööndi laius", self.one_warning())

    def test_decimal_in_compensation_passes_without_the_layer_type(self) -> None:
        form = self._easement_form()
        form._compensation.setText("019,98")

        form.accept()

        self.assertEqual(form.result(), QDialog.DialogCode.Accepted)
        self.warning.assert_not_called()


class EasementFinalCutCompensationTest(_Case):
    """The preview flow writes the parcels' sum as a default; a corrected form value must not be reported as rejected."""

    def _save(self, form_values):
        layer = polygon_layer()
        final = QgsVectorLayer("Polygon?crs=EPSG:3301", "lopp", "memory")
        feature = QgsFeature(final.fields())
        feature.setGeometry(QgsGeometry.fromWkt("POLYGON((0 0, 20 0, 20 20, 0 20, 0 0))"))
        final.dataProvider().addFeature(feature)
        problems: list[FieldValueProblem] = []
        ok, message = EasementLayerService.upsert_final_cut_feature(
            layer=layer,
            final_layer=final,
            item_id="1",
            item_data={"id": "1"},
            property_edges=[{"cadastralUnitNumber": "1:1:1", "totalPrice": {"amount": 19.98}}],
            form_values=form_values,
            value_problems=problems,
        )
        self.assertTrue(ok, message)
        saved = next(f for f in layer.getFeatures() if f["ext_easement_id"] == "1")
        return saved, problems

    def test_corrected_compensation_is_saved_without_a_notice(self) -> None:
        saved, problems = self._save({"Talumistasu": "20"})

        self.assertEqual(saved["Talumistasu"], 20)
        self.assertEqual(problems, [])

    def test_default_sum_is_still_reported_when_the_form_left_it_blank(self) -> None:
        _saved, problems = self._save({"Talumistasu": ""})

        self.assertEqual([(p.field_name, p.raw_value) for p in problems], [("Talumistasu", "19.98")])


class AsBuiltFormCheckTest(_Case):
    FIELDS = "field=Töö nr:integer&field=Objekt:string&field=Kontakt:string"

    def _layer(self, fields: str = FIELDS) -> QgsVectorLayer:
        layer = QgsVectorLayer(f"LineString?crs=EPSG:3301&{fields}", "asbuilt", "memory")
        feature = QgsFeature(layer.fields())
        feature.setGeometry(QgsGeometry.fromPolylineXY([QgsPointXY(0, 0), QgsPointXY(10, 0)]))
        layer.dataProvider().addFeature(feature)
        return layer

    def _form(self, layer=None, item=None) -> AsBuiltForm:
        validator = partial(AsBuiltLayerService.geometry_form_value_problems, layer) if layer is not None else None
        return self._keep(AsBuiltForm(item_data=item or {"id": "7", "number": "TJ-12"}, value_validator=validator))

    def test_prefilled_work_number_that_does_not_fit_is_marked_and_blocks_saving(self) -> None:
        form = self._form(self._layer())
        self.assert_marked(form._work_number, TranslationKeys.FIELD_VALUE_EXPECTED_INTEGER)

        form.accept()

        self.assertNotEqual(form.result(), QDialog.DialogCode.Accepted)
        self.assertIn("TJ-12", self.one_warning())

    def test_fixed_value_clears_the_mark_and_saves(self) -> None:
        form = self._form(self._layer())

        form._work_number.setText("12")
        self.assert_not_marked(form._work_number)
        form.accept()

        self.assertEqual(form.result(), QDialog.DialogCode.Accepted)
        self.warning.assert_not_called()

    def test_text_field_takes_any_text(self) -> None:
        form = self._form(self._layer(), item={"id": "7", "number": "12"})
        self._leave(form._contact, "Mari, 5555 5555")

        form.accept()

        self.assertEqual(form.result(), QDialog.DialogCode.Accepted)

    def test_without_a_layer_nothing_is_checked(self) -> None:
        form = self._form()

        form.accept()

        self.assertEqual(form.result(), QDialog.DialogCode.Accepted)
        self.warning.assert_not_called()

    def test_check_and_save_reject_the_same_values(self) -> None:
        layer = self._layer("field=Töö nr:integer&field=Objekt:double&field=Mõõdistaja:date&field=Kontakt:integer")
        form = self._form(layer)
        form._object.setText("Tee")
        form._surveyor.setText("Mari")
        form._contact.setText("55")
        values = form.values()

        checked = AsBuiltLayerService.geometry_form_value_problems(layer, values)
        problems: list[FieldValueProblem] = []
        ok, message = AsBuiltLayerService.attach_backend_item_to_feature(
            layer=layer,
            feature_id=next(layer.getFeatures()).id(),
            item_id="7",
            item_data={"id": "7", "_asbuilt_geometry_form": values},
            value_problems=problems,
        )

        self.assertTrue(ok, message)
        self.assertEqual(set(checked), {"Töö nr", "Objekt", "Mõõdistaja"})
        self.assertEqual({p.field_name for p in problems}, {p.field_name for p in checked.values()})

    def test_every_typed_field_is_checked(self) -> None:
        form = self._form()
        checked = {widget for widget, _label in form._text_inputs().values()}
        date_line = form._survey_date.findChild(QLineEdit)

        self.assertEqual(set(form.findChildren(QLineEdit)) - {date_line}, checked)

    def test_map_flow_hands_its_layer_to_the_form(self) -> None:
        layer = self._layer()
        with patch.object(asbuilt_controller_module.AsBuiltGeometryFormDialog, "prompt", return_value=None) as prompt:
            asbuilt_controller_module.AsBuiltFeatureMapController._attach_asbuilt_feature_and_sync_geometry(
                layer, 1, {"id": "7"}
            )

        self.assertIs(prompt.call_args.kwargs["layer"], layer)


if __name__ == "__main__":
    unittest.main()
