from __future__ import annotations

import importlib
import os
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import Mock, patch


os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
PLUGIN_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLUGIN_ROOT.parent))

from PyQt5.QtWidgets import QApplication


api_client_module = importlib.import_module("Kavitro_dev.python.api_client")
api_error_handling = importlib.import_module("Kavitro_dev.utils.api_error_handling")
login_dialog_module = importlib.import_module("Kavitro_dev.login_dialog")


class StubSessionManager:
    clear_calls = 0
    stored_sessions = []

    @classmethod
    def reset(cls) -> None:
        cls.clear_calls = 0
        cls.stored_sessions = []

    @classmethod
    def clear(cls) -> None:
        cls.clear_calls += 1

    def setSession(self, token, user, username=None) -> str:
        self.stored_sessions.append((token, user, username))
        return "persistent"

    @staticmethod
    def show_storage_warning(*_args, **_kwargs) -> None:
        return None


class ScriptedApiClient:
    def __init__(self, *responses) -> None:
        self.responses = list(responses)
        self.calls = []

    def send_query(self, query, variables=None, **kwargs):
        self.calls.append((query, variables, kwargs))
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response


class FakeGraphQLResponse:
    status_code = 200
    headers = {}

    def __init__(self, errors) -> None:
        self._errors = errors

    def json(self):
        return {"errors": self._errors}


class LoginMfaFlowTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._app = QApplication.instance() or QApplication([])

    def setUp(self) -> None:
        StubSessionManager.reset()
        self.dialog = login_dialog_module.LoginDialog()
        self.addCleanup(self.dialog.deleteLater)
        self.dialog.username_input.setText("person@example.com")
        self.dialog.password_input.setText("secret-password")

    def _patch_login(self, api_client):
        return (
            patch.object(login_dialog_module, "SessionManager", StubSessionManager),
            patch.object(login_dialog_module, "APIClient", return_value=api_client),
        )

    def test_challenge_then_recovery_code_finishes_login_without_leaking_secrets(self) -> None:
        api_client = ScriptedApiClient(
            {"login": {"accessToken": None}},
            {"login": {"accessToken": "mfa-access-token", "requiresMfa": False}},
        )
        session_patch, client_patch = self._patch_login(api_client)
        with session_patch, client_patch, patch.object(self.dialog, "accept") as accept:
            self.dialog.authenticate_user()

            self.assertEqual(self.dialog._step, "mfa")
            self.assertTrue(self.dialog.username_input.isReadOnly())
            self.assertTrue(self.dialog.password_input.isReadOnly())
            self.assertFalse(self.dialog.mfa_code_input.isHidden())
            self.assertTrue(self.dialog.errorLabel.isHidden())
            self.assertEqual(len(api_client.calls), 1)

            self.dialog.mfa_code_input.setText("12 3")
            self.dialog.verify_mfa_code()
            self.assertEqual(len(api_client.calls), 1)
            self.assertEqual(
                self.dialog.errorLabel.text(),
                self.dialog.lang.translate(login_dialog_module.TranslationKeys.MFA_CODE_FORMAT),
            )

            self.dialog.mfa_code_input.setText("ab 12 cd 34")
            self.dialog.verify_mfa_code()

        self.assertEqual(len(api_client.calls), 2)
        first_query, first_variables, first_kwargs = api_client.calls[0]
        second_query, second_variables, second_kwargs = api_client.calls[1]
        self.assertIn("mutation Login($input: LoginInput!)", first_query)
        self.assertNotIn("requiresMfa", first_query)
        self.assertEqual(
            first_variables,
            {"input": {"username": "person@example.com", "password": "secret-password"}},
        )
        self.assertEqual(
            second_variables,
            {
                "input": {
                    "username": "person@example.com",
                    "password": "secret-password",
                    "mfaCode": "AB12CD34",
                }
            },
        )
        self.assertIn("mutation LoginWithCode($input: LoginInput!)", second_query)
        self.assertNotIn("secret-password", second_query)
        self.assertNotIn("AB12CD34", second_query)
        for kwargs in (first_kwargs, second_kwargs):
            self.assertFalse(kwargs["require_auth"])
            self.assertFalse(kwargs["retry_network"])
            self.assertFalse(kwargs["retry_rate_limits"])
        self.assertEqual(StubSessionManager.clear_calls, 1)
        self.assertEqual(
            StubSessionManager.stored_sessions,
            [
                (
                    "mfa-access-token",
                    {"name": "person@example.com", "email": "person@example.com"},
                    "person@example.com",
                )
            ],
        )
        self.assertEqual(self.dialog.password_input.text(), "")
        self.assertEqual(self.dialog.mfa_code_input.text(), "")
        accept.assert_called_once()

    def test_wrong_code_clears_only_code_and_stays_on_mfa_step(self) -> None:
        api_client = ScriptedApiClient(
            {"login": {"accessToken": None}},
            {"login": {"accessToken": None, "requiresMfa": True}},
        )
        session_patch, client_patch = self._patch_login(api_client)
        with session_patch, client_patch:
            self.dialog.authenticate_user()
            self.dialog.mfa_code_input.setText("123456")
            self.dialog.verify_mfa_code()

        self.assertEqual(self.dialog._step, "mfa")
        self.assertEqual(self.dialog.mfa_code_input.text(), "")
        self.assertEqual(self.dialog.password_input.text(), "secret-password")
        self.assertEqual(self.dialog.mfa_code_input.property("validationState"), "error")
        self.assertEqual(
            self.dialog.errorLabel.text(),
            self.dialog.lang.translate(login_dialog_module.TranslationKeys.MFA_CODE_INVALID),
        )
        self.assertEqual(len(api_client.calls), 2)

    def test_credentials_error_on_verify_returns_to_password_step(self) -> None:
        error = Exception(
            api_error_handling.tag_message(api_error_handling.ApiErrorKind.AUTH, "Unauthenticated")
        )
        api_client = ScriptedApiClient(
            {"login": {"accessToken": None}},
            error,
        )
        session_patch, client_patch = self._patch_login(api_client)
        with session_patch, client_patch:
            self.dialog.authenticate_user()
            self.dialog.mfa_code_input.setText("123456")
            self.dialog.verify_mfa_code()

        self.assertEqual(self.dialog._step, "password")
        self.assertFalse(self.dialog.username_input.isReadOnly())
        self.assertFalse(self.dialog.password_input.isReadOnly())
        self.assertEqual(self.dialog.mfa_code_input.text(), "")
        self.assertEqual(self.dialog.username_input.property("validationState"), "error")
        self.assertEqual(self.dialog.password_input.property("validationState"), "error")

    def test_too_many_attempts_has_a_specific_message(self) -> None:
        message, username_error, password_error = self.dialog._classify_login_error(
            Exception(
                api_error_handling.tag_message(
                    api_error_handling.ApiErrorKind.GRAPHQL,
                    "Too many login attempts. Please try again in 42 seconds.",
                )
            )
        )

        self.assertEqual(
            message,
            self.dialog.lang.translate(
                login_dialog_module.TranslationKeys.LOGIN_TOO_MANY_ATTEMPTS
            ),
        )
        self.assertFalse(username_error)
        self.assertFalse(password_error)

    def test_back_and_close_restore_the_password_step(self) -> None:
        self.dialog._show_mfa_step()
        self.dialog.mfa_code_input.setText("123456")
        self.dialog.show_password_step()
        self.assertEqual(self.dialog._step, "password")
        self.assertEqual(self.dialog.mfa_code_input.text(), "")
        self.assertFalse(self.dialog.username_input.isReadOnly())

        self.dialog._show_mfa_step()
        with patch.object(login_dialog_module.QDialog, "reject"):
            self.dialog.reject()
        self.assertEqual(self.dialog._step, "password")


class MfaSetupRequiredTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._app = QApplication.instance() or QApplication([])

    @staticmethod
    def _errors():
        return [
            {"message": "Another error", "extensions": {"category": "OTHER"}},
            {
                "message": "Multi-factor authentication setup is required.",
                "extensions": {"category": "MFA_SETUP_REQUIRED"},
            },
        ]

    def test_regular_query_tags_setup_required_without_invalidating_session(self) -> None:
        client = api_client_module.APIClient(
            session_manager=Mock(get_token=Mock(return_value="valid-token"))
        )
        response = FakeGraphQLResponse(self._errors())
        with (
            patch.object(api_client_module, "send_api_request", return_value=response),
            patch.object(api_client_module.MfaSetupNotifier, "notify") as notify,
            patch.object(api_client_module.SessionManager, "invalidate_session") as invalidate,
            self.assertRaises(Exception) as raised,
        ):
            client.send_query("query Me { me { id } }")

        kind, _message = api_error_handling.parse_tagged_message(raised.exception)
        self.assertEqual(kind, api_error_handling.ApiErrorKind.MFA_SETUP_REQUIRED)
        notify.assert_called_once_with()
        invalidate.assert_not_called()

    def test_multipart_query_tags_setup_required_without_invalidating_session(self) -> None:
        client = api_client_module.APIClient(
            session_manager=Mock(get_token=Mock(return_value="valid-token"))
        )
        response = FakeGraphQLResponse(self._errors())
        with TemporaryDirectory() as directory:
            file_path = Path(directory) / "upload.txt"
            file_path.write_text("content", encoding="utf-8")
            with (
                patch.object(api_client_module, "send_api_request", return_value=response),
                patch.object(api_client_module.MfaSetupNotifier, "notify") as notify,
                patch.object(api_client_module.SessionManager, "invalidate_session") as invalidate,
                self.assertRaises(Exception) as raised,
            ):
                client.send_multipart_query(
                    "mutation Upload($file: Upload!) { upload(file: $file) { id } }",
                    variables={"file": None},
                    file_variables={"file": str(file_path)},
                )

        kind, _message = api_error_handling.parse_tagged_message(raised.exception)
        self.assertEqual(kind, api_error_handling.ApiErrorKind.MFA_SETUP_REQUIRED)
        notify.assert_called_once_with()
        invalidate.assert_not_called()

    def test_setup_notifier_deduplicates_repeated_errors(self) -> None:
        bridge = Mock()
        bridge.showRequested = Mock()
        with api_error_handling.DedupeNotifier._lock:
            api_error_handling.DedupeNotifier._last_shown_at.pop(
                api_error_handling.MfaSetupNotifier._dedupe_key,
                None,
            )
        with patch.object(
            api_error_handling.MfaSetupNotifier,
            "_get_bridge",
            return_value=bridge,
        ):
            self.assertTrue(api_error_handling.MfaSetupNotifier.notify())
            self.assertFalse(api_error_handling.MfaSetupNotifier.notify())

        bridge.showRequested.emit.assert_called_once_with()

    def test_setup_notice_action_opens_the_configured_web_app(self) -> None:
        messages_module = importlib.import_module("Kavitro_dev.utils.messagesHelper")
        url_module = importlib.import_module("Kavitro_dev.utils.url_manager")
        language_module = importlib.import_module("Kavitro_dev.languages.language_manager")
        keys_module = importlib.import_module("Kavitro_dev.languages.translation_keys")
        open_label = language_module.LanguageManager().translate(
            keys_module.TranslationKeys.MFA_OPEN_WEB_APP
        )
        bridge = api_error_handling._MfaSetupNotificationBridge()
        self.addCleanup(bridge.deleteLater)

        with (
            patch.object(
                messages_module.ModernMessageDialog,
                "ask_choice_modern",
                return_value=open_label,
            ),
            patch.object(url_module.loadWebpage, "open_webpage") as open_webpage,
        ):
            bridge._show_notification()

        open_webpage.assert_called_once_with(url_module.OpenLink().main)


if __name__ == "__main__":
    unittest.main()
