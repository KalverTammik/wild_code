"""Silent broad handlers in the shared layer service, the map tools, the module switch and the message dialog.

Each handler now either names the errors its try body can raise, or leaves a log line before the same fallback.
"""
from __future__ import annotations

import os
import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, Mock, patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
if os.environ.get("QGIS_PREFIX_PATH"):
    sys.path.append(str(Path(os.environ["QGIS_PREFIX_PATH"]) / "python" / "plugins"))

from PyQt5.QtCore import QCoreApplication, QEvent, QVariant
from qgis.core import (
    QgsApplication,
    QgsCoordinateReferenceSystem,
    QgsFeature,
    QgsField,
    QgsGeometry,
    QgsPointXY,
    QgsRectangle,
    QgsVectorLayer,
    QgsWkbTypes,
)

from Kavitro_dev.constants.cadastral_fields import Katastriyksus
from Kavitro_dev.Logs.python_fail_logger import PythonFailLogger
from Kavitro_dev.Logs.switch_logger import SwitchLogger
from Kavitro_dev.modules.asbuilt.asbuilt_layer_service import AsBuiltLayerService
from Kavitro_dev.modules.works import works_layer_service as works_module
from Kavitro_dev.modules.works.works_layer_service import WorksLayerService
from Kavitro_dev.utils import messagesHelper as messages_module
from Kavitro_dev.utils import moduleSwitchHelper as switch_module
from Kavitro_dev.utils.layers import module_layer_service_base as base_module
from Kavitro_dev.utils.MapTools import module_feature_controllers as controllers_module
from Kavitro_dev.utils.MapTools import module_identify_tool as identify_module
from Kavitro_dev.utils.MapTools.MapHelpers import FeatureActions, MapHelpers
from Kavitro_dev.utils.MapTools.module_feature_controllers import (
    FeatureLinkResult,
    ModuleFeatureAttachController,
    ModuleFeatureDrawController,
    ModuleFeatureEditController,
)
from Kavitro_dev.utils.MapTools.module_identify_tool import ModuleIdentifyToolController
from Kavitro_dev.utils.messagesHelper import ModernMessageDialog
from Kavitro_dev.utils.moduleSwitchHelper import ModuleSwitchHelper

maphelpers_module = sys.modules[MapHelpers.__module__]


def valid_layer(geometry=QgsWkbTypes.PointGeometry) -> MagicMock:
    layer = MagicMock(spec=QgsVectorLayer)
    layer.isValid.return_value = True
    layer.geometryType.return_value = geometry
    return layer


def memory_layer(fields: str = "") -> QgsVectorLayer:
    return QgsVectorLayer("Point?crs=EPSG:3301" + fields, "test", "memory")


def feature_with_geometry(**geometry_options) -> Mock:
    feature = Mock()
    geometry = feature.geometry.return_value
    geometry.isEmpty.return_value = False
    geometry.contains.return_value = geometry_options.get("contains", False)
    geometry.intersects.return_value = geometry_options.get("intersects", False)
    geometry.distance.return_value = geometry_options.get("distance", 0.0)
    return feature


class LoggedCase(unittest.TestCase):
    """Collects what PythonFailLogger.log_exception receives; no dialog of a regression can open a window."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QgsApplication.instance() or QgsApplication([], False)

    def setUp(self) -> None:
        patcher = patch.object(PythonFailLogger, "log_exception")
        self.log = patcher.start()
        self.addCleanup(patcher.stop)
        for name in ("show_warning", "show_info"):
            dialog_patcher = patch.object(ModernMessageDialog, name)
            setattr(self, name, dialog_patcher.start())
            self.addCleanup(dialog_patcher.stop)

    def events(self) -> list[str]:
        return [call.kwargs["event"] for call in self.log.call_args_list]

    def modules(self) -> set[str]:
        return {call.kwargs["module"] for call in self.log.call_args_list}


# ---------------------------------------------------------------- utils/layers/module_layer_service_base.py
class LayerServiceBaseTest(LoggedCase):
    SERVICE = AsBuiltLayerService  # inherits every helper below unchanged

    @classmethod
    def find(cls, features, *, geometry=QgsWkbTypes.PolygonGeometry, units=1.0, **options):
        layer = valid_layer(geometry)
        layer.getFeatures.return_value = iter(features)
        interface = Mock()
        interface.mapCanvas.return_value.mapUnitsPerPixel.return_value = units
        with patch.object(base_module, "iface", interface), patch.object(
            cls.SERVICE, "_point_in_layer_crs", side_effect=lambda point, _layer: point
        ):
            return cls.SERVICE.find_feature_at_point(QgsPointXY(10, 20), layer=layer, **options), layer

    def test_date_beyond_the_utc_range_keeps_its_clock_time(self) -> None:
        # Converting 23:59 at UTC-14 on the last day of year 9999 overflows the datetime range.
        self.assertEqual(
            self.SERVICE.parse_backend_datetime("9999-12-31T23:59:59-14:00"),
            datetime(9999, 12, 31, 23, 59, 59),
        )

    def test_zone_conversion_errors_of_the_os_fall_back_to_the_clock_time(self) -> None:
        for error in (OSError("bad time"), ValueError("bad time"), OverflowError("range")):
            with self.subTest(error=type(error).__name__):
                parsed = MagicMock()
                parsed.tzinfo = timezone.utc
                parsed.astimezone.side_effect = error
                parsed.replace.return_value = "naive"
                with patch.object(base_module, "datetime") as datetime_class:
                    datetime_class.fromisoformat.return_value = parsed
                    self.assertEqual(self.SERVICE.parse_backend_datetime("2026-01-01T00:00:00Z"), "naive")

    def test_other_errors_of_the_zone_conversion_are_not_hidden(self) -> None:
        parsed = MagicMock()
        parsed.tzinfo = timezone.utc
        parsed.astimezone.side_effect = RuntimeError("not a time error")
        with patch.object(base_module, "datetime") as datetime_class:
            datetime_class.fromisoformat.return_value = parsed
            with self.assertRaises(RuntimeError):
                self.SERVICE.parse_backend_datetime("2026-01-01T00:00:00Z")

    def test_unusable_search_radius_searches_two_map_units(self) -> None:
        for radius in ("far", None, 10 ** 400):
            with self.subTest(radius=repr(radius)[:20]):
                _found, layer = self.find([], radius_multiplier=radius)
                self.assertEqual(layer.getFeatures.call_args.args[0].filterRect().width(), 4.0)

    def test_point_whose_distance_cannot_be_measured_is_skipped(self) -> None:
        broken, near = feature_with_geometry(), feature_with_geometry(distance=1.0)
        broken.geometry.return_value.distance.side_effect = TypeError("not a geometry")
        found, _layer = self.find([broken, near], geometry=QgsWkbTypes.PointGeometry)
        self.assertIs(found, near)
        self.log.assert_not_called()

    def test_polygon_that_cannot_be_tested_is_skipped(self) -> None:
        broken, inside = feature_with_geometry(), feature_with_geometry(contains=True)
        broken.geometry.return_value.contains.side_effect = TypeError("not a geometry")
        found, _layer = self.find([broken, inside])
        self.assertIs(found, inside)
        self.log.assert_not_called()

    def test_unexpected_geometry_error_is_logged_and_finds_nothing(self) -> None:
        broken = feature_with_geometry()
        broken.geometry.return_value.distance.side_effect = RuntimeError("geometry deleted")
        found, _layer = self.find([broken, feature_with_geometry(distance=1.0)], geometry=QgsWkbTypes.PointGeometry)
        self.assertIsNone(found)
        self.assertEqual(self.events(), ["asbuilt_feature_at_point_failed"])


# ---------------------------------------------------------------- modules/works/works_layer_service.py
class WorksLayerServiceTest(LoggedCase):
    FIELD_MAP = {WorksLayerService.FIELD_DETAILED.lower(): WorksLayerService.FIELD_DETAILED}

    def test_failed_rollback_while_adding_required_fields_is_logged(self) -> None:
        layer = valid_layer()
        layer.isEditable.side_effect = [False, True]
        layer.startEditing.return_value = True
        layer.updateFields.side_effect = RuntimeError("boom")
        layer.rollBack.side_effect = RuntimeError("rollback boom")
        with patch.object(WorksLayerService, "_field_map", return_value={}), patch.object(
            WorksLayerService, "_incompatible_required_fields", return_value=[]
        ):
            result = WorksLayerService._prepare_required_fields(layer)

        self.assertEqual(result, (False, "boom"))
        self.assertEqual(
            self.events(),
            [
                "works_layer_prepare_required_fields_rollback_failed",
                "works_layer_prepare_required_fields_failed",
            ],
        )
        self.assertEqual(self.modules(), {"works"})

    def test_property_search_radius_falls_back_when_it_is_not_a_number(self) -> None:
        for radius in ("far", None, 10 ** 400):
            with self.subTest(radius=repr(radius)[:20]):
                layer = valid_layer()
                layer.getFeatures.return_value = iter([])
                interface = Mock()
                interface.mapCanvas.return_value.mapUnitsPerPixel.return_value = 1.0
                with patch.object(works_module, "iface", interface), patch.object(
                    works_module.ActiveLayersHelper, "resolve_main_property_layer", return_value=layer
                ), patch.object(WorksLayerService, "_point_in_layer_crs", side_effect=lambda point, _layer: point):
                    WorksLayerService.find_property_feature_at_point(QgsPointXY(10, 20), radius_multiplier=radius)
                self.assertEqual(layer.getFeatures.call_args.args[0].filterRect().width(), 4.0)

    def test_property_without_an_address_field_has_no_address(self) -> None:
        feature = Mock()
        feature.attribute.side_effect = KeyError(Katastriyksus.l_aadress)
        self.assertEqual(WorksLayerService.property_address(feature), "")

    def test_property_text_skips_the_fields_the_layer_does_not_have(self) -> None:
        present = {Katastriyksus.tunnus: "12345:001:0001", Katastriyksus.ay_nimi: " Tamme "}

        def attribute(name):
            return present[name]  # a missing name raises KeyError like QgsFeature.attribute

        feature = Mock()
        feature.attribute.side_effect = attribute
        text = WorksLayerService.property_display_text(feature, lang_manager=Mock())
        self.assertEqual(text, "12345:001:0001 · Tamme")

    def test_feature_id_that_is_not_finite_finds_nothing(self) -> None:
        layer = valid_layer()
        for feature_id in (float("inf"), float("-inf"), "abc", None):
            with self.subTest(feature_id=feature_id):
                self.assertIsNone(WorksLayerService.feature_by_id(layer, feature_id))
        layer.getFeatures.assert_not_called()

    def test_feature_without_geometry_has_no_pending_payload(self) -> None:
        feature = Mock()
        feature.geometry.side_effect = RuntimeError("feature deleted")
        with patch.object(WorksLayerService, "_field_map", return_value={}):
            self.assertEqual(WorksLayerService.pending_gis_payload_from_feature(valid_layer(), feature), {})

    def test_attribute_text_of_a_field_the_feature_lacks_is_empty(self) -> None:
        feature = Mock()
        feature.attribute.side_effect = KeyError("ext_job_id")
        self.assertEqual(WorksLayerService._feature_attr_text(feature, {"ext_job_id": "ext_job_id"}, "ext_job_id"), "")

    def test_null_check_that_fails_leaves_the_text_as_it_is(self) -> None:
        class Value:
            def isNull(self, _required):  # needs an argument, so calling it without raises TypeError
                return True

            def __str__(self) -> str:
                return " text "

        feature = Mock()
        feature.attribute.return_value = Value()
        self.assertEqual(WorksLayerService._feature_attr_text(feature, {"x": "x"}, "x"), "text")

    def test_null_value_gives_empty_text(self) -> None:
        feature = Mock()
        feature.attribute.return_value = SimpleNamespace(isNull=lambda: True)
        self.assertEqual(WorksLayerService._feature_attr_text(feature, {"x": "x"}, "x"), "")

    def test_detailed_payload_that_is_not_json_is_empty(self) -> None:
        # Another client may write anything here, including text that nests deeper than the parser allows.
        for raw in ("{not json", "[" * 100000):
            with self.subTest(raw=raw[:12]):
                feature = Mock()
                feature.attribute.return_value = raw
                self.assertEqual(WorksLayerService._feature_detailed_payload(feature, self.FIELD_MAP), {})

    def test_detailed_payload_object_is_read(self) -> None:
        feature = Mock()
        feature.attribute.return_value = '{"status": {"id": "3"}}'
        self.assertEqual(WorksLayerService._feature_detailed_payload(feature, self.FIELD_MAP), {"status": {"id": "3"}})

    def test_value_is_kept_when_the_field_type_cannot_be_read(self) -> None:
        for error in (RuntimeError("layer deleted"), AttributeError("no type")):
            with self.subTest(error=type(error).__name__):
                field = Mock()
                field.type.side_effect = error
                self.assertEqual(WorksLayerService.coerce_value_for_field(field, "7"), "7")

    def test_text_field_gets_json_for_objects_and_str_for_what_json_rejects(self) -> None:
        field = QgsField("detail", QVariant.String)
        circular: dict = {}
        circular["self"] = circular
        opaque = {"value": object()}
        self.assertEqual(WorksLayerService.coerce_value_for_field(field, {"ä": 1}), '{"ä": 1}')
        self.assertEqual(WorksLayerService.coerce_value_for_field(field, circular), str(circular))
        self.assertEqual(WorksLayerService.coerce_value_for_field(field, opaque), str(opaque))

    def test_integer_field_gets_nothing_for_numbers_it_cannot_read(self) -> None:
        # The value goes through str() first, so even int(inf) never reaches an OverflowError here.
        field = QgsField("state", QVariant.Int)
        for raw in ("abc", float("inf"), float("nan")):
            with self.subTest(raw=raw):
                self.assertIsNone(WorksLayerService.coerce_value_for_field(field, raw))
        self.assertEqual(WorksLayerService.coerce_value_for_field(field, " 12 "), 12)


# ---------------------------------------------------------------- utils/MapTools/MapHelpers.py
class MapHelpersTest(LoggedCase):
    def test_zoom_widens_the_extent_by_a_fifth(self) -> None:
        layer = valid_layer()
        feature = Mock()
        feature.geometry.return_value = QgsGeometry.fromRect(QgsRectangle(0, 0, 10, 10))
        layer.getFeatures.return_value = iter([feature])
        interface = Mock()
        with patch.object(maphelpers_module, "iface", interface):
            MapHelpers.select_features_by_ids(layer, [1], zoom=True)

        layer.selectByIds.assert_called_once_with([1])
        extent = interface.mapCanvas.return_value.setExtent.call_args.args[0]
        self.assertAlmostEqual(extent.width(), 12.0)
        self.assertAlmostEqual(extent.height(), 12.0)
        interface.mapCanvas.return_value.refresh.assert_called_once_with()

    def test_copy_goes_on_when_the_data_provider_cannot_report_its_keys(self) -> None:
        for provider_error in ({"return_value": None}, {"side_effect": RuntimeError("layer deleted")}):
            with self.subTest(provider=sorted(provider_error)):
                layer = memory_layer("&field=name:string")
                layer.startEditing()
                source = QgsFeature(layer.fields())
                source.setAttribute("name", "Tamme")
                source.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(1, 2)))
                with patch.object(QgsVectorLayer, "dataProvider", **provider_error):
                    copied, error = FeatureActions.copy_feature_to_layer(source, layer)
                self.assertTrue(copied, error)
                self.assertEqual(layer.featureCount(), 1)


# ---------------------------------------------------------------- utils/MapTools/module_identify_tool.py
class IdentifyToolTest(LoggedCase):
    @staticmethod
    def controller() -> ModuleIdentifyToolController:
        with patch.object(ModuleIdentifyToolController, "_safe_parent_window", return_value=None):
            return ModuleIdentifyToolController(lang_manager=Mock())

    def test_title_skips_the_fields_the_layer_does_not_have(self) -> None:
        values = {"name": " Objekt 7 "}

        def attribute(candidate):
            return values[candidate]

        feature = Mock()
        feature.attribute.side_effect = attribute
        self.assertEqual(ModuleIdentifyToolController._feature_title(feature, "id"), "Objekt 7")

    def test_failing_module_manager_gives_no_active_module_and_a_log_line(self) -> None:
        with patch.object(identify_module, "ModuleManager", side_effect=RuntimeError("no manager")):
            self.assertEqual(ModuleIdentifyToolController._active_module_key(), "")
        self.assertEqual(self.events(), ["module_identify_active_module_failed"])
        self.assertEqual(self.modules(), {"map"})

    def test_failed_selection_is_logged_and_the_item_still_opens(self) -> None:
        controller = self.controller()
        controller._layer = memory_layer()
        controller._module_key = "works"
        feature = Mock()
        feature.id.return_value = 7
        feature.attribute.return_value = "item-7"

        with (
            patch.object(controller, "_feature_at_point", return_value=feature),
            patch.object(controller, "_identity_field", return_value="id"),
            patch.object(identify_module.MapHelpers, "select_features_by_ids", side_effect=RuntimeError("select")),
            patch.object(controller, "_open_item") as open_item,
            patch.object(controller, "cancel") as cancel,
        ):
            controller.handle_map_click(QgsPointXY(1, 2))

        open_item.assert_called_once_with("works", "item-7", "item-7")
        cancel.assert_called_once_with(bring_front=True)
        self.assertEqual(self.events(), ["module_identify_select_feature_failed"])
        self.assertEqual(self.modules(), {"works"})
        self.assertEqual(self.log.call_args.kwargs["extra"], {"item_id": "item-7"})

    def test_failed_crs_transform_is_logged_and_the_point_is_searched_as_it_is(self) -> None:
        interface = Mock()
        interface.mapCanvas.return_value.mapSettings.return_value.destinationCrs.return_value = (
            QgsCoordinateReferenceSystem("EPSG:4326")
        )
        point = QgsPointXY(24.0, 58.0)
        with patch.object(identify_module, "iface", interface), patch.object(
            identify_module, "QgsCoordinateTransform", side_effect=RuntimeError("proj")
        ):
            result = ModuleIdentifyToolController._point_in_layer_crs(point, memory_layer())

        self.assertIs(result, point)
        self.assertEqual(self.events(), ["module_identify_point_transform_failed"])

    def test_search_goes_on_with_two_map_units_and_skips_what_cannot_be_measured(self) -> None:
        interface = Mock()
        interface.mapCanvas.return_value.mapUnitsPerPixel.side_effect = RuntimeError("canvas deleted")
        broken, near = feature_with_geometry(), feature_with_geometry(distance=1.0)
        broken.geometry.return_value.distance.side_effect = TypeError("not a geometry")
        layer = valid_layer()
        layer.getFeatures.return_value = iter([broken, near])
        controller = self.controller()

        with patch.object(identify_module, "iface", interface), patch.object(
            controller, "_point_in_layer_crs", side_effect=lambda point, _layer: point
        ):
            found = controller._feature_at_point(layer, QgsPointXY(10, 20))

        self.assertIs(found, near)
        self.assertEqual(layer.getFeatures.call_args.args[0].filterRect().width(), 4.0)
        self.log.assert_not_called()

    def test_polygon_that_cannot_be_tested_is_skipped(self) -> None:
        interface = Mock()
        interface.mapCanvas.return_value.mapUnitsPerPixel.return_value = 1.0
        broken, inside = feature_with_geometry(), feature_with_geometry(contains=True)
        broken.geometry.return_value.contains.side_effect = TypeError("not a geometry")
        layer = valid_layer(QgsWkbTypes.PolygonGeometry)
        layer.getFeatures.return_value = iter([broken, inside])
        controller = self.controller()

        with patch.object(identify_module, "iface", interface), patch.object(
            controller, "_point_in_layer_crs", side_effect=lambda point, _layer: point
        ):
            self.assertIs(controller._feature_at_point(layer, QgsPointXY(10, 20)), inside)

    def test_cancel_works_without_a_usable_pan_action(self) -> None:
        for error in (RuntimeError("deleted"), AttributeError("no action")):
            with self.subTest(error=type(error).__name__):
                interface = Mock()
                interface.actionPan.side_effect = error
                controller = self.controller()
                controller._module_key = "works"
                with patch.object(identify_module, "iface", interface), patch.object(
                    identify_module.DialogHelpers, "exit_map_selection_mode"
                ) as leave:
                    controller.cancel()
                leave.assert_called_once()
                self.assertEqual(controller._module_key, "")

    def test_parent_window_falls_back_to_none_when_the_plugin_dialog_cannot_be_read(self) -> None:
        interface = Mock()
        with patch.object(identify_module, "iface", interface), patch.object(
            ModuleIdentifyToolController, "_plugin_dialog_instance", side_effect=ImportError("dialog")
        ):
            self.assertIsNone(ModuleIdentifyToolController._safe_parent_window(None))
        self.assertEqual(self.events(), ["module_identify_parent_window_failed"])

    def test_parent_window_is_kept_when_the_qgis_main_window_cannot_be_read(self) -> None:
        interface = Mock()
        interface.mainWindow.side_effect = RuntimeError("deleted")
        parent = object()
        with patch.object(identify_module, "iface", interface):
            self.assertIs(ModuleIdentifyToolController._safe_parent_window(parent), parent)
        self.log.assert_not_called()


# ---------------------------------------------------------------- utils/MapTools/module_feature_controllers.py
class FeatureControllersTest(LoggedCase):
    MESSAGES = dict(
        save_failed_message="{item_id}: {error}",
        success_message="saved {item_id}",
        title_error="E",
        title_success="S",
    )

    def test_attach_goes_on_when_the_old_selection_cannot_be_cleared(self) -> None:
        layer = valid_layer()
        layer.removeSelection.side_effect = RuntimeError("deleted")
        interface = Mock()
        with (
            patch.object(controllers_module, "iface", interface),
            patch.object(controllers_module.DialogHelpers, "enter_map_selection_mode"),
            patch.object(controllers_module, "SingleClickMapTool"),
        ):
            started = ModuleFeatureAttachController().start_attach(
                item_data={"id": "7"},
                resolve_layer=lambda: layer,
                find_feature_at_point=lambda point, _layer: None,
                attach_handler=lambda *_args: FeatureLinkResult(True),
                start_failed_message="start",
                feature_not_found_message="missing",
                save_failed_message="failed",
                success_message="ok",
                title_error="E",
                title_warning="W",
                title_success="S",
                log_module="works",
            )

        self.assertTrue(started)
        interface.mapCanvas.return_value.setMapTool.assert_called_once()

    def test_attach_logs_a_failed_selection_and_still_attaches(self) -> None:
        controller = ModuleFeatureAttachController()
        layer = memory_layer()
        feature = Mock()
        feature.id.return_value = 5
        handler = Mock(return_value=FeatureLinkResult(True))
        controller._layer = layer
        controller._item_id = "job-9"
        controller._find_feature_at_point = lambda _point, _layer: feature
        controller._attach_handler = handler

        with patch.object(
            controllers_module.MapHelpers, "select_features_by_ids", side_effect=RuntimeError("select")
        ), patch.object(controller, "_clear_capture_tool"):
            controller._handle_point_selected(
                QgsPointXY(0, 0),
                feature_not_found_message="missing",
                title_warning="W",
                log_module="works",
                **self.MESSAGES,
            )

        handler.assert_called_once_with(layer, 5, {})
        self.show_info.assert_called_once_with("S", "saved job-9")
        self.assertEqual(self.events(), ["module_feature_attach_select_failed"])
        self.assertEqual(self.modules(), {"works"})
        self.assertEqual(self.log.call_args.kwargs["extra"], {"item_id": "job-9"})

    def test_cancel_clears_the_draw_state_when_the_layer_cannot_be_disconnected(self) -> None:
        for error in (TypeError("not connected"), RuntimeError("layer deleted")):
            with self.subTest(error=type(error).__name__):
                layer = valid_layer()
                layer.featureAdded.disconnect.side_effect = error
                controller = ModuleFeatureDrawController()
                controller._layer = layer
                controller._item_data = {"id": "1"}
                controller.cancel()
                self.assertIsNone(controller._layer)
                self.assertEqual(controller._item_data, {})

    def test_feature_id_that_is_not_a_number_cancels_the_draw(self) -> None:
        controller = ModuleFeatureDrawController()
        controller._layer = valid_layer()
        with patch.object(controllers_module.QTimer, "singleShot") as timer:
            controller._handle_feature_added("not a number")
            timer.assert_not_called()
            self.assertIsNone(controller._layer)

            controller._layer = valid_layer()
            controller._handle_feature_added(-3)  # temporary ids of the edit buffer are negative
            timer.assert_called_once()
        self.assertEqual(controller._pending_feature_ids, {-3})

    def draw_controller(self, layer, handler) -> ModuleFeatureDrawController:
        controller = ModuleFeatureDrawController()
        controller._layer = layer
        controller._on_feature_created = handler
        controller._title_error = "E"
        controller._title_success = "S"
        controller._layer_save_failed_message = "{item_id}: {error}"
        controller._sync_failed_message = "not synced {item_id}"
        controller._success_message = "saved {item_id}"
        controller._item_id = "job-4"
        controller._log_module = "works"
        return controller

    def test_draw_logs_a_failed_selection_and_a_failed_rollback_and_reports_the_commit_error(self) -> None:
        layer = valid_layer()
        layer.commitChanges.return_value = False
        layer.commitErrors.return_value = ["constraint failed"]
        layer.rollBack.side_effect = RuntimeError("rollback boom")
        controller = self.draw_controller(layer, Mock(return_value=FeatureLinkResult(True)))
        controller._started_edit_session = True

        with patch.object(controllers_module, "iface", Mock()), patch.object(
            controllers_module.MapHelpers, "select_features_by_ids", side_effect=RuntimeError("select")
        ):
            controller._finalize_feature_added(4)

        self.assertEqual(self.events(), ["module_feature_draw_select_failed", "module_feature_draw_rollback_failed"])
        self.assertEqual(self.modules(), {"works"})
        self.assertEqual(self.log.call_args.kwargs["extra"], {"feature_id": 4, "item_id": "job-4"})
        self.show_warning.assert_called_once_with("E", "job-4: constraint failed")
        self.show_info.assert_not_called()

    def test_draw_reports_success_although_the_repaint_and_pan_restore_fail(self) -> None:
        layer = valid_layer()
        layer.triggerRepaint.side_effect = RuntimeError("layer deleted")
        interface = Mock()
        interface.actionPan.side_effect = AttributeError("no pan action")
        controller = self.draw_controller(layer, Mock(return_value=FeatureLinkResult(True)))

        with patch.object(controllers_module, "iface", interface), patch.object(controllers_module, "MapHelpers"):
            controller._finalize_feature_added(4)

        self.show_info.assert_called_once_with("S", "saved job-4")
        self.log.assert_not_called()

    def test_next_candidate_action_is_tried_when_one_cannot_be_triggered(self) -> None:
        good = Mock()
        interface = SimpleNamespace(
            actionDeleted=Mock(side_effect=RuntimeError("deleted")),
            actionNeedsArgument=lambda required: required,  # calling it without one raises TypeError
            actionNoTrigger=lambda: object(),
            actionNone=lambda: None,
            actionGood=Mock(return_value=good),
        )
        with patch.object(controllers_module, "iface", interface):
            self.assertTrue(
                ModuleFeatureDrawController._trigger_iface_action(
                    "actionMissing", "actionDeleted", "actionNeedsArgument", "actionNoTrigger", "actionNone", "actionGood"
                )
            )
            self.assertFalse(ModuleFeatureDrawController._trigger_iface_action("actionMissing", "actionDeleted"))
        good.trigger.assert_called_once_with()

    def test_edit_action_follows_the_geometry_type_and_tries_on_after_a_failure(self) -> None:
        for geometry, first, error in (
            (QgsWkbTypes.PointGeometry, "actionMoveFeature", RuntimeError("deleted")),
            (QgsWkbTypes.PolygonGeometry, "actionVertexToolActiveLayer", RuntimeError("deleted")),
            (QgsWkbTypes.PolygonGeometry, "actionVertexToolActiveLayer", TypeError("needs an argument")),
        ):
            with self.subTest(geometry=first, error=type(error).__name__):
                triggered = []
                actions = {
                    name: Mock(return_value=Mock(trigger=lambda n=name: triggered.append(n)))
                    for name in ("actionMoveFeature", "actionVertexToolActiveLayer", "actionVertexTool")
                }
                actions[first] = Mock(side_effect=error)
                with patch.object(controllers_module, "iface", SimpleNamespace(**actions)):
                    self.assertTrue(ModuleFeatureEditController._trigger_edit_action(valid_layer(geometry)))
                self.assertEqual(len(triggered), 1)
                self.assertNotEqual(triggered[0], first)

    def test_edit_action_uses_the_polygon_order_when_the_layer_has_no_geometry_type(self) -> None:
        layer = valid_layer()
        layer.geometryType.side_effect = RuntimeError("layer deleted")
        action = Mock()
        interface = SimpleNamespace(actionVertexToolActiveLayer=Mock(return_value=action))
        with patch.object(controllers_module, "iface", interface):
            self.assertTrue(ModuleFeatureEditController._trigger_edit_action(layer))
        action.trigger.assert_called_once_with()


# ---------------------------------------------------------------- utils/moduleSwitchHelper.py
class ModuleSwitchHelperTest(unittest.TestCase):
    def test_module_name_is_canonical_and_unknown_names_are_lowercased(self) -> None:
        self.assertEqual(ModuleSwitchHelper._canonical_key("Property"), "property")
        self.assertEqual(ModuleSwitchHelper._canonical_key(" Somewhere "), "somewhere")
        with self.assertRaises(TypeError):
            ModuleSwitchHelper._canonical_key("  ")

    def test_failed_sidebar_update_while_redirecting_is_logged_and_the_redirect_still_happens(self) -> None:
        sidebar = Mock()
        sidebar.setActiveModuleOnSidebarButton.side_effect = RuntimeError("deleted")
        dlg = SimpleNamespace(lang_manager=Mock(), sidebar=sidebar, settingsModule=None)
        instance = object()
        manager = Mock()
        manager.getActiveModuleInstance.return_value = instance
        focus = Mock()

        with (
            patch.object(switch_module.SettingsSetupGuard, "is_ready", return_value=False),
            patch.object(switch_module.SettingsSetupGuard, "redirect_warning_text", return_value=("t", "m")),
            patch.object(ModernMessageDialog, "show_warning"),
            patch.object(ModuleSwitchHelper, "_settings_focus_handler", focus),
            patch.object(SwitchLogger, "log") as switch_log,
        ):
            redirected = ModuleSwitchHelper._redirect_to_settings_for_incomplete_setup(
                dlg=dlg, module_manager=manager, previous_module_name="settings", target_key="works"
            )

        self.assertTrue(redirected)
        self.assertIs(dlg.settingsModule, instance)
        focus.assert_called_once_with(instance, "works", dlg)
        switch_log.assert_called_once_with(
            "switch_settings_sidebar_failed", module="works", extra={"error": "deleted"}
        )

    def test_rollback_reports_no_current_widget_when_the_stack_cannot_tell(self) -> None:
        stack = Mock()
        stack.currentWidget.side_effect = RuntimeError("stack deleted")
        dlg = SimpleNamespace(moduleStack=stack, sidebar=Mock())
        manager = Mock()
        manager.getActiveModuleName.return_value = "home"

        with patch.object(SwitchLogger, "log") as switch_log:
            result = ModuleSwitchHelper._rollback_switch(
                module_manager=manager,
                dlg=dlg,
                previous_module_name="",
                prev_key="",
                prev_widget=None,
                normalized_name="works",
            )

        self.assertEqual(result, ("home", None))
        switch_log.assert_called_once_with(
            "switch_current_widget_after_fail_failed", module="works", extra={"error": "stack deleted"}
        )


# ---------------------------------------------------------------- utils/messagesHelper.py
class ChoiceDialogTest(LoggedCase):
    def test_choice_dialog_still_opens_when_it_cannot_be_widened(self) -> None:
        with patch.object(messages_module, "max", side_effect=RuntimeError("sizing"), create=True):
            dialog, result_box = ModernMessageDialog._create_choice_dialog(
                "Title", "Message", "info", buttons=["Yes", "No"], default="Yes", cancel="No"
            )
        try:
            self.assertEqual(self.events(), ["message_dialog_widen_failed"])
            self.assertEqual(self.modules(), {"ui"})
            self.assertIsNone(result_box["choice"])
            self.assertIsNotNone(dialog.layout())
        finally:
            dialog.hide()
            dialog.deleteLater()
            QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)


if __name__ == "__main__":
    unittest.main()
