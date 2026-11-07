from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
if os.environ.get("QGIS_PREFIX_PATH"):
    sys.path.append(str(Path(os.environ["QGIS_PREFIX_PATH"]) / "python" / "plugins"))

from PyQt5.QtCore import QCoreApplication, QEvent
from PyQt5.QtWidgets import QApplication, QWidget

from Kavitro_dev.feed.FeedLogic import UnifiedFeedLogic
from Kavitro_dev.languages.language_manager import LanguageManager
from Kavitro_dev.modules.coordination.CoordinationModule import CoordinationModule
from Kavitro_dev.utils.FilterHelpers.FilterHelper import FilterHelper, FilterRefreshService
from Kavitro_dev.utils.url_manager import ModuleSupports
from Kavitro_dev.widgets.Filters.StatusFilterWidget import StatusFilterWidget
from Kavitro_dev.widgets.Filters.TagsFilterWidget import TagsFilterWidget
from Kavitro_dev.widgets.Filters.TypeFilterWidget import TypeFilterWidget
from Kavitro_dev.widgets.HeaderWidget import HeaderWidget


def delete_now(widget: QWidget) -> None:
    widget.hide()
    widget.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)


def running_thread() -> Mock:
    thread = Mock()
    thread.isRunning.return_value = True
    return thread


class CancelPendingLoadContractTest(unittest.TestCase):
    """Every filter widget class carries the worker state cancel_pending_load uses."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self) -> None:
        self.host = QWidget()
        self.addCleanup(delete_now, self.host)
        lang = LanguageManager("et")
        self.widgets = [
            StatusFilterWidget("contract", self.host, auto_load=False, lang_manager=lang),
            TypeFilterWidget("contract", self.host, auto_load=False),
            TagsFilterWidget("contract", lang, self.host, auto_load=False),
        ]

    def test_invalidating_cancel_stops_the_running_load(self) -> None:
        for widget in self.widgets:
            with self.subTest(widget=type(widget).__name__):
                thread = running_thread()
                widget._worker = Mock()
                widget._worker_thread = thread
                request_id = widget._load_request_id
                finished = []
                widget.loadFinished.connect(finished.append)

                FilterHelper.cancel_pending_load(widget, invalidate_request=True)

                self.assertEqual(widget._load_request_id, request_id + 1)
                self.assertIsNone(widget._worker)
                self.assertIsNone(widget._worker_thread)
                thread.quit.assert_called_once()
                self.assertEqual(finished, [False])

    def test_restart_cancel_keeps_the_request_id_and_reports_nothing(self) -> None:
        for widget in self.widgets:
            with self.subTest(widget=type(widget).__name__):
                thread = running_thread()
                widget._worker_thread = thread
                request_id = widget._load_request_id
                finished = []
                widget.loadFinished.connect(finished.append)

                FilterHelper.cancel_pending_load(widget, invalidate_request=False)

                self.assertEqual(widget._load_request_id, request_id)
                self.assertIsNone(widget._worker_thread)
                thread.quit.assert_called_once()
                self.assertEqual(finished, [])


class ModuleFeedContractTest(unittest.TestCase):
    """CoordinationModule creates its feed lazily, so it exercises the whole pipeline."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self) -> None:
        patches = [
            patch("Kavitro_dev.modules.coordination.CoordinationModule.ModuleManager"),
            patch("requests.sessions.Session.request", side_effect=AssertionError("Unexpected network request")),
        ]
        mocks = [p.start() for p in patches]
        for p in patches:
            self.addCleanup(p.stop)
        mocks[0].return_value.getModuleSupports.return_value = (False, False, False, False)
        self.ui = CoordinationModule(language=LanguageManager("et"))
        self.addCleanup(delete_now, self.ui)

    def test_refresh_builds_a_list_feed_from_the_selected_filters(self) -> None:
        self.assertIsNone(self.ui.feed_logic)

        self.ui._refresh_filters(status_ids=["s1"], type_ids=["t1"], tags_ids=["g1"])

        feed = self.ui.feed_logic
        self.assertIsInstance(feed, UnifiedFeedLogic)
        # Type ids are ignored because the patched supports report no type filter.
        self.assertEqual(feed.where, {"AND": [{"column": "STATUS", "operator": "IN", "value": ["s1"]}]})
        self.assertEqual(feed._extra_args, {"whereHas": [{"relation": "TAGS", "mode": "ANY", "ids": ["g1"]}]})
        self.assertEqual(feed._single_item_query_name, CoordinationModule.SINGLE_ITEM_QUERY_FILE)
        self.assertFalse(feed._single_item_mode)

    def test_search_opens_one_item_and_refresh_returns_to_the_list(self) -> None:
        self.ui.init_feed_engine(self.ui.load_next_batch)
        engine = self.ui.feed_load_engine
        engine.buffer.append({"id": "old"})

        with patch.object(engine, "schedule_load") as schedule:
            self.ui.open_item_from_search("coordination", "7", "Title")

        feed = self.ui.feed_logic
        self.assertFalse(engine.has_buffer())
        schedule.assert_called_once()
        self.assertTrue(feed._single_item_mode)
        self.assertEqual(feed._extra_args, {"id": "7"})
        self.assertEqual(feed._single_item_query_name, CoordinationModule.SINGLE_ITEM_QUERY_FILE)

        with patch.object(engine, "schedule_load"):
            self.ui._refresh_filters()

        self.assertIs(self.ui.feed_logic, feed)
        self.assertFalse(feed._single_item_mode)
        self.assertEqual(feed._extra_args, {})

    def test_saved_filter_ids_come_from_the_module_preferences(self) -> None:
        self.ui._settings_logic = Mock()
        self.ui._settings_logic.load_module_preference_ids.return_value = [" a ", "", "b"]

        self.assertEqual(FilterRefreshService.saved_status_ids(self.ui), ["a", "b"])
        self.ui._settings_logic.load_module_preference_ids.assert_called_once_with(
            "coordination", support_key=ModuleSupports.STATUSES.value
        )

    def test_reset_overdue_pills_clears_both_pills(self) -> None:
        pills = self.ui.overdue_pills
        with patch.object(pills, "set_overdue_active") as overdue, patch.object(pills, "set_due_soon_active") as due_soon:
            FilterRefreshService.refresh_filters(self.ui, reset_overdue_pills=True)

        overdue.assert_called_once_with(False)
        due_soon.assert_called_once_with(False)


class SearchControllerParentContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def test_header_owns_the_search_lifecycle_token(self) -> None:
        header = HeaderWidget("Kavitro", Mock(), Mock())
        self.addCleanup(delete_now, header)
        controller = header.search_controller

        header.set_active_token(5)

        self.assertEqual(controller._current_token(), 5)
        self.assertTrue(controller._is_token_active(5))
        self.assertFalse(controller._is_token_active(4))


if __name__ == "__main__":
    unittest.main()
