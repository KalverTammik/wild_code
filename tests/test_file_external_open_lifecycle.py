"""Open externally: the plugin-owned temp folder and its age-based cleanup, the background
download with progress and cancel, the PDF dialog without WebEngine PDF support, and the
cleanup call in the plugin unload hook.

Every network call, message dialog and os.startfile/QDesktopServices call is patched."""
from __future__ import annotations

import os
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
PLUGIN_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLUGIN_ROOT.parent))

import requests
from qgis.core import QgsApplication
from qgis.PyQt.QtCore import QCoreApplication, QEvent

from Kavitro_dev.languages.language_manager import LanguageManager
from Kavitro_dev.languages.translation_keys import TranslationKeys
from Kavitro_dev.Logs.python_fail_logger import PythonFailLogger
from Kavitro_dev.python import workers
from Kavitro_dev.python.api_actions import APIModuleActions
from Kavitro_dev.ui.messages_helper import ModernMessageDialog
from Kavitro_dev.ui.theme_manager import ThemeManager
from Kavitro_dev.widgets.DataDisplayWidgets import TaskFilePreviewDialog as preview_module
from Kavitro_dev.widgets.DataDisplayWidgets import task_file_external_open as external_open
from Kavitro_dev.widgets.DataDisplayWidgets.TaskFilePreviewDialog import TaskFilePreviewDialog as Dialog

_APP = QgsApplication.instance() or QgsApplication([], False)
if QgsApplication.instance() is _APP:
    QgsApplication.initQgis()

INFO = {"uuid": "u", "fileName": "a.pdf", "ext": "pdf"}


def tr(key, **kwargs):
    text = LanguageManager().translate(key)
    return text.format(**kwargs) if kwargs else text


def fake_response(chunks, length=None):
    response = Mock()
    response.iter_content.return_value = chunks
    response.headers = {"Content-Length": str(length)} if length is not None else {}
    response.__enter__ = Mock(return_value=response)
    response.__exit__ = Mock(return_value=False)
    return response


def wait_until(condition, seconds=5.0):
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        QCoreApplication.processEvents()
        if condition():
            return True
        time.sleep(0.01)
    return condition()


class _Case(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.p(tempfile, "tempdir", folder.name)
        self.log = self.p(PythonFailLogger, "log")
        self.log_exception = self.p(PythonFailLogger, "log_exception")
        self.warning = self.p(ModernMessageDialog, "show_warning")
        self.ask = self.p(ModernMessageDialog, "ask_choice_modern", return_value=tr(TranslationKeys.YES))
        self.p(ThemeManager, "apply_module_style")
        self.p(APIModuleActions, "user_display_name", return_value="Jane")
        self.fetch = self.p(APIModuleActions, "fetch_file_preview_payload", return_value=None)
        self.link = self.p(APIModuleActions, "create_file_download_link", return_value="https://d")
        self.get = self.p(requests, "get", side_effect=AssertionError("unexpected network call"))
        self.startfile = self.p(os, "startfile", create=True)
        self.addCleanup(lambda: QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete))

    def p(self, target, name, *args, **kwargs):
        patcher = patch.object(target, name, *args, **kwargs)
        mock = patcher.start()
        self.addCleanup(patcher.stop)
        return mock

    def folder(self):
        return external_open.external_temp_folder()

    def put(self, name, age_seconds=0.0, content=b"x"):
        os.makedirs(self.folder(), exist_ok=True)
        path = os.path.join(self.folder(), name)
        Path(path).write_bytes(content)
        stamp = time.time() - age_seconds
        os.utime(path, (stamp, stamp))
        return path


class TempFolderCleanupTest(_Case):
    OLD = external_open.EXTERNAL_TEMP_MAX_AGE_SECONDS + 60

    def test_folder_is_plugin_owned_and_inside_the_system_temp(self):
        self.assertEqual(self.folder(), os.path.join(tempfile.gettempdir(), "Kavitro_files"))
        handle, path = external_open.create_external_temp_file(".pdf")
        with handle:
            handle.write(b"%PDF")
        self.assertEqual(os.path.dirname(path), self.folder())
        self.assertTrue(os.path.basename(path).startswith(external_open.EXTERNAL_TEMP_PREFIX))

    def test_only_old_plugin_files_are_removed(self):
        old = self.put("kavitro_old.pdf", self.OLD)
        young = self.put("kavitro_young.pdf", 5)
        foreign = self.put("someone_else.pdf", self.OLD)
        os.makedirs(os.path.join(self.folder(), "kavitro_dir"))
        self.assertEqual(external_open.cleanup_external_temp_files(), 1)
        self.assertFalse(os.path.exists(old))
        self.assertTrue(os.path.exists(young))
        self.assertTrue(os.path.exists(foreign))
        self.assertTrue(os.path.isdir(os.path.join(self.folder(), "kavitro_dir")))

    def test_a_file_still_open_elsewhere_is_skipped_and_logged(self):
        locked = self.put("kavitro_locked.pdf", self.OLD)
        other = self.put("kavitro_other.pdf", self.OLD)
        real_remove = os.remove

        def remove(path):
            if os.path.basename(path) == "kavitro_locked.pdf":
                raise PermissionError("in use")
            real_remove(path)

        with patch.object(os, "remove", side_effect=remove):
            self.assertEqual(external_open.cleanup_external_temp_files(), 1)
        self.assertTrue(os.path.exists(locked))
        self.assertFalse(os.path.exists(other))
        self.assertEqual(self.log.call_args.args[0], "task_file_temp_file_locked")
        self.assertEqual(self.log.call_args.kwargs["extra"], {"error_type": "PermissionError", "name": "kavitro_locked.pdf"})

    def test_cleanup_never_raises(self):
        self.assertEqual(external_open.cleanup_external_temp_files(), 0)  # no folder yet
        self.put("kavitro_a.pdf", self.OLD)
        with patch.object(os, "scandir", side_effect=RuntimeError("boom")):
            self.assertEqual(external_open.cleanup_external_temp_files(), 0)
        self.assertEqual(self.log_exception.call_args.kwargs["event"], "task_file_temp_cleanup_failed")

    def test_a_new_download_first_removes_old_files(self):
        old = self.put("kavitro_old.pdf", self.OLD)
        self.get.side_effect = None
        self.get.return_value = fake_response([b"ab"])
        path = external_open.materialize_remote_file_to_temp(INFO, allowed_extension="pdf")
        self.assertFalse(os.path.exists(old))
        self.assertEqual(Path(path).read_bytes(), b"ab")

    def test_pdf_preview_file_lives_in_the_same_folder_and_goes_on_close(self):
        self.p(Dialog, "_load_preview")
        dialog = Dialog(file_info=INFO)
        self.addCleanup(dialog.deleteLater)
        path = dialog._write_pdf_temp_file(b"%PDF")
        self.assertEqual(os.path.dirname(path), self.folder())
        dialog.accept()  # **Close** does not send a close event
        self.assertFalse(os.path.exists(path))

    def test_closing_the_dialog_runs_the_age_cleanup(self):
        self.p(Dialog, "_load_preview")
        old = self.put("kavitro_old.pdf", self.OLD)
        young = self.put("kavitro_young.pdf", 1)
        dialog = Dialog(file_info=INFO)
        self.addCleanup(dialog.deleteLater)
        dialog.reject()
        self.assertFalse(os.path.exists(old))
        self.assertTrue(os.path.exists(young))


class BackgroundDownloadTest(_Case):
    def test_progress_reports_bytes_and_the_total(self):
        self.get.side_effect = None
        self.get.return_value = fake_response([b"ab", b"", b"cde"], length=5)
        seen = []
        path = external_open.materialize_remote_file_to_temp(
            INFO, allowed_extension="pdf", progress=lambda done, total: seen.append((done, total)))
        self.assertEqual(seen, [(0, 5), (2, 5), (5, 5)])
        self.assertEqual(Path(path).read_bytes(), b"abcde")
        self.get.assert_called_once_with("https://d", stream=True, timeout=external_open.DOWNLOAD_TIMEOUT)

    def test_size_from_file_info_when_the_server_sends_none(self):
        self.get.side_effect = None
        self.get.return_value = fake_response([b"ab"])
        seen = []
        external_open.materialize_remote_file_to_temp(
            dict(INFO, size="9"), allowed_extension="pdf", progress=lambda d, t: seen.append(t))
        self.assertEqual(set(seen), {9})

    def test_cancel_mid_download_removes_the_partial_file(self):
        cancel = threading.Event()

        def chunks():
            yield b"ab"
            cancel.set()
            yield b"cd"

        self.get.side_effect = None
        self.get.return_value = fake_response(chunks())
        seen = []
        self.assertEqual(
            external_open.materialize_remote_file_to_temp(
                INFO, allowed_extension="pdf", cancel_event=cancel, progress=lambda d, t: seen.append(d)), "")
        self.assertEqual(seen, [0, 2])  # stopped at the chunk after the cancel
        self.assertEqual(os.listdir(self.folder()), [])

    def test_cancel_before_start_sends_no_request(self):
        cancel = threading.Event()
        cancel.set()
        self.assertEqual(
            external_open.materialize_remote_file_to_temp(INFO, allowed_extension="pdf", cancel_event=cancel), "")
        self.link.assert_not_called()
        self.get.assert_not_called()


class DialogDownloadTest(_Case):
    def setUp(self):
        super().setUp()
        self.p(Dialog, "_load_preview")
        self.open_local = self.p(preview_module, "open_local_path", return_value=True)
        self.release = threading.Event()
        self.addCleanup(self.release.set)

    def make(self, info=INFO):
        dialog = Dialog(file_info=info)
        self.addCleanup(dialog.deleteLater)
        return dialog

    def slow_download(self, result="C:/tmp/kavitro_x.pdf"):
        def download(file_info, *, allowed_extension, cancel_event, progress):
            progress(3, None)
            self.release.wait(5)
            return "" if cancel_event.is_set() else result
        return self.p(preview_module, "materialize_remote_file_to_temp", side_effect=download)

    def idle(self):
        return wait_until(lambda: not workers._ACTIVE_THREADS)

    def test_download_runs_in_the_background_and_then_opens_the_file(self):
        download = self.slow_download()
        dialog = self.make(dict(INFO, size=2048))
        dialog._open_externally()
        self.assertTrue(dialog._cancel_download_button.isVisibleTo(dialog))
        self.assertFalse(dialog._open_external_button.isEnabled())
        self.assertEqual(dialog._notice_label.text(),
                         tr(TranslationKeys.TASK_FILES_EXTERNAL_DOWNLOADING, done="0 B", total="2.0 KB"))
        self.assertTrue(wait_until(lambda: download.called))
        dialog._update_download_progress()
        self.assertEqual(dialog._notice_label.text(),
                         tr(TranslationKeys.TASK_FILES_EXTERNAL_DOWNLOADING_NO_SIZE, done="3 B"))
        self.open_local.assert_not_called()
        self.release.set()
        self.assertTrue(wait_until(lambda: self.open_local.called))
        self.open_local.assert_called_once_with("C:/tmp/kavitro_x.pdf")
        self.assertFalse(dialog._cancel_download_button.isVisibleTo(dialog))
        self.assertTrue(dialog._open_external_button.isEnabled())
        self.assertTrue(dialog._notice_label.isHidden())
        self.warning.assert_not_called()
        self.assertTrue(self.idle())

    def test_progress_text_with_a_known_size(self):
        self.slow_download()
        dialog = self.make(dict(INFO, size=2048))
        dialog._open_externally()
        self.assertEqual(dialog._notice_label.text(),
                         tr(TranslationKeys.TASK_FILES_EXTERNAL_DOWNLOADING, done="0 B", total="2.0 KB"))
        self.release.set()
        self.assertTrue(self.idle())

    def test_failed_download_warns(self):
        self.p(preview_module, "materialize_remote_file_to_temp", return_value="")
        dialog = self.make()
        dialog._open_externally()
        self.assertTrue(wait_until(lambda: self.warning.called))
        self.assertEqual(self.warning.call_args.args[1], f"<p>{tr(TranslationKeys.TASK_FILES_OPEN_FAILED, name='a.pdf')}</p>")
        self.open_local.assert_not_called()
        self.assertTrue(dialog._open_external_button.isEnabled())
        self.assertTrue(self.idle())

    def test_worker_error_warns_without_raising(self):
        self.p(preview_module, "materialize_remote_file_to_temp", side_effect=RuntimeError("boom"))
        dialog = self.make()
        dialog._open_externally()
        self.assertTrue(wait_until(lambda: self.warning.called))
        self.assertEqual(self.warning.call_args.args[1], f"<p>{tr(TranslationKeys.TASK_FILES_OPEN_FAILED, name='a.pdf')}</p>")
        self.assertTrue(self.idle())

    def test_cancel_stops_waiting_and_ignores_the_result(self):
        self.slow_download()
        dialog = self.make()
        dialog._open_externally()
        state = dialog._download_state
        dialog._cancel_download_button.click()
        self.assertTrue(state.cancel_event.is_set())
        self.assertEqual(dialog._notice_label.text(), tr(TranslationKeys.TASK_FILES_EXTERNAL_DOWNLOAD_CANCELLED))
        self.assertTrue(dialog._open_external_button.isEnabled())
        self.assertFalse(dialog._cancel_download_button.isVisibleTo(dialog))
        self.release.set()
        self.assertTrue(self.idle())
        self.open_local.assert_not_called()
        self.warning.assert_not_called()

    def test_closing_the_dialog_cancels_the_download(self):
        self.slow_download()
        dialog = self.make()
        dialog._open_externally()
        state = dialog._download_state
        dialog.accept()
        self.assertTrue(state.cancel_event.is_set())
        self.release.set()
        self.assertTrue(self.idle())
        self.open_local.assert_not_called()

    def test_local_files_open_without_a_worker(self):
        start = self.p(preview_module, "start_worker")
        with tempfile.TemporaryDirectory() as folder:
            path = os.path.join(folder, "a.pdf")
            Path(path).write_bytes(b"%PDF")
            dialog = Dialog(local_file_path=path)
            self.addCleanup(dialog.deleteLater)
            dialog._open_externally()
        start.assert_not_called()
        self.startfile.assert_called_once_with(path)


class PdfWithoutWebEngineTest(_Case):
    def test_dialog_opens_and_offers_open_externally(self):
        self.p(Dialog, "embedded_pdf_runtime_support", return_value=(False, {"qt": "5.15.3", "pyqt": "5.15"}))
        start = self.p(preview_module, "start_worker", return_value=object())
        dialog = Dialog.open_preview(file_info=INFO)
        self.addCleanup(dialog.deleteLater)
        self.assertIsInstance(dialog, Dialog)
        label = dialog._content_layout.itemAt(0).widget()
        self.assertEqual(label.text(), tr(TranslationKeys.TASK_FILES_PDF_PREVIEW_UNAVAILABLE, qt_version="5.15.3"))
        self.fetch.assert_not_called()
        self.assertTrue(dialog._open_external_button.isEnabled())
        dialog._open_external_button.click()
        start.assert_called_once()
        self.warning.assert_not_called()


class UnloadHookTest(unittest.TestCase):
    def test_unload_cleans_the_temp_folder(self):
        from Kavitro_dev import main

        plugin = main.WildCodePlugin(Mock())
        with patch.object(main, "cleanup_external_temp_files") as cleanup, \
                patch.object(main, "stop_all_workers"), \
                patch.object(main.PluginDialog, "get_instance", return_value=None), \
                patch.object(plugin._crash_logger, "stop"):
            plugin.unload()
        cleanup.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()
