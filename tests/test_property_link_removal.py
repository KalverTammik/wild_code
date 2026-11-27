"""Property links can be removed from a record (user decision 2026-11-24).

Two ways in: the "Link properties" review marks linked properties for removal, and the card menu
"Remove linked properties" lists them. A named confirmation (default No), one request, and success only
after Kavitro no longer links them. The request shape is RelatedPropertiesInput / EasementPropertiesInput
{associate, dissociate: [ID]} (kavitro.dev reference, checked 2026-11-24).
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

from qgis.core import QgsApplication
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtWidgets import QDialog

from Kavitro_dev.constants.cadastral_fields import Katastriyksus
from Kavitro_dev.languages.language_manager import LanguageManager
from Kavitro_dev.languages.translation_keys import TranslationKeys
from Kavitro_dev.Logs.python_fail_logger import PythonFailLogger
from Kavitro_dev.python.actions import property_link_actions as actions_module
from Kavitro_dev.python.actions.property_link_actions import PropertyLinkActions
from Kavitro_dev.widgets.DataDisplayWidgets import module_action_buttons as buttons_module
from Kavitro_dev.widgets.DataDisplayWidgets import property_link_removal as removal_module
from Kavitro_dev.widgets.DataDisplayWidgets.LinkReviewDialog import PropertyLinkReviewDialog

_APP = QgsApplication.instance() or QgsApplication([], False)
LANG = LanguageManager()
P1 = {"id": "p1", "number": "1:1", "address": "Tee 1"}
P2 = {"id": "p2", "number": "2:2", "address": ""}


def page(root: str, nodes, *, end=None, more=False) -> dict:
    return {"data": {root: {"properties": {
        "pageInfo": {"endCursor": end, "hasNextPage": more, "total": len(nodes)},
        "edges": [{"node": node} for node in nodes],
    }}}}


class Case(unittest.TestCase):
    def start(self, target, name, **kwargs):
        patcher = patch.object(target, name, **kwargs)
        mock = patcher.start()
        self.addCleanup(patcher.stop)
        return mock

    def setUp(self) -> None:
        for name in ("log", "log_exception"):
            self.start(PythonFailLogger, name)


class ApiTest(Case):
    def setUp(self) -> None:
        super().setUp()
        self.client = Mock()
        self.start(actions_module, "APIClient", return_value=self.client)
        self.start(actions_module.GraphQLQueryLoader, "load_query_by_module", side_effect=lambda m, f: f"{m}/{f}")

    def test_the_linked_properties_come_with_ids_from_every_page(self) -> None:
        self.client.send_query.side_effect = [
            page("project", [{"id": "p1", "cadastralUnitNumber": "1:1", "displayAddress": "Tee 1"}], end="c1", more=True),
            page("project", [{"id": "p2", "cadastralUnitNumber": "2:2"}]),
        ]
        self.assertEqual(PropertyLinkActions.get_linked_properties("project", "7"), [P1, P2])
        self.assertEqual([c.kwargs["variables"]["propertiesAfter"] for c in self.client.send_query.call_args_list],
                         [None, "c1"])

    def test_works_read_the_task(self) -> None:
        self.client.send_query.return_value = page("task", [])
        PropertyLinkActions.get_linked_properties("works", "9")
        self.assertEqual(self.client.send_query.call_args.args[0], "task/w_tasks_module_data_by_item_id.graphql")

    def test_a_failed_read_raises_instead_of_a_partial_list(self) -> None:
        self.client.send_query.side_effect = [
            page("project", [{"id": "p1", "cadastralUnitNumber": "1:1"}], end="c1", more=True), {"errors": ["x"]}]
        with self.assertRaises(RuntimeError):
            PropertyLinkActions.get_linked_properties("project", "7")

    def test_one_request_adds_and_removes(self) -> None:
        self.client.send_query.return_value = {"data": {"updateProject": {"id": "7"}}}
        PropertyLinkActions.update_property_links("project", "7", associate_ids=["p3"], dissociate_ids=["p1"])
        query, = self.client.send_query.call_args.args
        self.assertEqual(query, "project/updateProjectProperties.graphql")
        self.assertEqual(self.client.send_query.call_args.kwargs["variables"],
                         {"input": {"id": "7", "properties": {"associate": ["p3"], "dissociate": ["p1"]}}})

    def test_an_easement_removes_by_id_and_adds_as_objects(self) -> None:
        self.client.send_query.return_value = {"data": {"updateEasement": {"id": "5"}}}
        PropertyLinkActions.update_property_links("easement", "5", associate_ids=["p3"], dissociate_ids=["p1"])
        self.assertEqual(self.client.send_query.call_args.kwargs["variables"]["input"]["properties"],
                         {"associate": [{"id": "p3"}], "dissociate": ["p1"]})

    def test_a_removal_only_sends_no_associate(self) -> None:
        self.client.send_query.return_value = {"data": {"updateTask": {"id": "9"}}}
        PropertyLinkActions.update_property_links("asbuilt", "9", dissociate_ids=["p1"])
        self.assertEqual(self.client.send_query.call_args.kwargs["variables"]["input"]["properties"], {"dissociate": ["p1"]})

    def test_nothing_to_change_or_no_answer_raises(self) -> None:
        with self.assertRaises(ValueError):
            PropertyLinkActions.update_property_links("project", "7")
        self.client.send_query.return_value = {"data": {"updateProject": None}}
        with self.assertRaises(RuntimeError):
            PropertyLinkActions.update_property_links("project", "7", dissociate_ids=["p1"])

    def test_a_removal_is_checked_by_reading_back(self) -> None:
        with patch.object(PropertyLinkActions, "update_property_links"), \
                patch.object(PropertyLinkActions, "get_linked_properties", return_value=[P2]):
            self.assertEqual(PropertyLinkActions.remove_property_links("project", "7", ["p1"]), [P2])
        with patch.object(PropertyLinkActions, "update_property_links"), \
                patch.object(PropertyLinkActions, "get_linked_properties", return_value=[P1, P2]), \
                self.assertRaises(RuntimeError):
            PropertyLinkActions.remove_property_links("project", "7", ["p1"])


class DialogsTest(Case):
    def setUp(self) -> None:
        super().setUp()
        self.ask = self.start(removal_module.ModernMessageDialog, "ask_choice_modern")

    def test_the_review_marks_links_for_removal(self) -> None:
        dialog = PropertyLinkReviewDialog({"1:1": "Tee 1 — 1:1", "2:2": "2:2"}, {"3:3": "3:3"}, LANG, allow_removal=True)
        self.addCleanup(dialog.deleteLater)
        self.assertEqual(dialog.numbers_to_remove, [])
        self.assertEqual(dialog._confirm_btn.text(), LANG.translate(TranslationKeys.LINK_REVIEW_ADD_SELECTED))
        row = next(r for r in range(dialog._existing_list.count()) if dialog._existing_list.item(r).data(Qt.ItemDataRole.UserRole) == "2:2")
        dialog._existing_list.item(row).setCheckState(Qt.CheckState.Checked)
        self.assertEqual(dialog.numbers_to_remove, ["2:2"])
        self.assertEqual(dialog._confirm_btn.text(), LANG.translate(TranslationKeys.LINK_REVIEW_SAVE_CHANGES))

    def test_without_ids_the_review_stays_add_only(self) -> None:
        dialog = PropertyLinkReviewDialog({"1:1": "1:1"}, {}, LANG)
        self.addCleanup(dialog.deleteLater)
        self.assertFalse(dialog._existing_list.item(0).flags() & Qt.ItemFlag.ItemIsUserCheckable)

    def test_the_list_starts_with_nothing_ticked(self) -> None:
        dialog = removal_module.PropertyUnlinkDialog([P1, P2], LANG, module="project")
        self.addCleanup(dialog.deleteLater)
        self.assertEqual(dialog.checked_entries(), [])
        self.assertFalse(dialog._remove_button.isEnabled())
        dialog._list.item(0).setCheckState(Qt.CheckState.Checked)
        self.assertTrue(dialog._remove_button.isEnabled())
        self.assertEqual(len(dialog.checked_entries()), 1)

    def test_the_confirmation_names_the_links_and_defaults_to_no(self) -> None:
        self.ask.return_value = LANG.translate(TranslationKeys.NO)
        self.assertFalse(removal_module.confirm_link_removal(LANG, "project", "P-1", [P1]))
        kwargs = self.ask.call_args.kwargs
        self.assertEqual(kwargs["default"], LANG.translate(TranslationKeys.NO))
        self.assertIn("Tee 1 — 1:1", self.ask.call_args.args[1])
        self.assertNotIn(LANG.translate(TranslationKeys.LINK_REMOVE_EASEMENT_WARNING), self.ask.call_args.args[1])

    def test_an_easement_warns_about_its_link_data(self) -> None:
        self.ask.return_value = LANG.translate(TranslationKeys.YES)
        self.assertTrue(removal_module.confirm_link_removal(LANG, "easement", "S-1", [P1]))
        self.assertIn(LANG.translate(TranslationKeys.LINK_REMOVE_EASEMENT_WARNING), self.ask.call_args.args[1])


class MenuFlowTest(Case):
    def setUp(self) -> None:
        super().setUp()
        self.messages = self.start(removal_module, "ModernMessageDialog")
        self.api = self.start(removal_module, "APIModuleActions")
        self.api._property_owner_module.side_effect = PropertyLinkActions._property_owner_module
        self.api.get_linked_properties.return_value = [P1, P2]
        self.api.remove_property_links.return_value = [P2]
        self.dialog = self.start(removal_module, "PropertyUnlinkDialog").return_value
        self.dialog.exec.return_value = QDialog.DialogCode.Accepted
        self.dialog.checked_entries.return_value = [P1]
        self.confirm = self.start(removal_module, "confirm_link_removal", return_value=True)
        self.changed = Mock()

    def run_flow(self) -> bool:
        return removal_module.unlink_properties_from_card(
            module="contract", item_id="7", item_label="L-1", lang=LANG, on_linked_changed=self.changed)

    def test_a_confirmed_removal_tells_the_card(self) -> None:
        self.assertTrue(self.run_flow())
        self.api.remove_property_links.assert_called_once_with("contract", "7", ["p1"])
        self.changed.assert_called_once_with(["2:2"])
        self.messages.show_info.assert_called_once()

    def test_no_confirmation_sends_nothing(self) -> None:
        self.confirm.return_value = False
        self.assertFalse(self.run_flow())
        self.api.remove_property_links.assert_not_called()

    def test_a_cancelled_list_sends_nothing(self) -> None:
        self.dialog.exec.return_value = QDialog.DialogCode.Rejected
        self.assertFalse(self.run_flow())
        self.api.remove_property_links.assert_not_called()

    def test_a_failed_read_changes_nothing_and_says_so(self) -> None:
        self.api.get_linked_properties.side_effect = RuntimeError("offline")
        self.assertFalse(self.run_flow())
        self.api.remove_property_links.assert_not_called()
        self.messages.show_warning.assert_called_once()

    def test_a_failed_removal_is_not_shown_as_done(self) -> None:
        self.api.remove_property_links.side_effect = RuntimeError("still linked")
        self.assertFalse(self.run_flow())
        self.changed.assert_not_called()
        self.messages.show_info.assert_not_called()
        self.messages.show_warning.assert_called_once()

    def test_nothing_linked_says_so(self) -> None:
        self.api.get_linked_properties.return_value = []
        self.assertFalse(self.run_flow())
        self.messages.show_info.assert_called_once()


class ReviewFlowTest(Case):
    """The card's "Link properties" review: an add and a removal go out in one request."""

    def setUp(self) -> None:
        super().setUp()
        self.messages = self.start(buttons_module, "ModernMessageDialog")
        self.api = self.start(buttons_module, "APIModuleActions")
        self.api.get_linked_properties.side_effect = [[P1, P2], [P2, {"id": "p3", "number": "3:3", "address": ""}]]
        self.api.resolve_property_ids_by_cadastral.return_value = (["p3"], [])
        self.confirm = self.start(buttons_module, "confirm_link_removal", return_value=True)
        self.layer = Mock()
        self.start(buttons_module.ActiveLayersHelper, "resolve_main_property_layer", return_value=self.layer)
        self.start(buttons_module.MapHelpers, "find_features_by_fields_and_values", return_value=[])
        self.start(buttons_module.PropertiesSelectors, "show_connected_properties_on_map")
        self.orchestrator = Mock()
        self.orchestrator.start_selection_for_layer.return_value = True
        self.start(buttons_module, "MapSelectionOrchestrator", return_value=self.orchestrator)
        self.review_class = self.start(buttons_module, "PropertyLinkReviewDialog")
        self.review = self.review_class.return_value
        self.review.exec.return_value = QDialog.DialogCode.Accepted
        self.review.reselect_requested = False
        self.review.numbers_to_remove = ["1:1"]
        self.button = SimpleNamespace(_map_selection_orchestrator=None, _on_properties_linked=Mock(),
                                      _enter_map_selection_mode=Mock(), _restore_parent_window=Mock(),
                                      _parent_window=None)

    def select(self) -> None:
        buttons_module.MoreActionsButton._link_properties_from_map(self.button, "project", {"id": "7"}, LANG)
        on_selected = self.orchestrator.start_selection_for_layer.call_args.kwargs["on_selected"]
        on_selected(self.layer, [{Katastriyksus.tunnus: "3:3"}])

    def test_one_request_adds_and_removes_and_the_card_follows(self) -> None:
        self.select()
        self.assertTrue(self.review_class.call_args.kwargs["allow_removal"])
        self.api.update_property_links.assert_called_once_with(
            "project", "7", associate_ids=["p3"], dissociate_ids=["p1"])
        self.button._on_properties_linked.assert_called_once_with(["2:2", "3:3"])
        text = self.messages.show_info.call_args.args[1]
        self.assertIn(LANG.translate(TranslationKeys.LINK_REMOVED_NOTE).format(removed=1), text)

    def test_no_confirmation_changes_nothing(self) -> None:
        self.confirm.return_value = False
        self.select()
        self.api.update_property_links.assert_not_called()
        self.api.associate_properties.assert_not_called()

    def test_a_link_kavitro_kept_is_a_failure(self) -> None:
        self.api.get_linked_properties.side_effect = [[P1, P2], [P1, P2]]
        self.select()
        self.button._on_properties_linked.assert_not_called()
        self.messages.show_warning.assert_called_once()
        self.messages.show_info.assert_not_called()


class ProjectPreviewRemovalTest(Case):
    def dialog(self):
        from Kavitro_dev.modules.projects import project_preview_dialog as preview_module
        dialog = preview_module.ProjectPreviewDialog.__new__(preview_module.ProjectPreviewDialog)
        dialog._item_id = "5"
        self.api = self.start(preview_module, "APIModuleActions")
        self.api.resolve_property_ids_by_cadastral.return_value = ([], [])
        return dialog

    def test_a_confirmed_removal_returns_the_links_left(self) -> None:
        dialog = self.dialog()
        self.api.get_linked_properties.return_value = [P2]
        ok, refreshed, _resp = dialog._persist_property_links([], ("p1",))
        self.assertTrue(ok)
        self.assertEqual(refreshed, ["2:2"])
        self.api.update_property_links.assert_called_once_with("project", "5", associate_ids=[], dissociate_ids=["p1"])

    def test_a_link_kavitro_kept_raises(self) -> None:
        dialog = self.dialog()
        self.api.get_linked_properties.return_value = [P1, P2]
        with self.assertRaises(RuntimeError):
            dialog._persist_property_links([], ("p1",))


if __name__ == "__main__":
    unittest.main()
