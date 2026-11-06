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

from qgis.core import QgsFeature, QgsField, QgsFields, QgsPointXY
from qgis.PyQt.QtCore import QCoreApplication, QEvent, QPoint, QRect, Qt, QVariant
from qgis.PyQt.QtWidgets import QApplication, QLabel, QStyle, QStyledItemDelegate

from Kavitro_dev.constants.cadastral_fields import Katastriyksus
from Kavitro_dev.languages.language_manager import LanguageManager
from Kavitro_dev.languages.translation_keys import TranslationKeys
from Kavitro_dev.modules.works import works_create_dialog as dialog_module

ADDRESS =" ".join(["66601:008:0138 · Õpetajate tee 4 · Rannu alevik · Elva vald · Tartu maakond"] * 3)


class WorksCreateDialogTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self) -> None:
        self.lang = LanguageManager(language="et")
        address = patch.object(dialog_module.WorksLayerService, "property_display_text", return_value=ADDRESS)
        address.start()
        self.addCleanup(address.stop)
        self.dialog = self._make_dialog(Mock(attribute=self._property_attribute))

    @staticmethod
    def _property_attribute(name: str) -> str:
        return "Õpetajate tee 4" if name == Katastriyksus.l_aadress else "66601:008:0138"

    def _make_dialog(self, property_feature):
        return dialog_module.WorksCreateDialog(
            point=QgsPointXY(630385.62, 6457752.97),
            property_feature=property_feature,
            type_options=[{"id": "1", "label": "Avarii"}],
            assignable_users=[{"id": "1", "displayName": "Kasutaja"}],
            status_options=[{"id": "a", "name": "Planeeritud", "color": "4FBF6B", "type": "OPEN", "isDefault": True}],
            priority_options=[{"value": "", "label": "Puudub"}, {"value": "HIGH", "label": "Kõrge"}],
            lang_manager=self.lang,
        )

    def tearDown(self) -> None:
        self.dialog.hide()
        self.dialog.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)

    def _top(self, widget) -> int:
        return widget.mapTo(self.dialog, QPoint(0, 0)).y()

    def test_placeholder_type_stays_out_of_the_suggested_title(self) -> None:
        self.assertEqual(self.dialog.title_text(), "Õpetajate tee 4")
        self.assertNotIn(self.lang.translate(TranslationKeys.SELECT), self.dialog.title_text())

    def test_suggested_title_is_type_and_street_address_only(self) -> None:
        self.dialog._type_combo.setCurrentIndex(1)

        self.assertEqual(self.dialog.title_text(), "Avarii · Õpetajate tee 4")

    def test_suggested_title_without_a_property_is_the_type(self) -> None:
        dialog = self._make_dialog(None)
        self.addCleanup(dialog.deleteLater)

        dialog._type_combo.setCurrentIndex(1)

        self.assertEqual(dialog.title_text(), "Avarii")

    def test_suggested_title_skips_an_empty_address(self) -> None:
        fields = QgsFields()
        fields.append(QgsField(Katastriyksus.l_aadress, QVariant.String))
        feature = QgsFeature(fields)
        feature.setAttribute(Katastriyksus.l_aadress, None)
        dialog = self._make_dialog(feature)
        self.addCleanup(dialog.deleteLater)

        dialog._type_combo.setCurrentIndex(1)

        self.assertEqual(dialog.title_text(), "Avarii")

    def test_typed_title_is_not_replaced(self) -> None:
        self.dialog._title_edit.setText("Oma pealkiri")
        self.dialog._title_edit.textEdited.emit("Oma pealkiri")

        self.dialog._type_combo.setCurrentIndex(1)

        self.assertEqual(self.dialog.title_text(), "Oma pealkiri")

    def test_tab_order_follows_the_visible_form(self) -> None:
        names = {
            self.dialog._type_combo: "type",
            self.dialog._title_edit: "title",
            self.dialog._responsible_combo: "responsible",
            self.dialog._status_combo._control: "status",
            self.dialog._priority_combo: "priority",
            self.dialog._description_edit: "description",
            self.dialog._cancel_btn: "cancel",
            self.dialog._create_btn: "create",
        }
        order = []
        widget = self.dialog._type_combo
        for _ in range(60):
            name = names.get(widget)
            if name and name not in order:
                order.append(name)
            widget = widget.nextInFocusChain()

        self.assertEqual(order, ["type", "title", "responsible", "status", "priority", "description", "cancel", "create"])

    def test_form_combos_open_a_styled_list_instead_of_a_theme_menu(self) -> None:
        self.dialog.show()
        self.app.processEvents()

        for combo in (self.dialog._type_combo, self.dialog._responsible_combo, self.dialog._priority_combo):
            self.assertIsInstance(combo.itemDelegate(), QStyledItemDelegate)
            self.assertTrue(combo.view().property("kavitroFormPopup"))
            self.assertEqual(combo.style().styleHint(QStyle.SH_ComboBox_Popup, None, combo), 0)

    def test_wrapped_property_text_does_not_push_the_form_over_the_buttons(self) -> None:
        self.dialog.show()
        self.app.processEvents()

        description = self.dialog._description_edit
        self.assertLessEqual(self._top(description) + description.height(), self._top(self.dialog._create_btn))
        property_value = self.dialog._property_value
        self.assertGreater(property_value.heightForWidth(property_value.width()), property_value.fontMetrics().height(), "the text wraps")
        self.assertGreaterEqual(property_value.height(), property_value.heightForWidth(property_value.width()), "every wrapped line shows")

    def _rect(self, widget) -> QRect:
        return QRect(widget.mapTo(self.dialog, QPoint(0, 0)), widget.size())

    def test_fields_share_rows_and_line_up_on_both_edges(self) -> None:
        self.dialog.show()
        self.app.processEvents()
        dialog = self.dialog
        rows = [
            [dialog._property_value, dialog._coordinates_value],
            [dialog._type_combo, dialog._title_edit],
            [dialog._responsible_combo, dialog._status_combo, dialog._priority_combo],
            [dialog._description_edit],
        ]

        left, right = self._rect(rows[0][0]).left(), self._rect(rows[0][-1]).right()
        for row in rows:
            with self.subTest(row=[type(field).__name__ for field in row]):
                self.assertEqual(len({self._rect(field).top() for field in row}), 1, "fields of a row are side by side")
                self.assertEqual(self._rect(row[0]).left(), left)
                self.assertEqual(self._rect(row[-1]).right(), right)
                for current, following in zip(row, row[1:]):
                    self.assertLess(self._rect(current).right(), self._rect(following).left())

    def test_each_label_sits_right_above_its_field(self) -> None:
        self.dialog.show()
        self.app.processEvents()
        translate, dialog = self.lang.translate, self.dialog
        fields = {
            translate(TranslationKeys.WORKS_CREATE_PROPERTY_LABEL): dialog._property_value,
            translate(TranslationKeys.WORKS_CREATE_COORDINATES_LABEL): dialog._coordinates_value,
            f"{translate(TranslationKeys.WORKS_CREATE_TYPE_LABEL)} *": dialog._type_combo,
            f"{translate(TranslationKeys.WORKS_CREATE_TITLE_LABEL)} *": dialog._title_edit,
            translate(TranslationKeys.WORKS_CREATE_RESPONSIBLE_LABEL): dialog._responsible_combo,
            translate(TranslationKeys.WORKS_CREATE_STATUS_LABEL): dialog._status_combo,
            translate(TranslationKeys.WORKS_CREATE_PRIORITY_LABEL): dialog._priority_combo,
            translate(TranslationKeys.WORKS_CREATE_DESCRIPTION_LABEL): dialog._description_edit,
        }
        labels = {label.text(): label for label in dialog.findChildren(QLabel)}

        for text, field in fields.items():
            with self.subTest(label=text):
                label, field_rect = self._rect(labels[text]), self._rect(field)
                self.assertEqual(label.left(), field_rect.left())
                self.assertLessEqual(label.bottom(), field_rect.top())
                self.assertLessEqual(field_rect.top() - label.bottom(), 6)

    def test_wrapped_property_text_and_coordinates_start_on_the_same_line(self) -> None:
        for value in (self.dialog._property_value, self.dialog._coordinates_value):
            self.assertTrue(value.alignment() & Qt.AlignTop, value.text())

    def test_status_control_is_as_tall_as_the_other_inputs(self) -> None:
        self.dialog.show()
        self.app.processEvents()

        self.assertEqual(self.dialog._status_combo._control.height(), self.dialog._title_edit.height())


if __name__ == "__main__":
    unittest.main()
