"""Silent broad handlers in the easement and as-built modules now narrow the type or leave a log line."""
from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, Mock, patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
if os.environ.get("QGIS_PREFIX_PATH"):
    sys.path.append(str(Path(os.environ["QGIS_PREFIX_PATH"]) / "python" / "plugins"))

from qgis.core import QgsApplication, QgsFeature, QgsField, QgsVectorLayer
from qgis.PyQt.QtCore import QVariant

from Kavitro_dev.Logs.python_fail_logger import PythonFailLogger
from Kavitro_dev.modules.asbuilt.asbuilt_layer_service import AsBuiltLayerService
from Kavitro_dev.modules.easements import easement_pdf_service as pdf_module
from Kavitro_dev.modules.easements import easement_preview_dialog as preview_module
from Kavitro_dev.modules.easements.easement_layer_service import EasementLayerService
from Kavitro_dev.modules.easements.easement_pdf_service import EasementPdfService
from Kavitro_dev.modules.easements.easement_preview_dialog import EasementPreviewDialog


class LoggedExceptionTestCase(unittest.TestCase):
    """Collects what PythonFailLogger.log_exception receives, without writing real log files."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QgsApplication.instance() or QgsApplication([], False)

    def setUp(self) -> None:
        patcher = patch.object(PythonFailLogger, "log_exception")
        self.log = patcher.start()
        self.addCleanup(patcher.stop)

    def events(self) -> list[str]:
        return [call.kwargs["event"] for call in self.log.call_args_list]

    def modules(self) -> set[str]:
        return {call.kwargs["module"] for call in self.log.call_args_list}


def _editing_layer(*, update_fields_error: Exception) -> MagicMock:
    """A layer whose edit session fails halfway and whose rollBack fails too."""
    layer = MagicMock(spec=QgsVectorLayer)
    layer.isValid.return_value = True
    layer.isEditable.side_effect = [False, True]
    layer.startEditing.return_value = True
    layer.addAttribute.return_value = True
    layer.updateFields.side_effect = update_fields_error
    layer.rollBack.side_effect = RuntimeError("rollback boom")
    return layer


class AsBuiltLayerServiceLoggingTest(LoggedExceptionTestCase):
    def test_failed_rollback_is_logged_next_to_the_original_error(self) -> None:
        layer = _editing_layer(update_fields_error=RuntimeError("boom"))
        with patch.object(AsBuiltLayerService, "_field_map", return_value={}):
            result = AsBuiltLayerService._ensure_custom_fields(layer)

        self.assertEqual(result, (False, "boom"))
        self.assertEqual(
            self.events(),
            ["asbuilt_layer_ensure_fields_rollback_failed", "asbuilt_layer_ensure_fields_failed"],
        )
        self.assertEqual(self.modules(), {"asbuilt"})

    def test_added_by_failure_is_logged_and_saving_goes_on(self) -> None:
        layer = MagicMock(spec=QgsVectorLayer)
        layer.isValid.return_value = True
        layer.isEditable.return_value = True
        layer.updateFeature.return_value = False
        feature = Mock()
        feature.attribute.side_effect = KeyError("added_by")

        with (
            patch.object(AsBuiltLayerService, "_ensure_custom_fields", return_value=(True, "")),
            patch.object(AsBuiltLayerService, "_feature_by_id", return_value=feature),
            patch.object(AsBuiltLayerService, "_resolve_first_field_name", return_value="added_by"),
            patch.object(AsBuiltLayerService, "_set_attr_if_present"),
            patch.object(AsBuiltLayerService, "_apply_geometry_form_values"),
            patch.object(AsBuiltLayerService, "current_username", return_value="kasutaja"),
        ):
            result = AsBuiltLayerService.attach_backend_item_to_feature(
                layer=layer, feature_id=3, item_id="job-1", item_data={"name": "Tood"}
            )

        self.assertEqual(result, (False, "Could not update selected As-built feature"))
        self.assertEqual(self.events(), ["asbuilt_added_fields_set_failed"])
        self.assertEqual(self.log.call_args.kwargs["extra"], {"item_id": "job-1"})

    def test_coerce_keeps_the_raw_value_for_numbers_it_cannot_convert(self) -> None:
        field = QgsField("state", QVariant.Int)
        for raw in ("abc", None, float("inf")):
            with self.subTest(raw=raw):
                self.assertEqual(AsBuiltLayerService.coerce_value_for_field(field, raw), raw)
        self.log.assert_not_called()


class EasementLayerServiceLoggingTest(LoggedExceptionTestCase):
    def test_failed_rollback_is_logged_next_to_the_original_error(self) -> None:
        layer = _editing_layer(update_fields_error=RuntimeError("boom"))
        layer.dataProvider.return_value.addAttributes.return_value = True
        with patch.object(EasementLayerService, "_field_map", return_value={}):
            result = EasementLayerService._ensure_custom_fields(layer)

        self.assertEqual(result, (False, "boom"))
        self.assertEqual(
            self.events(),
            ["easement_layer_ensure_fields_rollback_failed", "easement_layer_ensure_fields_failed"],
        )
        self.assertEqual(self.modules(), {"easement"})

    def test_added_by_failure_is_logged_and_saving_goes_on(self) -> None:
        layer = MagicMock(spec=QgsVectorLayer)
        layer.isValid.return_value = True
        layer.isEditable.return_value = True
        layer.updateFeature.return_value = False
        feature = Mock()
        feature.attribute.side_effect = KeyError("Sisestaja")

        with (
            patch.object(EasementLayerService, "_ensure_custom_fields", return_value=(True, "")),
            patch.object(EasementLayerService, "_feature_by_id", return_value=feature),
            patch.object(EasementLayerService, "_resolve_first_field_name", return_value="Sisestaja"),
            patch.object(EasementLayerService, "_set_attr_if_present"),
            patch.object(EasementLayerService, "_set_mapped_status"),
            patch.object(EasementLayerService, "_apply_geometry_form_values"),
            patch.object(EasementLayerService, "current_username", return_value="kasutaja"),
        ):
            result = EasementLayerService.attach_backend_item_to_feature(
                layer=layer, feature_id=3, item_id="e-1", item_data={"number": "436-2"}
            )

        self.assertEqual(result, (False, "Could not update selected easement feature"))
        self.assertEqual(self.events(), ["easement_added_fields_set_failed"])
        self.assertEqual(self.log.call_args.kwargs["extra"], {"item_id": "e-1"})

    def test_missing_identity_field_on_the_feature_gives_an_empty_id(self) -> None:
        # QgsFeature.attribute(name) raises KeyError for a field the feature does not carry.
        id_field = EasementLayerService.FIELD_ID_CANDIDATES[0]
        layer = QgsVectorLayer(f"Polygon?crs=EPSG:3301&field={id_field}:string", "servituudid", "memory")
        self.assertTrue(layer.isValid())

        carrying = QgsFeature(layer.fields())
        carrying.setAttribute(id_field, " e-7 ")

        self.assertEqual(EasementLayerService.linked_backend_id_for_feature(layer, carrying), "e-7")
        self.assertEqual(EasementLayerService.linked_backend_id_for_feature(layer, QgsFeature()), "")
        self.log.assert_not_called()

    def test_coerce_keeps_the_raw_value_for_numbers_it_cannot_convert(self) -> None:
        for field_type in (QVariant.Int, QVariant.Double):
            field = QgsField("size", field_type)
            for raw in ("abc", float("inf") if field_type == QVariant.Int else "1,5 m"):
                with self.subTest(field_type=field_type, raw=raw):
                    self.assertEqual(EasementLayerService.coerce_value_for_field(field, raw), raw)
        self.log.assert_not_called()


class EasementPdfServiceLoggingTest(LoggedExceptionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.temp_dir = tempfile.TemporaryDirectory(prefix="kavitro_easement_exc_test_")
        self.addCleanup(self.temp_dir.cleanup)
        self.template = Path(self.temp_dir.name) / "template.qpt"
        self.template.write_text("<Layout/>", encoding="utf-8")

    def test_unreadable_template_is_logged_and_gives_no_layout(self) -> None:
        missing = Path(self.temp_dir.name) / "missing.qpt"

        self.assertIsNone(EasementPdfService._load_template_layout(object(), missing))
        self.assertEqual(self.events(), ["easement_pdf_template_read_failed"])
        self.assertEqual(self.modules(), {"easement"})

    def test_unparsable_template_is_logged_and_gives_no_layout(self) -> None:
        document = Mock()
        document.setContent.side_effect = TypeError("bad overload")
        with patch.object(pdf_module, "QDomDocument", return_value=document):
            self.assertIsNone(EasementPdfService._load_template_layout(object(), self.template))

        self.assertEqual(self.events(), ["easement_pdf_template_parse_failed"])

    def test_template_that_will_not_load_is_logged_and_gives_no_layout(self) -> None:
        layout = Mock()
        layout.loadFromTemplate.side_effect = ValueError("bad template")
        with patch.object(pdf_module, "QgsPrintLayout", return_value=layout):
            self.assertIsNone(EasementPdfService._load_template_layout(object(), self.template))

        self.assertEqual(self.events(), ["easement_pdf_template_load_failed"])

    def test_deleted_layer_gives_an_empty_feature_list_and_a_log_line(self) -> None:
        layer = Mock()
        layer.isValid.return_value = True
        layer.getFeatures.side_effect = RuntimeError("wrapped C/C++ object has been deleted")

        self.assertEqual(EasementPdfService._layer_features(layer, selected_only=False), [])
        self.assertEqual(self.events(), ["easement_pdf_layer_features_failed"])
        self.assertEqual(self.log.call_args.kwargs["extra"], {"selected_only": False})

    def test_property_label_skips_fields_the_feature_does_not_have(self) -> None:
        # feature[name] raises KeyError for an unknown field; the label is simply empty.
        self.assertEqual(EasementPdfService._property_label(QgsFeature()), "")
        self.log.assert_not_called()


class EasementPreviewDialogLoggingTest(LoggedExceptionTestCase):
    def test_property_summary_card_is_cleared_and_the_failure_logged(self) -> None:
        card = Mock()
        card.set_feature.side_effect = RuntimeError("card broke")
        host = SimpleNamespace(_property_summary_card=card, _first_property_feature=lambda: None)

        EasementPreviewDialog._refresh_property_summary_card(host)

        card.clear.assert_called_once_with()
        self.assertEqual(self.events(), ["easement_property_summary_refresh_failed"])
        self.assertEqual(self.modules(), {"easement"})

    def test_failed_selection_cancel_is_logged_and_the_orchestrator_dropped(self) -> None:
        orchestrator = Mock()
        orchestrator.cancel.side_effect = RuntimeError("cancel broke")
        host = SimpleNamespace(_property_selection_orchestrator=orchestrator)

        EasementPreviewDialog._finish_property_selection(host)

        self.assertIsNone(host._property_selection_orchestrator)
        self.assertEqual(self.events(), ["easement_property_selection_cancel_failed"])

    def test_one_failing_preview_layer_does_not_stop_the_cleanup(self) -> None:
        def remove_existing(name, only_memory=False):
            if name == "first":
                raise RuntimeError("project busy")
            return 1

        with patch.object(preview_module.MemoryLayerResultService, "remove_existing", side_effect=remove_existing) as remove:
            EasementPreviewDialog._cleanup_named_layers(SimpleNamespace(), ["first", "", "second"])

        self.assertEqual([call.args[0] for call in remove.call_args_list], ["first", "second"])
        self.assertEqual(self.events(), ["easement_named_layers_cleanup_failed"])
        self.assertEqual(self.log.call_args.kwargs["extra"], {"layer_name": "first"})

    def test_failed_pdf_cleanup_is_logged_and_the_path_forgotten(self) -> None:
        host = SimpleNamespace(_generated_pdf_path="C:/temp/x.pdf")
        with patch.object(
            preview_module.EasementPdfService, "cleanup_output_pdf", side_effect=RuntimeError("symlink loop")
        ):
            EasementPreviewDialog._cleanup_generated_pdf(host)

        self.assertEqual(host._generated_pdf_path, "")
        self.assertEqual(self.events(), ["easement_pdf_cleanup_failed"])

    def test_numbers_too_large_for_float_fall_back_instead_of_raising(self) -> None:
        huge = 10**400
        self.assertIsNone(EasementPreviewDialog._coerce_number(huge))
        self.assertEqual(EasementPreviewDialog._format_distance(huge), str(huge))
        self.assertEqual(EasementPreviewDialog._format_area_display(SimpleNamespace(), huge), "0.00 m²")
        self.log.assert_not_called()

    def test_property_label_ignores_fields_the_feature_does_not_have(self) -> None:
        self.assertEqual(EasementPreviewDialog._format_property_label(SimpleNamespace(), "12345", QgsFeature()), "12345")
        self.log.assert_not_called()


if __name__ == "__main__":
    unittest.main()
