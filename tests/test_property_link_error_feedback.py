"""A failed property link reaches the user as a translated warning, never as an exception out of a Qt slot.

Two callers did not catch the failures of `APIModuleActions`:
- the easement preview's `_save_property_details` looked the cadastral numbers up before its `try`;
- the card's "connect properties" flow (`_persist_links`) had no `try`, so its failure branch never ran and the
  map selection was never closed.
"""
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

from qgis.PyQt.QtWidgets import QDialog
from qgis.core import QgsApplication

from Kavitro_dev.constants.cadastral_fields import Katastriyksus
from Kavitro_dev.languages.language_manager import LanguageManager
from Kavitro_dev.languages.translation_keys import TranslationKeys
from Kavitro_dev.modules.easements import easement_preview_dialog as preview_module
from Kavitro_dev.modules.easements.preview_dialog import property_editor_mixin as editor_module
from Kavitro_dev.utils.api_error_handling import ApiError, ApiErrorKind
from Kavitro_dev.widgets.DataDisplayWidgets import module_action_buttons as buttons_module

NETWORK_DOWN = ApiError(ApiErrorKind.NETWORK, "Network is down")
SERVER_TEXT = 'Variable "$input" got invalid value "ORDINANCES" at "input.types[7]"'
GRAPHQL_ERROR = ApiError(ApiErrorKind.GRAPHQL, SERVER_TEXT)

# The language `user_message` itself translates with.
LANG = LanguageManager()


class QgsCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QgsApplication.instance() or QgsApplication([], False)

    def start(self, target, name: str, **kwargs) -> Mock:
        patcher = patch.object(target, name, **kwargs)
        started = patcher.start()
        self.addCleanup(patcher.stop)
        return started


class EasementPropertySaveTest(QgsCase):
    NUMBER = "12345:001:0001"

    def setUp(self) -> None:
        # A real message window would wait for a click that never comes; nothing here may reach the network.
        self.messages = self.start(editor_module, "ModernMessageDialog")
        self.log = self.start(editor_module.PythonFailLogger, "log_exception")
        self.api = self.start(editor_module, "APIModuleActions")
        self.api.get_easement_property_edges.return_value = [{"cadastralUnitNumber": self.NUMBER}]

        self.dialog = preview_module.EasementPreviewDialog.__new__(preview_module.EasementPreviewDialog)
        self.dialog._item_id = "42"
        self.dialog._lang = LANG
        self.dialog._property_edges = [{"cadastralUnitNumber": self.NUMBER}]
        self.dialog._collect_property_payloads = Mock(
            return_value=([{"id": "", "cadastralUnitNumber": self.NUMBER, "isPayable": True}], [])
        )
        self.dialog._set_property_edges = Mock()
        self.dialog._calculate_cut_areas = Mock()
        self.dialog._save_final_cut_to_main_layer = Mock(return_value=(True, ""))
        self.dialog._rerun_automation = Mock()

    def save(self) -> None:
        preview_module.EasementPreviewDialog._save_property_details(self.dialog)

    def failed_text(self, err: str) -> str:
        return LANG.translate(TranslationKeys.EASEMENT_PREVIEW_PROPERTY_SAVE_FAILED).format(
            pid="42", count=1, preview=self.NUMBER, err=err
        )

    def assertWarned(self, text: str) -> None:
        self.messages.show_warning.assert_called_once_with(LANG.translate(TranslationKeys.ERROR), text)
        self.messages.show_info.assert_not_called()
        self.api.associate_easement_properties.assert_not_called()
        self.dialog._rerun_automation.assert_not_called()

    def test_failed_lookup_shows_the_warning_with_the_translated_error(self) -> None:
        self.api.resolve_property_map_by_cadastral.side_effect = NETWORK_DOWN

        self.save()

        self.assertWarned(self.failed_text("Network is down"))
        self.assertNotIn("WC-API", self.messages.show_warning.call_args.args[1])

    def test_failed_lookup_is_logged_for_the_easement(self) -> None:
        self.api.resolve_property_map_by_cadastral.side_effect = NETWORK_DOWN

        self.save()

        self.log.assert_called_once_with(
            NETWORK_DOWN,
            module="easement",
            event="easement_preview_property_save_failed",
            extra={"item_id": "42"},
        )

    def test_graphql_failure_shows_the_short_text_not_the_server_text(self) -> None:
        self.api.resolve_property_map_by_cadastral.side_effect = GRAPHQL_ERROR

        self.save()

        self.assertWarned(self.failed_text(LANG.translate(TranslationKeys.SERVER_REQUEST_NOT_COMPLETED)))
        self.assertNotIn("ORDINANCES", self.messages.show_warning.call_args.args[1])

    def test_failed_save_after_a_good_lookup_still_shows_the_same_warning(self) -> None:
        self.api.resolve_property_map_by_cadastral.return_value = ({self.NUMBER: "p1"}, [])
        self.api.associate_easement_properties.side_effect = NETWORK_DOWN

        self.save()

        self.messages.show_warning.assert_called_once_with(
            LANG.translate(TranslationKeys.ERROR), self.failed_text("Network is down")
        )
        self.messages.show_info.assert_not_called()
        self.log.assert_called_once()

    def test_numbers_unknown_to_kavitro_are_reported_without_saving(self) -> None:
        self.api.resolve_property_map_by_cadastral.return_value = ({}, [self.NUMBER])

        self.save()

        self.assertWarned(self.failed_text(LANG.translate(TranslationKeys.EASEMENT_PREVIEW_PROPERTY_NONE_RESOLVED)))
        self.log.assert_not_called()

    def test_none_resolved_warning_uses_the_translated_text_not_the_english_literal(self) -> None:
        self.api.resolve_property_map_by_cadastral.return_value = ({}, [self.NUMBER])

        self.save()

        text = self.messages.show_warning.call_args.args[1]
        self.assertIn(LANG.translate(TranslationKeys.EASEMENT_PREVIEW_PROPERTY_NONE_RESOLVED), text)
        self.assertNotIn("No property ids", text)

    def test_good_save_reports_success_and_logs_nothing(self) -> None:
        self.api.resolve_property_map_by_cadastral.return_value = ({self.NUMBER: "p1"}, ["99999:001:0009"])

        self.save()

        self.api.resolve_property_map_by_cadastral.assert_called_once_with([self.NUMBER])
        self.api.associate_easement_properties.assert_called_once_with(
            "42", [{"id": "p1", "isPayable": True}]
        )
        note = "\n\n" + LANG.translate(TranslationKeys.LINK_PROPERTIES_MISSING_NOTE).format(missing="99999:001:0009")
        self.messages.show_info.assert_called_once_with(
            LANG.translate(TranslationKeys.SUCCESS),
            LANG.translate(TranslationKeys.EASEMENT_PREVIEW_PROPERTY_SAVE_SUCCESS).format(
                pid="42", count=1, preview=self.NUMBER, extra=note
            ),
        )
        self.messages.show_warning.assert_not_called()
        self.dialog._rerun_automation.assert_called_once()
        self.log.assert_not_called()


class LinkTextModuleNeutralTest(unittest.TestCase):
    """Link texts are shown on every module's card, so they must not name one module (project)."""

    def test_link_texts_do_not_name_the_project_module(self) -> None:
        for language in ("et", "en"):
            manager = LanguageManager(language)
            for key in (TranslationKeys.LINK_PROPERTIES_SUCCESS, TranslationKeys.LINK_PROPERTIES_ERROR):
                text = manager.translate(key).lower()
                for word in ("projekt", "project"):
                    with self.subTest(language=language, key=key):
                        self.assertNotIn(word, text)


class CardPropertyLinkTest(QgsCase):
    NUMBERS = ["1:1", "2:2"]

    def setUp(self) -> None:
        self.messages = self.start(buttons_module, "ModernMessageDialog")
        self.log = self.start(buttons_module.PythonFailLogger, "log_exception")
        self.api = self.start(buttons_module, "APIModuleActions")
        # The existing links are read with their ids (none here); the second read is the refresh after linking.
        self.api.get_linked_properties.return_value = []
        self.api.get_module_item_connected_properties.side_effect = [["1:1", "2:2"]]
        # The mutation answer holds no whole list here, so the linked numbers are read again.
        self.api.linked_cadastral_numbers_from_response.return_value = None

        self.layer = Mock()
        self.start(buttons_module.ActiveLayersHelper, "resolve_main_property_layer", return_value=self.layer)
        self.orchestrator = Mock()
        self.orchestrator.start_selection_for_layer.return_value = True
        self.start(buttons_module, "MapSelectionOrchestrator", return_value=self.orchestrator)
        self.review = self.start(buttons_module, "PropertyLinkReviewDialog").return_value
        self.review.exec.return_value = QDialog.DialogCode.Accepted
        self.review.reselect_requested = False
        self.review.numbers_to_remove = []

        self.button = SimpleNamespace(
            _map_selection_orchestrator=None,
            _on_properties_linked=Mock(),
            _enter_map_selection_mode=Mock(),
            _restore_parent_window=Mock(),
        )

    def select(self, numbers=None) -> None:
        """The user picks `numbers` on the map and confirms the review dialog."""
        buttons_module.MoreActionsButton._link_properties_from_map(self.button, "project", {"id": "7"}, LANG)
        self.assertIs(self.button._map_selection_orchestrator, self.orchestrator)
        on_selected = self.orchestrator.start_selection_for_layer.call_args.kwargs["on_selected"]
        on_selected(self.layer, [{Katastriyksus.tunnus: number} for number in (numbers or self.NUMBERS)])

    def failed_text(self, err: str, numbers=None) -> str:
        numbers = numbers or self.NUMBERS
        return LANG.translate(TranslationKeys.LINK_PROPERTIES_ERROR).format(
            pid="7", count=len(numbers), preview=", ".join(numbers[:5]), err=err
        )

    def assertWarned(self, text: str) -> None:
        self.messages.show_warning.assert_called_once_with(LANG.translate(TranslationKeys.ERROR), text)
        self.messages.show_info.assert_not_called()
        self.button._on_properties_linked.assert_not_called()

    def assertSelectionClosed(self) -> None:
        # Once when the selection ends, once when the review is done.
        self.assertIsNone(self.button._map_selection_orchestrator)
        self.assertEqual(self.button._restore_parent_window.call_count, 2)

    def test_failed_lookup_warns_with_the_translated_error_and_closes_the_selection(self) -> None:
        self.api.resolve_property_ids_by_cadastral.side_effect = NETWORK_DOWN

        self.select()

        self.assertWarned(self.failed_text("Network is down"))
        self.assertNotIn("WC-API", self.messages.show_warning.call_args.args[1])
        self.assertSelectionClosed()
        self.api.associate_properties.assert_not_called()

    def test_failed_lookup_is_logged(self) -> None:
        self.api.resolve_property_ids_by_cadastral.side_effect = NETWORK_DOWN

        self.select()

        self.log.assert_called_once_with(
            NETWORK_DOWN,
            module="project",
            event="module_action_link_properties_failed",
            extra={"item_id": "7"},
        )

    def test_failed_association_warns_logs_and_closes_the_selection(self) -> None:
        self.api.resolve_property_ids_by_cadastral.return_value = (["p1", "p2"], [])
        self.api.associate_properties.side_effect = NETWORK_DOWN

        self.select()

        self.assertWarned(self.failed_text("Network is down"))
        self.log.assert_called_once()
        self.assertSelectionClosed()

    def test_graphql_failure_shows_the_short_text_not_the_server_text(self) -> None:
        self.api.resolve_property_ids_by_cadastral.side_effect = GRAPHQL_ERROR

        self.select()

        self.assertWarned(self.failed_text(LANG.translate(TranslationKeys.SERVER_REQUEST_NOT_COMPLETED)))
        self.assertNotIn("ORDINANCES", self.messages.show_warning.call_args.args[1])
        self.assertSelectionClosed()

    def test_numbers_unknown_to_kavitro_are_listed_in_the_warning(self) -> None:
        self.api.resolve_property_ids_by_cadastral.return_value = ([], list(self.NUMBERS))

        self.select()

        note = LANG.translate(TranslationKeys.LINK_PROPERTIES_MISSING_NOTE).format(missing="1:1, 2:2")
        self.assertWarned(self.failed_text(note))
        self.log.assert_not_called()
        self.api.associate_properties.assert_not_called()
        self.assertSelectionClosed()

    def test_long_list_of_unknown_numbers_is_cut_to_five(self) -> None:
        numbers = [f"{n}:{n}" for n in range(1, 8)]
        self.api.resolve_property_ids_by_cadastral.return_value = ([], numbers)

        self.select(numbers)

        note = (
            LANG.translate(TranslationKeys.LINK_PROPERTIES_MISSING_NOTE).format(missing=", ".join(numbers[:5]))
            + LANG.translate(TranslationKeys.MORE_COUNT_SUFFIX).format(count=2)
        )
        summary = ", ".join(numbers[:5]) + LANG.translate(TranslationKeys.MORE_COUNT_SUFFIX).format(count=2)
        self.messages.show_warning.assert_called_once_with(
            LANG.translate(TranslationKeys.ERROR),
            LANG.translate(TranslationKeys.LINK_PROPERTIES_ERROR).format(
                pid="7", count=7, preview=summary, err=note
            ),
        )

    def test_good_link_reports_success_with_the_missing_note(self) -> None:
        self.api.resolve_property_ids_by_cadastral.return_value = (["p1", "p2"], ["3:3"])

        self.select()

        self.api.associate_properties.assert_called_once_with("project", "7", ["p1", "p2"])
        # Both are new links: the message says so apart from the total (found 2026-11-23).
        note = ("\n\n" + LANG.translate(TranslationKeys.LINK_PROPERTIES_ADDED_NOTE).format(added=2, already=0)
                + "\n\n" + LANG.translate(TranslationKeys.LINK_PROPERTIES_MISSING_NOTE).format(missing="3:3"))
        self.messages.show_info.assert_called_once_with(
            LANG.translate(TranslationKeys.SUCCESS),
            LANG.translate(TranslationKeys.LINK_PROPERTIES_SUCCESS).format(
                pid="7", count=2, preview="1:1, 2:2", extra=note
            ),
        )
        self.messages.show_warning.assert_not_called()
        self.button._on_properties_linked.assert_called_once_with(["1:1", "2:2"])
        self.log.assert_not_called()
        self.assertSelectionClosed()

    def test_linked_numbers_come_from_the_mutation_answer_without_a_second_read(self) -> None:
        self.api.resolve_property_ids_by_cadastral.return_value = (["p1", "p2"], [])
        self.api.linked_cadastral_numbers_from_response.return_value = ["1:1", "2:2", "9:9"]

        self.select()

        response = self.api.associate_properties.return_value
        self.api.linked_cadastral_numbers_from_response.assert_called_once_with("project", response)
        # Only the read of the existing links before the selection.
        self.api.get_linked_properties.assert_called_once_with("project", "7")
        self.api.get_module_item_connected_properties.assert_not_called()
        self.button._on_properties_linked.assert_called_once_with(["1:1", "2:2", "9:9"])
        self.messages.show_warning.assert_not_called()

    def test_cancelled_review_links_nothing_and_closes_the_selection(self) -> None:
        self.review.exec.return_value = QDialog.DialogCode.Rejected

        self.select()

        self.api.resolve_property_ids_by_cadastral.assert_not_called()
        self.messages.show_warning.assert_not_called()
        self.messages.show_info.assert_not_called()
        self.assertSelectionClosed()


if __name__ == "__main__":
    unittest.main()
