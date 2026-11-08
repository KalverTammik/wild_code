"""Contracts that replaced hasattr/getattr/setattr fallbacks: logout close flag, setup warning, label keys."""
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

from PyQt5.QtCore import QCoreApplication, QEvent
from PyQt5.QtWidgets import QApplication, QWidget

from Kavitro_dev.languages.language_manager import LanguageManager
from Kavitro_dev.languages.translation_keys import ToolbarTranslationKeys, TranslationKeys
from Kavitro_dev.modules.Settings.SettinsUtils.SettingsLogic import SettingsLogic
from Kavitro_dev.modules.Settings.setting_keys import SettingDialogPlaceholders
from Kavitro_dev.modules.Settings.settings_setup_guard import SettingsSetupGuard
from Kavitro_dev.utils import SessionManager as session_module
from Kavitro_dev.widgets.DataDisplayWidgets.module_action_buttons import MoreActionsButton


class LogoutClosesForGoodTest(unittest.TestCase):
    def test_close_flag_is_set_before_the_dialog_closes(self) -> None:
        dialog = Mock()
        seen = []
        dialog.close.side_effect = lambda: seen.append(dialog._force_close)

        with patch.object(session_module.SessionManager, "clear"), patch.object(session_module.PythonFailLogger, "log"):
            session_module.SessionUIController.logout(dialog)

        self.assertEqual(seen, [True], "closeEvent must see the flag, or close() only minimises")


class SetupWarningTextTest(unittest.TestCase):
    def test_warning_is_translated_and_names_the_module(self) -> None:
        lang = LanguageManager("et")

        title, message = SettingsSetupGuard.redirect_warning_text(lang, "WORKS")

        self.assertEqual(title, lang.translate(TranslationKeys.SETTINGS_SETUP_MISSING_TITLE))
        self.assertIn(lang.translate_module_name("works"), message)
        self.assertIn(lang.translate(TranslationKeys.SETTINGS_SETUP_MISSING_NOTE), message)


class MoreActionsWithoutLanguageTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def test_project_actions_build_with_the_default_language(self) -> None:
        host = QWidget()
        self.addCleanup(self._delete, host)

        button = MoreActionsButton(item_data={"id": "p1"}, module="project")
        button.setParent(host)

        self.assertEqual(button.toolTip(), LanguageManager().translate(ToolbarTranslationKeys.MORE_ACTIONS))

    @staticmethod
    def _delete(widget: QWidget) -> None:
        widget.hide()
        widget.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)


class ModuleLabelKeyTest(unittest.TestCase):
    def setUp(self) -> None:
        self.logic = SettingsLogic()
        self.logic._service = Mock()
        self.key = SettingDialogPlaceholders.PROJECTS_SOURCE_FOLDER

    def test_label_keys_are_plain_strings(self) -> None:
        self.assertIsInstance(self.key, str)

    def test_save_load_and_clear_pass_the_key_through(self) -> None:
        self.logic._service.module_label_value.return_value = "C:/projektid"

        self.logic.save_module_label_value("project", self.key, "C:/projektid")
        value = self.logic.load_module_label_value("project", self.key)
        self.logic.clear_module_label_value("project", self.key)

        self.assertEqual(value, "C:/projektid")
        calls = self.logic._service.module_label_value.call_args_list
        self.assertEqual(calls[0].args, ("project", self.key))
        self.assertEqual(calls[0].kwargs, {"value": "C:/projektid"})
        self.assertEqual(calls[1].args, ("project", self.key))
        self.assertEqual(calls[2].kwargs, {"clear": True})


if __name__ == "__main__":
    unittest.main()
