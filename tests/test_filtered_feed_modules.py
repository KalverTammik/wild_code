"""What the list modules have in common: their filters, feed area, loading and shutdown."""
from __future__ import annotations

import os
import sys
import unittest
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional
from unittest.mock import Mock, call, patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
if os.environ.get("QGIS_PREFIX_PATH"):
    sys.path.append(str(Path(os.environ["QGIS_PREFIX_PATH"]) / "python" / "plugins"))

from PyQt5.QtCore import QCoreApplication, QEvent, Qt
from PyQt5.QtWidgets import QApplication

from Kavitro_dev.Logs.python_fail_logger import PythonFailLogger
from Kavitro_dev.languages.language_manager import LanguageManager
from Kavitro_dev.languages.translation_keys import TranslationKeys
from Kavitro_dev.module_manager import ModuleManager
from Kavitro_dev.modules.asbuilt.AsBuiltUi import AsBuiltModule
from Kavitro_dev.modules.contract.ContractUi import ContractsModule
from Kavitro_dev.modules.coordination.CoordinationModule import CoordinationModule
from Kavitro_dev.modules.easements.EasementsUi import EasementsModule
from Kavitro_dev.modules.projects.ProjectsUi import ProjectsModule
from Kavitro_dev.modules.task_shared.task_module_base_ui import TaskModuleBaseUI
from Kavitro_dev.python.api_client import APIClient
from Kavitro_dev.ui.ModuleBaseUI import ModuleBaseUI
from Kavitro_dev.utils.FilterHelpers.FilterHelper import FilterHelper, FilterRefreshService
from Kavitro_dev.constants.module_names import Module, ModuleSupports
from Kavitro_dev.widgets.Filters.StatusFilterWidget import StatusFilterWidget
from Kavitro_dev.widgets.Filters.TagsFilterWidget import TagsFilterWidget
from Kavitro_dev.widgets.Filters.TypeFilterWidget import TypeFilterWidget
from Kavitro_dev.widgets.Filters.filter_refresh_helper import FilterRefreshHelper


@dataclass(frozen=True)
class Spec:
    cls: type
    build: Callable
    module: Module
    empty_key: str
    supports: tuple  # types, statuses, tags, archive, as the module registry gives them
    overdue: Optional[Module]
    event_prefix: str


SPECS = (
    Spec(ContractsModule, lambda: ContractsModule(), Module.CONTRACT,
         TranslationKeys.NO_CONTRACTS_FOUND, (True, True, True, False), Module.CONTRACT, "contract"),
    Spec(CoordinationModule, lambda: CoordinationModule(), Module.COORDINATION,
         TranslationKeys.NO_COORDINATIONS_FOUND, (True, True, True, True), Module.COORDINATION, "coordination"),
    Spec(ProjectsModule, lambda: ProjectsModule(), Module.PROJECT,
         TranslationKeys.NO_PROJECTS_FOUND, (False, True, True, False), Module.PROJECT, "projects"),
    Spec(AsBuiltModule, lambda: AsBuiltModule(), Module.ASBUILT,
         TranslationKeys.NO_ASBUILT_FOUND, (True, True, False, False), None, "task_module"),
    Spec(EasementsModule, lambda: EasementsModule(), Module.EASEMENT,
         TranslationKeys.NO_EASEMENTS_FOUND, (True, True, False, False), None, "task_module"),
)
BY_CLASS = {spec.cls: spec for spec in SPECS}
TASK_SPECS = tuple(spec for spec in SPECS if spec.event_prefix == "task_module")
THREE_FILTER_SPECS = (BY_CLASS[ContractsModule], BY_CLASS[CoordinationModule])


def delete_now(widget) -> None:
    widget.hide()
    widget.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)


class ModuleCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self) -> None:
        self.lang = LanguageManager()
        for patcher in (
            patch.object(APIClient, "send_query", side_effect=AssertionError("Unexpected API call")),
            patch("requests.sessions.Session.request", side_effect=AssertionError("Unexpected network request")),
        ):
            patcher.start()
            self.addCleanup(patcher.stop)

    def build(self, spec: Spec, supports=None):
        with patch.object(ModuleManager, "getModuleSupports", return_value=supports or spec.supports) as supports_read:
            module = spec.build()
        supports_read.assert_called_once_with(spec.module.name)
        self.addCleanup(delete_now, module)
        return module

    @staticmethod
    def filters_of(module) -> list:
        return [w for w in (module.status_filter, module.type_filter, module.tags_filter) if w is not None]


class ModuleIdentityTest(ModuleCase):
    def test_module_names_itself_and_keeps_its_language(self) -> None:
        for spec in SPECS:
            with self.subTest(module=spec.cls.__name__):
                module = self.build(spec)
                self.assertEqual(module.module_key, spec.module.value)
                self.assertEqual(module.objectName(), spec.module.value)
                self.assertEqual(module.lang_manager.language, self.lang.language)
                self.assertIs(module.get_widget(), module)


class ModuleFiltersTest(ModuleCase):
    EXPECTED = {
        ContractsModule: (StatusFilterWidget, TypeFilterWidget, TagsFilterWidget),
        CoordinationModule: (StatusFilterWidget, TypeFilterWidget, TagsFilterWidget),
        ProjectsModule: (StatusFilterWidget, TagsFilterWidget),
        AsBuiltModule: (StatusFilterWidget, TypeFilterWidget),
        EasementsModule: (StatusFilterWidget, TypeFilterWidget),
    }

    def test_registered_filters_are_built_in_order(self) -> None:
        for spec in SPECS:
            with self.subTest(module=spec.cls.__name__):
                module = self.build(spec)
                self.assertEqual([type(w) for w in module._filter_widgets], list(self.EXPECTED[spec.cls]))
                self.assertEqual(module._filter_widgets, self.filters_of(module))

    def test_filters_live_in_the_toolbar_and_wait_for_the_first_view(self) -> None:
        for spec in SPECS:
            with self.subTest(module=spec.cls.__name__):
                module = self.build(spec)
                for widget in module._filter_widgets:
                    self.assertIs(widget.parent(), module.toolbar_area._left)
                    self.assertEqual(widget._module, spec.module.value)
                    self.assertFalse(widget._auto_load)

    def test_only_modules_with_due_dates_show_the_due_pills(self) -> None:
        for spec in SPECS:
            with self.subTest(module=spec.cls.__name__):
                module = self.build(spec)
                self.assertEqual(module.overdue_pills is not None, spec.overdue is not None)

    def test_module_without_registered_filters_has_none(self) -> None:
        for spec in SPECS:
            with self.subTest(module=spec.cls.__name__):
                module = self.build(spec, supports=(False, False, False, False))
                self.assertEqual(module._filter_widgets, [])
                self.assertEqual(self.filters_of(module), [])

    def test_task_modules_never_have_a_tags_filter(self) -> None:
        for spec in TASK_SPECS:
            with self.subTest(module=spec.cls.__name__):
                self.assertIsNone(self.build(spec, supports=(True, True, True, False)).tags_filter)

    def test_type_support_is_known_to_the_refresh_pipeline(self) -> None:
        for spec in SPECS:
            with self.subTest(module=spec.cls.__name__):
                self.assertEqual(self.build(spec).supports_type_filter, spec.supports[0])

    def test_each_filter_change_refreshes_its_own_selection(self) -> None:
        for spec in SPECS:
            with self.subTest(module=spec.cls.__name__):
                module = self.build(spec)
                module._refresh_filters = Mock()
                expected = []
                for widget, keyword in ((module.status_filter, "status_ids"), (module.type_filter, "type_ids"),
                                        (module.tags_filter, "tags_ids")):
                    if widget is not None:
                        widget.selectionChanged.emit(["nimi"], ["7"])
                        expected.append(call(**{keyword: ["7"]}))
                self.assertEqual(module._refresh_filters.call_args_list, expected)

    def test_refresh_button_is_in_the_toolbar(self) -> None:
        for spec in SPECS:
            with self.subTest(module=spec.cls.__name__):
                module = self.build(spec)
                self.assertIsInstance(module._refresh_helper, FilterRefreshHelper)
                self.assertTrue(module.toolbar_area.isAncestorOf(module._filter_refresh_widget))
                self.assertIs(module.toolbar_area._refresh_widget, module._filter_refresh_widget)

    def test_task_modules_are_themed_when_built(self) -> None:
        for spec in TASK_SPECS:
            with self.subTest(module=spec.cls.__name__), patch.object(spec.cls, "retheme") as retheme:
                self.build(spec)
                retheme.assert_called_once_with()


class ModuleFeedAreaTest(ModuleCase):
    def test_feed_area_is_scrolled_and_empty_state_hidden(self) -> None:
        for spec in SPECS:
            with self.subTest(module=spec.cls.__name__):
                module = self.build(spec)
                self.assertIs(module.scroll_area.widget(), module.feed_content)
                self.assertTrue(module.scroll_area.widgetResizable())
                self.assertIs(module.feed_content.layout(), module.feed_layout)
                self.assertEqual(module.feed_layout.spacing(), 6)
                margins = module.feed_layout.contentsMargins()
                self.assertEqual((margins.left(), margins.top(), margins.right(), margins.bottom()), (0, 0, 0, 0))

    def test_empty_state_is_first_and_a_stretch_keeps_cards_up(self) -> None:
        for spec in SPECS:
            with self.subTest(module=spec.cls.__name__):
                module = self.build(spec)
                self.assertEqual(module._empty_state.text(), self.lang.translate(spec.empty_key))
                self.assertEqual(module._empty_state.alignment(), Qt.AlignCenter)
                self.assertFalse(module._empty_state.isVisibleTo(module))
                self.assertIs(module.feed_layout.itemAt(0).widget(), module._empty_state)
                self.assertEqual(module.feed_layout.count(), 2)
                self.assertIsNotNone(module.feed_layout.itemAt(1).spacerItem())


class ModuleFeedLogicTest(ModuleCase):
    def test_contracts_and_projects_can_open_one_item(self) -> None:
        for spec in (BY_CLASS[ContractsModule], BY_CLASS[ProjectsModule]):
            with self.subTest(module=spec.cls.__name__), patch.object(spec.cls, "FEED_LOGIC_CLS") as logic:
                module = self.build(spec)
                logic.assert_called_once_with(spec.module.value, spec.cls.QUERY_FILE)
                self.assertIs(module.feed_logic, logic.return_value)
                logic.return_value.configure_single_item_query.assert_called_once_with(spec.cls.SINGLE_ITEM_QUERY_FILE)

    def test_coordination_builds_its_feed_later(self) -> None:
        self.assertIsNone(self.build(BY_CLASS[CoordinationModule]).feed_logic)

    def test_task_modules_read_the_task_feed(self) -> None:
        for spec in TASK_SPECS:
            with self.subTest(module=spec.cls.__name__), patch.object(spec.cls, "FEED_LOGIC_CLS") as logic:
                module = self.build(spec)
                logic.assert_called_once_with(spec.cls.FEED_MODULE_ENUM.value, spec.cls.QUERY_FILE,
                                              root_field=spec.cls.FEED_ROOT_FIELD)
                self.assertIs(module.feed_logic, logic.return_value)
                logic.return_value.configure_single_item_query.assert_called_once_with(spec.cls.SINGLE_ITEM_QUERY_FILE)


class ModuleLifecycleTest(ModuleCase):
    def test_first_view_loads_filters_then_refreshes(self) -> None:
        for spec in SPECS:
            with self.subTest(module=spec.cls.__name__):
                module = self.build(spec)
                order = Mock()
                module._ensure_filters_loaded = order.ensure
                module._refresh_filters = order.refresh
                module.refresh_overdue_counts = order.overdue
                module.on_first_visible()
                expected = [call.ensure(), call.refresh()]
                if spec.overdue is not None:
                    expected.append(call.overdue(spec.overdue))
                self.assertEqual(order.mock_calls, expected)

    def test_without_a_further_page_no_request_is_sent(self) -> None:
        for spec in SPECS:
            with self.subTest(module=spec.cls.__name__):
                module, request = self.loading_module(spec)
                module.feed_logic.has_more = False
                module.process_next_batch = Mock(return_value="erä")
                self.assertEqual(module.load_next_batch(), "erä")
                request.submit.assert_not_called()
                module._activated = False
                self.assertEqual(module.load_next_batch(), [])

    def test_a_page_is_fetched_in_a_worker_on_a_snapshot_and_accepted_on_the_ui_thread(self) -> None:
        for spec in SPECS:
            with self.subTest(module=spec.cls.__name__):
                module, request = self.loading_module(spec)
                feed = module.feed_logic
                feed.where = {"AND": [{"column": "STATUS"}]}
                self.assertEqual(module.load_next_batch(), [])
                function, snapshot = request.submit.call_args.args
                self.assertIs(function, type(feed).fetch_snapshot)
                self.assertIsNot(snapshot, feed)
                self.assertIsNot(snapshot.where, feed.where)
                self.assertEqual(snapshot.where, feed.where)
                self.assertEqual((feed.is_loading, snapshot.is_loading), (True, False))
                # While the page is on its way, no second request for it.
                self.assertEqual(module.load_next_batch(), [])
                request.submit.assert_called_once()

                snapshot.end_cursor, snapshot.has_more, snapshot.total_count = "c2", False, 9
                module.accept_batch_result = Mock(return_value=["card"])
                module.feed_load_engine = Mock()
                module._on_feed_loaded((snapshot, [{"id": "1"}]))
                self.assertEqual((feed.end_cursor, feed.has_more, feed.total_count, feed.is_loading),
                                 ("c2", False, 9, False))
                module.accept_batch_result.assert_called_once_with([{"id": "1"}])
                module.feed_load_engine.accept_batch.assert_called_once_with(["card"], token=module._active_token)

    def test_a_page_for_an_old_view_or_session_is_dropped(self) -> None:
        for spec in SPECS:
            for change in ("token", "session", "deactivated"):
                with self.subTest(module=spec.cls.__name__, change=change):
                    module, request = self.loading_module(spec)
                    module.load_next_batch()
                    snapshot = request.submit.call_args.args[1]
                    snapshot.end_cursor = "c2"
                    module.accept_batch_result = Mock()
                    with patch("Kavitro_dev.ui.mixins.filtered_feed_mixin.SessionManager.session_signature",
                               return_value="other" if change == "session" else module._feed_request_key[1]):
                        if change == "token":
                            module.bump_token()
                        elif change == "deactivated":
                            module._activated = False
                        module._on_feed_loaded((snapshot, [{"id": "1"}]))
                    module.accept_batch_result.assert_not_called()
                    self.assertIsNone(module.feed_logic.end_cursor)
                    self.assertFalse(module.feed_logic.is_loading)
                    request.invalidate.assert_called()

    def test_a_new_filter_or_session_cancels_the_page_on_its_way(self) -> None:
        for spec in SPECS:
            for step in ("clear_feed", "reset_feed_session"):
                with self.subTest(module=spec.cls.__name__, step=step):
                    module, request = self.loading_module(spec)
                    module.load_next_batch()
                    if step == "clear_feed":
                        module.clear_feed(module.feed_layout, module._empty_state)
                    else:
                        module.reset_feed_session()
                    request.invalidate.assert_called()
                    self.assertFalse(module.feed_logic.is_loading)
                    self.assertIsNone(module._feed_request_key)

    def test_a_worker_failure_is_shown_in_the_feed(self) -> None:
        for spec in SPECS:
            with self.subTest(module=spec.cls.__name__):
                module, request = self.loading_module(spec)
                module.load_next_batch()
                module._show_empty_state = Mock()
                module._on_feed_failed("[WC-API][network] Connection refused")
                self.assertFalse(module.feed_logic.is_loading)
                self.assertTrue(module.feed_logic.last_error_message)
                self.assertNotIn("WC-API", module.feed_logic.last_error_message)
                module._show_empty_state.assert_called_once_with(module.feed_logic.last_error_message)

    def test_the_request_runs_off_the_ui_thread(self) -> None:
        import threading
        import time
        from Kavitro_dev.feed.FeedLogic import UnifiedFeedLogic

        spec = BY_CLASS[ProjectsModule]
        module = self.build(spec)
        module._activated = True
        threads = []

        def fetch(feed):
            threads.append(threading.current_thread())
            feed.end_cursor, feed.has_more = "c2", False
            return [{"id": "1"}]

        module.accept_batch_result = Mock(return_value=[])
        module.feed_load_engine = Mock()
        with patch.object(UnifiedFeedLogic, "fetch_next_batch", fetch):
            self.assertEqual(module.load_next_batch(), [])
            deadline = time.monotonic() + 5
            while not module.accept_batch_result.called and time.monotonic() < deadline:
                QCoreApplication.processEvents()
                time.sleep(0.01)
        module.accept_batch_result.assert_called_once_with([{"id": "1"}])
        self.assertEqual(len(threads), 1)
        self.assertIsNot(threads[0], threading.main_thread())
        self.assertEqual((module.feed_logic.end_cursor, module.feed_logic.is_loading), ("c2", False))
        module._invalidate_feed_request()

    def test_autofill_waits_for_the_page_instead_of_polling(self) -> None:
        spec = BY_CLASS[ProjectsModule]
        module = self.build(spec)
        module._activated = True
        module.feed_load_engine = Mock()
        module.feed_load_engine.has_buffer.return_value = False
        module._is_scrollable = Mock(return_value=False)
        with patch("Kavitro_dev.ui.mixins.progressive_load_mixin.QTimer.singleShot") as later:
            module.feed_logic.is_loading = True
            module._initial_autofill_tick()
            module.feed_load_engine.schedule_load.assert_not_called()
            module.feed_logic.is_loading = False
            module._initial_autofill_tick()
            module.feed_load_engine.schedule_load.assert_called_once()
            # The page answer starts the next tick, so nothing is queued meanwhile.
            later.assert_not_called()
            module.feed_load_engine.has_buffer.return_value = True
            module._initial_autofill_tick()
            module.feed_load_engine.feed_until_filled_plus_one.assert_called_once_with(max_cards=50)
            later.assert_called_once()

    def loading_module(self, spec):
        module = self.build(spec)
        if module.feed_logic is None:
            module.feed_logic = module.FEED_LOGIC_CLS(module.module_key, module.QUERY_FILE)
        module._activated = True
        request = Mock()
        module._feed_request = request
        return module, request

    def test_deactivate_clears_cancels_and_ends_the_session(self) -> None:
        for spec in SPECS:
            with self.subTest(module=spec.cls.__name__):
                module = self.build(spec)
                order = Mock()
                module._clear_filters = order.clear
                filters = self.filters_of(module)
                with patch.object(FilterHelper, "cancel_pending_load", order.cancel), patch.object(
                    ModuleBaseUI, "deactivate", order.base
                ):
                    module.deactivate()
                calls = [c for c in order.mock_calls if not (c[0] == "cancel" and c.args[0] is None)]
                self.assertEqual(calls, [call.clear()] + [call.cancel(w, invalidate_request=True) for w in filters] + [call.base()])

    def test_failed_cancel_is_logged_and_the_rest_continue(self) -> None:
        for spec in SPECS:
            with self.subTest(module=spec.cls.__name__):
                module = self.build(spec)
                module._clear_filters = Mock()

                def failing(widget, *, invalidate_request):
                    if widget is module.status_filter:
                        raise RuntimeError("thread")

                with patch.object(FilterHelper, "cancel_pending_load", side_effect=failing) as cancel, patch.object(
                    PythonFailLogger, "log_exception"
                ) as log, patch.object(ModuleBaseUI, "deactivate") as base:
                    module.deactivate()
                self.assertEqual(log.call_args.kwargs["event"], f"{spec.event_prefix}_cancel_status_filter_failed")
                touched = [c.args[0] for c in cancel.call_args_list if c.args[0] is not None]
                self.assertEqual(touched, self.filters_of(module))
                base.assert_called_once_with()

    def test_failed_type_and_tags_cancels_name_their_filter(self) -> None:
        for spec in THREE_FILTER_SPECS:
            with self.subTest(module=spec.cls.__name__):
                module = self.build(spec)
                module._clear_filters = Mock()
                with patch.object(FilterHelper, "cancel_pending_load", side_effect=[None, RuntimeError("a"), RuntimeError("b")]), patch.object(
                    PythonFailLogger, "log_exception"
                ) as log, patch.object(ModuleBaseUI, "deactivate"):
                    module.deactivate()
                self.assertEqual([c.kwargs["event"] for c in log.call_args_list],
                                 [f"{spec.event_prefix}_cancel_type_filter_failed", f"{spec.event_prefix}_cancel_tags_filter_failed"])

    def assert_each_widget_is_tried(self, method_name: str, widget_method: str, event_part: str) -> None:
        for spec in SPECS:
            with self.subTest(module=spec.cls.__name__):
                module = self.build(spec)
                failing, working = Mock(), Mock()
                getattr(failing, widget_method).side_effect = RuntimeError("deleted")
                module._filter_widgets = [failing, working]
                with patch.object(PythonFailLogger, "log_exception") as log:
                    getattr(module, method_name)()
                getattr(working, widget_method).assert_called_once_with()
                self.assertEqual(log.call_args.kwargs["module"], spec.module.value)
                self.assertIn(event_part, log.call_args.kwargs["event"])

    def test_failed_filter_load_is_logged_and_the_rest_continue(self) -> None:
        self.assert_each_widget_is_tried("_ensure_filters_loaded", "ensure_loaded", "filter")

    def test_failed_filter_clear_is_logged_and_the_rest_continue(self) -> None:
        self.assert_each_widget_is_tried("_clear_filters", "clear_data", "filter")


class ModuleRefreshTest(ModuleCase):
    def refresh(self, module, **selection):
        with patch.object(FilterRefreshService, "refresh_filters") as refresh:
            module._refresh_filters(**selection)
        refresh.assert_called_once()
        self.assertIs(refresh.call_args.args[0], module)
        return refresh.call_args.kwargs

    def test_contracts_and_coordination_pass_every_filter_on(self) -> None:
        for spec in THREE_FILTER_SPECS:
            with self.subTest(module=spec.cls.__name__):
                module = self.build(spec)
                self.assertEqual(self.refresh(module, status_ids=["1"], type_ids=["2"], tags_ids=["3"]), {
                    "status_ids": ["1"], "type_ids": ["2"], "tags_ids": ["3"], "status_filter": module.status_filter,
                    "type_filter": module.type_filter, "tags_filter": module.tags_filter,
                })

    def test_projects_have_no_type_filter_and_reset_the_due_pills(self) -> None:
        module = self.build(BY_CLASS[ProjectsModule])
        self.assertEqual(self.refresh(module, status_ids=["1"], type_ids=["2"], tags_ids=["3"]), {
            "status_ids": ["1"], "tags_ids": ["3"], "status_filter": module.status_filter,
            "tags_filter": module.tags_filter, "reset_overdue_pills": True,
        })

    def test_task_modules_have_no_tags_and_limit_types_to_their_scope(self) -> None:
        for spec in TASK_SPECS:
            with self.subTest(module=spec.cls.__name__):
                module = self.build(spec)
                module._effective_type_ids = Mock(return_value=["9"])
                self.assertEqual(self.refresh(module, status_ids=["1"], type_ids=["2"], tags_ids=["3"]), {
                    "status_ids": ["1"], "type_ids": ["9"], "tags_ids": None, "status_filter": module.status_filter,
                    "type_filter": module.type_filter, "tags_filter": None,
                })
                module._effective_type_ids.assert_called_once_with(["2"])

    def test_task_scope_decides_the_effective_types(self) -> None:
        for spec in TASK_SPECS:
            module = self.build(spec)
            for scope, selected, expected in (([], ["1"], ["1"]), ([], None, []), (["1", "2"], ["2", "3"], ["2"]),
                                              (["1", "2"], [], ["1", "2"]), (["1"], ["3"], [])):
                with self.subTest(module=spec.cls.__name__, scope=scope, selected=selected):
                    module._settings_logic = Mock()
                    module._settings_logic.load_module_preference_ids.return_value = scope
                    self.assertEqual(module._effective_type_ids(selected), expected)
                    module._settings_logic.load_module_preference_ids.assert_called_once_with(
                        spec.module.value, support_key=ModuleSupports.TYPES.value
                    )


class SharedPartsStayInOnePlaceTest(unittest.TestCase):
    def test_no_module_carries_its_own_copy(self) -> None:
        shared = ("_ensure_filters_loaded", "_clear_filters", "load_next_batch", "get_widget", "deactivate", "activate",
                  "_on_status_filter_selection", "_on_type_filter_selection", "_on_tags_filter_selection")
        for module_class in (ContractsModule, CoordinationModule, ProjectsModule, TaskModuleBaseUI):
            for name in shared:
                with self.subTest(module=module_class.__name__, part=name):
                    self.assertNotIn(name, vars(module_class))


if __name__ == "__main__":
    unittest.main()
