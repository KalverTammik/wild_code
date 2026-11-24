"""Characterization tests for the file and property-link actions behind APIModuleActions.

They pin which query each action loads, which variables it sends, how it reads the answer
and what it does with an empty or broken answer or a failed request, so the actions can
move out of python/api_actions.py without changing behaviour. The patch helper covers every
module the code may live in, so the same tests run before and after the move.
"""
from __future__ import annotations

import importlib
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
if os.environ.get("QGIS_PREFIX_PATH"):
    sys.path.append(str(Path(os.environ["QGIS_PREFIX_PATH"]) / "python" / "plugins"))

import requests
from qgis.core import QgsApplication

from Kavitro_dev.Logs.python_fail_logger import PythonFailLogger
from Kavitro_dev.python import api_actions as api_actions_module
from Kavitro_dev.python.GraphQLQueryLoader import GraphQLQueryLoader
from Kavitro_dev.python.api_actions import APIModuleActions


# Every module the actions may be defined in; a missing one is skipped, so the tests run
# on the single-file layout as well as on the split one.
CODE_MODULES = (
    "Kavitro_dev.python.api_actions",
    "Kavitro_dev.python.actions.file_actions",
    "Kavitro_dev.python.actions.property_link_actions",
)
REQUEST_HEADERS = {"Accept": "*/*", "X-Requested-With": "XMLHttpRequest"}


def _code_modules() -> list:
    modules = []
    for name in CODE_MODULES:
        try:
            modules.append(importlib.import_module(name))
        except ImportError:
            continue
    return modules


def file_page(start: int, end: int, cursor, has_more: bool, *, root: str = "task") -> dict:
    return {root: {"files": {
        "edges": [{"node": {"uuid": f"u{i}", "id": str(i), "fileName": f"File {i}.pdf"}} for i in range(start, end)],
        "pageInfo": {"endCursor": cursor, "hasNextPage": has_more},
    }}}


def connected_page(numbers, cursor, has_more: bool, *, root: str = "task") -> dict:
    return {"data": {root: {"properties": {
        "edges": [{"node": {"cadastralUnitNumber": number}} for number in numbers],
        "pageInfo": {"endCursor": cursor, "hasNextPage": has_more},
    }}}}


def easement_page(edges, cursor, has_more: bool) -> dict:
    return {"data": {"easement": {"properties": {
        "edges": edges,
        "pageInfo": {"endCursor": cursor, "hasNextPage": has_more},
    }}}}


def easement_edge(number, **node_extra) -> dict:
    return {"node": {"cadastralUnitNumber": number, **node_extra}, "area": {"value": 1, "unit": "M2"}}


def property_page(pairs) -> dict:
    return {"data": {"properties": {
        "edges": [{"node": {"id": property_id, "cadastralUnitNumber": number}} for number, property_id in pairs],
    }}}


class ActionTestCase(unittest.TestCase):
    """Mocked loader, client and logger; no request leaves the process."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QgsApplication.instance() or QgsApplication([], False)

    def setUp(self) -> None:
        self.client = Mock()
        self.loader = Mock()
        self.loader.load_query_by_module.side_effect = self._query_text
        self.log = self._patch(PythonFailLogger, "log_exception")
        for module in _code_modules():
            for name, instance in (("APIClient", self.client), ("GraphQLQueryLoader", self.loader)):
                if hasattr(module, name):
                    self._patch(module, name, return_value=instance)

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

    def reset_calls(self) -> None:
        self.loader.load_query_by_module.reset_mock()
        self.client.send_query.reset_mock()
        self.client.send_multipart_query.reset_mock()
        self.log.reset_mock()


class FileHelperTest(ActionTestCase):
    def test_file_owner_module_maps_task_like_modules_to_task(self) -> None:
        cases = (("works", "task"), ("asbuilt", "task"), ("task", "task"), (" Project ", "project"),
                 ("easement", "easement"), ("", ""), (None, ""))
        for module, owner in cases:
            with self.subTest(module=module):
                self.assertEqual(APIModuleActions._file_owner_module(module), owner)

    def test_file_model_type_is_the_upper_case_owner(self) -> None:
        cases = (("works", "TASK"), ("asbuilt", "TASK"), ("easement", "EASEMENT"), ("contract", "CONTRACT"),
                 ("", ""), (None, ""))
        for module, model_type in cases:
            with self.subTest(module=module):
                self.assertEqual(APIModuleActions._file_model_type(module), model_type)

    def test_file_query_name_per_owner(self) -> None:
        cases = (("works", "taskFiles.graphql"), ("asbuilt", "taskFiles.graphql"), ("task", "taskFiles.graphql"),
                 ("project", "projectFiles.graphql"), ("contract", "contractFiles.graphql"),
                 ("coordination", "coordinationFiles.graphql"), ("easement", "easementFiles.graphql"),
                 ("property", ""), ("", ""))
        for module, query_name in cases:
            with self.subTest(module=module):
                self.assertEqual(APIModuleActions._file_query_name(module), query_name)


class GetModuleFilesTest(ActionTestCase):
    def test_blank_item_returns_an_empty_list_without_a_request(self) -> None:
        self.assertEqual(APIModuleActions.get_module_files("works", "  "), [])
        self.loader.load_query_by_module.assert_not_called()
        self.client.send_query.assert_not_called()

    def test_module_without_a_file_query_returns_none_without_a_request(self) -> None:
        self.assertIsNone(APIModuleActions.get_module_files("property", "p-1"))
        self.assertIsNone(APIModuleActions.get_module_files("", "p-1"))
        self.client.send_query.assert_not_called()
        self.log.assert_not_called()

    def test_task_like_module_loads_the_task_files_query_newest_first(self) -> None:
        self.client.send_query.return_value = file_page(0, 1, None, False)
        result = APIModuleActions.get_module_files("works", " task-1 ")
        self.assertEqual([item["uuid"] for item in result], ["u0"])
        self.assertEqual(self.loaded(), [("task", "taskFiles.graphql")])
        self.assertEqual(self.sent(), [("query task/taskFiles.graphql", {"variables": {
            "id": "task-1",
            "first": 50,
            "after": None,
            "orderBy": [{"column": "CREATED_AT", "order": "DESC"}],
        }})])

    def test_other_module_loads_its_own_query_newest_first(self) -> None:
        # Found 2026-11-23: only tasks asked for an order, so a contract detail showed any five files.
        for module in ("project", "contract", "coordination", "easement"):
            with self.subTest(module=module):
                self.reset_calls()
                self.client.send_query.return_value = file_page(0, 1, None, False, root=module)
                result = APIModuleActions.get_module_files(module, "x-1")
                self.assertEqual([item["uuid"] for item in result], ["u0"])
                self.assertEqual(self.loaded(), [(module, f"{module}Files.graphql")])
                self.assertEqual(self.sent(), [(f"query {module}/{module}Files.graphql", {"variables": {
                    "id": "x-1",
                    "first": 50,
                    "after": None,
                    "orderBy": [{"column": "CREATED_AT", "order": "DESC"}],
                }})])

    def test_answer_under_another_root_is_broken(self) -> None:
        self.client.send_query.return_value = file_page(0, 1, None, False, root="task")
        self.assertIsNone(APIModuleActions.get_module_files("project", "x-1"))
        self.assertEqual(self.log.call_args.kwargs["event"], "module_get_files_failed")

    def test_node_fields_are_normalised(self) -> None:
        node = {
            "uuid": " u1 ", "id": 7, "fileName": " a.pdf ", "mimeType": "application/pdf ", "ext": " pdf",
            "size": 12, "humanReadableSize": " 12 B ", "uploader": {"id": "9"}, "model": "not-a-dict",
            "createdAt": "2026-01-01", "updatedAt": None, "deletedAt": "2026-02-02", "extra": "dropped",
        }
        self.client.send_query.return_value = {"task": {"files": {"edges": [{"node": node}], "pageInfo": {}}}}
        self.assertEqual(APIModuleActions.get_module_files("task", "t"), [{
            "id": "7", "uuid": "u1", "fileName": "a.pdf", "mimeType": "application/pdf", "ext": "pdf",
            "size": 12, "humanReadableSize": "12 B", "uploader": {"id": "9"}, "model": {},
            "createdAt": "2026-01-01", "updatedAt": None, "deletedAt": "2026-02-02",
        }])

    def test_nodes_are_keyed_by_uuid_then_id_and_empty_nodes_are_skipped(self) -> None:
        edges = [
            {"node": {"id": "only-id"}},
            {"node": {}},
            {"node": None},
            {},
            {"node": {"uuid": "u1", "fileName": "first"}},
            {"node": {"uuid": "u1", "fileName": "last wins"}},
        ]
        self.client.send_query.return_value = {"task": {"files": {"edges": edges, "pageInfo": {}}}}
        result = APIModuleActions.get_module_files("task", "t")
        self.assertEqual([(item["id"], item["uuid"], item["fileName"]) for item in result],
                         [("only-id", "", ""), ("", "u1", "last wins")])
        self.assertEqual(result[0]["uploader"], {})
        self.assertEqual(result[0]["model"], {})

    def test_pages_follow_the_end_cursor(self) -> None:
        self.client.send_query.side_effect = [
            file_page(0, 50, "c1", True), file_page(50, 100, "c2", True), file_page(100, 101, "c3", False),
        ]
        result = APIModuleActions.get_module_files("task", "t")
        self.assertEqual(len(result), 101)
        self.assertEqual([kwargs["variables"]["after"] for _query, kwargs in self.sent()], [None, "c1", "c2"])
        self.assertEqual([kwargs["variables"]["first"] for _query, kwargs in self.sent()], [50, 50, 50])
        self.log.assert_not_called()

    def test_limit_caps_the_page_size_and_the_result(self) -> None:
        self.client.send_query.side_effect = [file_page(0, 50, "c1", True)]
        result = APIModuleActions.get_module_files("task", "t", limit=2)
        self.assertEqual([item["uuid"] for item in result], ["u0", "u1"])
        self.assertEqual([kwargs["variables"]["first"] for _query, kwargs in self.sent()], [2])

    def test_limit_asks_only_for_the_remaining_files_on_later_pages(self) -> None:
        self.client.send_query.side_effect = [file_page(0, 50, "c1", True), file_page(50, 100, "c2", True)]
        result = APIModuleActions.get_module_files("task", "t", limit=60)
        self.assertEqual(len(result), 60)
        self.assertEqual([kwargs["variables"]["first"] for _query, kwargs in self.sent()], [50, 10])

    def test_limit_zero_still_asks_for_one_file(self) -> None:
        self.client.send_query.side_effect = [file_page(0, 50, "c1", True)]
        result = APIModuleActions.get_module_files("task", "t", limit=0)
        self.assertEqual(len(result), 1)
        self.assertEqual(self.sent()[0][1]["variables"]["first"], 1)

    def test_empty_first_page_is_an_empty_list(self) -> None:
        self.client.send_query.return_value = {"task": {"files": {"edges": [], "pageInfo": {"hasNextPage": False}}}}
        self.assertEqual(APIModuleActions.get_module_files("task", "t"), [])
        self.log.assert_not_called()

    def test_repeated_cursor_is_refused_without_another_request(self) -> None:
        # A third page is available; a cursor seen before must stop the walk before it is asked for.
        self.client.send_query.side_effect = [
            file_page(0, 1, "same", True), file_page(1, 2, "same", True), file_page(2, 3, "other", False),
        ]
        self.assertIsNone(APIModuleActions.get_module_files("task", "t"))
        self.assertEqual(self.client.send_query.call_count, 2)
        self.assertEqual(self.log.call_args.kwargs["event"], "module_get_files_failed")

    def test_broken_answers_return_none_and_are_logged(self) -> None:
        cases = {
            "no answer": [None],
            "missing root": [{"task": None}],
            "edges not a list": [{"task": {"files": {"edges": None}}}],
            "empty intermediate page": [{"task": {"files": {"edges": [], "pageInfo": {"hasNextPage": True, "endCursor": "x"}}}}],
            "cursor missing": [file_page(0, 1, "", True)],
            "cursor repeats": [file_page(0, 1, "same", True), file_page(1, 2, "same", True)],
            "request raises": [RuntimeError("offline")],
        }
        for name, pages in cases.items():
            with self.subTest(case=name):
                self.reset_calls()
                self.client.send_query.side_effect = pages
                self.assertIsNone(APIModuleActions.get_module_files("works", " t-1 "))
                self.assertEqual(self.log.call_args.kwargs, {
                    "module": "task",
                    "event": "module_get_files_failed",
                    "extra": {"item_id": "t-1", "module": "works"},
                })


class CreateFileDownloadLinkTest(ActionTestCase):
    def test_blank_uuid_returns_none_without_a_request(self) -> None:
        self.assertIsNone(APIModuleActions.create_file_download_link(" "))
        self.assertIsNone(APIModuleActions.create_file_download_link(None))
        self.loader.load_query_by_module.assert_not_called()
        self.client.send_query.assert_not_called()

    def test_loads_the_task_download_link_mutation_and_returns_the_url(self) -> None:
        self.client.send_query.return_value = {"createDownloadLink": {"url": " https://files.example/abc "}}
        self.assertEqual(APIModuleActions.create_file_download_link(" abc "), "https://files.example/abc")
        self.assertEqual(self.loaded(), [("task", "createDownloadLink.graphql")])
        self.assertEqual(self.sent(), [("query task/createDownloadLink.graphql", {"variables": {"uuid": "abc"}})])

    def test_answer_without_a_url_returns_none(self) -> None:
        for response in (None, {}, {"createDownloadLink": None}, {"createDownloadLink": {}},
                         {"createDownloadLink": {"url": " "}}):
            with self.subTest(response=response):
                self.client.send_query.return_value = response
                self.assertIsNone(APIModuleActions.create_file_download_link("abc"))
        self.log.assert_not_called()

    def test_request_failure_returns_none_and_is_logged(self) -> None:
        self.client.send_query.side_effect = RuntimeError("offline")
        self.assertIsNone(APIModuleActions.create_file_download_link("abc"))
        self.assertEqual(self.log.call_args.kwargs, {
            "module": "task",
            "event": "task_file_download_link_failed",
            "extra": {"uuid": "abc"},
        })


class FetchFilePreviewPayloadTest(ActionTestCase):
    URL = "https://files.example/abc"

    def setUp(self) -> None:
        super().setUp()
        self.get = self._patch(requests, "get")
        self.response = MagicMock()
        self.response.headers = {
            "Content-Type": "Application/PDF; charset=binary",
            "Content-Disposition": ' attachment; filename="a.pdf" ',
            "Content-Length": " 7 ",
        }
        self.get.return_value.__enter__.return_value = self.response

    def link(self) -> None:
        self.client.send_query.return_value = {"createDownloadLink": {"url": self.URL}}

    def test_blank_uuid_returns_none_without_any_request(self) -> None:
        self.assertIsNone(APIModuleActions.fetch_file_preview_payload(" ", max_bytes=10))
        self.client.send_query.assert_not_called()
        self.get.assert_not_called()

    def test_without_a_download_link_nothing_is_downloaded(self) -> None:
        self.client.send_query.return_value = {"createDownloadLink": {}}
        self.assertIsNone(APIModuleActions.fetch_file_preview_payload("abc", max_bytes=10))
        self.assertEqual(self.loaded(), [("task", "createDownloadLink.graphql")])
        self.get.assert_not_called()

    def test_download_is_streamed_with_the_expected_headers(self) -> None:
        self.link()
        self.response.iter_content.return_value = [b"abc", b"", b"defg"]
        payload = APIModuleActions.fetch_file_preview_payload(" abc ", max_bytes=100)
        self.assertEqual(self.sent(), [("query task/createDownloadLink.graphql", {"variables": {"uuid": "abc"}})])
        self.get.assert_called_once_with(self.URL, headers=REQUEST_HEADERS, stream=True, timeout=60)
        self.response.raise_for_status.assert_called_once_with()
        self.response.iter_content.assert_called_once_with(chunk_size=65536)
        self.assertEqual(payload, {
            "url": self.URL,
            "content": b"abcdefg",
            "contentType": "application/pdf",
            "contentDisposition": 'attachment; filename="a.pdf"',
            "contentLength": "7",
            "truncated": False,
        })

    def test_content_is_cut_at_max_bytes_and_marked_truncated(self) -> None:
        self.link()
        cases = (
            ([b"abc", b"defg"], 5, b"abcde", True),
            ([b"abc", b"de", b"f"], 5, b"abcde", True),
            ([b"abc", b"de"], 5, b"abcde", False),
            ([b"abcdef"], 0, b"a", True),
        )
        for chunks, max_bytes, content, truncated in cases:
            with self.subTest(chunks=chunks, max_bytes=max_bytes):
                self.response.iter_content.return_value = list(chunks)
                payload = APIModuleActions.fetch_file_preview_payload("abc", max_bytes=max_bytes)
                self.assertEqual((payload["content"], payload["truncated"]), (content, truncated))

    def test_download_failure_returns_none_and_is_logged(self) -> None:
        self.link()
        self.response.raise_for_status.side_effect = requests.HTTPError("404")
        self.assertIsNone(APIModuleActions.fetch_file_preview_payload("abc", max_bytes=0))
        self.assertEqual(self.log.call_args.kwargs, {
            "module": "task",
            "event": "task_file_preview_fetch_failed",
            "extra": {"uuid": "abc", "max_bytes": 1},
        })


class DeleteFileTest(ActionTestCase):
    def test_blank_uuid_returns_none_without_a_request(self) -> None:
        self.assertIsNone(APIModuleActions.delete_file(""))
        self.assertIsNone(APIModuleActions.delete_file(None))
        self.loader.load_query_by_module.assert_not_called()
        self.client.send_query.assert_not_called()

    def test_loads_the_task_delete_mutation_and_returns_the_deleted_file(self) -> None:
        deleted = {"uuid": "abc", "fileName": "a.pdf"}
        self.client.send_query.return_value = {"deleteFile": deleted}
        self.assertIs(APIModuleActions.delete_file(" abc "), deleted)
        self.assertEqual(self.loaded(), [("task", "deleteFile.graphql")])
        self.assertEqual(self.sent(), [("query task/deleteFile.graphql", {"variables": {"uuid": "abc"}})])

    def test_answer_without_a_uuid_returns_none(self) -> None:
        for response in (None, {}, {"deleteFile": None}, {"deleteFile": {"uuid": " "}}, {"deleteFile": "abc"}):
            with self.subTest(response=response):
                self.client.send_query.return_value = response
                self.assertIsNone(APIModuleActions.delete_file("abc"))
        self.log.assert_not_called()

    def test_request_failure_returns_none_and_is_logged(self) -> None:
        self.client.send_query.side_effect = RuntimeError("offline")
        self.assertIsNone(APIModuleActions.delete_file("abc"))
        self.assertEqual(self.log.call_args.kwargs, {
            "module": "task",
            "event": "task_file_delete_failed",
            "extra": {"uuid": "abc"},
        })


class UploadModuleFileTest(ActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        handle = tempfile.NamedTemporaryFile("wb", suffix=".pdf", delete=False)
        handle.write(b"%PDF-1.4")
        handle.close()
        self.path = handle.name
        self.addCleanup(os.remove, self.path)

    def test_missing_inputs_return_none_without_a_request(self) -> None:
        cases = (
            ("", "t-1", self.path),
            (None, "t-1", self.path),
            ("works", " ", self.path),
            ("works", "t-1", ""),
            ("works", "t-1", self.path + ".missing"),
            ("works", "t-1", os.path.dirname(self.path)),
        )
        for module, item_id, path in cases:
            with self.subTest(module=module, item_id=item_id, path=path):
                self.assertIsNone(APIModuleActions.upload_module_file(module, item_id, path))
        self.loader.load_query_by_module.assert_not_called()
        self.client.send_multipart_query.assert_not_called()
        self.log.assert_not_called()

    def test_upload_uses_the_task_upload_mutation_with_the_owner_model_type(self) -> None:
        uploaded = {"uuid": "u1", "fileName": "a.pdf"}
        self.client.send_multipart_query.return_value = {"uploadFile": uploaded}
        # Every module that has a file list uploads with its upper-cased owner name; the task-like ones as TASK.
        cases = (("works", "TASK"), ("asbuilt", "TASK"), ("task", "TASK"), ("easement", "EASEMENT"),
                 ("project", "PROJECT"), ("contract", "CONTRACT"), ("coordination", "COORDINATION"))
        for module, model_type in cases:
            with self.subTest(module=module):
                self.reset_calls()
                self.assertIs(APIModuleActions.upload_module_file(module, " t-1 ", f" {self.path} "), uploaded)
                self.assertEqual(self.loaded(), [("task", "uploadTaskFile.graphql")])
                self.client.send_multipart_query.assert_called_once_with(
                    "query task/uploadTaskFile.graphql",
                    variables={"file": None, "model": {"id": "t-1", "type": model_type}, "data": None},
                    file_variables={"file": self.path},
                    timeout=120,
                )
        self.client.send_query.assert_not_called()

    def test_module_without_a_file_list_is_refused_before_any_request_and_logged(self) -> None:
        for module in ("property", " Property ", "tag", "nonsense"):
            with self.subTest(module=module):
                self.reset_calls()
                self.client.send_multipart_query.return_value = {"uploadFile": {"uuid": "u1"}}
                self.assertIsNone(APIModuleActions.upload_module_file(module, " t-1 ", f" {self.path} "))
                self.loader.load_query_by_module.assert_not_called()
                self.client.send_multipart_query.assert_not_called()
                self.client.send_query.assert_not_called()
                self.assertEqual(self.log.call_count, 1)
                self.assertIsInstance(self.log.call_args.args[0], ValueError)
                self.assertEqual(self.log.call_args.kwargs, {
                    "module": module.strip().lower(),
                    "event": "module_file_upload_unsupported_module",
                    "extra": {"item_id": "t-1", "file_name": os.path.basename(self.path), "module": module},
                })

    def test_blank_module_stays_a_silent_refusal(self) -> None:
        # A missing module name is a plain missing input, as before; only a named but unsupported module is logged.
        for module in ("", "  ", None):
            with self.subTest(module=module):
                self.assertIsNone(APIModuleActions.upload_module_file(module, "t-1", self.path))
        self.loader.load_query_by_module.assert_not_called()
        self.client.send_multipart_query.assert_not_called()
        self.log.assert_not_called()

    def test_metadata_is_sent_as_data(self) -> None:
        self.client.send_multipart_query.return_value = {"uploadFile": {"uuid": "u1"}}
        APIModuleActions.upload_module_file("works", "t-1", self.path, metadata={"note": "x"})
        self.assertEqual(self.client.send_multipart_query.call_args.kwargs["variables"]["data"], {"note": "x"})

    def test_answer_without_a_uuid_returns_none(self) -> None:
        for response in (None, {}, {"uploadFile": None}, {"uploadFile": {"uuid": " "}}, {"uploadFile": "u1"}):
            with self.subTest(response=response):
                self.client.send_multipart_query.return_value = response
                self.assertIsNone(APIModuleActions.upload_module_file("works", "t-1", self.path))
        self.log.assert_not_called()

    def test_upload_failure_returns_none_and_is_logged(self) -> None:
        self.client.send_multipart_query.side_effect = RuntimeError("offline")
        self.assertIsNone(APIModuleActions.upload_module_file("asbuilt", "t-1", self.path))
        self.assertEqual(self.log.call_args.kwargs, {
            "module": "task",
            "event": "module_file_upload_failed",
            "extra": {"item_id": "t-1", "file_name": os.path.basename(self.path), "module": "asbuilt"},
        })


class PropertyOwnerModuleTest(ActionTestCase):
    def test_task_like_modules_map_to_task(self) -> None:
        cases = (("works", "task"), ("asbuilt", "task"), ("task", "task"), (" Easement ", "easement"),
                 ("project", "project"), ("", ""), (None, ""))
        for module, owner in cases:
            with self.subTest(module=module):
                self.assertEqual(APIModuleActions._property_owner_module(module), owner)


class GetModuleItemConnectedPropertiesTest(ActionTestCase):
    def test_task_like_modules_use_the_task_query_and_task_root(self) -> None:
        for module in ("works", "asbuilt", "task"):
            with self.subTest(module=module):
                self.reset_calls()
                self.client.send_query.return_value = connected_page(["1", "2"], None, False)
                self.assertEqual(APIModuleActions.get_module_item_connected_properties(module, "t-1"), ["1", "2"])
                self.assertEqual(self.loaded(), [("task", "w_tasks_module_data_by_item_id.graphql")])
                self.assertEqual(self.sent(), [("query task/w_tasks_module_data_by_item_id.graphql", {
                    "variables": {"propertiesFirst": 50, "propertiesAfter": None, "id": "t-1"},
                    "return_raw": True,
                })])

    def test_other_modules_use_their_own_id_query_and_root(self) -> None:
        for module in ("project", "contract", "coordination", "easement"):
            with self.subTest(module=module):
                self.reset_calls()
                self.client.send_query.return_value = connected_page(["3"], None, False, root=module)
                self.assertEqual(APIModuleActions.get_module_item_connected_properties(module, "x-1"), ["3"])
                self.assertEqual(self.loaded(), [(module, f"W_{module}_id.graphql")])
                self.assertEqual(self.sent()[0][1]["variables"], {"propertiesFirst": 50, "propertiesAfter": None, "id": "x-1"})

    def test_answer_under_another_root_yields_nothing(self) -> None:
        self.client.send_query.return_value = connected_page(["3"], None, False, root="task")
        self.assertEqual(APIModuleActions.get_module_item_connected_properties("project", "x-1"), [])
        self.log.assert_not_called()

    def test_missing_or_unknown_module_returns_nothing_and_is_logged_like_any_unknown_module(self) -> None:
        # The real loader refuses an empty or unknown module, so the same path serves None, blank and unknown names.
        real_loader = GraphQLQueryLoader()
        self.loader.load_query_by_module.side_effect = real_loader.load_query_by_module
        cases = ((None, "property", "W__id.graphql"), ("", "property", "W__id.graphql"),
                 ("  ", "property", "W__id.graphql"), (" Nonsense ", "nonsense", "W_nonsense_id.graphql"))
        for module, logged_module, query_file in cases:
            with self.subTest(module=module):
                self.reset_calls()
                self.assertEqual(APIModuleActions.get_module_item_connected_properties(module, "x-1"), [])
                self.client.send_query.assert_not_called()
                self.assertEqual(self.log.call_args.kwargs, {
                    "module": logged_module,
                    "event": "module_connected_properties_query_load_failed",
                    "extra": {"item_id": "x-1", "query_file": query_file},
                })

    def test_edges_without_a_node_are_skipped(self) -> None:
        page_one = connected_page(["1"], "c1", True)
        page_one["data"]["task"]["properties"]["edges"] = [
            {"node": None}, {}, None, {"node": "text"}, {"node": {"cadastralUnitNumber": "1"}},
        ]
        self.client.send_query.side_effect = [page_one, connected_page(["2"], None, False)]
        self.assertEqual(APIModuleActions.get_module_item_connected_properties("works", "t-1"), ["1", "2"])
        self.assertEqual(self.client.send_query.call_count, 2)
        self.log.assert_not_called()

    def test_item_id_is_sent_stripped(self) -> None:
        for item_id, sent_id in ((" t-1 ", "t-1"), ("t-1", "t-1"), (None, ""), (12, "12")):
            with self.subTest(item_id=item_id):
                self.reset_calls()
                self.client.send_query.return_value = connected_page(["1"], None, False)
                APIModuleActions.get_module_item_connected_properties("works", item_id)
                self.assertEqual(self.sent()[0][1]["variables"]["id"], sent_id)

    def test_pages_follow_the_cursor_and_numbers_are_deduped(self) -> None:
        self.client.send_query.side_effect = [
            connected_page(["1", "2", "2"], "c1", True),
            connected_page(["2", "3", None, ""], "c2", True),
            connected_page([], "c3", True),
        ]
        self.assertEqual(APIModuleActions.get_module_item_connected_properties("works", "t-1"), ["1", "2", "3"])
        self.assertEqual([kwargs["variables"]["propertiesAfter"] for _query, kwargs in self.sent()], [None, "c1", "c2"])
        self.log.assert_not_called()

    def test_pagination_stops_without_a_next_page_or_cursor(self) -> None:
        pages = (
            connected_page(["1"], "c1", False),
            connected_page(["1"], None, True),
            connected_page(["1"], "", True),
            {"data": {"task": {"properties": {"edges": [{"node": {"cadastralUnitNumber": "1"}}]}}}},
        )
        for page in pages:
            with self.subTest(page=page):
                self.reset_calls()
                self.client.send_query.return_value = page
                self.assertEqual(APIModuleActions.get_module_item_connected_properties("works", "t-1"), ["1"])
                self.assertEqual(self.client.send_query.call_count, 1)

    def test_unloadable_query_returns_nothing_and_is_logged(self) -> None:
        self.loader.load_query_by_module.side_effect = FileNotFoundError("query_file_not_found")
        self.assertEqual(APIModuleActions.get_module_item_connected_properties("works", " t-1 "), [])
        self.client.send_query.assert_not_called()
        self.assertEqual(self.log.call_args.kwargs, {
            "module": "works",
            "event": "module_connected_properties_query_load_failed",
            "extra": {"item_id": "t-1", "query_file": "w_tasks_module_data_by_item_id.graphql"},
        })

    def test_request_failure_keeps_the_numbers_already_read_and_is_logged(self) -> None:
        self.client.send_query.side_effect = [connected_page(["1"], "c1", True, root="project"), RuntimeError("offline")]
        self.assertEqual(APIModuleActions.get_module_item_connected_properties("project", "p-1"), ["1"])
        self.assertEqual(self.log.call_args.kwargs, {
            "module": "project",
            "event": "module_connected_properties_fetch_failed",
            "extra": {"item_id": "p-1"},
        })


class ResolvePropertiesByCadastralTest(ActionTestCase):
    def test_blank_numbers_resolve_to_nothing_without_a_request(self) -> None:
        self.assertEqual(APIModuleActions.resolve_property_map_by_cadastral([]), ({}, []))
        self.assertEqual(APIModuleActions.resolve_property_map_by_cadastral(["", "  "]), ({}, []))
        self.assertEqual(APIModuleActions.resolve_property_ids_by_cadastral([]), ([], []))
        self.loader.load_query_by_module.assert_not_called()
        self.client.send_query.assert_not_called()

    def test_numbers_are_looked_up_with_an_in_filter_on_the_property_query(self) -> None:
        self.client.send_query.return_value = property_page([("11", "p1")])
        self.assertEqual(APIModuleActions.resolve_property_map_by_cadastral([" 11 ", "22", ""]), ({"11": "p1"}, ["22"]))
        self.assertEqual(self.loaded(), [("property", "id_number.graphql")])
        self.assertEqual(self.sent(), [("query property/id_number.graphql", {
            "variables": {
                "first": 2,
                "after": None,
                "search": None,
                "where": {"AND": [{"column": "CADASTRAL_UNIT_NUMBER", "operator": "IN", "value": ["11", "22"]}]},
            },
            "return_raw": True,
        })])

    def test_numbers_are_sent_in_chunks_of_twenty_five(self) -> None:
        numbers = [str(i) for i in range(1, 27)]
        self.client.send_query.side_effect = [property_page([("1", "p1")]), property_page([("26", "p26")])]
        resolved, missing = APIModuleActions.resolve_property_map_by_cadastral(numbers)
        self.assertEqual(resolved, {"1": "p1", "26": "p26"})
        self.assertEqual(missing, [str(i) for i in range(2, 26)])
        values = [kwargs["variables"]["where"]["AND"][0]["value"] for _query, kwargs in self.sent()]
        self.assertEqual(values, [numbers[:25], numbers[25:]])
        self.assertEqual([kwargs["variables"]["first"] for _query, kwargs in self.sent()], [25, 1])

    def test_nodes_without_an_id_or_number_are_ignored(self) -> None:
        self.client.send_query.return_value = {"data": {"properties": {"edges": [
            {"node": {"id": "", "cadastralUnitNumber": "1"}},
            {"node": {"id": "p2"}},
            {"node": None},
            {"node": {"id": 3, "cadastralUnitNumber": 3}},
        ]}}}
        self.assertEqual(APIModuleActions.resolve_property_map_by_cadastral(["1", "2", "3"]), ({"3": "3"}, ["1", "2"]))

    def test_ids_variant_returns_the_ids_in_answer_order(self) -> None:
        self.client.send_query.return_value = property_page([("22", "p2"), ("11", "p1")])
        self.assertEqual(APIModuleActions.resolve_property_ids_by_cadastral(["11", "22", "33"]), (["p2", "p1"], ["33"]))

    def test_request_failure_propagates(self) -> None:
        self.client.send_query.side_effect = RuntimeError("offline")
        with self.assertRaises(RuntimeError):
            APIModuleActions.resolve_property_map_by_cadastral(["11"])
        with self.assertRaises(RuntimeError):
            APIModuleActions.resolve_property_ids_by_cadastral(["11"])
        self.log.assert_not_called()


class GetEasementPropertyEdgesTest(ActionTestCase):
    def test_blank_id_returns_nothing_without_a_request(self) -> None:
        self.assertEqual(APIModuleActions.get_easement_property_edges(" "), [])
        self.assertEqual(APIModuleActions.get_easement_property_edges(None), [])
        self.loader.load_query_by_module.assert_not_called()
        self.client.send_query.assert_not_called()

    def test_loads_the_easement_id_query_and_returns_the_edges_whole(self) -> None:
        edges = [{"node": {"cadastralUnitNumber": "1", "id": "p1"}, "area": {"value": 2, "unit": "M2"}, "isPayable": True}]
        self.client.send_query.return_value = easement_page(edges, None, False)
        self.assertEqual(APIModuleActions.get_easement_property_edges(" e-1 "), edges)
        self.assertEqual(self.loaded(), [("easement", "W_easement_id.graphql")])
        self.assertEqual(self.sent(), [("query easement/W_easement_id.graphql", {
            "variables": {"propertiesFirst": 50, "propertiesAfter": None, "id": "e-1"},
            "return_raw": True,
        })])

    def test_pages_follow_the_cursor_and_repeated_numbers_are_dropped(self) -> None:
        self.client.send_query.side_effect = [
            easement_page([easement_edge("1"), easement_edge("1", id="dup"), {"node": {}}, "not-an-edge"], "c1", True),
            easement_page([easement_edge("2"), easement_edge(" 1 "), {"node": None}], "c2", False),
        ]
        self.assertEqual(APIModuleActions.get_easement_property_edges("e-1"), [
            easement_edge("1"), {"node": {}}, easement_edge("2"), {"node": None},
        ])
        self.assertEqual([kwargs["variables"]["propertiesAfter"] for _query, kwargs in self.sent()], [None, "c1"])
        self.log.assert_not_called()

    def test_pagination_stops_on_an_empty_page_or_a_missing_cursor(self) -> None:
        cases = (
            (easement_page([easement_edge("1")], "c1", False), [easement_edge("1")]),
            (easement_page([easement_edge("1")], "", True), [easement_edge("1")]),
            (easement_page([], "c1", True), []),
            ({"data": {"easement": None}}, []),
        )
        for page, expected in cases:
            with self.subTest(page=page):
                self.reset_calls()
                self.client.send_query.return_value = page
                self.assertEqual(APIModuleActions.get_easement_property_edges("e-1"), expected)
                self.assertEqual(self.client.send_query.call_count, 1)

    def test_unloadable_query_returns_nothing_and_is_logged(self) -> None:
        self.loader.load_query_by_module.side_effect = ValueError("unknown_module")
        self.assertEqual(APIModuleActions.get_easement_property_edges(" e-1 "), [])
        self.client.send_query.assert_not_called()
        self.assertEqual(self.log.call_args.kwargs, {
            "module": "easement",
            "event": "easement_property_edges_query_load_failed",
            "extra": {"item_id": "e-1"},
        })

    def test_request_failure_keeps_the_edges_already_read_and_is_logged(self) -> None:
        self.client.send_query.side_effect = [easement_page([easement_edge("1")], "c1", True), RuntimeError("offline")]
        self.assertEqual(APIModuleActions.get_easement_property_edges("e-1"), [easement_edge("1")])
        self.assertEqual(self.log.call_args.kwargs, {
            "module": "easement",
            "event": "easement_property_edges_fetch_failed",
            "extra": {"item_id": "e-1"},
        })


class AssociatePropertiesTest(ActionTestCase):
    def test_without_property_ids_nothing_is_sent(self) -> None:
        for property_ids in ([], None):
            with self.subTest(property_ids=property_ids):
                with self.assertRaises(ValueError):
                    APIModuleActions.associate_properties("project", "p-1", property_ids)
        self.loader.load_query_by_module.assert_not_called()
        self.client.send_query.assert_not_called()

    def test_task_like_modules_update_the_task_properties(self) -> None:
        response = {"data": {"updateTask": {"id": "t-1"}}}
        self.client.send_query.return_value = response
        for module in ("works", "asbuilt", "task"):
            with self.subTest(module=module):
                self.reset_calls()
                self.assertIs(APIModuleActions.associate_properties(module, "t-1", ["p1", "p2"]), response)
                self.assertEqual(self.loaded(), [("task", "updateTaskProperties.graphql")])
                self.assertEqual(self.sent(), [("query task/updateTaskProperties.graphql", {
                    "variables": {"input": {"id": "t-1", "properties": {"associate": ["p1", "p2"]}}},
                    "return_raw": True,
                })])

    def test_other_modules_update_their_own_properties(self) -> None:
        cases = (("project", "updateProject"), ("contract", "updateContract"),
                 ("coordination", "updateCoordination"))
        for module, root in cases:
            with self.subTest(module=module):
                self.reset_calls()
                self.client.send_query.return_value = {"data": {root: {"id": "x-1"}}}
                APIModuleActions.associate_properties(module, "x-1", ["p1"])
                self.assertEqual(self.loaded(), [(module, f"update{module.capitalize()}Properties.graphql")])
                self.assertEqual(self.sent()[0][1]["variables"], {"input": {"id": "x-1", "properties": {"associate": ["p1"]}}})

    def test_an_easement_links_each_property_as_an_object(self) -> None:
        # The server rejects a bare id here: Expected type "EasementPropertyInput" to be an object.
        response = {"data": {"updateEasement": {"id": "e-1"}}}
        self.client.send_query.return_value = response
        self.assertIs(APIModuleActions.associate_properties("Easement", "e-1", ["p1", "p2"]), response)
        self.assertEqual(self.loaded(), [("easement", "updateEasementProperties.graphql")])
        self.assertEqual(self.sent()[0][1]["variables"],
                         {"input": {"id": "e-1", "properties": {"associate": [{"id": "p1"}, {"id": "p2"}]}}})

    def test_answer_without_the_updated_id_raises(self) -> None:
        for response in (None, {}, {"data": None}, {"data": {"updateProject": None}},
                         {"data": {"updateProject": {"id": ""}}}, {"data": {"updateTask": {"id": "p-1"}}}):
            with self.subTest(response=response):
                self.client.send_query.return_value = response
                with self.assertRaisesRegex(RuntimeError, "updateProject.id"):
                    APIModuleActions.associate_properties("project", "p-1", ["p1"])
        self.log.assert_not_called()

    def test_request_failure_propagates(self) -> None:
        self.client.send_query.side_effect = RuntimeError("offline")
        with self.assertRaisesRegex(RuntimeError, "offline"):
            APIModuleActions.associate_properties("works", "t-1", ["p1"])
        self.log.assert_not_called()


class LinkedNumbersFromResponseTest(unittest.TestCase):
    @staticmethod
    def answer(root, edges, has_next=False, page_info=True):
        properties = {"edges": edges}
        if page_info:
            properties["pageInfo"] = {"hasNextPage": has_next}
        return {"data": {root: {"id": "x", "properties": properties}}}

    def test_whole_list_is_read_from_the_answer_of_each_module(self) -> None:
        edges = [{"node": {"cadastralUnitNumber": "1:1"}}, {"node": {"cadastralUnitNumber": "2:2"}},
                 {"node": {"cadastralUnitNumber": "1:1"}}, {"node": {"cadastralUnitNumber": ""}}, {"node": None}, "x"]
        cases = (("project", "updateProject"), ("Easement", "updateEasement"), ("works", "updateTask"),
                 ("asbuilt", "updateTask"), ("contract", "updateContract"), ("coordination", "updateCoordination"))
        for module, root in cases:
            with self.subTest(module=module):
                self.assertEqual(
                    APIModuleActions.linked_cadastral_numbers_from_response(module, self.answer(root, edges)),
                    ["1:1", "2:2"])
        self.assertEqual(APIModuleActions.linked_cadastral_numbers_from_response(
            "project", self.answer("updateProject", [])), [])

    def test_part_of_the_list_or_another_answer_is_none(self) -> None:
        edges = [{"node": {"cadastralUnitNumber": "1:1"}}]
        for response in (
            self.answer("updateProject", edges, has_next=True),
            self.answer("updateProject", edges, page_info=False),
            {"data": {"updateProject": {"id": "x", "properties": {"pageInfo": {"hasNextPage": None}, "edges": edges}}}},
            self.answer("updateTask", edges),
            {"data": {"updateProject": {"id": "x"}}},
            {"data": {"updateProject": {"id": "x", "properties": {"pageInfo": {"hasNextPage": False}}}}},
            {"data": None}, None, "text",
        ):
            with self.subTest(response=response):
                self.assertIsNone(APIModuleActions.linked_cadastral_numbers_from_response("project", response))

    def test_every_link_mutation_asks_whether_more_pages_exist(self) -> None:
        loader = GraphQLQueryLoader()
        for module, filename in (("project", "updateProjectProperties.graphql"),
                                 ("contract", "updateContractProperties.graphql"),
                                 ("coordination", "updateCoordinationProperties.graphql"),
                                 ("easement", "updateEasementProperties.graphql"),
                                 ("task", "updateTaskProperties.graphql")):
            with self.subTest(file=filename):
                text = " ".join(loader.load_query_by_module(module, filename).split())
                self.assertIn("pageInfo { hasNextPage }", text)
                self.assertIn("cadastralUnitNumber", text)


class AssociateEasementPropertiesTest(ActionTestCase):
    def test_missing_id_or_properties_raise_before_any_request(self) -> None:
        cases = (
            (" ", [{"id": "p1"}]),
            ("e-1", []),
            ("e-1", None),
            ("e-1", [{"area": {"value": 1}}, "p1", {"id": ""}]),
        )
        for item_id, properties in cases:
            with self.subTest(item_id=item_id, properties=properties):
                with self.assertRaises(ValueError):
                    APIModuleActions.associate_easement_properties(item_id, properties)
        self.loader.load_query_by_module.assert_not_called()
        self.client.send_query.assert_not_called()

    def test_only_the_easement_edge_fields_are_sent(self) -> None:
        response = {"data": {"updateEasement": {"id": "e-1"}}}
        self.client.send_query.return_value = response
        properties = [
            {
                "id": "p1", "area": {"value": 2, "unit": "M2"}, "pricePerAreaUnit": {"amount": 3, "currency": "EUR"},
                "isPayable": 0, "nextPaymentDate": "2026-12-01", "cadastralUnitNumber": "dropped",
            },
            {"id": "p2", "area": "12", "pricePerAreaUnit": None, "nextPaymentDate": ""},
            {"id": "p3", "isPayable": "yes"},
        ]
        self.assertIs(APIModuleActions.associate_easement_properties(" e-1 ", properties), response)
        self.assertEqual(self.loaded(), [("easement", "updateEasementProperties.graphql")])
        self.assertEqual(self.sent(), [("query easement/updateEasementProperties.graphql", {
            "variables": {"input": {"id": "e-1", "properties": {"associate": [
                {
                    "id": "p1", "area": {"value": 2, "unit": "M2"}, "pricePerAreaUnit": {"amount": 3, "currency": "EUR"},
                    "isPayable": False, "nextPaymentDate": "2026-12-01",
                },
                {"id": "p2"},
                {"id": "p3", "isPayable": True},
            ]}}},
            "return_raw": True,
        })])

    def test_answer_without_the_updated_id_raises(self) -> None:
        for response in (None, {}, {"data": {"updateEasement": None}}, {"data": {"updateEasement": {"id": ""}}},
                         {"data": {"updateTask": {"id": "e-1"}}}):
            with self.subTest(response=response):
                self.client.send_query.return_value = response
                with self.assertRaisesRegex(RuntimeError, "updateEasement.id"):
                    APIModuleActions.associate_easement_properties("e-1", [{"id": "p1"}])
        self.log.assert_not_called()

    def test_request_failure_propagates(self) -> None:
        self.client.send_query.side_effect = RuntimeError("offline")
        with self.assertRaisesRegex(RuntimeError, "offline"):
            APIModuleActions.associate_easement_properties("e-1", [{"id": "p1"}])
        self.log.assert_not_called()


class EntryPointInterfaceTest(unittest.TestCase):
    """APIModuleActions keeps its whole surface after the split, and the moved code left api_actions.py."""

    EXPECTED_METHODS = (
        "_geometry_input_value", "_is_unknown_input_field_error", "_is_unknown_geometry_input_error",
        "_is_geometry_retryable_create_error", "_property_owner_module", "_status_module_value",
        "_file_owner_module", "_file_model_type", "_file_query_name", "get_module_status_options",
        "get_task_priority_values", "task_priority_label", "get_task_priority_options",
        "get_current_user_payload", "get_current_user_id", "user_display_name", "get_assignable_users",
        "get_module_item_connected_properties", "resolve_property_ids_by_cadastral",
        "resolve_property_map_by_cadastral", "get_easement_property_edges", "associate_properties",
        "associate_easement_properties", "linked_cadastral_numbers_from_response", "get_task_data",
        "get_module_files", "get_tasks_by_ids",
        "get_task_description", "update_task_description", "_update_module_geometry", "update_task_geometry",
        "update_project_geometry", "update_easement_geometry", "get_easement_status", "update_easement_status",
        "create_file_download_link", "fetch_file_preview_payload", "delete_file", "upload_module_file",
        "update_task_status", "update_task_members", "_build_task_member_associate_payload", "create_task",
    )
    MOVED = {
        "Kavitro_dev.python.actions.file_actions": ("FileActions", (
            "_file_owner_module", "_file_model_type", "_file_query_name", "get_module_files",
            "create_file_download_link", "fetch_file_preview_payload", "delete_file", "upload_module_file",
        )),
        "Kavitro_dev.python.actions.property_link_actions": ("PropertyLinkActions", (
            "_property_owner_module", "get_module_item_connected_properties", "resolve_property_ids_by_cadastral",
            "resolve_property_map_by_cadastral", "get_easement_property_edges", "associate_properties",
            "associate_easement_properties",
        )),
    }
    # Text only the moved code used; none of it may stay behind in api_actions.py.
    MOVED_TEXT = (
        "taskFiles.graphql", "createDownloadLink.graphql", "deleteFile.graphql", "uploadTaskFile.graphql",
        "requests.get(", "id_number.graphql", "W_easement_id.graphql", "updateEasementProperties.graphql",
        "Properties.graphql", "_PROPERTIES_PAGE_SIZE", "JsonResponseHandler",
    )

    def test_entry_point_still_offers_every_method(self) -> None:
        self.assertEqual(len(set(self.EXPECTED_METHODS)), 43)
        for name in self.EXPECTED_METHODS:
            with self.subTest(method=name):
                self.assertTrue(callable(getattr(APIModuleActions, name, None)), name)
        self.assertEqual(APIModuleActions._TASK_PRIORITY_VALUES, ("URGENT", "HIGH", "MEDIUM", "LOW"))

    def test_moved_methods_are_the_domain_class_functions(self) -> None:
        for module_name, (class_name, names) in self.MOVED.items():
            owner = getattr(importlib.import_module(module_name), class_name)
            self.assertTrue(issubclass(APIModuleActions, owner))
            for name in names:
                with self.subTest(method=name):
                    function = getattr(APIModuleActions, name)
                    self.assertIs(function, getattr(owner, name))
                    self.assertEqual(function.__module__, module_name)

    def test_moved_code_left_api_actions(self) -> None:
        source = Path(api_actions_module.__file__).read_text(encoding="utf-8")
        for _class_name, names in self.MOVED.values():
            for name in names:
                with self.subTest(method=name):
                    self.assertNotIn(f"def {name}(", source)
        for text in self.MOVED_TEXT:
            with self.subTest(text=text):
                self.assertNotIn(text, source)


if __name__ == "__main__":
    unittest.main()
