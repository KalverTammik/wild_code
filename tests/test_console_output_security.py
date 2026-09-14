from __future__ import annotations

import ast
import sys
import unittest
from pathlib import Path
from unittest.mock import Mock, patch


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLUGIN_ROOT.parent))

from Kavitro_dev.modules.Property.FlowControllers import UpdatePropertyData as update_module
from Kavitro_dev.modules.Property.FlowControllers.UpdatePropertyData import UpdatePropertyData
from Kavitro_dev.utils.Folders import foldersHelpers


class ConsoleOutputSecurityTest(unittest.TestCase):
    def test_property_update_success_does_not_print_graphql_responses(self) -> None:
        api_client = Mock()
        api_client.send_query.side_effect = [
            {"updateProperty": {"id": "property-1", "address": {"street": "Private street"}}},
            {"updatePropertyIntendedUses": {"id": "property-1"}},
        ]

        with (
            patch.object(update_module, "APIClient", return_value=api_client),
            patch.object(update_module.GraphQLQueryLoader, "load_query_by_module", return_value="mutation"),
            patch("builtins.print") as print_mock,
        ):
            result = UpdatePropertyData.update_single_property_item(
                "property-1",
                {"address": {"street": "Private street"}},
                ["residential"],
            )

        self.assertTrue(result)
        self.assertEqual(api_client.send_query.call_count, 2)
        print_mock.assert_not_called()

    def test_property_update_failure_uses_private_logger_instead_of_print(self) -> None:
        api_client = Mock()
        api_client.send_query.side_effect = RuntimeError("backend rejected update")

        with (
            patch.object(update_module, "APIClient", return_value=api_client),
            patch.object(update_module.GraphQLQueryLoader, "load_query_by_module", return_value="mutation"),
            patch.object(update_module.PythonFailLogger, "log_exception") as log_exception,
            patch("builtins.print") as print_mock,
        ):
            result = UpdatePropertyData.update_single_property_item(
                "property-1",
                {},
                [],
            )

        self.assertFalse(result)
        print_mock.assert_not_called()
        log_exception.assert_called_once()
        self.assertEqual(log_exception.call_args.kwargs["event"], "property_backend_update_failed")
        self.assertEqual(log_exception.call_args.kwargs["extra"],
                         {"item_id": "property-1", "stage": "updateProperty", "tunnus": None})

    def test_folder_name_generation_does_not_print_project_data(self) -> None:
        with (
            patch.object(
                foldersHelpers.SettingsService,
                "module_label_value",
                return_value="PROJECT_NAME + SYMBOL(_) + PROJECT_NUMBER",
            ),
            patch("builtins.print") as print_mock,
        ):
            result = foldersHelpers.FolderNameGenerator().folder_structure_name_order(
                "Private project",
                "PR-42",
            )

        self.assertEqual(result, "Private project_PR-42")
        print_mock.assert_not_called()

    def test_audited_runtime_paths_have_no_active_sensitive_print_calls(self) -> None:
        targets = {
            PLUGIN_ROOT / "modules" / "Property" / "FlowControllers" / "UpdatePropertyData.py": {
                "response",
                "input_id",
            },
            PLUGIN_ROOT / "utils" / "Folders" / "foldersHelpers.py": {
                "project_name",
                "project_number",
                "folder_name",
                "rule_raw",
            },
        }

        violations: list[str] = []
        for path, sensitive_names in targets.items():
            source = path.read_text(encoding="utf-8-sig")
            tree = ast.parse(source, filename=str(path))
            for node in ast.walk(tree):
                if not (
                    isinstance(node, ast.Call)
                    and isinstance(node.func, ast.Name)
                    and node.func.id == "print"
                ):
                    continue
                names = {
                    child.id
                    for child in ast.walk(node)
                    if isinstance(child, ast.Name)
                }
                if names & sensitive_names:
                    violations.append(f"{path.name}:{node.lineno}")

        self.assertEqual(violations, [])


if __name__ == "__main__":
    unittest.main()
