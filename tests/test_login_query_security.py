from __future__ import annotations

import importlib
import os
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch


os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
PLUGIN_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLUGIN_ROOT.parent))

from PyQt5.QtWidgets import QApplication


login_dialog_module = importlib.import_module("Kavitro_dev.login_dialog")
api_client_module = importlib.import_module("Kavitro_dev.python.api_client")


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


class StubApiClient:
    def __init__(self) -> None:
        self.calls = []

    def send_query(self, query, variables=None, **kwargs):
        self.calls.append((query, variables, kwargs))
        return {
            "login": {
                "accessToken": "test-access-token",
                "refreshToken": "unused-refresh-token",
                "expiresIn": 3600,
            }
        }


class FakeResponse:
    status_code = 200
    text = ""

    @staticmethod
    def json():
        return {"data": {"login": {"accessToken": "test-access-token"}}}


class FakeHttpErrorResponse:
    status_code = 422
    text = 'secret-response-body={"accessToken":"must-not-be-persisted"}'


class LoginQuerySecurityTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._app = QApplication.instance() or QApplication([])

    def setUp(self) -> None:
        StubSessionManager.reset()

    def test_login_query_uses_typed_input_variable(self) -> None:
        query_path = (
            PLUGIN_ROOT
            / "python"
            / "queries"
            / "graphql"
            / "user"
            / "login.graphql"
        )
        query = query_path.read_text(encoding="utf-8")

        self.assertIn("mutation Login($input: LoginInput!)", query)
        self.assertIn("login(input: $input)", query)
        self.assertNotIn("username:", query)
        self.assertNotIn("password:", query)

    def test_login_dialog_keeps_credentials_out_of_query_document(self) -> None:
        username = 'user+"quoted"@example.com'
        password = 'Päss"word\\with\\slashes'
        api_client = StubApiClient()
        dialog = login_dialog_module.LoginDialog()
        dialog.username_input.setText(username)
        dialog.password_input.setText(password)

        with (
            patch.object(login_dialog_module, "SessionManager", StubSessionManager),
            patch.object(login_dialog_module, "APIClient", return_value=api_client),
            patch.object(dialog, "accept"),
        ):
            dialog.authenticate_user()

        self.assertEqual(len(api_client.calls), 1)
        query, variables, kwargs = api_client.calls[0]
        self.assertNotIn(username, query)
        self.assertNotIn(password, query)
        self.assertEqual(
            variables,
            {"input": {"username": username, "password": password}},
        )
        self.assertFalse(kwargs["require_auth"])
        self.assertEqual(kwargs["timeout"], 10)
        self.assertEqual(dialog.password_input.text(), "")

    def test_api_client_preserves_special_characters_in_json_variables(self) -> None:
        query = "mutation Login($input: LoginInput!) { login(input: $input) { accessToken } }"
        variables = {
            "input": {
                "username": 'kasutaja+"test"@example.com',
                "password": 'rida1\\rida2\nÕä"',
            }
        }
        client = api_client_module.APIClient(session_manager=object())

        with patch.object(
            api_client_module.requests,
            "post",
            return_value=FakeResponse(),
        ) as post:
            client.send_query(
                query,
                variables=variables,
                require_auth=False,
                timeout=10,
            )

        payload = post.call_args.kwargs["json"]
        headers = post.call_args.kwargs["headers"]
        self.assertEqual(payload["query"], query)
        self.assertEqual(payload["variables"], variables)
        self.assertNotIn(variables["input"]["password"], payload["query"])
        self.assertNotIn("Authorization", headers)

    def test_api_client_omits_http_error_body_from_result(self) -> None:
        client = api_client_module.APIClient(session_manager=object())

        with patch.object(
            api_client_module.requests,
            "post",
            return_value=FakeHttpErrorResponse(),
        ):
            result = client.send_query(
                "query Test { test }",
                require_auth=False,
                with_success=True,
            )

        self.assertFalse(result["success"])
        self.assertIn("HTTP 422", result["error"])
        self.assertNotIn(FakeHttpErrorResponse.text, result["error"])
        self.assertNotIn("accessToken", result["error"])

    def test_multipart_api_client_omits_http_error_body_from_exception(self) -> None:
        client = api_client_module.APIClient(session_manager=object())

        with TemporaryDirectory() as temp_dir:
            upload_path = Path(temp_dir) / "upload.txt"
            upload_path.write_text("test upload", encoding="utf-8")
            with patch.object(
                api_client_module.requests,
                "post",
                return_value=FakeHttpErrorResponse(),
            ):
                with self.assertRaises(Exception) as raised:
                    client.send_multipart_query(
                        "mutation Upload($file: Upload!) { upload(file: $file) { id } }",
                        variables={"file": None},
                        file_variables={"file": str(upload_path)},
                        require_auth=False,
                    )

        message = str(raised.exception)
        self.assertIn("HTTP 422", message)
        self.assertNotIn(FakeHttpErrorResponse.text, message)
        self.assertNotIn("accessToken", message)

    def test_login_dialog_source_has_no_interpolated_credentials(self) -> None:
        source = (PLUGIN_ROOT / "login_dialog.py").read_text(encoding="utf-8")

        self.assertNotIn("graphql = f", source)
        self.assertNotIn('password: "{password}"', source)
        self.assertIn('"login.graphql"', source)
        self.assertIn('"password": password', source)


if __name__ == "__main__":
    unittest.main()
