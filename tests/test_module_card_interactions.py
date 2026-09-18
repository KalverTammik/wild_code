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
sys.path.insert(0, str(Path(__file__).resolve().parent))
qgis_prefix = os.environ.get("QGIS_PREFIX_PATH")
if qgis_prefix:
    sys.path.append(str(Path(qgis_prefix) / "python" / "plugins"))

from PyQt5.QtCore import QCoreApplication, QEvent, QThread, Qt
from PyQt5.QtTest import QTest
from PyQt5.QtGui import QFont, QFontDatabase
from PyQt5.QtWidgets import QApplication, QLabel, QPushButton, QVBoxLayout, QWidget

from property_fixtures import wait_for

from Kavitro_dev.languages.language_manager import LanguageManager
from Kavitro_dev.python.api_actions import APIModuleActions
from Kavitro_dev.python.workers import _ACTIVE_THREADS
from Kavitro_dev.widgets.DataDisplayWidgets.AsyncContentWidget import AsyncContentWidget
from Kavitro_dev.widgets.DataDisplayWidgets.ExtraInfoWidget import ExtraInfoFrame
from Kavitro_dev.widgets.DataDisplayWidgets.MembersView import AvatarBubble, MembersView
from Kavitro_dev.widgets.DataDisplayWidgets.ModuleConfig import ModuleConfigFactory
from Kavitro_dev.widgets.DataDisplayWidgets.TaskDetailOverviewWidget import (
    TaskFilesSummaryWidget, _FilePreviewSquareButton,
)
from Kavitro_dev.widgets.DataDisplayWidgets.TaskFilesDialog import TaskFilesDialog


class ModuleCardInteractionTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])
        if not QFontDatabase().families():
            for filename in ("segoeui.ttf", "segoeuib.ttf"):
                QFontDatabase.addApplicationFont(str(Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts" / filename))
            cls.app.setFont(QFont("Segoe UI", 9))

    def setUp(self):
        self.widgets = []
        self.gates = []
        self.lang = LanguageManager("et")
        self.file_patch = patch.object(APIModuleActions, "get_module_files", return_value=[])
        self.files_api = self.file_patch.start()
        self.description_patch = patch.object(
            ModuleConfigFactory, "_load_single_item_description", return_value="<p>Kirjeldus</p>"
        )
        self.description_api = self.description_patch.start()

    def tearDown(self):
        for gate in self.gates:
            gate.set()
        self.wait_for(lambda: not _ACTIVE_THREADS)
        for widget in self.widgets:
            widget.close()
            widget.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)
        self.app.processEvents()
        ExtraInfoFrame._set_expanded_project_frame(None)
        self.description_patch.stop()
        self.file_patch.stop()

    def wait_for(self, predicate, timeout=3):
        wait_for(self, predicate, timeout=timeout, message="Timed out waiting for UI state")

    def show(self, widget):
        self.widgets.append(widget)
        widget.show()
        self.app.processEvents()
        return widget

    def gate(self):
        gate = threading.Event()
        self.gates.append(gate)
        return gate

    def frame(self):
        host = QWidget()
        layout = QVBoxLayout(host)
        frame = ExtraInfoFrame({"id": "task-1", "name": "Kasutaja määratud nimi"}, "works",
                               lang_manager=self.lang, handle_host=host)
        layout.addWidget(frame)
        host.resize(650, 100)
        self.show(host)
        return frame

    def test_slow_load_keeps_gui_free_and_builds_widgets_on_gui_thread(self):
        gate = self.gate()
        started = threading.Event()
        threads = {}

        def fetch():
            threads["fetch"] = QThread.currentThread()
            started.set()
            gate.wait(3)
            return "Valmis"

        def build(value):
            threads["build"] = QThread.currentThread()
            return QLabel(value)

        widget = self.show(AsyncContentWidget(fetch, build, lang_manager=self.lang))
        self.wait_for(started.is_set)
        self.assertTrue(widget._status.isVisible())
        self.assertIsNone(widget._content)
        gate.set()
        self.wait_for(lambda: widget._content is not None)
        self.assertNotEqual(threads["fetch"], self.app.thread())
        self.assertEqual(threads["build"], self.app.thread())
        self.assertEqual(widget._content.text(), "Valmis")

    def test_failed_detail_can_be_retried_without_recreating_card(self):
        fetch = Mock(side_effect=[RuntimeError("network error"), "Taastatud"])
        widget = self.show(AsyncContentWidget(fetch, QLabel, lang_manager=self.lang))
        self.wait_for(lambda: widget._retry.isVisible())
        self.assertIn("ebaõnnestus", widget._status.text())
        widget._retry.click()
        self.wait_for(lambda: widget._content is not None)
        self.assertEqual(widget._content.text(), "Taastatud")
        self.assertEqual(fetch.call_count, 2)

    def test_deleting_card_during_load_does_not_build_late_widget(self):
        gate = self.gate()
        started = threading.Event()

        def fetch():
            started.set()
            gate.wait(3)
            return "late"

        build = Mock(return_value=None)
        widget = self.show(AsyncContentWidget(fetch, build, lang_manager=self.lang))
        self.wait_for(started.is_set)
        self.widgets.remove(widget)
        widget.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)
        gate.set()
        self.wait_for(lambda: not _ACTIVE_THREADS)
        build.assert_not_called()

    def test_collapsing_during_load_stays_collapsed_and_reuses_result(self):
        gate = self.gate()
        started = threading.Event()

        def description(**kwargs):
            started.set()
            gate.wait(3)
            return "<p>Valmis kirjeldus</p>"

        self.description_api.side_effect = description
        frame = self.frame()
        frame._expand_handle.click()
        self.wait_for(started.is_set)
        self.assertTrue(frame._expand_handle.isChecked())
        self.assertEqual(frame._expand_handle.arrowType(), Qt.UpArrow)
        frame._expand_handle.click()
        gate.set()
        self.wait_for(lambda: not _ACTIVE_THREADS)
        self.wait_for(lambda: frame._detail_container.isHidden())
        self.assertFalse(frame._detail_expanded)
        frame._expand_handle.click()
        self.wait_for(lambda: frame._detail_container.height() > 24)
        self.assertEqual(self.description_api.call_count, 1)
        self.assertEqual(frame._expand_handle.size().width(), 56)
        self.assertEqual(frame._expand_handle.size().height(), 16)

    def test_opening_second_card_collapses_first(self):
        first = self.frame()
        second = self.frame()
        first._expand_handle.click()
        second._expand_handle.click()
        self.assertFalse(first._detail_expanded)
        self.assertFalse(first._expand_handle.isChecked())
        self.assertTrue(second._detail_expanded)

    def test_unassigned_avatar_opens_all_members_and_closes_on_escape(self):
        nodes = [{"id": str(i), "displayName": f"Osaleja {i}"} for i in range(20)]
        view = self.show(MembersView(
            {"members": {"edges": [{"node": node, "responsible": False} for node in nodes]}},
            lang_manager=self.lang,
        ))
        bubbles = view.findChildren(AvatarBubble)
        self.assertEqual(len(bubbles), 1)
        bubble = bubbles[0]
        self.assertEqual(bubble.text(), "")
        self.assertIn("määramata", bubble.toolTip())
        QTest.mouseClick(bubble, Qt.LeftButton)
        popup = bubble._click_popup
        self.assertTrue(popup.isVisible())
        texts = [label.text() for label in popup.findChildren(QLabel)]
        self.assertIn("Osaleja 19", texts)
        QTest.keyClick(popup, Qt.Key_Escape)
        self.assertFalse(popup.isVisible())

    def test_unassigned_avatar_with_no_members_has_an_empty_state(self):
        view = self.show(MembersView({}, lang_manager=self.lang))
        bubble = view.findChild(AvatarBubble)
        QTest.keyClick(bubble, Qt.Key_Return)
        texts = [label.text() for label in bubble._click_popup.findChildren(QLabel)]
        self.assertIn("Liikmeid pole lisatud.", texts)

    def test_file_load_failure_has_inline_retry(self):
        self.files_api.side_effect = [None, []]
        widget = self.show(TaskFilesSummaryWidget(item_id="task-1", lang_manager=self.lang))
        self.wait_for(lambda: widget._retry_button.isVisible())
        widget._retry_button.click()
        self.wait_for(lambda: not widget._loading)
        self.assertFalse(widget._retry_button.isVisible())
        self.assertFalse(widget._all_files_button.isVisible())
        self.assertEqual(self.files_api.call_count, 2)

    def test_all_files_action_receives_full_list_and_thumbnail_is_next_to_name(self):
        files = [{"uuid": str(i), "fileName": f"Pilt {i}.png", "mimeType": "image/png"} for i in range(7)]
        self.files_api.return_value = files
        with patch.object(_FilePreviewSquareButton, "_start_thumbnail_load"):
            widget = self.show(TaskFilesSummaryWidget(item_id="task-1", lang_manager=self.lang))
            self.wait_for(lambda: not widget._loading)
            self.assertEqual(widget._list_layout.count(), 6)  # Five rows and a stretch.
            row_layout = widget._list_layout.itemAt(0).widget().layout()
            self.assertIsInstance(row_layout.itemAt(0).widget(), _FilePreviewSquareButton)
            self.assertEqual(row_layout.itemAt(1).widget().text(), "Pilt 0.png")
            self.assertEqual(widget._all_files_button.text(), "Vaata kõiki faile (7)")
            with patch("Kavitro_dev.widgets.DataDisplayWidgets.TaskDetailOverviewWidget.TaskFilesDialog") as dialog:
                widget._all_files_button.click()
                self.assertEqual(dialog.call_args.kwargs["initial_files"], files)
                dialog.return_value.exec_.assert_called_once()
            self.wait_for(lambda: not widget._loading)

    def test_all_files_dialog_uses_loaded_data_without_another_query(self):
        files = [{"uuid": "one", "fileName": "Fail.pdf"}]
        dialog = self.show(TaskFilesDialog(item_id="task-1", initial_files=files, lang_manager=self.lang))
        self.assertEqual(dialog._table.rowCount(), 1)
        self.files_api.assert_not_called()

    def test_inline_height_follows_asynchronously_loaded_files(self):
        gate = self.gate()

        def fetch_files(*args):
            gate.wait(3)
            return [{"uuid": str(i), "fileName": f"Fail {i}.pdf"} for i in range(6)]

        self.files_api.side_effect = fetch_files
        frame = self.frame()
        frame._expand_handle.click()
        self.wait_for(lambda: frame.findChild(TaskFilesSummaryWidget) is not None)
        QTest.qWait(300)
        loading_height = frame._detail_container.height()
        gate.set()
        self.wait_for(lambda: not _ACTIVE_THREADS)
        self.wait_for(lambda: frame._detail_container.height() > loading_height + 50)
        self.assertEqual(frame._detail_container.maximumHeight(), frame._project_detail_target_height())


class ModuleFilePaginationTest(unittest.TestCase):
    @staticmethod
    def page(start, end, cursor, has_more):
        return {"task": {"files": {
            "edges": [{"node": {"uuid": str(i), "fileName": f"File {i}.pdf"}} for i in range(start, end)],
            "pageInfo": {"endCursor": cursor, "hasNextPage": has_more},
        }}}

    def fetch(self, pages, **kwargs):
        with patch("Kavitro_dev.python.api_actions.GraphQLQueryLoader"), \
                patch("Kavitro_dev.python.api_actions.APIClient") as client:
            client.return_value.send_query.side_effect = pages
            result = APIModuleActions.get_module_files("works", "task-1", **kwargs)
            return result, client.return_value.send_query.call_count

    def test_default_file_list_includes_more_than_two_hundred_files(self):
        pages = [self.page(i, i + 50, str(i), True) for i in range(0, 200, 50)]
        result, count = self.fetch(pages + [self.page(200, 201, "last", False)])
        self.assertEqual(len(result), 201)
        self.assertEqual(count, 5)

    def test_explicit_file_limit_is_preserved(self):
        result, count = self.fetch([self.page(0, 50, "first", True)], limit=2)
        self.assertEqual(len(result), 2)
        self.assertEqual(count, 1)

    def test_broken_pagination_or_missing_item_is_not_reported_as_complete(self):
        cases = [
            [self.page(0, 1, "same", True), self.page(1, 2, "same", True)],
            [self.page(0, 1, "first", True), self.page(1, 1, "next", True)],
            [{"task": None}],
        ]
        for pages in cases:
            with self.subTest(pages=pages):
                result, _count = self.fetch(pages)
                self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
