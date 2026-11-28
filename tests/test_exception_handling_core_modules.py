"""Silent broad handlers in works, projects, settings, python/, feed and the root modules now narrow the type or leave a log line."""
from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import threading
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, Mock, patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
if os.environ.get("QGIS_PREFIX_PATH"):
    sys.path.append(str(Path(os.environ["QGIS_PREFIX_PATH"]) / "python" / "plugins"))

import requests
from qgis.PyQt import sip
from qgis.core import (
    QgsApplication,
    QgsCoordinateReferenceSystem,
    QgsCoordinateTransform,
    QgsFeature,
    QgsField,
    QgsGeometry,
    QgsPointXY,
    QgsProject,
    QgsVectorLayer,
)
from qgis.PyQt.QtCore import QCoreApplication, QDateTime, QEvent, QMetaType
from qgis.PyQt.QtWidgets import QWidget

from Kavitro_dev import dialog as dialog_module
from Kavitro_dev import main as main_module
from Kavitro_dev.Logs.python_fail_logger import PythonFailLogger
from Kavitro_dev.constants.file_paths import _read_metadata_value
from Kavitro_dev.feed.feed_load_engine import FeedLoadEngine
from Kavitro_dev.languages.language_manager import LanguageManager, set_current_language
from Kavitro_dev.languages.translation_keys import TranslationKeys
from Kavitro_dev.module_manager import ModuleManager
from Kavitro_dev.modules.Property.query_coordinator import ConnectedModuleData
from Kavitro_dev.modules.projects import project_board_overview_service as board_module
from Kavitro_dev.modules.projects import projects_card_actions as card_actions_module
from Kavitro_dev.modules.projects.project_board_overview_service import ProjectBoardOverviewService
from Kavitro_dev.utils.project_board_status_rules import ProjectBoardStatusRules
from Kavitro_dev.modules.projects.project_preview_dialog import ProjectPreviewDialog
from Kavitro_dev.modules.projects.projects_card_actions import ProjectCardActions
from Kavitro_dev.modules.projects.projects_layer_service import ProjectsLayerService
from Kavitro_dev.modules.Settings.cards.SettingsModuleCard import SettingsModuleCard
from Kavitro_dev.modules.Settings.cards.SettingsPropertyManagement import PropertyManagementUI
from Kavitro_dev.modules.Settings.GeospatialLayerMapperDialog import GeospatialLayerMapperDialog
from Kavitro_dev.modules.Settings.SettingsUI import SettingsModule
from Kavitro_dev.modules.works import works_create_controller as controller_module

from Kavitro_dev.utils.FilterHelpers.FilterHelper import FilterHelper
from Kavitro_dev.modules.works import works_create_dialog as create_dialog_module
from Kavitro_dev.modules.works.works_sync_service import WorksSyncService
from Kavitro_dev.python import api_client as api_client_module
from Kavitro_dev.python.api_actions import APIModuleActions
from Kavitro_dev.python.responses import JsonResponseHandler
from tools import qgis_repo_release


class LoggedExceptionTestCase(unittest.TestCase):
    """Collects what PythonFailLogger.log_exception receives, without writing real log files."""

    @classmethod
    def setUpClass(cls) -> None:
        # GUI enabled: some classes below build widgets; memory layers need the providers.
        cls.app = QgsApplication.instance() or QgsApplication([], True)
        QgsApplication.initQgis()

    def setUp(self) -> None:
        patcher = patch.object(PythonFailLogger, "log_exception")
        self.log = patcher.start()
        self.addCleanup(patcher.stop)

    def events(self) -> list[str]:
        return [call.kwargs["event"] for call in self.log.call_args_list]

    def modules(self) -> set[str]:
        return {call.kwargs["module"] for call in self.log.call_args_list}


# ---------------------------------------------------------------- root, constants, feed


class RootModulesTest(LoggedExceptionTestCase):
    def test_metadata_value_is_empty_for_a_missing_or_undecodable_file(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            good = Path(folder, "metadata.txt")
            good.write_text("name=Kavitro\nversion=2.12.1\n", encoding="utf-8")
            broken = Path(folder, "broken.txt")
            broken.write_bytes(b"version=\xff\xfe\n")

            self.assertEqual(_read_metadata_value(str(good), "version"), "2.12.1")
            self.assertEqual(_read_metadata_value(str(broken), "version"), "")
            self.assertEqual(_read_metadata_value(str(Path(folder, "missing.txt")), "version"), "")

    def test_only_a_deleted_owner_makes_a_token_inactive(self) -> None:
        deleted_owner = Mock(_activated=True, _active_token=3)
        deleted_owner.is_token_active.side_effect = RuntimeError("wrapped C/C++ object has been deleted")
        engine = FeedLoadEngine(list).attach(parent_ui=deleted_owner)
        self.assertFalse(engine._is_token_active(3))

        # A parent without the contract method is a coding error and must not turn into "inactive".
        engine = FeedLoadEngine(list).attach(parent_ui=SimpleNamespace(_activated=True, _active_token=3))
        with self.assertRaises(AttributeError):
            engine._is_token_active(3)

    def test_dialog_deleted_check_tells_a_deleted_widget_from_a_plain_object(self) -> None:
        widget = QWidget()
        self.assertFalse(main_module.WildCodePlugin._is_dialog_deleted(widget))
        sip.delete(widget)
        self.assertTrue(main_module.WildCodePlugin._is_dialog_deleted(widget))
        self.assertTrue(main_module.WildCodePlugin._is_dialog_deleted(None))
        # sip.isdeleted refuses objects that are not wrapped Qt objects; that is "not deleted".
        self.assertFalse(main_module.WildCodePlugin._is_dialog_deleted(object()))

    def test_failed_widget_lookup_is_logged_and_no_widget_is_registered(self) -> None:
        class BrokenModule:
            def get_widget(self):
                raise ValueError("no widget yet")

        instance = BrokenModule()

        self.assertIsNone(ModuleManager._get_widget_safe(instance))
        self.assertEqual(self.events(), ["module_widget_build_failed"])
        self.assertEqual(self.log.call_args.kwargs["extra"], {"module_class": "BrokenModule"})

    def test_failed_footer_refresh_is_logged_and_the_window_goes_on(self) -> None:
        window = SimpleNamespace(
            footer_widget=Mock(refresh_versions=Mock(side_effect=RuntimeError("deleted"))),
            _sync_map_canvas_overlays=Mock(),
        )

        with patch.object(dialog_module.SessionManager, "is_session_valid", return_value=True):
            dialog_module.PluginDialog._refresh_session_dependent_ui(window)

        window._sync_map_canvas_overlays.assert_called_once_with()
        self.assertEqual(self.events(), ["footer_versions_refresh_failed"])
        self.assertEqual(self.modules(), {"ui"})


# ---------------------------------------------------------------- settings


def _memory_layer(crs: str = "EPSG:3301") -> QgsVectorLayer:
    return QgsVectorLayer(f"Point?crs={crs}&field=name:string", "layer", "memory")


class GeospatialLayerMapperTest(LoggedExceptionTestCase):
    def test_coordinates_outside_the_target_crs_are_logged_and_give_no_geometry(self) -> None:
        transform = QgsCoordinateTransform(
            QgsCoordinateReferenceSystem("EPSG:4326"),
            QgsCoordinateReferenceSystem("EPSG:3301"),
            QgsProject.instance().transformContext(),
        )
        geometry = QgsGeometry.fromWkt("POINT(1000000 1000000)")

        result = GeospatialLayerMapperDialog._transformed_geometry(geometry, transform)

        # The feature must not be written; the source geometry stays untouched.
        self.assertIsNone(result)
        self.assertEqual(geometry.asWkt(), "Point (1000000 1000000)")
        self.assertEqual(self.events(), ["geospatial_mapper_geometry_transform_failed"])
        self.assertEqual(self.modules(), {"settings"})

    def test_valid_coordinates_are_transformed_without_a_log_line(self) -> None:
        transform = QgsCoordinateTransform(
            QgsCoordinateReferenceSystem("EPSG:4326"),
            QgsCoordinateReferenceSystem("EPSG:3301"),
            QgsProject.instance().transformContext(),
        )

        result = GeospatialLayerMapperDialog._transformed_geometry(QgsGeometry.fromWkt("POINT(24 58)"), transform)

        self.assertAlmostEqual(result.asPoint().x(), 500000.0, delta=1.0)
        self.assertEqual(GeospatialLayerMapperDialog._transformed_geometry(None, transform), None)
        self.assertEqual(
            GeospatialLayerMapperDialog._transformed_geometry(QgsGeometry.fromWkt("POINT(1 1)"), None).asWkt(),
            "Point (1 1)",
        )
        self.log.assert_not_called()

    def test_missing_layer_gives_no_transform_and_a_log_line(self) -> None:
        self.assertIsNone(GeospatialLayerMapperDialog._build_geometry_transform(None, _memory_layer()))

        self.assertEqual(self.events(), ["geospatial_mapper_transform_build_failed"])

    def test_different_crs_gives_a_transform_and_equal_crs_none(self) -> None:
        wgs = _memory_layer("EPSG:4326")
        estonian = _memory_layer("EPSG:3301")

        self.assertIsNotNone(GeospatialLayerMapperDialog._build_geometry_transform(wgs, estonian))
        self.assertIsNone(GeospatialLayerMapperDialog._build_geometry_transform(estonian, _memory_layer("EPSG:3301")))
        self.log.assert_not_called()

    def test_unexpected_error_types_are_not_swallowed_by_the_narrowed_handlers(self) -> None:
        broken_layer = Mock(spec=QgsVectorLayer)
        broken_layer.crs.side_effect = ValueError("not a crs problem")
        with self.assertRaises(ValueError):
            GeospatialLayerMapperDialog._build_geometry_transform(broken_layer, _memory_layer())

        broken_field = Mock()
        broken_field.type.side_effect = ValueError("not a field problem")
        with self.assertRaises(ValueError):
            GeospatialLayerMapperDialog._coerce_value_for_field(broken_field, "1", [])

    def test_number_that_cannot_be_converted_becomes_none_and_a_deleted_layer_a_dash(self) -> None:
        field = QgsField("count", QMetaType.Type.Int)
        problems = []
        self.assertEqual(GeospatialLayerMapperDialog._coerce_value_for_field(field, " 12 ", problems), 12)
        self.assertIsNone(GeospatialLayerMapperDialog._coerce_value_for_field(field, "abc", problems))
        # The rejected value is reported, not dropped silently.
        self.assertEqual([problem.raw_value for problem in problems], ["abc"])

        deleted_layer = MagicMock(spec=QgsVectorLayer)
        deleted_layer.name.side_effect = RuntimeError("wrapped C/C++ object has been deleted")
        self.assertEqual(GeospatialLayerMapperDialog._layer_label(deleted_layer), "-")

    def test_field_with_a_broken_type_call_is_not_compatible(self) -> None:
        field = QgsField("count", QMetaType.Type.Int)
        stub = Mock()
        stub.type.side_effect = AttributeError("no type")

        self.assertFalse(GeospatialLayerMapperDialog._field_types_compatible(field, stub))
        self.assertTrue(GeospatialLayerMapperDialog._field_types_compatible(field, QgsField("n", QMetaType.Type.Int)))


class SettingsModuleTest(LoggedExceptionTestCase):
    def test_failing_dirty_check_is_logged_and_assumes_unsaved_changes(self) -> None:
        window = SimpleNamespace(
            logic=Mock(has_unsaved_changes=Mock(side_effect=AttributeError("gone"))),
            _any_module_dirty=Mock(return_value=False),
        )

        self.assertTrue(SettingsModule.has_unsaved_changes(window))
        self.assertEqual(self.events(), ["settings_unsaved_check_failed"])
        self.assertEqual(self.modules(), {"settings"})

    def test_clean_state_is_reported_without_a_log_line(self) -> None:
        window = SimpleNamespace(
            logic=Mock(has_unsaved_changes=Mock(return_value=False)),
            _any_module_dirty=Mock(return_value=False),
        )

        self.assertFalse(SettingsModule.has_unsaved_changes(window))
        self.log.assert_not_called()


class SettingsModuleCardTest(LoggedExceptionTestCase):
    def setUp(self) -> None:
        super().setUp()
        set_current_language("en")
        self.addCleanup(set_current_language, "et")
        self.lang = LanguageManager()
        # Never write the real settings of the profile; one test asserts the build does not try.
        writes = patch("qgis.core.QgsSettings.setValue")
        self.setting_writes = writes.start()
        self.addCleanup(writes.stop)
        self.card = SettingsModuleCard(
            self.lang, "works", "Works", supports_types=True, supports_statuses=True, supports_tags=False,
        )
        self.addCleanup(self.dispose)

    def dispose(self) -> None:
        self.card.hide()
        self.card.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)

    def test_building_the_card_writes_no_settings(self) -> None:
        self.setting_writes.assert_not_called()

    def test_status_and_type_filters_use_the_language_of_the_card(self) -> None:
        self.assertEqual(self.card._status_filter_widget.selector.toolTip(), self.lang.translate(TranslationKeys.STATUS_FILTER))
        self.assertEqual(self.card._type_filter_widget.type_combo.toolTip(), self.lang.translate(TranslationKeys.TYPE_FILTER))

    def test_filter_that_fails_to_clear_is_logged_and_the_others_still_clear(self) -> None:
        self.card._status_filter_widget.clear_data = Mock(side_effect=RuntimeError("deleted"))
        self.card._type_filter_widget.clear_data = Mock()

        self.card.on_settings_deactivate()

        self.card._type_filter_widget.clear_data.assert_called_once_with()
        self.assertEqual(self.events(), ["settings_card_clear_data_failed"])
        self.assertEqual(self.log.call_args.kwargs["extra"], {"widget": type(self.card._status_filter_widget).__name__})


class SettingsPropertyManagementTest(LoggedExceptionTestCase):
    def test_deleted_import_layer_is_counted_without_a_cache_hit(self) -> None:
        card = SimpleNamespace(_shp_feature_cache={"layer_id": "x", "count": 3, "ts": 0.0})
        layer = Mock()
        layer.id.side_effect = RuntimeError("wrapped C/C++ object has been deleted")
        layer.getFeatures.return_value = iter([1, 2, 3, 4])

        self.assertEqual(PropertyManagementUI._get_shp_feature_count_cached(card, layer), 3)

        card = SimpleNamespace(_shp_feature_cache={})
        layer.id.side_effect = ValueError("not a deleted layer")
        with self.assertRaises(ValueError):
            PropertyManagementUI._get_shp_feature_count_cached(card, layer)


# ---------------------------------------------------------------- projects


class ProjectBoardTest(LoggedExceptionTestCase):
    def test_failed_property_request_is_logged_with_the_property_and_the_board_goes_on(self) -> None:
        def fetch(property_id):
            if property_id == "p-1":
                raise RuntimeError("[WC-API] timeout")
            return ConnectedModuleData(nodes_by_module={"works": [{"id": "7", "name": "Töö", "status": {"type": "OPEN"}}]})

        with (
            patch.object(board_module.PropertyLookupService, "property_id_by_cadastral", side_effect=["p-1", "p-2"]),
            patch.object(board_module.PropertiesConnectedElementsQueries, "fetch_all_module_data", side_effect=fetch),
            patch.object(ProjectBoardOverviewService, "_tracked_modules", return_value=["works"]),
        ):
            items, failed_modules = ProjectBoardOverviewService._load_connected_module_items(["1:1", "2:2"], exclude_project_id="")

        self.assertEqual([item["id"] for item in items["works"]], ["7"])
        self.assertEqual(failed_modules, ["works"])
        self.assertEqual(self.events(), ["project_board_connected_items_failed"])
        self.assertEqual(self.modules(), {"project"})
        self.assertEqual(self.log.call_args.kwargs["extra"], {"property_id": "p-1"})

    def test_status_rows_of_a_text_that_is_not_json_are_empty(self) -> None:
        self.assertEqual(ProjectBoardStatusRules.parse_not_started_status_rows("{not json"), [])
        rows = ProjectBoardStatusRules.parse_not_started_status_rows('[{"statusId": "1", "statusName": "Uus"}]')
        self.assertEqual(rows, [{"statusId": "1", "statusName": "Uus"}])


def _editing_layer(*, update_fields_error: Exception) -> MagicMock:
    """A layer whose edit session fails halfway and whose rollBack fails too."""
    layer = MagicMock(spec=QgsVectorLayer)
    layer.isValid.return_value = True
    layer.isEditable.side_effect = [False, True]
    layer.startEditing.return_value = True
    layer.addAttribute.return_value = True
    layer.updateFields.side_effect = update_fields_error
    layer.rollBack.side_effect = RuntimeError("rollback boom")
    return layer


class ProjectsLayerServiceTest(LoggedExceptionTestCase):
    def test_failed_rollback_is_logged_next_to_the_original_error(self) -> None:
        layer = _editing_layer(update_fields_error=RuntimeError("boom"))
        layer.dataProvider.return_value.addAttributes.return_value = True
        with patch.object(ProjectsLayerService, "_field_map", return_value={}):
            result = ProjectsLayerService._ensure_custom_fields(layer)

        self.assertEqual(result, (False, "boom"))
        self.assertEqual(
            self.events(),
            ["project_layer_ensure_fields_rollback_failed", "project_layer_ensure_fields_failed"],
        )
        self.assertEqual(self.modules(), {"project"})

    def test_added_by_failure_is_logged_and_saving_goes_on(self) -> None:
        layer = MagicMock(spec=QgsVectorLayer)
        layer.isValid.return_value = True
        layer.isEditable.return_value = True
        layer.updateFeature.return_value = False
        feature = Mock()
        feature.attribute.side_effect = KeyError("Sisestaja")

        with (
            patch.object(ProjectsLayerService, "_ensure_custom_fields", return_value=(True, "")),
            patch.object(ProjectsLayerService, "_feature_by_id", return_value=feature),
            patch.object(ProjectsLayerService, "_resolve_first_field_name", return_value="Sisestaja"),
            patch.object(ProjectsLayerService, "_set_attr_if_present"),
            patch.object(ProjectsLayerService, "current_username", return_value="kasutaja"),
        ):
            result = ProjectsLayerService.attach_backend_item_to_feature(
                layer=layer, feature_id=3, item_id="p-1", item_data={"name": "Projekt"}
            )

        self.assertEqual(result, (False, ProjectsLayerService._layer_text(TranslationKeys.LAYER_EDIT_UPDATE_FAILED)))
        self.assertEqual(self.events(), ["project_added_fields_set_failed"])
        self.assertEqual(self.log.call_args.kwargs["extra"], {"item_id": "p-1"})

    def test_field_without_a_type_keeps_the_raw_value(self) -> None:
        stub = Mock()
        stub.type.side_effect = RuntimeError("wrapped C/C++ object has been deleted")

        self.assertEqual(ProjectsLayerService.coerce_value_for_field(stub, "text"), "text")
        self.log.assert_not_called()


class ProjectPreviewNarrowedHandlersTest(LoggedExceptionTestCase):
    def test_property_label_falls_back_to_the_number_when_the_feature_lacks_the_fields(self) -> None:
        layer = _memory_layer()
        feature = QgsFeature(layer.fields())

        self.assertEqual(ProjectPreviewDialog._format_property_label(None, "1:1", feature), "1:1")
        self.assertEqual(ProjectPreviewDialog._format_property_label(None, " 1:1 "), "1:1")

    def test_other_errors_of_a_feature_lookup_are_not_swallowed(self) -> None:
        feature = MagicMock()
        feature.__getitem__.side_effect = TypeError("not a feature")

        with self.assertRaises(TypeError):
            ProjectPreviewDialog._format_property_label(None, "1:1", feature)


class ProjectCardActionsTest(LoggedExceptionTestCase):
    def test_deleted_preview_dialog_is_replaced_by_a_new_one(self) -> None:
        host = Mock(item_data={"id": "1"}, lang_manager=Mock())
        actions = ProjectCardActions(host)
        actions._preview_dialog = Mock()
        actions._preview_dialog.isVisible.side_effect = RuntimeError("wrapped C/C++ object has been deleted")

        with patch.object(card_actions_module, "ProjectPreviewDialog") as dialog_class:
            actions.open_preview()

        self.assertIs(actions._preview_dialog, dialog_class.return_value)
        dialog_class.return_value.show.assert_called_once_with()


# ---------------------------------------------------------------- works


class WorksCreateOptionLoadsTest(LoggedExceptionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.controller = controller_module.WorksCreateController()

    def test_every_failed_option_load_is_logged_and_the_preload_payload_stays_empty(self) -> None:
        with (
            patch.object(FilterHelper, "get_filter_edges_by_key_and_module", side_effect=RuntimeError("a")),
            patch.object(APIModuleActions, "get_assignable_users", side_effect=RuntimeError("b")),
            patch.object(APIModuleActions, "get_current_user_id", side_effect=RuntimeError("c")),
            patch.object(APIModuleActions, "get_module_status_options", side_effect=RuntimeError("d")),
            patch.object(APIModuleActions, "get_task_priority_options", side_effect=RuntimeError("e")),
        ):
            payload = self.controller._fetch_preload_payload()

        self.assertEqual(
            self.events(),
            [
                "works_create_type_options_load_failed",
                "works_create_assignable_users_load_failed",
                "works_create_default_responsible_load_failed",
                "works_create_status_options_load_failed",
                "works_create_priority_options_load_failed",
            ],
        )
        self.assertEqual(self.modules(), {"works"})
        self.assertEqual(payload["type_options"], [])
        self.assertEqual(payload["assignable_users"], [])
        self.assertEqual(payload["default_responsible_id"], "")
        self.assertEqual(payload["status_options"], [])
        self.assertEqual(payload["priority_options"], [])

    def test_failed_lookups_after_the_preload_are_logged_too(self) -> None:
        with (
            patch.object(FilterHelper, "get_filter_edges_by_key_and_module", side_effect=RuntimeError("a")),
            patch.object(APIModuleActions, "get_module_status_options", side_effect=RuntimeError("d")),
        ):
            self.assertEqual(self.controller._resolve_type_options(), [])
            self.assertEqual(self.controller._resolve_status_options(), [])

        self.assertEqual(
            self.events(),
            ["works_create_type_options_load_failed", "works_create_status_options_load_failed"],
        )

    def test_dialog_without_preloaded_types_logs_the_failed_lookup_and_shows_the_hint(self) -> None:
        with (
            patch.object(create_dialog_module.FilterHelper, "get_filter_edges_by_key_and_module", side_effect=RuntimeError("a")),
            patch.object(create_dialog_module.WorksLayerService, "property_display_text", return_value=""),
        ):
            dialog = create_dialog_module.WorksCreateDialog(
                point=QgsPointXY(1, 1),
                property_feature=None,
                type_options=[],
                assignable_users=[],
                status_options=[],
                priority_options=[],
            )
        self.addCleanup(self.dispose, dialog)

        self.assertIn("works_create_type_options_load_failed", self.events())
        self.assertFalse(dialog._create_btn.isEnabled())

    @staticmethod
    def dispose(widget) -> None:
        widget.hide()
        widget.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)


class WorksSyncServiceTest(LoggedExceptionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.service = WorksSyncService()
        self.addCleanup(self.service.deleteLater)

    def test_detach_of_a_layer_that_was_never_connected_is_quiet(self) -> None:
        self.service._layer = _memory_layer()

        self.service.detach()

        self.assertIsNone(self.service._layer)
        self.log.assert_not_called()

    def test_features_without_the_task_id_field_are_skipped(self) -> None:
        layer = QgsVectorLayer("Point?crs=EPSG:3301&field=task_id:string", "works", "memory")
        with_id = QgsFeature(layer.fields())
        with_id["task_id"] = " t-1 "
        blank = QgsFeature(layer.fields())

        by_task = WorksSyncService._feature_ids_by_task_id([with_id, blank], "task_id")
        missing_field = WorksSyncService._feature_ids_by_task_id([with_id], "no_such_field")

        self.assertEqual(by_task, {"t-1": [with_id.id()]})
        self.assertEqual(missing_field, {})

    def test_deleted_layer_has_no_name_and_is_not_editable(self) -> None:
        layer = MagicMock(spec=QgsVectorLayer)
        layer.name.side_effect = RuntimeError("wrapped C/C++ object has been deleted")
        layer.isEditable.side_effect = RuntimeError("wrapped C/C++ object has been deleted")

        self.assertEqual(WorksSyncService._layer_name(layer), "")
        self.assertFalse(self.service._is_layer_editable(layer, event="works_sync_test"))

    def test_invalid_date_time_is_not_a_timestamp(self) -> None:
        self.assertIsNone(WorksSyncService._normalize_datetime_value(QDateTime()))
        valid = WorksSyncService._normalize_datetime_value(QDateTime(2024, 5, 6, 7, 8, 9))
        self.assertEqual((valid.year, valid.month, valid.second), (2024, 5, 9))

    def test_failed_geometry_comparison_is_logged_and_counts_as_different(self) -> None:
        existing = QgsGeometry.fromWkt("POINT(1 1)")
        new = QgsGeometry.fromWkt("POINT(1 1)")
        self.assertTrue(WorksSyncService._geometries_equal(existing, new))
        self.log.assert_not_called()

        broken = MagicMock(spec=QgsGeometry)
        broken.isEmpty.return_value = False
        broken.constGet.side_effect = RuntimeError("geos failure")

        self.assertFalse(WorksSyncService._geometries_equal(broken, new))
        self.assertEqual(self.events(), ["works_geometry_compare_failed"])
        self.assertEqual(self.modules(), {"works"})


# ---------------------------------------------------------------- python, tools


class ApiResponseTest(LoggedExceptionTestCase):
    @staticmethod
    def _response(body: bytes) -> requests.Response:
        response = requests.Response()
        response.status_code = 502
        response._content = body
        return response

    def test_gateway_page_instead_of_json_is_logged_and_gives_an_empty_answer(self) -> None:
        result = JsonResponseHandler.get_raw_json(self._response(b"<html>Bad gateway</html>"))

        self.assertEqual(result, {})
        self.assertEqual(self.events(), ["api_response_not_json"])
        self.assertEqual(self.modules(), {"api"})

    def test_json_body_and_plain_dict_are_returned_without_a_log_line(self) -> None:
        self.assertEqual(JsonResponseHandler.get_raw_json(self._response(b'{"data": {}}')), {"data": {}})
        self.assertEqual(JsonResponseHandler.get_raw_json({"a": 1}), {"a": 1})
        self.assertEqual(JsonResponseHandler.get_raw_json(None), {})
        self.log.assert_not_called()


class ApiClientErrorTextTest(LoggedExceptionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.client = SimpleNamespace(lang=Mock(translate=Mock(return_value="Network error {error}")))

    def extract(self, errors):
        return api_client_module.APIClient._extract_error_message(self.client, errors)

    def test_message_of_the_first_error_wins(self) -> None:
        self.assertEqual(self.extract([{"message": "Boom"}, {"message": "Later"}]), "Boom")
        self.assertEqual(self.extract(["plain"]), "plain")

    def test_unexpected_error_shapes_are_serialised_or_replaced_by_the_network_text(self) -> None:
        self.assertEqual(self.extract([]), "[]")
        self.assertEqual(self.extract({"message": "not a list"}), '{"message": "not a list"}')
        self.assertEqual(self.extract(None), "null")
        self.assertEqual(self.extract({"a": object()}), "Network error ")

    def test_gui_thread_check_tells_the_gui_thread_from_a_worker(self) -> None:
        self.assertTrue(api_client_module.APIClient._on_gui_thread())

        seen: list[bool] = []
        worker = threading.Thread(target=lambda: seen.append(api_client_module.APIClient._on_gui_thread()))
        worker.start()
        worker.join(5)

        self.assertEqual(seen, [False])


class ReleaseToolTest(unittest.TestCase):
    def test_missing_gh_or_failed_gh_or_bad_json_give_no_release_notes(self) -> None:
        failures = [
            subprocess.CalledProcessError(1, "gh"),
            FileNotFoundError("gh"),
            None,  # stdout that is not JSON
        ]
        for failure in failures:
            with self.subTest(failure=repr(failure)):
                completed = SimpleNamespace(stdout="not json")
                with patch.object(
                    qgis_repo_release.subprocess,
                    "run",
                    side_effect=failure,
                    return_value=completed,
                ):
                    self.assertEqual(qgis_repo_release._fetch_github_release_notes("v1.0.0"), ("", ""))

    def test_release_notes_are_read_from_the_gh_answer(self) -> None:
        completed = SimpleNamespace(stdout='{"name": " Title ", "body": " Body "}')
        with patch.object(qgis_repo_release.subprocess, "run", return_value=completed):
            self.assertEqual(qgis_repo_release._fetch_github_release_notes("v1.0.0"), ("Title", "Body"))

    def test_unreadable_plugins_xml_gives_no_changelog(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            broken = Path(folder, "plugins.xml")
            broken.write_text("<plugins><pyqgis_plugin", encoding="utf-8")

            self.assertEqual(qgis_repo_release._extract_changelog_from_plugins_xml(broken, "Kavitro"), "")
            self.assertEqual(
                qgis_repo_release._extract_changelog_from_plugins_xml(Path(folder, "missing.xml"), "Kavitro"), ""
            )
            self.assertEqual(qgis_repo_release._extract_changelog_from_plugins_xml(Path(folder), "Kavitro"), "")


if __name__ == "__main__":
    unittest.main()
