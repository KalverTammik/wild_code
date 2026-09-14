from __future__ import annotations

import os
import sys
import unittest
import threading
from datetime import date
from pathlib import Path
from unittest.mock import Mock, patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
if os.environ.get("QGIS_PREFIX_PATH"):
    sys.path.append(str(Path(os.environ["QGIS_PREFIX_PATH"]) / "python" / "plugins"))

from PyQt5.QtCore import QCoreApplication, QEvent, QTimer, QThread
from PyQt5.QtGui import QFont, QFontDatabase
from PyQt5.QtTest import QTest
from PyQt5.QtWidgets import QApplication, QFrame, QLabel, QVBoxLayout
from Kavitro_dev.languages.language_manager import LanguageManager
from Kavitro_dev.modules.works.works_list_service import (
    ListChoices, WorksFeedLogic, WorksListPreferences, group_loaded_items, sort_loaded_items,
)
from Kavitro_dev.modules.works.WorksUi import WorksModule
from Kavitro_dev.ui.module_card_factory import ModuleCardFactory
from Kavitro_dev.widgets.DataDisplayWidgets.StatusWidget import StatusWidget
from Kavitro_dev.widgets.DataDisplayWidgets.ExtraInfoWidget import ExtraInfoFrame


def task(key, *, names=(), status="Töös", priority="MEDIUM", due=None):
    return {"id": str(key), "name": f"Töö {key}", "dueAt": due,
            "priority": priority, "status": {"id": status, "name": status, "type": "OPEN"},
            "type": {"id": "repair", "name": "Remont"},
            "members": {"edges": [{"responsible": True, "node": {"id": name, "displayName": name}}
                                    for name in names]}}


def page(items, cursor="last", more=False):
    return {"data": {"tasks": {"edges": [{"node": item} for item in items],
                                "pageInfo": {"endCursor": cursor, "hasNextPage": more, "total": 20}}}}


class WorksListRulesTest(unittest.TestCase):
    def setUp(self):
        self.lang = LanguageManager("et")

    def test_priority_direction_and_missing_always_last(self):
        items = [task(1, priority=""), task(2, priority="LOW"), task(3, priority="URGENT"), task(4)]
        self.assertEqual([i['id'] for i in sort_loaded_items(items, ListChoices('priority'))], ['3', '4', '2', '1'])
        self.assertEqual([i['id'] for i in sort_loaded_items(items, ListChoices('priority', True))], ['2', '4', '3', '1'])

    def test_equal_sort_values_have_stable_natural_id_order(self):
        items = [task('10'), task('2'), task('1')]
        self.assertEqual([i['id'] for i in sort_loaded_items(items, ListChoices('status', True))], ['1', '2', '10'])

    def test_remote_sort_preserves_server_order(self):
        items = [task('10'), task('2')]
        self.assertEqual(sort_loaded_items(items, ListChoices('title')), items)

    def test_responsible_groups_repeat_item_but_not_duplicate_memberships(self):
        items = [task(1, names=['Mari', 'Kalver', 'Kalver']), task(2)]
        groups = group_loaded_items(items, ListChoices(group='responsible'), self.lang)
        self.assertEqual([g.label for g in groups], ['Kalver', 'Mari', 'Vastutaja määramata'])
        self.assertEqual([len(g.items) for g in groups], [1, 1, 1])
        self.assertEqual(len({i['id'] for g in groups for i in g.items}), 2)

    def test_group_members_keep_selected_priority_order(self):
        items = [task(1, priority='LOW'), task(2, priority='URGENT')]
        groups = group_loaded_items(items, ListChoices('priority', group='type'), self.lang)
        self.assertEqual([i['id'] for i in groups[0].items], ['2', '1'])

    def test_deadline_buckets_are_disjoint_at_sunday_boundary(self):
        items = [task(1, due='2026-09-12'), task(2, due='2026-09-13'),
                 task(3, due='2026-09-14'), task(4, due='2026-09-20'),
                 task(5, due='2026-09-21'), task(6), task(7, due='not-a-date')]
        closed = task(8, due='2020-01-01')
        closed['status']['type'] = 'CLOSED'
        groups = group_loaded_items(items + [closed], ListChoices(group='deadline'), self.lang, today=date(2026, 9, 13))
        by_label = {g.label: [i['id'] for i in g.items] for g in groups}
        self.assertEqual(by_label, {'Üle tähtaja':['1'], 'Täna':['2'], 'Homme':['3'],
                                   'Järgmisel nädalal':['4'], 'Hiljem':['5'], 'Lõpetatud':['8'], 'Tähtajata':['6', '7']})

    def test_preferences_are_scoped_by_user_environment_and_module(self):
        data = {}
        settings = Mock()
        settings.value.side_effect = lambda key, default: data.get(key, default)
        settings.setValue.side_effect = data.__setitem__
        prefs = WorksListPreferences(settings, user_id='u1', endpoint='test')
        choice = ListChoices('responsible', True, 'deadline')
        prefs.save(choice)
        self.assertEqual(prefs.load(), choice)
        for kwargs in ({'user_id':'u2', 'endpoint':'test'}, {'user_id':'u1', 'endpoint':'live'},
                       {'user_id':'u1', 'endpoint':'test', 'module_key':'asbuilt'}):
            self.assertEqual(WorksListPreferences(settings, **kwargs).load(), ListChoices())
        data[prefs.key] = '{invalid'
        self.assertEqual(prefs.load(), ListChoices())


class WorksSortedFeedTest(unittest.TestCase):
    def setUp(self):
        self.client_patch = patch('Kavitro_dev.feed.FeedLogic.APIClient')
        self.client = self.client_patch.start().return_value
        self.addCleanup(self.client_patch.stop)
        self.feed = WorksFeedLogic('task', 'ListFilteredTasks.graphql', root_field='tasks')

    def test_sort_and_scope_survive_pagination_and_null_pass(self):
        self.feed.choices = ListChoices('due')
        scope = {'AND':[{'column':'TYPE', 'operator':'IN', 'value':['repair']}]}
        self.feed.set_where(scope)
        self.client.send_query.side_effect = [page([task(1)], 'p1', True), page([task(2)]), page([task(3)])]
        self.assertEqual(self.feed.fetch_next_batch()[0]['id'], '1')
        self.assertEqual(self.feed.fetch_next_batch()[0]['id'], '2')
        self.assertTrue(self.feed.has_more)
        self.assertIsNone(self.feed.total_count)
        self.assertEqual(self.feed.fetch_next_batch()[0]['id'], '3')
        calls = [call.args[1] for call in self.client.send_query.call_args_list]
        self.assertEqual([v['after'] for v in calls], [None, 'p1', None])
        self.assertEqual(calls[0]['orderBy'], [{'column':'DUE_AT','order':'ASC'}, {'column':'ID','order':'ASC'}])
        self.assertEqual(calls[-1]['where'], {'AND':[scope, {'column':'DUE_AT', 'operator':'IS_NULL'}]})
        self.assertEqual(self.feed.where, scope)
        self.assertEqual(self.feed._extra_args, {})
        self.assertFalse(self.feed.has_more)
        self.assertEqual(self.feed.total_count, 3)

    def test_empty_dated_pass_continues_to_undated_items(self):
        self.feed.choices = ListChoices('start', True)
        self.client.send_query.side_effect = [page([]), page([task(1)])]
        self.assertEqual(len(self.feed.fetch_next_batch()), 1)
        self.assertEqual(self.client.send_query.call_count, 2)

    def test_failed_page_keeps_cursor_and_can_be_retried(self):
        self.feed.choices = ListChoices('due')
        self.client.send_query.side_effect = [page([task(1)], 'p1', True), RuntimeError('offline'), page([task(2)])]
        self.feed.fetch_next_batch()
        self.assertEqual(self.feed.fetch_next_batch(), [])
        self.assertIsNotNone(self.feed.last_error)
        self.assertEqual(self.feed.end_cursor, 'p1')
        self.assertEqual(self.feed.fetch_next_batch()[0]['id'], '2')
        self.assertEqual(self.client.send_query.call_args.args[1]['after'], 'p1')

    def test_reset_restarts_sort_from_first_non_null_page(self):
        self.feed.choices = ListChoices('updated', True)
        self.client.send_query.return_value = page([task(1)])
        self.feed.fetch_next_batch()
        self.feed.reset_pagination()
        self.feed.fetch_next_batch()
        variables = self.client.send_query.call_args.args[1]
        self.assertIsNone(variables['after'])
        self.assertEqual(variables['where']['AND'][-1]['operator'], 'IS_NOT_NULL')
        self.assertEqual(variables['orderBy'][0], {'column':'UPDATED_AT','order':'DESC'})

    def test_single_item_query_does_not_receive_list_sort_or_null_filters(self):
        self.feed.choices = ListChoices('due')
        self.feed.configure_single_item_query('w_tasks_module_data_by_item_id.graphql')
        self.feed.set_single_item_mode(True, id='7')
        self.client.send_query.return_value = {'data':{'task':task(7)}}
        self.assertEqual(self.feed.fetch_next_batch()[0]['id'], '7')
        self.assertEqual(self.client.send_query.call_args.args[1], {'id':'7'})


class WorksListWidgetTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])
        if not QFontDatabase().families():
            for name in ('segoeui.ttf', 'segoeuib.ttf'):
                QFontDatabase.addApplicationFont('C:/Windows/Fonts/' + name)
            cls.app.setFont(QFont('Segoe UI', 9))

    def setUp(self):
        self.patches = [
            patch('Kavitro_dev.modules.works.WorksUi.WorksCreateController'),
            patch('Kavitro_dev.modules.works.WorksUi.WorksSyncService'),
            patch('Kavitro_dev.modules.task_shared.task_module_base_ui.ModuleManager'),
            patch('requests.sessions.Session.request', side_effect=AssertionError('Unexpected network request')),
            patch.object(ModuleCardFactory, 'create_item_card', side_effect=self.make_card),
        ]
        mocks = [p.start() for p in self.patches]
        mocks[2].return_value.getModuleSupports.return_value = (False, False, False, False)
        self.factory = mocks[4]
        self.ui = WorksModule(lang_manager=LanguageManager('et'))
        self.ui.resize(700, 500)
        self.ui.show()
        self.app.processEvents()

    def tearDown(self):
        self.ui._activated = False
        self.ui._invalidate_feed_request()
        self.ui._list_view.clear()
        self.ui.close()
        self.ui.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)
        for p in reversed(self.patches):
            p.stop()

    @staticmethod
    def make_card(item, **kwargs):
        card = QFrame()
        card.setObjectName('ModuleInfoCard')
        layout = QVBoxLayout(card)
        layout.addWidget(QLabel(item['name']))
        card.setMinimumHeight(60)
        return card

    def add(self, *items):
        for item in items:
            self.ui._progressive_insert_card(item)
        self.wait_until(lambda: not self.ui._list_view._render_timer.isActive())
        self.app.processEvents()

    def test_responsible_groups_count_unique_items_and_reuse_existing_cards(self):
        self.ui._list_controls.group_actions['responsible'].trigger()
        self.add(task(1, names=['Mari', 'Kalver']), task(2))
        self.assertEqual(self.ui._compute_loaded_cards(), 2)
        self.assertEqual(len(self.ui._list_view.cards), 3)
        previous = dict(self.ui._list_view.cards)
        self.add(task(3, names=['Mari']))
        for key, card in previous.items():
            self.assertIs(self.ui._list_view.cards[key], card)
        self.assertEqual(len(self.ui._list_view.headers), 3)
        self.assertIn('laaditud', self.ui._list_scope_label.text())

    def test_collapse_persists_when_a_page_adds_items(self):
        self.ui._list_controls.group_actions['status'].trigger()
        self.add(task(1))
        header = next(iter(self.ui._list_view.headers.values()))
        header.click()
        self.add(task(2))
        self.assertTrue(self.ui._list_view.all_collapsed)
        self.assertTrue(self.ui._is_filled_plus_one())
        self.assertTrue(all(card.isHidden() for card in self.ui._list_view.cards.values()))
        self.ui._list_controls.expand_action.trigger()
        self.assertFalse(self.ui._list_view.all_collapsed)
        self.assertTrue(all(card.isVisible() for card in self.ui._list_view.cards.values()))

    def test_new_remote_sort_discards_old_buffer_and_resets_cursor(self):
        self.ui.init_feed_engine(self.ui.load_next_batch)
        self.ui.feed_load_engine.buffer.append(task('old'))
        self.ui.feed_logic.end_cursor = 'old-cursor'
        self.add(task(1))
        self.ui._list_controls.sort_actions[('due', False)].trigger()
        self.assertEqual(self.ui._compute_loaded_cards(), 0)
        self.assertFalse(self.ui.feed_load_engine.has_buffer())
        self.assertIsNone(self.ui.feed_logic.end_cursor)
        self.assertEqual(self.ui.feed_logic.choices.sort, 'due')

    def test_collapsed_groups_do_not_start_an_autofill_loop(self):
        self.ui._list_controls.group_actions['status'].trigger()
        self.add(task(1))
        self.ui._list_controls.collapse_action.trigger()
        self.ui.init_feed_engine(self.ui.load_next_batch)
        self.ui.feed_load_engine.buffer.append(task(2))
        self.ui._activated = True
        with patch('Kavitro_dev.ui.mixins.progressive_load_mixin.QTimer.singleShot') as timer:
            self.ui._initial_autofill_tick()
            timer.assert_not_called()
        self.ui._activated = False
        self.assertEqual(len(self.ui.feed_load_engine.buffer), 1)

    def test_local_sort_changes_reuse_loaded_items_and_show_scope(self):
        self.ui._list_controls.sort_actions[('priority', False)].trigger()
        self.add(task(1, priority='LOW'), task(2, priority='URGENT'))
        self.assertEqual([key[1] for key in self.ui._list_view.cards], ['2', '1'])
        self.ui._list_controls.sort_actions[('priority', True)].trigger()
        self.assertEqual([key[1] for key in self.ui._list_view.cards], ['1', '2'])
        self.assertEqual(self.ui._compute_loaded_cards(), 2)
        self.assertIn('laaditud kannetes', self.ui._list_scope_label.text())

    def test_filter_clear_removes_group_state_and_queued_cards(self):
        self.ui._list_controls.group_actions['type'].trigger()
        self.add(task(1))
        self.ui._progressive_insert_card(task('late'))
        self.ui.clear_feed(self.ui.feed_layout, self.ui.empty_state)
        QTest.qWait(20)
        self.assertEqual(self.ui._compute_loaded_cards(), 0)
        self.assertEqual(self.ui.feed_layout.count(), 2)
        self.assertEqual(self.ui._list_view.headers, {})

    def test_status_edit_moves_item_to_its_new_group(self):
        self.ui._list_controls.group_actions['status'].trigger()
        self.add(task(1), task(2))
        self.ui._on_list_item_updated(task(1, status='Valmis'))
        QTest.qWait(30)
        groups = self.ui._list_view.cards
        self.assertIn((('status', 'Valmis'), '1'), groups)
        self.assertNotIn((('status', 'Töös'), '1'), groups)
        self.assertIn((('status', 'Töös'), '2'), groups)
        self.assertEqual(self.ui._compute_loaded_cards(), 2)

    def test_real_card_status_edit_updates_every_occurrence_and_handles_stay_at_bottom(self):
        self.patches[-1].stop()
        self.ui._list_controls.group_actions['responsible'].trigger()
        self.add(task(1, names=['Kalver', 'Mari']))
        QTest.qWait(70)
        card = next(iter(self.ui._list_view.cards.values()))
        card.findChild(StatusWidget)._replace_current_card(task(1, names=['Kalver', 'Mari'], status='Valmis'))
        QTest.qWait(70)
        QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)
        self.add(task(2))
        QTest.qWait(50)
        for key, card in self.ui._list_view.cards.items():
            if key[1] == '1':
                self.assertEqual(card.findChild(StatusWidget)._item_data['status']['name'], 'Valmis')
            frame = card.findChild(ExtraInfoFrame)
            handle = frame._expand_handle
            self.assertEqual(handle.y(), card.height() - handle.height() - 1)
            self.assertGreater(handle.x(), 0)
        self.assertEqual(self.ui._compute_loaded_cards(), 2)

    def test_late_edit_cannot_restore_cleared_feed(self):
        self.add(task(1))
        self.ui.clear_feed(self.ui.feed_layout, self.ui.empty_state)
        self.ui._on_list_item_updated(task(1, status='Valmis'))
        QTest.qWait(20)
        self.assertEqual(self.ui._compute_loaded_cards(), 0)

    def prepare_loading(self):
        self.ui.init_feed_engine(self.ui.load_next_batch)
        self.ui._activated = True
        self.ui.feed_logic.api_client = Mock()
        return self.ui.feed_logic.api_client

    def wait_until(self, condition):
        for _ in range(150):
            if condition():
                return
            QTest.qWait(10)
        self.fail('Background result was not delivered')

    def test_terminal_empty_page_after_ungrouping_keeps_cards_without_empty_message(self):
        client = self.prepare_loading()
        self.ui._list_controls.group_actions['status'].trigger()
        self.add(task(1))
        self.ui._list_controls.group_actions['none'].trigger()
        client.send_query.return_value = page([])
        self.ui.load_next_batch()
        self.wait_until(lambda: not self.ui.feed_logic.is_loading)
        self.assertEqual(self.ui._compute_loaded_cards(), 1)
        self.assertTrue(self.ui.empty_state.isHidden())
        self.assertFalse(self.ui.feed_logic.has_more)

    def test_genuinely_empty_first_page_shows_translated_empty_state(self):
        client = self.prepare_loading()
        client.send_query.return_value = page([])
        self.ui.load_next_batch()
        self.wait_until(lambda: not self.ui.feed_logic.is_loading)
        self.assertFalse(self.ui.empty_state.isHidden())
        from Kavitro_dev.languages.translation_keys import TranslationKeys
        self.assertEqual(self.ui.empty_state.text(), self.ui.lang_manager.translate(TranslationKeys.NO_VALUES_FOUND))

    def test_empty_page_with_buffered_cards_does_not_show_empty_state(self):
        client = self.prepare_loading()
        self.ui.feed_load_engine.buffer.append(task(1))
        client.send_query.return_value = page([])
        self.ui.process_next_batch()
        self.assertTrue(self.ui.empty_state.isHidden())

    def test_real_request_error_stays_visible_when_grouping_changes(self):
        client = self.prepare_loading()
        self.add(task(1))
        client.send_query.side_effect = RuntimeError('Connection unavailable')
        self.ui.load_next_batch()
        self.wait_until(lambda: not self.ui.feed_logic.is_loading)
        self.ui._list_controls.group_actions['status'].trigger()
        self.assertFalse(self.ui.empty_state.isHidden())
        self.assertEqual(self.ui.empty_state.text(), 'Connection unavailable')
        self.assertEqual(self.ui._compute_loaded_cards(), 1)

    def test_slow_request_leaves_gui_responsive_and_does_not_poll_or_overlap(self):
        client = self.prepare_loading()
        gate, entered = threading.Event(), threading.Event()
        threads, pulses = [], []
        def fetch(*args, **kwargs):
            threads.append(QThread.currentThread())
            entered.set()
            gate.wait(3)
            return page([task(1)])
        client.send_query.side_effect = fetch
        try:
            self.ui.load_next_batch()
            self.wait_until(entered.is_set)
            QTimer.singleShot(0, lambda: pulses.append(True))
            for _ in range(10):
                self.ui.load_next_batch()
                self.ui._initial_autofill_tick()
            QTest.qWait(100)
            self.assertEqual(pulses, [True])
            self.assertEqual(client.send_query.call_count, 1)
            self.assertNotEqual(threads[0], self.app.thread())
            self.assertFalse(self.ui.feed_load_engine._load_pending)
        finally:
            gate.set()
        ui_threads = []
        self.ui._list_view.changed.connect(lambda: ui_threads.append(QThread.currentThread()))
        self.wait_until(lambda: bool(self.ui._list_view.cards))
        self.assertTrue(all(t == self.app.thread() for t in ui_threads))

    def test_sort_change_during_request_discards_old_page_and_uses_latest_sort(self):
        client = self.prepare_loading()
        gate, entered = threading.Event(), threading.Event()
        def fetch(_query, variables, **kwargs):
            if 'orderBy' not in variables:
                entered.set()
                gate.wait(3)
                return page([task('old')], 'old-cursor')
            return page([task('new')], 'new-cursor')
        client.send_query.side_effect = fetch
        try:
            self.ui.load_next_batch()
            self.wait_until(entered.is_set)
            self.ui._list_controls.sort_actions[('title', False)].trigger()
            self.ui.load_next_batch()
            self.ui._list_controls.sort_actions[('title', True)].trigger()
            self.ui.load_next_batch()
            self.assertEqual(client.send_query.call_count, 1)
        finally:
            gate.set()
        self.wait_until(lambda: 'new' in self.ui._list_view.items)
        self.assertNotIn('old', self.ui._list_view.items)
        self.assertEqual(client.send_query.call_count, 2)
        self.assertEqual(client.send_query.call_args.args[1]['orderBy'][0], {'column':'TITLE', 'order':'DESC'})
        self.assertEqual(self.ui.feed_logic.end_cursor, 'new-cursor')

    def test_deactivation_during_request_does_not_restore_cards(self):
        client = self.prepare_loading()
        gate, entered = threading.Event(), threading.Event()
        def fetch(*args, **kwargs):
            entered.set()
            gate.wait(3)
            return page([task('late')])
        client.send_query.side_effect = fetch
        try:
            self.ui.load_next_batch()
            self.wait_until(entered.is_set)
            self.ui.deactivate()
        finally:
            gate.set()
        self.wait_until(lambda: not self.ui._feed_request.busy)
        self.assertEqual(self.ui._list_view.items, {})
        self.assertIsNone(self.ui.feed_logic.end_cursor)

    def test_opening_single_item_while_list_request_runs_discards_list_response(self):
        client = self.prepare_loading()
        gate, entered = threading.Event(), threading.Event()
        def fetch(_query, variables, **kwargs):
            if variables.get('id') == 'selected':
                return {'data': {'task': task('selected')}}
            entered.set()
            gate.wait(3)
            return page([task('old')])
        client.send_query.side_effect = fetch
        try:
            self.ui.load_next_batch()
            self.wait_until(entered.is_set)
            self.ui.open_item_from_search('works', 'selected', 'Selected work')
            self.ui.load_next_batch()
        finally:
            gate.set()
        self.wait_until(lambda: 'selected' in self.ui._list_view.items)
        self.assertEqual(set(self.ui._list_view.items), {'selected'})
        self.assertEqual(client.send_query.call_args.args[1], {'id': 'selected'})

    def test_filter_change_isolated_even_without_a_new_activation_token(self):
        client = self.prepare_loading()
        gate, entered = threading.Event(), threading.Event()
        new_where = {'column': 'STATUS', 'operator': 'EQ', 'value': 'new-status'}
        def fetch(_query, variables, **kwargs):
            if variables.get('where') == new_where:
                return page([task('new')])
            entered.set()
            gate.wait(3)
            return page([task('old')])
        client.send_query.side_effect = fetch
        try:
            self.ui.load_next_batch()
            self.wait_until(entered.is_set)
            self.ui.feed_logic.set_where(new_where)
            self.ui.clear_feed(self.ui.feed_layout, self.ui.empty_state)
            self.ui.load_next_batch()
        finally:
            gate.set()
        self.wait_until(lambda: 'new' in self.ui._list_view.items)
        self.assertEqual(set(self.ui._list_view.items), {'new'})
        self.assertEqual(self.ui.feed_logic.where, new_where)

    def test_appending_a_page_does_not_reinsert_or_retheme_existing_cards(self):
        self.add(task(1), task(2))
        original = set(self.ui._list_view.cards.values())
        with patch.object(self.ui.feed_layout, 'insertWidget', wraps=self.ui.feed_layout.insertWidget) as insert:
            self.add(task(3), task(4), task(5))
        self.assertEqual(insert.call_count, 3)
        self.assertTrue(all(call.args[1] not in original for call in insert.call_args_list))
        self.assertEqual(self.factory.call_count, 5)
        with patch.object(self.ui, 'retheme') as retheme:
            self.ui._schedule_post_batch_updates()
        retheme.assert_not_called()


if __name__ == '__main__':
    unittest.main()
