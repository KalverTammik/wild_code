from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
if os.environ.get("QGIS_PREFIX_PATH"):
    sys.path.append(str(Path(os.environ["QGIS_PREFIX_PATH"]) / "python" / "plugins"))

from qgis.core import QgsApplication, QgsFeature, QgsGeometry, QgsVectorLayer
from qgis.PyQt.QtCore import QCoreApplication, QDate, QEvent, QPoint, QRect
from qgis.PyQt.QtGui import QFont
from qgis.PyQt.QtWidgets import QComboBox, QDialog, QLabel, QLineEdit, QPushButton, QTabWidget, QWidget

from Kavitro_dev.modules.asbuilt.asbuilt_geometry_form_dialog import AsBuiltGeometryFormDialog
from Kavitro_dev.modules.easements import easement_geometry_form_dialog as form_module
from Kavitro_dev.modules.easements.easement_geometry_form_dialog import EasementGeometryFormDialog as Form
from Kavitro_dev.modules.easements.easement_layer_service import EasementLayerService
from Kavitro_dev.widgets.form_grid import StackedFormGrid

PREPARING = {"id": "1", "name": "Ettevalmistamisel", "color": "4FBF6B", "type": "OPEN"}
SIGNED = {"id": "2", "name": "Allkirjastatud", "color": "2188FF", "type": "OPEN"}
ARCHIVED = {"id": "3", "name": "Arhiveeritud", "color": "888888", "type": "CLOSED"}
# Named like the layer value but tied to another one, which the map must follow.
NAMED_ESTABLISHED = {"id": "4", "name": "Kehtestatud", "color": "4FBF6B", "type": "CLOSED"}
# Mapped to a layer value of its own name.
WAITING = {"id": "5", "name": "Ootel", "color": "F2C94C", "type": "OPEN"}
STATUSES = [PREPARING, SIGNED, ARCHIVED, NAMED_ESTABLISHED, WAITING]
# ARCHIVED has no row, as after „Ära kirjuta“.
MAPPING = [
    {"statusId": "1", "statusName": "Ettevalmistamisel", "layerStatus": "Ootel"},
    {"statusId": "2", "statusName": "Allkirjastatud", "layerStatus": "Kehtestatud"},
    {"statusId": "4", "statusName": "Kehtestatud", "layerStatus": "Ootel"},
    {"statusId": "5", "statusName": "Ootel", "layerStatus": "Ootel"},
]


class _FormDialogTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QgsApplication.instance() or QgsApplication([], False)

    def _keep(self, dialog):
        def delete() -> None:
            dialog.hide()
            dialog.deleteLater()
            QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)

        self.addCleanup(delete)
        return dialog

    def _show(self, dialog):
        dialog.show()
        self.app.processEvents()
        return dialog

    @staticmethod
    def _rect(dialog, widget) -> QRect:
        return QRect(widget.mapTo(dialog, QPoint(0, 0)), widget.size())

    def assert_form_is_finished(self, dialog) -> None:
        self.assertEqual(dialog.width(), dialog.DIALOG_WIDTH)
        texts = [label.text() for label in dialog.findChildren(QLabel)]
        self.assertNotIn(dialog.windowTitle(), texts, "the window title is already in the title bar")

    def assert_text_area_clears_the_buttons(self, dialog, text_area) -> None:
        bottom = text_area.mapTo(dialog, QPoint(0, 0)).y() + text_area.height()
        for button in dialog.findChildren(QPushButton):
            if button.isVisible():
                self.assertLessEqual(bottom, button.mapTo(dialog, QPoint(0, 0)).y(), button.text())

    def assert_rows_line_up(self, dialog, rows) -> None:
        left, right = self._rect(dialog, rows[0][0]).left(), self._rect(dialog, rows[0][-1]).right()
        for row in rows:
            with self.subTest(row=[type(field).__name__ for field in row]):
                self.assertEqual(len({self._rect(dialog, field).top() for field in row}), 1, "fields of a row are side by side")
                self.assertEqual(self._rect(dialog, row[0]).left(), left)
                self.assertEqual(self._rect(dialog, row[-1]).right(), right)
                for current, following in zip(row, row[1:]):
                    self.assertLess(self._rect(dialog, current).right(), self._rect(dialog, following).left())

    def assert_labels_sit_right_above(self, dialog, fields: dict) -> None:
        labels = {label.text(): label for label in dialog.findChildren(QLabel)}
        for text, field in fields.items():
            with self.subTest(label=text):
                label, field_rect = self._rect(dialog, labels[text]), self._rect(dialog, field)
                self.assertEqual(label.left(), field_rect.left())
                self.assertLessEqual(label.bottom(), field_rect.top())
                self.assertLessEqual(field_rect.top() - label.bottom(), 6)


class _EasementFormTest(_FormDialogTest):
    def setUp(self) -> None:
        self._patch(EasementLayerService, "load_status_mapping_rows", return_value=MAPPING)
        # No test may reach the server: without a session the login dialog would block the run.
        self.read = self._patch(form_module.APIModuleActions, "get_easement_status", return_value=None)
        self.update = self._patch(form_module.APIModuleActions, "update_easement_status", return_value=None)
        self.warning = self._patch(form_module.ModernMessageDialog, "show_warning", return_value=True)

    def _patch(self, target, name, **kwargs):
        patcher = patch.object(target, name, **kwargs)
        mock = patcher.start()
        self.addCleanup(patcher.stop)
        return mock

    def _form(self, status=PREPARING, *, options=STATUSES, **kwargs) -> Form:
        item = {"id": "1"} if status is None else {"id": "1", "status": status}
        return self._keep(Form(item_data=item, status_options=options, **kwargs))


class EasementFormValuesTest(_EasementFormTest):
    def test_every_value_the_layer_reads_is_returned(self) -> None:
        values = self._form().values()

        for name in (
            Form.FIELD_KIND, Form.FIELD_STATUS, Form.FIELD_NOTARY_NUMBER, Form.FIELD_LAND_OWNER, Form.FIELD_CADASTRAL,
            Form.FIELD_PHONE, Form.FIELD_EMAIL, Form.FIELD_NOTE, Form.FIELD_ESTABLISHED_DATE, Form.FIELD_SOURCE,
            Form.FIELD_NETWORK, Form.FIELD_PROTECTION_WIDTH, Form.FIELD_COMPENSATION, Form.FIELD_MUNICIPALITY,
            Form.FIELD_REGION, Form.FIELD_ADDRESS, Form.FIELD_HOUSE_NUMBER,
        ):
            self.assertIn(name, values)

    def test_initial_values_fill_both_tabs(self) -> None:
        form = self._form(initial_values={
            Form.FIELD_LAND_OWNER: "Mari", Form.FIELD_ADDRESS: "Tee 4", Form.FIELD_COMPENSATION: "12",
            Form.FIELD_CADASTRAL: "66601:008:0138, 66601:008:0139",
        })

        values = form.values()

        self.assertEqual(values[Form.FIELD_LAND_OWNER], "Mari")
        self.assertEqual(values[Form.FIELD_ADDRESS], "Tee 4")
        self.assertEqual(values[Form.FIELD_COMPENSATION], "12")
        self.assertEqual(values[Form.FIELD_CADASTRAL], "66601:008:0138, 66601:008:0139")
        self.assertEqual(values[Form.FIELD_SOURCE], "Kavitro")

    def test_long_prefilled_value_shows_its_beginning(self) -> None:
        form = self._form(initial_values={Form.FIELD_LAND_OWNER: "Riigimetsa Majandamise Keskus " * 3})

        self.assertEqual(form._land_owner.cursorPosition(), 0)


class EasementStatusTest(_EasementFormTest):
    def test_field_lists_the_kavitro_statuses_and_opens_on_the_easements_own(self) -> None:
        form = self._form(SIGNED)

        self.assertEqual(form._status.count(), len(STATUSES))
        self.assertEqual(form._status.currentData(), SIGNED["id"])
        self.assertEqual(form._status.currentText(), SIGNED["name"])

    def test_saved_value_is_the_layer_value_mapped_in_settings(self) -> None:
        self.assertEqual(self._form(PREPARING).values()[Form.FIELD_STATUS], "Ootel")

    def test_choosing_another_status_saves_its_mapped_value(self) -> None:
        form = self._form(PREPARING)

        form._status.set_current_status_id(SIGNED["id"])

        self.assertEqual(form.values()[Form.FIELD_STATUS], "Kehtestatud")

    def test_status_without_a_mapping_leaves_the_map_value_alone(self) -> None:
        form = self._form(ARCHIVED)

        self.assertEqual(form.values()[Form.FIELD_STATUS], "")
        self.assertEqual(form._status_label.text(), "Staatus (kaardil ei muutu)")

    def test_label_tells_what_reaches_the_map(self) -> None:
        form = self._form(PREPARING)
        self.assertEqual(form._status_label.text(), "Staatus (kaardil: Ootel)")

        form._status.set_current_status_id(SIGNED["id"])
        self.assertEqual(form._status_label.text(), "Staatus (kaardil: Kehtestatud)")

        form._status.set_current_status_id(ARCHIVED["id"])
        self.assertEqual(form._status_label.text(), "Staatus (kaardil ei muutu)")

        form._status.set_current_status_id(WAITING["id"])
        self.assertEqual(form._status_label.text(), "Staatus")

    def test_status_missing_from_the_list_stays_selected(self) -> None:
        retired = {"id": "99", "name": "Vana staatus", "color": "888888", "type": "OPEN"}

        form = self._form(retired)

        self.assertEqual(form._status.currentData(), "99")
        self.assertEqual(form.values()[Form.FIELD_STATUS], "")
        self.assertEqual(form._status.count(), len(STATUSES) + 1)

    def test_failed_list_keeps_the_easements_own_status(self) -> None:
        form = self._form(SIGNED, options=[])

        self.assertEqual(form._status.count(), 1)
        self.assertTrue(form._status.isEnabled())
        self.assertEqual(form.values()[Form.FIELD_STATUS], "Kehtestatud")

    def test_nothing_to_choose_saves_no_status(self) -> None:
        form = self._form(None, options=[])

        self.assertFalse(form._status.isEnabled())
        self.assertEqual(form.values()[Form.FIELD_STATUS], "")
        self.assertEqual(form._status_label.text(), "Staatus")

    def test_mapped_value_reaches_the_map_layer(self) -> None:
        layer = QgsVectorLayer("Polygon?crs=EPSG:3301&field=Staatus:string&field=Kehtestamise kuupäev:string", "servituudid", "memory")
        layer.dataProvider().addFeature(QgsFeature(layer.fields()))
        layer.updateExtents()
        feature_id = next(layer.getFeatures()).id()
        form = self._form(PREPARING)
        form._status.set_current_status_id(SIGNED["id"])

        ok, message = EasementLayerService.attach_backend_item_to_feature(
            layer=layer,
            feature_id=feature_id,
            item_id="1",
            item_data={"id": "1", "status": PREPARING, "_easement_geometry_form": form.values()},
        )

        self.assertTrue(ok, message)
        feature = layer.getFeature(feature_id)
        self.assertEqual(feature["Staatus"], "Kehtestatud")
        self.assertEqual(feature["Kehtestamise kuupäev"], QDate.currentDate().toString("yyyy-MM-dd"))

    def test_prompt_offers_the_loaded_statuses_and_returns_the_mapped_value(self) -> None:
        offered = []

        def accept(dialog) -> int:
            offered.append(dialog._status.count())
            return QDialog.Accepted

        with (
            patch.object(form_module.APIModuleActions, "get_module_status_options", return_value=STATUSES) as load,
            patch.object(Form, "exec_", new=accept),
        ):
            values = Form.prompt(item_data={"id": "1", "status": PREPARING})

        load.assert_called_once_with("easement")
        self.assertEqual(offered, [len(STATUSES)])
        self.assertEqual(values[Form.FIELD_STATUS], "Ootel")

    def test_cancelled_prompt_returns_nothing(self) -> None:
        with (
            patch.object(form_module.APIModuleActions, "get_module_status_options", return_value=STATUSES),
            patch.object(Form, "exec_", return_value=QDialog.Rejected),
        ):
            self.assertIsNone(Form.prompt(item_data={"id": "1", "status": PREPARING}))


class EasementLayerStatusTest(_EasementFormTest):
    FIELDS = "field=Staatus:string&field=ext_easement_id:string&field=Kehtestamise kuupäev:string"

    def _layer_with_area(self, status: str):
        layer = QgsVectorLayer(f"Polygon?crs=EPSG:3301&{self.FIELDS}", "servituudid", "memory")
        feature = QgsFeature(layer.fields())
        feature.setAttribute("Staatus", status)
        feature.setAttribute("ext_easement_id", "1")
        feature.setGeometry(QgsGeometry.fromWkt("POLYGON((0 0, 10 0, 10 10, 0 10, 0 0))"))
        layer.dataProvider().addFeature(feature)
        layer.updateExtents()
        return layer, next(layer.getFeatures()).id()

    @staticmethod
    def _final_cut():
        final = QgsVectorLayer("Polygon?crs=EPSG:3301", "lopp", "memory")
        feature = QgsFeature(final.fields())
        feature.setGeometry(QgsGeometry.fromWkt("POLYGON((0 0, 20 0, 20 20, 0 20, 0 0))"))
        final.dataProvider().addFeature(feature)
        return final

    def _attach(self, layer, feature_id, status):
        return EasementLayerService.attach_backend_item_to_feature(
            layer=layer,
            feature_id=feature_id,
            item_id="1",
            item_data={"id": "1", "status": status, "_easement_geometry_form": self._form(status).values()},
        )

    def _save_final_cut(self, layer, status):
        return EasementLayerService.upsert_final_cut_feature(
            layer=layer,
            final_layer=self._final_cut(),
            item_id="1",
            item_data={"id": "1", "status": status},
            form_values=self._form(status).values(),
        )

    def test_attaching_with_an_unmapped_status_keeps_the_field(self) -> None:
        layer, feature_id = self._layer_with_area("Kehtestatud")

        ok, message = self._attach(layer, feature_id, ARCHIVED)

        self.assertTrue(ok, message)
        self.assertEqual(layer.getFeature(feature_id)["Staatus"], "Kehtestatud")

    def test_final_cut_with_an_unmapped_status_keeps_the_field(self) -> None:
        layer, feature_id = self._layer_with_area("Kehtestatud")

        ok, message = self._save_final_cut(layer, ARCHIVED)

        self.assertTrue(ok, message)
        saved = layer.getFeature(feature_id)
        self.assertEqual(saved["Staatus"], "Kehtestatud")
        self.assertAlmostEqual(saved.geometry().area(), 400.0)

    def test_final_cut_with_a_mapped_status_writes_its_value(self) -> None:
        layer, feature_id = self._layer_with_area("Ootel")

        ok, message = self._save_final_cut(layer, SIGNED)

        self.assertTrue(ok, message)
        self.assertEqual(layer.getFeature(feature_id)["Staatus"], "Kehtestatud")

    def test_mapped_status_is_written_also_without_form_values(self) -> None:
        for name, save in (
            ("attach", lambda layer, feature_id: EasementLayerService.attach_backend_item_to_feature(
                layer=layer, feature_id=feature_id, item_id="1", item_data={"id": "1", "status": SIGNED})),
            ("final cut", lambda layer, _feature_id: EasementLayerService.upsert_final_cut_feature(
                layer=layer, final_layer=self._final_cut(), item_id="1", item_data={"id": "1", "status": SIGNED})),
        ):
            with self.subTest(flow=name):
                layer, feature_id = self._layer_with_area("Ootel")

                ok, message = save(layer, feature_id)

                self.assertTrue(ok, message)
                self.assertEqual(layer.getFeature(feature_id)["Staatus"], "Kehtestatud")


class EasementKavitroStatusTest(_EasementFormTest):
    def test_form_opens_on_the_status_kavitro_has_now(self) -> None:
        form = self._form(PREPARING, current_status=SIGNED)

        self.assertEqual(form._status.currentData(), SIGNED["id"])
        self.assertEqual(form.values()[Form.FIELD_STATUS], "Kehtestatud")

    def test_cards_status_is_used_when_kavitro_could_not_be_read(self) -> None:
        form = self._form(PREPARING, current_status=None)

        self.assertEqual(form._status.currentData(), PREPARING["id"])

    def test_new_status_goes_to_kavitro_before_the_form_closes(self) -> None:
        form = self._form(PREPARING)
        form._status.set_current_status_id(SIGNED["id"])
        self.update.return_value = SIGNED

        form.accept()

        self.update.assert_called_once_with("1", SIGNED["id"])
        self.assertEqual(form.result(), QDialog.Accepted)
        self.assertEqual(form.kavitro_status(), SIGNED)

    def test_unchanged_status_is_not_sent(self) -> None:
        form = self._form(PREPARING, current_status=PREPARING)

        form.accept()

        self.update.assert_not_called()
        self.assertEqual(form.result(), QDialog.Accepted)

    def test_refused_status_keeps_the_form_open(self) -> None:
        form = self._show(self._form(PREPARING))
        form._status.set_current_status_id(SIGNED["id"])

        form.accept()

        self.assertNotEqual(form.result(), QDialog.Accepted)
        self.assertTrue(form.isVisible())
        self.warning.assert_called_once()
        self.assertEqual(form.kavitro_status(), PREPARING)

    def test_old_status_chosen_again_after_a_refusal_closes_the_form(self) -> None:
        form = self._form(PREPARING)
        form._status.set_current_status_id(SIGNED["id"])
        form.accept()

        form._status.set_current_status_id(PREPARING["id"])
        form.accept()

        self.update.assert_called_once()
        self.assertEqual(form.result(), QDialog.Accepted)
        self.assertEqual(form.values()[Form.FIELD_STATUS], "Ootel")

    def _prompt(self, *, kavitro, choose=None, accept=True):
        reported = []

        def run(dialog) -> int:
            if choose is not None:
                dialog._status.set_current_status_id(choose["id"])
            if not accept:
                return QDialog.Rejected
            dialog.accept()
            return dialog.result()

        self.read.return_value = kavitro
        with (
            patch.object(form_module.APIModuleActions, "get_module_status_options", return_value=STATUSES),
            patch.object(Form, "exec_", new=run),
        ):
            values = Form.prompt(item_data={"id": "1", "status": PREPARING}, on_status_changed=reported.append)
        return values, reported

    def test_prompt_reads_the_status_from_kavitro_and_tells_the_card(self) -> None:
        values, reported = self._prompt(kavitro=SIGNED)

        self.read.assert_called_once_with("1")
        self.update.assert_not_called()
        self.assertEqual(values[Form.FIELD_STATUS], "Kehtestatud")
        self.assertEqual(reported, [SIGNED])

    def test_prompt_tells_the_card_the_saved_status(self) -> None:
        self.update.return_value = SIGNED

        values, reported = self._prompt(kavitro=PREPARING, choose=SIGNED)

        self.update.assert_called_once_with("1", SIGNED["id"])
        self.assertEqual(values[Form.FIELD_STATUS], "Kehtestatud")
        self.assertEqual(reported, [SIGNED])

    def test_prompt_tells_the_card_nothing_when_the_status_stays(self) -> None:
        _values, reported = self._prompt(kavitro=PREPARING)

        self.assertEqual(reported, [])

    def test_cancel_sends_nothing(self) -> None:
        values, reported = self._prompt(kavitro=PREPARING, choose=SIGNED, accept=False)

        self.assertIsNone(values)
        self.update.assert_not_called()
        self.assertEqual(reported, [])


class EasementEstablishedDateTest(_EasementFormTest):
    def test_date_that_will_not_be_saved_is_blank_and_locked(self) -> None:
        form = self._form(PREPARING)

        self.assertFalse(form._established_date.isEnabled())
        self.assertEqual(form._established_date.text().strip(), "")
        self.assertEqual(form.values()[Form.FIELD_ESTABLISHED_DATE], "")

    def test_status_mapped_to_established_opens_todays_date_and_saves_it(self) -> None:
        form = self._form(PREPARING)

        form._status.set_current_status_id(SIGNED["id"])

        self.assertTrue(form._established_date.isEnabled())
        self.assertEqual(form.values()[Form.FIELD_ESTABLISHED_DATE], QDate.currentDate().toString("yyyy-MM-dd"))

    def test_kavitro_name_alone_does_not_open_the_date(self) -> None:
        form = self._form(NAMED_ESTABLISHED)

        self.assertFalse(form._established_date.isEnabled())
        self.assertEqual(form.values()[Form.FIELD_ESTABLISHED_DATE], "")

    def test_leaving_the_established_status_locks_the_date_again(self) -> None:
        form = self._form(SIGNED)

        form._status.set_current_status_id(PREPARING["id"])

        self.assertFalse(form._established_date.isEnabled())
        self.assertEqual(form.values()[Form.FIELD_ESTABLISHED_DATE], "")

    def test_stored_date_stays_editable_and_keeps_its_value(self) -> None:
        form = self._form(PREPARING, initial_values={Form.FIELD_ESTABLISHED_DATE: "2025-03-14"})

        self.assertTrue(form._established_date.isEnabled())
        self.assertEqual(form.values()[Form.FIELD_ESTABLISHED_DATE], "2025-03-14")


class EasementFormLayoutTest(_EasementFormTest):
    def setUp(self) -> None:
        super().setUp()
        self.form = self._show(self._form())
        form = self.form
        self.data_rows = [
            [form._kind, form._status],
            [form._established_date, form._notary_number, form._source],
            [form._land_owner, form._phone, form._email],
            [form._network, form._protection_width, form._compensation],
            [form._note],
        ]
        self.location_rows = [[form._municipality, form._region], [form._address, form._house_number], [form._cadastral]]

    def _x(self, widget) -> int:
        return self._rect(self.form, widget).x()

    def _open_location_tab(self) -> None:
        self.form.findChild(QTabWidget).setCurrentIndex(1)
        self.app.processEvents()

    def test_form_has_no_repeated_title_and_uses_the_form_width(self) -> None:
        self.assert_form_is_finished(self.form)

    def test_fields_share_rows_and_line_up_on_both_edges(self) -> None:
        self.assert_rows_line_up(self.form, self.data_rows)

        self._open_location_tab()
        self.assert_rows_line_up(self.form, self.location_rows)

    def test_cadastral_number_is_on_the_location_tab(self) -> None:
        tabs = self.form.findChild(QTabWidget)

        self.assertTrue(tabs.widget(1).isAncestorOf(self.form._cadastral))
        self.assertFalse(tabs.widget(0).isAncestorOf(self.form._cadastral))

    def test_field_widths_follow_what_they_hold(self) -> None:
        form = self.form
        self.assertLess(form._established_date.width(), form._kind.width())

        self._open_location_tab()
        self.assertLess(form._house_number.width(), form._address.width())
        self.assertLess(form._address.width(), form._cadastral.width())

    def test_rows_of_three_share_their_columns(self) -> None:
        form = self.form

        self.assertEqual(self._x(form._notary_number), self._x(form._phone))
        self.assertEqual(self._x(form._notary_number), self._x(form._protection_width))
        self.assertEqual(self._x(form._source), self._x(form._email))
        self.assertEqual(self._x(form._source), self._x(form._compensation))

    def test_every_single_line_field_has_the_same_height(self) -> None:
        # The status widget's own frame fills the row; what shows is the control inside it.
        visible = [self.form._status._control if field is self.form._status else field for row in self.data_rows[:-1] for field in row]

        heights = {field.height() for field in visible}

        self.assertEqual(len(heights), 1, heights)

    def test_each_label_sits_right_above_its_field(self) -> None:
        form = self.form
        self.assert_labels_sit_right_above(form, {
            Form.FIELD_KIND: form._kind, form._status_label.text(): form._status,
            Form.FIELD_ESTABLISHED_DATE: form._established_date, Form.FIELD_NOTARY_NUMBER: form._notary_number,
            Form.FIELD_SOURCE: form._source, Form.FIELD_LAND_OWNER: form._land_owner,
            Form.FIELD_PHONE: form._phone, Form.FIELD_EMAIL: form._email, Form.FIELD_NETWORK: form._network,
            Form.FIELD_PROTECTION_WIDTH: form._protection_width, Form.FIELD_COMPENSATION: form._compensation,
            Form.FIELD_NOTE: form._note,
        })

        self._open_location_tab()
        self.assert_labels_sit_right_above(form, {
            Form.FIELD_MUNICIPALITY: form._municipality, Form.FIELD_REGION: form._region,
            Form.FIELD_ADDRESS: form._address, Form.FIELD_HOUSE_NUMBER: form._house_number,
            Form.FIELD_CADASTRAL: form._cadastral,
        })

    def test_changing_the_status_does_not_move_the_other_fields(self) -> None:
        kind_width = self.form._kind.width()
        long_value = [{"statusId": "2", "statusName": "Allkirjastatud", "layerStatus": "Väga pikk väärtus " * 8}]

        with patch.object(EasementLayerService, "load_status_mapping_rows", return_value=long_value):
            self.form._status.set_current_status_id(SIGNED["id"])
            self.app.processEvents()

        self.assert_form_is_finished(self.form)
        self.assertEqual(self.form._kind.width(), kind_width)

    def test_fields_keep_their_place_when_the_tab_changes(self) -> None:
        data_x = self._x(self.form._kind)

        self._open_location_tab()

        self.assertEqual(self._x(self.form._municipality), data_x)

    def test_tab_key_follows_the_visible_order(self) -> None:
        expected = [field for row in self.data_rows + self.location_rows for field in row]
        order, widget = [], self.form._kind
        for _ in range(200):
            if any(widget is known for known in expected) and not any(widget is seen for seen in order):
                order.append(widget)
            widget = widget.nextInFocusChain()

        self.assertEqual([id(item) for item in order], [id(item) for item in expected])

    def test_content_does_not_reach_the_buttons(self) -> None:
        self.assert_text_area_clears_the_buttons(self.form, self.form._note)
        self.assertGreaterEqual(self.form._note.height(), 76)

    def test_note_grows_with_the_window(self) -> None:
        before = self.form._note.height()

        self.form.resize(self.form.width(), self.form.height() + 100)
        self.app.processEvents()

        self.assertEqual(self.form._note.height(), before + 100)

    def test_side_by_side_fields_make_the_form_shorter(self) -> None:
        self.assertLessEqual(self.form.height(), 600)


class StackedFormGridTest(_FormDialogTest):
    def test_spans_of_one_size_are_equally_wide_however_the_rows_are_split(self) -> None:
        # One-letter labels: what is measured is the grid, not label text in the test fonts.
        host = QWidget()
        self._keep(host)
        grid = StackedFormGrid(host)
        rows = [[QLineEdit(host) for _ in range(count)] for count in (2, 3, 4, 3)]
        for row in rows:
            grid.add_fields(*[("a", field, StackedFormGrid.COLUMNS // len(row)) for field in row])
        host.resize(588, 400)
        self._show(host)

        for row in rows:
            with self.subTest(fields=len(row)):
                self.assertEqual(len({field.width() for field in row}), 1, [field.width() for field in row])
        self.assertEqual(rows[1][0].width(), rows[3][0].width())
        self.assertEqual(sum(field.width() for field in rows[1]) + 2 * StackedFormGrid.SPACING, 588)

    def test_long_value_does_not_widen_its_column(self) -> None:
        host = QWidget()
        self._keep(host)
        grid = StackedFormGrid(host)
        # A combo asks for the width of its longest item; a line edit's wish does not depend on its text.
        long_value, short_value = QComboBox(host), QComboBox(host)
        long_value.addItem("x" * 200)
        short_value.addItem("x")
        grid.add_fields(("a", long_value, 6), ("b", short_value, 6))
        host.resize(588, 200)
        self._show(host)

        self.assertEqual(long_value.width(), short_value.width())


class FormOpeningHeightTest(_FormDialogTest):
    def _opening_height_is_what_the_content_asks_for(self, make_form) -> None:
        for point_size in (9, 10, 12):
            self.addCleanup(self.app.setFont, self.app.font())
            self.app.setFont(QFont("Segoe UI", point_size))
            form = self._show(self._keep(make_form()))
            with self.subTest(point_size=point_size):
                self.assertEqual(form.height(), form.layout().totalHeightForWidth(form.width()))

    def test_easement_form(self) -> None:
        with patch.object(EasementLayerService, "load_status_mapping_rows", return_value=MAPPING):
            self._opening_height_is_what_the_content_asks_for(lambda: Form(item_data={"id": "1", "status": PREPARING}, status_options=STATUSES))

    def test_as_built_form(self) -> None:
        self._opening_height_is_what_the_content_asks_for(lambda: AsBuiltGeometryFormDialog(item_data={"id": "1"}))


class AsBuiltFormTest(_FormDialogTest):
    def _form(self, item_data=None) -> AsBuiltGeometryFormDialog:
        return self._keep(AsBuiltGeometryFormDialog(item_data=item_data or {"id": "1"}))

    def test_form_has_no_repeated_title_and_uses_the_form_width(self) -> None:
        self.assert_form_is_finished(self._show(self._form()))

    def test_buttons_do_not_cover_the_notes(self) -> None:
        form = self._show(self._form())

        self.assert_text_area_clears_the_buttons(form, form._notes)
        self.assertGreaterEqual(form._notes.height(), 80)

    def test_fields_share_rows_and_line_up_on_both_edges(self) -> None:
        form = self._show(self._form())
        network = form._network_checks["Vesi"].parentWidget()

        self.assert_rows_line_up(form, [
            [form._work_number, form._object],
            [form._survey_date, form._surveyor, form._contact],
            [form._drawing_type, form._scale, form._coordinate_system, form._height_system],
            [network],
            [form._notes],
        ])

    def test_each_label_sits_right_above_its_field(self) -> None:
        form = self._show(self._form())

        self.assert_labels_sit_right_above(form, {
            "Töö nr": form._work_number, "Objekt": form._object, "Mõõdistamise kpv": form._survey_date,
            "Mõõdistaja": form._surveyor, "Kontakt": form._contact, "Joonis": form._drawing_type,
            "Mõõtkava": form._scale, "Koordinaatsüsteem": form._coordinate_system, "Kõrgussüsteem": form._height_system,
            "Võrk": form._network_checks["Vesi"].parentWidget(), "Märkused": form._notes,
        })

    def test_values_keep_their_field_names_and_defaults(self) -> None:
        form = self._form({"id": "7", "name": "Tee 1"})
        form._network_checks["Vesi"].setChecked(True)

        values = form.values()

        self.assertEqual(values["Töö nr"], "7")
        self.assertEqual(values["Objekt"], "Tee 1")
        self.assertEqual(values["Joonis"], "TJ")
        self.assertEqual(values["Mõõtkava"], "500")
        self.assertIs(values["Vesi"], True)
        self.assertIs(values["Gaas"], False)
        self.assertEqual(len(form._network_checks), len(AsBuiltGeometryFormDialog.NETWORK_FIELDS))


if __name__ == "__main__":
    unittest.main()
