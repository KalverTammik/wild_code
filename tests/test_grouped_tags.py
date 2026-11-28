"""Grouped tags (prototype): reading them, arranging them, choosing them."""
from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from qgis.core import QgsApplication
from qgis.PyQt.QtCore import QCoreApplication, QEvent, Qt
from qgis.PyQt.QtWidgets import QFrame, QLabel

from Kavitro_dev.languages.language_manager import LanguageManager
from Kavitro_dev.languages.translation_keys import TranslationKeys
from Kavitro_dev.python.actions import tag_actions
from Kavitro_dev.python.api_actions import APIModuleActions
from Kavitro_dev.python.responses import DataDisplayExtractors
from Kavitro_dev.python.tag_catalog import TagCatalog
from Kavitro_dev.ui.theme_manager import ThemeManager
from Kavitro_dev.widgets.Filters.TagsFilterWidget import TagsFilterWidget
from Kavitro_dev.widgets.Tags.grouped_tag_picker import GroupedTagPicker
from Kavitro_dev.widgets.Tags.record_tags import RecordTagsView
from Kavitro_dev.widgets.Tags.tag_catalog_store import TagCatalogStore
from Kavitro_dev.widgets.Tags.tag_chips import TagChipsView
from Kavitro_dev.widgets.Tags.tag_prototype_panel import TagPrototypePanel

_APP = QgsApplication.instance() or QgsApplication([], False)


def node(tag_id: str, name: str, group: tuple[str, str] | None = None) -> dict:
    return {"id": tag_id, "name": name, "group": {"id": group[0], "name": group[1]} if group else None}


ROADS, MONEY = ("g2", "Teed"), ("g1", "Raha")
NODES = [
    node("1", "kruus", ROADS), node("2", "Asfalt", ROADS), node("3", " liitumine "), node("4", "Kulu", MONEY),
    node("5", "Asd"), node("1", "kruus", ROADS), node("", "nimeta"), node("6", "  "),
]


def delete_later(test: unittest.TestCase, widget) -> None:
    def delete() -> None:
        widget.hide()
        widget.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)

    test.addCleanup(delete)


class TagCatalogTest(unittest.TestCase):
    def test_groups_and_tags_are_in_name_order_and_ungrouped_come_last(self) -> None:
        catalog = TagCatalog.from_nodes(NODES)

        self.assertEqual([(group.name, [tag.name for tag in tags]) for group, tags in catalog.groups],
                         [("Raha", ["Kulu"]), ("Teed", ["Asfalt", "kruus"])])
        self.assertEqual([tag.name for tag in catalog.ungrouped], ["Asd", "liitumine"])
        self.assertEqual(len(catalog), 5)


class TagReadTest(unittest.TestCase):
    def read(self, *pages):
        with patch.object(tag_actions, "APIClient") as client, patch.object(tag_actions, "GraphQLQueryLoader"):
            client.return_value.send_query.side_effect = list(pages)
            return APIModuleActions.get_module_tag_catalog("project"), client.return_value.send_query

    @staticmethod
    def page(nodes, cursor=None) -> dict:
        return {"tags": {"pageInfo": {"hasNextPage": cursor is not None, "endCursor": cursor},
                         "edges": [{"node": item} for item in nodes]}}

    def test_every_page_is_read(self) -> None:
        catalog, send = self.read(self.page(NODES[:2], "a"), self.page(NODES[2:5]))

        self.assertEqual(len(catalog), 5)
        self.assertEqual([call.kwargs["variables"]["after"] for call in send.call_args_list], [None, "a"])
        self.assertEqual(send.call_args.kwargs["variables"]["where"]["value"], "PROJECTS")

    def test_an_unfinished_read_raises(self) -> None:
        for pages in (({"tags": None},), (self.page(NODES[:1], ""),), (self.page(NODES[:1], "a"),) * 2):
            with self.subTest(pages=pages), self.assertRaises(RuntimeError):
                self.read(*pages)


class GroupedTagPickerTest(unittest.TestCase):
    def setUp(self) -> None:
        self.picker = GroupedTagPicker()
        delete_later(self, self.picker)
        self.picker.set_catalog(TagCatalog.from_nodes(NODES))
        self.picker._toggle_popup()
        self.popup = self.picker._popup
        self.addCleanup(self.picker.close_popup)
        self.money, self.roads, self.other = self.popup._top_items()
        self.emitted: list[list[str]] = []
        self.picker.selectionChanged.connect(self.emitted.append)

    def test_a_row_ticks_one_tag_and_its_group_shows_a_part(self) -> None:
        self.popup.toggle(self.roads.child(0))

        self.assertEqual(self.emitted, [["2"]])
        self.assertEqual(self.roads.checkState(0), Qt.CheckState.PartiallyChecked)

    def test_the_group_box_ticks_and_clears_its_tags(self) -> None:
        self.popup.toggle(self.roads)
        self.assertEqual(self.picker.selected_ids(), ["2", "1"])

        self.popup.toggle(self.roads)
        self.assertEqual(self.picker.selected_ids(), [])

    def test_the_ungrouped_header_ticks_nothing(self) -> None:
        self.assertIsNone(self.other.data(0, Qt.ItemDataRole.CheckStateRole))
        self.popup.toggle(self.other)

        self.assertEqual(self.emitted, [])

    def test_search_hides_the_rest_and_the_group_box_acts_on_what_is_shown(self) -> None:
        self.popup.search.setText("asf")
        self.assertTrue(self.money.isHidden())
        self.assertTrue(self.other.isHidden())

        self.popup.toggle(self.roads)

        self.assertEqual(self.picker.selected_ids(), ["2"])

    def test_a_group_name_shows_its_whole_group(self) -> None:
        self.popup.search.setText("teed")

        self.assertEqual([self.roads.child(i).isHidden() for i in range(2)], [False, False])

    def test_an_id_the_list_does_not_hold_is_kept(self) -> None:
        self.picker.set_selected_ids(["99", "5"])
        self.picker.clear_selection()
        self.picker.set_catalog(TagCatalog.from_nodes(NODES + [node("99", "Uus")]))

        self.assertEqual(self.picker.selected_ids(), ["99"])


class PanelTest(unittest.TestCase):
    def test_the_panel_shows_a_failed_read(self) -> None:
        panel = TagPrototypePanel()
        delete_later(self, panel)

        panel._on_failed("[WC-API][network] Offline")

        self.assertIn("Offline", panel.status_label.text())
        self.assertNotIn("WC-API", panel.status_label.text())


def capsules(view) -> list[tuple[str, list[str]]]:
    """(group name, tag names) of the capsules in the order they are shown."""
    result = []
    for index in range(view._flow.count()):
        box = view._flow.itemAt(index).widget()
        if box.objectName() != "TagCapsule":
            continue
        name = box.findChild(QLabel, "TagCapsuleName")
        result.append((name.text() if name else "", [label.text() for label in box.findChildren(QLabel, "TagName")]))
    return result


class TagsFilterTest(unittest.TestCase):
    def setUp(self) -> None:
        self.settings = Mock()
        self.settings.load_module_preference_ids.return_value = ["2"]
        self.widget = TagsFilterWidget("project", auto_load=False, settings_logic=self.settings)
        delete_later(self, self.widget)
        TagCatalogStore.shared()._catalogs.clear()
        self.addCleanup(TagCatalogStore.shared()._catalogs.clear)
        self.finished: list[bool] = []
        self.widget.loadFinished.connect(self.finished.append)

    def load(self, request_id=None) -> None:
        current = self.widget._load_request_id
        self.widget._handle_load_success(
            TagCatalog.from_nodes(NODES), None, current if request_id is None else request_id)

    def test_saved_preferences_are_selected_and_the_catalog_is_shared(self) -> None:
        self.load()

        self.assertEqual(self.widget.selected_ids(), ["2"])
        self.assertEqual(self.widget.selected_texts(), ["Asfalt"])
        self.assertEqual(len(TagCatalogStore.shared().get("project")), 5)
        self.assertEqual(self.finished, [True])

    def test_a_choice_made_while_loading_wins_also_when_it_is_empty(self) -> None:
        for choice in ([], ["5"]):
            with self.subTest(choice=choice):
                self.widget.clear_data()
                self.widget.set_selected_ids(choice, emit=False)
                self.load()

                self.assertEqual(self.widget.selected_ids(), choice)

    def test_an_old_answer_is_ignored(self) -> None:
        self.load(request_id=self.widget._load_request_id - 1)

        self.assertFalse(self.widget.is_loaded())
        self.assertEqual(self.finished, [])

    def test_ticking_reports_names_and_ids(self) -> None:
        self.load()
        chosen: list = []
        self.widget.selectionChanged.connect(lambda names, ids: chosen.append((names, ids)))

        self.widget.picker.set_checked(["5"], True)

        self.assertEqual(chosen, [(["Asfalt", "Asd"], ["2", "5"])])


class CapsuleTest(unittest.TestCase):
    def test_each_group_and_the_ungrouped_have_their_own_capsule(self) -> None:
        view = TagChipsView()
        delete_later(self, view)

        view.show_tags(TagCatalog.from_nodes(NODES), ["1", "4", "5"])

        self.assertEqual(capsules(view), [("Raha", ["Kulu"]), ("Teed", ["kruus"]),
                                          (LanguageManager().translate(TranslationKeys.TAG_PICKER_UNGROUPED), ["Asd"])])

    def test_many_tags_wrap_inside_the_card(self) -> None:
        nodes = [node(str(i), f"pikk tunnuse nimi {i}") for i in range(1, 11)] + [node("20", "Kulu", MONEY)]
        view = TagChipsView()
        delete_later(self, view)
        view.show_tags(TagCatalog.from_nodes(nodes), [str(i) for i in range(1, 11)])
        view.resize(420, view.layout().heightForWidth(420))  # room for the name and one tag in the test font
        view.show()
        QCoreApplication.processEvents()

        box = view.findChild(QFrame, "TagCapsule")
        self.assertLessEqual(box.width(), 420)
        labels = box.findChildren(QLabel, "TagName")
        self.assertGreater(len({label.y() for label in labels}), 1)

    def test_the_tags_carry_their_own_style_and_follow_the_theme(self) -> None:
        with patch.object(ThemeManager, "effective_theme", return_value="light"):
            view = TagChipsView()
        delete_later(self, view)
        light = view.styleSheet()
        self.assertIn("QFrame#TagCapsule", light)
        self.assertIn("padding: 1px 2px; border-right", light)

        with patch.object(ThemeManager, "effective_theme", return_value="dark"):
            view.retheme()

        self.assertNotEqual(view.styleSheet(), light)

    def test_the_prototype_settings_change_the_sample_record(self) -> None:
        panel = TagPrototypePanel()
        delete_later(self, panel)
        panel._requested_module = "project"
        panel._on_loaded(TagCatalog.from_nodes(NODES))

        panel.look_spins["tag_pad"].setValue(9)

        self.assertIn("padding: 1px 9px", panel.record_chips.styleSheet())
        self.assertEqual(len(panel.record_picker.selected_ids()), 5)


class RecordTagsTest(unittest.TestCase):
    ITEM = {"tags": {"edges": [{"node": {"id": "2", "name": "Asfalt "}}, {"node": {"id": "5", "name": "Asd"}}]}}

    def test_a_card_groups_its_tags_once_the_catalog_arrives(self) -> None:
        store = TagCatalogStore.shared()
        store._catalogs.clear()
        self.addCleanup(store._catalogs.clear)
        view = RecordTagsView("project", DataDisplayExtractors.extract_tags(self.ITEM))
        delete_later(self, view)
        self.assertEqual(capsules(view), [("", ["Asfalt", "Asd"])])

        store.put("project", TagCatalog.from_nodes(NODES))
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)

        self.assertEqual([names for _name, names in capsules(view)], [["Asfalt"], ["Asd"]])


if __name__ == "__main__":
    unittest.main()
