"""Characterization tests for the task, geometry and easement status actions behind APIModuleActions.

They pin which query each action loads, which variables it sends, how it reads the answer and
what it does with an empty or broken answer, a failed request or a query file that cannot be
loaded. For create_task they pin every branch of the retry loop: which errors are retried, that
an error after which the task may already exist is never retried, in which order the input is
simplified, how many attempts are made, which follow-up requests put back what the create left
out, and what is returned or logged in the end. The patch helper
covers every module the code may live in, so the same tests run before and after the move out
of python/api_actions.py. MissingCurrentUserQueryTest and StatusFilterLoadErrorTest check two
error-path fixes made after the move as their callers see them. The layout tests at the end
describe the split.
"""
from __future__ import annotations

import datetime
import importlib
import json
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

from qgis.PyQt.QtCore import QCoreApplication, QEvent
from qgis.PyQt.QtWidgets import QWidget
from qgis.core import QgsApplication

from Kavitro_dev.Logs.python_fail_logger import PythonFailLogger
from Kavitro_dev.modules.works import works_create_controller as controller_module
from Kavitro_dev.python import workers as workers_module
from Kavitro_dev.python.GraphQLQueryLoader import GraphQLQueryLoader
from Kavitro_dev.python.api_actions import APIModuleActions
from Kavitro_dev.utils.api_error_handling import ApiError, ApiErrorKind
from Kavitro_dev.widgets.Filters.StatusFilterWidget import StatusFilterWidget


# Every module the actions may be defined in; a missing one is skipped, so the tests run
# on the single-file layout as well as on the split one.
CODE_MODULES = (
    "Kavitro_dev.python.api_actions",
    "Kavitro_dev.python.actions.task_actions",
    "Kavitro_dev.python.actions.geometry_actions",
    "Kavitro_dev.python.actions.status_actions",
    "Kavitro_dev.python.actions.user_actions",
)

TASK_DATA_QUERY = "query task/w_tasks_module_data_by_item_id.graphql"
TASK_LIST_QUERY = "query task/ListFilteredTasks.graphql"
TASK_DESCRIPTION_QUERY = "query task/updateTaskDescription.graphql"
TASK_STATUS_QUERY = "query task/updateTaskStatus.graphql"
TASK_MEMBERS_QUERY = "query task/updateTaskMembers.graphql"
CREATE_QUERY = "query task/createTask.graphql"
ME_QUERY = "query user/me.graphql"
EASEMENT_STATUS_QUERY = "query easement/easementStatus.graphql"
EASEMENT_UPDATE_STATUS_QUERY = "query easement/updateEasementStatus.graphql"

POINT = {"type": "Point", "coordinates": [630385.62, 6457752.97], "properties": {"iconColor": "#4FBF6B"}}
POINT_TEXT = '{"type":"Point","coordinates":[630385.62,6457752.97],"properties":{"iconColor":"#4FBF6B"}}'

# Error texts as the client raises them; each one hits exactly one retry branch of create_task.
STATUS_UNKNOWN = '[WC-API][graphql] Field "status" is not defined by type "CreateTaskInput".'
FLAG_REFUSED = '[WC-API][graphql] Variable "$input" got invalid value at "input.members.associate[0]"; Field "responsible" is not defined.'
GEOMETRY_ERROR = "[WC-API][graphql] Internal server error"
SERVER_ERROR = "[WC-API][server] HTTP 500 Internal Server Error"
REFUSED = "[WC-API][graphql] Validation failed"
# One text that hits all three branches.
EVERY_BRANCH = f"{STATUS_UNKNOWN} {FLAG_REFUSED} {GEOMETRY_ERROR}"
GRAPHQL_TAG = "[WC-API][graphql] "
# What Kavitro answers to the follow-up that sets the status the create left out.
STATUS_SET = {"updateTask": {"id": "77", "status": {"id": "s1"}}}


def rejected(message: str) -> ApiError:
    """The error the client raises when the server answers and refuses the request."""
    text = str(message or "")
    return ApiError(ApiErrorKind.GRAPHQL, text[len(GRAPHQL_TAG):] if text.startswith(GRAPHQL_TAG) else text)


def _code_modules() -> list:
    modules = []
    for name in CODE_MODULES:
        try:
            modules.append(importlib.import_module(name))
        except ImportError:
            continue
    return modules


def task_page(nodes) -> dict:
    return {"tasks": {"edges": [{"node": node} for node in nodes]}}


class ActionTestCase(unittest.TestCase):
    """Mocked loader, client, session and logger; no request leaves the process."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QgsApplication.instance() or QgsApplication([], False)

    def setUp(self) -> None:
        self.client = Mock()
        self.loader = Mock()
        self.loader.load_query_by_module.side_effect = self._query_text
        self.session = SimpleNamespace(loggedInUser=None)
        self.session_class = MagicMock()
        self.session_class.return_value = self.session
        self.log = self._patch(PythonFailLogger, "log_exception")
        for module in _code_modules():
            for name, instance in (("APIClient", self.client), ("GraphQLQueryLoader", self.loader)):
                if hasattr(module, name):
                    self._patch(module, name, return_value=instance)
            if hasattr(module, "SessionManager"):
                self._patch(module, "SessionManager", new=self.session_class)

    @staticmethod
    def _query_text(module: str, filename: str) -> str:
        return f"query {module}/{filename}"

    def _patch(self, target, name, **kwargs):
        patcher = patch.object(target, name, **kwargs)
        started = patcher.start()
        self.addCleanup(patcher.stop)
        return started

    def loaded(self) -> list:
        return [tuple(call.args) for call in self.loader.load_query_by_module.call_args_list]

    def sent(self) -> list:
        return [(call.args[0], dict(call.kwargs)) for call in self.client.send_query.call_args_list]

    def queries(self) -> list:
        return [query for query, _kwargs in self.sent()]

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

    def missing_query(self, filename: str) -> None:
        """The loader cannot load this one file; every other file loads."""

        def load(module, name):
            if name == filename:
                raise FileNotFoundError(f"query_file_not_found: {name}")
            return self._query_text(module, name)

        self.loader.load_query_by_module.side_effect = load

    def assert_logged(self, error, **kwargs) -> None:
        self.assertEqual(self.log.call_count, 1, self.log.call_args_list)
        if isinstance(error, type):
            self.assertIsInstance(self.log.call_args.args[0], error)
        else:
            self.assertIs(self.log.call_args.args[0], error)
        self.assertEqual(self.log.call_args.kwargs, kwargs)


class GeometryInputValueTest(unittest.TestCase):
    def test_geometry_is_compact_json_in_the_given_key_order(self) -> None:
        self.assertEqual(APIModuleActions._geometry_input_value(POINT), POINT_TEXT)
        self.assertEqual(APIModuleActions._geometry_input_value({"b": 1, "a": [1, 2.5]}), '{"b":1,"a":[1,2.5]}')

    def test_non_ascii_text_is_kept(self) -> None:
        self.assertEqual(
            APIModuleActions._geometry_input_value({"type": "Point", "name": "Õpetajate tee"}),
            '{"type":"Point","name":"Õpetajate tee"}',
        )

    def test_value_reads_back_as_the_same_geometry(self) -> None:
        self.assertEqual(json.loads(APIModuleActions._geometry_input_value(POINT)), POINT)


class UnknownInputFieldErrorTest(unittest.TestCase):
    def test_every_unknown_field_marker_counts(self) -> None:
        cases = (
            'Unknown field "status" on CreateTaskInput',
            'Field "status" is not defined by type "CreateTaskInput".',
            "undefined field status",
            "input field is not defined: status",
            'Field "status" does not exist on type "CreateTaskInput"',
            'Field "statuz" is unknown. Did you mean "status"?',
        )
        for message in cases:
            with self.subTest(message=message):
                self.assertTrue(APIModuleActions._is_unknown_input_field_error(message, "status"))

    def test_text_and_field_are_compared_without_case_and_spaces(self) -> None:
        self.assertTrue(APIModuleActions._is_unknown_input_field_error('UNKNOWN FIELD "STATUS"', " Status "))

    def test_only_the_whole_field_name_counts(self) -> None:
        # "status" is not "statusId", "status_id" or "statuses".
        for message in ('Unknown field "statusId"', 'Field "status_id" is not defined', "Unknown field statuses",
                        'Field "CreateStatusInput" is not defined'):
            with self.subTest(message=message):
                self.assertFalse(APIModuleActions._is_unknown_input_field_error(message, "status"))
        self.assertTrue(APIModuleActions._is_unknown_input_field_error('Unknown field "statusId"', "statusId"))

    def test_field_name_is_found_as_a_quoted_name_in_a_path_or_in_brackets(self) -> None:
        for message in ('Unknown field "status"', "Unknown field input.status", "undefined field (status)",
                        'Field "statusId" is not defined; Did you mean "status"?'):
            with self.subTest(message=message):
                self.assertTrue(APIModuleActions._is_unknown_input_field_error(message, "status"))

    def test_other_field_or_other_error_does_not_count(self) -> None:
        cases = (
            ('Unknown field "priority"', "status"),
            ('status "s1" is invalid', "status"),
            ("Internal server error", "status"),
            ("", "status"),
            (None, "status"),
        )
        for message, field in cases:
            with self.subTest(message=message):
                self.assertFalse(APIModuleActions._is_unknown_input_field_error(message, field))

    def test_blank_field_never_counts(self) -> None:
        for field in ("", "  ", None):
            with self.subTest(field=field):
                self.assertFalse(APIModuleActions._is_unknown_input_field_error('Unknown field ""', field))


class UnknownGeometryInputErrorTest(unittest.TestCase):
    def test_only_an_unknown_geometry_field_counts(self) -> None:
        self.assertTrue(APIModuleActions._is_unknown_geometry_input_error(
            'Field "geometry" is not defined by type "CreateTaskInput".'))
        self.assertTrue(APIModuleActions._is_unknown_geometry_input_error('Unknown field "Geometry"'))
        for message in (STATUS_UNKNOWN, "geometry is invalid", SERVER_ERROR, "", None,
                        'Field "geometryType" is not defined by type "CreateTaskInput".'):
            with self.subTest(message=message):
                self.assertFalse(APIModuleActions._is_unknown_geometry_input_error(message))


class GeometryRetryableCreateErrorTest(unittest.TestCase):
    RETRYABLE = (
        "Internal server error",
        "Invalid GeoJSON",
        "JSON parse error",
        "icon is missing",
        "iconColor is invalid",
        'Field "geometry" is not defined by type "CreateTaskInput".',
    )
    NOT_RETRYABLE = (
        "HTTP 400", "HTTP 501", "[WC-API][network] offline", REFUSED, STATUS_UNKNOWN, FLAG_REFUSED, "", None,
        # HTTP status errors leave it unknown whether the task was created.
        "[WC-API][server] request failed", "HTTP 500", "http 502 bad gateway", "HTTP 503",
        "[WC-API][server] Serveri päring ebaõnnestus (HTTP 504).",
    )

    def test_geometry_style_errors_in_the_server_answer_are_retryable(self) -> None:
        for message in self.RETRYABLE:
            with self.subTest(message=message):
                self.assertTrue(APIModuleActions._is_geometry_retryable_create_error(message))

    def test_other_errors_are_not(self) -> None:
        for message in self.NOT_RETRYABLE:
            with self.subTest(message=message):
                self.assertFalse(APIModuleActions._is_geometry_retryable_create_error(message))


class BuildTaskMemberAssociatePayloadTest(unittest.TestCase):
    @staticmethod
    def build(*args, **kwargs) -> list:
        return APIModuleActions._build_task_member_associate_payload(*args, **kwargs)

    def test_responsible_member_is_flagged_and_the_rest_are_not(self) -> None:
        self.assertEqual(self.build(["u1", "u2"], responsible_id="u2"), [
            {"id": "u1", "responsible": False}, {"id": "u2", "responsible": True},
        ])

    def test_ids_are_stripped_deduplicated_and_keep_their_order(self) -> None:
        self.assertEqual(self.build([" u2 ", "u1", "u2", "", "  ", 7], responsible_id=" u1 "), [
            {"id": "u2", "responsible": False}, {"id": "u1", "responsible": True}, {"id": "7", "responsible": False},
        ])

    def test_none_id_is_no_id(self) -> None:
        self.assertEqual(self.build([None]), [])
        self.assertEqual(self.build([None, "u1", None], responsible_id="u1"), [{"id": "u1", "responsible": True}])

    def test_without_a_responsible_no_member_is_flagged(self) -> None:
        for responsible in ("", "  ", None):
            with self.subTest(responsible=responsible):
                self.assertEqual(self.build(["u1", "u2"], responsible_id=responsible), [{"id": "u1"}, {"id": "u2"}])
        self.assertEqual(self.build(["u1"]), [{"id": "u1"}])

    def test_flag_can_be_left_out(self) -> None:
        self.assertEqual(
            self.build(["u1", "u2"], responsible_id="u2", include_responsible_flag=False), [{"id": "u1"}, {"id": "u2"}],
        )

    def test_responsible_outside_the_list_flags_nobody(self) -> None:
        self.assertEqual(self.build(["u1"], responsible_id="u9"), [{"id": "u1", "responsible": False}])

    def test_no_members_give_an_empty_list(self) -> None:
        for member_ids in (None, [], ["", " "]):
            with self.subTest(member_ids=member_ids):
                self.assertEqual(self.build(member_ids, responsible_id="u1"), [])


class GetTaskDataTest(ActionTestCase):
    def test_blank_id_returns_none_without_a_request(self) -> None:
        for item_id in ("", "  ", None):
            with self.subTest(item_id=item_id):
                self.assertIsNone(APIModuleActions.get_task_data(item_id))
        self.loader.load_query_by_module.assert_not_called()
        self.client.send_query.assert_not_called()
        self.log.assert_not_called()

    def test_loads_the_task_query_with_the_stripped_id_and_returns_the_task(self) -> None:
        for item_id, sent_id in ((" 7 ", "7"), (7, "7")):
            with self.subTest(item_id=item_id):
                self.reset_calls()
                task = {"id": "7", "name": "Avarii"}
                self.client.send_query.return_value = {"task": task}
                self.assertIs(APIModuleActions.get_task_data(item_id), task)
                self.assertEqual(self.loaded(), [("task", "w_tasks_module_data_by_item_id.graphql")])
                self.assertEqual(self.sent(), [(TASK_DATA_QUERY, {"variables": {"id": sent_id}})])

    def test_empty_or_broken_answers_return_none_without_a_log(self) -> None:
        for response in (None, {}, "text", [], {"task": None}, {"task": {}}, {"task": "x"}, {"task": ["x"]}):
            with self.subTest(response=response):
                self.client.send_query.return_value = response
                self.assertIsNone(APIModuleActions.get_task_data("7"))
        self.log.assert_not_called()

    def test_failed_request_returns_none_and_is_logged(self) -> None:
        error = RuntimeError("offline")
        self.client.send_query.side_effect = error
        self.assertIsNone(APIModuleActions.get_task_data(" 7 "))
        self.assert_logged(error, module="task", event="task_get_data_failed", extra={"item_id": "7"})

    def test_unloadable_query_returns_none_and_is_logged(self) -> None:
        error = FileNotFoundError("query_file_not_found")
        self.loader.load_query_by_module.side_effect = error
        self.assertIsNone(APIModuleActions.get_task_data(" 7 "))
        self.client.send_query.assert_not_called()
        self.assert_logged(error, module="task", event="task_get_data_failed", extra={"item_id": "7"})


class GetTasksByIdsTest(ActionTestCase):
    @staticmethod
    def where(ids) -> dict:
        return {"AND": [{"column": "ID", "operator": "IN", "value": list(ids)}]}

    def test_no_usable_id_returns_nothing_without_a_request(self) -> None:
        for item_ids in (None, [], ["", "  "]):
            with self.subTest(item_ids=item_ids):
                self.assertEqual(APIModuleActions.get_tasks_by_ids(item_ids), {})
        self.loader.load_query_by_module.assert_not_called()
        self.client.send_query.assert_not_called()

    def test_ids_are_cleaned_and_asked_with_an_in_filter(self) -> None:
        nodes = [{"id": "1", "name": "A"}, {"id": 2, "name": "B"}, {"id": "3", "name": "C"}]
        self.client.send_query.return_value = task_page(nodes)
        result = APIModuleActions.get_tasks_by_ids(["1", " 2 ", "1", 3, ""])
        self.assertEqual(result, {"1": nodes[0], "2": nodes[1], "3": nodes[2]})
        self.assertIs(result["2"], nodes[1])
        self.assertEqual(self.loaded(), [("task", "ListFilteredTasks.graphql")])
        self.assertEqual(self.sent(), [(TASK_LIST_QUERY, {"variables": {
            "first": 3, "after": None, "where": self.where(["1", "2", "3"]),
        }})])

    def test_ids_are_asked_in_chunks_of_twenty_five(self) -> None:
        ids = [str(i) for i in range(60)]
        self.client.send_query.side_effect = lambda query, variables=None: task_page(
            [{"id": value} for value in variables["where"]["AND"][0]["value"]]
        )
        result = APIModuleActions.get_tasks_by_ids(ids)
        self.assertEqual(sorted(result, key=int), ids)
        sent = [kwargs["variables"] for _query, kwargs in self.sent()]
        self.assertEqual([variables["first"] for variables in sent], [25, 25, 10])
        self.assertEqual([variables["where"] for variables in sent], [
            self.where(ids[0:25]), self.where(ids[25:50]), self.where(ids[50:60]),
        ])
        self.assertEqual(self.loader.load_query_by_module.call_count, 1)

    def test_failed_chunk_is_logged_and_the_other_chunks_are_kept(self) -> None:
        ids = [str(i) for i in range(55)]
        error = RuntimeError("offline")
        self.client.send_query.side_effect = [
            task_page([{"id": value} for value in ids[0:25]]), error, task_page([{"id": value} for value in ids[50:55]]),
        ]
        result = APIModuleActions.get_tasks_by_ids(ids)
        self.assertEqual(sorted(result, key=int), ids[0:25] + ids[50:55])
        self.assert_logged(error, module="task", event="task_bulk_fetch_failed", extra={"count": 25})

    def test_unusable_nodes_are_skipped(self) -> None:
        edges = [
            None, {}, "text", 5, ["node"], {"node": None}, {"node": "text"}, {"node": {"id": ""}}, {"node": {"id": 0}},
            {"node": {"name": "no id"}}, {"node": {"id": 5, "name": "Kept"}},
        ]
        self.client.send_query.return_value = {"tasks": {"edges": edges}}
        self.assertEqual(APIModuleActions.get_tasks_by_ids(["5"]), {"5": {"id": 5, "name": "Kept"}})
        self.log.assert_not_called()

    def test_repeated_node_keeps_the_last_and_unasked_nodes_are_kept(self) -> None:
        self.client.send_query.return_value = task_page([{"id": "1", "v": "first"}, {"id": "9"}, {"id": "1", "v": "last"}])
        self.assertEqual(APIModuleActions.get_tasks_by_ids(["1"]), {"1": {"id": "1", "v": "last"}, "9": {"id": "9"}})

    def test_empty_or_broken_answers_give_nothing_without_a_log(self) -> None:
        answers = (None, {}, "text", {"tasks": None}, {"tasks": {}}, {"tasks": {"edges": None}},
                   {"tasks": {"edges": []}}, {"tasks": {"edges": "x"}}, {"tasks": "x"}, {"tasks": ["x"]}, {"tasks": 5})
        for response in answers:
            with self.subTest(response=response):
                self.client.send_query.return_value = response
                self.assertEqual(APIModuleActions.get_tasks_by_ids(["1"]), {})
        self.log.assert_not_called()

    def test_chunk_of_the_wrong_type_is_skipped_and_the_other_chunks_are_kept(self) -> None:
        ids = [str(i) for i in range(30)]
        self.client.send_query.side_effect = [{"tasks": "x"}, task_page([{"id": value} for value in ids[25:30]])]
        self.assertEqual(sorted(APIModuleActions.get_tasks_by_ids(ids), key=int), ids[25:30])
        self.assertEqual(len(self.sent()), 2)

    def test_none_id_is_not_asked(self) -> None:
        self.assertEqual(APIModuleActions.get_tasks_by_ids([None]), {})
        self.client.send_query.assert_not_called()
        self.client.send_query.return_value = task_page([])
        APIModuleActions.get_tasks_by_ids([None, "1"])
        self.assertEqual(self.sent()[0][1]["variables"]["where"], self.where(["1"]))

    def test_unloadable_query_gives_nothing_and_is_logged(self) -> None:
        error = FileNotFoundError("query_file_not_found")
        self.loader.load_query_by_module.side_effect = error
        self.assertEqual(APIModuleActions.get_tasks_by_ids(["1", "2", "1"]), {})
        self.client.send_query.assert_not_called()
        self.assert_logged(error, module="task", event="task_bulk_fetch_failed", extra={"count": 2})


class GetTaskDescriptionTest(ActionTestCase):
    def test_description_of_the_fetched_task_is_returned(self) -> None:
        self.client.send_query.return_value = {"task": {"id": "7", "description": "<p>Märkus</p>"}}
        self.assertEqual(APIModuleActions.get_task_description(" 7 "), "<p>Märkus</p>")
        self.assertEqual(self.sent(), [(TASK_DATA_QUERY, {"variables": {"id": "7"}})])

    def test_missing_description_is_empty_text_and_other_values_become_text(self) -> None:
        for task, expected in (({"id": "7"}, ""), ({"id": "7", "description": None}, ""),
                               ({"id": "7", "description": ""}, ""), ({"id": "7", "description": 5}, "5")):
            with self.subTest(task=task):
                self.client.send_query.return_value = {"task": task}
                self.assertEqual(APIModuleActions.get_task_description("7"), expected)

    def test_without_a_task_there_is_no_description(self) -> None:
        self.assertIsNone(APIModuleActions.get_task_description(""))
        self.client.send_query.assert_not_called()
        for response in ({"task": None}, {"task": "x"}, None):
            with self.subTest(response=response):
                self.client.send_query.return_value = response
                self.assertIsNone(APIModuleActions.get_task_description("7"))
        self.log.assert_not_called()

    def test_failed_request_gives_none_and_is_logged_by_the_task_read(self) -> None:
        error = RuntimeError("offline")
        self.client.send_query.side_effect = error
        self.assertIsNone(APIModuleActions.get_task_description("7"))
        self.assert_logged(error, module="task", event="task_get_data_failed", extra={"item_id": "7"})

    def test_unloadable_query_gives_none_and_is_logged_by_the_task_read(self) -> None:
        error = FileNotFoundError("query_file_not_found")
        self.loader.load_query_by_module.side_effect = error
        self.assertIsNone(APIModuleActions.get_task_description("7"))
        self.assert_logged(error, module="task", event="task_get_data_failed", extra={"item_id": "7"})


class UpdateTaskDescriptionTest(ActionTestCase):
    def test_blank_id_is_refused_without_a_request(self) -> None:
        for item_id in ("", "  ", None):
            with self.subTest(item_id=item_id):
                self.assertFalse(APIModuleActions.update_task_description(item_id, "<p>x</p>"))
        self.loader.load_query_by_module.assert_not_called()
        self.client.send_query.assert_not_called()

    def test_sends_the_description_in_the_task_input(self) -> None:
        self.client.send_query.return_value = {"updateTask": {"id": "7"}}
        self.assertIs(APIModuleActions.update_task_description(" 7 ", "<p>Märkus</p>"), True)
        self.assertEqual(self.loaded(), [("task", "updateTaskDescription.graphql")])
        self.assertEqual(self.sent(), [(TASK_DESCRIPTION_QUERY, {"variables": {
            "input": {"id": "7", "description": "<p>Märkus</p>"},
        }})])

    def test_description_is_sent_as_text(self) -> None:
        for description, sent in ((None, ""), ("", ""), (5, "5")):
            with self.subTest(description=description):
                self.reset_calls()
                self.client.send_query.return_value = {"updateTask": {"id": "7"}}
                APIModuleActions.update_task_description("7", description)
                self.assertEqual(self.sent()[0][1]["variables"]["input"]["description"], sent)

    def test_answer_without_the_task_id_is_a_silent_false(self) -> None:
        for response in (None, {}, "text", {"updateTask": None}, {"updateTask": {}}, {"updateTask": {"id": ""}}):
            with self.subTest(response=response):
                self.client.send_query.return_value = response
                self.assertIs(APIModuleActions.update_task_description("7", "x"), False)
        self.log.assert_not_called()

    def test_answer_of_the_wrong_type_is_logged_like_a_failed_request(self) -> None:
        self.client.send_query.return_value = {"updateTask": "x"}
        self.assertIs(APIModuleActions.update_task_description("7", "x"), False)
        self.assert_logged(AttributeError, module="task", event="task_update_description_failed", extra={"item_id": "7"})

    def test_failed_request_returns_false_and_is_logged(self) -> None:
        error = RuntimeError("offline")
        self.client.send_query.side_effect = error
        self.assertIs(APIModuleActions.update_task_description(" 7 ", "x"), False)
        self.assert_logged(error, module="task", event="task_update_description_failed", extra={"item_id": "7"})

    def test_unloadable_query_returns_false_and_is_logged(self) -> None:
        error = FileNotFoundError("query_file_not_found")
        self.loader.load_query_by_module.side_effect = error
        self.assertIs(APIModuleActions.update_task_description(" 7 ", "x"), False)
        self.client.send_query.assert_not_called()
        self.assert_logged(error, module="task", event="task_update_description_failed", extra={"item_id": "7"})


# (plugin module, Kavitro entity, mutation root, .graphql file): every task section shares the task row.
STATUS_UPDATE_CASES = (
    ("works", "task", "updateTask", "updateTaskStatus.graphql"),
    ("asbuilt", "task", "updateTask", "updateTaskStatus.graphql"),
    ("task", "task", "updateTask", "updateTaskStatus.graphql"),
    ("easement", "easement", "updateEasement", "updateEasementStatus.graphql"),
    ("project", "project", "updateProject", "updateProjectStatus.graphql"),
    ("contract", "contract", "updateContract", "updateContractStatus.graphql"),
    ("coordination", "coordination", "updateCoordination", "updateCoordinationStatus.graphql"),
)


class UpdateItemStatusTest(ActionTestCase):
    def test_blank_item_or_status_is_refused_without_a_request(self) -> None:
        for module, *_rest in STATUS_UPDATE_CASES:
            for item_id, status_id in (("", "s"), ("  ", "s"), (None, "s"), ("7", ""), ("7", "  "), ("7", None)):
                with self.subTest(module=module, item_id=item_id, status_id=status_id):
                    self.assertIsNone(APIModuleActions.update_item_status(module, item_id, status_id))
        self.loader.load_query_by_module.assert_not_called()
        self.client.send_query.assert_not_called()

    def test_module_without_a_status_change_is_refused_without_a_request(self) -> None:
        for module in ("property", "letter", "settings", "", None, "nonsense"):
            with self.subTest(module=module):
                self.assertIsNone(APIModuleActions.update_item_status(module, "7", "s2"))
        self.loader.load_query_by_module.assert_not_called()
        self.client.send_query.assert_not_called()
        self.log.assert_not_called()

    def test_sends_the_status_id_and_returns_the_updated_item(self) -> None:
        for module, entity, root, filename in STATUS_UPDATE_CASES:
            with self.subTest(module=module):
                self.reset_calls()
                updated = {"id": "7", "status": {"id": "s2"}}
                self.client.send_query.return_value = {root: updated}
                self.assertIs(APIModuleActions.update_item_status(module, " 7 ", " s2 "), updated)
                self.assertEqual(self.loaded(), [(entity, filename)])
                self.assertEqual(self.sent(), [(f"query {entity}/{filename}",
                                                {"variables": {"input": {"id": "7", "status": "s2"}}})])
                self.log.assert_not_called()

    def test_module_name_is_normalised(self) -> None:
        self.client.send_query.return_value = {"updateTask": {"id": "7", "status": {"id": "s2"}}}
        self.assertIsNotNone(APIModuleActions.update_item_status(" Works ", "7", "s2"))
        self.assertEqual(self.loaded(), [("task", "updateTaskStatus.graphql")])

    def test_answered_status_is_compared_as_text_with_the_requested_one(self) -> None:
        for module, _entity, root, _filename in STATUS_UPDATE_CASES:
            with self.subTest(module=module):
                updated = {"id": "7", "status": {"id": 2}}
                self.client.send_query.return_value = {root: updated}
                self.assertIs(APIModuleActions.update_item_status(module, "7", " 2 "), updated)
        self.log.assert_not_called()

    def test_answer_without_the_item_or_the_requested_status_is_logged_as_not_applied(self) -> None:
        for module, entity, root, _filename in STATUS_UPDATE_CASES:
            answers = (None, {}, "text", {root: None}, {root: "x"}, {root: {}},
                       {root: {"id": "7"}}, {root: {"id": "7", "status": "x"}},
                       {root: {"id": "7", "status": {"name": "no id"}}},
                       {root: {"id": "7", "status": {"id": "other"}}},
                       {root: {"id": "", "status": {"id": "s2"}}},
                       {root: {"status": {"id": "s2"}}})
            for response in answers:
                with self.subTest(module=module, response=response):
                    self.log.reset_mock()
                    self.client.send_query.return_value = response
                    self.assertIsNone(APIModuleActions.update_item_status(module, "7", "s2"))
                    self.assert_logged(RuntimeError, module=entity, event=f"{entity}_update_status_not_applied",
                                       extra={"item_id": "7", "status_id": "s2"})
                    self.assertEqual(str(self.log.call_args.args[0]), f"{root} did not return the requested status")

    def test_failed_request_returns_none_and_is_logged(self) -> None:
        for module, entity, _root, _filename in STATUS_UPDATE_CASES:
            with self.subTest(module=module):
                self.log.reset_mock()
                error = RuntimeError("offline")
                self.client.send_query.side_effect = error
                self.assertIsNone(APIModuleActions.update_item_status(module, " 7 ", " s2 "))
                self.assert_logged(error, module=entity, event=f"{entity}_update_status_failed",
                                   extra={"item_id": "7", "status_id": "s2"})

    def test_unloadable_query_returns_none_and_is_logged(self) -> None:
        for module, entity, _root, _filename in STATUS_UPDATE_CASES:
            with self.subTest(module=module):
                self.reset_calls()
                self.log.reset_mock()
                error = FileNotFoundError("query_file_not_found")
                self.loader.load_query_by_module.side_effect = error
                self.assertIsNone(APIModuleActions.update_item_status(module, " 7 ", " s2 "))
                self.client.send_query.assert_not_called()
                self.assert_logged(error, module=entity, event=f"{entity}_update_status_failed",
                                   extra={"item_id": "7", "status_id": "s2"})


class UpdateTaskMembersTest(ActionTestCase):
    def test_blank_task_or_no_members_is_refused_without_a_request(self) -> None:
        for item_id, members in (("", [{"id": "1"}]), (" ", [{"id": "1"}]), (None, [{"id": "1"}]),
                                 ("7", []), ("7", None), ("7", [None, {}, ""])):
            with self.subTest(item_id=item_id, members=members):
                self.assertIs(APIModuleActions.update_task_members(item_id, members), False)
        self.loader.load_query_by_module.assert_not_called()
        self.client.send_query.assert_not_called()

    def test_empty_entries_are_dropped_and_the_rest_sent_as_given(self) -> None:
        self.client.send_query.return_value = {"updateTask": {"id": "7"}}
        members = [{"id": "1", "responsible": True}, None, {}, {"id": "2"}, "3"]
        self.assertIs(APIModuleActions.update_task_members(" 7 ", members), True)
        self.assertEqual(self.loaded(), [("task", "updateTaskMembers.graphql")])
        self.assertEqual(self.sent(), [(TASK_MEMBERS_QUERY, {"variables": {"input": {
            "id": "7", "members": {"associate": [{"id": "1", "responsible": True}, {"id": "2"}, "3"]},
        }}})])

    def test_answer_without_the_task_id_is_a_silent_false(self) -> None:
        for response in (None, {}, "text", {"updateTask": None}, {"updateTask": {"id": None}}):
            with self.subTest(response=response):
                self.client.send_query.return_value = response
                self.assertIs(APIModuleActions.update_task_members("7", [{"id": "1"}]), False)
        self.log.assert_not_called()

    def test_answer_of_the_wrong_type_is_logged_like_a_failed_request(self) -> None:
        self.client.send_query.return_value = {"updateTask": "x"}
        self.assertIs(APIModuleActions.update_task_members("7", [{"id": "1"}]), False)
        self.assert_logged(AttributeError, module="task", event="task_update_members_failed", extra={"item_id": "7"})

    def test_failed_request_returns_false_and_is_logged(self) -> None:
        error = RuntimeError("offline")
        self.client.send_query.side_effect = error
        self.assertIs(APIModuleActions.update_task_members(" 7 ", [{"id": "1"}]), False)
        self.assert_logged(error, module="task", event="task_update_members_failed", extra={"item_id": "7"})

    def test_unloadable_query_returns_false_and_is_logged(self) -> None:
        error = FileNotFoundError("query_file_not_found")
        self.loader.load_query_by_module.side_effect = error
        self.assertIs(APIModuleActions.update_task_members(" 7 ", [{"id": "1"}]), False)
        self.client.send_query.assert_not_called()
        self.assert_logged(error, module="task", event="task_update_members_failed", extra={"item_id": "7"})


class UpdateGeometryTest(ActionTestCase):
    """update_task_geometry, update_project_geometry and update_easement_geometry share _update_module_geometry."""

    CASES = (
        ("update_task_geometry", "task", "updateTaskGeometry.graphql", "updateTask",
         "task_update_geometry_failed", "task_update_geometry_empty_response"),
        ("update_project_geometry", "project", "updateProjectGeometry.graphql", "updateProject",
         "project_update_geometry_failed", "project_update_geometry_empty_response"),
        ("update_easement_geometry", "easement", "updateEasementGeometry.graphql", "updateEasement",
         "easement_update_geometry_failed", "easement_update_geometry_empty_response"),
    )

    def each_case(self, check) -> None:
        """Run check(update, module, filename, key, failure_event, empty_event) once per public method."""
        for method, *details in self.CASES:
            with self.subTest(method=method):
                self.reset_calls()
                self.client.send_query.side_effect = None
                self.client.send_query.return_value = None
                check(getattr(APIModuleActions, method), *details)

    def test_blank_id_or_a_geometry_that_is_no_dict_is_refused_without_a_request(self) -> None:
        def check(update, *_details) -> None:
            for item_id, geometry in (("", POINT), ("  ", POINT), (None, POINT), ("7", None), ("7", "text"), ("7", [1, 2])):
                self.assertIs(update(item_id, geometry), False)
            self.loader.load_query_by_module.assert_not_called()
            self.client.send_query.assert_not_called()

        self.each_case(check)

    def test_sends_the_geometry_as_compact_json_and_returns_true_on_the_updated_id(self) -> None:
        def check(update, module, filename, key, _failure_event, _empty_event) -> None:
            self.client.send_query.return_value = {key: {"id": "7"}}
            self.assertIs(update(" 7 ", POINT), True)
            self.assertEqual(self.loaded(), [(module, filename)])
            self.assertEqual(self.sent(), [(f"query {module}/{filename}", {"variables": {
                "input": {"id": "7", "geometry": POINT_TEXT},
            }})])
            self.log.assert_not_called()

        self.each_case(check)

    def test_task_geometry_can_carry_property_links(self) -> None:
        self.client.send_query.return_value = {"updateTask": {"id": "7"}}
        self.assertIs(APIModuleActions.update_task_geometry("7", POINT, property_ids=[" p1 ", ""]), True)
        self.assertEqual(self.sent()[0][1]["variables"]["input"],
                         {"id": "7", "geometry": POINT_TEXT, "properties": {"associate": ["p1"]}})
        self.client.send_query.reset_mock()
        APIModuleActions.update_task_geometry("7", POINT, property_ids=[" "])
        self.assertEqual(self.sent()[0][1]["variables"]["input"], {"id": "7", "geometry": POINT_TEXT})

    def test_empty_dict_geometry_is_sent(self) -> None:
        def check(update, _module, _filename, key, _failure_event, _empty_event) -> None:
            self.client.send_query.return_value = {key: {"id": "7"}}
            self.assertIs(update("7", {}), True)
            self.assertEqual(self.sent()[0][1]["variables"]["input"]["geometry"], "{}")

        self.each_case(check)

    def test_answer_without_the_id_is_false_and_logged(self) -> None:
        def check(update, module, _filename, key, _failure_event, empty_event) -> None:
            for response in (None, {}, "text", {"other": {"id": "7"}}, {key: None}, {key: {}}, {key: {"id": ""}}):
                self.log.reset_mock()
                self.client.send_query.return_value = response
                self.assertIs(update(" 7 ", POINT), False)
                self.assert_logged(RuntimeError, module=module, event=empty_event,
                                   extra={"item_id": "7", "geometry_type": "Point"})
                self.assertEqual(str(self.log.call_args.args[0]), f"{key} geometry update returned no id")

        self.each_case(check)

    def test_empty_response_log_names_a_missing_geometry_type_as_empty(self) -> None:
        self.client.send_query.return_value = {"updateTask": {}}
        self.assertIs(APIModuleActions.update_task_geometry("7", {"coordinates": [1, 2]}), False)
        self.assertEqual(self.log.call_args.kwargs["extra"], {"item_id": "7", "geometry_type": ""})

    def test_answer_of_the_wrong_type_is_logged_like_a_failed_request(self) -> None:
        def check(update, module, _filename, key, failure_event, _empty_event) -> None:
            self.client.send_query.return_value = {key: "x"}
            self.assertIs(update("7", POINT), False)
            self.assert_logged(AttributeError, module=module, event=failure_event, extra={"item_id": "7"})

        self.each_case(check)

    def test_failed_request_returns_false_and_is_logged(self) -> None:
        def check(update, module, _filename, _key, failure_event, _empty_event) -> None:
            error = RuntimeError("offline")
            self.client.send_query.side_effect = error
            self.assertIs(update(" 7 ", POINT), False)
            self.assert_logged(error, module=module, event=failure_event, extra={"item_id": "7"})

        self.each_case(check)

    def test_unloadable_query_returns_false_and_is_logged(self) -> None:
        error = FileNotFoundError("query_file_not_found")

        def check(update, module, _filename, _key, failure_event, _empty_event) -> None:
            self.assertIs(update(" 7 ", POINT), False)
            self.client.send_query.assert_not_called()
            self.assert_logged(error, module=module, event=failure_event, extra={"item_id": "7"})

        self.loader.load_query_by_module.side_effect = error
        self.each_case(check)

    def test_shared_helper_takes_any_module(self) -> None:
        self.client.send_query.return_value = {"updateContract": {}}
        result = APIModuleActions._update_module_geometry(
            item_id="c1", geometry={"type": "Polygon"}, module="contract", query_filename="updateContractGeometry.graphql",
            response_key="updateContract", failure_event="contract_failed", empty_event="contract_empty",
        )
        self.assertIs(result, False)
        self.assertEqual(self.loaded(), [("contract", "updateContractGeometry.graphql")])
        self.assert_logged(RuntimeError, module="contract", event="contract_empty",
                           extra={"item_id": "c1", "geometry_type": "Polygon"})


class CanUpdateStatusTest(unittest.TestCase):
    def test_every_module_with_a_status_change_says_yes_and_a_task_section_counts_as_a_task(self) -> None:
        for module, *_rest in STATUS_UPDATE_CASES:
            with self.subTest(module=module):
                self.assertTrue(APIModuleActions.can_update_status(module))
        self.assertTrue(APIModuleActions.can_update_status(" Works "))

    def test_other_modules_say_no(self) -> None:
        for module in ("property", "letter", "settings", "", None, "nonsense"):
            with self.subTest(module=module):
                self.assertFalse(APIModuleActions.can_update_status(module))

    def test_every_status_change_has_its_query_file_in_the_module_folder(self) -> None:
        loader = GraphQLQueryLoader()
        for module, entity, root, filename in STATUS_UPDATE_CASES:
            with self.subTest(module=module):
                text = loader.load_query_by_module(entity, filename)
                self.assertIn(f"{root}(input: $input)", text)
                self.assertIn("status {", text)


class GetItemStatusTest(ActionTestCase):
    def test_blank_id_returns_none_without_a_request(self) -> None:
        for item_id in ("", "  ", None):
            with self.subTest(item_id=item_id):
                self.assertIsNone(APIModuleActions.get_item_status("easement", item_id))
        self.loader.load_query_by_module.assert_not_called()
        self.client.send_query.assert_not_called()

    def test_module_without_a_status_read_returns_none_without_a_request(self) -> None:
        for module in ("works", "asbuilt", "task", "project", "", None):
            with self.subTest(module=module):
                self.assertIsNone(APIModuleActions.get_item_status(module, "7"))
        self.loader.load_query_by_module.assert_not_called()
        self.client.send_query.assert_not_called()
        self.log.assert_not_called()

    def test_loads_the_easement_status_query_and_returns_the_status(self) -> None:
        status = {"id": "2", "name": "Allkirjastatud", "color": "2188FF"}
        self.client.send_query.return_value = {"easement": {"id": "7", "status": status}}
        self.assertIs(APIModuleActions.get_item_status("easement", " 7 "), status)
        self.assertEqual(self.loaded(), [("easement", "easementStatus.graphql")])
        self.assertEqual(self.sent(), [(EASEMENT_STATUS_QUERY, {"variables": {"id": "7"}})])

    def test_status_without_an_id_or_a_broken_answer_is_none_without_a_log(self) -> None:
        answers = (None, {}, "text", {"easement": None}, {"easement": "x"}, {"easement": {"status": None}},
                   {"easement": {"status": "x"}}, {"easement": {"status": {"name": "x"}}},
                   {"easement": {"status": {"id": "  "}}})
        for response in answers:
            with self.subTest(response=response):
                self.client.send_query.return_value = response
                self.assertIsNone(APIModuleActions.get_item_status("easement", "7"))
        self.log.assert_not_called()

    def test_failed_request_returns_none_and_is_logged(self) -> None:
        error = RuntimeError("offline")
        self.client.send_query.side_effect = error
        self.assertIsNone(APIModuleActions.get_item_status("easement", " 7 "))
        self.assert_logged(error, module="easement", event="easement_status_fetch_failed", extra={"item_id": "7"})

    def test_unloadable_query_returns_none_and_is_logged(self) -> None:
        error = FileNotFoundError("query_file_not_found")
        self.loader.load_query_by_module.side_effect = error
        self.assertIsNone(APIModuleActions.get_item_status("easement", "7"))
        self.client.send_query.assert_not_called()
        self.assert_logged(error, module="easement", event="easement_status_fetch_failed", extra={"item_id": "7"})


class CreateTaskTestCase(ActionTestCase):
    """The logged-in user "me" is in the session, so the create needs no user request."""

    def setUp(self) -> None:
        super().setUp()
        self.session.loggedInUser = {"id": "me", "displayName": "Mina"}

    def create(self, **kwargs):
        arguments = {"title": "Avarii", "type_id": "t1"}
        arguments.update(kwargs)
        return APIModuleActions.create_task(**arguments)

    def create_inputs(self) -> list:
        return [kwargs["variables"]["input"] for query, kwargs in self.sent() if query == CREATE_QUERY]

    def follow_ups(self) -> list:
        return [(query, kwargs["variables"]["input"]) for query, kwargs in self.sent() if query != CREATE_QUERY]

    def assert_create_failed(self, error) -> None:
        self.assert_logged(error, module="task", event="task_create_failed", extra={"title": "Avarii", "type_id": "t1"})


class CreateTaskInputTest(CreateTaskTestCase):
    def test_blank_title_or_type_returns_none_without_any_request(self) -> None:
        self.session.loggedInUser = None
        for title, type_id in (("", "t1"), ("  ", "t1"), (None, "t1"), ("Avarii", ""), ("Avarii", " "), ("Avarii", None)):
            with self.subTest(title=title, type_id=type_id):
                self.assertIsNone(APIModuleActions.create_task(title=title, type_id=type_id))
        self.loader.load_query_by_module.assert_not_called()
        self.client.send_query.assert_not_called()
        self.log.assert_not_called()

    def test_smallest_input_makes_the_current_user_the_responsible_member(self) -> None:
        self.client.send_query.return_value = {"createTask": {"id": "77"}}
        self.assertEqual(APIModuleActions.create_task(title=" Avarii ", type_id=" t1 "), "77")
        self.assertEqual(self.loaded(), [("task", "createTask.graphql")])
        self.assertEqual(self.create_inputs(), [{
            "title": "Avarii", "typeId": "t1", "description": "",
            "members": {"associate": [{"id": "me", "responsible": True}]},
        }])
        self.assertEqual(self.follow_ups(), [])
        self.log.assert_not_called()

    def test_every_field_is_sent_in_one_request(self) -> None:
        self.client.send_query.return_value = {"createTask": {"id": 77}}
        task_id = self.create(
            description="<p>Märkus</p>", priority=" high ", start_at="2026-11-20", due_at="2026-11-27",
            member_ids=["u3", " u2 ", "", "me"], responsible_id=" u2 ", status_id=" s1 ", geometry=POINT,
        )
        self.assertEqual(task_id, "77")
        self.assertEqual(self.create_inputs(), [{
            "title": "Avarii", "typeId": "t1", "description": "<p>Märkus</p>", "priority": "HIGH",
            "startAt": "2026-11-20", "dueAt": "2026-11-27", "status": "s1", "geometry": POINT_TEXT,
            "members": {"associate": [
                {"id": "u2", "responsible": True}, {"id": "me", "responsible": False}, {"id": "u3", "responsible": False},
            ]},
        }])
        self.assertEqual(self.follow_ups(), [])
        self.log.assert_not_called()

    def test_property_ids_are_linked_by_the_create(self) -> None:
        self.client.send_query.return_value = {"createTask": {"id": "77"}}
        self.assertEqual(self.create(property_ids=[" p1 ", "", "p2", "p1"]), "77")
        self.assertEqual(self.create_inputs()[0]["properties"], {"associate": ["p1", "p2"]})
        self.assertEqual(self.follow_ups(), [])
        self.client.send_query.reset_mock()
        self.create(property_ids=[" "])
        self.assertNotIn("properties", self.create_inputs()[0])

    def test_refused_properties_are_dropped_and_the_task_is_still_created(self) -> None:
        refused = 'Variable "$input" got invalid value "p1" at "input.properties.associate[0]"'
        for message in (refused, "Property p1 not found", "Field \"properties\" is not defined by type CreateTaskInput"):
            with self.subTest(message=message):
                self.reset_calls()
                self.answer({CREATE_QUERY: [rejected(message), {"createTask": {"id": "77"}}]})
                self.assertEqual(self.create(property_ids=["p1"], geometry=POINT), "77")
                first, second = self.create_inputs()
                self.assertEqual(first["properties"], {"associate": ["p1"]})
                self.assertNotIn("properties", second)
                self.assertEqual(second["geometry"], POINT_TEXT)
                self.log.assert_not_called()

    def test_property_error_is_not_retried_without_properties(self) -> None:
        error = rejected("Property p1 not found")
        self.client.send_query.side_effect = error
        self.assertIsNone(self.create())
        self.assertEqual(self.queries(), [CREATE_QUERY])
        self.assert_create_failed(error)

    def test_refusal_that_names_no_property_keeps_the_properties_and_is_not_retried(self) -> None:
        error = rejected(REFUSED)
        self.client.send_query.side_effect = error
        self.assertIsNone(self.create(property_ids=["p1"]))
        self.assertEqual(self.queries(), [CREATE_QUERY])
        self.assert_create_failed(error)

    def test_empty_optional_fields_are_left_out(self) -> None:
        self.client.send_query.return_value = {"createTask": {"id": "77"}}
        self.create(description=None, priority="", start_at="", due_at=None, status_id="  ", geometry=None)
        self.assertEqual(self.create_inputs(), [{
            "title": "Avarii", "typeId": "t1", "members": {"associate": [{"id": "me", "responsible": True}]},
        }])

    def test_values_are_sent_as_text(self) -> None:
        self.client.send_query.return_value = {"createTask": {"id": "77"}}
        self.create(description=5, priority=" low ", start_at=datetime.date(2026, 11, 20), due_at=20261127)
        sent = self.create_inputs()[0]
        self.assertEqual((sent["description"], sent["priority"], sent["startAt"], sent["dueAt"]),
                         ("5", "LOW", "2026-11-20", "20261127"))

    def test_blank_priority_is_left_out(self) -> None:
        self.client.send_query.return_value = {"createTask": {"id": "77"}}
        for priority in ("", "  ", "\t", None):
            with self.subTest(priority=priority):
                self.reset_calls()
                self.create(priority=priority)
                self.assertNotIn("priority", self.create_inputs()[0])

    def test_none_member_id_is_not_sent_as_text(self) -> None:
        self.client.send_query.return_value = {"createTask": {"id": "77"}}
        self.create(member_ids=[None, "u3", ""])
        self.assertEqual(self.create_inputs()[0]["members"], {"associate": [
            {"id": "me", "responsible": True}, {"id": "u3", "responsible": False},
        ]})

    def test_geometry_that_is_no_dict_is_left_out_and_an_empty_dict_is_sent(self) -> None:
        self.client.send_query.return_value = {"createTask": {"id": "77"}}
        for geometry, expected in (("text", None), ([1, 2], None), ({}, "{}")):
            with self.subTest(geometry=geometry):
                self.reset_calls()
                self.create(geometry=geometry)
                self.assertEqual(self.create_inputs()[0].get("geometry"), expected)

    def test_responsible_defaults_to_the_current_user(self) -> None:
        self.client.send_query.return_value = {"createTask": {"id": "77"}}
        self.create(member_ids=["u3", "me"], responsible_id="  ")
        self.assertEqual(self.create_inputs()[0]["members"], {"associate": [
            {"id": "me", "responsible": True}, {"id": "u3", "responsible": False},
        ]})

    def test_current_user_is_fetched_first_when_the_session_has_none(self) -> None:
        self.session.loggedInUser = None
        self.answer({ME_QUERY: {"me": {"id": "me"}}, CREATE_QUERY: {"createTask": {"id": "77"}}})
        self.assertEqual(self.create(responsible_id="u2"), "77")
        self.assertEqual(self.loaded(), [("user", "me.graphql"), ("task", "createTask.graphql")])
        self.assertEqual(self.queries(), [ME_QUERY, CREATE_QUERY])
        self.assertEqual(self.create_inputs()[0]["members"], {"associate": [
            {"id": "u2", "responsible": True}, {"id": "me", "responsible": False},
        ]})

    def test_without_a_current_user_or_responsible_no_member_is_flagged(self) -> None:
        self.session.loggedInUser = None
        for member_ids, members in ((["u3", " u4 "], {"associate": [{"id": "u3"}, {"id": "u4"}]}), ([], None)):
            with self.subTest(member_ids=member_ids):
                self.reset_calls()
                self.answer({ME_QUERY: {"me": None}, CREATE_QUERY: {"createTask": {"id": "77"}}})
                self.assertEqual(self.create(member_ids=member_ids), "77")
                self.assertEqual(self.create_inputs()[0].get("members"), members)

    def test_without_a_current_user_the_chosen_responsible_is_flagged(self) -> None:
        self.session.loggedInUser = None
        self.answer({ME_QUERY: RuntimeError("offline"), CREATE_QUERY: {"createTask": {"id": "77"}}})
        self.assertEqual(self.create(responsible_id="u2", member_ids=["u3"]), "77")
        self.assertEqual(self.create_inputs()[0]["members"], {"associate": [
            {"id": "u2", "responsible": True}, {"id": "u3", "responsible": False},
        ]})
        self.assertEqual([call.kwargs["event"] for call in self.log.call_args_list], ["current_user_fetch_failed"])


class CreateTaskAnswerTest(CreateTaskTestCase):
    def test_answer_without_a_task_id_returns_none_without_a_log_or_follow_up(self) -> None:
        answers = (None, {}, "text", [], {"createTask": None}, {"createTask": {}}, {"createTask": {"id": None}},
                   {"createTask": {"id": ""}}, {"createTask": {"id": 0}})
        for response in answers:
            with self.subTest(response=response):
                self.reset_calls()
                self.answer({CREATE_QUERY: [rejected(STATUS_UNKNOWN), response]})
                self.assertIsNone(self.create(status_id="s1"))
                self.assertEqual(self.queries(), [CREATE_QUERY, CREATE_QUERY])
                self.log.assert_not_called()

    def test_answer_of_the_wrong_type_is_logged_like_a_failed_create(self) -> None:
        self.client.send_query.return_value = {"createTask": "x"}
        self.assertIsNone(self.create())
        self.assert_create_failed(AttributeError)

    def test_error_that_no_branch_retries_is_logged_once_with_the_stripped_title_and_type(self) -> None:
        for message in (REFUSED, "[WC-API][network] offline", "HTTP 400"):
            with self.subTest(message=message):
                self.reset_calls()
                error = RuntimeError(message)
                self.client.send_query.side_effect = error
                self.assertIsNone(APIModuleActions.create_task(
                    title=" Avarii ", type_id=" t1 ", status_id="s1", responsible_id="u2", geometry=POINT,
                ))
                self.assertEqual(self.queries(), [CREATE_QUERY])
                self.assert_create_failed(error)

    def test_unloadable_create_query_returns_none_and_is_logged(self) -> None:
        self.missing_query("createTask.graphql")
        self.assertIsNone(self.create())
        self.client.send_query.assert_not_called()
        self.assert_create_failed(FileNotFoundError)


class CreateTaskRetryTest(CreateTaskTestCase):
    def test_unknown_status_field_is_retried_without_the_status_and_the_status_is_set_afterwards(self) -> None:
        self.answer({
            CREATE_QUERY: [rejected(STATUS_UNKNOWN), {"createTask": {"id": "77"}}],
            TASK_STATUS_QUERY: STATUS_SET,
        })
        self.assertEqual(self.create(status_id=" s1 ", geometry=POINT), "77")
        first, second = self.create_inputs()
        self.assertEqual(first["status"], "s1")
        self.assertNotIn("status", second)
        self.assertEqual({key: value for key, value in first.items() if key != "status"}, second)
        self.assertEqual(self.follow_ups(), [(TASK_STATUS_QUERY, {"id": "77", "status": "s1"})])
        self.assertEqual(self.loaded(), [("task", "createTask.graphql"), ("task", "updateTaskStatus.graphql")])
        self.log.assert_not_called()

    def test_status_error_is_retried_only_when_a_status_was_sent_and_the_field_is_unknown(self) -> None:
        cases = (
            (None, STATUS_UNKNOWN),
            ("s1", 'status "s1" is invalid'),
            ("s1", '[WC-API][graphql] Field "statusId" is not defined by type "CreateTaskInput".'),
            ("s1", '[WC-API][graphql] Field "priority" is not defined by type "CreateTaskInput".'),
        )
        for status_id, message in cases:
            with self.subTest(status_id=status_id, message=message):
                self.reset_calls()
                error = rejected(message)
                self.client.send_query.side_effect = error
                self.assertIsNone(self.create(status_id=status_id))
                self.assertEqual(self.queries(), [CREATE_QUERY])
                self.assert_create_failed(error)

    def test_refused_responsible_flag_is_retried_without_flags_and_the_members_are_sent_again(self) -> None:
        self.answer({
            CREATE_QUERY: [rejected(FLAG_REFUSED), {"createTask": {"id": "77"}}],
            TASK_MEMBERS_QUERY: {"updateTask": {"id": "77"}},
        })
        self.assertEqual(self.create(responsible_id="u2", member_ids=["u3"], geometry=POINT), "77")
        first, second = self.create_inputs()
        flagged = [{"id": "u2", "responsible": True}, {"id": "me", "responsible": False}, {"id": "u3", "responsible": False}]
        self.assertEqual(first["members"], {"associate": flagged})
        self.assertEqual(second["members"], {"associate": [{"id": "u2"}, {"id": "me"}, {"id": "u3"}]})
        self.assertEqual(second["geometry"], POINT_TEXT)
        self.assertEqual(self.follow_ups(), [(TASK_MEMBERS_QUERY, {"id": "77", "members": {"associate": flagged}})])
        self.log.assert_not_called()

    def test_flag_retry_with_the_current_user_as_the_responsible(self) -> None:
        self.answer({
            CREATE_QUERY: [rejected(FLAG_REFUSED), {"createTask": {"id": "77"}}],
            TASK_MEMBERS_QUERY: {"updateTask": {"id": "77"}},
        })
        self.assertEqual(self.create(), "77")
        self.assertEqual(self.create_inputs()[1]["members"], {"associate": [{"id": "me"}]})
        self.assertEqual(self.follow_ups(), [
            (TASK_MEMBERS_QUERY, {"id": "77", "members": {"associate": [{"id": "me", "responsible": True}]}}),
        ])

    def test_flag_error_needs_both_texts(self) -> None:
        for message in ('invalid value at "input.members.associate[0]"', 'Field "responsible" is not defined'):
            with self.subTest(message=message):
                self.reset_calls()
                error = rejected(message)
                self.client.send_query.side_effect = error
                self.assertIsNone(self.create(responsible_id="u2"))
                self.assertEqual(self.queries(), [CREATE_QUERY])
                self.assert_create_failed(error)

    def test_flag_error_is_found_in_any_letter_case(self) -> None:
        for message in ('INPUT.MEMBERS.ASSOCIATE[0] RESPONSIBLE', 'input.MEMBERS.ASSOCIATE[0]: Field "responsible"',
                        'input.members.associate[0]: Field "RESPONSIBLE"'):
            with self.subTest(message=message):
                self.reset_calls()
                self.answer({
                    CREATE_QUERY: [rejected(message), {"createTask": {"id": "77"}}],
                    TASK_MEMBERS_QUERY: {"updateTask": {"id": "77"}},
                })
                self.assertEqual(self.create(responsible_id="u2"), "77")
                first, second = self.create_inputs()
                self.assertIn("responsible", first["members"]["associate"][0])
                self.assertEqual(second["members"], {"associate": [{"id": "u2"}, {"id": "me"}]})
                self.assertEqual([query for query, _input in self.follow_ups()], [TASK_MEMBERS_QUERY])
                self.log.assert_not_called()

    def test_flag_error_is_not_retried_when_no_member_carries_a_flag(self) -> None:
        self.session.loggedInUser = None
        for member_ids in (["u3"], []):
            with self.subTest(member_ids=member_ids):
                self.reset_calls()
                error = rejected(FLAG_REFUSED)
                self.answer({ME_QUERY: {"me": None}, CREATE_QUERY: error})
                self.assertIsNone(self.create(member_ids=member_ids))
                self.assertEqual(self.queries(), [ME_QUERY, CREATE_QUERY])
                self.assert_create_failed(error)

    def test_geometry_error_is_retried_without_the_geometry_and_the_geometry_is_not_sent_again(self) -> None:
        self.answer({CREATE_QUERY: [rejected(GEOMETRY_ERROR), {"createTask": {"id": "77"}}]})
        self.assertEqual(self.create(geometry=POINT, status_id="s1"), "77")
        first, second = self.create_inputs()
        self.assertEqual(first["geometry"], POINT_TEXT)
        self.assertNotIn("geometry", second)
        self.assertEqual({key: value for key, value in first.items() if key != "geometry"}, second)
        self.assertEqual(self.follow_ups(), [])
        self.log.assert_not_called()

    def test_every_geometry_marker_triggers_the_geometry_retry(self) -> None:
        for message in GeometryRetryableCreateErrorTest.RETRYABLE:
            with self.subTest(message=message):
                self.reset_calls()
                self.answer({CREATE_QUERY: [rejected(message), {"createTask": {"id": "77"}}]})
                self.assertEqual(self.create(geometry=POINT), "77")
                self.assertEqual(["geometry" in sent for sent in self.create_inputs()], [True, False])

    def test_geometry_error_is_retried_only_when_a_geometry_was_sent(self) -> None:
        for geometry in (None, "text"):
            with self.subTest(geometry=geometry):
                self.reset_calls()
                error = rejected(GEOMETRY_ERROR)
                self.client.send_query.side_effect = error
                self.assertIsNone(self.create(geometry=geometry))
                self.assertEqual(self.queries(), [CREATE_QUERY])
                self.assert_create_failed(error)

    def test_one_error_for_every_branch_drops_status_then_flags_then_geometry(self) -> None:
        error = rejected(EVERY_BRANCH)
        self.answer({
            CREATE_QUERY: [error, error, error, {"createTask": {"id": "77"}}],
            TASK_MEMBERS_QUERY: {"updateTask": {"id": "77"}},
            TASK_STATUS_QUERY: STATUS_SET,
        })
        self.assertEqual(self.create(responsible_id="u2", status_id="s1", geometry=POINT), "77")
        shape = [("status" in sent, "responsible" in sent["members"]["associate"][0], "geometry" in sent)
                 for sent in self.create_inputs()]
        self.assertEqual(shape, [(True, True, True), (False, True, True), (False, False, True), (False, False, False)])
        flagged = [{"id": "u2", "responsible": True}, {"id": "me", "responsible": False}]
        self.assertEqual(self.follow_ups(), [
            (TASK_MEMBERS_QUERY, {"id": "77", "members": {"associate": flagged}}),
            (TASK_STATUS_QUERY, {"id": "77", "status": "s1"}),
        ])
        self.log.assert_not_called()

    def test_input_is_simplified_in_the_order_the_errors_arrive(self) -> None:
        self.answer({
            CREATE_QUERY: [rejected(GEOMETRY_ERROR), rejected(FLAG_REFUSED), rejected(STATUS_UNKNOWN),
                           {"createTask": {"id": "77"}}],
            TASK_MEMBERS_QUERY: {"updateTask": {"id": "77"}},
            TASK_STATUS_QUERY: STATUS_SET,
        })
        self.assertEqual(self.create(responsible_id="u2", status_id="s1", geometry=POINT), "77")
        shape = [("status" in sent, "responsible" in sent["members"]["associate"][0], "geometry" in sent)
                 for sent in self.create_inputs()]
        self.assertEqual(shape, [(True, True, True), (True, True, False), (True, False, False), (False, False, False)])
        self.assertEqual([query for query, _input in self.follow_ups()], [TASK_MEMBERS_QUERY, TASK_STATUS_QUERY])

    def test_four_attempts_at_most_then_the_last_error_is_logged(self) -> None:
        errors = [rejected(EVERY_BRANCH) for _ in range(5)]
        self.answer({CREATE_QUERY: list(errors)})
        self.assertIsNone(self.create(responsible_id="u2", status_id="s1", geometry=POINT))
        self.assertEqual(self.queries(), [CREATE_QUERY] * 4)
        self.assert_create_failed(errors[3])

    def test_without_a_flag_to_drop_three_attempts_at_most(self) -> None:
        self.session.loggedInUser = None
        errors = [rejected(EVERY_BRANCH) for _ in range(4)]
        self.answer({ME_QUERY: {"me": None}, CREATE_QUERY: list(errors)})
        self.assertIsNone(self.create(member_ids=["u3"], status_id="s1", geometry=POINT))
        self.assertEqual(self.queries(), [ME_QUERY] + [CREATE_QUERY] * 3)
        shape = [("status" in sent, "geometry" in sent, sent["members"]) for sent in self.create_inputs()]
        no_flags = {"associate": [{"id": "u3"}]}
        self.assertEqual(shape, [(True, True, no_flags), (False, True, no_flags), (False, False, no_flags)])
        self.assert_create_failed(errors[2])

    def test_each_simplification_is_used_once(self) -> None:
        cases = (
            (GEOMETRY_ERROR, {"geometry": POINT}),
            (STATUS_UNKNOWN, {"status_id": "s1"}),
            (FLAG_REFUSED, {"responsible_id": "u2"}),
        )
        for message, arguments in cases:
            with self.subTest(message=message):
                self.reset_calls()
                second = rejected(message)
                self.answer({CREATE_QUERY: [rejected(message), second, {"createTask": {"id": "77"}}]})
                self.assertIsNone(self.create(**arguments))
                self.assertEqual(self.queries(), [CREATE_QUERY, CREATE_QUERY])
                self.assert_create_failed(second)

    def test_failed_follow_ups_do_not_change_the_result(self) -> None:
        status_error = RuntimeError("status offline")
        self.answer({
            CREATE_QUERY: [rejected(EVERY_BRANCH), rejected(EVERY_BRANCH), {"createTask": {"id": "77"}}],
            TASK_MEMBERS_QUERY: {"updateTask": {}},
            TASK_STATUS_QUERY: status_error,
        })
        self.assertEqual(self.create(responsible_id="u2", status_id="s1"), "77")
        self.assertEqual([query for query, _input in self.follow_ups()], [TASK_MEMBERS_QUERY, TASK_STATUS_QUERY])
        self.assert_logged(status_error, module="task", event="task_update_status_failed",
                           extra={"item_id": "77", "status_id": "s1"})

    def test_status_follow_up_that_kavitro_did_not_take_does_not_change_the_result(self) -> None:
        self.answer({
            CREATE_QUERY: [rejected(STATUS_UNKNOWN), {"createTask": {"id": "77"}}],
            TASK_STATUS_QUERY: {"updateTask": {"id": "77", "status": {"id": "other"}}},
        })
        self.assertEqual(self.create(status_id="s1"), "77")
        self.assert_logged(RuntimeError, module="task", event="task_update_status_not_applied",
                           extra={"item_id": "77", "status_id": "s1"})

    def test_unloadable_status_follow_up_query_does_not_undo_the_created_task(self) -> None:
        self.missing_query("updateTaskStatus.graphql")
        self.answer({CREATE_QUERY: [rejected(STATUS_UNKNOWN), {"createTask": {"id": "77"}}]})
        self.assertEqual(self.create(status_id="s1"), "77")
        self.assertEqual(self.queries(), [CREATE_QUERY, CREATE_QUERY])
        self.assert_logged(FileNotFoundError, module="task", event="task_update_status_failed",
                           extra={"item_id": "77", "status_id": "s1"})

    def test_unloadable_members_follow_up_query_does_not_undo_the_created_task(self) -> None:
        self.missing_query("updateTaskMembers.graphql")
        self.answer({CREATE_QUERY: [rejected(FLAG_REFUSED), {"createTask": {"id": "77"}}]})
        self.assertEqual(self.create(responsible_id="u2"), "77")
        self.assertEqual(self.queries(), [CREATE_QUERY, CREATE_QUERY])
        self.assert_logged(FileNotFoundError, module="task", event="task_update_members_failed",
                           extra={"item_id": "77"})

    def test_both_follow_up_queries_unloadable_are_logged_and_the_task_id_is_still_returned(self) -> None:
        def load(module, name):
            if name in ("updateTaskMembers.graphql", "updateTaskStatus.graphql"):
                raise FileNotFoundError(f"query_file_not_found: {name}")
            return self._query_text(module, name)

        self.loader.load_query_by_module.side_effect = load
        error = rejected(EVERY_BRANCH)
        self.answer({CREATE_QUERY: [error, error, {"createTask": {"id": "77"}}]})
        self.assertEqual(self.create(responsible_id="u2", status_id="s1"), "77")
        self.assertEqual(self.queries(), [CREATE_QUERY] * 3)
        self.assertEqual([call.kwargs["event"] for call in self.log.call_args_list],
                         ["task_update_members_failed", "task_update_status_failed"])


class CreateTaskUnknownOutcomeTest(CreateTaskTestCase):
    """After an error that leaves it unknown whether the task exists, nothing is sent again."""

    ERRORS = (
        ApiError(ApiErrorKind.SERVER, "Serveri päring ebaõnnestus (HTTP 504)."),
        ApiError(ApiErrorKind.SERVER, "Server request failed (HTTP 500)."),
        ApiError(ApiErrorKind.NETWORK, "Network error: connection timed out"),
        ApiError(ApiErrorKind.UNKNOWN, "Internal server error"),
        # Errors that are no API errors carry no answer from the server either.
        ValueError(EVERY_BRANCH),
        RuntimeError(GEOMETRY_ERROR),
    )

    def test_create_is_sent_once_and_the_error_is_logged(self) -> None:
        for error in self.ERRORS:
            with self.subTest(error=str(error)):
                self.reset_calls()
                self.answer({CREATE_QUERY: [error, {"createTask": {"id": "77"}}]})
                self.assertIsNone(self.create(responsible_id="u2", status_id="s1", geometry=POINT))
                self.assertEqual(self.queries(), [CREATE_QUERY])
                self.assertEqual(self.follow_ups(), [])
                self.assert_create_failed(error)

    def test_unknown_outcome_after_a_refused_create_stops_the_retries(self) -> None:
        timeout = ApiError(ApiErrorKind.SERVER, "Serveri päring ebaõnnestus (HTTP 504).")
        self.answer({CREATE_QUERY: [rejected(STATUS_UNKNOWN), timeout, {"createTask": {"id": "77"}}]})
        self.assertIsNone(self.create(responsible_id="u2", status_id="s1", geometry=POINT))
        self.assertEqual(self.queries(), [CREATE_QUERY, CREATE_QUERY])
        self.assert_create_failed(timeout)


class MissingCurrentUserQueryTest(CreateTaskTestCase):
    """A me.graphql that cannot be loaded counts as an unknown current user instead of reaching the caller."""

    def setUp(self) -> None:
        super().setUp()
        self.session.loggedInUser = None
        self.missing_query("me.graphql")

    def test_create_task_goes_ahead_without_the_current_user(self) -> None:
        self.client.send_query.return_value = {"createTask": {"id": "77"}}
        self.assertEqual(self.create(responsible_id="u2", member_ids=["u3"]), "77")
        self.assertEqual(self.queries(), [CREATE_QUERY])
        self.assertEqual(self.create_inputs()[0]["members"], {"associate": [
            {"id": "u2", "responsible": True}, {"id": "u3", "responsible": False},
        ]})
        self.assertEqual([call.kwargs["event"] for call in self.log.call_args_list], ["current_user_fetch_failed"])

    def test_works_dialog_opens_without_a_default_responsible(self) -> None:
        # _handle_point_selected asks for it on the GUI thread without a try block.
        controller = controller_module.WorksCreateController()
        self.assertEqual(controller._resolve_default_responsible_id(), "")
        self.client.send_query.assert_not_called()
        self.assertEqual([call.kwargs["event"] for call in self.log.call_args_list], ["current_user_fetch_failed"])


class StatusFilterLoadErrorTest(ActionTestCase):
    """The status filter loads its options in a FunctionWorker; a failed load must reach _handle_load_error."""

    def setUp(self) -> None:
        super().setUp()
        self._patch(workers_module.SwitchLogger, "log")
        self.host = QWidget()
        self.addCleanup(self.delete_host)
        settings = Mock()
        settings.load_module_preference_ids.return_value = []
        self.widget = StatusFilterWidget("works", self.host, auto_load=False,
                                         settings_logic=settings)

    def delete_host(self) -> None:
        self.host.hide()
        self.host.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)

    def load(self) -> tuple[list, list]:
        """Run the filter's load like its worker thread would, and hand the outcome to the widget."""
        finished, errors = [], []
        worker = workers_module.FunctionWorker(self.widget._fetch_options)
        worker.finished.connect(finished.append)
        worker.error.connect(errors.append)
        worker.run()
        request_id = self.widget._load_request_id
        for payload in finished:
            self.widget._handle_load_success(payload, None, request_id)
        for message in errors:
            self.widget._handle_load_error(message, None, request_id)
        return finished, errors

    def test_failed_later_page_is_shown_in_the_filter(self) -> None:
        error = ApiError(ApiErrorKind.NETWORK, "Võrguühendus katkes")
        self.client.send_query.side_effect = [
            {"statuses": {"edges": [{"node": {"id": "1", "name": "Ootel"}}],
                          "pageInfo": {"endCursor": "c1", "hasNextPage": True}}},
            error,
        ]
        finished, errors = self.load()
        self.assertEqual((finished, errors), ([], [str(error)]))
        # The failure is logged once, by the worker that hands it to the filter.
        self.assert_logged(error, module="works", event="worker_error", extra={"func": "_fetch_options"})
        self.assertIn("Võrguühendus katkes", self.widget.selector._display_override)
        self.assertNotIn("[WC-API]", self.widget.selector._display_override)
        self.assertFalse(self.widget.is_loaded())
        self.assertFalse(self.widget.selector.isEnabled())

    def test_read_statuses_fill_the_filter(self) -> None:
        self.client.send_query.return_value = {"statuses": {"edges": [{"node": {"id": "1", "name": "Ootel"}}]}}
        finished, errors = self.load()
        self.assertEqual(errors, [])
        self.assertEqual([option["id"] for option in finished[0]], ["1"])
        self.assertTrue(self.widget.is_loaded())
        self.assertEqual(self.widget.selector.count(), 1)


class QueryFilesTest(unittest.TestCase):
    """The query files the actions load exist where the loader looks for them (the real loader, no request)."""

    def test_every_loaded_query_file_exists(self) -> None:
        cases = (
            ("task", "w_tasks_module_data_by_item_id.graphql", "task(id: $id)"),
            ("task", "ListFilteredTasks.graphql", "tasks(first: $first"),
            ("task", "updateTaskDescription.graphql", "updateTask(input: $input)"),
            ("task", "updateTaskStatus.graphql", "updateTask(input: $input)"),
            ("task", "updateTaskMembers.graphql", "updateTask(input: $input)"),
            ("task", "createTask.graphql", "createTask(input: $input)"),
            ("task", "updateTaskGeometry.graphql", "updateTask(input: $input)"),
            ("project", "updateProjectGeometry.graphql", "updateProject(input: $input)"),
            ("easement", "updateEasementGeometry.graphql", "updateEasement(input: $input)"),
            ("easement", "easementStatus.graphql", "easement(id: $id)"),
            ("easement", "updateEasementStatus.graphql", "updateEasement(input: $input)"),
        )
        loader = GraphQLQueryLoader()
        for module, filename, text in cases:
            with self.subTest(file=filename):
                self.assertIn(text, loader.load_query_by_module(module, filename))


class TaskAndGeometryLayoutTest(unittest.TestCase):
    """The task, geometry and easement status code lives in python/actions/ (red on the single-file layout)."""

    TASKS = (
        "get_task_data", "get_tasks_by_ids", "get_task_description", "update_task_description",
        "update_task_members", "_build_task_member_associate_payload", "create_task",
        "get_task_priority_values", "task_priority_label", "get_task_priority_options",
    )
    GEOMETRY = (
        "_geometry_input_value", "_is_unknown_input_field_error", "_is_unknown_geometry_input_error",
        "_is_geometry_retryable_create_error", "_update_module_geometry", "update_task_geometry",
        "update_project_geometry", "update_easement_geometry",
    )
    EASEMENT_STATUS = ("get_item_status", "update_item_status")
    OWNERS = {
        "Kavitro_dev.python.actions.task_actions": ("TaskActions", TASKS),
        "Kavitro_dev.python.actions.geometry_actions": ("GeometryActions", GEOMETRY),
        "Kavitro_dev.python.actions.status_actions": ("StatusActions", EASEMENT_STATUS),
    }

    @staticmethod
    def source(module_name: str) -> str:
        return Path(importlib.import_module(module_name).__file__).read_text(encoding="utf-8")

    def test_each_domain_class_owns_its_methods(self) -> None:
        for module_name, (class_name, names) in self.OWNERS.items():
            owner = getattr(importlib.import_module(module_name), class_name)
            self.assertTrue(issubclass(APIModuleActions, owner), class_name)
            for name in names:
                with self.subTest(method=name):
                    self.assertIn(name, vars(owner))
                    self.assertIs(getattr(APIModuleActions, name), getattr(owner, name))

    def test_task_and_geometry_classes_inherit_nothing(self) -> None:
        # The task code reaches the geometry and user code through their classes, not through inheritance.
        for module_name, class_name in (("Kavitro_dev.python.actions.task_actions", "TaskActions"),
                                        ("Kavitro_dev.python.actions.geometry_actions", "GeometryActions")):
            with self.subTest(owner=class_name):
                self.assertEqual(getattr(importlib.import_module(module_name), class_name).__bases__, (object,))

    def test_imports_run_one_way(self) -> None:
        task_source = self.source("Kavitro_dev.python.actions.task_actions")
        self.assertIn("from .geometry_actions import GeometryActions", task_source)
        self.assertIn("from .user_actions import UserActions", task_source)
        for module_name in ("Kavitro_dev.python.actions.geometry_actions", "Kavitro_dev.python.actions.user_actions",
                            "Kavitro_dev.python.actions.status_actions"):
            with self.subTest(module=module_name):
                self.assertNotIn("task_actions", self.source(module_name))
        geometry_source = self.source("Kavitro_dev.python.actions.geometry_actions")
        for other in ("user_actions", "status_actions", "file_actions", "property_link_actions"):
            with self.subTest(geometry_imports=other):
                self.assertNotIn(other, geometry_source)


if __name__ == "__main__":
    unittest.main()
