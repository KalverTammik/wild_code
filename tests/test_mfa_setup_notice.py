"""The MFA setup notice: the transport only decides when, the plugin registers how it looks.

The transport (`api_error_handling`) must not import dialogs, so the notice lives in
`ui/mfa_setup_notice.py` and the plugin registers it in `initGui` and clears it in `unload`.
"""
from __future__ import annotations

import ast
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
if os.environ.get("QGIS_PREFIX_PATH"):
    sys.path.append(str(Path(os.environ["QGIS_PREFIX_PATH"]) / "python" / "plugins"))

from qgis.core import QgsApplication

from Kavitro_dev import main as main_module
from Kavitro_dev.constants.module_icons import IconNames
from Kavitro_dev.languages.language_manager import LanguageManager
from Kavitro_dev.languages.translation_keys import TranslationKeys
from Kavitro_dev.ui import mfa_setup_notice
from Kavitro_dev.utils import api_error_handling
from Kavitro_dev.utils.api_error_handling import DedupeNotifier, MfaSetupNotifier
from Kavitro_dev.utils.messagesHelper import ModernMessageDialog
from Kavitro_dev.utils.url_manager import OpenLink, loadWebpage

API_ERROR_HANDLING = Path(api_error_handling.__file__)
DIALOG_METHODS = ("ask_choice_modern", "show_warning", "show_info", "ask_yes_no")


class MfaNoticeCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QgsApplication.instance() or QgsApplication([], False)

    def setUp(self) -> None:
        # A regression must never open a modal window.
        self.dialogs = {}
        for name in DIALOG_METHODS:
            patcher = patch.object(ModernMessageDialog, name)
            self.dialogs[name] = patcher.start()
            self.addCleanup(patcher.stop)
        self.addCleanup(MfaSetupNotifier.set_presenter, None)
        MfaSetupNotifier.set_presenter(None)

    def assert_no_dialog(self) -> None:
        for name, stub in self.dialogs.items():
            with self.subTest(dialog=name):
                stub.assert_not_called()


class BridgePresenterTest(MfaNoticeCase):
    def setUp(self) -> None:
        super().setUp()
        self.bridge = api_error_handling._MfaSetupNotificationBridge()
        self.addCleanup(self.bridge.deleteLater)

    def test_the_bridge_calls_the_registered_presenter_once(self) -> None:
        presenter = Mock()
        MfaSetupNotifier.set_presenter(presenter)

        self.bridge._show_notification()

        presenter.assert_called_once_with()
        self.assert_no_dialog()

    def test_a_failing_presenter_is_logged_with_the_notification_event(self) -> None:
        error = RuntimeError("presenter broke")
        MfaSetupNotifier.set_presenter(Mock(side_effect=error))

        with patch.object(api_error_handling.PythonFailLogger, "log_exception") as log_exception:
            self.bridge._show_notification()

        log_exception.assert_called_once_with(
            error,
            module=api_error_handling.PythonFailLogger.LOG_MODULE_UI,
            event=api_error_handling.PythonFailLogger.EVENT_MFA_NOTIFICATION_FAILED,
        )

    def test_without_a_presenter_it_is_logged_and_nothing_is_shown(self) -> None:
        with patch.object(api_error_handling.PythonFailLogger, "log") as log:
            self.bridge._show_notification()

        log.assert_called_once_with(
            "mfa_setup_notice_unavailable",
            module=api_error_handling.PythonFailLogger.LOG_MODULE_UI,
        )
        self.assert_no_dialog()

    def test_notify_reaches_the_presenter_once_per_dedupe_window(self) -> None:
        presenter = Mock()
        MfaSetupNotifier.set_presenter(presenter)
        with DedupeNotifier._lock:
            DedupeNotifier._last_shown_at.pop(MfaSetupNotifier._dedupe_key, None)
        self.addCleanup(DedupeNotifier._last_shown_at.pop, MfaSetupNotifier._dedupe_key, None)

        with patch.object(MfaSetupNotifier, "_get_bridge", return_value=self.bridge):
            self.assertTrue(MfaSetupNotifier.notify())
            self.assertFalse(MfaSetupNotifier.notify())

        presenter.assert_called_once_with()


class ShowMfaSetupNoticeTest(MfaNoticeCase):
    def setUp(self) -> None:
        super().setUp()
        lang = LanguageManager()
        self.open_label = lang.translate(TranslationKeys.MFA_OPEN_WEB_APP)
        self.close_label = lang.translate(TranslationKeys.OK)
        self.choice = self.dialogs["ask_choice_modern"]
        patcher = patch.object(loadWebpage, "open_webpage")
        self.open_webpage = patcher.start()
        self.addCleanup(patcher.stop)

    def test_it_asks_the_warning_choice_with_the_web_app_as_default(self) -> None:
        lang = LanguageManager()
        self.choice.return_value = self.close_label

        mfa_setup_notice.show_mfa_setup_notice()

        self.choice.assert_called_once_with(
            lang.translate(TranslationKeys.WARNING),
            lang.translate(TranslationKeys.MFA_SETUP_REQUIRED),
            buttons=[self.open_label, self.close_label],
            default=self.open_label,
            cancel=self.close_label,
            icon_name=IconNames.WARNING,
        )

    def test_choosing_open_opens_the_configured_web_app(self) -> None:
        self.choice.return_value = self.open_label

        mfa_setup_notice.show_mfa_setup_notice()

        self.open_webpage.assert_called_once_with(OpenLink().main)

    def test_choosing_ok_does_not_open_the_web_app(self) -> None:
        self.choice.return_value = self.close_label

        mfa_setup_notice.show_mfa_setup_notice()

        self.open_webpage.assert_not_called()

    def test_closing_the_dialog_does_not_open_the_web_app(self) -> None:
        self.choice.return_value = None

        mfa_setup_notice.show_mfa_setup_notice()

        self.open_webpage.assert_not_called()


class PluginRegistrationTest(MfaNoticeCase):
    def test_the_plugin_registers_the_presenter_at_start_and_removes_it_at_unload(self) -> None:
        plugin = main_module.WildCodePlugin(Mock())
        plugin._crash_logger = Mock()
        with patch.object(main_module, "QAction"):
            plugin.initGui()
        self.assertIs(MfaSetupNotifier._presenter, mfa_setup_notice.show_mfa_setup_notice)

        with patch.object(main_module.PluginDialog, "get_instance", return_value=None):
            plugin.unload()
        self.assertIsNone(MfaSetupNotifier._presenter)


class TransportImportsTest(unittest.TestCase):
    def test_the_transport_imports_no_message_dialog_even_inside_a_function(self) -> None:
        tree = ast.parse(API_ERROR_HANDLING.read_text(encoding="utf-8"))
        imported = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                imported.append(node.module or "")
                imported.extend(alias.name for alias in node.names)

        offenders = [name for name in imported if "messagesHelper" in name]
        self.assertEqual(offenders, [])


if __name__ == "__main__":
    unittest.main()
