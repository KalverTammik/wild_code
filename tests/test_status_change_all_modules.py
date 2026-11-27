"""The card status can be changed in every module that has a status, the same way, and the map layer follows."""
from __future__ import annotations

import importlib
import os
import sys
import threading
import time
import unittest
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parents[1].parent))

from PyQt5 import sip
from PyQt5.QtCore import QCoreApplication, QEvent, QEventLoop, Qt, QTimer
from PyQt5.QtWidgets import QWidget
from qgis.core import QgsApplication, QgsFeature, QgsGeometry, QgsVectorLayer

from Kavitro_dev.Logs.python_fail_logger import PythonFailLogger
from Kavitro_dev.modules.asbuilt.asbuilt_layer_service import AsBuiltLayerService
from Kavitro_dev.modules.easements.easement_layer_service import EasementLayerService
from Kavitro_dev.modules.projects.projects_layer_service import ProjectsLayerService

status_widget_module = importlib.import_module("Kavitro_dev.widgets.DataDisplayWidgets.status_change_controller")
StatusWidget = status_widget_module.StatusChangeController
MainStatusWidget = importlib.import_module("Kavitro_dev.widgets.DataDisplayWidgets.MainStatusWidget").MainStatusWidget

OPEN = {"id": "1", "name": "Avatud", "color": "4FBF6B", "type": "OPEN"}
CLOSED = {"id": "2", "name": "Suletud", "color": "999999", "type": "CLOSED"}
MODULES_WITH_STATUS_CHANGE = ("works", "asbuilt", "task", "project", "contract", "coordination", "easement")


class ControllerTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QgsApplication.instance() or QgsApplication([], False)

    def widget(self, module: str, item_id: str = "7") -> StatusWidget:
        owner = QWidget()
        self.addCleanup(owner.deleteLater)
        controller = StatusWidget(owner, {"id": item_id, "status": OPEN}, module_name=module)
        controller.test_owner = owner  # the owner is a Python-owned widget; keep it alive with its controller
        controller.busy = []
        controller.busy_changed.connect(controller.busy.append)
        return controller

    def patch_api(self, **returns):
        patched = {}
        for name, value in returns.items():
            patcher = patch.object(status_widget_module.APIModuleActions, name, return_value=value)
            patched[name] = patcher.start()
            self.addCleanup(patcher.stop)
        return patched


class EditableModulesTest(ControllerTestCase):
    def test_every_module_with_a_status_change_can_be_edited(self) -> None:
        for module in MODULES_WITH_STATUS_CHANGE:
            with self.subTest(module=module):
                self.assertTrue(self.widget(module).can_edit_status())

    def test_an_item_without_an_id_or_a_module_without_a_status_change_cannot(self) -> None:
        self.assertFalse(self.widget("project", item_id="").can_edit_status())
        for module in ("property", "letter", ""):
            with self.subTest(module=module):
                self.assertFalse(self.widget(module).can_edit_status())


class StatusChangeFlowTest(ControllerTestCase):
    def setUp(self) -> None:
        refresh = patch.object(StatusWidget, "_schedule_card_refresh")
        self.refresh = refresh.start()
        self.addCleanup(refresh.stop)
        hooks = patch.dict(StatusWidget._status_change_hooks, clear=True)
        hooks.start()
        self.addCleanup(hooks.stop)
        log = patch.object(PythonFailLogger, "log_exception")
        self.hook = log.start()
        self.addCleanup(log.stop)

    @staticmethod
    def run_change(widget, option) -> None:
        """The change runs on a worker thread; wait for the widget to report that it is done."""
        loop = QEventLoop()
        widget.status_change_finished.connect(loop.quit)
        QTimer.singleShot(5000, loop.quit)
        widget._update_status(option)
        loop.exec_()

    def test_a_non_task_module_takes_the_card_from_the_answer_and_runs_its_hook(self) -> None:
        seen = []
        StatusWidget.register_status_change_hook(("project",), "probe", lambda item_id, payload: seen.append((item_id, payload)))
        api = self.patch_api(update_item_status={"id": "7", "updatedAt": "2026-11-25", "status": CLOSED}, get_task_data=None)
        widget = self.widget("project")

        self.run_change(widget, CLOSED)

        api["update_item_status"].assert_called_once_with("project", "7", "2")
        api["get_task_data"].assert_not_called()
        self.assertEqual(widget._item_data["status"], CLOSED)
        self.assertEqual(widget._item_data["updatedAt"], "2026-11-25")
        self.assertEqual(seen, [("7", widget._item_data)])
        self.refresh.assert_called_once()

    def test_every_non_task_module_changes_the_status_through_the_same_path(self) -> None:
        for module in ("contract", "coordination", "easement", "project"):
            with self.subTest(module=module):
                api = self.patch_api(update_item_status={"id": "7", "status": CLOSED}, get_task_data=None)
                widget = self.widget(module)
                self.run_change(widget, CLOSED)
                api["update_item_status"].assert_called_once_with(module, "7", "2")
                api["get_task_data"].assert_not_called()
                self.assertEqual(widget._item_data["status"], CLOSED)

    def test_a_task_section_reads_the_task_again(self) -> None:
        fresh = {"id": "7", "status": CLOSED, "title": "Töö"}
        api = self.patch_api(update_item_status={"id": "7", "status": CLOSED}, get_task_data=fresh)
        widget = self.widget("works")

        self.run_change(widget, CLOSED)

        api["get_task_data"].assert_called_once_with("7")
        self.assertEqual(widget._item_data, fresh)

    def test_a_refused_change_keeps_the_old_status_and_tells_the_user(self) -> None:
        StatusWidget.register_status_change_hook(("contract",), "probe", lambda *_args: self.fail("hook must not run"))
        self.patch_api(update_item_status=None, get_task_data=None)
        widget = self.widget("contract")
        with patch.object(status_widget_module.ModernMessageDialog, "show_warning") as warning:
            self.run_change(widget, CLOSED)

        warning.assert_called_once()
        self.assertEqual(widget._item_data["status"], OPEN)
        self.refresh.assert_not_called()

    def test_a_failing_hook_is_logged_and_does_not_undo_the_change(self) -> None:
        def broken(_item_id, _payload):
            raise RuntimeError("layer gone")

        StatusWidget.register_status_change_hook(("easement",), "probe", broken)
        self.patch_api(update_item_status={"id": "7", "status": CLOSED}, get_task_data=None)
        widget = self.widget("easement")

        self.run_change(widget, CLOSED)

        self.assertEqual(widget._item_data["status"], CLOSED)
        self.assertEqual(self.hook.call_args.kwargs["event"], "status_widget_status_change_hook_failed")


class BackgroundChangeTest(ControllerTestCase):
    """The change does not block the GUI: the card shows it inline and a dialog waits for a slow answer."""

    def setUp(self) -> None:
        for target, name in ((StatusWidget, "_schedule_card_refresh"), (PythonFailLogger, "log_exception")):
            patcher = patch.object(target, name)
            patcher.start()
            self.addCleanup(patcher.stop)
        hooks = patch.dict(StatusWidget._status_change_hooks, clear=True)
        hooks.start()
        self.addCleanup(hooks.stop)
        start = patch.object(status_widget_module, "start_worker")
        self.start_worker = start.start()
        self.addCleanup(start.stop)

    def test_the_card_shows_the_change_inline_at_once_and_no_dialog_yet(self) -> None:
        widget = self.widget("project")

        widget._update_status(CLOSED)

        self.assertTrue(widget._is_updating)
        self.assertEqual(widget.busy, [True])
        self.start_worker.assert_called_once()
        self.assertIsNone(widget._saving_dialog)

    def test_the_worker_runs_the_change_for_this_item(self) -> None:
        widget = self.widget("works", item_id="9")

        widget._update_status(CLOSED)

        worker = self.start_worker.call_args.args[0]
        self.assertEqual((worker._func, worker._args), (status_widget_module._change_status, ("works", "9", "2")))

    def test_the_dialog_waits_one_second_and_only_a_slow_change_gets_it(self) -> None:
        self.assertEqual(StatusWidget.SAVING_DIALOG_DELAY_MS, 1000)
        widget = self.widget("project")

        widget._update_status(CLOSED)

        self.assertTrue(widget._saving_timer.isActive())
        self.assertEqual(widget._saving_timer.interval(), 1000)
        self.assertIsNone(widget._saving_dialog)

        widget._show_saving_dialog()  # what the timer does when the answer is still missing after a second
        self.assertTrue(widget._saving_dialog.isVisible())
        dialog = widget._saving_dialog
        dialog.reject()  # Escape must not hide a running write
        self.assertTrue(dialog.isVisible())

        widget._on_status_change_done({"updated": {"id": "7", "status": CLOSED}, "refreshed": None})
        self.assertIsNone(widget._saving_dialog)
        self.assertFalse(widget._saving_timer.isActive())
        self.assertFalse(widget._is_updating)

    def test_a_fast_change_never_shows_the_dialog(self) -> None:
        widget = self.widget("project")
        widget._update_status(CLOSED)

        widget._on_status_change_done({"updated": {"id": "7", "status": CLOSED}, "refreshed": None})
        widget._show_saving_dialog()  # a timer that fires after the answer has nothing to show

        self.assertIsNone(widget._saving_dialog)

    def test_a_second_change_while_one_is_running_is_ignored(self) -> None:
        widget = self.widget("project")

        widget._update_status(CLOSED)
        widget._update_status(OPEN)

        self.start_worker.assert_called_once()

    def test_a_failed_worker_restores_the_old_status(self) -> None:
        widget = self.widget("project")
        widget._update_status(CLOSED)
        with patch.object(status_widget_module.ModernMessageDialog, "show_warning") as warning:
            widget._on_status_change_error("boom")

        warning.assert_called_once()
        self.assertFalse(widget._is_updating)
        self.assertEqual(widget._item_data["status"], OPEN)
        self.assertEqual(widget.busy, [True, False])


class RealWorkerTest(ControllerTestCase):
    def test_the_change_runs_off_the_gui_thread_and_the_card_follows(self) -> None:
        for target, name in ((StatusWidget, "_schedule_card_refresh"), (PythonFailLogger, "log_exception")):
            patcher = patch.object(target, name)
            patcher.start()
            self.addCleanup(patcher.stop)
        seen = []

        def record(*_args):
            seen.append(threading.current_thread())
            return {"id": "7", "status": CLOSED}

        update = patch.object(status_widget_module.APIModuleActions, "update_item_status", side_effect=record)
        update.start()
        self.addCleanup(update.stop)
        widget = self.widget("project")
        loop = QEventLoop()
        widget.status_change_finished.connect(loop.quit)
        QTimer.singleShot(5000, loop.quit)

        widget._update_status(CLOSED)
        loop.exec_()

        self.assertEqual(len(seen), 1)
        self.assertIsNot(seen[0], threading.main_thread())
        self.assertEqual(widget._item_data["status"], CLOSED)


class ChangeStatusFunctionTest(unittest.TestCase):
    def run_it(self, module, updated, fresh=None):
        with patch.object(status_widget_module.APIModuleActions, "update_item_status", return_value=updated) as update,                 patch.object(status_widget_module.APIModuleActions, "get_task_data", return_value=fresh) as read:
            return status_widget_module._change_status(module, "7", "2"), update, read

    def test_a_task_section_reads_the_task_after_the_change(self) -> None:
        for module in ("works", "asbuilt", "task"):
            with self.subTest(module=module):
                result, update, read = self.run_it(module, {"id": "7"}, {"id": "7", "title": "Töö"})
                update.assert_called_once_with(module, "7", "2")
                read.assert_called_once_with("7")
                self.assertEqual(result, {"updated": {"id": "7"}, "refreshed": {"id": "7", "title": "Töö"}})

    def test_any_other_module_reads_nothing_more(self) -> None:
        for module in ("project", "contract", "coordination", "easement"):
            with self.subTest(module=module):
                result, _update, read = self.run_it(module, {"id": "7"})
                read.assert_not_called()
                self.assertEqual(result, {"updated": {"id": "7"}, "refreshed": None})

    def test_a_refused_change_is_not_followed_by_a_read(self) -> None:
        result, _update, read = self.run_it("works", None)
        read.assert_not_called()
        self.assertEqual(result, {"updated": None, "refreshed": None})


class StatusMenuOptionsTest(ControllerTestCase):
    """The statuses of a module are cached; a missing list is loaded in the background, never on the click."""

    def setUp(self) -> None:
        StatusWidget.clear_options_cache()
        self.addCleanup(StatusWidget.clear_options_cache)
        self.opened = []
        for target, name, kwargs in (
            (status_widget_module, "start_worker", {}),
            (status_widget_module.ModernMessageDialog, "show_warning", {}),
            (StatusWidget, "_open_status_menu", {"side_effect": lambda options, anchor: self.opened.append(list(options))}),
        ):
            patcher = patch.object(target, name, **kwargs)
            setattr(self, name, patcher.start())
            self.addCleanup(patcher.stop)

    def test_a_cached_list_opens_the_menu_without_a_request(self) -> None:
        StatusWidget._options_cache["project"] = (time.monotonic(), [OPEN, CLOSED])
        widget = self.widget("project")

        widget.show_status_menu()

        self.assertEqual(self.opened, [[OPEN, CLOSED]])
        self.start_worker.assert_not_called()
        self.assertEqual(widget.busy, [])

    def test_a_missing_list_is_loaded_in_the_background_and_the_menu_opens_when_it_arrives(self) -> None:
        widget = self.widget("project")

        widget.show_status_menu()

        worker = self.start_worker.call_args.args[0]
        self.assertEqual((worker._func, worker._args), (status_widget_module._load_status_options, ("project",)))
        self.assertEqual(widget.busy, [True])
        self.assertEqual(self.opened, [])

        widget._on_options_loaded([OPEN, CLOSED])

        self.assertEqual(widget.busy, [True, False])
        self.assertEqual(self.opened, [[OPEN, CLOSED]])
        self.assertIn("project", StatusWidget._options_cache)

    def test_a_list_older_than_the_ttl_is_loaded_again(self) -> None:
        StatusWidget._options_cache["project"] = (time.monotonic() - StatusWidget.OPTIONS_TTL_SECONDS - 1, [OPEN])
        widget = self.widget("project")

        widget.show_status_menu()

        self.start_worker.assert_called_once()
        self.assertEqual(self.opened, [])

    def test_the_cache_is_kept_per_module(self) -> None:
        StatusWidget._options_cache["contract"] = (time.monotonic(), [OPEN])
        widget = self.widget("project")

        widget.show_status_menu()

        self.start_worker.assert_called_once()

    def test_an_empty_answer_warns_and_is_not_cached(self) -> None:
        widget = self.widget("project")
        widget.show_status_menu()

        widget._on_options_failed("boom")

        self.show_warning.assert_called_once()
        self.assertNotIn("project", StatusWidget._options_cache)
        self.assertEqual(widget.busy, [True, False])
        self.assertEqual(self.opened, [])

    def test_clicks_while_the_list_loads_are_ignored(self) -> None:
        widget = self.widget("project")

        widget.show_status_menu()
        widget.show_status_menu()

        self.start_worker.assert_called_once()

    def test_a_module_without_a_status_change_or_an_item_without_an_id_opens_nothing(self) -> None:
        self.widget("property").show_status_menu()
        self.widget("project", item_id="").show_status_menu()

        self.start_worker.assert_not_called()
        self.assertEqual(self.opened, [])


class RailBusyLookTest(ControllerTestCase):
    """The rail is the only thing the user sees of a status change, so it shows that one is running."""

    def setUp(self) -> None:
        self.window = QWidget()
        self.window.show()
        self.addCleanup(self.window.close)
        self.rail = MainStatusWidget({"id": "7", "status": OPEN}, module_name="project", parent=self.window)

    def test_the_rail_fades_and_shows_a_busy_cursor_while_busy(self) -> None:
        idle_style = self.rail.core_fill.styleSheet()

        self.rail._status_changes.busy_changed.emit(True)

        self.assertEqual(self.rail.cursor().shape(), Qt.BusyCursor)
        self.assertEqual(self.rail.rail_frame.cursor().shape(), Qt.BusyCursor)
        self.assertNotEqual(self.rail.core_fill.styleSheet(), idle_style)

        self.rail._status_changes.busy_changed.emit(False)

        self.assertEqual(self.rail.cursor().shape(), Qt.PointingHandCursor)
        self.assertEqual(self.rail.core_fill.styleSheet(), idle_style)

    def test_a_rail_that_cannot_be_edited_goes_back_to_the_normal_cursor(self) -> None:
        rail = MainStatusWidget({"id": "7", "status": OPEN}, module_name="property", parent=self.window)

        rail._status_changes.busy_changed.emit(True)
        rail._status_changes.busy_changed.emit(False)

        self.assertNotEqual(rail.cursor().shape(), Qt.PointingHandCursor)
        self.assertNotEqual(rail.cursor().shape(), Qt.BusyCursor)

    def test_a_saved_status_recolours_the_rail_at_once(self) -> None:
        self.rail._status_changes.status_changed.emit({"id": "7", "status": CLOSED})

        self.assertEqual(self.rail._status_name, CLOSED["name"])
        self.assertEqual(self.rail._status_changes._item_data["status"], CLOSED)


class HoverPopupLifetimeTest(ControllerTestCase):
    """The status name tooltip is a window of its own; it must not stay on the screen when its card goes."""

    def setUp(self) -> None:
        self.window = QWidget()
        self.window.resize(300, 200)
        self.window.show()
        self.addCleanup(self.window.close)
        self.rail = MainStatusWidget({"id": "7", "status": OPEN}, module_name="project", parent=self.window)
        self.rail.show()
        self.rail.show_status_popup()
        self.popup = self.rail.hover_popup

    def test_the_popup_is_shown_by_the_hover(self) -> None:
        self.assertIsNotNone(self.popup)
        self.assertTrue(self.popup.isVisible())

    def test_hiding_the_rail_closes_the_popup(self) -> None:
        self.rail.hide()

        self.assertFalse(self.popup.isVisible())
        self.assertIsNone(self.rail.hover_popup)

    def test_deleting_the_rail_closes_the_popup(self) -> None:
        self.rail.setParent(None)
        self.rail.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)
        QCoreApplication.processEvents()

        self.assertTrue(sip.isdeleted(self.popup) or not self.popup.isVisible())

    def test_clicking_the_rail_for_the_status_menu_removes_the_tooltip_first(self) -> None:
        with patch.object(StatusWidget, "show_status_menu") as menu:
            self.rail.mousePressEvent(_left_click())

        menu.assert_called_once()
        self.assertFalse(self.popup.isVisible())
        self.assertIsNone(self.rail.hover_popup)


def _left_click():
    from PyQt5.QtCore import QEvent as _Event, QPointF, Qt
    from PyQt5.QtGui import QMouseEvent

    return QMouseEvent(_Event.Type.MouseButtonPress, QPointF(2, 2), Qt.MouseButton.LeftButton,
                       Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier)


def memory_layer(fields: str, attributes: list, name: str) -> QgsVectorLayer:
    layer = QgsVectorLayer(f"Polygon?crs=EPSG:3301&{fields}", name, "memory")
    feature = QgsFeature(layer.fields())
    feature.setAttributes(attributes)
    feature.setGeometry(QgsGeometry.fromWkt("POLYGON((0 0, 10 0, 10 10, 0 10, 0 0))"))
    layer.dataProvider().addFeatures([feature])
    return layer


class LayerSyncCase(unittest.TestCase):
    service = None
    module = ""

    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QgsApplication.instance() or QgsApplication([], False)

    def use_layer(self, layer: QgsVectorLayer) -> None:
        self.layer = layer
        resolve = patch.object(self.service, "resolve_main_layer", return_value=layer)
        resolve.start()
        self.addCleanup(resolve.stop)
        log = patch.object(PythonFailLogger, "log")
        self.log = log.start()
        self.addCleanup(log.stop)

    def feature(self):
        return next(self.layer.getFeatures())


class ProjectStatusSyncTest(LayerSyncCase):
    service = ProjectsLayerService

    def setUp(self) -> None:
        self.use_layer(memory_layer("field=ext_project_id:string&field=active:integer&field=detailed:string",
                                    ["P1", 1, ""], "Projektid"))

    def test_the_closed_status_reaches_the_project_feature(self) -> None:
        self.assertTrue(ProjectsLayerService.sync_status_from_project("P1", {"id": "P1", "status": CLOSED}))

        feature = self.feature()
        self.assertEqual(feature["active"], 0)
        self.assertIn("Suletud", str(feature["detailed"]))
        self.assertFalse(self.layer.isEditable())

    def test_a_layer_the_user_edits_is_left_alone(self) -> None:
        self.layer.startEditing()
        self.addCleanup(self.layer.rollBack)

        self.assertFalse(ProjectsLayerService.sync_status_from_project("P1", {"id": "P1", "status": CLOSED}))

        self.assertEqual(self.feature()["active"], 1)
        self.assertEqual(self.log.call_args.args[0], "project_status_sync_skipped_layer_editable")

    def test_a_project_not_on_the_map_or_an_answer_without_a_status_changes_nothing(self) -> None:
        self.assertFalse(ProjectsLayerService.sync_status_from_project("P2", {"id": "P2", "status": CLOSED}))
        self.assertFalse(ProjectsLayerService.sync_status_from_project("P1", {"id": "P1"}))
        self.assertFalse(ProjectsLayerService.sync_status_from_project("P1", None))
        self.assertEqual(self.feature()["active"], 1)

    def test_a_layer_without_the_status_fields_reports_nothing_written(self) -> None:
        self.use_layer(memory_layer("field=ext_project_id:string", ["P1"], "Projektid"))
        self.assertFalse(ProjectsLayerService.sync_status_from_project("P1", {"id": "P1", "status": CLOSED}))


class EasementStatusSyncTest(LayerSyncCase):
    service = EasementLayerService

    def setUp(self) -> None:
        self.use_layer(memory_layer("field=ext_easement_id:string&field=Staatus:string", ["E1", "Eelnõu"], "Servituudid"))
        mapping = patch.object(EasementLayerService, "map_backend_status_to_layer_value",
                               side_effect=lambda status: {"1": "Eelnõu", "2": "Seatud"}.get(str((status or {}).get("id")), ""))
        mapping.start()
        self.addCleanup(mapping.stop)

    def test_the_mapped_status_reaches_the_easement_feature(self) -> None:
        self.assertTrue(EasementLayerService.sync_status_from_easement("E1", {"id": "E1", "status": CLOSED}))
        self.assertEqual(self.feature()["Staatus"], "Seatud")

    def test_a_status_nobody_mapped_leaves_the_layer_alone(self) -> None:
        self.assertFalse(EasementLayerService.sync_status_from_easement("E1", {"id": "E1", "status": {"id": "9"}}))
        self.assertEqual(self.feature()["Staatus"], "Eelnõu")

    def test_an_easement_not_on_the_map_changes_nothing(self) -> None:
        self.assertFalse(EasementLayerService.sync_status_from_easement("E2", {"id": "E2", "status": CLOSED}))
        self.assertEqual(self.feature()["Staatus"], "Eelnõu")

    def test_an_unchanged_status_is_a_match_without_a_write(self) -> None:
        with patch.object(QgsVectorLayer, "startEditing") as start:
            self.assertTrue(EasementLayerService.sync_status_from_easement("E1", {"id": "E1", "status": OPEN}))
        start.assert_not_called()


class SharedSyncKeepsTheAsBuiltBehaviourTest(LayerSyncCase):
    service = AsBuiltLayerService

    def test_the_asbuilt_status_still_goes_through_the_shared_sync(self) -> None:
        self.use_layer(memory_layer("field=ext_job_id:string&field=ext_job_state:integer", ["77", 1], "Teostus"))
        self.assertTrue(AsBuiltLayerService.sync_status_from_task("77", {"status": {"id": "5"}}))
        self.assertEqual(self.feature()["ext_job_state"], 5)


if __name__ == "__main__":
    unittest.main()
