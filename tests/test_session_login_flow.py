"""How a login is asked for, what its outcome does, and what the plugin window does around a session."""
from __future__ import annotations

import ast
import importlib
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
PLUGIN_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLUGIN_ROOT.parent))

from PyQt5.QtCore import QCoreApplication
from PyQt5.QtWidgets import QApplication, QDialog

from Kavitro_dev import main as main_module
from Kavitro_dev.Logs.python_fail_logger import PythonFailLogger
from Kavitro_dev.Logs.switch_logger import SwitchLogger
from Kavitro_dev.constants.settings_keys import SettingsService
from Kavitro_dev.languages.language_manager import LanguageManager
from Kavitro_dev.languages.translation_keys import TranslationKeys
from Kavitro_dev.ui.session_storage_warning import show_pending_storage_warning, show_storage_warning
from Kavitro_dev.ui.session_ui_controller import SessionUIController
from Kavitro_dev.utils.messagesHelper import ModernMessageDialog
from Kavitro_dev.utils.moduleSwitchHelper import ModuleSwitchHelper
from Kavitro_dev.utils.url_manager import Module

login_dialog_module = importlib.import_module("Kavitro_dev.login_dialog")
session_module = importlib.import_module("Kavitro_dev.utils.SessionManager")
session_ui_module = importlib.import_module("Kavitro_dev.ui.session_ui_controller")

SessionManager = session_module.SessionManager
# Where the login window class is looked up when a prompt opens.
DIALOG_HOME = session_ui_module


def install_login_prompt() -> None:
    """The plugin does this at startup."""
    SessionManager.set_login_prompt(SessionUIController.open_login_prompt)


def flush_events() -> None:
    for _ in range(3):
        QCoreApplication.processEvents()


class LoginPromptTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self) -> None:
        SessionManager._login_dialog_open = False
        SessionManager._login_cancelled_for_reason = None
        install_login_prompt()
        self.dialog_class = self.start(patch.object(DIALOG_HOME, "LoginDialog"))
        self.dialog = self.dialog_class.return_value
        self.dialog.exec_.return_value = 0
        self.session_valid = self.start(patch.object(SessionManager, "is_session_valid", return_value=False))
        self.log = self.start(patch.object(PythonFailLogger, "log"))
        self.log_exception = self.start(patch.object(PythonFailLogger, "log_exception"))
        self.addCleanup(self.reset_flags)

    def start(self, patcher):
        self.addCleanup(patcher.stop)
        return patcher.start()

    @staticmethod
    def reset_flags() -> None:
        SessionManager._login_dialog_open = False
        SessionManager._login_cancelled_for_reason = None
        SessionManager.set_login_prompt(None)

    def events(self) -> list:
        return [call.args[0] for call in self.log.call_args_list]

    def extra_of(self, event: str) -> dict:
        return next(call.kwargs["extra"] for call in self.log.call_args_list if call.args[0] == event)

    def test_window_opens_after_the_caller_has_returned(self) -> None:
        SessionManager.request_login(reason="startup")
        self.dialog_class.assert_not_called()
        flush_events()
        self.dialog_class.assert_called_once()
        self.dialog.exec_.assert_called_once_with()

    def test_without_a_registered_prompt_nothing_opens_and_it_is_logged(self) -> None:
        SessionManager.set_login_prompt(None)
        SessionManager.request_login(reason="startup", user_initiated=True)
        flush_events()
        self.dialog_class.assert_not_called()
        self.assertEqual(self.extra_of("login_prompt_unavailable"), {"reason": "startup"})
        self.assertFalse(SessionManager._login_dialog_open)

    def test_request_is_logged_with_its_reason(self) -> None:
        SessionManager.request_login(reason="startup")
        self.assertEqual(self.extra_of("login_dialog_requested"), {"reason": "startup"})
        flush_events()

    def test_given_parent_is_used(self) -> None:
        parent = object()
        SessionManager.request_login(parent=parent, reason="startup")
        flush_events()
        self.dialog_class.assert_called_once_with(parent=parent)

    def test_without_a_parent_the_qgis_window_is_used(self) -> None:
        interface = Mock()
        with patch("qgis.utils.iface", interface):
            SessionManager.request_login(reason="startup")
            flush_events()
        self.dialog_class.assert_called_once_with(parent=interface.mainWindow.return_value)

    def test_outside_qgis_the_active_window_is_used(self) -> None:
        active = object()
        with patch("qgis.utils.iface", None), patch.object(QApplication, "activeWindow", return_value=active):
            SessionManager.request_login(reason="startup")
            flush_events()
        self.dialog_class.assert_called_once_with(parent=active)

    def test_open_window_is_not_opened_twice(self) -> None:
        self.dialog.exec_.side_effect = lambda: SessionManager.request_login(reason="toinen", user_initiated=True) or 0
        SessionManager.request_login(reason="startup")
        flush_events()
        self.dialog_class.assert_called_once()

    def test_two_requests_before_opening_make_one_window(self) -> None:
        SessionManager.request_login(reason="startup")
        SessionManager.request_login(reason="startup")
        flush_events()
        self.dialog_class.assert_called_once()

    def test_window_can_be_opened_again_after_closing(self) -> None:
        SessionManager.request_login(reason="startup", user_initiated=True)
        flush_events()
        SessionManager.request_login(reason="startup", user_initiated=True)
        flush_events()
        self.assertEqual(self.dialog_class.call_count, 2)

    def test_successful_login_tells_the_listeners_afterwards(self) -> None:
        listener = Mock()
        SessionManager.register_listener(listener)
        self.addCleanup(SessionManager.unregister_listener, listener)
        self.session_valid.return_value = True
        self.dialog.exec_.return_value = 1
        SessionManager.request_login(reason="startup")
        flush_events()
        listener.assert_called_once_with()
        self.assertEqual(self.extra_of("login_dialog_success"), {"reason": "startup"})

    def test_cancel_silences_only_automatic_retries_of_that_reason(self) -> None:
        SessionManager.request_login(reason="unauthenticated")
        flush_events()
        self.assertEqual(self.extra_of("login_dialog_cancelled"), {"reason": "unauthenticated"})

        SessionManager.request_login(reason="unauthenticated")
        flush_events()
        self.assertEqual(self.dialog_class.call_count, 1)

        SessionManager.request_login(reason="muu")
        flush_events()
        self.assertEqual(self.dialog_class.call_count, 2)

    def test_user_can_always_ask_again_after_cancelling(self) -> None:
        SessionManager.request_login(reason="unauthenticated")
        flush_events()
        SessionManager.request_login(reason="unauthenticated", user_initiated=True)
        flush_events()
        self.assertEqual(self.dialog_class.call_count, 2)

    def test_accepted_window_without_a_session_is_logged_and_not_silenced(self) -> None:
        self.dialog.exec_.return_value = 1
        SessionManager.request_login(reason="unauthenticated")
        flush_events()
        self.assertEqual(self.extra_of("login_dialog_no_session"), {"reason": "unauthenticated"})
        self.assertIsNone(SessionManager._login_cancelled_for_reason)

    def test_window_that_cannot_open_is_logged_and_can_be_tried_again(self) -> None:
        self.dialog_class.side_effect = RuntimeError("ei avane")
        SessionManager.request_login(reason="startup")
        flush_events()
        self.assertEqual(self.log_exception.call_args.kwargs["event"], "login_dialog_open_failed")
        self.dialog_class.side_effect = None
        SessionManager.request_login(reason="startup")
        flush_events()
        self.assertEqual(self.dialog_class.call_count, 2)


class SessionUIControllerTest(unittest.TestCase):
    def setUp(self) -> None:
        self.dialog = MagicMock()
        self.dialog._session_listener = None
        self.dialog._has_shown = False
        self.dialog._force_close = False
        self.dialog.moduleManager.modules = {"works": object()}
        self.dialog.moduleManager.getActiveModuleName.return_value = None
        self.session_valid = self.start(patch.object(SessionManager, "is_session_valid", return_value=True))
        self.request_login = self.start(patch.object(SessionManager, "request_login"))
        self.register = self.start(patch.object(SessionManager, "register_listener"))
        self.unregister = self.start(patch.object(SessionManager, "unregister_listener"))
        self.switch = self.start(patch.object(ModuleSwitchHelper, "switch_module"))
        self.preferred = self.start(patch.object(SettingsService, "preferred_module", return_value=""))
        self.start(patch.object(PythonFailLogger, "log"))

    def start(self, patcher):
        self.addCleanup(patcher.stop)
        return patcher.start()

    def test_logout_clears_the_session_and_closes_for_good(self) -> None:
        with patch.object(SessionManager, "clear") as clear:
            SessionUIController.logout(self.dialog)
        clear.assert_called_once_with()
        self.assertIs(self.dialog._force_close, True)
        self.dialog.close.assert_called_once_with()
        self.dialog.deleteLater.assert_called_once_with()

    def test_logout_survives_an_already_deleted_window(self) -> None:
        self.dialog.deleteLater.side_effect = RuntimeError("deleted")
        with patch.object(SessionManager, "clear"):
            SessionUIController.logout(self.dialog)

    def test_valid_session_shows_the_window(self) -> None:
        self.assertTrue(SessionUIController.ensure_logged_in(self.dialog))
        self.dialog.hide.assert_not_called()
        self.request_login.assert_not_called()

    def test_invalid_session_hides_the_window_and_asks_for_a_login(self) -> None:
        self.session_valid.return_value = False
        self.assertFalse(SessionUIController.ensure_logged_in(self.dialog))
        self.dialog.hide.assert_called_once_with()
        self.request_login.assert_called_once_with(reason="dialog_show", user_initiated=True)

    def test_session_gates_the_window_but_logout_stays_available(self) -> None:
        for valid in (True, False):
            with self.subTest(valid=valid):
                self.session_valid.return_value = valid
                SessionUIController.refresh_login_ui(self.dialog)
                self.dialog.sidebar.setEnabled.assert_called_with(valid)
                self.dialog.moduleStack.setEnabled.assert_called_with(valid)
                self.dialog.footer_widget.setEnabled.assert_called_with(valid)
                self.dialog.header_widget.logoutButton.setEnabled.assert_called_with(True)

    def test_session_change_refreshes_the_window(self) -> None:
        SessionUIController.handle_session_changed(self.dialog)
        self.dialog.sidebar.setEnabled.assert_called_once_with(True)
        self.dialog._refresh_session_dependent_ui.assert_called_once_with()

    def test_listener_is_registered_once_and_follows_the_session(self) -> None:
        SessionUIController.after_show(self.dialog)
        SessionUIController.after_show(self.dialog)
        self.register.assert_called_once()
        listener = self.register.call_args.args[0]
        self.assertIs(self.dialog._session_listener, listener)
        self.dialog._refresh_session_dependent_ui.reset_mock()
        listener()
        self.dialog._refresh_session_dependent_ui.assert_called_once_with()

    def test_closing_the_window_removes_its_listener(self) -> None:
        SessionUIController.after_show(self.dialog)
        listener = self.register.call_args.args[0]
        self.dialog.destroyed.connect.call_args.args[0]()
        self.unregister.assert_called_once_with(listener)

    def test_first_show_opens_the_preferred_module(self) -> None:
        self.preferred.return_value = "Works"
        SessionUIController.after_show(self.dialog)
        self.switch.assert_called_once_with("works", dialog=self.dialog)
        self.assertTrue(self.dialog._has_shown)

    def test_first_show_without_a_known_preference_opens_home(self) -> None:
        for preferred in ("", "Tundmatu"):
            with self.subTest(preferred=preferred):
                self.switch.reset_mock()
                self.dialog._has_shown = False
                self.preferred.return_value = preferred
                SessionUIController.after_show(self.dialog)
                self.switch.assert_called_once_with(Module.HOME.name, dialog=self.dialog)

    def test_later_show_returns_to_the_active_module(self) -> None:
        self.dialog._has_shown = True
        self.dialog.moduleManager.getActiveModuleName.return_value = "works"
        widget = self.dialog.moduleManager.getActiveModuleInstance.return_value.get_widget.return_value
        SessionUIController.after_show(self.dialog)
        self.dialog.moduleManager.getActiveModuleInstance.assert_called_once_with("works")
        self.dialog.moduleStack.setCurrentWidget.assert_called_once_with(widget)
        self.dialog.sidebar.setActiveModuleOnSidebarButton.assert_called_once_with("works")
        self.switch.assert_not_called()

    def test_failed_restore_is_logged_without_a_module_switch(self) -> None:
        self.dialog._has_shown = True
        self.dialog.moduleManager.getActiveModuleName.return_value = "works"
        self.dialog.moduleManager.getActiveModuleInstance.return_value.get_widget.side_effect = RuntimeError("deleted")
        with patch.object(SwitchLogger, "log") as log:
            SessionUIController.after_show(self.dialog)
        self.assertEqual(log.call_args.args[0], "dialog_restore_widget_failed")
        self.switch.assert_not_called()

    def test_later_show_without_an_active_module_opens_one(self) -> None:
        self.dialog._has_shown = True
        SessionUIController.after_show(self.dialog)
        self.switch.assert_called_once_with(Module.HOME.name, dialog=self.dialog)


class StorageWarningTest(unittest.TestCase):
    MESSAGES = {
        session_module.SESSION_STORAGE_MEMORY_ONLY: TranslationKeys.SESSION_STORAGE_MEMORY_ONLY,
        session_module.SESSION_STORAGE_MIGRATION_PENDING: TranslationKeys.SESSION_STORAGE_MIGRATION_PENDING,
        session_module.SESSION_STORAGE_CLEANUP_FAILED: TranslationKeys.SESSION_STORAGE_CLEANUP_FAILED,
    }

    def setUp(self) -> None:
        self.lang = LanguageManager("en")
        patcher = patch.object(ModernMessageDialog, "show_warning")
        self.addCleanup(patcher.stop)
        self.warning = patcher.start()
        self.addCleanup(setattr, SessionManager, "_storage_warning_pending", None)

    def test_each_problem_has_its_own_message(self) -> None:
        parent = object()
        for status, key in self.MESSAGES.items():
            with self.subTest(status=status):
                self.warning.reset_mock()
                show_storage_warning(status, parent=parent, lang_manager=self.lang)
                self.warning.assert_called_once_with(
                    self.lang.translate(TranslationKeys.SESSION_STORAGE_WARNING_TITLE),
                    self.lang.translate(key),
                    parent=parent,
                )

    def test_healthy_storage_shows_nothing(self) -> None:
        for status in (session_module.SESSION_STORAGE_PERSISTENT, "", "login_required"):
            with self.subTest(status=status):
                show_storage_warning(status, lang_manager=self.lang)
                self.warning.assert_not_called()

    def test_default_language_is_used_when_none_is_given(self) -> None:
        show_storage_warning(session_module.SESSION_STORAGE_MEMORY_ONLY)
        self.assertEqual(self.warning.call_args.args[1],
                         LanguageManager().translate(TranslationKeys.SESSION_STORAGE_MEMORY_ONLY))

    def test_pending_warning_is_shown_once(self) -> None:
        SessionManager._storage_warning_pending = session_module.SESSION_STORAGE_CLEANUP_FAILED
        show_pending_storage_warning(lang_manager=self.lang)
        show_pending_storage_warning(lang_manager=self.lang)
        self.warning.assert_called_once()
        self.assertIsNone(SessionManager._storage_warning_pending)

    def test_nothing_pending_shows_nothing(self) -> None:
        SessionManager._storage_warning_pending = None
        show_pending_storage_warning(lang_manager=self.lang)
        self.warning.assert_not_called()


class FinishedLoginWarningTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def test_login_reports_a_storage_problem_over_its_own_window(self) -> None:
        window = login_dialog_module.LoginDialog()
        self.addCleanup(window.deleteLater)
        status = session_module.SESSION_STORAGE_MEMORY_ONLY
        with patch.object(login_dialog_module.SessionManager, "setSession", return_value=status), patch.object(
            ModernMessageDialog, "show_warning"
        ) as warning, patch.object(QDialog, "accept"):
            window._finish_login("mari", "token")
        warning.assert_called_once()
        self.assertIs(warning.call_args.kwargs["parent"], window)
        self.assertEqual(warning.call_args.args[1], window.lang.translate(TranslationKeys.SESSION_STORAGE_MEMORY_ONLY))


class SessionLayeringTest(unittest.TestCase):
    FORBIDDEN = ("login_dialog", "dialog", "ui", "widgets", "messagesHelper", "moduleSwitchHelper")

    def imported_by(self, relative: str) -> list:
        tree = ast.parse((PLUGIN_ROOT / relative).read_text(encoding="utf-8"))
        return [node.module.split(".") for node in ast.walk(tree)
                if isinstance(node, ast.ImportFrom) and node.level and node.module]

    def test_session_state_and_the_api_client_know_no_windows(self) -> None:
        for relative in ("utils/SessionManager.py", "python/api_client.py"):
            with self.subTest(file=relative):
                touched = [".".join(parts) for parts in self.imported_by(relative) if set(parts) & set(self.FORBIDDEN)]
                self.assertEqual(touched, [])


class PluginWiringTest(unittest.TestCase):
    def setUp(self) -> None:
        self.addCleanup(SessionManager.set_login_prompt, None)

    def test_plugin_registers_the_login_prompt_and_removes_it_on_unload(self) -> None:
        plugin = main_module.WildCodePlugin(Mock())
        plugin._crash_logger = Mock()
        with patch.object(main_module, "QAction"), patch.object(main_module.PluginDialog, "get_instance", return_value=None):
            plugin.initGui()
            self.assertEqual(SessionManager._login_prompt, SessionUIController.open_login_prompt)
            plugin.unload()
        self.assertIsNone(SessionManager._login_prompt)


if __name__ == "__main__":
    unittest.main()
