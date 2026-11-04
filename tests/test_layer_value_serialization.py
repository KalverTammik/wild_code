from __future__ import annotations

import json
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
if os.environ.get("QGIS_PREFIX_PATH"):
    sys.path.append(str(Path(os.environ["QGIS_PREFIX_PATH"]) / "python" / "plugins"))

from qgis.PyQt.QtCore import QVariant
from qgis.PyQt.QtWidgets import QApplication

from Kavitro_dev.languages.language_manager import LanguageManager
from Kavitro_dev.modules.easements import easement_layer_service as easement_module
from Kavitro_dev.modules.projects import projects_layer_service as projects_module
from Kavitro_dev.modules.Settings import EasementStatusMappingDialog as mapping_dialog_module

EasementLayerService = easement_module.EasementLayerService
ProjectsLayerService = projects_module.ProjectsLayerService

MAPPING_ROWS = [{"statusId": "1", "statusName": "Aktiivne", "layerStatus": "A"}]
STORED_MAPPING = json.dumps(MAPPING_ROWS, ensure_ascii=False)


class EasementStatusMappingTest(unittest.TestCase):
    def test_stored_json_text_is_read_back(self) -> None:
        self.assertEqual(EasementLayerService.parse_status_mapping_rows(STORED_MAPPING), MAPPING_ROWS)

    def test_rows_wrapped_in_an_object_are_read_back(self) -> None:
        stored = json.dumps({"rows": MAPPING_ROWS})
        self.assertEqual(EasementLayerService.parse_status_mapping_rows(stored), MAPPING_ROWS)

    def test_backend_status_uses_the_stored_mapping(self) -> None:
        with patch.object(easement_module, "SettingsService") as settings:
            settings.return_value.module_label_value.return_value = STORED_MAPPING
            mapped = EasementLayerService.map_backend_status_to_layer_value({"id": "1", "name": "Aktiivne"})
            unmapped = EasementLayerService.map_backend_status_to_layer_value({"id": "2", "name": "Lõpetatud"})
        self.assertEqual(mapped, "A")
        self.assertEqual(unmapped, "Lõpetatud")

    def test_summary_shows_the_stored_mapping(self) -> None:
        self.assertIn("Aktiivne → A", EasementLayerService.format_status_mapping_summary(STORED_MAPPING))

    def test_corrupt_stored_text_is_logged_and_reads_as_empty(self) -> None:
        with patch.object(easement_module.PythonFailLogger, "log_exception") as log_exception:
            self.assertEqual(EasementLayerService.parse_status_mapping_rows("{not json"), [])
        log_exception.assert_called_once()

    def test_programming_errors_are_not_reported_as_an_empty_mapping(self) -> None:
        with patch.object(easement_module.json, "loads", side_effect=NameError("boom")):
            with self.assertRaises(NameError):
                EasementLayerService.parse_status_mapping_rows(STORED_MAPPING)


class EasementStatusMappingDialogTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._app = QApplication.instance() or QApplication([])

    def test_reopening_and_accepting_keeps_the_stored_mapping(self) -> None:
        statuses = [{"id": "1", "name": "Aktiivne"}, {"id": "2", "name": "Lõpetatud"}]
        service = mapping_dialog_module.EasementLayerService
        with (
            patch.object(mapping_dialog_module.APIModuleActions, "get_module_status_options", return_value=statuses),
            patch.object(service, "resolve_main_layer", return_value=None),
            patch.object(service, "resolve_status_field_name", return_value="staatus"),
            patch.object(service, "layer_status_value_options", return_value=["A", "B"]),
        ):
            dialog = mapping_dialog_module.EasementStatusMappingDialog(
                lang_manager=LanguageManager("et"),
                stored_value=STORED_MAPPING,
            )
        self.addCleanup(dialog.deleteLater)

        self.assertEqual(json.loads(dialog.serialized_mapping()), MAPPING_ROWS)


class ProjectFieldCoercionTest(unittest.TestCase):
    @staticmethod
    def _string_field() -> Mock:
        field = Mock()
        field.type.return_value = QVariant.String
        return field

    def test_dict_is_written_as_json(self) -> None:
        value = {"a": 1, "ä": "õ"}
        self.assertEqual(
            ProjectsLayerService.coerce_value_for_field(self._string_field(), value),
            '{"a": 1, "ä": "õ"}',
        )

    def test_list_is_written_as_json(self) -> None:
        self.assertEqual(ProjectsLayerService.coerce_value_for_field(self._string_field(), ["a", 1]), '["a", 1]')

    def test_value_json_cannot_represent_falls_back_to_text(self) -> None:
        value = {"unserializable": {1, 2}}
        self.assertEqual(ProjectsLayerService.coerce_value_for_field(self._string_field(), value), str(value))

    def test_programming_errors_are_not_hidden_by_the_text_fallback(self) -> None:
        with patch.object(projects_module.json, "dumps", side_effect=NameError("boom")):
            with self.assertRaises(NameError):
                ProjectsLayerService.coerce_value_for_field(self._string_field(), {"a": 1})


if __name__ == "__main__":
    unittest.main()
