"""What APIClient.send_query and send_multipart_query return or raise for each server answer.

Both methods must answer the same way; the error text is what workers carry to the UI,
so it is checked exactly.
"""
from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import requests
from qgis.core import QgsApplication

from Kavitro_dev.languages.translation_keys import TranslationKeys
from Kavitro_dev.python import api_client as api_client_module
from Kavitro_dev.python.api_rate_limit import ApiRateLimitError, RequestCancelled
from Kavitro_dev.utils.api_error_handling import ApiError, ApiErrorKind, parse_tagged_message
from Kavitro_dev.utils.SessionManager import SESSION_REASON_UNAUTHENTICATED


QUERY = "query Task { task(id: 1) { id } }"
MUTATION = "mutation Upload($input: UploadInput!) { upload(input: $input) { id } }"


class _Response:
    def __init__(self, status_code: int, body=None, headers: dict | None = None) -> None:
        self.status_code = status_code
        self._body = body
        self.headers = headers or {}
        self.text = "<html>secret page</html>"

    def json(self):
        if self._body is None:
            raise ValueError("not JSON")
        return self._body


class _Session:
    def __init__(self) -> None:
        self.invalidated_with: list = []

    def get_token(self) -> str:
        return "live-token"

    def invalidate_session(self, reason=None) -> None:
        self.invalidated_with.append(reason)


class _WorkerThread:
    """Stands in for QThread so the client believes it runs off the GUI thread."""

    @staticmethod
    def currentThread():
        return object()


class _ClientCase(unittest.TestCase):
    multipart = False

    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QgsApplication.instance() or QgsApplication([], False)

    def setUp(self) -> None:
        self.session = _Session()
        self.client = api_client_module.APIClient(session_manager=self.session)
        self.calls: list = []
        for target, name in (
            (api_client_module.PythonFailLogger, "log"),
            (api_client_module.MfaSetupNotifier, "notify"),
            (api_client_module.time, "sleep"),
        ):
            patcher = patch.object(target, name)
            setattr(self, f"mock_{name}", patcher.start())
            self.addCleanup(patcher.stop)
        session_patch = patch.object(api_client_module, "SessionManager", self.session)
        session_patch.start()
        self.addCleanup(session_patch.stop)

    def t(self, key) -> str:
        return self.client.lang.translate(key)

    def _answers(self, answers):
        answers = list(answers)

        def fake_send(send, **kwargs):
            self.calls.append(kwargs)
            answer = answers.pop(0) if len(answers) > 1 else answers[0]
            if isinstance(answer, BaseException):
                raise answer
            return answer

        return patch.object(api_client_module, "send_api_request", fake_send)

    def call(self, *answers, **kwargs):
        with self._answers(answers):
            if self.multipart:
                upload = tempfile.NamedTemporaryFile(suffix=".txt", delete=False)
                upload.write(b"x")
                upload.close()
                self.addCleanup(os.remove, upload.name)
                kwargs.pop("with_success", None)
                kwargs.pop("retry_network", None)
                return self.client.send_multipart_query(
                    MUTATION, {"input": {}}, file_variables={"input.file": upload.name}, **kwargs
                )
            return self.client.send_query(QUERY, **kwargs)

    def error_of(self, *answers, **kwargs) -> Exception:
        with self.assertRaises(Exception) as caught:
            self.call(*answers, **kwargs)
        return caught.exception

    def call_real_multipart(self) -> None:
        upload = tempfile.NamedTemporaryFile(suffix=".txt", delete=False)
        upload.write(b"x")
        upload.close()
        self.addCleanup(os.remove, upload.name)
        self.client.send_multipart_query(MUTATION, {"input": {}}, file_variables={"input.file": upload.name})


class ApiClientAnswersTest(_ClientCase):
    # --- success -------------------------------------------------------------

    def test_success_returns_data(self) -> None:
        self.assertEqual(self.call(_Response(200, {"data": {"task": {"id": "1"}}})), {"task": {"id": "1"}})

    def test_success_return_raw_returns_whole_body(self) -> None:
        body = {"data": {"task": None}, "extensions": {"cost": 1}}
        self.assertEqual(self.call(_Response(200, body), return_raw=True), body)

    # --- GraphQL errors ------------------------------------------------------

    def test_graphql_error_carries_the_first_server_message(self) -> None:
        body = {"errors": [{"message": 'Value "ORDINANCES" does not exist'}, {"message": "second"}]}
        error = self.error_of(_Response(200, body))
        self.assertEqual(str(error), '[WC-API][graphql] Value "ORDINANCES" does not exist')
        self.assertEqual(self.session.invalidated_with, [])

    def test_graphql_error_without_message_falls_back_to_its_text(self) -> None:
        error = self.error_of(_Response(200, {"errors": ["plain"]}))
        self.assertEqual(str(error), "[WC-API][graphql] plain")

    def test_graphql_error_with_empty_message_reads_graphql_error(self) -> None:
        error = self.error_of(_Response(200, {"errors": [{"message": "", "path": ["x"]}]}))
        self.assertEqual(str(error), "[WC-API][graphql] {'message': '', 'path': ['x']}")

    def test_mfa_setup_category_is_tagged_and_notified(self) -> None:
        body = {"errors": [{"message": "x", "extensions": {"category": "MFA_SETUP_REQUIRED"}}]}
        error = self.error_of(_Response(200, body))
        self.assertEqual(str(error), f"[WC-API][mfa_setup_required] {self.t(TranslationKeys.MFA_SETUP_REQUIRED)}")
        self.mock_notify.assert_called_once_with()
        self.assertEqual(self.session.invalidated_with, [])

    def test_graphql_unauthenticated_ends_the_session(self) -> None:
        error = self.error_of(_Response(200, {"errors": [{"message": "Unauthenticated."}]}))
        self.assertEqual(str(error), f"[WC-API][auth] {self.t(TranslationKeys.SESSION_EXPIRED)}")
        self.assertEqual(self.session.invalidated_with, [SESSION_REASON_UNAUTHENTICATED])
        self.mock_log.assert_any_call(
            "api_session_rejected", module="auth", extra={"cause": "[WC-API][auth] GraphQL Unauthenticated"}
        )

    # --- HTTP status ---------------------------------------------------------

    def test_401_ends_the_session(self) -> None:
        error = self.error_of(_Response(401, {}))
        self.assertEqual(str(error), f"[WC-API][auth] {self.t(TranslationKeys.SESSION_EXPIRED)}")
        self.assertEqual(self.session.invalidated_with, [SESSION_REASON_UNAUTHENTICATED])
        self.mock_log.assert_any_call(
            "api_session_rejected", module="auth", extra={"cause": "[WC-API][auth] HTTP 401 Unauthenticated"}
        )

    def test_401_without_auth_keeps_the_raw_tag(self) -> None:
        error = self.error_of(_Response(401, {}), require_auth=False)
        self.assertEqual(str(error), "[WC-API][auth] HTTP 401 Unauthenticated")
        self.assertEqual(self.session.invalidated_with, [])

    def test_403_is_a_refusal_not_an_expiry(self) -> None:
        error = self.error_of(_Response(403, {}))
        refused = self.t(TranslationKeys.SERVER_REQUEST_REFUSED).format(reason="HTTP 403")
        self.assertEqual(str(error), f"[WC-API][server] {refused}")
        self.assertEqual(self.session.invalidated_with, [])

    def test_5xx_on_gui_thread_fails_at_once(self) -> None:
        error = self.error_of(_Response(502), _Response(200, {"data": {}}))
        self.assertEqual(str(error), "[WC-API][server] HTTP 502")
        self.assertEqual(len(self.calls), 1)

    def test_other_status_names_only_the_code(self) -> None:
        error = self.error_of(_Response(404))
        failed = self.t(TranslationKeys.SERVER_REQUEST_FAILED).format(status_code=404)
        self.assertEqual(str(error), f"[WC-API][server] {failed}")
        self.assertNotIn("secret page", str(error))

    # --- transport -----------------------------------------------------------

    def test_connection_error_is_summarised(self) -> None:
        error = self.error_of(requests.exceptions.ConnectionError("Max retries exceeded with url: /graphql"))
        network = self.t(TranslationKeys.NETWORK_ERROR).format(error="Connection failed (max retries exceeded)")
        self.assertEqual(str(error), f"[WC-API][network] {network}")
        self.assertEqual(self.session.invalidated_with, [])

    def test_rate_limit_and_cancel_pass_through_unchanged(self) -> None:
        for raised in (ApiRateLimitError(2.0), RequestCancelled()):
            with self.subTest(type=type(raised).__name__):
                with self.assertRaises(type(raised)) as caught:
                    self.call(raised)
                self.assertIs(caught.exception, raised)

    def test_untagged_failure_keeps_its_text(self) -> None:
        error = self.error_of(RuntimeError("boom"))
        self.assertEqual(str(error), "boom")
        self.assertEqual(parse_tagged_message(error), (ApiErrorKind.UNKNOWN, "boom"))

    def test_empty_failure_reads_as_network_error(self) -> None:
        error = self.error_of(RuntimeError(""))
        network = self.t(TranslationKeys.NETWORK_ERROR).format(error="").strip()
        self.assertEqual(str(error), f"[WC-API][network] {network}")

    def test_request_carries_bearer_token(self) -> None:
        with patch.object(api_client_module.requests, "post") as post:
            post.return_value = _Response(200, {"data": {}})

            def run_send(send, **kwargs):
                return send()

            with patch.object(api_client_module, "send_api_request", run_send):
                if self.multipart:
                    self.call_real_multipart()
                else:
                    self.client.send_query(QUERY)
        headers = post.call_args.kwargs["headers"]
        self.assertEqual(headers["Authorization"], "Bearer live-token")
        self.assertEqual(headers["X-Requested-With"], "XMLHttpRequest")
        self.assertTrue(headers["User-Agent"].startswith("QGIS/"))
        self.assertEqual(headers["Accept"], "application/json")
        if self.multipart:
            # requests writes the multipart boundary into Content-Type itself.
            self.assertNotIn("Content-Type", headers)
        else:
            self.assertEqual(headers["Content-Type"], "application/json")


class ApiClientMultipartAnswersTest(ApiClientAnswersTest):
    multipart = True


class SendQueryOnlyTest(_ClientCase):
    """Behaviour that only send_query has: retries off the GUI thread and the with_success shape."""

    def off_gui_thread(self):
        return patch.object(api_client_module, "QThread", _WorkerThread)

    def test_worker_thread_retries_reads_after_5xx(self) -> None:
        with self.off_gui_thread():
            result = self.call(_Response(503), _Response(500), _Response(200, {"data": {"ok": 1}}))
        self.assertEqual(result, {"ok": 1})
        self.assertEqual(len(self.calls), 3)

    def test_worker_thread_gives_up_after_three_5xx(self) -> None:
        with self.off_gui_thread():
            error = self.error_of(_Response(500))
        self.assertEqual(str(error), "[WC-API][server] HTTP 500")
        self.assertEqual(len(self.calls), 3)

    def test_worker_thread_retries_reads_after_connection_errors(self) -> None:
        with self.off_gui_thread():
            result = self.call(requests.exceptions.ConnectionError("x"), _Response(200, {"data": {"ok": 2}}))
        self.assertEqual(result, {"ok": 2})
        self.assertEqual(len(self.calls), 2)

    def test_worker_thread_does_not_repeat_mutations(self) -> None:
        with self.off_gui_thread(), self._answers([_Response(500)]):
            with self.assertRaises(Exception):
                self.client.send_query(MUTATION)
        self.assertEqual(len(self.calls), 1)

    def test_retry_network_true_still_needs_a_worker_thread(self) -> None:
        error = self.error_of(_Response(500), retry_network=True)
        self.assertEqual(str(error), "[WC-API][server] HTTP 500")
        self.assertEqual(len(self.calls), 1)

    def test_with_success_wraps_data(self) -> None:
        body = {"data": {"task": {"id": "1"}}}
        self.assertEqual(
            self.call(_Response(200, body), with_success=True),
            {"success": True, "response": {"task": {"id": "1"}}, "raw": body, "error": None},
        )

    def test_with_success_and_raw_wraps_whole_body(self) -> None:
        body = {"data": {}}
        self.assertEqual(
            self.call(_Response(200, body), with_success=True, return_raw=True),
            {"success": True, "response": body, "raw": body, "error": None},
        )

    def test_with_success_returns_errors_instead_of_raising(self) -> None:
        result = self.call(_Response(200, {"errors": [{"message": "bad"}]}), with_success=True)
        self.assertEqual(result, {"success": False, "response": None, "raw": None, "error": "[WC-API][graphql] bad"})

    def test_with_success_returns_expiry_instead_of_raising(self) -> None:
        result = self.call(_Response(401, {}), with_success=True)
        self.assertEqual(result["error"], f"[WC-API][auth] {self.t(TranslationKeys.SESSION_EXPIRED)}")
        self.assertEqual(self.session.invalidated_with, [SESSION_REASON_UNAUTHENTICATED])

    def test_with_success_still_raises_network_errors(self) -> None:
        error = self.error_of(requests.exceptions.ConnectionError("Connection refused"), with_success=True)
        self.assertTrue(str(error).startswith("[WC-API][network] "))


class TypedErrorTest(_ClientCase):
    """The client raises ApiError, so callers can read the kind without parsing text."""

    def test_server_answers_raise_api_error_with_kind_and_user_text(self) -> None:
        cases = (
            (_Response(200, {"errors": [{"message": "bad"}]}), ApiErrorKind.GRAPHQL, "bad"),
            (_Response(403, {}), ApiErrorKind.SERVER,
             self.t(TranslationKeys.SERVER_REQUEST_REFUSED).format(reason="HTTP 403")),
            (_Response(500), ApiErrorKind.SERVER, "HTTP 500"),
            (_Response(401, {}), ApiErrorKind.AUTH, self.t(TranslationKeys.SESSION_EXPIRED)),
            (requests.exceptions.ConnectionError("Connection refused"), ApiErrorKind.NETWORK,
             self.t(TranslationKeys.NETWORK_ERROR).format(error="Connection refused")),
        )
        for answer, kind, text in cases:
            for multipart in (False, True):
                with self.subTest(answer=getattr(answer, "status_code", answer), multipart=multipart):
                    self.multipart = multipart
                    error = self.error_of(answer)
                    self.assertIsInstance(error, ApiError)
                    self.assertEqual((error.kind, error.message), (kind, text))
                    self.assertEqual(parse_tagged_message(error), (kind, text))
                    self.assertEqual(parse_tagged_message(str(error)), (kind, text))

    def test_expiry_keeps_the_servers_answer_as_its_cause(self) -> None:
        error = self.error_of(_Response(401, {}))
        self.assertIsInstance(error.__cause__, ApiError)
        self.assertEqual(str(error.__cause__), "[WC-API][auth] HTTP 401 Unauthenticated")


class MultipartOnlyTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QgsApplication.instance() or QgsApplication([], False)

    def test_without_files_it_is_a_plain_query(self) -> None:
        client = api_client_module.APIClient(session_manager=_Session())
        with patch.object(client, "send_query", return_value={"ok": 1}) as send_query:
            result = client.send_multipart_query(
                MUTATION, {"input": {"file": "x"}}, file_variables={"input.file": ""}, timeout=7, return_raw=True
            )
        self.assertEqual(result, {"ok": 1})
        send_query.assert_called_once_with(
            MUTATION, variables={"input": {"file": "x"}}, require_auth=True, timeout=7, return_raw=True
        )

    def test_upload_is_never_repeated_after_5xx(self) -> None:
        session = _Session()
        client = api_client_module.APIClient(session_manager=session)
        calls = []

        def fake_send(send, **kwargs):
            calls.append(kwargs)
            return _Response(500)

        upload = tempfile.NamedTemporaryFile(suffix=".txt", delete=False)
        upload.close()
        self.addCleanup(os.remove, upload.name)
        with patch.object(api_client_module, "send_api_request", fake_send), \
                patch.object(api_client_module, "QThread", _WorkerThread), \
                patch.object(api_client_module.time, "sleep"):
            with self.assertRaises(Exception) as caught:
                client.send_multipart_query(MUTATION, {"input": {}}, file_variables={"input.file": upload.name})
        self.assertEqual(str(caught.exception), "[WC-API][server] HTTP 500")
        self.assertEqual(len(calls), 1)


if __name__ == "__main__":
    unittest.main()
