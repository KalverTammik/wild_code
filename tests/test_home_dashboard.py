"""The home page and the toolbar indicators: which numbers are asked for, how the answers are read,
the cards in every state, the due filters behind the clickable numbers and the user's choice of design."""
from __future__ import annotations

import os
import sys
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import Mock, patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from qgis.core import QgsApplication
from qgis.PyQt.QtCore import QCoreApplication, QEvent, QPoint, QRect, Qt
from qgis.PyQt.QtTest import QTest

from Kavitro_dev.ui.mixins.filtered_feed_mixin import FilteredFeedMixin
from Kavitro_dev.utils.FilterHelpers.due_filters import due_soon_conditions, overdue_conditions
from Kavitro_dev.languages.language_manager import LanguageManager
from Kavitro_dev.utils.settings_service import SettingsService
from Kavitro_dev.widgets.home import dashboard_counts as counts
from Kavitro_dev.widgets.home.dashboard import HomeDashboard
from Kavitro_dev.widgets.home.dashboard_cards import FAILED_MARK, LOADING_MARK, TOOLBAR
from Kavitro_dev.widgets.home.indicator_styles import DEFAULT_DESIGN, DEFAULT_PALETTE, DESIGNS, PALETTES
from Kavitro_dev.widgets.home.module_indicator import ModuleIndicator, chosen_style

_APP = QgsApplication.instance() or QgsApplication([], False)

TODAY = date(2026, 1, 15)
STATUS = {"column": "STATUS", "operator": "IN", "value": ["1"]}


def delete_later(test: unittest.TestCase, widget) -> None:
    def delete() -> None:
        widget.hide()
        widget.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)

    test.addCleanup(delete)


class ConditionsTest(unittest.TestCase):
    def test_overdue_is_asked_with_the_servers_own_column(self) -> None:
        self.assertEqual(overdue_conditions(), [{"column": "IS_OVERDUE", "operator": "EQ", "value": True}])
        self.assertEqual([part["value"] for part in due_soon_conditions(TODAY)], ["2026-01-15", "2026-01-18"])

    def test_every_condition_keeps_the_selection(self) -> None:
        for key in counts.SOURCES:
            wheres = counts.conditions_by_alias(key, (STATUS,), TODAY)
            with self.subTest(module=key):
                self.assertTrue(all(STATUS in where["AND"] for where in wheres.values()))
        self.assertIsNone(counts.conditions_by_alias(counts.PROJECT, (), TODAY)["total"])

    def test_the_contract_weeks_follow_each_other_without_gaps(self) -> None:
        wheres = counts.conditions_by_alias(counts.CONTRACT, (), TODAY)
        spans = [tuple(part["value"] for part in wheres[f"week{i}"]["AND"]) for i in range(counts.WEEKS_AHEAD)]

        self.assertEqual(spans[:2], [("2026-01-15", "2026-01-21"), ("2026-01-22", "2026-01-28")])
        self.assertEqual(spans[-1], ("2026-02-12", "2026-02-18"))

    def test_the_works_months_end_with_the_current_one(self) -> None:
        wheres = counts.conditions_by_alias(counts.WORKS, (), TODAY)
        spans = [tuple(part["value"] for part in wheres[f"month{i}"]["AND"]) for i in range(counts.MONTHS_BACK)]

        self.assertEqual(spans[0], ("2025-02-01", "2025-03-01"))
        self.assertEqual(spans[-2:], [("2025-12-01", "2026-01-01"), ("2026-01-01", "2026-02-01")])

    def test_the_query_names_each_modules_types_and_tags_only_the_asked_aliases(self) -> None:
        projects = counts.build_query(counts.PROJECT, ["total", "late", "all_total"], {"total", "late"})
        works = counts.build_query(counts.WORKS, ["total"], set())

        self.assertIn("$where_late: QueryProjectsWhereWhereConditions", projects)
        self.assertIn("$whereHas: [ProjectsWhereHasInput!]", projects)
        self.assertIn("late: projects(first: 1, where: $where_late, trashed: WITHOUT, whereHas: $whereHas)", projects)
        self.assertIn("all_total: projects(first: 1, where: $where_all_total, trashed: WITHOUT) {", projects)
        self.assertIn("total: tasks(first: 1, where: $where_total) { pageInfo { total } }", works)
        self.assertNotIn("whereHas", works)


class FetchTest(unittest.TestCase):
    def fetch(self, key: str, answer):
        with patch.object(counts, "APIClient") as client, \
                patch.object(counts, "saved_selection", return_value=counts.Selection((STATUS,))):
            client.return_value.send_query.side_effect = answer
            return counts.fetch_counts(key, TODAY), client.return_value.send_query

    @staticmethod
    def numbered(_query, variables):
        aliases = [name.removeprefix("where_") for name in variables]
        return {alias: {"pageInfo": {"total": index}} for index, alias in enumerate(aliases)}

    def test_one_request_gives_all_the_numbers_of_a_module(self) -> None:
        result, send = self.fetch(counts.CONTRACT, self.numbered)

        self.assertEqual(send.call_count, 1)
        self.assertEqual((result.total, result.late, result.soon), (0, 1, 2))
        self.assertEqual(result.weeks, (3, 4, 5, 6, 7))
        self.assertEqual(result.months, ())

    def test_a_missing_number_is_an_error_not_a_zero(self) -> None:
        with self.assertRaises(RuntimeError):
            self.fetch(counts.EASEMENT, lambda _query, _variables: {"total": {"pageInfo": {"total": 3}}})

    def overview(self, shown, whole):
        def answer(query, _variables):
            aliases = [line.split(":")[0].strip() for line in query.splitlines()[1:-1]]
            return {alias: {"pageInfo": {"total": 20 if alias.startswith("all_") else 2}} for alias in aliases}

        with patch.object(counts, "APIClient") as client:
            client.return_value.send_query.side_effect = answer
            result = counts.fetch_overview(counts.PROJECT, shown, whole, TODAY)
        self.assertEqual(client.return_value.send_query.call_count, 1)
        return result, client.return_value.send_query.call_args.args

    def test_the_filtered_and_the_whole_data_come_in_one_request(self) -> None:
        tags = [{"column": "ID"}]
        result, (query, variables) = self.overview(counts.Selection((STATUS,), tags), counts.Selection())

        self.assertEqual((result.shown.total, result.whole.total), (2, 20))
        self.assertEqual(variables["whereHas"], tags)
        # The whole data takes neither the filters nor the tags.
        self.assertNotIn("where_all_total", variables)
        late = next(line for line in query.splitlines() if line.strip().startswith("all_late"))
        self.assertNotIn("whereHas", late)
        self.assertEqual(variables["where_all_late"], {"AND": overdue_conditions()})

    def test_without_filters_nothing_is_asked_twice(self) -> None:
        result, (query, _variables) = self.overview(counts.Selection(), counts.Selection())

        self.assertNotIn("all_", query)
        self.assertIs(result.whole, result.shown)


class MemorySettings:
    """Stands in for QgsSettings: nothing of the user's is read or written."""

    def __init__(self, **values) -> None:
        self.values = dict(values)

    def value(self, key, default=None):
        return self.values.get(key, default)

    def setValue(self, key, value) -> None:  # noqa: N802 - QgsSettings
        self.values[key] = value

    def remove(self, key) -> None:
        self.values.pop(key, None)


class PaintedCase(unittest.TestCase):
    def setUp(self) -> None:
        self.failures: list[str] = []
        patcher = patch.object(sys, "excepthook", lambda kind, value, _tb: self.failures.append(f"{kind.__name__}: {value}"))
        patcher.start()
        self.addCleanup(patcher.stop)


class DashboardTest(PaintedCase):
    def setUp(self) -> None:
        super().setUp()
        self.page = HomeDashboard()
        delete_later(self, self.page)
        self.page.show()

    def paint(self) -> None:
        QCoreApplication.processEvents()
        for dark in (False, True):
            for card in self.page.cards:
                card.dark = dark
                card.grab()
        self.assertEqual(self.failures, [])

    def test_the_cards_paint_while_loading_loaded_empty_and_failed(self) -> None:
        self.assertEqual(self.page._data.mark(counts.WORKS), LOADING_MARK)
        self.paint()
        for item in (counts.ModuleCounts(0, 0, 0, (0,) * 5, (0,) * 12),
                     counts.ModuleCounts(15230, 900, 400, (31, 22, 12, 9, 4), tuple(range(12)))):
            for key in counts.SOURCES:
                self.page._on_counts(key, item)
            self.paint()

        self.page._on_failed(counts.COORDINATION, "[WC-API][network] Offline")
        self.paint()

        self.assertEqual(self.page._data.mark(counts.COORDINATION), FAILED_MARK)
        self.assertIsNone(self.page._data.get(counts.COORDINATION))
        tips = {card.toolTip() for card in self.page.cards if counts.COORDINATION in card.spec.modules}
        self.assertTrue(all("Offline" in tip and "WC-API" not in tip for tip in tips))

    def test_a_refresh_asks_every_module_again_and_forgets_the_errors(self) -> None:
        self.page._on_failed(counts.WORKS, "Offline")
        with patch.object(type(self.page._requests[counts.WORKS]), "submit") as submit:
            self.page.refresh()

        self.assertEqual([call.args[1] for call in submit.call_args_list], list(counts.SOURCES))
        self.assertEqual(self.page._data.failed, set())
        self.assertEqual({card.toolTip() for card in self.page.cards}, {""})


class ModuleIndicatorTest(PaintedCase):
    ITEM = counts.ModuleCounts(9, 2, 0, (1, 0, 2, 0, 3), tuple(range(12)))
    WHOLE = counts.ModuleCounts(40, 16, 3)

    def setUp(self) -> None:
        super().setUp()
        self.settings = MemorySettings()
        patcher = patch("Kavitro_dev.utils.settings_service.QgsSettings", return_value=self.settings)
        patcher.start()
        self.addCleanup(patcher.stop)

    def build(self, key: str) -> ModuleIndicator:
        indicator = ModuleIndicator(key)
        delete_later(self, indicator)
        return indicator

    def test_every_module_with_deadlines_has_one_that_paints_in_every_state(self) -> None:
        for key in counts.SOURCES:
            indicator = self.build(key)
            indicator.resize(indicator.sizeHint())
            indicator.grab()
            indicator._on_overview(counts.Overview(self.ITEM, self.WHOLE))
            indicator.set_active((True, True))
            indicator.grab()
            indicator._on_failed("Offline")
            indicator.grab()
            indicator.resize(40, 69)
            indicator.grab()
            self.assertEqual(indicator.graphic is not None, key in TOOLBAR, key)
        self.assertEqual(self.failures, [])

    def test_new_filters_are_counted_and_clear_the_active_number(self) -> None:
        indicator = self.build(counts.CONTRACT)
        indicator.set_active((False, True))
        shown, whole = counts.Selection((STATUS,)), counts.Selection()
        with patch.object(indicator._request, "submit") as submit:
            indicator.show_selection(shown, whole)

        self.assertEqual(submit.call_args.args, (counts.fetch_overview, counts.CONTRACT, shown, whole))
        self.assertIsNone(indicator.active())

    def test_every_design_marks_exactly_the_numbers_above_zero(self) -> None:
        indicator = self.build(counts.PROJECT)
        indicator._on_overview(counts.Overview(self.ITEM, self.WHOLE))
        indicator.show()
        clicked: list = []
        indicator.dueClicked.connect(lambda whole, overdue: clicked.append((whole, overdue)))
        card = indicator.summary
        # The selection has nothing due soon; every other number is above zero.
        expected = {(False, True), (True, True), (True, False)}

        for key in DESIGNS:
            indicator.design_actions[key].trigger()
            card.grab()
            with self.subTest(design=key):
                self.assertEqual(card.height(), DESIGNS[key].height)
                self.assertEqual(set(card.data.cells), expected)
                clicked.clear()
                for cell, rect in card.data.cells.items():
                    self.assertTrue(QRect(0, 0, card.width(), card.height()).contains(rect.toAlignedRect()), cell)
                    center = rect.center()
                    QTest.mouseClick(card, Qt.MouseButton.LeftButton, pos=QPoint(int(center.x()), int(center.y())))
                self.assertEqual(set(clicked), expected)
        self.assertEqual(self.failures, [])

    def test_the_shown_number_stays_clickable_at_zero(self) -> None:
        indicator = self.build(counts.PROJECT)
        indicator._on_overview(counts.Overview(self.ITEM, self.WHOLE))
        indicator.set_active((False, False))
        for key in DESIGNS:
            indicator.summary.set_design(key)
            indicator.summary.grab()
            with self.subTest(design=key):
                self.assertIn((False, False), indicator.summary.data.cells)

    def test_every_design_paints_empty_and_large_numbers_in_every_colour_set(self) -> None:
        indicator = self.build(counts.CONTRACT)
        for item in (counts.ModuleCounts(0, 0, 0, (0,) * 5), counts.ModuleCounts(15230, 2900, 412, (9,) * 5)):
            indicator._on_overview(counts.Overview(item, item))
            for design in DESIGNS:
                for palette in PALETTES:
                    indicator.design_actions[design].trigger()
                    indicator.palette_actions[palette].trigger()
                    indicator.summary.grab()
                    indicator.graphic.grab()
        self.assertEqual(self.failures, [])

    def test_the_choice_is_saved_and_serves_the_other_modules(self) -> None:
        first, second = self.build(counts.COORDINATION), self.build(counts.PROJECT)
        self.assertEqual(chosen_style(), (DEFAULT_DESIGN, DEFAULT_PALETTE))

        first.design_actions["bands"].trigger()
        first.palette_actions["pastel"].trigger()
        second.show()

        self.assertEqual((SettingsService().indicator_design(), SettingsService().indicator_palette()),
                         ("bands", "pastel"))
        self.assertEqual(second.summary.data.design, "bands")
        self.assertTrue(second.palette_actions["pastel"].isChecked())
        pastel = PALETTES["pastel"]
        self.assertEqual(first.graphic.colors, (pastel.late, pastel.soon, pastel.fine, pastel.total))

    def test_an_unknown_saved_choice_gives_the_defaults(self) -> None:
        SettingsService().indicator_design("removed-design")
        SettingsService().indicator_palette("removed-palette")

        self.assertEqual(chosen_style(), (DEFAULT_DESIGN, DEFAULT_PALETTE))

    def test_every_choice_has_a_name_in_both_languages(self) -> None:
        keys = [choice.name_key for choice in (*DESIGNS.values(), *PALETTES.values())]
        for language in ("en", "et"):
            translate = LanguageManager(language=language).translate
            with self.subTest(language=language):
                self.assertEqual([key for key in keys if translate(key) == key], [])

    def test_a_narrow_toolbar_keeps_the_numbers(self) -> None:
        indicator = self.build(counts.COORDINATION)

        self.assertEqual(indicator.graphic.minimumWidth(), 0)
        self.assertGreater(indicator.summary.minimumWidth(), 200)


class DueClickTest(unittest.TestCase):
    @staticmethod
    def module(active=None) -> Mock:
        module = Mock()
        module.module_indicator.active.return_value = active
        module.module_indicator.shown = counts.Selection((STATUS,), ["tag"])
        module.module_indicator.whole = counts.Selection()
        return module

    def test_a_click_lists_exactly_the_counted_records(self) -> None:
        for whole, conditions, where_has in ((False, [STATUS], ["tag"]), (True, [], None)):
            module = self.module()
            FilteredFeedMixin._on_due_clicked(module, whole, True)
            with self.subTest(whole=whole):
                module.feed_logic.set_where.assert_called_once_with({"AND": [*conditions, *overdue_conditions()]})
                module.feed_logic.set_extra_arguments.assert_called_once_with(whereHas=where_has)
                module.module_indicator.set_active.assert_called_once_with((whole, True))
                module.feed_load_engine.schedule_load.assert_called_once_with()

    def test_the_same_number_again_returns_to_the_filters(self) -> None:
        module = self.module(active=(True, False))

        FilteredFeedMixin._on_due_clicked(module, True, False)

        module._refresh_filters.assert_called_once_with()
        module.feed_logic.set_where.assert_not_called()


if __name__ == "__main__":
    unittest.main()
