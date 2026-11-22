"""Characterization tests for the three WorksCreateController flows, written against the code
before the shared steps (property link, created callback, feature values) were merged:

- a new work from a map click,
- an existing task placed on the map,
- a pending GIS feature turned into a work.
"""
from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
PLUGIN_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLUGIN_ROOT.parent))
if os.environ.get("QGIS_PREFIX_PATH"):
    sys.path.append(str(Path(os.environ["QGIS_PREFIX_PATH"]) / "python" / "plugins"))

from qgis.core import QgsApplication, QgsPointXY

from Kavitro_dev.Logs.python_fail_logger import PythonFailLogger
from Kavitro_dev.modules.works import works_create_controller as controller_module
from Kavitro_dev.modules.works import works_pending_gis_review as review_module
from Kavitro_dev.modules.works.works_layer_service import WorksLayerService
from Kavitro_dev.python.api_actions import APIModuleActions
from Kavitro_dev.ui.messages_helper import ModernMessageDialog
from Kavitro_dev.ui.window_state.dialog_helpers import DialogHelpers

_APP = QgsApplication.instance() or QgsApplication([], False)
if QgsApplication.instance() is _APP:
    QgsApplication.initQgis()

Controller = controller_module.WorksCreateController
POINT = QgsPointXY(10, 20)
TASK = {
    "id": "77",
    "name": "Server name",
    "createdAt": "2026-01-02T03:04:05",
    "updatedAt": "2026-01-03T00:00:00",
    "startAt": "2026-01-05",
    "dueAt": "2026-01-09",
    "status": {"id": "5", "type": "OPEN", "color": "#4FBF6B"},
    "type": {"id": "3"},
    "members": {"edges": [{"responsible": True, "node": {"displayName": "Mari"}}]},
}


class _Text(str):
    def format(self, *args, **kwargs):
        return f"{self}{sorted(kwargs.items())}"


def _translate(key):
    return _Text(f"T:{key}")


class _Dialog:
    """WorksCreateDialog stand-in: records its arguments and answers like a filled form."""

    Accepted = 1
    accept = True
    made: list = []

    def __init__(self, **kwargs):
        self.kwargs = kwargs
        _Dialog.made.append(self)

    def exec_(self):
        return 1 if _Dialog.accept else 0

    description_text = staticmethod(lambda: "desc")
    title_text = staticmethod(lambda: "Form title")
    selected_type_id = staticmethod(lambda: "form-type")
    selected_status_id = staticmethod(lambda: "")
    selected_status_color = staticmethod(lambda: "#4FBF6B")
    selected_responsible_id = staticmethod(lambda: "u1")
    selected_responsible_label = staticmethod(lambda: "Form user")
    priority_value = staticmethod(lambda: "HIGH")


def expected_fields(task, *, title, type_id, responsible):
    created_at = WorksLayerService.created_date_from_task(task)
    return dict(
        title=title,
        type_id=type_id,
        status_id=WorksLayerService.status_id_from_task(task),
        active=WorksLayerService.active_from_task(task),
        detailed=WorksLayerService.detailed_from_task(task),
        begin_date=WorksLayerService.begin_date_from_task(task) or created_at,
        end_date=WorksLayerService.end_date_from_task(task),
        added_by=responsible,
        added_date=created_at,
        updated_by=responsible,
        update_date=WorksLayerService.updated_date_from_task(task) or created_at,
    )


class _FlowTest(unittest.TestCase):
    def setUp(self):
        _Dialog.accept = True
        _Dialog.made = []
        self.layer = Mock(name="works_layer")
        self.property_feature = Mock(name="property")
        self.on_created = Mock()
        self.p(controller_module, "WorksCreateDialog", _Dialog)
        self.p(controller_module, "iface", None)
        self.p(DialogHelpers, "exit_map_selection_mode")
        self.log = self.p(PythonFailLogger, "log_exception")
        self.warning = self.p(ModernMessageDialog, "show_warning")
        self.info = self.p(ModernMessageDialog, "show_info")
        service = WorksLayerService
        self.resolve_layer = self.p(service, "resolve_main_layer", return_value=self.layer)
        self.p(service, "find_property_feature_at_point", return_value=self.property_feature)
        self.cadastral = self.p(service, "property_cadastral_number", return_value="1:2:3")
        self.p(service, "current_username", return_value="QGIS user")
        self.insert = self.p(service, "insert_work_feature", return_value=(True, ""))
        self.update_feature = self.p(service, "update_existing_work_feature", return_value=(True, ""))
        self.find_by_task = self.p(service, "find_feature_by_task_id", return_value=None)
        self.focus_task = self.p(service, "focus_feature_by_task_id")
        self.p(Controller, "_backend_point_geometry_payload", side_effect=lambda point, layer, status_color=None: {"color": status_color})
        self.create_task = self.p(APIModuleActions, "create_task", return_value="77")
        self.get_task = self.p(APIModuleActions, "get_task_data", return_value=dict(TASK))
        self.update_status = self.p(APIModuleActions, "update_task_status", return_value={"id": "77"})
        self.update_geometry = self.p(APIModuleActions, "update_task_geometry", return_value=True)
        self.resolve_props = self.p(APIModuleActions, "resolve_property_ids_by_cadastral", return_value=(["p1"], []))
        self.associate = self.p(APIModuleActions, "associate_properties")
        self.controller = Controller(lang_manager=Mock(translate=_translate))
        self.controller._on_created = self.on_created
        self.controller._cached_status_options = [{"id": "s", "name": "S", "color": "4FBF6B", "isDefault": True}]
        self.controller._cached_default_status_id = "s"
        self.controller._cached_default_status_color = "4FBF6B"
        self.controller._cached_type_options = [{"id": "t", "label": "Avarii"}]
        self.controller._cached_assignable_users = [{"id": "u1", "displayName": "U"}]
        self.controller._cached_priority_options = [{"value": "", "label": "-"}]
        self.controller._cached_default_responsible_id = "u1"

    def p(self, target, name, *args, **kwargs):
        patcher = patch.object(target, name, *args, **kwargs)
        mock = patcher.start()
        self.addCleanup(patcher.stop)
        return mock

    def events(self):
        return [call.kwargs.get("event") for call in self.log.call_args_list]

    def last_warning(self):
        return self.warning.call_args.args[1]


class NewWorkFlowTest(_FlowTest):
    def run_flow(self):
        self.controller._handle_point_selected(POINT)

    def test_rejected_form_creates_nothing(self):
        _Dialog.accept = False
        self.run_flow()
        self.create_task.assert_not_called()

    def test_form_gets_the_point_property_and_options(self):
        self.controller._allowed_type_ids = ["t"]
        self.run_flow()
        kwargs = _Dialog.made[0].kwargs
        self.assertIs(kwargs["point"], POINT)
        self.assertIs(kwargs["property_feature"], self.property_feature)
        self.assertEqual(kwargs["allowed_type_ids"], ["t"])
        self.assertEqual(kwargs["load_failures"], [])

    def test_backend_task_is_created_from_the_form(self):
        self.run_flow()
        kwargs = self.create_task.call_args.kwargs
        self.assertEqual(
            {k: kwargs[k] for k in ("title", "type_id", "priority", "responsible_id", "status_id", "geometry")},
            {"title": "Form title", "type_id": "form-type", "priority": "HIGH", "responsible_id": "u1",
             "status_id": "", "geometry": {"color": "#4FBF6B"}},
        )
        self.assertRegex(kwargs["start_at"], r"^\d{4}-\d\d-\d\d$")

    def test_failed_create_warns_and_saves_nothing(self):
        self.create_task.return_value = None
        self.run_flow()
        self.assertEqual(self.last_warning(), "T:works_create_failed")
        self.insert.assert_not_called()
        self.create_task.side_effect = RuntimeError("down")
        self.run_flow()
        self.assertIn("works_task_create_failed", self.events())

    def test_success_saves_the_feature_links_the_property_and_reports(self):
        self.run_flow()
        kwargs = self.insert.call_args.kwargs
        self.assertIs(kwargs.pop("layer"), self.layer)
        self.assertIs(kwargs.pop("point"), POINT)
        self.assertEqual(kwargs.pop("task_id"), "77")
        self.assertEqual(kwargs.pop("value_problems"), [])
        self.assertEqual(kwargs, expected_fields(TASK, title="Server name", type_id=3, responsible="Mari"))
        self.resolve_props.assert_called_once_with(["1:2:3"])
        self.associate.assert_called_once_with("task", "77", ["p1"])
        self.on_created.assert_called_once_with("77")
        self.assertEqual(self.info.call_args.args, ("T:Success", "T:works_create_success[('task_id', '77')]"))
        self.warning.assert_not_called()

    def test_form_values_fill_what_the_task_lacks(self):
        task = {"id": "77", "createdAt": "2026-01-02T03:04:05"}
        self.get_task.return_value = task
        self.run_flow()
        kwargs = self.insert.call_args.kwargs
        self.assertEqual((kwargs["title"], kwargs["type_id"], kwargs["added_by"]), ("Form title", "form-type", "Form user"))
        self.assertEqual(kwargs["begin_date"], WorksLayerService.created_date_from_task(task))
        self.assertEqual(kwargs["update_date"], kwargs["added_date"])
        with patch.object(_Dialog, "selected_responsible_label", staticmethod(lambda: "")):
            self.run_flow()
        self.assertEqual(self.insert.call_args.kwargs["updated_by"], "QGIS user")

    def test_selected_status_is_set_after_create_when_the_backend_chose_another(self):
        with patch.object(_Dialog, "selected_status_id", staticmethod(lambda: "other")):
            self.run_flow()
        self.update_status.assert_called_once_with("77", "other")
        self.assertEqual(self.get_task.call_count, 2)
        self.update_status.return_value = None
        with patch.object(_Dialog, "selected_status_id", staticmethod(lambda: "other")):
            self.run_flow()
        self.assertIn("works_task_status_update_failed", self.events())

    def test_geometry_colour_follows_the_created_status(self):
        self.get_task.return_value = dict(TASK, status={"id": "5", "type": "OPEN", "color": "#112233"})
        self.run_flow()
        self.update_geometry.assert_called_once_with("77", {"color": "#112233"})
        self.update_geometry.reset_mock()
        self.get_task.return_value = dict(TASK)
        self.run_flow()
        self.update_geometry.assert_not_called()

    def test_without_cadastral_no_link_is_tried(self):
        self.cadastral.return_value = ""
        self.run_flow()
        self.resolve_props.assert_not_called()
        self.info.assert_called_once()

    def test_unknown_property_and_failed_link_warn(self):
        self.resolve_props.return_value = ([], ["1:2:3"])
        self.run_flow()
        self.assertEqual(self.last_warning(), "T:works_create_property_link_failed[('cadastral', '1:2:3'), ('task_id', '77')]")
        self.associate.assert_not_called()
        self.resolve_props.side_effect = RuntimeError("api")
        self.run_flow()
        self.assertEqual(self.events(), ["works_property_link_failed"])
        self.assertEqual(self.log.call_args.kwargs["extra"], {"task_id": "77", "cadastral": "1:2:3"})
        self.info.assert_not_called()

    def test_failing_callback_is_logged_and_the_success_still_shown(self):
        self.on_created.side_effect = RuntimeError("list gone")
        self.run_flow()
        self.assertEqual(self.events(), ["works_post_create_callback_failed"])
        self.info.assert_called_once()

    def test_map_save_failure_warns_after_link_and_callback(self):
        self.insert.return_value = (False, "locked")
        self.run_flow()
        self.assertEqual(self.last_warning(), "T:works_create_map_save_failed[('error', 'locked'), ('task_id', '77')]")
        self.associate.assert_called_once()
        self.on_created.assert_called_once()
        self.info.assert_not_called()

    def test_missing_layer_after_create_is_a_map_save_failure(self):
        self.resolve_layer.return_value = None
        self.run_flow()
        self.insert.assert_not_called()
        self.assertEqual(self.last_warning(), "T:works_create_map_save_failed[('error', 'T:Error'), ('task_id', '77')]")


class ExistingTaskFlowTest(_FlowTest):
    def run_flow(self, cached=None):
        self.controller._existing_task_id = " 77 "
        self.controller._existing_task_payload = dict(cached or {})
        self.controller._handle_point_selected(POINT)

    def test_state_is_cleared_and_an_unloadable_task_warns(self):
        self.get_task.return_value = None
        self.run_flow()
        self.assertEqual(self.controller._existing_task_id, "")
        self.assertEqual(self.controller._existing_task_payload, {})
        self.assertEqual(self.last_warning(), "T:works_add_existing_on_map_task_load_failed[('task_id', '77')]")
        self.insert.assert_not_called()
        _Dialog.made or self.assertEqual(_Dialog.made, [])

    def test_cached_payload_is_used_when_the_fetch_fails(self):
        self.get_task.return_value = None
        self.run_flow(cached={"id": "77", "name": "Cached"})
        self.assertEqual(self.insert.call_args.kwargs["title"], "Cached")

    def test_missing_layer_and_already_linked_task(self):
        self.resolve_layer.return_value = None
        self.run_flow()
        self.assertEqual(self.last_warning(), "T:works_layer_missing")
        self.resolve_layer.return_value = self.layer
        self.find_by_task.return_value = Mock()
        self.run_flow()
        self.focus_task.assert_called_once_with(self.layer, "77")
        self.assertEqual(self.info.call_args.args[1], "T:works_add_existing_on_map_already_linked[('task_id', '77')]")
        self.insert.assert_not_called()

    def test_success_places_the_task_and_sends_its_geometry(self):
        self.run_flow()
        kwargs = self.insert.call_args.kwargs
        for name in ("layer", "point", "task_id", "value_problems"):
            kwargs.pop(name)
        self.assertEqual(kwargs, expected_fields(TASK, title="Server name", type_id=3, responsible="Mari"))
        self.update_geometry.assert_called_once_with("77", {"color": "#4FBF6B"})
        self.associate.assert_called_once_with("task", "77", ["p1"])
        self.on_created.assert_called_once_with("77")
        self.assertEqual(self.info.call_args.args[1], "T:works_add_existing_on_map_success[('task_id', '77')]")
        self.create_task.assert_not_called()

    def test_task_without_name_type_or_responsible(self):
        self.get_task.return_value = {"id": "77"}
        self.run_flow()
        kwargs = self.insert.call_args.kwargs
        self.assertEqual((kwargs["title"], kwargs["type_id"], kwargs["added_by"]), ("77", None, "QGIS user"))
        self.assertIsNotNone(kwargs["added_date"])
        self.assertEqual(kwargs["begin_date"], kwargs["added_date"])

    def test_map_save_failure_stops_before_the_geometry(self):
        self.insert.return_value = (False, "")
        self.run_flow()
        self.assertEqual(self.last_warning(), "T:works_add_existing_on_map_save_failed[('error', 'T:Error'), ('task_id', '77')]")
        self.update_geometry.assert_not_called()
        self.on_created.assert_not_called()

    def test_failures_are_logged_with_their_own_events(self):
        self.update_geometry.side_effect = RuntimeError("geom")
        self.resolve_props.side_effect = RuntimeError("api")
        self.on_created.side_effect = RuntimeError("cb")
        self.run_flow()
        self.assertEqual(
            self.events(),
            ["works_existing_task_geometry_update_failed", "works_existing_property_link_failed",
             "works_post_add_existing_callback_failed"],
        )
        self.assertEqual(
            self.last_warning(),
            "T:works_add_existing_on_map_property_link_failed[('cadastral', '1:2:3'), ('task_id', '77')]",
        )


class PendingGisFlowTest(_FlowTest):
    def setUp(self):
        super().setUp()
        self.feature = Mock(name="feature")
        self.by_id = self.p(WorksLayerService, "feature_by_id", return_value=self.feature)
        self.payload = self.p(WorksLayerService, "pending_gis_payload_from_feature",
                              return_value={"title": "GIS title", "type_id": "t", "status_id": "s"})
        self.focus = self.p(WorksLayerService, "focus_feature_by_id")
        self.point = self.p(WorksLayerService, "feature_point_in_canvas_crs", return_value=POINT)
        self.owner = Mock(name="owner")

    def run_flow(self):
        return self.controller._open_pending_gis_feature(self.layer, 5, parent_window=self.owner)

    def test_missing_feature_payload_or_point_warn_on_the_owner(self):
        for mock, value in ((self.by_id, None), (self.payload, {}), (self.point, None)):
            with self.subTest(step=mock._mock_name):
                self.warning.reset_mock()
                original = mock.return_value
                mock.return_value = value
                self.assertFalse(self.run_flow())
                mock.return_value = original
                self.assertEqual(self.last_warning(), "T:works_pending_gis_feature_missing")
                self.assertIs(self.warning.call_args.kwargs["parent"], self.owner)
        self.create_task.assert_not_called()

    def test_form_starts_from_the_pending_values(self):
        _Dialog.accept = False
        self.assertFalse(self.run_flow())
        self.focus.assert_called_once_with(self.layer, 5)
        kwargs = _Dialog.made[0].kwargs
        self.assertEqual((kwargs["initial_title"], kwargs["initial_type_id"], kwargs["initial_status_id"]), ("GIS title", "t", "s"))
        self.assertIs(kwargs["parent"], self.owner)

    def test_success_updates_the_existing_feature(self):
        self.assertTrue(self.run_flow())
        kwargs = self.update_feature.call_args.kwargs
        self.assertIs(kwargs.pop("layer"), self.layer)
        self.assertEqual(kwargs.pop("feature_id"), 5)
        self.assertEqual(kwargs.pop("task_id"), "77")
        kwargs.pop("value_problems")
        self.assertEqual(kwargs, expected_fields(TASK, title="Server name", type_id=3, responsible="Mari"))
        self.insert.assert_not_called()
        self.on_created.assert_called_once_with("77")
        self.assertEqual(self.info.call_args.args[1], "T:works_create_success[('task_id', '77')]")

    def test_failures_use_the_pending_events_and_the_owner(self):
        self.resolve_props.side_effect = RuntimeError("api")
        self.on_created.side_effect = RuntimeError("cb")
        self.assertTrue(self.run_flow())
        self.assertEqual(self.events(), ["works_pending_gis_property_link_failed", "works_pending_gis_post_create_callback_failed"])
        self.assertEqual(self.last_warning(), "T:works_create_property_link_failed[('cadastral', '1:2:3'), ('task_id', '77')]")
        self.assertIs(self.warning.call_args.kwargs["parent"], self.owner)

    def test_map_save_failure_returns_false(self):
        self.update_feature.return_value = (False, "busy")
        self.assertFalse(self.run_flow())
        self.assertEqual(self.last_warning(), "T:works_create_map_save_failed[('error', 'busy'), ('task_id', '77')]")
        self.assertIs(self.warning.call_args.kwargs["parent"], self.owner)


class PreloadAnswerTest(_FlowTest):
    def test_only_the_latest_preload_answer_is_kept(self):
        self.controller._preload_request_id = 2
        self.controller._cached_type_options = []
        self.controller._handle_preload_success({"type_options": [{"id": "old", "label": "Old"}]}, 1)
        self.assertEqual(self.controller._cached_type_options, [])
        self.controller._handle_preload_success({"type_options": [{"id": "new", "label": "New"}]}, 2)
        self.assertEqual(self.controller._cached_type_options, [{"id": "new", "label": "New"}])
        self.controller._handle_preload_error("late", 1)
        self.log.assert_not_called()
        self.controller._handle_preload_error("now", 2)
        self.assertEqual(self.events(), ["works_create_dialog_preload_failed"])


class PendingGisReviewTest(_FlowTest):
    def setUp(self):
        super().setUp()
        self.p(Controller, "preload_dialog_data")
        self.scan = self.p(WorksLayerService, "pending_gis_work_features", return_value=[])
        self.review_dialog = self.p(review_module, "WorksPendingGisDialog")

    def test_nothing_pending_is_reported(self):
        self.assertFalse(self.controller.review_pending_gis_features(parent_window=None, progress_anchor=None))
        self.assertEqual(self.info.call_args.args[1], "T:works_pending_gis_none")
        self.review_dialog.assert_not_called()

    def test_rows_get_type_and_status_labels(self):
        self.scan.return_value = [{"type_id": "t", "status_id": "x"}, {"type_id": "?", "status_id": "s"}]
        anchor = Mock()
        anchor.mapToGlobal.side_effect = RuntimeError("deleted")
        self.assertTrue(self.controller.review_pending_gis_features(allowed_type_ids=["t", ""], progress_anchor=anchor))
        rows = self.review_dialog.call_args.kwargs["rows"]
        self.assertEqual(rows, [{"type_id": "t", "status_id": "x", "type_label": "Avarii", "status_label": "x"},
                                {"type_id": "?", "status_id": "s", "type_label": "?", "status_label": "S"}])
        self.assertEqual(self.controller._allowed_type_ids, ["t"])
        self.review_dialog.return_value.exec_.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()
