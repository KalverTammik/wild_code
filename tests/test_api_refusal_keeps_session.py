"""An HTTP 403 is a refusal (Cloudflare, an IP rule, no access) and keeps the user signed in; a 401 still ends it."""
from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from PyQt5.QtWidgets import QApplication

from Kavitro_dev.languages.translation_keys import TranslationKeys
from Kavitro_dev.python import api_client as api_client_module
from Kavitro_dev.utils.api_error_handling import ApiErrorKind, parse_tagged_message
from Kavitro_dev.utils.SessionManager import SESSION_REASON_UNAUTHENTICATED


class _Response:
    def __init__(self, status_code: int, body=None, headers: dict | None = None) -> None:
        self.status_code = status_code
        self._body = body
        self.headers = headers or {}
        self.text = ""

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


class RefusalKeepsSessionTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self) -> None:
        self.session = _Session()
        self.client = api_client_module.APIClient(session_manager=self.session)
        log = patch.object(api_client_module.PythonFailLogger, "log")
        self.log = log.start()
        self.addCleanup(log.stop)

    def send(self, response: _Response, *, multipart: bool = False) -> str:
        with patch.object(api_client_module, "send_api_request", lambda *_a, **_k: response), \
                patch.object(api_client_module, "SessionManager", self.session):
            with self.assertRaises(Exception) as caught:
                if multipart:
                    upload = tempfile.NamedTemporaryFile(suffix=".txt", delete=False)
                    upload.close()
                    self.addCleanup(os.remove, upload.name)
                    self.client.send_multipart_query(
                        "mutation Upload { upload }", {"input": {}}, file_variables={"input.file": upload.name})
                else:
                    self.client.send_query("query Task { task(id: 347) { id } }")
        return str(caught.exception)

    def refused_text(self, reason: str) -> str:
        return self.client.lang.translate(TranslationKeys.SERVER_REQUEST_REFUSED).format(reason=reason)

    def test_a_403_keeps_the_user_signed_in_and_says_the_server_refused(self) -> None:
        message = self.send(_Response(403, {}))

        self.assertEqual(self.session.invalidated_with, [])
        self.assertEqual(parse_tagged_message(message), (ApiErrorKind.SERVER, self.refused_text("HTTP 403")))

    def test_the_servers_category_is_named(self) -> None:
        body = {"errors": [{"message": "refused", "extensions": {"category": "IP_NOT_ALLOWED"}}]}

        message = self.send(_Response(403, body))

        self.assertEqual(parse_tagged_message(message)[1], self.refused_text("IP_NOT_ALLOWED"))
        self.log.assert_called_with("api_request_forbidden", module="api", extra={"reason": "IP_NOT_ALLOWED"})

    def test_a_cloudflare_challenge_is_named_and_its_page_kept_out(self) -> None:
        message = self.send(_Response(403, None, {"cf-mitigated": "challenge"}))

        self.assertEqual(parse_tagged_message(message)[1], self.refused_text("Cloudflare challenge"))

    def test_text_that_is_no_category_stays_out_of_the_message(self) -> None:
        body = {"extensions": {"category": "<b>Just a moment</b>"}}

        message = self.send(_Response(403, body))

        self.assertNotIn("Just a moment", message)
        self.assertEqual(parse_tagged_message(message)[1], self.refused_text("HTTP 403"))

    def test_an_upload_refused_with_403_keeps_the_session_too(self) -> None:
        self.send(_Response(403, {}), multipart=True)

        self.assertEqual(self.session.invalidated_with, [])

    def test_a_401_still_ends_the_session_and_the_log_names_it(self) -> None:
        message = self.send(_Response(401, {}))

        self.assertEqual(self.session.invalidated_with, [SESSION_REASON_UNAUTHENTICATED])
        self.assertEqual(parse_tagged_message(message)[0], ApiErrorKind.AUTH)
        cause = self.log.call_args.kwargs["extra"]["cause"]
        self.assertIn("HTTP 401", cause)

    def test_a_graphql_unauthenticated_answer_ends_it_with_its_own_cause(self) -> None:
        self.send(_Response(200, {"errors": [{"message": "Unauthenticated."}]}))

        self.assertEqual(self.session.invalidated_with, [SESSION_REASON_UNAUTHENTICATED])
        self.assertIn("GraphQL", self.log.call_args.kwargs["extra"]["cause"])


if __name__ == "__main__":
    unittest.main()
