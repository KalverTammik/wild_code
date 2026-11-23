"""Characterization tests for the status, priority and user actions behind APIModuleActions.

They pin which query each action loads, which variables it sends, how it reads the answer
and what it does with an empty or broken answer, a failed request, the cache or the session,
so the actions can move out of python/api_actions.py without changing behaviour. The patch
helper covers every module the code may live in, so the same tests run before and after the
move. The entry point tests at the end describe the layout after the move.
"""
from __future__ import annotations

import ast
import importlib
import os
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, Mock, patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
if os.environ.get("QGIS_PREFIX_PATH"):
    sys.path.append(str(Path(os.environ["QGIS_PREFIX_PATH"]) / "python" / "plugins"))

from qgis.core import QgsApplication

from Kavitro_dev.languages.translation_keys import TranslationKeys
from Kavitro_dev.Logs.python_fail_logger import PythonFailLogger
from Kavitro_dev.python import api_actions as api_actions_module
from Kavitro_dev.python.GraphQLQueryLoader import GraphQLQueryLoader
from Kavitro_dev.python.api_actions import APIModuleActions


# Every module the actions may be defined in; a missing one is skipped, so the tests run
# on the single-file layout as well as on the split one.
CODE_MODULES = (
    "Kavitro_dev.python.api_actions",
    "Kavitro_dev.python.actions.status_actions",
    "Kavitro_dev.python.actions.user_actions",
)
PRIORITY_VALUES = ["URGENT", "HIGH", "MEDIUM", "LOW"]


def _code_modules() -> list:
    modules = []
    for name in CODE_MODULES:
        try:
            modules.append(importlib.import_module(name))
        except ImportError:
            continue
    return modules


def status_node(status_id, name, **extra) -> dict:
    return {"id": status_id, "name": name, "color": "4FBF6B", "type": "open", **extra}


def status_nodes(start: int, end: int) -> list:
    return [status_node(str(i), f"Status {i:03d}", sortOrder=i) for i in range(start, end)]


def status_page(nodes, cursor=None, has_more: bool = False) -> dict:
    return {"statuses": {
        "edges": [{"node": node} for node in nodes],
        "pageInfo": {"endCursor": cursor, "hasNextPage": has_more},
    }}


def user_node(user_id, display_name, **extra) -> dict:
    return {"id": user_id, "displayName": display_name, **extra}


def user_page(nodes, cursor=None, has_more: bool = False) -> dict:
    return {"users": {
        "edges": [{"node": node} for node in nodes],
        "pageInfo": {"endCursor": cursor, "hasNextPage": has_more},
    }}


class LockedSession:
    """A session whose user cannot be stored."""

    loggedInUser = None

    def __setattr__(self, name, value) -> None:
        raise RuntimeError("locked")


class ActionTestCase(unittest.TestCase):
    """Mocked loader, client, language manager, session and logger; no request leaves the process."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QgsApplication.instance() or QgsApplication([], False)

    def setUp(self) -> None:
        self.client = Mock()
        self.loader = Mock()
        self.loader.load_query_by_module.side_effect = self._query_text
        self.lang = Mock()
        self.lang.translate.side_effect = self._translation
        self.session = SimpleNamespace(loggedInUser=None)
        self.session_class = MagicMock()
        self.session_class.return_value = self.session
        self.lang_classes = []
        self.log = self._patch(PythonFailLogger, "log_exception")
        for module in _code_modules():
            for name, instance in (("APIClient", self.client), ("GraphQLQueryLoader", self.loader)):
                if hasattr(module, name):
                    self._patch(module, name, return_value=instance)
            if hasattr(module, "LanguageManager"):
                self.lang_classes.append(self._patch(module, "LanguageManager", return_value=self.lang))
            if hasattr(module, "SessionManager"):
                self._patch(module, "SessionManager", new=self.session_class)

    @staticmethod
    def _query_text(module: str, filename: str) -> str:
        return f"query {module}/{filename}"

    @staticmethod
    def _translation(key) -> str:
        return f"T[{key}]"

    def _patch(self, target, name, **kwargs):
        patcher = patch.object(target, name, **kwargs)
        started = patcher.start()
        self.addCleanup(patcher.stop)
        return started

    def loaded(self) -> list:
        return [tuple(call.args) for call in self.loader.load_query_by_module.call_args_list]

    def sent(self) -> list:
        return [(call.args[0], dict(call.kwargs)) for call in self.client.send_query.call_args_list]

    def reset_calls(self) -> None:
        self.loader.load_query_by_module.reset_mock()
        self.client.send_query.reset_mock()
        self.log.reset_mock()

    def answer(self, responses: dict) -> None:
        """Answer every request by its query text; a list is read one answer per request, an exception is raised."""
        pending = {query: list(value) if isinstance(value, list) else value for query, value in responses.items()}

        def send(query, variables=None, **kwargs):
            value = pending[query]
            if isinstance(value, list):
                value = value.pop(0)
            if isinstance(value, BaseException):
                raise value
            return value

        self.client.send_query.side_effect = send

    def language_managers_built(self) -> int:
        return sum(klass.call_count for klass in self.lang_classes)


class StatusModuleValueTest(ActionTestCase):
    def test_blank_module_has_no_status_module(self) -> None:
        for module in ("", "  ", None):
            with self.subTest(module=module):
                self.assertEqual(APIModuleActions._status_module_value(module), "")

    def test_property_has_its_own_plural(self) -> None:
        self.assertEqual(APIModuleActions._status_module_value("property"), "PROPERTIES")
        self.assertEqual(APIModuleActions._status_module_value(" Property "), "PROPERTIES")

    def test_task_like_modules_share_the_task_statuses(self) -> None:
        for module in ("task", "works", "asbuilt", " Works ", "ASBUILT"):
            with self.subTest(module=module):
                self.assertEqual(APIModuleActions._status_module_value(module), "TASKS")

    def test_other_modules_get_an_upper_case_plural(self) -> None:
        cases = (("project", "PROJECTS"), ("contract", "CONTRACTS"), ("coordination", "COORDINATIONS"),
                 ("easement", "EASEMENTS"), (" Easement ", "EASEMENTS"), ("letter", "LETTERS"),
                 ("nonsense", "NONSENSES"))
        for module, expected in cases:
            with self.subTest(module=module):
                self.assertEqual(APIModuleActions._status_module_value(module), expected)


class GetModuleStatusOptionsTest(ActionTestCase):
    def test_blank_module_returns_nothing_without_a_request(self) -> None:
        for module in ("", "  ", None):
            with self.subTest(module=module):
                self.assertEqual(APIModuleActions.get_module_status_options(module), [])
        self.loader.load_query_by_module.assert_not_called()
        self.client.send_query.assert_not_called()
        self.log.assert_not_called()

    def test_loads_the_module_status_query_filtered_by_the_status_module(self) -> None:
        cases = (("works", "TASKS"), ("asbuilt", "TASKS"), ("property", "PROPERTIES"),
                 ("easement", "EASEMENTS"), (" Project ", "PROJECTS"))
        for module, status_module in cases:
            with self.subTest(module=module):
                self.reset_calls()
                self.client.send_query.return_value = status_page([status_node("1", "Open")])
                self.assertEqual([option["id"] for option in APIModuleActions.get_module_status_options(module)], ["1"])
                self.assertEqual(self.loaded(), [("statuses", "ListModuleStatuses.graphql")])
                self.assertEqual(self.sent(), [("query statuses/ListModuleStatuses.graphql", {"variables": {
                    "first": 50,
                    "after": None,
                    "where": {"column": "MODULE", "operator": "EQ", "value": status_module},
                }})])

    def test_node_fields_are_normalised(self) -> None:
        node = {
            "id": " 7 ", "name": " Ootel ", "color": " 4FBF6B ", "type": " open ", "description": " Wait ",
            "isDefault": 1, "sortOrder": 3, "extra": "dropped",
        }
        self.client.send_query.return_value = status_page([node])
        self.assertEqual(APIModuleActions.get_module_status_options("works"), [{
            "id": "7", "name": "Ootel", "color": "4FBF6B", "type": "OPEN", "description": "Wait",
            "isDefault": True, "sortOrder": 3,
        }])

    def test_missing_node_fields_get_their_defaults(self) -> None:
        for color in (None, "", " "):
            with self.subTest(color=color):
                node = {"id": 8, "name": "B", "color": color, "type": None, "description": None, "isDefault": None}
                self.client.send_query.return_value = status_page([node])
                self.assertEqual(APIModuleActions.get_module_status_options("works"), [{
                    "id": "8", "name": "B", "color": "cccccc", "type": "", "description": "",
                    "isDefault": False, "sortOrder": None,
                }])

    def test_nodes_without_an_id_or_a_name_are_skipped(self) -> None:
        edges = [
            None, {}, {"node": None}, {"node": "text"}, {"node": {"id": "", "name": "x"}}, {"node": {"id": "1"}},
            {"node": {"id": "2", "name": "  "}}, {"node": {"name": "no id"}}, {"node": status_node("3", "Good")},
        ]
        self.client.send_query.return_value = {"statuses": {"edges": edges, "pageInfo": {}}}
        self.assertEqual([option["id"] for option in APIModuleActions.get_module_status_options("works")], ["3"])
        self.log.assert_not_called()

    def test_a_repeated_id_keeps_the_last_node(self) -> None:
        self.client.send_query.return_value = status_page([
            status_node("1", "First"), status_node("2", "Other"), status_node("1", "Last"),
        ])
        options = APIModuleActions.get_module_status_options("works")
        self.assertEqual(sorted((option["id"], option["name"]) for option in options), [("1", "Last"), ("2", "Other")])

    def test_options_are_sorted_by_sort_order_then_name(self) -> None:
        # A missing or unreadable sort order counts as 0; a float is cut to its integer part.
        # The nodes arrive in an order that neither the sort order nor the names give.
        self.client.send_query.return_value = status_page([
            status_node("6", "f"), status_node("5", "e", sortOrder=1.9), status_node("1", "B", sortOrder=2),
            status_node("4", "D", sortOrder="x"), status_node("2", "a", sortOrder="1"),
            status_node("3", "c", sortOrder=None),
        ])
        options = APIModuleActions.get_module_status_options("works")
        self.assertEqual([option["id"] for option in options], ["3", "4", "6", "2", "5", "1"])
        self.assertEqual([option["sortOrder"] for option in options], [None, "x", None, "1", 1.9, 2])

    def test_pages_follow_the_end_cursor_until_the_default_limit(self) -> None:
        self.client.send_query.side_effect = [
            status_page(status_nodes(0, 50), "c1", True), status_page(status_nodes(50, 100), "c2", True),
            status_page(status_nodes(100, 101), "c3", False),
        ]
        options = APIModuleActions.get_module_status_options("works")
        self.assertEqual(len(options), 100)
        self.assertEqual([kwargs["variables"]["after"] for _query, kwargs in self.sent()], [None, "c1"])
        self.assertEqual([kwargs["variables"]["first"] for _query, kwargs in self.sent()], [50, 50])
        self.log.assert_not_called()

    def test_limit_asks_only_for_the_remaining_statuses_on_later_pages(self) -> None:
        self.client.send_query.side_effect = [status_page(status_nodes(0, 50), "c1", True), status_page(status_nodes(50, 100), "c2", True)]
        options = APIModuleActions.get_module_status_options("works", limit=60)
        self.assertEqual(len(options), 60)
        self.assertEqual([kwargs["variables"]["first"] for _query, kwargs in self.sent()], [50, 10])

    def test_limit_caps_the_result_and_stops_the_walk(self) -> None:
        self.client.send_query.side_effect = [status_page(status_nodes(0, 3), "c1", True), status_page(status_nodes(3, 6))]
        options = APIModuleActions.get_module_status_options("works", limit=2)
        self.assertEqual([option["id"] for option in options], ["0", "1"])
        self.assertEqual([kwargs["variables"]["first"] for _query, kwargs in self.sent()], [2])

    def test_limit_below_one_still_keeps_one_status(self) -> None:
        for limit in (0, None, -5):
            with self.subTest(limit=limit):
                self.reset_calls()
                self.client.send_query.return_value = status_page(status_nodes(0, 3), "c1", True)
                options = APIModuleActions.get_module_status_options("works", limit=limit)
                self.assertEqual([option["id"] for option in options], ["0"])
                self.assertEqual(self.sent()[0][1]["variables"]["first"], 1)

    def test_pagination_stops_without_a_next_page_or_cursor(self) -> None:
        pages = (
            status_page([status_node("1", "A")], "c1", False),
            status_page([status_node("1", "A")], None, True),
            status_page([status_node("1", "A")], "  ", True),
            {"statuses": {"edges": [{"node": status_node("1", "A")}]}},
        )
        for page in pages:
            with self.subTest(page=page):
                self.reset_calls()
                # Another page follows, so a walk that does not stop reads it instead of looping on one answer.
                self.client.send_query.side_effect = [page, status_page([status_node("2", "B")], "c9", True)]
                self.assertEqual([option["id"] for option in APIModuleActions.get_module_status_options("works")], ["1"])
                self.assertEqual(self.client.send_query.call_count, 1)

    def test_empty_or_broken_answers_yield_nothing_without_a_log(self) -> None:
        answers = (None, {}, "text", [], {"statuses": None}, {"statuses": {}}, {"statuses": {"edges": None}},
                   {"statuses": {"edges": []}}, {"statuses": {"edges": "x"}})
        for response in answers:
            with self.subTest(response=response):
                self.reset_calls()
                self.client.send_query.return_value = response
                self.assertEqual(APIModuleActions.get_module_status_options("works"), [])
                self.assertEqual(self.client.send_query.call_count, 1)
                self.log.assert_not_called()

    def test_connection_of_the_wrong_type_is_logged_like_a_failed_request(self) -> None:
        self.client.send_query.return_value = {"statuses": "x"}
        self.assertEqual(APIModuleActions.get_module_status_options("works"), [])
        self.assertIsInstance(self.log.call_args.args[0], AttributeError)
        self.assertEqual(self.log.call_args.kwargs["event"], "module_statuses_fetch_failed")

    def test_failed_request_returns_nothing_and_is_logged(self) -> None:
        error = RuntimeError("offline")
        self.client.send_query.side_effect = error
        self.assertEqual(APIModuleActions.get_module_status_options("works"), [])
        self.assertIs(self.log.call_args.args[0], error)
        self.assertEqual(self.log.call_args.kwargs, {
            "module": "statuses",
            "event": "module_statuses_fetch_failed",
            "extra": {"module": "works"},
        })

    def test_failure_on_a_later_page_drops_the_statuses_already_read(self) -> None:
        self.client.send_query.side_effect = [status_page(status_nodes(0, 50), "c1", True), RuntimeError("offline")]
        self.assertEqual(APIModuleActions.get_module_status_options("easement"), [])
        self.assertEqual(self.log.call_args.kwargs["extra"], {"module": "easement"})

    def test_unloadable_query_returns_nothing_and_is_logged(self) -> None:
        self.loader.load_query_by_module.side_effect = FileNotFoundError("query_file_not_found")
        self.assertEqual(APIModuleActions.get_module_status_options("works"), [])
        self.client.send_query.assert_not_called()
        self.assertEqual(self.log.call_args.kwargs["event"], "module_statuses_fetch_failed")


class StatusOptionsRaiseOnErrorTest(ActionTestCase):
    """A caller that shows the error itself (the status filter) asks for it with raise_on_error=True.

    The caller logs what it receives (the filter's worker does), so the action must not log it as well.
    """

    def test_failure_is_raised_to_the_caller_and_left_for_it_to_log(self) -> None:
        cases = (
            ("first page", [RuntimeError("offline")]),
            ("later page", [status_page(status_nodes(0, 50), "c1", True), RuntimeError("offline")]),
        )
        for name, answers in cases:
            with self.subTest(case=name):
                self.reset_calls()
                error = answers[-1]
                self.client.send_query.side_effect = answers
                with self.assertRaises(RuntimeError) as raised:
                    APIModuleActions.get_module_status_options("works", raise_on_error=True)
                self.assertIs(raised.exception, error)
                self.log.assert_not_called()

    def test_unloadable_query_is_raised_to_the_caller_and_not_logged_here(self) -> None:
        error = FileNotFoundError("query_file_not_found")
        self.loader.load_query_by_module.side_effect = error
        with self.assertRaises(FileNotFoundError) as raised:
            APIModuleActions.get_module_status_options("works", raise_on_error=True)
        self.assertIs(raised.exception, error)
        self.client.send_query.assert_not_called()
        self.log.assert_not_called()

    def test_read_statuses_are_the_same_as_without_the_flag(self) -> None:
        pages = [status_page([status_node("2", "b", sortOrder=2)], "c1", True), status_page([status_node("1", "a")])]
        self.client.send_query.side_effect = list(pages)
        raised_mode = APIModuleActions.get_module_status_options("works", limit=7, raise_on_error=True)
        raised_mode_sent = self.sent()
        self.reset_calls()
        self.client.send_query.side_effect = list(pages)
        self.assertEqual(raised_mode, APIModuleActions.get_module_status_options("works", limit=7))
        self.assertEqual(raised_mode_sent, self.sent())
        self.assertEqual([option["id"] for option in raised_mode], ["1", "2"])
        self.log.assert_not_called()

    def test_blank_module_and_empty_answers_are_no_error(self) -> None:
        self.assertEqual(APIModuleActions.get_module_status_options(" ", raise_on_error=True), [])
        self.client.send_query.assert_not_called()
        for response in (None, {}, {"statuses": {"edges": []}}):
            with self.subTest(response=response):
                self.client.send_query.return_value = response
                self.assertEqual(APIModuleActions.get_module_status_options("works", raise_on_error=True), [])
        self.log.assert_not_called()

    def test_flag_is_keyword_only_and_off_by_default(self) -> None:
        self.client.send_query.side_effect = RuntimeError("offline")
        self.assertEqual(APIModuleActions.get_module_status_options("works"), [])
        with self.assertRaises(TypeError):
            APIModuleActions.get_module_status_options("works", 100, True)


class TaskPriorityValuesTest(ActionTestCase):
    def test_values_are_the_schema_enum_and_need_no_request(self) -> None:
        # The server refuses the introspection query that once read them (a log error every session).
        self.assertEqual(APIModuleActions.get_task_priority_values(), PRIORITY_VALUES)
        self.loader.load_query_by_module.assert_not_called()
        self.client.send_query.assert_not_called()
        self.log.assert_not_called()

    def test_callers_get_a_fresh_list(self) -> None:
        APIModuleActions.get_task_priority_values().append("CHANGED")
        self.assertEqual(APIModuleActions.get_task_priority_values(), PRIORITY_VALUES)
        self.assertEqual(APIModuleActions._TASK_PRIORITY_VALUES, tuple(PRIORITY_VALUES))


class TaskPriorityLabelTest(ActionTestCase):
    def test_blank_priority_has_the_none_label(self) -> None:
        for priority in (None, "", "  "):
            with self.subTest(priority=priority):
                self.assertEqual(
                    APIModuleActions.task_priority_label(priority, lang_manager=self.lang),
                    f"T[{TranslationKeys.WORKS_PRIORITY_NONE}]",
                )

    def test_known_priorities_use_their_translation_key(self) -> None:
        cases = (("URGENT", TranslationKeys.WORKS_PRIORITY_URGENT), ("high", TranslationKeys.WORKS_PRIORITY_HIGH),
                 (" Medium ", TranslationKeys.WORKS_PRIORITY_MEDIUM), ("LOW", TranslationKeys.WORKS_PRIORITY_LOW))
        for priority, key in cases:
            with self.subTest(priority=priority):
                self.lang.translate.reset_mock()
                self.assertEqual(APIModuleActions.task_priority_label(priority, lang_manager=self.lang), f"T[{key}]")
                self.lang.translate.assert_called_once_with(key)

    def test_unknown_priority_is_shown_as_title_case_words_without_a_translation(self) -> None:
        cases = (("not_started", "Not Started"), ("CRITICAL", "Critical"), (" very_high ", "Very High"))
        for priority, label in cases:
            with self.subTest(priority=priority):
                self.assertEqual(APIModuleActions.task_priority_label(priority, lang_manager=self.lang), label)
        self.lang.translate.assert_not_called()

    def test_given_language_manager_is_used_and_no_other_is_built(self) -> None:
        APIModuleActions.task_priority_label("high", lang_manager=self.lang)
        self.assertEqual(self.language_managers_built(), 0)

    def test_without_a_language_manager_one_is_built(self) -> None:
        self.assertEqual(APIModuleActions.task_priority_label("low"), f"T[{TranslationKeys.WORKS_PRIORITY_LOW}]")
        self.assertEqual(self.language_managers_built(), 1)


class TaskPriorityOptionsTest(ActionTestCase):
    def test_options_start_with_the_empty_choice_and_follow_the_schema_order(self) -> None:
        self.assertEqual(APIModuleActions.get_task_priority_options(lang_manager=self.lang), [
            {"value": "", "label": f"T[{TranslationKeys.WORKS_PRIORITY_NONE}]"},
            {"value": "URGENT", "label": f"T[{TranslationKeys.WORKS_PRIORITY_URGENT}]"},
            {"value": "HIGH", "label": f"T[{TranslationKeys.WORKS_PRIORITY_HIGH}]"},
            {"value": "MEDIUM", "label": f"T[{TranslationKeys.WORKS_PRIORITY_MEDIUM}]"},
            {"value": "LOW", "label": f"T[{TranslationKeys.WORKS_PRIORITY_LOW}]"},
        ])
        self.client.send_query.assert_not_called()

    def test_empty_choice_can_be_left_out(self) -> None:
        options = APIModuleActions.get_task_priority_options(lang_manager=self.lang, include_empty=False)
        self.assertEqual([option["value"] for option in options], PRIORITY_VALUES)

    def test_one_language_manager_serves_every_label(self) -> None:
        self.assertEqual(len(APIModuleActions.get_task_priority_options()), 5)
        self.assertEqual(self.language_managers_built(), 1)

    def test_given_language_manager_builds_no_other(self) -> None:
        APIModuleActions.get_task_priority_options(lang_manager=self.lang)
        self.assertEqual(self.language_managers_built(), 0)


class GetCurrentUserPayloadTest(ActionTestCase):
    ME_QUERY = "query user/me.graphql"

    def test_cached_user_with_an_id_is_returned_without_a_request(self) -> None:
        cached = {"id": "7", "displayName": "Mari"}
        self.session.loggedInUser = cached
        self.assertIs(APIModuleActions.get_current_user_payload(), cached)
        self.loader.load_query_by_module.assert_not_called()
        self.client.send_query.assert_not_called()
        self.session_class.save_session.assert_not_called()
        self.log.assert_not_called()

    def test_missing_or_unusable_cache_loads_the_me_query_without_variables(self) -> None:
        for cached in (None, {}, {"id": ""}, {"id": "  "}, {"displayName": "no id"}, "text", 5):
            with self.subTest(cached=cached):
                self.reset_calls()
                self.session.loggedInUser = cached
                self.client.send_query.return_value = {"me": {"id": "7"}}
                self.assertEqual(APIModuleActions.get_current_user_payload(), {"id": "7"})
                self.assertEqual(self.loaded(), [("user", "me.graphql")])
                self.assertEqual(self.sent(), [(self.ME_QUERY, {})])

    def test_fetched_user_is_stored_on_the_session_and_saved(self) -> None:
        user = {"id": "7", "displayName": "Mari"}
        self.client.send_query.return_value = {"me": user}
        self.assertIs(APIModuleActions.get_current_user_payload(), user)
        self.assertIs(self.session.loggedInUser, user)
        self.session_class.save_session.assert_called_once_with()
        self.log.assert_not_called()

    def test_failed_save_is_logged_and_the_user_is_still_returned(self) -> None:
        error = RuntimeError("disk")
        self.session_class.save_session.side_effect = error
        user = {"id": "7"}
        self.client.send_query.return_value = {"me": user}
        self.assertIs(APIModuleActions.get_current_user_payload(), user)
        self.assertEqual(self.log.call_count, 1)
        self.assertIs(self.log.call_args.args[0], error)
        self.assertEqual(self.log.call_args.kwargs, {"module": "user", "event": "current_user_cache_failed"})

    def test_session_that_refuses_the_user_is_logged_and_the_user_is_still_returned(self) -> None:
        self.session_class.return_value = LockedSession()
        user = {"id": "7"}
        self.client.send_query.return_value = {"me": user}
        self.assertIs(APIModuleActions.get_current_user_payload(), user)
        self.assertEqual(self.log.call_args.kwargs, {"module": "user", "event": "current_user_cache_failed"})
        self.session_class.save_session.assert_not_called()

    def test_answer_without_a_user_id_falls_back_to_the_cached_dict_or_nothing(self) -> None:
        answers = (None, {}, "text", {"me": None}, {"me": {}}, {"me": {"id": " "}}, {"me": "text"}, {"me": {"id": None}})
        for response in answers:
            for cached, expected in ((None, None), ({"displayName": "no id"}, {"displayName": "no id"}), ("text", None)):
                with self.subTest(response=response, cached=cached):
                    self.reset_calls()
                    self.session_class.save_session.reset_mock()
                    self.session.loggedInUser = cached
                    self.client.send_query.return_value = response
                    self.assertEqual(APIModuleActions.get_current_user_payload(), expected)
                    self.session_class.save_session.assert_not_called()
                    self.log.assert_not_called()

    def test_failed_request_is_logged_and_falls_back_to_the_cached_dict_or_nothing(self) -> None:
        error = RuntimeError("offline")
        self.client.send_query.side_effect = error
        for cached, expected in ((None, None), ({"displayName": "no id"}, {"displayName": "no id"}), ("text", None)):
            with self.subTest(cached=cached):
                self.reset_calls()
                self.session.loggedInUser = cached
                self.assertEqual(APIModuleActions.get_current_user_payload(), expected)
                self.assertIs(self.log.call_args.args[0], error)
                self.assertEqual(self.log.call_args.kwargs, {"module": "user", "event": "current_user_fetch_failed"})

    def test_unloadable_query_is_logged_and_falls_back_to_the_cached_dict_or_nothing(self) -> None:
        # Like a failed request: the missing file no longer reaches the caller.
        error = FileNotFoundError("query_file_not_found")
        self.loader.load_query_by_module.side_effect = error
        for cached, expected in ((None, None), ({"displayName": "no id"}, {"displayName": "no id"}), ("text", None)):
            with self.subTest(cached=cached):
                self.reset_calls()
                self.session.loggedInUser = cached
                self.assertEqual(APIModuleActions.get_current_user_payload(), expected)
                self.client.send_query.assert_not_called()
                self.session_class.save_session.assert_not_called()
                self.assertEqual(self.log.call_count, 1)
                self.assertIs(self.log.call_args.args[0], error)
                self.assertEqual(self.log.call_args.kwargs, {"module": "user", "event": "current_user_fetch_failed"})


class GetCurrentUserIdTest(ActionTestCase):
    def test_cached_id_is_returned_stripped_as_text(self) -> None:
        for cached_id, expected in ((" 7 ", "7"), (7, "7"), ("abc", "abc")):
            with self.subTest(cached_id=cached_id):
                self.session.loggedInUser = {"id": cached_id}
                self.assertEqual(APIModuleActions.get_current_user_id(), expected)
        self.client.send_query.assert_not_called()

    def test_fetched_user_gives_its_id(self) -> None:
        self.client.send_query.return_value = {"me": {"id": " 9 "}}
        self.assertEqual(APIModuleActions.get_current_user_id(), "9")

    def test_unloadable_query_gives_an_empty_id(self) -> None:
        self.loader.load_query_by_module.side_effect = FileNotFoundError("query_file_not_found")
        self.assertEqual(APIModuleActions.get_current_user_id(), "")
        self.assertEqual(self.log.call_args.kwargs["event"], "current_user_fetch_failed")

    def test_no_user_gives_an_empty_id(self) -> None:
        self.client.send_query.side_effect = RuntimeError("offline")
        self.assertEqual(APIModuleActions.get_current_user_id(), "")
        self.session.loggedInUser = {"displayName": "no id"}
        self.assertEqual(APIModuleActions.get_current_user_id(), "")


class UserDisplayNameTest(unittest.TestCase):
    def test_display_name_wins(self) -> None:
        user = {"displayName": "  Mari Maa  ", "firstName": "M", "lastName": "X", "email": "m@x.ee", "id": "7"}
        self.assertEqual(APIModuleActions.user_display_name(user), "Mari Maa")

    def test_first_and_last_name_are_joined_when_there_is_no_display_name(self) -> None:
        cases = (
            ({"firstName": " Mari ", "lastName": " Maa "}, "Mari Maa"),
            ({"displayName": " ", "firstName": "Mari"}, "Mari"),
            ({"lastName": "Maa", "email": "m@x.ee"}, "Maa"),
            ({"displayName": None, "firstName": "Mari", "lastName": None}, "Mari"),
        )
        for user, expected in cases:
            with self.subTest(user=user):
                self.assertEqual(APIModuleActions.user_display_name(user), expected)

    def test_email_then_id_are_the_last_fallbacks(self) -> None:
        cases = (
            ({"email": " m@x.ee ", "id": "7"}, "m@x.ee"),
            ({"firstName": " ", "lastName": "", "email": "m@x.ee"}, "m@x.ee"),
            ({"id": " 7 "}, "7"),
            ({"id": 7}, "7"),
        )
        for user, expected in cases:
            with self.subTest(user=user):
                self.assertEqual(APIModuleActions.user_display_name(user), expected)

    def test_nothing_usable_gives_an_empty_name(self) -> None:
        for user in (None, "text", 5, [], {}, {"id": None}, {"displayName": " ", "id": ""}):
            with self.subTest(user=user):
                self.assertEqual(APIModuleActions.user_display_name(user), "")


class GetAssignableUsersTest(ActionTestCase):
    USERS_QUERY = "query user/users.graphql"
    ME_QUERY = "query user/me.graphql"

    def setUp(self) -> None:
        super().setUp()
        self.session.loggedInUser = {"id": "1", "displayName": "Zed"}

    @staticmethod
    def entry(user_id, display_name) -> dict:
        return {"id": user_id, "displayName": display_name}

    def test_loads_the_users_query_with_a_page_size_and_no_filter(self) -> None:
        self.client.send_query.return_value = user_page([user_node("2", "Ann")])
        APIModuleActions.get_assignable_users()
        self.assertEqual(self.loaded(), [("user", "users.graphql")])
        self.assertEqual(self.sent(), [(self.USERS_QUERY, {"variables": {"first": 50, "after": None}})])

    def test_current_user_comes_first_then_the_rest_by_name_ignoring_case(self) -> None:
        self.client.send_query.return_value = user_page([
            user_node("2", "bob"), user_node("3", "Ann"), user_node("4", "Cid"), user_node("5", "anna"),
        ])
        self.assertEqual(APIModuleActions.get_assignable_users(), [
            self.entry("1", "Zed"), self.entry("3", "Ann"), self.entry("5", "anna"),
            self.entry("2", "bob"), self.entry("4", "Cid"),
        ])

    def test_only_the_id_and_the_display_name_are_kept(self) -> None:
        self.client.send_query.return_value = user_page([user_node("2", " Ann ", deletedAt=None, email="a@x.ee")])
        self.assertEqual(APIModuleActions.get_assignable_users(), [self.entry("1", "Zed"), self.entry("2", "Ann")])

    def test_listed_current_user_keeps_the_first_place_with_the_listed_name(self) -> None:
        self.client.send_query.return_value = user_page([user_node("2", "Ann"), user_node("1", "Zed Renamed")])
        self.assertEqual(APIModuleActions.get_assignable_users(), [self.entry("1", "Zed Renamed"), self.entry("2", "Ann")])

    def test_deleted_users_ids_less_nodes_and_broken_edges_are_skipped(self) -> None:
        edges = [
            None, {}, {"node": None}, {"node": "text"}, {"node": {"displayName": "no id"}}, {"node": {"id": ""}},
            {"node": user_node("2", "Gone", deletedAt="2026-01-01")},
            {"node": user_node("3", "Kept blank", deletedAt="  ")},
            {"node": user_node("4", "Kept none", deletedAt=None)},
            {"node": user_node("1", "Zed deleted copy", deletedAt="2026-01-01")},
        ]
        self.client.send_query.return_value = {"users": {"edges": edges, "pageInfo": {}}}
        self.assertEqual(APIModuleActions.get_assignable_users(), [
            self.entry("1", "Zed"), self.entry("3", "Kept blank"), self.entry("4", "Kept none"),
        ])
        self.log.assert_not_called()

    def test_node_without_a_display_name_is_shown_by_name_parts_email_or_id(self) -> None:
        self.client.send_query.return_value = user_page([
            {"id": "2", "firstName": "Ann", "lastName": "Aru"}, {"id": "3", "email": "c@x.ee"}, {"id": "4"},
        ])
        self.assertEqual(APIModuleActions.get_assignable_users(), [
            self.entry("1", "Zed"), self.entry("4", "4"), self.entry("2", "Ann Aru"), self.entry("3", "c@x.ee"),
        ])

    def test_current_user_without_a_name_is_listed_by_id(self) -> None:
        self.session.loggedInUser = {"id": "1"}
        self.client.send_query.return_value = user_page([])
        self.assertEqual(APIModuleActions.get_assignable_users(), [self.entry("1", "1")])

    def test_pages_follow_the_end_cursor_and_a_repeated_user_counts_once(self) -> None:
        self.client.send_query.side_effect = [
            user_page([user_node("2", "Ann")], "c1", True),
            user_page([user_node("2", "Ann"), user_node("3", "Bob")], "c2", True),
            user_page([user_node("4", "Cid")], None, False),
        ]
        users = APIModuleActions.get_assignable_users()
        self.assertEqual([user["id"] for user in users], ["1", "2", "3", "4"])
        self.assertEqual([kwargs["variables"]["after"] for _query, kwargs in self.sent()], [None, "c1", "c2"])
        self.assertEqual([kwargs["variables"]["first"] for _query, kwargs in self.sent()], [50, 50, 50])

    def test_pagination_stops_without_a_next_page_cursor_or_edges(self) -> None:
        pages = (
            user_page([user_node("2", "Ann")], "c1", False),
            user_page([user_node("2", "Ann")], None, True),
            user_page([user_node("2", "Ann")], "  ", True),
            {"users": {"edges": [{"node": user_node("2", "Ann")}]}},
        )
        for page in pages:
            with self.subTest(page=page):
                self.reset_calls()
                # Another page follows, so a walk that does not stop reads it instead of looping on one answer.
                self.client.send_query.side_effect = [page, user_page([user_node("3", "Cid")], "c9", True)]
                self.assertEqual([user["id"] for user in APIModuleActions.get_assignable_users()], ["1", "2"])
                self.assertEqual(self.client.send_query.call_count, 1)

    def test_empty_or_broken_answers_leave_only_the_current_user(self) -> None:
        answers = (None, {}, "text", {"users": None}, {"users": {}}, {"users": {"edges": None}},
                   {"users": {"edges": []}}, {"users": {"edges": "x"}})
        for response in answers:
            with self.subTest(response=response):
                self.reset_calls()
                self.client.send_query.return_value = response
                self.assertEqual(APIModuleActions.get_assignable_users(), [self.entry("1", "Zed")])
                self.assertEqual(self.client.send_query.call_count, 1)
                self.log.assert_not_called()

    def test_connection_of_the_wrong_type_is_logged_like_a_failed_request(self) -> None:
        self.client.send_query.return_value = {"users": "x"}
        self.assertEqual(APIModuleActions.get_assignable_users(), [self.entry("1", "Zed")])
        self.assertIsInstance(self.log.call_args.args[0], AttributeError)
        self.assertEqual(self.log.call_args.kwargs["event"], "assignable_users_fetch_failed")

    def test_limit_counts_the_current_user_and_shrinks_the_page_size(self) -> None:
        self.client.send_query.return_value = user_page([user_node(str(i), f"User {i}") for i in range(2, 7)], "c1", True)
        users = APIModuleActions.get_assignable_users(limit=3)
        self.assertEqual([user["id"] for user in users], ["1", "2", "3"])
        self.assertEqual(self.sent(), [(self.USERS_QUERY, {"variables": {"first": 2, "after": None}})])

    def test_limit_asks_only_for_the_remaining_users_on_later_pages(self) -> None:
        self.client.send_query.side_effect = [
            user_page([user_node(str(i), f"User {i:02d}") for i in range(2, 52)], "c1", True),
            user_page([user_node(str(i), f"User {i:02d}") for i in range(52, 62)], "c2", True),
        ]
        users = APIModuleActions.get_assignable_users(limit=61)
        self.assertEqual(len(users), 61)
        self.assertEqual([kwargs["variables"]["first"] for _query, kwargs in self.sent()], [50, 10])

    def test_limit_of_one_with_a_current_user_asks_for_no_page(self) -> None:
        for limit in (1, 0, None, -3):
            with self.subTest(limit=limit):
                self.reset_calls()
                self.assertEqual(APIModuleActions.get_assignable_users(limit=limit), [self.entry("1", "Zed")])
                self.assertEqual(self.loaded(), [("user", "users.graphql")])
                self.client.send_query.assert_not_called()

    def test_limit_of_one_without_a_current_user_asks_for_one_user(self) -> None:
        self.session.loggedInUser = None
        self.answer({self.ME_QUERY: {"me": None}, self.USERS_QUERY: user_page([user_node("2", "Ann"), user_node("3", "Bob")])})
        self.assertEqual(APIModuleActions.get_assignable_users(limit=0), [self.entry("2", "Ann")])
        self.assertEqual(self.sent()[-1], (self.USERS_QUERY, {"variables": {"first": 1, "after": None}}))

    def test_current_user_is_fetched_first_when_the_session_has_none(self) -> None:
        self.session.loggedInUser = None
        self.answer({
            self.ME_QUERY: {"me": {"id": "1", "displayName": "Zed"}},
            self.USERS_QUERY: user_page([user_node("2", "Ann")]),
        })
        self.assertEqual(APIModuleActions.get_assignable_users(), [self.entry("1", "Zed"), self.entry("2", "Ann")])
        self.assertEqual(self.loaded(), [("user", "me.graphql"), ("user", "users.graphql")])
        self.assertEqual(self.session.loggedInUser, {"id": "1", "displayName": "Zed"})
        self.session_class.save_session.assert_called_once_with()

    def test_users_are_listed_when_the_current_user_query_cannot_be_loaded(self) -> None:
        self.session.loggedInUser = None

        def load(module, filename):
            if filename == "me.graphql":
                raise FileNotFoundError("query_file_not_found")
            return self._query_text(module, filename)

        self.loader.load_query_by_module.side_effect = load
        self.client.send_query.return_value = user_page([user_node("3", "Bob"), user_node("2", "Ann")])
        self.assertEqual(APIModuleActions.get_assignable_users(), [self.entry("2", "Ann"), self.entry("3", "Bob")])
        self.assertEqual(self.sent(), [(self.USERS_QUERY, {"variables": {"first": 50, "after": None}})])
        self.assertEqual([call.kwargs["event"] for call in self.log.call_args_list], ["current_user_fetch_failed"])

    def test_users_are_listed_without_a_current_user_when_it_cannot_be_read(self) -> None:
        self.session.loggedInUser = None
        self.answer({
            self.ME_QUERY: RuntimeError("offline"),
            self.USERS_QUERY: user_page([user_node("3", "Bob"), user_node("2", "Ann")]),
        })
        self.assertEqual(APIModuleActions.get_assignable_users(), [self.entry("2", "Ann"), self.entry("3", "Bob")])
        self.assertEqual([call.kwargs["event"] for call in self.log.call_args_list], ["current_user_fetch_failed"])

    def test_failed_request_keeps_the_users_already_read_and_is_logged(self) -> None:
        error = RuntimeError("offline")
        self.client.send_query.side_effect = [user_page([user_node("3", "Bob")], "c1", True), error]
        self.assertEqual(APIModuleActions.get_assignable_users(limit=80), [self.entry("1", "Zed"), self.entry("3", "Bob")])
        self.assertIs(self.log.call_args.args[0], error)
        self.assertEqual(self.log.call_args.kwargs, {
            "module": "user",
            "event": "assignable_users_fetch_failed",
            "extra": {"limit": 80},
        })

    def test_unloadable_query_leaves_the_current_user_and_is_logged(self) -> None:
        self.loader.load_query_by_module.side_effect = FileNotFoundError("query_file_not_found")
        self.assertEqual(APIModuleActions.get_assignable_users(limit=0), [self.entry("1", "Zed")])
        self.client.send_query.assert_not_called()
        self.assertEqual(self.log.call_args.kwargs, {
            "module": "user",
            "event": "assignable_users_fetch_failed",
            "extra": {"limit": 1},
        })


class QueryFilesTest(unittest.TestCase):
    """The query files the actions load exist where the loader looks for them (the real loader, no request)."""

    def test_every_loaded_query_file_exists(self) -> None:
        cases = (
            ("statuses", "ListModuleStatuses.graphql", "statuses(first: $first"),
            ("user", "me.graphql", "me {"),
            ("user", "users.graphql", "users(first: $first"),
        )
        loader = GraphQLQueryLoader()
        for module, filename, text in cases:
            with self.subTest(file=filename):
                self.assertIn(text, loader.load_query_by_module(module, filename))


class EntryPointInterfaceTest(unittest.TestCase):
    """APIModuleActions keeps its whole surface after the split, and api_actions.py keeps only the entry point."""

    FILES = (
        "_file_owner_module", "_file_model_type", "_file_query_name", "get_module_files",
        "create_file_download_link", "fetch_file_preview_payload", "delete_file", "upload_module_file",
    )
    PROPERTIES = (
        "_property_owner_module", "get_module_item_connected_properties", "resolve_property_ids_by_cadastral",
        "resolve_property_map_by_cadastral", "get_easement_property_edges", "associate_properties",
        "associate_easement_properties", "linked_cadastral_numbers_from_response",
    )
    STATUSES = (
        "_status_module_value", "get_module_status_options", "get_task_priority_values", "task_priority_label",
        "get_task_priority_options", "get_easement_status", "update_easement_status",
    )
    USERS = ("get_current_user_payload", "get_current_user_id", "user_display_name", "get_assignable_users")
    TASKS = (
        "get_task_data", "get_tasks_by_ids", "get_task_description", "update_task_description", "update_task_status",
        "update_task_members", "_build_task_member_associate_payload", "create_task",
    )
    GEOMETRY = (
        "_geometry_input_value", "_is_unknown_input_field_error", "_is_unknown_geometry_input_error",
        "_is_geometry_retryable_create_error", "_update_module_geometry", "update_task_geometry",
        "update_project_geometry", "update_easement_geometry",
    )
    MOVED = {
        "Kavitro_dev.python.actions.file_actions": ("FileActions", FILES),
        "Kavitro_dev.python.actions.property_link_actions": ("PropertyLinkActions", PROPERTIES),
        "Kavitro_dev.python.actions.status_actions": ("StatusActions", STATUSES),
        "Kavitro_dev.python.actions.user_actions": ("UserActions", USERS),
        "Kavitro_dev.python.actions.task_actions": ("TaskActions", TASKS),
        "Kavitro_dev.python.actions.geometry_actions": ("GeometryActions", GEOMETRY),
    }
    # Text only the moved code used; none of it may stay behind in api_actions.py.
    MOVED_TEXT = (
        "ListModuleStatuses.graphql", "taskPriorityEnum.graphql", "me.graphql", "users.graphql",
        "_TASK_PRIORITY_VALUES", "_sort_key", "SessionManager",
        "LanguageManager", "TranslationKeys", "createTask.graphql", "_build_task_input", "json.dumps",
        "easementStatus.graphql", "APIClient", "GraphQLQueryLoader", "PythonFailLogger",
    )

    def test_entry_point_still_offers_every_method(self) -> None:
        names = [name for _class_name, group in self.MOVED.values() for name in group]
        self.assertEqual(len(names), 43)
        self.assertEqual(len(set(names)), 43)
        for name in names:
            with self.subTest(method=name):
                self.assertTrue(callable(getattr(APIModuleActions, name, None)), name)
        self.assertEqual(APIModuleActions._TASK_PRIORITY_VALUES, tuple(PRIORITY_VALUES))

    def test_moved_methods_are_the_domain_class_functions(self) -> None:
        for module_name, (class_name, names) in self.MOVED.items():
            owner = getattr(importlib.import_module(module_name), class_name)
            self.assertTrue(issubclass(APIModuleActions, owner), class_name)
            for name in names:
                with self.subTest(method=name):
                    function = getattr(APIModuleActions, name)
                    self.assertIs(function, getattr(owner, name))
                    self.assertEqual(function.__module__, module_name)
                    self.assertNotIn(name, vars(APIModuleActions), "the entry point must not shadow a domain method")

    def test_entry_point_defines_nothing_of_its_own(self) -> None:
        own = {name: value for name, value in vars(APIModuleActions).items()
               if not (name.startswith("__") and name.endswith("__"))}
        self.assertEqual(own, {})
        domain_classes = {getattr(importlib.import_module(module), name) for module, (name, _names) in self.MOVED.items()}
        self.assertEqual(set(APIModuleActions.__bases__), domain_classes)

    def test_api_actions_is_only_imports_and_the_class(self) -> None:
        tree = ast.parse(Path(api_actions_module.__file__).read_text(encoding="utf-8"))
        body = list(tree.body)
        if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant):
            body.pop(0)
        *imports, entry = body
        for node in imports:
            with self.subTest(line=node.lineno):
                self.assertIsInstance(node, ast.ImportFrom)
                self.assertEqual(node.level, 1)
                self.assertTrue(str(node.module).startswith("actions."), node.module)
        self.assertIsInstance(entry, ast.ClassDef)
        self.assertEqual(entry.name, "APIModuleActions")
        self.assertEqual(len(entry.body), 1)
        self.assertIsInstance(entry.body[0], ast.Expr)
        self.assertIsInstance(entry.body[0].value, ast.Constant)

    def test_task_priority_state_has_one_owner(self) -> None:
        status_actions = importlib.import_module("Kavitro_dev.python.actions.status_actions").StatusActions
        for name in ("_TASK_PRIORITY_VALUES",):
            with self.subTest(attribute=name):
                self.assertIn(name, vars(status_actions))
                self.assertNotIn(name, vars(APIModuleActions))

    def test_moved_code_left_api_actions(self) -> None:
        source = Path(api_actions_module.__file__).read_text(encoding="utf-8")
        for _class_name, names in self.MOVED.values():
            for name in names:
                with self.subTest(method=name):
                    self.assertNotIn(f"def {name}(", source)
        for text in self.MOVED_TEXT:
            with self.subTest(text=text):
                self.assertNotIn(text, source)

    def test_domain_modules_do_not_import_the_entry_point(self) -> None:
        for module_name in self.MOVED:
            with self.subTest(module=module_name):
                source = Path(importlib.import_module(module_name).__file__).read_text(encoding="utf-8")
                self.assertNotIn("api_actions", source)


if __name__ == "__main__":
    unittest.main()
