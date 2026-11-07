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
from PyQt5.QtWidgets import QApplication, QLabel

from Kavitro_dev.languages.language_manager import LanguageManager
from Kavitro_dev.modules.Property import query_cordinator
from Kavitro_dev.modules.Property.property_service import PropertyDataService
from Kavitro_dev.modules.Property.property_tree_widget import ModuleConnectionRow, PropertyConnectionCard
from Kavitro_dev.modules.Property.query_cordinator import (
    PropertiesConnectedElementsQueries,
    PropertyConnectionFormatter,
)
from Kavitro_dev.modules.projects.project_board_overview_service import ProjectBoardOverviewService
from Kavitro_dev.utils.url_manager import Module, ModuleSupports

PROPERTY_ID = "p1"
CADASTRAL = "12345:001:0001"
WORK_TYPE = "7"
ASBUILT_TYPE = "9"


def task(task_id: str, type_id: str) -> dict:
    return {
        "__typename": "Task",
        "id": task_id,
        "title": f"Töö {task_id}",
        "startAt": None,
        "dueAt": "2026-11-20",
        "createdAt": "2026-11-01T08:00:00+00:00",
        "updatedAt": "2026-11-02T08:00:00+00:00",
        "members": {"edges": []},
        "status": {"id": "s1", "name": "Avatud", "color": "00aa00", "type": "OPEN"},
        "priority": "HIGH",
        "type": {"id": type_id, "name": "Remont" if type_id == WORK_TYPE else "Teostusjoonis"},
        "properties": {"pageInfo": {"count": 1}},
    }


def tasks_page(nodes, *, end_cursor=None, has_next=False) -> dict:
    return {
        "data": {
            "property": {
                "__typename": "Property",
                "id": PROPERTY_ID,
                "tasks": {
                    "pageInfo": {"hasNextPage": has_next, "endCursor": end_cursor, "total": len(nodes)},
                    "edges": [{"node": node} for node in nodes],
                },
            }
        }
    }


class FakeBackend:
    """Answers the property lookup, the tasks connection and empty other connections."""

    def __init__(self, task_page):
        self._task_page = task_page
        self.task_variables = []

    def send_query(self, query, variables=None, return_raw=False):
        variables = dict(variables or {})
        if "query properties(" in query:
            return {"data": {"properties": {"edges": [{"node": {"id": PROPERTY_ID}}]}}}
        if "tasks(first: $first" in query:
            self.task_variables.append(variables)
            return self._task_page(variables.get("after"))
        return {"data": {"property": {"id": variables.get("id")}}}


def pages(by_cursor: dict):
    return lambda after: by_cursor[after]


def preference_ids(type_ids):
    def load(module_key, *, support_key):
        if module_key == Module.WORKS.value and support_key == ModuleSupports.TYPES.value:
            return list(type_ids)
        return []
    return load


class BackendTestCase(unittest.TestCase):
    def use_backend(self, task_page, *, works_types=(WORK_TYPE,)) -> FakeBackend:
        backend = FakeBackend(task_page)
        for patcher in (
            patch.object(query_cordinator, "APIClient", return_value=Mock(send_query=backend.send_query)),
            patch.object(
                query_cordinator.SettingsLogic,
                "load_module_preference_ids",
                side_effect=preference_ids(works_types),
            ),
        ):
            patcher.start()
            self.addCleanup(patcher.stop)
        return backend


class PropertyWorksQueryTest(BackendTestCase):
    def fetch_works(self):
        return PropertiesConnectedElementsQueries().fetch_module_data(Module.WORKS.value, PROPERTY_ID)

    def test_works_are_read_from_the_property_tasks_without_an_order_clause(self) -> None:
        backend = self.use_backend(pages({None: tasks_page([task("1", WORK_TYPE)])}))

        self.fetch_works()

        self.assertEqual(
            PropertiesConnectedElementsQueries.module_to_filename[Module.WORKS.value],
            "connected_tasks.graphql",
        )
        # Tasks have no NUMBER column, and the property tasks order clause is unverified.
        self.assertEqual(backend.task_variables, [{"id": PROPERTY_ID, "first": 30, "after": None}])

    def test_only_tasks_of_the_works_types_are_works_on_every_page(self) -> None:
        backend = self.use_backend(pages({
            None: tasks_page([task("1", WORK_TYPE), task("2", ASBUILT_TYPE)], end_cursor="c1", has_next=True),
            "c1": tasks_page([task("3", WORK_TYPE)], end_cursor="c2"),
        }))

        works = self.fetch_works()

        self.assertEqual([work["id"] for work in works], ["1", "3"])
        self.assertEqual([variables["after"] for variables in backend.task_variables], [None, "c1"])

    def test_without_works_types_every_task_is_a_work(self) -> None:
        self.use_backend(
            pages({None: tasks_page([task("1", WORK_TYPE), task("2", ASBUILT_TYPE)])}),
            works_types=(),
        )

        self.assertEqual([work["id"] for work in self.fetch_works()], ["1", "2"])

    def test_page_limit_stops_the_request_loop_and_is_logged(self) -> None:
        backend = self.use_backend(
            lambda after: tasks_page([task(f"{after}-w", WORK_TYPE)], end_cursor=f"{after}+", has_next=True)
        )

        with patch.object(query_cordinator.PythonFailLogger, "log") as log:
            works = self.fetch_works()

        limit = PropertiesConnectedElementsQueries.WORKS_MAX_PAGES
        self.assertEqual(len(backend.task_variables), limit)
        self.assertEqual(len(works), limit)
        log.assert_called_once()
        self.assertEqual(log.call_args.args[0], "property_works_page_limit_reached")

    def test_missing_property_or_tasks_maps_to_no_works(self) -> None:
        current = {}
        self.use_backend(lambda after: current["response"])

        for response in (
            {"data": {"property": None}},
            {"data": {"property": {"id": PROPERTY_ID, "tasks": None}}},
            {"data": None},
            {},
        ):
            with self.subTest(response=response):
                current["response"] = response
                self.assertEqual(self.fetch_works(), [])


class PropertyConnectionsWithWorksTest(BackendTestCase):
    def build_connections(self) -> dict:
        service = PropertyDataService()
        with patch.object(service, "_session_signature", return_value="test-session"):
            return service.build_connections_for_cadastral(CADASTRAL)

    def test_property_connections_list_works_with_count_and_summaries(self) -> None:
        self.use_backend(pages({None: tasks_page([task("1", WORK_TYPE), task("2", ASBUILT_TYPE), task("3", WORK_TYPE)])}))

        payload = self.build_connections()

        connections = payload["entries"][0]["moduleConnections"]
        self.assertEqual(set(connections), {Module.WORKS.value})
        works = connections[Module.WORKS.value]
        self.assertEqual(works["count"], 2)
        summary = works["items"][0]
        self.assertEqual(
            {key: summary[key] for key in ("id", "number", "title", "status", "type", "updatedAt")},
            {
                "id": "1",
                "number": None,
                "title": "Töö 1",
                "status": "Avatud",
                "type": "Remont",
                "updatedAt": "2026-11-02T08:00:00+00:00",
            },
        )
        self.assertEqual(summary["raw"]["properties"], {"pageInfo": {"count": 1}})

    def test_property_without_works_gets_no_works_connection(self) -> None:
        self.use_backend(pages({None: tasks_page([task("2", ASBUILT_TYPE)])}))

        payload = self.build_connections()

        self.assertEqual(payload["entries"][0]["moduleConnections"], {})

    def test_failed_works_request_is_logged_and_other_connections_stay(self) -> None:
        def refuse(_after):
            raise RuntimeError("[WC-API][graphql] Cannot query field tasks")

        self.use_backend(refuse)

        with patch.object(query_cordinator.PythonFailLogger, "log_exception") as log_exception:
            module_data = PropertiesConnectedElementsQueries().fetch_all_module_data(PROPERTY_ID)

        self.assertEqual(module_data, {})
        log_exception.assert_called_once()
        self.assertEqual(log_exception.call_args.kwargs["extra"], {"target_module": Module.WORKS.value})

    def test_project_board_lists_works_of_the_project_properties(self) -> None:
        self.use_backend(pages({None: tasks_page([task("1", WORK_TYPE), task("2", ASBUILT_TYPE)])}))

        items = ProjectBoardOverviewService._load_connected_module_items([CADASTRAL], exclude_project_id="")

        self.assertEqual([item["id"] for item in items[Module.WORKS.value]], ["1"])
        self.assertEqual(items[Module.WORKS.value][0]["title"], "Töö 1")


class PropertyTreeWorksSectionTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.lang = LanguageManager("et")

    def build_card(self, module_connections: dict) -> PropertyConnectionCard:
        entry = PropertyConnectionFormatter().build_entry(CADASTRAL, PROPERTY_ID, module_connections)
        card = PropertyConnectionCard(entry, self.lang)
        self.addCleanup(self.dispose, card)
        return card

    @staticmethod
    def dispose(card) -> None:
        card.hide()
        card.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)

    def label_texts(self, card) -> list[str]:
        return [label.text() for label in card.findChildren(QLabel)]

    def test_works_section_shows_its_title_count_and_rows(self) -> None:
        card = self.build_card({Module.WORKS.value: [task("1", WORK_TYPE), task("3", WORK_TYPE)]})

        self.assertIn("Tööd (2)", self.label_texts(card))
        rows = card.findChildren(ModuleConnectionRow)
        self.assertEqual([row.item_id for row in rows], ["1", "3"])
        self.assertEqual({row.module_key for row in rows}, {Module.WORKS.value})
        self.assertIn("Töö 1", self.label_texts(card))

    def test_card_without_works_has_no_works_section(self) -> None:
        contract = {"id": "c1", "number": "L-1", "name": "Leping", "status": {"name": "Avatud"}}
        card = self.build_card({Module.CONTRACT.value: [contract]})

        texts = self.label_texts(card)
        self.assertFalse([text for text in texts if text.startswith(self.lang.translate_module_name(Module.WORKS.value))])
        self.assertEqual([row.module_key for row in card.findChildren(ModuleConnectionRow)], [Module.CONTRACT.value])


if __name__ == "__main__":
    unittest.main()
