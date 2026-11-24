"""File upload runs in background workers, one file at a time (audit 09, 2026-11-24).

It used to run in the GUI thread: a long queue froze the window and could not be stopped.
Now the window stays usable, the status line shows progress, Cancel stops after the file
in flight, the first unconfirmed file still stops the queue, and closing drops the queue.
"""
from __future__ import annotations

import os
import sys
import threading
import time
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
if os.environ.get("QGIS_PREFIX_PATH"):
    sys.path.append(str(Path(os.environ["QGIS_PREFIX_PATH"]) / "python" / "plugins"))

from qgis.core import QgsApplication
from qgis.PyQt.QtCore import QCoreApplication

from Kavitro_dev.languages.language_manager import LanguageManager
from Kavitro_dev.languages.translation_keys import TranslationKeys
from Kavitro_dev.widgets.DataDisplayWidgets import TaskFilesDialog as files

PATHS = ["C:/data/a.txt", "C:/data/b.txt", "C:/data/c.txt"]


class UploadQueueTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QgsApplication.instance() or QgsApplication([], False)

    def setUp(self) -> None:
        self.lang = LanguageManager("et")
        self.dialog = files.TaskFilesDialog(item_id="task-1", module_name="works", lang_manager=self.lang,
                                            initial_files=[])
        self.addCleanup(self.dialog.deleteLater)
        self.dialog._load_files = Mock()
        self.workers = []
        patches = {
            "pick": patch.object(files.QFileDialog, "getOpenFileNames", return_value=(list(PATHS), "")),
            "upload": patch.object(files.APIModuleActions, "upload_module_file"),
            "warning": patch.object(files.ModernMessageDialog, "show_warning"),
            "info": patch.object(files.ModernMessageDialog, "show_info"),
            "log": patch.object(files.PythonFailLogger, "log_exception"),
            "start": patch.object(files, "start_worker", side_effect=self._run_in_place),
        }
        self.mocks = {name: p.start() for name, p in patches.items()}
        for p in patches.values():
            self.addCleanup(p.stop)

    def _run_in_place(self, worker):
        self.workers.append(worker)
        worker.run()

    def _text(self, key, **kwargs) -> str:
        return self.lang.translate(key).format(**kwargs)

    def test_all_files_upload_one_request_each_and_report_success(self) -> None:
        self.mocks["upload"].side_effect = [{"uuid": "a"}, {"uuid": "b"}, {"uuid": "c"}]

        self.dialog._upload_files()

        self.assertEqual([c.args[2] for c in self.mocks["upload"].call_args_list], PATHS)
        self.assertEqual(len(self.workers), 3)
        self.assertEqual(self.mocks["info"].call_args.args[1], self._text(TranslationKeys.TASK_FILES_UPLOAD_SUCCESS, count=3))
        self.dialog._load_files.assert_called_once()
        self.assertFalse(self.dialog._uploading)
        self.assertTrue(self.dialog._upload_button.isEnabled())
        self.assertTrue(self.dialog._cancel_upload_button.isHidden())

    def test_progress_and_locked_buttons_while_uploading(self) -> None:
        seen = []

        def upload(_module, _item, path):
            seen.append((self.dialog._count_label.text(), self.dialog._upload_button.isEnabled(),
                         self.dialog._refresh_button.isEnabled(), self.dialog._cancel_upload_button.isHidden()))
            return {"uuid": path}

        self.mocks["upload"].side_effect = upload
        self.dialog._upload_files()

        self.assertEqual(seen[1][0], self._text(TranslationKeys.TASK_FILES_UPLOADING, index=2, total=3, name="b.txt"))
        self.assertTrue(all(not up and not refresh and not hidden for _t, up, refresh, hidden in seen))

    def test_first_unconfirmed_file_stops_the_queue(self) -> None:
        self.mocks["upload"].side_effect = [{"uuid": "a"}, None, {"uuid": "c"}]

        self.dialog._upload_files()

        self.assertEqual(self.mocks["upload"].call_count, 2)
        message = self.mocks["warning"].call_args.args[1]
        self.assertIn("b.txt", message)
        self.assertIn("c.txt", message)
        self.mocks["info"].assert_not_called()

    def test_a_worker_error_counts_as_unconfirmed(self) -> None:
        self.mocks["upload"].side_effect = [RuntimeError("offline")]

        self.dialog._upload_files()

        self.assertEqual(self.mocks["upload"].call_count, 1)
        self.assertIn("a.txt", self.mocks["warning"].call_args.args[1])

    def test_cancel_stops_after_the_file_in_flight(self) -> None:
        def upload(_module, _item, path):
            if path.endswith("a.txt"):
                self.dialog._cancel_upload()
                self.assertEqual(self.dialog._count_label.text(),
                                 self._text(TranslationKeys.TASK_FILES_UPLOAD_CANCELLING, name="a.txt"))
            return {"uuid": path}

        self.mocks["upload"].side_effect = upload
        self.dialog._upload_files()

        self.assertEqual(self.mocks["upload"].call_count, 1)
        self.assertEqual(self.mocks["info"].call_args.args[1], self._text(
            TranslationKeys.TASK_FILES_UPLOAD_CANCELLED, uploaded=1, pending=2, pending_names="b.txt, c.txt"))
        self.mocks["warning"].assert_not_called()
        self.dialog._load_files.assert_called_once()

    def test_closing_drops_the_queue_and_the_result(self) -> None:
        held = []
        self.mocks["start"].side_effect = held.append
        self.mocks["upload"].return_value = {"uuid": "x"}

        self.dialog._upload_files()
        self.assertEqual(len(held), 1)
        self.dialog.reject()

        self.assertFalse(self.dialog._uploading)
        self.assertEqual(self.dialog._upload_queue, [])
        held[0].run()  # the file in flight finishes after the close: nothing more happens
        self.assertEqual(self.mocks["upload"].call_count, 1)
        self.mocks["info"].assert_not_called()
        self.mocks["warning"].assert_not_called()

    def test_a_second_click_during_upload_is_ignored(self) -> None:
        held = []
        self.mocks["start"].side_effect = held.append

        self.dialog._upload_files()
        self.dialog._upload_files()

        self.assertEqual(self.mocks["pick"].call_count, 1)
        self.assertEqual(len(held), 1)

    def test_no_file_chosen_changes_nothing(self) -> None:
        self.mocks["pick"].return_value = ([], "")

        self.dialog._upload_files()

        self.mocks["upload"].assert_not_called()
        self.assertFalse(self.dialog._uploading)
        self.assertTrue(self.dialog._cancel_upload_button.isHidden())

    def test_an_error_while_starting_does_not_escape_and_unlocks(self) -> None:
        self.mocks["start"].side_effect = RuntimeError("thread")

        self.dialog._upload_files()

        self.mocks["log"].assert_called_once()
        self.assertFalse(self.dialog._uploading)
        self.assertTrue(self.dialog._upload_button.isEnabled())


class UploadThreadTest(unittest.TestCase):
    """With the real worker the upload call runs outside the GUI thread."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QgsApplication.instance() or QgsApplication([], False)

    def test_upload_runs_in_a_worker_thread(self) -> None:
        dialog = files.TaskFilesDialog(item_id="task-1", module_name="works", lang_manager=LanguageManager("et"),
                                       initial_files=[])
        self.addCleanup(dialog.deleteLater)
        dialog._load_files = Mock()
        threads = []

        def upload(_module, _item, path):
            threads.append(threading.current_thread())
            return {"uuid": path}

        with patch.object(files.QFileDialog, "getOpenFileNames", return_value=(PATHS[:2], "")), \
                patch.object(files.APIModuleActions, "upload_module_file", side_effect=upload), \
                patch.object(files.ModernMessageDialog, "show_info") as info, \
                patch.object(files.ModernMessageDialog, "show_warning"):
            dialog._upload_files()
            deadline = time.monotonic() + 10
            while dialog._uploading and time.monotonic() < deadline:
                QCoreApplication.processEvents()
                time.sleep(0.01)

        self.assertFalse(dialog._uploading)
        self.assertEqual(len(threads), 2)
        self.assertTrue(all(t is not threading.main_thread() for t in threads))
        info.assert_called_once()


if __name__ == "__main__":
    unittest.main()
