"""Contracts that replaced getattr/hasattr fallbacks: request tokens, the token owner lookup, the works page copy."""
from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
if os.environ.get("QGIS_PREFIX_PATH"):
    sys.path.append(str(Path(os.environ["QGIS_PREFIX_PATH"]) / "python" / "plugins"))

from PyQt5.QtCore import QCoreApplication, QEvent
from PyQt5.QtWidgets import QApplication, QWidget

from Kavitro_dev.modules.Settings import SettingsUI as settings_module
from Kavitro_dev.modules.Settings.SettingsUI import SettingsModule
from Kavitro_dev.modules.works.works_list_service import WorksFeedLogic
from Kavitro_dev.ui.mixins.token_mixin import TokenMixin
from Kavitro_dev.widgets.Filters.BaseSingleFilterWidget import BaseSingleFilterWidget
from Kavitro_dev.widgets.Filters.StatusFilterWidget import StatusFilterWidget
from Kavitro_dev.widgets.Filters.TypeFilterWidget import TypeFilterWidget


class _Settings(TokenMixin):
    """The parts of SettingsModule the user fetch uses, without its cards."""

    _refresh_user_info = SettingsModule._refresh_user_info
    _handle_user_worker_success = SettingsModule._handle_user_worker_success
    _handle_user_worker_error = SettingsModule._handle_user_worker_error
    _clear_user_worker_refs = SettingsModule._clear_user_worker_refs

    def __init__(self) -> None:
        TokenMixin.__init__(self)
        self._user_fetch_thread = None
        self._user_fetch_worker = None
        self._user_fetch_token = None
        self._on_user_payload_ready = Mock()


class UserFetchTokenTest(unittest.TestCase):
    def setUp(self) -> None:
        self.settings = _Settings()
        self.settings.mark_activated()
        start = patch.object(settings_module.SettingsUserFetchService, "start_user_fetch", return_value=(Mock(), Mock()))
        self.start = start.start()
        self.addCleanup(start.stop)

    def test_the_answer_to_the_current_request_is_used(self) -> None:
        self.settings._refresh_user_info()

        self.settings._handle_user_worker_success({"name": "Mari"})

        self.settings._on_user_payload_ready.assert_called_once_with({"name": "Mari"})

    def test_an_answer_after_leaving_settings_is_dropped(self) -> None:
        self.settings._refresh_user_info()
        self.settings.mark_deactivated()
        self.settings.mark_activated()

        self.settings._handle_user_worker_success({"name": "Mari"})

        self.settings._on_user_payload_ready.assert_not_called()

    def test_the_token_is_kept_by_the_module_not_written_onto_the_worker(self) -> None:
        self.settings._refresh_user_info()

        self.assertEqual(self.settings._user_fetch_token, self.settings._active_token)
        self.assertNotIn("active_token", self.start.call_args.kwargs)


class _Owner(TokenMixin, QWidget):
    def __init__(self) -> None:
        QWidget.__init__(self)
        TokenMixin.__init__(self)


class FilterTokenOwnerTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self) -> None:
        self.owner = _Owner()
        self.addCleanup(self._delete, self.owner)
        self.child = QWidget(QWidget(self.owner))

    @staticmethod
    def _delete(widget: QWidget) -> None:
        widget.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)

    def ask(self, widget_class, child: QWidget, token: int | None) -> bool:
        # The lookup only needs the widget's place in the tree.
        fake = SimpleNamespace(parent=child.parent, _is_widget_alive=lambda: True)
        return widget_class._is_token_active(fake, token)

    def test_the_nearest_owner_decides(self) -> None:
        token = self.owner.mark_activated()
        for widget_class in (BaseSingleFilterWidget, StatusFilterWidget, TypeFilterWidget):
            with self.subTest(widget=widget_class.__name__):
                self.assertTrue(self.ask(widget_class, self.child, token))
                self.assertFalse(self.ask(widget_class, self.child, token - 1))

    def test_a_deactivated_owner_rejects_its_old_token(self) -> None:
        token = self.owner.mark_activated()
        self.owner.mark_deactivated()
        for widget_class in (BaseSingleFilterWidget, StatusFilterWidget, TypeFilterWidget):
            with self.subTest(widget=widget_class.__name__):
                self.assertFalse(self.ask(widget_class, self.child, token))

    def test_without_an_owner_every_token_is_current(self) -> None:
        orphan = QWidget()
        self.addCleanup(self._delete, orphan)
        for widget_class in (BaseSingleFilterWidget, StatusFilterWidget, TypeFilterWidget):
            with self.subTest(widget=widget_class.__name__):
                self.assertTrue(self.ask(widget_class, QWidget(orphan), 7))


class WorksPageCopyTest(unittest.TestCase):
    def setUp(self) -> None:
        client = patch("Kavitro_dev.feed.FeedLogic.APIClient")
        client.start()
        self.addCleanup(client.stop)
        self.feed = WorksFeedLogic("task", "ListFilteredTasks.graphql", root_field="tasks")

    def test_the_page_read_into_the_copy_becomes_the_feeds(self) -> None:
        copy = self.feed.snapshot()
        copy.end_cursor = "p2"
        copy.has_more = True
        copy.total_count = 12
        copy._sort_seen_ids.add("41")
        self.feed.is_loading = True

        self.feed.accept_snapshot(copy)

        self.assertEqual((self.feed.end_cursor, self.feed.has_more, self.feed.total_count), ("p2", True, 12))
        self.assertEqual(self.feed._sort_seen_ids, {"41"})
        self.assertFalse(self.feed.is_loading)


if __name__ == "__main__":
    unittest.main()
