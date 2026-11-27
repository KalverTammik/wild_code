"""Three easement preview fixes from the 07_01 button audit.

1. "Rounded corners" sets the buffer join style; "Round ends" sets the end cap.
2. Marking a free property link payable shows its total and payment date; unmarking hides them.
3. Publishing the PDF checks for a file with the same name and asks replace / new version / cancel.
"""
from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
PLUGIN_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLUGIN_ROOT.parent))

from qgis.core import QgsApplication, QgsFeature, QgsGeometry, QgsVectorLayer
from qgis.PyQt.QtCore import QCoreApplication, QEvent

from Kavitro_dev.constants.cadastral_fields import AreaUnit
from Kavitro_dev.languages.translation_keys import TranslationKeys
from Kavitro_dev.modules.easements.easement_pdf_service import EasementPdfService
from Kavitro_dev.modules.easements.easement_preview_dialog import EasementPreviewDialog
from Kavitro_dev.utils.project_base_layers import ProjectBaseLayerKeys, ProjectBaseLayersService
from Kavitro_dev.widgets.EasementPropertyAreaCalculationWidget import EasementPropertyAreaCalculationWidget

_APP = QgsApplication.instance() or QgsApplication([], False)
if QgsApplication.instance() is _APP:
    QgsApplication.initQgis()

ITEM = {"id": "E1", "number": "S-1", "name": "Servituut"}
LAYERS = "Kavitro_dev.modules.easements.preview_dialog.preview_layers_mixin"
SAVE = "Kavitro_dev.modules.easements.preview_dialog.final_save_mixin"


def _line_layer():
    layer = QgsVectorLayer("LineString?crs=EPSG:3301&field=x:int", "pipes", "memory")
    feature = QgsFeature(layer.fields())
    feature.setAttributes([1])
    feature.setGeometry(QgsGeometry.fromWkt("LINESTRING(0 0, 10 0, 10 10)"))
    layer.dataProvider().addFeatures([feature])
    layer.selectAll()
    return layer


class _DialogCase(unittest.TestCase):
    def setUp(self):
        resolve = patch.object(ProjectBaseLayersService, "resolve_layer", return_value=None)
        resolve.start()
        self.addCleanup(resolve.stop)
        self.dialog = EasementPreviewDialog(item_data=ITEM)
        self.addCleanup(self._delete_dialog)

    def _delete_dialog(self):
        self.dialog.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)


# --------------------------------------------------------------------------- 1. corners and ends
class BufferStyleTest(_DialogCase):
    def test_both_checkboxes_start_rounded(self):
        self.assertTrue(self.dialog._rounded_corners_checkbox.isChecked())
        self.assertTrue(self.dialog._round_ends_checkbox.isChecked())
        self.assertEqual((self.dialog._buffer_join_style(), self.dialog._buffer_end_cap_style()), (0, 0))

    def test_rounded_corners_sets_only_the_join_style(self):
        self.dialog._rounded_corners_checkbox.setChecked(False)
        self.assertEqual((self.dialog._buffer_join_style(), self.dialog._buffer_end_cap_style()), (1, 0))

    def test_round_ends_sets_only_the_end_cap(self):
        self.dialog._round_ends_checkbox.setChecked(False)
        self.assertEqual((self.dialog._buffer_join_style(), self.dialog._buffer_end_cap_style()), (0, 1))

    def test_the_labels_name_corners_and_ends(self):
        lang = self.dialog._lang
        self.assertEqual(self.dialog._rounded_corners_checkbox.text(),
                         lang.translate(TranslationKeys.EASEMENT_PREVIEW_ROUNDED_CAPS))
        self.assertEqual(self.dialog._round_ends_checkbox.text(),
                         lang.translate(TranslationKeys.EASEMENT_PREVIEW_ROUND_ENDS))
        self.assertNotEqual(self.dialog._rounded_corners_checkbox.text(), self.dialog._round_ends_checkbox.text())

    def test_network_buffer_gets_both_styles(self):
        self.dialog._rounded_corners_checkbox.setChecked(False)
        layer = _line_layer()
        with patch.object(self.dialog, "_resolve_source_layer", return_value=layer), \
                patch(f"{LAYERS}.LayerProcessingService.buffer_selected_features", return_value=None) as buffer:
            self.dialog._create_preview(ProjectBaseLayerKeys.WATERPIPES)
        kwargs = buffer.call_args.kwargs
        self.assertEqual((kwargs["join_style"], kwargs["end_cap_style"]), (1, 0))

    def test_property_buffer_gets_both_styles(self):
        self.dialog._round_ends_checkbox.setChecked(False)
        self.dialog._connected_property_numbers = ["1:1"]
        with patch(f"{LAYERS}.PropertiesSelectors.show_connected_properties_on_map", return_value=_line_layer()), \
                patch.object(self.dialog, "_refresh_property_summary_card"), \
                patch(f"{LAYERS}.LayerProcessingService.buffer_selected_features", return_value=None) as buffer:
            self.dialog._run_connected_property_preview_flow()
        kwargs = buffer.call_args.kwargs
        self.assertEqual((kwargs["join_style"], kwargs["end_cap_style"]), (0, 1))

    def test_each_checkbox_reruns_the_preview(self):
        self.dialog._auto_initialized = True
        with patch("Kavitro_dev.modules.easements.easement_preview_dialog.QTimer.singleShot") as single_shot:
            self.dialog._rounded_corners_checkbox.setChecked(False)
            self.dialog._round_ends_checkbox.setChecked(False)
        self.assertEqual(single_shot.call_count, 2)


# --------------------------------------------------------------------------- 2. payable link fields
class PayableFieldsWidgetTest(unittest.TestCase):
    def setUp(self):
        self.lang = Mock()
        self.lang.translate.side_effect = str
        self.widget = EasementPropertyAreaCalculationWidget(
            lang_manager=self.lang,
            edge={"area": {"size": 2.0, "unit": AreaUnit.M}, "isPayable": False},
            area_unit_labels={AreaUnit.M: "m2", AreaUnit.H: "ha"},
            default_currency="EUR",
        )

    def tearDown(self):
        self.widget.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)

    def test_free_link_hides_the_payment_fields(self):
        self.assertIsNotNone(self.widget.total_label)
        self.assertIsNotNone(self.widget.next_payment_edit)
        self.assertTrue(self.widget.total_label.isHidden())
        self.assertTrue(self.widget.next_payment_edit.isHidden())

    def test_marking_payable_shows_the_fields_and_unmarking_hides_them(self):
        totals = []
        self.widget.totalsChanged.connect(lambda: totals.append(True))
        self.widget.payable_checkbox.setChecked(True)
        self.assertFalse(self.widget.total_label.isHidden())
        self.assertFalse(self.widget.next_payment_edit.isHidden())
        self.widget.next_payment_edit.setText(" 2027-03-01 ")
        self.assertEqual(self.widget.next_payment_text(), "2027-03-01")

        self.widget.payable_checkbox.setChecked(False)
        self.assertTrue(self.widget.total_label.isHidden())
        self.assertTrue(self.widget.next_payment_edit.isHidden())
        self.assertEqual(self.widget.next_payment_text(), "")
        self.assertEqual(totals, [True, True])


class PayableFieldsDialogTest(_DialogCase):
    def _edges(self):
        return [{"node": {"id": "P2", "cadastralUnitNumber": "2:2"}, "isPayable": False}]

    def test_new_payable_link_sends_its_payment_date(self):
        self.dialog._set_property_edges(self._edges())
        editor = self.dialog._property_row_widgets["2:2"]["editor_widget"]
        editor.payable_checkbox.setChecked(True)
        editor.next_payment_edit.setText("2027-03-01")

        payloads, invalid = self.dialog._collect_property_payloads()

        self.assertEqual(invalid, [])
        self.assertTrue(payloads[0]["isPayable"])
        self.assertIn("nextPaymentDate", payloads[0])
        self.assertTrue(editor.total_label.text())

    def test_hidden_date_of_a_free_link_does_not_block_saving(self):
        self.dialog._set_property_edges(self._edges())
        editor = self.dialog._property_row_widgets["2:2"]["editor_widget"]
        editor.payable_checkbox.setChecked(True)
        editor.next_payment_edit.setText("vigane")
        editor.payable_checkbox.setChecked(False)

        payloads, invalid = self.dialog._collect_property_payloads()

        self.assertEqual(invalid, [])
        self.assertNotIn("nextPaymentDate", payloads[0])


# --------------------------------------------------------------------------- 3. publishing the PDF
class PublishDrawingTest(_DialogCase):
    def setUp(self):
        super().setUp()
        self.path = str(EasementPdfService._output_pdf_path(item_number="S-1", item_id="E1"))
        Path(self.path).write_bytes(b"%PDF-1.4\n")
        self.dialog._generated_pdf_path = self.path
        self.addCleanup(self._cleanup_pdf)
        ensure = patch.object(self.dialog, "_ensure_generated_pdf", side_effect=lambda: (self.dialog._generated_pdf_path, ""))
        ensure.start()
        self.addCleanup(ensure.stop)
        self.messages = MagicMock()
        self.messages.show_warning.return_value = False
        messages = patch(f"{SAVE}.ModernMessageDialog", self.messages)
        messages.start()
        self.addCleanup(messages.stop)
        self.api = MagicMock()
        self.api.get_module_files.return_value = []
        self.api.upload_module_file.return_value = {"uuid": "new"}
        self.api.delete_file.return_value = {"uuid": "old"}
        api = patch(f"{SAVE}.APIModuleActions", self.api)
        api.start()
        self.addCleanup(api.stop)

    def _cleanup_pdf(self):
        for path in {self.path, self.dialog._generated_pdf_path}:
            if path:
                EasementPdfService.cleanup_output_pdf(path)

    def _existing(self, *names, deleted=False):
        self.api.get_module_files.return_value = [
            {"uuid": f"old-{i}", "fileName": name, "deletedAt": "2026-01-01" if deleted else None}
            for i, name in enumerate(names)
        ]

    def _choose(self, key):
        label = None if key is None else self.dialog._lang.translate(key)
        self.messages.ask_choice_modern.return_value = label

    def _uploaded_name(self):
        return os.path.basename(self.api.upload_module_file.call_args.args[2])

    def test_without_a_same_name_file_it_uploads_and_names_the_file(self):
        self._existing("muu.pdf", "S-1.pdf", deleted=True)
        self.dialog._publish_pdf_drawing()

        self.messages.ask_choice_modern.assert_not_called()
        self.assertEqual(self._uploaded_name(), "S-1.pdf")
        self.assertIn("S-1.pdf", self.messages.show_info.call_args.args[1])
        self.api.delete_file.assert_not_called()

    def test_existing_file_asks_with_cancel_as_default(self):
        self._existing("s-1.PDF")
        self._choose(TranslationKeys.CANCEL_BUTTON)
        self.dialog._publish_pdf_drawing()

        kwargs = self.messages.ask_choice_modern.call_args.kwargs
        cancel = self.dialog._lang.translate(TranslationKeys.CANCEL_BUTTON)
        self.assertEqual((kwargs["default"], kwargs["cancel"]), (cancel, cancel))
        self.assertEqual(len(kwargs["buttons"]), 3)
        self.assertIn("S-1.pdf", self.messages.ask_choice_modern.call_args.args[1])
        self.api.upload_module_file.assert_not_called()

    def test_closing_the_question_uploads_nothing(self):
        self._existing("S-1.pdf")
        self._choose(None)
        self.dialog._publish_pdf_drawing()
        self.api.upload_module_file.assert_not_called()

    def test_replace_uploads_first_then_removes_the_old_file(self):
        self._existing("S-1.pdf")
        self._choose(TranslationKeys.EASEMENT_PREVIEW_DRAWING_REPLACE)
        order = []
        self.api.upload_module_file.side_effect = lambda *a, **k: order.append("upload") or {"uuid": "new"}
        self.api.delete_file.side_effect = lambda uuid: order.append(f"delete {uuid}") or {"uuid": uuid}

        self.dialog._publish_pdf_drawing()

        self.assertEqual(order, ["upload", "delete old-0"])
        self.assertEqual(self._uploaded_name(), "S-1.pdf")
        self.messages.show_info.assert_called_once()

    def test_replace_warns_when_the_old_file_stays(self):
        self._existing("S-1.pdf")
        self._choose(TranslationKeys.EASEMENT_PREVIEW_DRAWING_REPLACE)
        self.api.delete_file.return_value = None

        self.dialog._publish_pdf_drawing()

        self.messages.show_warning.assert_called_once()
        self.messages.show_info.assert_not_called()

    def test_failed_upload_in_replace_keeps_the_old_file(self):
        self._existing("S-1.pdf")
        self._choose(TranslationKeys.EASEMENT_PREVIEW_DRAWING_REPLACE)
        self.api.upload_module_file.return_value = None

        self.dialog._publish_pdf_drawing()

        self.api.delete_file.assert_not_called()
        self.messages.show_error.assert_called_once()

    def test_new_version_uploads_the_next_free_name(self):
        self._existing("S-1.pdf", "S-1_v2.pdf")
        self._choose(TranslationKeys.EASEMENT_PREVIEW_DRAWING_NEW_VERSION)

        self.dialog._publish_pdf_drawing()

        self.assertIn("S-1_v3.pdf", self.messages.ask_choice_modern.call_args.args[1])
        self.assertEqual(self._uploaded_name(), "S-1_v3.pdf")
        self.assertTrue(os.path.isfile(self.dialog._generated_pdf_path))
        self.assertEqual(os.path.basename(self.dialog._generated_pdf_path), "S-1_v3.pdf")
        self.api.delete_file.assert_not_called()

    def test_unreadable_file_list_asks_before_uploading(self):
        self.api.get_module_files.return_value = None
        self.dialog._publish_pdf_drawing()
        self.assertTrue(self.messages.show_warning.call_args.kwargs["with_cancel"])
        self.api.upload_module_file.assert_not_called()

        self.messages.show_warning.return_value = True
        self.dialog._publish_pdf_drawing()
        self.api.upload_module_file.assert_called_once()

    def test_button_is_disabled_while_publishing(self):
        states = []
        self.api.upload_module_file.side_effect = (
            lambda *a, **k: states.append(self.dialog._publish_drawing_button.isEnabled()) or {"uuid": "new"}
        )
        self.dialog._publish_pdf_drawing()
        self.assertEqual(states, [False])
        self.assertTrue(self.dialog._publish_drawing_button.isEnabled())

    def test_a_second_click_during_publishing_does_nothing(self):
        self.dialog._publish_in_progress = True
        self.dialog._publish_pdf_drawing()
        self.api.get_module_files.assert_not_called()
        self.api.upload_module_file.assert_not_called()

    def test_an_error_is_reported_and_the_button_comes_back(self):
        self.api.get_module_files.side_effect = RuntimeError("boom")
        with patch(f"{SAVE}.PythonFailLogger") as logger:
            self.dialog._publish_pdf_drawing()
        logger.log_exception.assert_called_once()
        self.messages.show_error.assert_called_once()
        self.assertTrue(self.dialog._publish_drawing_button.isEnabled())
        self.assertFalse(self.dialog._publish_in_progress)


class RenameOutputPdfTest(unittest.TestCase):
    def test_only_owned_files_are_renamed(self):
        path = EasementPdfService._output_pdf_path(item_number="S-9", item_id="E9")
        path.write_bytes(b"%PDF")
        renamed = EasementPdfService.rename_output_pdf(path, "S-9_v2")
        try:
            self.assertEqual(os.path.basename(renamed), "S-9_v2.pdf")
            self.assertFalse(path.exists())
            self.assertEqual(EasementPdfService.rename_output_pdf(path, "x"), "")
        finally:
            EasementPdfService.cleanup_output_pdf(renamed)
        self.assertFalse(Path(renamed).exists())


if __name__ == "__main__":
    unittest.main()
