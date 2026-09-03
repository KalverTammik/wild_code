from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path
from unittest.mock import Mock, patch


os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
qgis_prefix = str(os.environ.get("QGIS_PREFIX_PATH") or "").strip()
if qgis_prefix:
    qgis_plugins_path = str(Path(qgis_prefix) / "python" / "plugins")
    if qgis_plugins_path not in sys.path:
        sys.path.append(qgis_plugins_path)

from PyQt5.QtWidgets import QApplication

from Kavitro_dev.constants.module_icons import IconNames
from Kavitro_dev.utils.Folders.foldersHelpers import FolderHelpers
from Kavitro_dev.widgets.DataDisplayWidgets import module_action_buttons
from Kavitro_dev.widgets.DataDisplayWidgets.ModuleConnectionActions import (
    ModuleConnectionActions,
)
from Kavitro_dev.widgets.DataDisplayWidgets.module_action_buttons import (
    MoreActionsButton,
    OpenFolderActionButton,
    ShowOnMapActionButton,
)


class StubLanguageManager:
    @staticmethod
    def translate(key) -> str:
        return str(getattr(key, "value", key) or "")


class ProjectCardFilesPathRefreshTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._app = QApplication.instance() or QApplication([])

    def test_folder_button_uses_latest_path_without_reconnection(self) -> None:
        button = OpenFolderActionButton(None, None)
        self.assertFalse(button.isEnabled())

        with patch.object(FolderHelpers, "open_item_folder") as open_folder:
            button.set_file_path(r"C:\Projects\First")
            self.assertTrue(button.isEnabled())
            button.click()

            button.set_file_path(r"C:\Projects\Second")
            button.click()

        self.assertEqual(
            [call.args[0] for call in open_folder.call_args_list],
            [r"C:\Projects\First", r"C:\Projects\Second"],
        )

    def test_more_actions_callback_updates_only_its_own_folder_button(self) -> None:
        lang_manager = StubLanguageManager()
        first_actions = ModuleConnectionActions(
            "project",
            "project-1",
            {"id": "project-1", "filesPath": ""},
            lang_manager,
        )
        second_actions = ModuleConnectionActions(
            "project",
            "project-2",
            {"id": "project-2", "filesPath": r"C:\Projects\Other"},
            lang_manager,
        )

        first_more = next(
            button for button in first_actions.buttons if isinstance(button, MoreActionsButton)
        )
        first_folder = next(
            button for button in first_actions.buttons if isinstance(button, OpenFolderActionButton)
        )
        second_folder = next(
            button for button in second_actions.buttons if isinstance(button, OpenFolderActionButton)
        )

        first_more._handle_files_path_updated(r"C:\Projects\Project-1")

        self.assertTrue(first_folder.isEnabled())
        self.assertEqual(first_folder.file_path, r"C:\Projects\Project-1")
        self.assertEqual(second_folder.file_path, r"C:\Projects\Other")

    def test_empty_map_action_starts_shared_property_linking_workflow(self) -> None:
        lang_manager = StubLanguageManager()
        start_linking = Mock()
        button = ShowOnMapActionButton(
            "project",
            "project-1",
            lang_manager,
            has_connections=0,
        )
        button.set_link_properties_callback(start_linking)

        with patch.object(module_action_buttons, "show_items_on_map") as show_on_map:
            button.click()

        self.assertTrue(button.isEnabled())
        self.assertEqual(button.connection_mode, ShowOnMapActionButton.LINK_MODE)
        self.assertEqual(button._icon_name, IconNames.ICON_CONNECT_PROPERTIES)
        self.assertEqual(
            button.toolTip(),
            "No linked properties - connect properties",
        )
        self.assertEqual(button.accessibleName(), button.toolTip())
        start_linking.assert_called_once_with()
        show_on_map.assert_not_called()

    def test_connected_map_action_shows_items_instead_of_starting_linking(self) -> None:
        lang_manager = StubLanguageManager()
        start_linking = Mock()
        button = ShowOnMapActionButton(
            "project",
            "project-1",
            lang_manager,
            has_connections=1,
        )
        button.set_link_properties_callback(start_linking)

        with patch.object(module_action_buttons, "show_items_on_map") as show_on_map:
            button.click()

        self.assertEqual(button.connection_mode, ShowOnMapActionButton.SHOW_MODE)
        self.assertEqual(button._icon_name, IconNames.ICON_SHOW_ON_MAP)
        self.assertEqual(
            button.toolTip(),
            "Show connected properties on map",
        )
        self.assertEqual(button.accessibleName(), button.toolTip())
        show_on_map.assert_called_once_with("project", "project-1", lang_manager)
        start_linking.assert_not_called()

    def test_successful_link_callback_switches_only_the_current_card_to_map_mode(self) -> None:
        lang_manager = StubLanguageManager()
        first_actions = ModuleConnectionActions(
            "project",
            "project-1",
            {"id": "project-1", "properties": {"pageInfo": {"count": 0}}},
            lang_manager,
        )
        second_actions = ModuleConnectionActions(
            "project",
            "project-2",
            {"id": "project-2", "properties": {"pageInfo": {"count": 0}}},
            lang_manager,
        )

        first_map = next(
            button for button in first_actions.buttons if isinstance(button, ShowOnMapActionButton)
        )
        second_map = next(
            button for button in second_actions.buttons if isinstance(button, ShowOnMapActionButton)
        )
        self.assertEqual(first_map.connection_mode, ShowOnMapActionButton.LINK_MODE)
        self.assertEqual(second_map.connection_mode, ShowOnMapActionButton.LINK_MODE)

        first_actions._more_actions_button._on_properties_linked(["78401:101:0001"])

        self.assertEqual(first_map.connection_mode, ShowOnMapActionButton.SHOW_MODE)
        self.assertEqual(second_map.connection_mode, ShowOnMapActionButton.LINK_MODE)


if __name__ == "__main__":
    unittest.main()
