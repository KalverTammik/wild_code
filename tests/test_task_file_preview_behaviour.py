"""Characterization tests for TaskFilePreviewDialog, written against the code before it was
split: which files get which preview, every placeholder on the way, and opening a file in
the default application."""
from __future__ import annotations

import os
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
PLUGIN_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLUGIN_ROOT.parent))
if os.environ.get("QGIS_PREFIX_PATH"):
    sys.path.append(str(Path(os.environ["QGIS_PREFIX_PATH"]) / "python" / "plugins"))

import requests
from qgis.core import QgsApplication
from qgis.PyQt.QtCore import QBuffer, QByteArray, QCoreApplication, QEvent, QIODevice
from qgis.PyQt.QtGui import QColor, QDesktopServices, QPixmap
from qgis.PyQt.QtWidgets import QLabel, QPlainTextEdit, QScrollArea, QWidget

from Kavitro_dev.Logs.python_fail_logger import PythonFailLogger
from Kavitro_dev.python import workers
from Kavitro_dev.python.api_actions import APIModuleActions
from Kavitro_dev.ui.messages_helper import ModernMessageDialog
from Kavitro_dev.ui.theme_manager import ThemeManager
from Kavitro_dev.widgets.DataDisplayWidgets import TaskFilePreviewDialog as preview_module
from Kavitro_dev.widgets.DataDisplayWidgets import task_file_external_open as external_open
from Kavitro_dev.widgets.DataDisplayWidgets import task_file_identity
from Kavitro_dev.widgets.DataDisplayWidgets.TaskFilePreviewDialog import TaskFilePreviewDialog as Dialog

_APP = QgsApplication.instance() or QgsApplication([], False)
if QgsApplication.instance() is _APP:
    QgsApplication.initQgis()


class _Text(str):
    def format(self, *args, **kwargs):
        return f"{self}{sorted(kwargs.items())}"


LANG = Mock(translate=lambda key: _Text(f"T:{key}"))


def failed(name):
    return f"T:task_files_preview_failed[('name', '{name}')]"


def png_bytes():
    pixmap = QPixmap(4, 3)
    pixmap.fill(QColor("red"))
    data = QByteArray()
    buffer = QBuffer(data)
    buffer.open(QIODevice.WriteOnly)
    pixmap.save(buffer, "PNG")
    return bytes(data)


class _FakeWebView(QWidget):
    made: list = []

    def __init__(self, parent):
        super().__init__(parent)
        self.loadFinished = Mock()
        self.urls = []
        self.attributes = []
        _FakeWebView.made.append(self)

    def settings(self):
        return types.SimpleNamespace(setAttribute=lambda attr, value: self.attributes.append((attr, value)))

    def setUrl(self, url):
        self.urls.append(url.toLocalFile() or url.toString())

    def stop(self):
        pass


class _Base(unittest.TestCase):
    def setUp(self):
        self.p(ThemeManager, "apply_module_style")
        self.log = self.p(PythonFailLogger, "log_exception")
        self.warning = self.p(ModernMessageDialog, "show_warning")
        self.fetch = self.p(APIModuleActions, "fetch_file_preview_payload")
        self.p(APIModuleActions, "user_display_name", return_value="Jane")
        self.addCleanup(lambda: QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete))

    def p(self, target, name, *args, **kwargs):
        patcher = patch.object(target, name, *args, **kwargs)
        mock = patcher.start()
        self.addCleanup(patcher.stop)
        return mock

    def make(self, file_info=None, **kwargs):
        dialog = Dialog(file_info=file_info, lang_manager=LANG, **kwargs)
        self.addCleanup(dialog.deleteLater)
        return dialog

    def content(self, dialog):
        item = dialog._content_layout.itemAt(0)
        return item.widget() if item is not None else None

    def placeholder(self, dialog):
        widget = self.content(dialog)
        self.assertIsInstance(widget, QLabel)
        return widget.text()


class ClassificationTest(unittest.TestCase):
    def test_image_candidates(self):
        self.assertTrue(Dialog.is_image_preview_candidate(file_info={"mimeType": "Image/X-Icon"}))
        self.assertTrue(Dialog.is_image_preview_candidate(file_info={"ext": ".WEBP"}))
        self.assertTrue(Dialog.is_image_preview_candidate(local_file_path="C:/a/b.jpeg"))
        self.assertFalse(Dialog.is_image_preview_candidate(file_info={"ext": "pdf", "mimeType": "application/pdf"}))
        self.assertFalse(Dialog.is_image_preview_candidate(file_info=None))

    def test_internal_candidates(self):
        yes = [{"mimeType": "text/plain"}, {"mimeType": "application/json"}, {"ext": "md"},
               {"ext": "pdf"}, {"mimeType": "application/pdf"}, {"ext": "png"}, {"mimeType": "image/svg+xml"}]
        for info in yes:
            self.assertTrue(Dialog.is_internal_preview_candidate(file_info=info), info)
        self.assertFalse(Dialog.is_internal_preview_candidate(file_info={"ext": "zip", "mimeType": "application/zip"}))
        self.assertTrue(Dialog.is_internal_preview_candidate(local_file_path="x/notes.log"))
        self.assertFalse(Dialog.is_internal_preview_candidate(local_file_path="x/data.dwg", file_info={"ext": "pdf"}))

    def test_file_names(self):
        self.assertEqual(Dialog.resolve_file_name(local_file_path=" C:/a/b.pdf "), "b.pdf")
        self.assertEqual(Dialog.resolve_file_name(local_file_path="C:/a/"), "C:/a/")
        self.assertEqual(Dialog.resolve_file_name(file_info={"fileName": "f.txt", "uuid": "u"}), "f.txt")
        self.assertEqual(Dialog.resolve_file_name(file_info={"uuid": "u"}), "u")
        self.assertEqual(Dialog.resolve_file_name(file_info="bad"), "-")

    def test_pdf_runtime_support_reports_versions(self):
        supported, info = Dialog.embedded_pdf_runtime_support()
        self.assertIsInstance(supported, bool)
        self.assertEqual(set(info), {"qt", "pyqt"})
        with patch.dict(sys.modules, {"qgis.PyQt.QtWebEngineWidgets": None}):
            self.assertFalse(Dialog.embedded_pdf_runtime_support()[0])


class OpenPreviewTest(_Base):
    def setUp(self):
        super().setUp()
        self.p(Dialog, "_load_preview")

    def test_pdf_without_runtime_warns_and_opens_nothing(self):
        self.p(Dialog, "embedded_pdf_runtime_support", return_value=(False, {"qt": "5.15", "pyqt": ""}))
        self.assertIsNone(Dialog.open_preview(file_info={"ext": "pdf", "uuid": "u"}, lang_manager=LANG))
        self.assertEqual(self.warning.call_args.args,
                         ("T:Warning", "T:task_files_pdf_runtime_unsupported[('pyqt_version', 'unknown'), ('qt_version', '5.15')]"))

    def test_pdf_opens_full_size_and_others_keep_compact_and_lazy(self):
        self.p(Dialog, "embedded_pdf_runtime_support", return_value=(True, {}))
        pdf = Dialog.open_preview(file_info={"ext": "pdf", "uuid": "u"}, lang_manager=LANG, compact=True, lazy=True)
        self.addCleanup(pdf.deleteLater)
        self.assertEqual((pdf._compact_mode, pdf._lazy_preview), (False, False))
        text = Dialog.open_preview(file_info={"ext": "txt", "uuid": "u"}, lang_manager=LANG, compact=True, lazy=True)
        self.addCleanup(text.deleteLater)
        self.assertEqual((text._compact_mode, text._lazy_preview), (True, True))


class DialogFrameTest(_Base):
    def setUp(self):
        super().setUp()
        self.p(Dialog, "_load_preview")

    def test_title_sizes_and_meta(self):
        dialog = self.make({"uuid": "u", "fileName": "plan.pdf", "mimeType": "application/pdf",
                            "humanReadableSize": "2 MB", "uploader": {}})
        self.assertEqual(dialog.windowTitle(), "T:task_files_preview_title[('name', 'plan.pdf')]")
        self.assertEqual((dialog.minimumWidth(), dialog.minimumHeight()), (760, 520))
        self.assertEqual(dialog._meta_label.text(), "<b>plan.pdf</b><br>application/pdf • 2 MB • Jane")
        compact = self.make({"uuid": "u", "ext": "png"}, compact=True, local_title="Foto")
        self.assertEqual((compact.minimumWidth(), compact.minimumHeight(), compact.width()), (420, 320, 520))
        self.assertEqual(compact.windowTitle(), "T:task_files_preview_title[('name', 'Foto')]")
        self.assertEqual(compact._meta_label.text(), "<b>u</b><br>png • – • Jane")

    def test_local_file_meta(self):
        with tempfile.TemporaryDirectory() as folder:
            path = os.path.join(folder, "a.txt")
            Path(path).write_bytes(b"x" * 2048)
            dialog = self.make(local_file_path=path)
            self.assertEqual(dialog._meta_label.text(), "<b>a.txt</b><br>text/plain • 2.0 KB • T:task_file_local_file")
            missing = self.make(local_file_path=os.path.join(folder, "gone.zzz"))
            self.assertEqual(missing._meta_label.text(), "<b>gone.zzz</b><br>zzz • – • T:task_file_local_file")

    def test_external_button_follows_the_allow_list(self):
        allowed = self.make({"uuid": "u", "fileName": "a.pdf", "ext": "pdf"})
        self.assertTrue(allowed._open_external_button.isEnabled())
        blocked = self.make({"uuid": "u", "fileName": "a.exe", "ext": "exe"})
        self.assertFalse(blocked._open_external_button.isEnabled())
        self.assertIn("task_files_external_open_blocked", blocked._open_external_button.toolTip())


class RemotePreviewTest(_Base):
    def test_no_uuid_and_unsupported(self):
        self.assertEqual(self.placeholder(self.make({"fileName": "a.png", "ext": "png"})), failed("a.png"))
        self.assertEqual(self.placeholder(self.make({"uuid": "u", "ext": "zip"})), "T:task_files_preview_unsupported")
        self.fetch.assert_not_called()

    def test_image_preview(self):
        info = {"uuid": "u", "fileName": "a.png", "ext": "png"}
        self.assertEqual(self.placeholder(self.make(dict(info, size=Dialog.IMAGE_PREVIEW_MAX_BYTES + 1))),
                         "T:task_files_preview_too_large")
        self.fetch.assert_not_called()
        self.fetch.return_value = None
        self.assertEqual(self.placeholder(self.make(info)), failed("a.png"))
        self.fetch.assert_called_with("u", max_bytes=25 * 1024 * 1024)
        self.fetch.return_value = {"truncated": True, "url": "https://x"}
        dialog = self.make(info)
        self.assertEqual((self.placeholder(dialog), dialog._last_url), ("T:task_files_preview_too_large", "https://x"))
        self.fetch.return_value = {"content": b"not an image"}
        self.assertEqual(self.placeholder(self.make(info)), failed("a.png"))
        self.fetch.return_value = {"content": png_bytes(), "url": " https://y "}
        dialog = self.make(info)
        scroll = self.content(dialog)
        self.assertIsInstance(scroll, QScrollArea)
        image = scroll.widget().findChild(QLabel)
        self.assertEqual((image.pixmap().width(), image.pixmap().height()), (1280, 960))
        self.assertEqual(dialog._last_url, "https://y")
        self.assertTrue(dialog._notice_label.isHidden())

    def test_compact_image_is_scaled_smaller(self):
        self.fetch.return_value = {"content": png_bytes()}
        dialog = self.make({"uuid": "u", "ext": "png"}, compact=True)
        image = self.content(dialog).widget().findChild(QLabel)
        self.assertEqual((image.pixmap().width(), image.pixmap().height()), (560, 420))

    def test_text_preview(self):
        info = {"uuid": "u", "fileName": "a.csv", "mimeType": "text/csv"}
        self.fetch.return_value = None
        self.assertEqual(self.placeholder(self.make(info)), failed("a.csv"))
        self.fetch.return_value = {"content": "ä;b".encode("cp1252"), "url": "https://t"}
        dialog = self.make(info)
        editor = self.content(dialog)
        self.assertIsInstance(editor, QPlainTextEdit)
        self.assertEqual(editor.toPlainText(), "ä;b")
        self.assertTrue(editor.isReadOnly())
        self.assertEqual(editor.lineWrapMode(), QPlainTextEdit.NoWrap)
        self.assertTrue(dialog._notice_label.isHidden())
        self.fetch.assert_called_with("u", max_bytes=512 * 1024)
        self.fetch.return_value = {"content": b"abc", "truncated": True}
        dialog = self.make(info)
        self.assertEqual(dialog._notice_label.text(), "T:task_files_preview_truncated[('count', 512)]")
        self.assertFalse(dialog._notice_label.isHidden())

    def test_text_decoding_order(self):
        self.assertEqual(task_file_identity.decode_text("\ufeffhi".encode("utf-8")), "hi")
        self.assertEqual(task_file_identity.decode_text("hi".encode("utf-16")), "hi")
        self.assertEqual(task_file_identity.human_readable_size(None), "–")
        self.assertEqual(task_file_identity.human_readable_size(1023), "1023 B")
        self.assertEqual(task_file_identity.human_readable_size(5 * 1024 ** 3), "5.0 GB")
        self.assertEqual(task_file_identity.human_readable_size(5 * 1024 ** 4), "5120.0 GB")
        self.assertIsNone(task_file_identity.safe_int("x"))
        self.assertEqual(task_file_identity.safe_int("7"), 7)


class PdfPreviewTest(_Base):
    INFO = {"uuid": "u", "fileName": "a.pdf", "ext": "pdf"}

    def setUp(self):
        super().setUp()
        _FakeWebView.made = []
        engine = types.SimpleNamespace(QWebEngineView=_FakeWebView,
                                       QWebEngineSettings=types.SimpleNamespace(PdfViewerEnabled=1, PluginsEnabled=2))
        modules = patch.dict(sys.modules, {"qgis.PyQt.QtWebEngineWidgets": engine})
        modules.start()
        self.addCleanup(modules.stop)

    def test_pdf_wins_over_an_image_mime_type(self):
        self.fetch.return_value = None
        self.assertEqual(self.placeholder(self.make({"uuid": "u", "mimeType": "image/png", "ext": "pdf"})), failed("u"))
        self.fetch.assert_called_once_with("u", max_bytes=40 * 1024 * 1024)

    def test_size_limit_and_missing_engine(self):
        self.assertEqual(self.placeholder(self.make(dict(self.INFO, size=Dialog.PDF_PREVIEW_MAX_BYTES + 1))),
                         "T:task_files_preview_too_large")
        with patch.dict(sys.modules, {"qgis.PyQt.QtWebEngineWidgets": None}):
            self.assertEqual(self.placeholder(self.make(self.INFO)), "T:task_files_preview_unsupported")
        self.fetch.assert_not_called()

    def test_payload_problems(self):
        for payload, text in ((None, failed("a.pdf")), ({"truncated": True}, "T:task_files_preview_too_large"),
                              ({"content": b""}, failed("a.pdf"))):
            with self.subTest(payload=payload):
                self.fetch.return_value = payload
                self.assertEqual(self.placeholder(self.make(self.INFO)), text)
        self.fetch.assert_called_with("u", max_bytes=40 * 1024 * 1024)

    def test_pdf_is_shown_from_a_temp_file_that_is_removed_on_close(self):
        self.fetch.return_value = {"content": b"%PDF-1.4", "url": "https://p"}
        dialog = self.make(self.INFO)
        view = _FakeWebView.made[-1]
        temp_path = dialog._pdf_temp_path
        self.assertTrue(temp_path.endswith(".pdf"))
        self.assertEqual(Path(temp_path).read_bytes(), b"%PDF-1.4")
        self.assertEqual(view.urls, [temp_path.replace("\\", "/")])
        self.assertEqual(view.attributes, [(1, True), (2, True)])
        view.loadFinished.connect.assert_called_once_with(dialog._handle_pdf_web_view_loaded)
        self.assertEqual(dialog._last_url, "https://p")
        dialog.close()
        self.assertFalse(os.path.exists(temp_path))
        self.assertIsNone(dialog._web_view)

    def test_failed_load_signal_removes_the_temp_file(self):
        self.fetch.return_value = {"content": b"%PDF"}
        dialog = self.make(self.INFO)
        temp_path = dialog._pdf_temp_path
        dialog._handle_pdf_web_view_loaded(False)
        self.assertTrue(os.path.exists(temp_path))
        dialog.show()
        dialog._handle_pdf_web_view_loaded(True)
        self.assertTrue(os.path.exists(temp_path))
        dialog._handle_pdf_web_view_loaded(False)
        self.assertFalse(os.path.exists(temp_path))
        self.assertEqual(self.placeholder(dialog), failed("a.pdf"))
        dialog.close()

    def test_view_that_cannot_load_falls_back_to_the_placeholder(self):
        self.fetch.return_value = {"content": b"%PDF"}
        with patch.object(Dialog, "_load_pdf_webengine_preview", return_value=False):
            dialog = self.make(self.INFO)
        self.assertEqual(self.placeholder(dialog), failed("a.pdf"))
        self.assertEqual(dialog._pdf_temp_path, "")
        with patch.object(Dialog, "_write_pdf_temp_file", return_value=""):
            self.assertEqual(self.placeholder(self.make(self.INFO)), failed("a.pdf"))

    def test_local_pdf(self):
        with tempfile.TemporaryDirectory() as folder:
            pdf = os.path.join(folder, "a.pdf")
            Path(pdf).write_bytes(b"%PDF")
            dialog = self.make(local_file_path=pdf)
            self.assertEqual(_FakeWebView.made[-1].urls, [pdf.replace("\\", "/")])
            self.assertTrue(dialog._last_url.startswith("file:"))
            self.assertEqual(dialog._pdf_temp_path, "")
            dialog.close()
            self.assertTrue(os.path.exists(pdf))
            text = os.path.join(folder, "a.txt")
            Path(text).write_text("x")
            self.assertEqual(self.placeholder(self.make(local_file_path=text)), "T:task_files_preview_unsupported")
            self.assertEqual(self.placeholder(self.make(local_file_path=os.path.join(folder, "gone.pdf"))), failed("gone.pdf"))
            with patch.object(Dialog, "PDF_PREVIEW_MAX_BYTES", 2):
                self.assertEqual(self.placeholder(self.make(local_file_path=pdf)), "T:task_files_preview_too_large")
            with patch.dict(sys.modules, {"qgis.PyQt.QtWebEngineWidgets": None}):
                self.assertEqual(self.placeholder(self.make(local_file_path=pdf)), "T:task_files_preview_unsupported")
            with patch.object(Dialog, "_load_pdf_webengine_preview", return_value=False):
                self.assertEqual(self.placeholder(self.make(local_file_path=pdf)), failed("a.pdf"))
        self.fetch.assert_not_called()


class LazyImageTest(_Base):
    def setUp(self):
        super().setUp()
        self.start = self.p(preview_module, "start_worker", return_value=object())
        self.p(preview_module.QTimer, "singleShot")

    def test_lazy_image_waits_then_loads_on_a_worker(self):
        dialog = self.make({"uuid": "u", "ext": "png"}, lazy=True)
        self.assertEqual(self.placeholder(dialog), "T:loading")
        self.fetch.assert_not_called()
        dialog._start_lazy_image_preview_load()
        self.start.assert_called_once()
        worker = self.start.call_args.args[0]
        self.assertIsInstance(worker, workers.FunctionWorker)
        dialog._start_lazy_image_preview_load()
        self.start.assert_called_once()
        dialog._fetch_image_preview_payload("u")
        self.fetch.assert_called_once_with("u", max_bytes=25 * 1024 * 1024)
        dialog._handle_lazy_image_preview_loaded({"content": png_bytes()})
        self.assertIsInstance(self.content(dialog), QScrollArea)
        dialog._handle_lazy_image_preview_loaded("x")
        self.assertEqual(self.placeholder(dialog), failed("u"))
        dialog._handle_lazy_image_preview_error("boom")
        self.assertEqual(self.placeholder(dialog), failed("u"))
        dialog._cleanup_preview_worker()
        self.assertIsNone(dialog._preview_thread)

    def test_lazy_only_for_remote_images(self):
        self.fetch.return_value = {"content": b"abc"}
        self.assertIsInstance(self.content(self.make({"uuid": "u", "ext": "txt"}, lazy=True)), QPlainTextEdit)
        dialog = self.make({"ext": "png"}, lazy=True)
        dialog._start_lazy_image_preview_load()
        self.start.assert_not_called()
        self.assertEqual(self.placeholder(dialog), failed("-"))


class OpenExternallyTest(_Base):
    def setUp(self):
        super().setUp()
        self.p(Dialog, "_load_preview")
        self.ask = self.p(ModernMessageDialog, "ask_choice_modern", return_value="T:Yes")
        self.open_default = self.p(Dialog, "open_in_default_application", return_value=True)

    def test_blocked_type_warns_on_the_dialog(self):
        dialog = self.make({"uuid": "u", "fileName": "a.exe", "ext": "exe"})
        dialog._open_externally()
        self.assertIs(self.warning.call_args.kwargs["parent"], dialog)
        self.ask.assert_not_called()

    def test_confirmation_then_open(self):
        dialog = self.make({"uuid": "u", "fileName": "a.pdf", "ext": "pdf"}, local_title="Plaan")
        dialog._open_externally()
        args, kwargs = self.ask.call_args
        self.assertEqual(args[0], "T:confirm")
        self.assertIn("Plaan", args[1])
        self.assertEqual((kwargs["buttons"], kwargs["default"], kwargs["cancel"]), (["T:Yes", "T:No"], "T:No", "T:No"))
        self.open_default.assert_called_once_with(file_info=dialog._file_info, local_file_path="", user_confirmed=True)
        self.warning.assert_not_called()
        self.ask.return_value = "T:No"
        dialog._open_externally()
        self.assertEqual(self.open_default.call_count, 1)

    def test_failed_open_warns(self):
        self.open_default.return_value = False
        dialog = self.make({"uuid": "u", "fileName": "a.pdf", "ext": "pdf"})
        dialog._open_externally()
        self.assertEqual(self.warning.call_args.args[0], "T:Error")
        self.assertIn("task_files_open_failed", self.warning.call_args.args[1])


class DefaultApplicationTest(_Base):
    INFO = {"uuid": "u", "fileName": "a.pdf", "ext": "pdf"}

    def test_needs_confirmation_and_an_allowed_type(self):
        link = self.p(APIModuleActions, "create_file_download_link", return_value="https://d")
        start = self.p(os, "startfile", create=True)
        self.assertFalse(Dialog.open_in_default_application(file_info=self.INFO))
        self.assertFalse(Dialog.open_in_default_application(local_file_path=__file__.replace(".py", ".pdf")))
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as handle:
            name = handle.name
        self.addCleanup(os.remove, name)
        self.assertFalse(Dialog.open_in_default_application(local_file_path=name))
        link.assert_not_called()
        start.assert_not_called()
        self.assertFalse(Dialog.open_in_default_application(file_info={"uuid": "u", "ext": "exe"}, user_confirmed=True))

    def test_local_file_opens_directly(self):
        with tempfile.TemporaryDirectory() as folder:
            path = os.path.join(folder, "a.pdf")
            Path(path).write_bytes(b"x")
            with patch.object(os, "startfile", create=True) as start:
                self.assertTrue(Dialog.open_in_default_application(local_file_path=path, user_confirmed=True))
            start.assert_called_once_with(path)
            self.assertFalse(Dialog.open_in_default_application(local_file_path=path + "x.pdf", user_confirmed=True))
        with patch.object(os, "startfile", side_effect=OSError, create=True), \
                patch.object(QDesktopServices, "openUrl", return_value=False):
            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as handle:
                name = handle.name
            self.addCleanup(os.remove, name)
            self.assertFalse(Dialog.open_in_default_application(local_file_path=name, user_confirmed=True))

    def test_remote_file_is_downloaded_to_a_temp_file_first(self):
        response = Mock()
        response.iter_content.return_value = [b"ab", b"", b"c"]
        response.__enter__ = Mock(return_value=response)
        response.__exit__ = Mock(return_value=False)
        self.p(APIModuleActions, "create_file_download_link", return_value="https://d")
        get = self.p(requests, "get", return_value=response)
        start = self.p(os, "startfile", create=True)
        self.assertTrue(Dialog.open_in_default_application(file_info=self.INFO, user_confirmed=True))
        get.assert_called_once_with("https://d", stream=True, timeout=120)
        path = start.call_args.args[0]
        self.addCleanup(lambda: os.path.exists(path) and os.remove(path))
        self.assertTrue(path.endswith(".pdf"))
        self.assertEqual(Path(path).read_bytes(), b"abc")
        self.assertIn(path, external_open.EXTERNAL_TEMP_FILES)

    def test_remote_download_guards(self):
        link = self.p(APIModuleActions, "create_file_download_link", return_value="")
        self.assertEqual(external_open.materialize_remote_file_to_temp({"ext": "pdf"}, allowed_extension="pdf"), "")
        self.assertEqual(external_open.materialize_remote_file_to_temp(self.INFO, allowed_extension="docx"), "")
        link.assert_not_called()
        self.assertEqual(external_open.materialize_remote_file_to_temp(self.INFO, allowed_extension="pdf"), "")
        link.assert_called_once_with("u")

    def test_forgotten_temp_files_are_dropped(self):
        with patch.object(external_open, "EXTERNAL_TEMP_FILES", {"", "C:/nope/gone.pdf", __file__}):
            external_open.cleanup_missing_temp_paths()
            self.assertEqual(external_open.EXTERNAL_TEMP_FILES, {__file__})


if __name__ == "__main__":
    unittest.main()
