"""Module widget lookup, drive probe and file preview logging: each failure lands on the safe side."""
from __future__ import annotations

import ctypes
import os
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, Mock, patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
if os.environ.get("QGIS_PREFIX_PATH"):
    sys.path.append(str(Path(os.environ["QGIS_PREFIX_PATH"]) / "python" / "plugins"))

import requests
from qgis.core import QgsApplication
from qgis.PyQt.QtCore import QCoreApplication, QEvent, QUrl
from qgis.PyQt.QtWidgets import QWidget

from Kavitro_dev import module_manager as manager_module
from Kavitro_dev.Logs.python_fail_logger import PythonFailLogger
from Kavitro_dev.languages.translation_keys import TranslationKeys
from Kavitro_dev.python.actions import file_actions as file_actions_module
from Kavitro_dev.python.api_actions import APIModuleActions
from Kavitro_dev.ui.mixins.token_mixin import TokenMixin
from Kavitro_dev.utils import security_boundaries
from Kavitro_dev.utils.messagesHelper import ModernMessageDialog
from Kavitro_dev.widgets import theme_manager as theme_module
from Kavitro_dev.widgets.DataDisplayWidgets import HtmlDescriptionWidget as html_module

ModuleManager = manager_module.ModuleManager

SIGNED_URL = "https://files.example/abc.pdf?X-Amz-Signature=SECRET123&X-Amz-Credential=KEY456"


def delete_now(widget: QWidget) -> None:
    widget.hide()
    widget.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)


class QtTestCase(unittest.TestCase):
    """No modal window can open, whatever the code under test does."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QgsApplication.instance() or QgsApplication([], False)

    def setUp(self) -> None:
        for name in ("ask_choice_modern", "show_warning", "show_error", "show_info"):
            if hasattr(ModernMessageDialog, name):
                patcher = patch.object(ModernMessageDialog, name, return_value=None)
                patcher.start()
                self.addCleanup(patcher.stop)
        self.window = QWidget()
        self.addCleanup(delete_now, self.window)


class WidgetlessModule(TokenMixin):
    """A module whose widget cannot be built; it is not a QWidget itself."""

    def __init__(self, **_kwargs) -> None:
        self._active_token = 0
        self._activated = False

    def activate(self) -> None:
        pass

    def deactivate(self) -> None:
        pass

    def get_widget(self):
        raise ValueError("no widget yet")


class ModuleWidgetLookupTest(QtTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.engine = theme_module.RethemeEngine()
        for patcher in (
            patch.object(ModuleManager, "_instance", None),
            patch.object(theme_module.ThemeManager, "_retheme_engine", self.engine),
            patch.object(PythonFailLogger, "log_exception"),
        ):
            started = patcher.start()
            self.addCleanup(patcher.stop)
        self.log = started
        names = manager_module.MODULES_LIST_BY_NAME
        saved_names = list(names)
        self.addCleanup(lambda: names.__setitem__(slice(None), saved_names))
        self.manager = ModuleManager()

    def test_a_qwidget_is_returned_as_is_without_a_log_line(self) -> None:
        widget = QWidget(self.window)
        self.assertIs(ModuleManager._get_widget_safe(SimpleNamespace(get_widget=lambda: widget)), widget)
        self.log.assert_not_called()

    def test_failed_lookup_gives_none_and_is_logged(self) -> None:
        self.assertIsNone(ModuleManager._get_widget_safe(WidgetlessModule()))
        self.assertEqual(self.log.call_args.kwargs, {
            "module": "general",
            "event": "module_widget_build_failed",
            "extra": {"module_class": "WidgetlessModule"},
        })

    def test_a_lookup_that_returns_no_qwidget_gives_none_and_is_logged(self) -> None:
        for value in (None, object()):
            with self.subTest(value=value):
                self.log.reset_mock()
                self.assertIsNone(ModuleManager._get_widget_safe(SimpleNamespace(get_widget=lambda v=value: v)))
                self.assertIsInstance(self.log.call_args.args[0], TypeError)
                self.assertEqual(self.log.call_args.kwargs["event"], "module_widget_build_failed")

    def test_module_without_a_widget_still_activates_and_the_next_theme_switch_works(self) -> None:
        self.manager.registerModule(WidgetlessModule, "WORKS")
        self.manager.activateModule("WORKS")

        self.assertEqual(self.manager.getActiveModuleName(), "works")
        self.assertEqual(self.engine._registrations, [])
        with patch.object(theme_module.ThemeManager, "apply_theme") as apply_theme:
            self.engine.retheme_all()  # raised TypeError while the module instance was registered
        apply_theme.assert_not_called()


def broken_windll() -> SimpleNamespace:
    def broken(*_args):
        raise OSError("probe failed")

    return SimpleNamespace(
        kernel32=SimpleNamespace(GetDriveTypeW=broken),
        mpr=SimpleNamespace(WNetGetConnectionW=broken),
    )


@unittest.skipUnless(os.name == "nt", "the drive probe only runs on Windows")
class FailedDriveProbeTest(QtTestCase):
    def setUp(self) -> None:
        super().setUp()
        for patcher in (
            patch.object(ctypes, "windll", broken_windll(), create=True),
            patch.object(PythonFailLogger, "log"),
        ):
            started = patcher.start()
            self.addCleanup(patcher.stop)
        self.log = started

    def test_failed_probe_reports_a_remote_drive_and_is_logged(self) -> None:
        self.assertEqual(security_boundaries.windows_drive_type("Z:\\file.pdf"), security_boundaries._WINDOWS_DRIVE_REMOTE)
        self.assertEqual(self.log.call_args.args[0], "security_drive_probe_failed")

    def test_unverified_drive_paths_are_network_targets(self) -> None:
        for raw in (r"Z:\Project\Drawing.pdf", "file:///Z:/Project/Drawing.pdf"):
            with self.subTest(raw=raw):
                target = security_boundaries.classify_description_link(raw)
                self.assertEqual(target.kind, security_boundaries.DESCRIPTION_LINK_NETWORK_PATH)
                self.assertEqual(target.target, r"Z:\Project\Drawing.pdf")
                self.assertEqual(target.host, "Z:")

    def test_a_local_pdf_link_asks_for_the_network_confirmation_before_opening(self) -> None:
        texts = {
            TranslationKeys.YES: "Yes",
            TranslationKeys.NO: "No",
            TranslationKeys.CONFIRM: "Confirm",
            TranslationKeys.DESCRIPTION_LINK_NETWORK_CONFIRM: "Network: {host} {path}",
        }
        lang = SimpleNamespace(translate=lambda key: texts.get(key, str(key)))
        widget = html_module.HtmlDescriptionWidget("", parent=self.window, lang_manager=lang)
        with tempfile.TemporaryDirectory() as folder:
            path = os.path.join(folder, "drawing.pdf")
            Path(path).write_bytes(b"%PDF-1.4")
            with patch.object(ModernMessageDialog, "ask_choice_modern", return_value="No") as ask, \
                    patch.object(html_module.TaskFilePreviewDialog, "open_preview") as open_preview:
                widget._handle_anchor_clicked(QUrl.fromLocalFile(path))

        ask.assert_called_once()
        self.assertTrue(ask.call_args.args[1].startswith(f"Network: {path[:2].upper()} "))
        open_preview.assert_not_called()


class RedactedFileLogTest(QtTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.client = Mock()
        self.client.send_query.return_value = {"createDownloadLink": {"url": SIGNED_URL}}
        loader = Mock()
        loader.load_query_by_module.return_value = "query"
        self.response = MagicMock()
        for target, name, kwargs in (
            (file_actions_module, "APIClient", {"return_value": self.client}),
            (file_actions_module, "GraphQLQueryLoader", {"return_value": loader}),
            (requests, "get", {}),
            (PythonFailLogger, "log_exception", {}),
        ):
            patcher = patch.object(target, name, **kwargs)
            started = patcher.start()
            self.addCleanup(patcher.stop)
            if name == "get":
                started.return_value.__enter__.return_value = self.response
        self.log = started

    def logged_message(self) -> str:
        return str(self.log.call_args.args[0])

    def assert_no_secret(self, message: str) -> None:
        for secret in ("SECRET123", "KEY456", "X-Amz", "files.example", "/abc.pdf"):
            self.assertNotIn(secret, message)

    def test_preview_http_error_keeps_type_and_status_but_not_the_signed_url(self) -> None:
        self.response.raise_for_status.side_effect = requests.HTTPError(
            f"403 Client Error: Forbidden for url: {SIGNED_URL}"
        )
        self.assertIsNone(APIModuleActions.fetch_file_preview_payload("abc", max_bytes=10))

        message = self.logged_message()
        self.assertEqual(message, "HTTPError: 403 Client Error: Forbidden for url: <url>")
        self.assertEqual(self.log.call_args.kwargs["event"], "task_file_preview_fetch_failed")

    def test_preview_connection_error_drops_the_path_and_query_urllib3_prints(self) -> None:
        self.response.raise_for_status.side_effect = requests.ConnectionError(
            "HTTPSConnectionPool(host='files.example', port=443): Max retries exceeded with "
            "url: /abc.pdf?X-Amz-Signature=SECRET123&X-Amz-Credential=KEY456 (Caused by timeout)"
        )
        self.assertIsNone(APIModuleActions.fetch_file_preview_payload("abc", max_bytes=10))

        message = self.logged_message()
        self.assertTrue(message.startswith("ConnectionError: "))
        self.assertIn("url: <url>", message)
        self.assertNotIn("SECRET123", message)
        self.assertNotIn("KEY456", message)

    def test_graphql_file_actions_strip_urls_from_their_errors_too(self) -> None:
        error = RuntimeError(f"upstream failed for {SIGNED_URL} and /x?token=SECRET123")
        self.client.send_query.side_effect = error
        calls = {
            "download link": lambda: APIModuleActions.create_file_download_link("abc"),
            "delete": lambda: APIModuleActions.delete_file("abc"),
            "file list": lambda: APIModuleActions.get_module_files("works", "t-1"),
        }
        for name, call in calls.items():
            with self.subTest(action=name):
                self.log.reset_mock()
                self.assertIsNone(call())
                message = self.logged_message()
                self.assertTrue(message.startswith("RuntimeError: upstream failed for <url>"))
                self.assert_no_secret(message)
                self.assertNotIn("token=", message)

    def test_an_error_without_a_url_is_logged_unchanged(self) -> None:
        error = RuntimeError("offline")
        self.client.send_query.side_effect = error
        self.assertIsNone(APIModuleActions.delete_file("abc"))
        self.assertIs(self.log.call_args.args[0], error)

    def test_upload_error_is_stripped_of_urls(self) -> None:
        self.client.send_multipart_query.side_effect = RuntimeError(f"upload refused by {SIGNED_URL}")
        with tempfile.TemporaryDirectory() as folder:
            path = os.path.join(folder, "a.pdf")
            Path(path).write_bytes(b"%PDF-1.4")
            self.assertIsNone(APIModuleActions.upload_module_file("works", "t-1", path))

        self.assertEqual(self.logged_message(), "RuntimeError: upload refused by <url>")
        self.assertEqual(self.log.call_args.kwargs["event"], "module_file_upload_failed")


if __name__ == "__main__":
    unittest.main()
