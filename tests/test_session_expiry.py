from __future__ import annotations

import importlib
import os
import sys
import threading
import unittest
from pathlib import Path
from unittest.mock import patch


os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
PLUGIN_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLUGIN_ROOT.parent))

from PyQt5.QtWidgets import QApplication

api_client_module = importlib.import_module("Kavitro_dev.python.api_client")
api_error_handling = importlib.import_module("Kavitro_dev.utils.api_error_handling")
login_dialog_module = importlib.import_module("Kavitro_dev.login_dialog")
session_module = importlib.import_module("Kavitro_dev.utils.SessionManager")
settings_ui_module = importlib.import_module("Kavitro_dev.modules.Settings.SettingsUI")

ApiErrorKind = api_error_handling.ApiErrorKind
SessionManager = session_module.SessionManager
tag_message = api_error_handling.tag_message


class FakeUnauthorizedResponse:
    status_code = 401
    headers: dict = {}
    text = ""

    @staticmethod
    def json():
        return {}


class RecordingSessionManager:
    """Stands in for SessionManager inside api_client during a send_query call."""

    def __init__(self, token: str = "live-token") -> None:
        self.invalidated_with: list = []
        self._token = token

    def get_token(self) -> str:
        return self._token

    def invalidate_session(self, reason=None) -> None:
        self.invalidated_with.append(reason)
        self._token = ""


class BackgroundThreadInvalidationTest(unittest.TestCase):
    """A 401 must end the session no matter which thread noticed it."""

    @classmethod
    def setUpClass(cls) -> None:
        cls._app = QApplication.instance() or QApplication([])

    def _send_unauthorized(self, *, on_worker_thread: bool):
        recorder = RecordingSessionManager()
        client = api_client_module.APIClient(session_manager=recorder)

        def fake_send(_send, **_kwargs):
            return FakeUnauthorizedResponse()

        with (
            patch.object(api_client_module, "send_api_request", fake_send),
            patch.object(api_client_module, "SessionManager", recorder),
        ):
            if not on_worker_thread:
                with self.assertRaises(Exception) as caught:
                    client.send_query("query Ping { ping }")
                return recorder, str(caught.exception)

            box: dict = {}

            def run() -> None:
                try:
                    client.send_query("query Ping { ping }")
                except Exception as exc:  # noqa: BLE001 - captured for the assertion
                    box["error"] = str(exc)

            worker = threading.Thread(target=run)
            worker.start()
            worker.join(timeout=10)
            self.assertFalse(worker.is_alive(), "send_query did not finish")
            return recorder, box.get("error", "")

    def test_main_thread_401_invalidates_session(self) -> None:
        recorder, message = self._send_unauthorized(on_worker_thread=False)

        self.assertEqual(
            recorder.invalidated_with,
            [session_module.SESSION_REASON_UNAUTHENTICATED],
        )
        self.assertEqual(api_error_handling.parse_tagged_message(message)[0], ApiErrorKind.AUTH)

    def test_worker_thread_401_also_invalidates_session(self) -> None:
        """Regression: the is_main_thread guard used to skip invalidation entirely."""
        recorder, message = self._send_unauthorized(on_worker_thread=True)

        self.assertEqual(
            recorder.invalidated_with,
            [session_module.SESSION_REASON_UNAUTHENTICATED],
        )
        self.assertEqual(api_error_handling.parse_tagged_message(message)[0], ApiErrorKind.AUTH)


class LoginPromptSuppressionTest(unittest.TestCase):
    """A cancelled prompt must never block the user's own next attempt."""

    def setUp(self) -> None:
        self._opened: list = []
        SessionManager._login_dialog_open = False
        SessionManager._login_cancelled_for_reason = None

    def tearDown(self) -> None:
        SessionManager._login_cancelled_for_reason = None

    def _request(self, reason, user_initiated=False) -> None:
        # QTimer.singleShot defers the dialog; run the callback straight away instead.
        with patch.object(session_module, "QTimer") as timer:
            timer.singleShot.side_effect = lambda _ms, fn: self._opened.append(reason)
            SessionManager.request_login(reason=reason, user_initiated=user_initiated)

    def test_automatic_prompt_is_silenced_after_cancel(self) -> None:
        SessionManager._login_cancelled_for_reason = "unauthenticated"

        self._request("unauthenticated")

        self.assertEqual(self._opened, [])

    def test_user_initiated_prompt_survives_cancel(self) -> None:
        SessionManager._login_cancelled_for_reason = "module_switch:property"

        self._request("module_switch:property", user_initiated=True)

        self.assertEqual(self._opened, ["module_switch:property"])


class LocalizedSessionErrorTest(unittest.TestCase):
    """Session detection must not depend on the language of the message."""

    def test_estonian_expiry_message_is_recognised(self) -> None:
        estonian = tag_message(
            ApiErrorKind.AUTH,
            "Teie seanss on aegunud. Palun logige uuesti sisse.",
        )

        self.assertTrue(settings_ui_module.SettingsModule._is_session_error_message(estonian))

    def test_network_failure_is_not_treated_as_expiry(self) -> None:
        network = tag_message(ApiErrorKind.NETWORK, "Ühendus katkes")

        self.assertFalse(settings_ui_module.SettingsModule._is_session_error_message(network))


class LoginErrorClassificationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._app = QApplication.instance() or QApplication([])

    def setUp(self) -> None:
        self.dialog = login_dialog_module.LoginDialog()
        self.addCleanup(self.dialog.deleteLater)

    def test_rejected_credentials_do_not_read_as_server_outage(self) -> None:
        """Regression: the client tags a 401 'Unauthenticated', which matched no marker."""
        error = Exception(tag_message(ApiErrorKind.AUTH, "Unauthenticated"))

        message, username_error, password_error = self.dialog._classify_login_error(error)

        self.assertTrue(username_error)
        self.assertTrue(password_error)
        self.assertNotEqual(
            message,
            self.dialog.lang.translate(
                login_dialog_module.TranslationKeys.LOGIN_SERVER_UNAVAILABLE
            ),
        )

    def test_network_failure_reads_as_server_unavailable(self) -> None:
        error = Exception(tag_message(ApiErrorKind.NETWORK, "Cannot resolve server name (DNS)"))

        message, username_error, password_error = self.dialog._classify_login_error(error)

        self.assertFalse(username_error)
        self.assertFalse(password_error)
        self.assertEqual(
            message,
            self.dialog.lang.translate(
                login_dialog_module.TranslationKeys.LOGIN_SERVER_UNAVAILABLE
            ),
        )


class LoginDialogLanguageTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._app = QApplication.instance() or QApplication([])

    def test_switching_language_retranslates_the_visible_labels(self) -> None:
        dialog = login_dialog_module.LoginDialog()
        self.addCleanup(dialog.deleteLater)
        estonian = dialog.username_label.text()

        dialog.change_language("en")

        self.assertNotEqual(dialog.username_label.text(), estonian)
        self.assertEqual(dialog.login_button.text(), dialog.lang.translate(
            login_dialog_module.TranslationKeys.LOGIN_BUTTON))

    def test_only_translated_languages_are_offered(self) -> None:
        dialog = login_dialog_module.LoginDialog()
        self.addCleanup(dialog.deleteLater)

        offered = [dialog.language_switch.itemText(i)
                   for i in range(dialog.language_switch.count())]

        self.assertEqual(offered, list(login_dialog_module.SUPPORTED_LANGUAGES))


if __name__ == "__main__":
    unittest.main()
