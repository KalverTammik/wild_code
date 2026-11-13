"""Where a failed request reaches the user, it reads as translated short text, never as "[WC-API][graphql] ...".

The search box on 2026-11-13 showed '[WC-API][graphql] Variable "$input" got invalid val...'.
"""
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
from PyQt5.QtWidgets import QWidget
from qgis.core import QgsApplication

from Kavitro_dev.feed import FeedLogic as feed_module
from Kavitro_dev.languages.language_manager import LanguageManager
from Kavitro_dev.languages.translation_keys import TranslationKeys
from Kavitro_dev.utils.api_error_handling import ApiError, ApiErrorKind
from Kavitro_dev.utils.search.UnifiedSearchController import UnifiedSearchController
from Kavitro_dev.widgets.Filters.StatusFilterWidget import StatusFilterWidget
from Kavitro_dev.widgets.Filters.TagsFilterWidget import TagsFilterWidget
from Kavitro_dev.widgets.Filters.TypeFilterWidget import TypeFilterWidget


SERVER_TEXT = 'Variable "$input" got invalid value "ORDINANCES" at "input.types[7]"'
GRAPHQL_ERROR = ApiError(ApiErrorKind.GRAPHQL, SERVER_TEXT)
CARRIED_TEXT = str(GRAPHQL_ERROR)  # what FunctionWorker.error delivers


def translated(key) -> str:
    return LanguageManager().translate(key)


class UserFacingCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QgsApplication.instance() or QgsApplication([], False)

    def setUp(self) -> None:
        for name in ("log", "log_exception"):
            patcher = patch.object(feed_module.PythonFailLogger, name)
            patcher.start()
            self.addCleanup(patcher.stop)

    def assertReadable(self, text: str) -> None:
        self.assertNotIn("WC-API", text)
        self.assertNotIn("ORDINANCES", text)


class SearchErrorTest(UserFacingCase):
    def test_failed_search_shows_the_translated_text(self) -> None:
        controller = UnifiedSearchController()
        shown = Mock()
        controller.searchFailed.connect(shown)

        controller._handle_error(CARRIED_TEXT, None, controller._request_token)

        shown.assert_called_once_with(translated(TranslationKeys.SERVER_REQUEST_NOT_COMPLETED))

    def test_empty_error_falls_back_to_search_failed(self) -> None:
        controller = UnifiedSearchController()
        shown = Mock()
        controller.searchFailed.connect(shown)

        controller._handle_error("", None, controller._request_token)

        shown.assert_called_once_with(translated(TranslationKeys.SEARCH_FAILED))


class FeedErrorTest(UserFacingCase):
    def test_failed_list_page_keeps_the_kind_and_shows_translated_text(self) -> None:
        logic = feed_module.UnifiedFeedLogic("contract", "ListFilteredContracts.graphql")
        logic.api_client = Mock()
        logic.api_client.send_query.side_effect = GRAPHQL_ERROR

        self.assertEqual(logic.fetch_next_batch(), [])

        self.assertIs(logic.last_error, GRAPHQL_ERROR)
        self.assertEqual(logic.last_error_kind, ApiErrorKind.GRAPHQL)
        self.assertEqual(logic.last_error_message, translated(TranslationKeys.SERVER_REQUEST_NOT_COMPLETED))
        self.assertFalse(logic.is_loading)

    def test_expired_session_text_stays_as_the_client_worded_it(self) -> None:
        logic = feed_module.UnifiedFeedLogic("contract", "ListFilteredContracts.graphql")
        logic.api_client = Mock()
        logic.api_client.send_query.side_effect = ApiError(
            ApiErrorKind.AUTH, translated(TranslationKeys.SESSION_EXPIRED)
        )

        logic.fetch_next_batch()

        self.assertEqual(logic.last_error_kind, ApiErrorKind.AUTH)
        self.assertEqual(logic.last_error_message, translated(TranslationKeys.SESSION_EXPIRED))


class FilterErrorTest(UserFacingCase):
    def setUp(self) -> None:
        super().setUp()
        self.host = QWidget()
        self.addCleanup(self.delete_host)
        lang = LanguageManager("et")
        settings = Mock()
        settings.load_module_preference_ids.return_value = []
        self.status = StatusFilterWidget("contract", self.host, auto_load=False, lang_manager=lang, settings_logic=settings)
        self.types = TypeFilterWidget("contract", self.host, auto_load=False, settings_logic=settings)
        self.tags = TagsFilterWidget("contract", lang, self.host, auto_load=False, settings_logic=settings)

    def delete_host(self) -> None:
        self.host.hide()
        self.host.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)

    def fail(self, widget) -> None:
        widget._load_request_id = 4
        widget._handle_load_error(CARRIED_TEXT, None, 4)

    def test_filters_show_the_start_of_the_translated_text(self) -> None:
        start = translated(TranslationKeys.SERVER_REQUEST_NOT_COMPLETED)[:20]
        self.fail(self.status)
        self.fail(self.types)
        self.fail(self.tags)
        shown = {
            "status": self.status.selector._display_override,
            "type": self.types.group_combo.itemText(0),
            "tags": self.tags.combo.itemText(0),
        }
        for name, text in shown.items():
            with self.subTest(filter=name):
                self.assertReadable(text)
                self.assertIn(start, text)


if __name__ == "__main__":
    unittest.main()
