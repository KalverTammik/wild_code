"""A module that fails to open must tell the user, not only the switch log."""
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

from Kavitro_dev.languages import en, et
from Kavitro_dev.languages.language_manager import LanguageManager
from Kavitro_dev.languages.translation_keys import TranslationKeys
from Kavitro_dev.utils import moduleSwitchHelper as helper_module
from Kavitro_dev.utils.moduleSwitchHelper import ModuleSwitchHelper


class FakeModule:
    def __init__(self, widget=None):
        self._active_token = 1
        self._widget = object() if widget is None else widget

    def get_widget(self):
        return self._widget


class FakeModuleManager:
    def __init__(self, instances: dict, *, active: str, failing: str = ""):
        self.instances = instances
        self.active = active
        self.failing = failing

    def getActiveModuleName(self):
        return self.active

    def activateModule(self, name):
        # Like ModuleManager: the target is marked active before its activate() can fail.
        self.active = name
        if name == self.failing:
            raise RuntimeError(f"{name} failed to activate")

    def getActiveModuleInstance(self, name):
        return self.instances.get(name) if name == self.active else None


class FakeStack:
    def __init__(self, current):
        self.widgets = [current]
        self.current = current

    def currentWidget(self):
        return self.current

    def indexOf(self, widget):
        return self.widgets.index(widget) if widget in self.widgets else -1

    def addWidget(self, widget):
        self.widgets.append(widget)

    def setCurrentWidget(self, widget):
        self.current = widget

    def update(self):
        pass

    def repaint(self):
        pass


class ModuleSwitchFailureNoticeTest(unittest.TestCase):
    def setUp(self) -> None:
        self.home = FakeModule()
        self.works = FakeModule()
        self.manager = FakeModuleManager({"home": self.home, "works": self.works}, active="home")
        self.dialog = Mock(lang_manager=LanguageManager("et"))
        self.dialog.moduleStack = FakeStack(self.home.get_widget())
        self.switch_locked_during_notice = None

        def record_lock(*_args, **_kwargs):
            self.switch_locked_during_notice = ModuleSwitchHelper._is_switching
            return True

        self.show_warning = Mock(side_effect=record_lock)
        self.log = Mock()
        for patcher in (
            patch.multiple(
                ModuleSwitchHelper,
                _is_switching=False,
                _dialog_resolver=None,
                _confirm_unsaved_handler=None,
                _settings_focus_handler=None,
                _pending_login_listener=None,
            ),
            patch.object(helper_module, "ModuleManager", lambda: self.manager),
            patch.object(helper_module.SessionManager, "is_session_valid", return_value=True),
            patch.object(helper_module.SettingsSetupGuard, "is_ready", return_value=True),
            patch.object(helper_module.SwitchLogger, "log", self.log),
            patch.object(helper_module.ModernMessageDialog, "show_warning", self.show_warning),
            patch("traceback.print_exc"),
        ):
            patcher.start()
            self.addCleanup(patcher.stop)

    def logged_events(self) -> list:
        return [call.args[0] for call in self.log.call_args_list]

    def test_failed_activation_tells_the_user_which_module(self) -> None:
        self.manager.failing = "works"

        ModuleSwitchHelper.switch_module("WORKS", dialog=self.dialog)

        self.show_warning.assert_called_once()
        title, message = self.show_warning.call_args.args
        self.assertEqual(title, "Moodulit ei saanud avada")
        self.assertIn("Mooduli Tööd avamine ebaõnnestus", message)
        self.assertIn("Logs/SwitchLogs", message)
        self.assertIs(self.show_warning.call_args.kwargs.get("parent"), self.dialog)
        self.assertIn("switch_failed", self.logged_events(), "the log keeps its record")

    def test_previous_module_stays_open_behind_the_notice(self) -> None:
        self.manager.failing = "works"

        ModuleSwitchHelper.switch_module("WORKS", dialog=self.dialog)

        self.assertEqual(self.manager.active, "home")
        self.assertIs(self.dialog.moduleStack.currentWidget(), self.home.get_widget())

    def test_module_without_a_widget_is_a_failure_the_user_sees(self) -> None:
        self.works._widget = None

        ModuleSwitchHelper.switch_module("WORKS", dialog=self.dialog)

        self.show_warning.assert_called_once()

    def test_notice_waits_until_the_switch_lock_is_released(self) -> None:
        self.manager.failing = "works"

        ModuleSwitchHelper.switch_module("WORKS", dialog=self.dialog)

        self.assertIs(self.switch_locked_during_notice, False)
        self.assertFalse(ModuleSwitchHelper._is_switching)

    def test_successful_switch_shows_nothing(self) -> None:
        ModuleSwitchHelper.switch_module("WORKS", dialog=self.dialog)

        self.show_warning.assert_not_called()
        self.assertEqual(self.manager.active, "works")
        self.assertIs(self.dialog.moduleStack.currentWidget(), self.works.get_widget())

    def test_broken_notice_is_logged_and_does_not_escape(self) -> None:
        self.manager.failing = "works"
        self.show_warning.side_effect = RuntimeError("dialog failed")

        ModuleSwitchHelper.switch_module("WORKS", dialog=self.dialog)

        self.assertIn("switch_failed_notice_failed", self.logged_events())
        self.assertFalse(ModuleSwitchHelper._is_switching)


class ModuleSwitchFailureTextTest(unittest.TestCase):
    def test_both_languages_name_the_module(self) -> None:
        for name, translations in (("et", et.TRANSLATIONS), ("en", en.TRANSLATIONS)):
            with self.subTest(language=name):
                self.assertTrue(translations[TranslationKeys.MODULE_SWITCH_FAILED_TITLE])
                self.assertIn("{module}", translations[TranslationKeys.MODULE_SWITCH_FAILED_MESSAGE])


if __name__ == "__main__":
    unittest.main()
