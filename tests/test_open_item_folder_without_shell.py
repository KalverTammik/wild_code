"""The card's folder button opens Kavitro's path without a shell.

Found 2026-11-23: FolderHelpers.open_item_folder ran ``start``/``explorer`` with ``shell=True``, so
characters such as ``&`` in the path from Kavitro were read by cmd.exe as further commands.
"""
import inspect
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
if os.environ.get("QGIS_PREFIX_PATH"):
    sys.path.append(str(Path(os.environ["QGIS_PREFIX_PATH"]) / "python" / "plugins"))

from qgis.core import QgsApplication
from qgis.PyQt.QtCore import QUrl

from Kavitro_dev.utils.Folders import foldersHelpers as helpers_module
from Kavitro_dev.utils.Folders.foldersHelpers import FolderHelpers
from Kavitro_dev.widgets.DataDisplayWidgets import module_action_buttons as buttons_module

_APP = QgsApplication.instance() or QgsApplication([], False)


class OpenItemFolderTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        opener = patch.object(helpers_module.QDesktopServices, "openUrl", return_value=True)
        self.open_url = opener.start()
        self.addCleanup(opener.stop)
        logger = patch.object(helpers_module, "PythonFailLogger")
        logger.start()
        self.addCleanup(logger.stop)

    def folder(self, name):
        path = os.path.join(self.tmp.name, name)
        os.makedirs(path)
        return path

    def test_a_folder_with_shell_characters_opens_as_one_path(self):
        path = self.folder("Projekt & Co (2026) ^x % !y")
        self.assertEqual(FolderHelpers.open_item_folder(path), FolderHelpers.FOLDER_OPENED)
        self.open_url.assert_called_once_with(QUrl.fromLocalFile(os.path.normpath(path)))

    def test_a_command_glued_to_a_path_does_not_run(self):
        path = self.folder("kaust")
        self.assertEqual(FolderHelpers.open_item_folder(path + " & calc.exe"), FolderHelpers.FOLDER_NOT_FOUND)
        self.open_url.assert_not_called()

    def test_a_known_document_opens_in_its_program(self):
        for name in ("Leping & lisa (1).pdf", "joonis.dwg", "tabel.XLSX"):
            with self.subTest(name=name):
                self.open_url.reset_mock()
                path = os.path.join(self.tmp.name, name)
                Path(path).write_bytes(b"")
                self.assertEqual(FolderHelpers.open_item_folder(path), FolderHelpers.FOLDER_OPENED)
                self.open_url.assert_called_once_with(QUrl.fromLocalFile(os.path.normpath(path)))

    def test_a_program_or_script_is_not_run(self):
        for name in ("tool.exe", "run.bat", "x.ps1", "a.cmd", "b.vbs", "c.lnk", "ilma_laiendita"):
            with self.subTest(name=name):
                path = os.path.join(self.tmp.name, name)
                Path(path).write_bytes(b"")
                self.assertEqual(FolderHelpers.open_item_folder(path), FolderHelpers.FOLDER_BLOCKED)
        self.open_url.assert_not_called()

    def test_a_missing_document_is_reported_as_not_found(self):
        path = os.path.join(self.tmp.name, "puudub.pdf")
        self.assertEqual(FolderHelpers.open_item_folder(path), FolderHelpers.FOLDER_NOT_FOUND)
        self.open_url.assert_not_called()

    def test_other_schemes_device_paths_and_control_characters_are_blocked(self):
        for value in ("javascript:alert(1)", "cmd:/c calc", r"\\?\C:\Windows", "C:\\a\nb", "relative\\path"):
            with self.subTest(value=value):
                self.assertEqual(FolderHelpers.open_item_folder(value), FolderHelpers.FOLDER_BLOCKED)
        self.open_url.assert_not_called()

    def test_a_web_address_opens_in_the_browser(self):
        url = "https://kavitro.com/files/a?b=1&c=2"
        self.assertEqual(FolderHelpers.open_item_folder(url), FolderHelpers.FOLDER_OPENED)
        self.assertEqual(self.open_url.call_args.args[0].toString(), url)

    def test_a_failed_open_is_reported(self):
        self.open_url.return_value = False
        self.assertEqual(FolderHelpers.open_item_folder(self.folder("x")), FolderHelpers.FOLDER_OPEN_FAILED)

    def test_no_shell_is_used(self):
        source = inspect.getsource(helpers_module)
        self.assertNotIn("import subprocess", source)
        self.assertNotIn("Popen(", source)
        self.assertNotIn("os.system(", source)


class FolderButtonMessageTest(unittest.TestCase):
    def test_the_button_names_what_went_wrong(self):
        lang = Mock(translate=lambda key: f"<{key}>" + (" {target}" if "link" in str(key) else ""))
        button = buttons_module.OpenFolderActionButton("X:\\puudub", lang)
        self.addCleanup(button.deleteLater)
        with patch.object(buttons_module.FolderHelpers, "open_item_folder",
                          return_value=FolderHelpers.FOLDER_NOT_FOUND), \
                patch.object(buttons_module, "ModernMessageDialog") as dialogs:
            button.click()
        dialogs.show_warning.assert_called_once()
        self.assertIn("X:\\puudub", dialogs.show_warning.call_args.args[1])

        with patch.object(buttons_module.FolderHelpers, "open_item_folder",
                          return_value=FolderHelpers.FOLDER_OPENED), \
                patch.object(buttons_module, "ModernMessageDialog") as dialogs:
            button.click()
        dialogs.show_warning.assert_not_called()


if __name__ == "__main__":
    unittest.main()
