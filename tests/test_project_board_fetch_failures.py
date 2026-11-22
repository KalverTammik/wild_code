"""A failed connected-module request must show as a load failure, never as "nothing linked"."""
from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
if os.environ.get("QGIS_PREFIX_PATH"):
    sys.path.append(str(Path(os.environ["QGIS_PREFIX_PATH"]) / "python" / "plugins"))

from qgis.core import QgsApplication
from PyQt5.QtCore import QCoreApplication, QEvent
from PyQt5.QtWidgets import QLabel, QWidget

from Kavitro_dev.Logs.python_fail_logger import PythonFailLogger
from Kavitro_dev.languages.language_manager import LanguageManager
from Kavitro_dev.languages.translation_keys import TranslationKeys
from Kavitro_dev.modules.Property.property_service import PropertyDataService
from Kavitro_dev.modules.Property.query_cordinator import (
    ConnectedModuleData,
    PropertiesConnectedElementsQueries,
    PropertyLookupService,
)
from Kavitro_dev.modules.projects.project_board_overview_service import ProjectBoardOverviewService
from Kavitro_dev.modules.projects.project_board_status_rules import ProjectBoardStatusRules
from Kavitro_dev.modules.projects.project_board_widgets import ProjectBoardOverviewWidget
from Kavitro_dev.ui.messages_helper import ModernMessageDialog
from Kavitro_dev.constants.module_names import Module

ALL_MODULES = list(PropertiesConnectedElementsQueries.module_to_filename)
WORK = {"id": "w1", "title": "Töö 1", "status": {"id": "s1", "name": "Avatud", "type": "OPEN"}}
CONTRACT = {"id": "c1", "number": "L-1", "name": "Leping", "status": {"id": "s2", "name": "Lõpetatud", "type": "CLOSED"}}


def project(*cadastral_numbers: str) -> dict:
    return {
        "id": "pr-1",
        "properties": {"edges": [{"node": {"cadastralUnitNumber": number}} for number in cadastral_numbers]},
    }


def module_fetch(results: dict):
    """fetch_module_data stand-in: an Exception value raises, anything else is the module's nodes."""

    def fetch(module_key, _property_id):
        value = results.get(module_key, [])
        if isinstance(value, Exception):
            raise value
        return value

    return fetch


class BoardFailureTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QgsApplication.instance() or QgsApplication([], False)

    def setUp(self) -> None:
        self.lang = LanguageManager("et")
        for target, name, kwargs in (
            # A real message window would wait for a click that never comes.
            (ModernMessageDialog, "show_info", {}),
            (ModernMessageDialog, "show_warning", {}),
            (ModernMessageDialog, "show_error", {}),
            (ModernMessageDialog, "Warning_messages_modern", {}),
            (PythonFailLogger, "log_exception", {}),
            (ProjectBoardStatusRules, "load_not_started_status_ids", {"return_value": set()}),
        ):
            patcher = patch.object(target, name, **kwargs)
            patcher.start()
            self.addCleanup(patcher.stop)

    def use_lookup(self, ids_by_number: dict) -> None:
        patcher = patch.object(
            PropertyLookupService,
            "property_id_by_cadastral",
            side_effect=lambda number: ids_by_number.get(number),
        )
        patcher.start()
        self.addCleanup(patcher.stop)

    def use_modules(self, results: dict) -> None:
        patcher = patch.object(PropertiesConnectedElementsQueries, "fetch_module_data", side_effect=module_fetch(results))
        patcher.start()
        self.addCleanup(patcher.stop)

    def board(self, *cadastral_numbers: str) -> dict:
        return ProjectBoardOverviewService.build_project_board_data(project(*cadastral_numbers), lang_manager=self.lang)

    def t(self, key: str) -> str:
        return self.lang.translate(key)


class FetchAllModuleDataTest(BoardFailureTestCase):
    def test_failed_module_is_reported_apart_from_modules_without_nodes(self) -> None:
        error = RuntimeError("[WC-API] timeout")
        self.use_modules({Module.WORKS.value: [WORK], Module.CONTRACT.value: error})

        result = PropertiesConnectedElementsQueries().fetch_all_module_data("p1")

        self.assertIsInstance(result, ConnectedModuleData)
        self.assertEqual(result.nodes_by_module, {Module.WORKS.value: [WORK]})
        self.assertEqual(result.errors, {Module.CONTRACT.value: error})


class ProjectBoardFailureTest(BoardFailureTestCase):
    def test_partly_failed_load_names_the_failed_module_and_does_not_claim_nothing_is_linked(self) -> None:
        self.use_lookup({"1:1": "p1"})
        self.use_modules({Module.WORKS.value: [WORK], Module.CONTRACT.value: RuntimeError("[WC-API] timeout")})

        data = self.board("1:1")

        self.assertIn(self.lang.translate_module_name(Module.CONTRACT.value), data["notice"])
        self.assertEqual(
            data["notice"],
            self.t(TranslationKeys.PROJECT_BOARD_DETAILS_LOAD_FAILED_MODULES).format(
                modules=self.lang.translate_module_name(Module.CONTRACT.value)
            ),
        )
        todo, in_progress, done = data["columns"]
        self.assertEqual([group["module_key"] for group in in_progress["groups"]], [Module.WORKS.value])
        incomplete = self.t(TranslationKeys.PROJECT_BOARD_DETAILS_EMPTY_INCOMPLETE)
        self.assertEqual(todo["empty_text"], incomplete)
        self.assertEqual(done["empty_text"], incomplete)

    def test_successful_load_keeps_the_nothing_linked_texts_and_has_no_notice(self) -> None:
        self.use_lookup({"1:1": "p1"})
        self.use_modules({Module.CONTRACT.value: [CONTRACT]})

        data = self.board("1:1")

        self.assertEqual(data["notice"], "")
        todo, in_progress, done = data["columns"]
        self.assertEqual(todo["empty_text"], self.t(TranslationKeys.PROJECT_BOARD_DETAILS_EMPTY_TODO))
        self.assertEqual(in_progress["empty_text"], self.t(TranslationKeys.PROJECT_BOARD_DETAILS_EMPTY_IN_PROGRESS))
        self.assertEqual([group["module_key"] for group in done["groups"]], [Module.CONTRACT.value])

    def test_board_whose_every_module_failed_raises_so_the_card_shows_a_load_failure(self) -> None:
        error = RuntimeError("[WC-API] offline")
        self.use_lookup({"1:1": "p1", "2:2": "p2"})
        self.use_modules({module_key: error for module_key in ALL_MODULES})

        with self.assertRaises(RuntimeError) as raised:
            self.board("1:1", "2:2")

        self.assertIs(raised.exception, error)

    def test_failed_property_marks_every_module_as_not_loaded_and_keeps_the_other_property(self) -> None:
        self.use_lookup({"1:1": "p1", "2:2": "p2"})

        def fetch_all(property_id):
            if property_id == "p1":
                raise RuntimeError("[WC-API] timeout")
            return ConnectedModuleData(nodes_by_module={Module.WORKS.value: [WORK]})

        with patch.object(PropertiesConnectedElementsQueries, "fetch_all_module_data", side_effect=fetch_all):
            items, failed_modules = ProjectBoardOverviewService._load_connected_module_items(
                ["1:1", "2:2"], exclude_project_id=""
            )

        self.assertEqual([item["id"] for item in items[Module.WORKS.value]], ["w1"])
        self.assertEqual(set(failed_modules), set(ALL_MODULES))

    def test_every_property_failing_raises(self) -> None:
        error = RuntimeError("[WC-API] timeout")
        self.use_lookup({"1:1": "p1"})

        with patch.object(PropertiesConnectedElementsQueries, "fetch_all_module_data", side_effect=error):
            with self.assertRaises(RuntimeError):
                ProjectBoardOverviewService._load_connected_module_items(["1:1"], exclude_project_id="")


class ProjectBoardNoticeWidgetTest(BoardFailureTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.host = QWidget()
        self.addCleanup(self.dispose)

    def dispose(self) -> None:
        self.host.hide()
        self.host.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)

    def notice_labels(self, board_data: dict) -> list[QLabel]:
        widget = ProjectBoardOverviewWidget(board_data, self.host)
        return widget.findChildren(QLabel, "ProjectBoardNoticeLabel")

    def test_notice_is_shown_above_the_columns(self) -> None:
        self.use_lookup({"1:1": "p1"})
        self.use_modules({Module.WORKS.value: [WORK], Module.CONTRACT.value: RuntimeError("[WC-API] timeout")})
        data = self.board("1:1")

        labels = self.notice_labels(data)

        self.assertEqual([label.text() for label in labels], [data["notice"]])

    def test_board_without_failures_has_no_notice(self) -> None:
        self.use_lookup({"1:1": "p1"})
        self.use_modules({Module.WORKS.value: [WORK]})

        self.assertEqual(self.notice_labels(self.board("1:1")), [])


class PropertyConnectionsFailureTest(BoardFailureTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.use_lookup({"1:1": "p1"})
        self.service = PropertyDataService()
        patcher = patch.object(self.service, "_session_signature", return_value="test-session")
        patcher.start()
        self.addCleanup(patcher.stop)

    def counting_fetch(self, results: dict) -> list:
        calls = []
        fetch = module_fetch(results)

        def counted(module_key, property_id):
            calls.append(module_key)
            return fetch(module_key, property_id)

        patcher = patch.object(PropertiesConnectedElementsQueries, "fetch_module_data", side_effect=counted)
        patcher.start()
        self.addCleanup(patcher.stop)
        return calls

    def test_property_whose_every_module_failed_raises_instead_of_showing_no_connections(self) -> None:
        error = RuntimeError("[WC-API] offline")
        self.counting_fetch({module_key: error for module_key in ALL_MODULES})

        with self.assertRaises(RuntimeError) as raised:
            self.service.build_connections_for_cadastral("1:1")

        self.assertIs(raised.exception, error)

    def test_partly_failed_property_keeps_the_loaded_modules_and_is_asked_again(self) -> None:
        calls = self.counting_fetch({Module.WORKS.value: [WORK], Module.CONTRACT.value: RuntimeError("[WC-API] timeout")})

        payload = self.service.build_connections_for_cadastral("1:1")
        self.service.build_connections_for_cadastral("1:1")

        self.assertEqual(set(payload["entries"][0]["moduleConnections"]), {Module.WORKS.value})
        self.assertEqual(len(calls), 2 * len(ALL_MODULES))

    def test_fully_loaded_property_is_cached(self) -> None:
        calls = self.counting_fetch({Module.WORKS.value: [WORK]})

        self.service.build_connections_for_cadastral("1:1")
        self.service.build_connections_for_cadastral("1:1")

        self.assertEqual(len(calls), len(ALL_MODULES))


if __name__ == "__main__":
    unittest.main()
