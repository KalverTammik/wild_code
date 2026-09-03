from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch


sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from Kavitro_dev.utils.Folders import foldersHelpers
from Kavitro_dev.utils.url_manager import Module


class ExistingProjectFolderLinkFlowTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory(prefix="kavitro_existing_project_folder_")
        self.root = Path(self.temp_dir.name)
        self.source = self.root / "source"
        self.target = self.root / "target"
        self.destination = self.target / "Existing project"
        self.source.mkdir()
        self.target.mkdir()
        self.destination.mkdir()
        (self.source / "template-only.txt").write_text("template", encoding="utf-8")
        (self.destination / "existing-only.txt").write_text("existing", encoding="utf-8")

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def _run_flow(self, on_files_path_updated=None) -> None:
        foldersHelpers.FolderEngines.generate_project_folder_from_template(
            "project-42",
            "Existing project",
            "PR-42",
            str(self.source),
            str(self.target),
            on_files_path_updated=on_files_path_updated,
        )

    @patch.object(foldersHelpers.FolderNameGenerator, "folder_structure_name_order", return_value="Existing project")
    @patch.object(foldersHelpers.ModernMessageDialog, "show_warning")
    @patch.object(foldersHelpers.ModernMessageDialog, "show_info")
    @patch.object(foldersHelpers.ModernMessageDialog, "ask_yes_no", return_value=True)
    @patch.object(foldersHelpers, "ModuleFilesPathUpdater")
    def test_existing_folder_can_be_linked_without_copying_or_modifying_contents(
        self,
        updater_class,
        ask_yes_no,
        show_info,
        show_warning,
        _folder_name,
    ) -> None:
        expected_path = str(self.destination.resolve())
        updater_class.return_value.update.return_value = {
            "id": "project-42",
            "filesPath": expected_path,
        }
        path_updated = Mock()

        self._run_flow(path_updated)

        updater_class.return_value.update.assert_called_once_with(
            Module.PROJECT,
            "project-42",
            expected_path,
        )
        self.assertTrue((self.destination / "existing-only.txt").is_file())
        self.assertFalse((self.destination / "template-only.txt").exists())
        self.assertEqual(ask_yes_no.call_args.kwargs["default"], ask_yes_no.call_args.kwargs["no_label"])
        self.assertIn("Lisa või uuenda", ask_yes_no.call_args.kwargs["yes_label"])
        path_updated.assert_called_once_with(expected_path)
        show_info.assert_called_once()
        show_warning.assert_not_called()

    @patch.object(foldersHelpers.FolderNameGenerator, "folder_structure_name_order", return_value="Existing project")
    @patch.object(foldersHelpers.ModernMessageDialog, "show_warning")
    @patch.object(foldersHelpers.ModernMessageDialog, "show_info")
    @patch.object(foldersHelpers.ModernMessageDialog, "ask_yes_no", return_value=False)
    @patch.object(foldersHelpers, "ModuleFilesPathUpdater")
    def test_default_no_leaves_existing_folder_and_project_link_unchanged(
        self,
        updater_class,
        ask_yes_no,
        show_info,
        show_warning,
        _folder_name,
    ) -> None:
        path_updated = Mock()

        self._run_flow(path_updated)

        updater_class.return_value.update.assert_not_called()
        self.assertTrue((self.destination / "existing-only.txt").is_file())
        self.assertFalse((self.destination / "template-only.txt").exists())
        self.assertEqual(ask_yes_no.call_args.kwargs["default"], ask_yes_no.call_args.kwargs["no_label"])
        path_updated.assert_not_called()
        show_info.assert_not_called()
        show_warning.assert_not_called()

    @patch.object(foldersHelpers.FolderNameGenerator, "folder_structure_name_order", return_value="Existing project")
    @patch.object(foldersHelpers.ModernMessageDialog, "show_warning")
    @patch.object(foldersHelpers.ModernMessageDialog, "show_info")
    @patch.object(foldersHelpers.ModernMessageDialog, "ask_yes_no", return_value=True)
    @patch.object(foldersHelpers, "ModuleFilesPathUpdater")
    def test_failed_link_update_does_not_refresh_the_card_button(
        self,
        updater_class,
        _ask_yes_no,
        show_info,
        show_warning,
        _folder_name,
    ) -> None:
        updater_class.return_value.update.side_effect = RuntimeError("API failure")
        path_updated = Mock()

        self._run_flow(path_updated)

        path_updated.assert_not_called()
        show_info.assert_not_called()
        show_warning.assert_called_once()

    @patch.object(foldersHelpers.FolderNameGenerator, "folder_structure_name_order", return_value="New project")
    @patch.object(foldersHelpers.ModernMessageDialog, "show_warning")
    @patch.object(foldersHelpers.ModernMessageDialog, "show_info")
    @patch.object(foldersHelpers.ModernMessageDialog, "ask_yes_no", side_effect=[True, True])
    @patch.object(foldersHelpers, "ModuleFilesPathUpdater")
    def test_new_folder_link_updates_only_the_requesting_card_callback(
        self,
        updater_class,
        ask_yes_no,
        show_info,
        show_warning,
        _folder_name,
    ) -> None:
        destination = self.target / "New project"
        expected_path = str(destination.resolve())
        updater_class.return_value.update.return_value = {
            "id": "project-42",
            "filesPath": expected_path,
        }
        path_updated = Mock()

        self._run_flow(path_updated)

        self.assertEqual(ask_yes_no.call_count, 2)
        updater_class.return_value.update.assert_called_once_with(
            Module.PROJECT,
            "project-42",
            expected_path,
        )
        path_updated.assert_called_once_with(expected_path)
        self.assertTrue((destination / "template-only.txt").is_file())
        show_info.assert_called_once()
        show_warning.assert_not_called()


if __name__ == "__main__":
    unittest.main()
