"""Helpers the module layer services share: dates, layer lookup, field writes and the refresh after saving."""
from __future__ import annotations

import os
import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
if os.environ.get("QGIS_PREFIX_PATH"):
    sys.path.append(str(Path(os.environ["QGIS_PREFIX_PATH"]) / "python" / "plugins"))

from qgis.core import QgsPointXY, QgsVectorLayer, QgsWkbTypes

from Kavitro_dev.languages.translation_keys import TranslationKeys
from Kavitro_dev.modules.asbuilt.asbuilt_layer_service import AsBuiltLayerService
from Kavitro_dev.modules.easements.easement_layer_service import EasementLayerService
from Kavitro_dev.modules.projects.projects_layer_service import ProjectsLayerService
from Kavitro_dev.modules.works.works_layer_service import WorksLayerService
from Kavitro_dev.utils.MapTools.MapHelpers import MapHelpers
from Kavitro_dev.utils.messagesHelper import ModernMessageDialog

ALL_SERVICES = (AsBuiltLayerService, EasementLayerService, ProjectsLayerService, WorksLayerService)
LAYER_LOOKUP_SERVICES = (AsBuiltLayerService, EasementLayerService, ProjectsLayerService)
FIELD_WRITE_SERVICES = (AsBuiltLayerService, EasementLayerService, ProjectsLayerService)
PLAIN_INT_SERVICES = (AsBuiltLayerService, EasementLayerService, WorksLayerService)
REFRESH_SERVICES = (EasementLayerService, ProjectsLayerService)
NAME_LABEL_SERVICES = (AsBuiltLayerService, ProjectsLayerService)
DRAW_SERVICES = {
    AsBuiltLayerService: TranslationKeys.ASBUILT_DRAW_NEW_START_FAILED,
    ProjectsLayerService: TranslationKeys.PROJECT_DRAW_NEW_START_FAILED,
}
MODULE_NAMES = {AsBuiltLayerService: "asbuilt", EasementLayerService: "easement",
                ProjectsLayerService: "project", WorksLayerService: "works"}
# missing layer, several layers with the name, wrong geometry
MAIN_LAYER_KEYS = {
    AsBuiltLayerService: (TranslationKeys.ASBUILT_LAYER_MISSING, TranslationKeys.ASBUILT_LAYER_MISSING, None),
    EasementLayerService: (TranslationKeys.EASEMENT_LAYER_MISSING, TranslationKeys.EASEMENT_MAIN_LAYER_AMBIGUOUS,
                           TranslationKeys.EASEMENT_LAYER_INVALID_GEOMETRY),
    ProjectsLayerService: (TranslationKeys.PROJECT_LAYER_MISSING, TranslationKeys.PROJECT_LAYER_MISSING,
                           TranslationKeys.PROJECT_LAYER_INVALID_GEOMETRY),
    WorksLayerService: (TranslationKeys.WORKS_LAYER_MISSING, TranslationKeys.WORKS_MAIN_LAYER_AMBIGUOUS,
                        TranslationKeys.WORKS_LAYER_INVALID_GEOMETRY),
}


def good_geometry(service):
    return QgsWkbTypes.PointGeometry if service is WorksLayerService else QgsWkbTypes.PolygonGeometry


def wrong_geometry(service):
    return QgsWkbTypes.PolygonGeometry if service is WorksLayerService else QgsWkbTypes.PointGeometry


def home_of(function):
    """The module whose names a helper resolves, wherever the helper is defined."""
    return sys.modules[function.__module__]


def valid_layer() -> MagicMock:
    layer = MagicMock(spec=QgsVectorLayer)
    layer.isValid.return_value = True
    return layer


def invalid_layer() -> MagicMock:
    layer = valid_layer()
    layer.isValid.return_value = False
    return layer


def assert_logged(test: unittest.TestCase, logger, service, suffix: str) -> None:
    name = MODULE_NAMES[service]
    logger.log_exception.assert_called_once()
    arguments = logger.log_exception.call_args.kwargs
    test.assertEqual(arguments["module"], name)
    test.assertEqual(arguments["event"], f"{name}_{suffix}")


class FieldMapTest(unittest.TestCase):
    @staticmethod
    def field(name: str) -> Mock:
        field = Mock()
        field.name.return_value = name
        return field

    def test_field_names_are_indexed_in_lowercase(self) -> None:
        layer = valid_layer()
        layer.fields.return_value = [self.field("Kood"), self.field("NIMI")]
        for service in ALL_SERVICES:
            with self.subTest(service=service.__name__):
                self.assertEqual(service._field_map(layer), {"kood": "Kood", "nimi": "NIMI"})

    def test_invalid_or_foreign_layer_has_no_fields(self) -> None:
        for service in ALL_SERVICES:
            for layer in (None, object(), invalid_layer()):
                with self.subTest(service=service.__name__, layer=layer):
                    self.assertEqual(service._field_map(layer), {})

    def test_unreadable_fields_are_logged_for_the_module(self) -> None:
        layer = valid_layer()
        layer.fields.side_effect = RuntimeError("deleted")
        for service in ALL_SERVICES:
            with self.subTest(service=service.__name__), patch.object(
                home_of(service._field_map), "PythonFailLogger"
            ) as logger:
                self.assertEqual(service._field_map(layer), {})
                assert_logged(self, logger, service, "layer_field_map_failed")


class CurrentUsernameTest(unittest.TestCase):
    @staticmethod
    def ask(service, *, username="", stored="", error=None):
        home = home_of(service.current_username)
        with patch.object(home, "SessionManager") as manager, patch.object(home, "PythonFailLogger") as logger:
            manager.side_effect = error
            manager.return_value.username = username
            manager.return_value.get_username.return_value = stored
            return service.current_username(), logger

    def test_session_name_is_trimmed(self) -> None:
        for service in ALL_SERVICES:
            with self.subTest(service=service.__name__):
                self.assertEqual(self.ask(service, username="  Mari ", stored="muu")[0], "Mari")

    def test_stored_name_is_used_when_the_session_has_none(self) -> None:
        for service in ALL_SERVICES:
            with self.subTest(service=service.__name__):
                self.assertEqual(self.ask(service, username=" ", stored="Jaan")[0], "Jaan")

    def test_failure_is_logged_and_gives_an_empty_name(self) -> None:
        for service in ALL_SERVICES:
            with self.subTest(service=service.__name__):
                name, logger = self.ask(service, error=RuntimeError("no session"))
                self.assertEqual(name, "")
                assert_logged(self, logger, service, "current_user_resolve_failed")


class PointInLayerCrsTest(unittest.TestCase):
    point = QgsPointXY(24.5, 59.4)

    def convert(self, service, *, layer=None, source=None, target=None, interface=None, error=None):
        home = home_of(service._point_in_layer_crs)
        layer = layer if layer is not None else valid_layer()
        source, target = source or self.crs(), target or self.crs()
        layer.crs.return_value = target
        if interface is None:
            interface = Mock()
            interface.mapCanvas.return_value.mapSettings.return_value.destinationCrs.return_value = source
        elif interface == "none":
            interface = None
        with patch.object(home, "iface", interface), patch.object(home, "QgsCoordinateTransform") as transform, patch.object(
            home, "QgsProject"
        ) as project, patch.object(home, "PythonFailLogger") as logger:
            transform.return_value.transform.side_effect = error
            if error is None:
                transform.return_value.transform.side_effect = None
                transform.return_value.transform.return_value = "converted"
            return service._point_in_layer_crs(self.point, layer), transform, project, logger

    @staticmethod
    def crs(valid: bool = True) -> MagicMock:
        crs = MagicMock()
        crs.isValid.return_value = valid
        return crs

    def test_point_is_converted_from_the_canvas_to_the_layer(self) -> None:
        source, target = self.crs(), self.crs()
        for service in ALL_SERVICES:
            with self.subTest(service=service.__name__):
                result, transform, project, _logger = self.convert(service, source=source, target=target)
                self.assertEqual(result, "converted")
                transform.assert_called_once_with(source, target, project.instance.return_value.transformContext.return_value)
                transform.return_value.transform.assert_called_once_with(self.point)

    def test_same_or_invalid_coordinate_system_keeps_the_point(self) -> None:
        shared = self.crs()
        for service in ALL_SERVICES:
            for source, target in ((shared, shared), (self.crs(False), self.crs()), (self.crs(), self.crs(False))):
                with self.subTest(service=service.__name__):
                    result, transform, _project, _logger = self.convert(service, source=source, target=target)
                    self.assertIs(result, self.point)
                    transform.assert_not_called()

    def test_no_canvas_or_invalid_layer_keeps_the_point(self) -> None:
        for service in ALL_SERVICES:
            with self.subTest(service=service.__name__):
                self.assertIs(self.convert(service, interface="none")[0], self.point)
                self.assertIs(self.convert(service, layer=invalid_layer())[0], self.point)

    def test_failed_conversion_is_logged_and_keeps_the_point(self) -> None:
        for service in ALL_SERVICES:
            with self.subTest(service=service.__name__):
                result, _transform, _project, logger = self.convert(service, error=RuntimeError("crs"))
                self.assertIs(result, self.point)
                assert_logged(self, logger, service, "point_transform_failed")


class BackendGeometryPayloadTest(unittest.TestCase):
    def test_payload_is_built_for_the_module(self) -> None:
        geometry = object()
        for service in ALL_SERVICES:
            name = MODULE_NAMES[service]
            home = home_of(service.backend_geometry_payload_from_geometry)
            with self.subTest(service=service.__name__), patch.object(home, "GeometryPayloadService") as payloads:
                result = service.backend_geometry_payload_from_geometry(geometry)
                self.assertIs(result, payloads.from_qgs_geometry.return_value)
                payloads.from_qgs_geometry.assert_called_once_with(
                    geometry, module=name, error_event=f"{name}_geometry_to_payload_failed"
                )


class GeometryInLayerCrsTest(unittest.TestCase):
    @staticmethod
    def convert(service, *, same_crs=False, error=None):
        home = home_of(service._geometry_in_layer_crs)
        geometry, source, target = object(), Mock(), Mock()
        source.crs.return_value = "EPSG:3301"
        target.crs.return_value = "EPSG:3301" if same_crs else "EPSG:4326"
        with patch.object(home, "QgsGeometry") as geometry_class, patch.object(
            home, "QgsCoordinateTransform"
        ) as transform, patch.object(home, "QgsProject") as project, patch.object(home, "PythonFailLogger") as logger:
            geometry_class.return_value.transform.side_effect = error
            result = service._geometry_in_layer_crs(geometry, source_layer=source, target_layer=target)
            geometry_class.assert_called_once_with(geometry)
            return result, geometry_class.return_value, transform, project, logger

    def test_copy_is_transformed_between_different_systems(self) -> None:
        for service in REFRESH_SERVICES:
            with self.subTest(service=service.__name__):
                result, copy, transform, project, _logger = self.convert(service)
                self.assertIs(result, copy)
                transform.assert_called_once_with("EPSG:3301", "EPSG:4326", project.instance.return_value)
                copy.transform.assert_called_once_with(transform.return_value)

    def test_same_system_leaves_the_copy_alone(self) -> None:
        for service in REFRESH_SERVICES:
            with self.subTest(service=service.__name__):
                result, copy, transform, _project, _logger = self.convert(service, same_crs=True)
                self.assertIs(result, copy)
                transform.assert_not_called()

    def test_failed_transform_is_logged_and_returns_the_copy(self) -> None:
        for service in REFRESH_SERVICES:
            with self.subTest(service=service.__name__):
                result, copy, _transform, _project, logger = self.convert(service, error=RuntimeError("crs"))
                self.assertIs(result, copy)
                assert_logged(self, logger, service, "layer_geometry_transform_failed")


class ResolveMainLayerTest(unittest.TestCase):
    def setUp(self) -> None:
        self.lang = Mock()
        self.lang.translate.side_effect = lambda key: f"t:{key}"
        for patcher in (patch.object(WorksLayerService, "resolve_task_id_field_name", return_value="ext_job_id"),
                        patch.object(WorksLayerService, "_prepare_required_fields", return_value=(True, ""))):
            patcher.start()
            self.addCleanup(patcher.stop)

    @staticmethod
    def layer(geometry=QgsWkbTypes.PolygonGeometry, layer_id="layer-1") -> MagicMock:
        layer = valid_layer()
        layer.id.return_value = layer_id
        layer.geometryType.return_value = geometry
        return layer

    def resolve(self, service, matches, *, identifier="Kiht", silent=False, save_error=None):
        home = home_of(service.resolve_main_layer)
        with patch.object(service, "_configured_layers", return_value=matches) as configured, patch.object(
            home, "SettingsService"
        ) as settings, patch.object(home, "ModernMessageDialog") as dialogs, patch.object(home, "PythonFailLogger") as logger:
            setting = settings.return_value.module_main_layer_name
            setting.side_effect = [identifier, save_error if save_error is not None else None]
            result = service.resolve_main_layer(lang_manager=self.lang, silent=silent)
            configured.assert_called_once_with(identifier)
            return result, setting, dialogs.show_warning, logger

    def assert_warned(self, warning, key) -> None:
        warning.assert_called_once_with(f"t:{TranslationKeys.ERROR}", f"t:{key}")

    def test_several_layers_with_the_name_warn_and_give_nothing(self) -> None:
        for service, (_missing, ambiguous, _geometry) in MAIN_LAYER_KEYS.items():
            with self.subTest(service=service.__name__):
                result, _setting, warning, _logger = self.resolve(service, [self.layer(), self.layer()])
                self.assertIsNone(result)
                self.assert_warned(warning, ambiguous)

    def test_missing_or_invalid_layer_warns_and_gives_nothing(self) -> None:
        for service, (missing, _ambiguous, _geometry) in MAIN_LAYER_KEYS.items():
            for matches in ([], [invalid_layer()]):
                with self.subTest(service=service.__name__, matches=matches):
                    result, _setting, warning, _logger = self.resolve(service, matches)
                    self.assertIsNone(result)
                    self.assert_warned(warning, missing)

    def test_silent_lookup_shows_no_warning(self) -> None:
        for service in MAIN_LAYER_KEYS:
            for matches in ([], [self.layer(), self.layer()]):
                with self.subTest(service=service.__name__, matches=len(matches)):
                    result, _setting, warning, _logger = self.resolve(service, matches, silent=True)
                    self.assertIsNone(result)
                    warning.assert_not_called()

    def test_layer_found_by_name_is_stored_under_its_id(self) -> None:
        for service in MAIN_LAYER_KEYS:
            layer = self.layer(good_geometry(service))
            with self.subTest(service=service.__name__):
                result, setting, warning, _logger = self.resolve(service, [layer], identifier="Kiht")
                self.assertIs(result, layer)
                setting.assert_called_with(MODULE_NAMES[service], value="layer-1")
                warning.assert_not_called()

    def test_layer_already_stored_under_its_id_is_not_written_again(self) -> None:
        for service in MAIN_LAYER_KEYS:
            layer = self.layer(good_geometry(service))
            with self.subTest(service=service.__name__):
                result, setting, _warning, _logger = self.resolve(service, [layer], identifier="layer-1")
                self.assertIs(result, layer)
                self.assertEqual(setting.call_count, 1)

    def test_failed_id_write_is_logged_and_keeps_the_layer(self) -> None:
        for service in MAIN_LAYER_KEYS:
            layer = self.layer(good_geometry(service))
            with self.subTest(service=service.__name__):
                result, _setting, _warning, logger = self.resolve(service, [layer], save_error=RuntimeError("settings"))
                self.assertIs(result, layer)
                assert_logged(self, logger, service, "layer_setting_id_migrate_failed")

    def test_layer_of_the_wrong_geometry_is_refused_after_its_id_is_stored(self) -> None:
        for service, (_missing, _ambiguous, wrong_key) in MAIN_LAYER_KEYS.items():
            if wrong_key is None:
                continue
            with self.subTest(service=service.__name__):
                result, setting, warning, _logger = self.resolve(service, [self.layer(wrong_geometry(service))])
                self.assertIsNone(result)
                self.assert_warned(warning, wrong_key)
                setting.assert_called_with(MODULE_NAMES[service], value="layer-1")

    def test_as_built_layer_may_have_any_geometry(self) -> None:
        for geometry in (QgsWkbTypes.PointGeometry, QgsWkbTypes.LineGeometry, QgsWkbTypes.PolygonGeometry):
            layer = self.layer(geometry)
            with self.subTest(geometry=geometry):
                self.assertIs(self.resolve(AsBuiltLayerService, [layer])[0], layer)


class WorksMainLayerChecksTest(unittest.TestCase):
    FALLBACK = "Configured Works layer does not match the required schema."

    def setUp(self) -> None:
        self.lang = Mock()
        self.lang.translate.side_effect = lambda key: f"t:{key}"

    def resolve(self, geometry=QgsWkbTypes.PointGeometry, *, id_field="ext_job_id", fields=(True, ""), silent=False):
        layer = valid_layer()
        layer.id.return_value = "layer-1"
        layer.geometryType.return_value = geometry
        home = home_of(WorksLayerService.resolve_main_layer)
        with patch.object(MapHelpers, "resolve_layer", return_value=layer), patch.object(
            MapHelpers, "find_layer_by_id", return_value=layer
        ), patch.object(home, "SettingsService") as settings, patch.object(
            ModernMessageDialog, "show_warning"
        ) as warning, patch.object(WorksLayerService, "resolve_task_id_field_name", return_value=id_field), patch.object(
            WorksLayerService, "_prepare_required_fields", return_value=fields
        ) as prepare:
            settings.return_value.module_main_layer_name.return_value = "layer-1"
            result = WorksLayerService.resolve_main_layer(lang_manager=self.lang, silent=silent)
            return result, layer, warning, prepare

    def test_point_layer_with_its_fields_is_returned(self) -> None:
        result, layer, warning, prepare = self.resolve()
        self.assertIs(result, layer)
        prepare.assert_called_once_with(layer)
        warning.assert_not_called()

    def test_layer_that_is_not_a_point_layer_is_refused(self) -> None:
        result, _layer, warning, prepare = self.resolve(QgsWkbTypes.PolygonGeometry)
        self.assertIsNone(result)
        warning.assert_called_once_with(f"t:{TranslationKeys.ERROR}", f"t:{TranslationKeys.WORKS_LAYER_INVALID_GEOMETRY}")
        prepare.assert_not_called()

    def test_layer_without_the_task_id_field_is_refused(self) -> None:
        result, _layer, warning, prepare = self.resolve(id_field=None)
        self.assertIsNone(result)
        warning.assert_called_once_with(f"t:{TranslationKeys.ERROR}", f"t:{TranslationKeys.WORKS_LAYER_ID_FIELD_MISSING}")
        prepare.assert_not_called()

    def test_field_problem_is_shown_with_its_own_message(self) -> None:
        result, _layer, warning, _prepare = self.resolve(fields=(False, "väli ei sobi"))
        self.assertIsNone(result)
        warning.assert_called_once_with(f"t:{TranslationKeys.ERROR}", "väli ei sobi")

    def test_field_problem_without_a_message_has_a_general_text(self) -> None:
        result, _layer, warning, _prepare = self.resolve(fields=(False, ""))
        self.assertIsNone(result)
        warning.assert_called_once_with(f"t:{TranslationKeys.ERROR}", self.FALLBACK)

    def test_silent_lookup_refuses_without_a_warning(self) -> None:
        for options in ({"geometry": QgsWkbTypes.PolygonGeometry}, {"id_field": None}, {"fields": (False, "väli ei sobi")}):
            with self.subTest(options=options):
                result, _layer, warning, _prepare = self.resolve(silent=True, **options)
                self.assertIsNone(result)
                warning.assert_not_called()


class PrepareLayerForDrawTest(unittest.TestCase):
    def setUp(self) -> None:
        self.lang = Mock()
        self.lang.translate.side_effect = lambda key: f"t:{key}"

    def prepare(self, service, *, layer="layer", fields=(True, ""), silent=False):
        home = home_of(service.prepare_layer_for_draw)
        with patch.object(service, "resolve_main_layer", return_value=layer) as resolve, patch.object(
            service, "_ensure_custom_fields", return_value=fields
        ), patch.object(home, "ModernMessageDialog") as dialogs:
            result = service.prepare_layer_for_draw(lang_manager=self.lang, silent=silent)
            resolve.assert_called_once_with(lang_manager=self.lang, silent=silent)
            return result, dialogs.show_warning

    def test_ready_layer_is_returned(self) -> None:
        for service in DRAW_SERVICES:
            with self.subTest(service=service.__name__):
                result, warning = self.prepare(service)
                self.assertEqual(result, ("layer", ""))
                warning.assert_not_called()

    def test_missing_layer_gives_nothing_without_another_warning(self) -> None:
        for service in DRAW_SERVICES:
            with self.subTest(service=service.__name__):
                result, warning = self.prepare(service, layer=None)
                self.assertEqual(result, (None, ""))
                warning.assert_not_called()

    def test_field_problem_is_shown_with_its_own_message(self) -> None:
        for service in DRAW_SERVICES:
            with self.subTest(service=service.__name__):
                result, warning = self.prepare(service, fields=(False, "väli puudub"))
                self.assertEqual(result, (None, "väli puudub"))
                warning.assert_called_once_with(f"t:{TranslationKeys.ERROR}", "väli puudub")

    def test_field_problem_without_a_message_uses_the_module_text(self) -> None:
        for service, key in DRAW_SERVICES.items():
            with self.subTest(service=service.__name__):
                result, warning = self.prepare(service, fields=(False, ""))
                self.assertEqual(result, (None, ""))
                warning.assert_called_once_with(f"t:{TranslationKeys.ERROR}", f"t:{key}")

    def test_silent_preparation_shows_nothing(self) -> None:
        for service in DRAW_SERVICES:
            with self.subTest(service=service.__name__):
                result, warning = self.prepare(service, fields=(False, "väli puudub"), silent=True)
                self.assertEqual(result, (None, "väli puudub"))
                warning.assert_not_called()


class FeatureByIdTest(unittest.TestCase):
    @staticmethod
    def feature(feature_id: int) -> Mock:
        feature = Mock()
        feature.id.return_value = feature_id
        return feature

    @staticmethod
    def find(service, layer, feature_id=7):
        with patch.object(home_of(service._feature_by_id), "PythonFailLogger"):
            return service._feature_by_id(layer, feature_id)

    def test_feature_comes_from_the_id_request(self) -> None:
        wanted = self.feature(7)
        for service in LAYER_LOOKUP_SERVICES:
            with self.subTest(service=service.__name__):
                layer = valid_layer()
                layer.getFeatures.return_value = iter([wanted])
                self.assertIs(self.find(service, layer), wanted)
                layer.getFeatures.assert_called_once()

    def test_invalid_or_missing_layer_is_not_read(self) -> None:
        for service in LAYER_LOOKUP_SERVICES:
            broken = invalid_layer()
            with self.subTest(service=service.__name__):
                self.assertIsNone(self.find(service, None))
                self.assertIsNone(self.find(service, broken))
                broken.getFeatures.assert_not_called()

    def test_failed_scan_is_logged_for_the_module(self) -> None:
        for service in LAYER_LOOKUP_SERVICES:
            layer = valid_layer()
            layer.getFeatures.side_effect = [iter([]), RuntimeError("provider")]
            with self.subTest(service=service.__name__), patch.object(
                home_of(service._feature_by_id), "PythonFailLogger"
            ) as logger:
                self.assertIsNone(service._feature_by_id(layer, 7))
                assert_logged(self, logger, service, "feature_by_id_failed")

    def test_empty_or_failed_request_falls_back_to_scanning(self) -> None:
        wanted = self.feature(7)
        for service in LAYER_LOOKUP_SERVICES:
            for first in (iter([]), RuntimeError("provider")):
                with self.subTest(service=service.__name__, first=type(first).__name__):
                    layer = valid_layer()
                    layer.getFeatures.side_effect = [first, iter([self.feature(1), wanted])]
                    self.assertIs(self.find(service, layer), wanted)

    def test_unknown_id_finds_nothing(self) -> None:
        for service in LAYER_LOOKUP_SERVICES:
            with self.subTest(service=service.__name__):
                layer = valid_layer()
                layer.getFeatures.side_effect = [iter([]), iter([self.feature(1)])]
                self.assertIsNone(self.find(service, layer))

    def test_failed_scan_finds_nothing(self) -> None:
        for service in LAYER_LOOKUP_SERVICES:
            with self.subTest(service=service.__name__):
                layer = valid_layer()
                layer.getFeatures.side_effect = [iter([]), RuntimeError("provider")]
                self.assertIsNone(self.find(service, layer))


class FindFeatureAtPointTest(unittest.TestCase):
    @staticmethod
    def feature(*, contains=False, intersects=False, distance=0.0, empty=False) -> Mock:
        feature = Mock()
        geometry = feature.geometry.return_value
        geometry.isEmpty.return_value = empty
        geometry.contains.return_value = contains
        geometry.intersects.return_value = intersects
        geometry.distance.return_value = distance
        return feature

    @staticmethod
    def find(service, features, *, geometry=QgsWkbTypes.PolygonGeometry, units=1.0, interface="canvas", layer=None, **options):
        home = home_of(service.find_feature_at_point)
        layer = layer if layer is not None else valid_layer()
        layer.geometryType.return_value = geometry
        layer.getFeatures.return_value = iter(features)
        if interface == "canvas":
            interface = Mock()
            interface.mapCanvas.return_value.mapUnitsPerPixel.return_value = units
        with patch.object(home, "iface", interface), patch.object(
            service, "_point_in_layer_crs", side_effect=lambda point, _layer: point
        ):
            return service.find_feature_at_point(QgsPointXY(10, 20), layer=layer, **options), layer

    def test_polygon_under_the_point_is_found(self) -> None:
        outside, inside, touching = self.feature(), self.feature(contains=True), self.feature(intersects=True)
        for service in LAYER_LOOKUP_SERVICES:
            with self.subTest(service=service.__name__):
                self.assertIs(self.find(service, [outside, inside])[0], inside)
                self.assertIs(self.find(service, [touching])[0], touching)

    def test_nothing_under_the_point_finds_nothing(self) -> None:
        for service in LAYER_LOOKUP_SERVICES:
            with self.subTest(service=service.__name__):
                self.assertIsNone(self.find(service, [self.feature(), self.feature(empty=True, contains=True)])[0])

    def test_search_area_follows_the_map_scale(self) -> None:
        for service in LAYER_LOOKUP_SERVICES:
            with self.subTest(service=service.__name__):
                _found, layer = self.find(service, [], units=2.0, radius_multiplier=4.0)
                area = layer.getFeatures.call_args.args[0].filterRect()
                self.assertEqual((area.xMinimum(), area.xMaximum()), (2.0, 18.0))
                self.assertEqual((area.yMinimum(), area.yMaximum()), (12.0, 28.0))

    def test_unusable_map_scale_searches_two_map_units(self) -> None:
        for service in LAYER_LOOKUP_SERVICES:
            with self.subTest(service=service.__name__):
                _found, layer = self.find(service, [], units=0.0)
                self.assertEqual(layer.getFeatures.call_args.args[0].filterRect().width(), 4.0)

    def test_no_canvas_or_invalid_layer_finds_nothing(self) -> None:
        for service in LAYER_LOOKUP_SERVICES:
            with self.subTest(service=service.__name__):
                self.assertIsNone(self.find(service, [self.feature(contains=True)], interface=None)[0])
                self.assertIsNone(self.find(service, [self.feature(contains=True)], layer=invalid_layer())[0])

    def test_failed_scan_is_logged_and_finds_nothing(self) -> None:
        for service in LAYER_LOOKUP_SERVICES:
            home = home_of(service.find_feature_at_point)
            layer = valid_layer()
            with self.subTest(service=service.__name__), patch.object(home, "PythonFailLogger") as logger:
                found, _layer = self.find(service, [], layer=layer)
                layer.getFeatures.side_effect = RuntimeError("provider")
                found, _layer = self.find(service, [], layer=layer)
                self.assertIsNone(found)
                assert_logged(self, logger, service, "feature_at_point_failed")

    def test_as_built_point_layer_finds_the_closest_within_reach(self) -> None:
        near, nearer, far = self.feature(distance=2.0), self.feature(distance=1.0), self.feature(distance=9.0)
        found, _layer = self.find(AsBuiltLayerService, [nearer, near, far], geometry=QgsWkbTypes.PointGeometry)
        self.assertIs(found, nearer)

    def test_as_built_point_out_of_reach_finds_nothing(self) -> None:
        found, _layer = self.find(AsBuiltLayerService, [self.feature(distance=9.0)], geometry=QgsWkbTypes.PointGeometry)
        self.assertIsNone(found)


class ParseBackendDatetimeTest(unittest.TestCase):
    def check(self, value, expected) -> None:
        for service in ALL_SERVICES:
            with self.subTest(service=service.__name__, value=value):
                self.assertEqual(service.parse_backend_datetime(value), expected)

    def test_empty_and_unreadable_values_give_nothing(self) -> None:
        for value in (None, "", "   ", 0, "not a date"):
            self.check(value, None)

    def test_date_alone_is_midnight(self) -> None:
        self.check("2026-03-04", datetime(2026, 3, 4))

    def test_value_without_a_zone_is_kept(self) -> None:
        self.check("2026-03-04 05:06:07", datetime(2026, 3, 4, 5, 6, 7))
        self.check("2026-03-04T05:06:07", datetime(2026, 3, 4, 5, 6, 7))

    def test_unpadded_value_is_read_by_the_fallback_formats(self) -> None:
        self.check("2026-3-4", datetime(2026, 3, 4))
        self.check("2026-3-4 5:06:07", datetime(2026, 3, 4, 5, 6, 7))

    def test_utc_and_offset_values_become_naive_local_time(self) -> None:
        expected = datetime(2026, 3, 4, 5, 6, 7, tzinfo=timezone.utc).astimezone().replace(tzinfo=None)
        self.check("2026-03-04T05:06:07Z", expected)
        self.check("2026-03-04T07:06:07+02:00", expected)


class ConfiguredLayersTest(unittest.TestCase):
    @staticmethod
    def named(name) -> Mock:
        layer = Mock()
        layer.name.return_value = name
        return layer

    @staticmethod
    def lookup(service, identifier, *, direct=None, layers=(), has_project=True):
        home = home_of(service._configured_layers)
        with patch.object(home, "MapHelpers") as helpers, patch.object(home, "QgsProject") as project_class:
            helpers.find_layer_by_id.return_value = direct
            project = Mock()
            project.mapLayers.return_value = dict(enumerate(layers))
            project_class.instance.return_value = project if has_project else None
            return service._configured_layers(identifier), helpers

    def test_blank_identifier_finds_nothing_without_searching(self) -> None:
        for service in ALL_SERVICES:
            for identifier in (None, "", "   "):
                with self.subTest(service=service.__name__, identifier=identifier):
                    found, helpers = self.lookup(service, identifier, layers=[self.named("")])
                    self.assertEqual(found, [])
                    helpers.find_layer_by_id.assert_not_called()

    def test_layer_id_wins_over_names(self) -> None:
        direct = self.named("id match")
        for service in ALL_SERVICES:
            with self.subTest(service=service.__name__):
                found, helpers = self.lookup(service, "  abc ", direct=direct, layers=[self.named("abc")])
                self.assertEqual(found, [direct])
                helpers.find_layer_by_id.assert_called_once_with("abc")

    def test_names_match_without_case_and_surrounding_spaces(self) -> None:
        first, second, other = self.named("Tööd"), self.named("  TÖÖD "), self.named("Muu")
        for service in ALL_SERVICES:
            with self.subTest(service=service.__name__):
                found, _helpers = self.lookup(service, " TööD ", layers=[first, other, second])
                self.assertEqual(found, [first, second])

    def test_layer_that_cannot_report_its_name_is_skipped(self) -> None:
        broken, good = Mock(), self.named("Tööd")
        broken.name.side_effect = RuntimeError("deleted")
        for service in ALL_SERVICES:
            with self.subTest(service=service.__name__):
                found, _helpers = self.lookup(service, "tööd", layers=[broken, good])
                self.assertEqual(found, [good])

    def test_without_a_project_nothing_is_found(self) -> None:
        for service in ALL_SERVICES:
            with self.subTest(service=service.__name__):
                found, _helpers = self.lookup(service, "tööd", has_project=False)
                self.assertEqual(found, [])


class LayerTargetLabelTest(unittest.TestCase):
    def test_label_is_the_trimmed_layer_name(self) -> None:
        layer = Mock()
        layer.name.return_value = "  Projektid "
        for service in NAME_LABEL_SERVICES:
            with self.subTest(service=service.__name__):
                self.assertEqual(service._layer_target_label(layer), "Projektid")

    def test_missing_or_broken_layer_gives_empty_label(self) -> None:
        broken = Mock()
        broken.name.side_effect = RuntimeError("deleted")
        for service in NAME_LABEL_SERVICES:
            with self.subTest(service=service.__name__):
                self.assertEqual(service._layer_target_label(None), "")
                self.assertEqual(service._layer_target_label(broken), "")

    def test_easement_label_also_names_the_source(self) -> None:
        layer = Mock()
        layer.name.return_value = "Servituudid"
        layer.source.return_value = "tee/servituudid.gpkg"
        self.assertEqual(EasementLayerService._layer_target_label(layer), "Servituudid (tee/servituudid.gpkg)")


class FieldWriteTest(unittest.TestCase):
    def test_first_candidate_on_the_layer_wins(self) -> None:
        for service in FIELD_WRITE_SERVICES:
            with self.subTest(service=service.__name__), patch.object(
                service, "_field_map", return_value={"later": "LATER", "first": "FIRST"}
            ) as field_map:
                layer = object()
                self.assertEqual(service._resolve_first_field_name(layer, ("Missing", "First", "later")), "FIRST")
                field_map.assert_called_once_with(layer)

    def test_no_candidate_on_the_layer_gives_nothing(self) -> None:
        for service in FIELD_WRITE_SERVICES:
            with self.subTest(service=service.__name__), patch.object(service, "_field_map", return_value={"a": ""}):
                self.assertIsNone(service._resolve_first_field_name(object(), ("a", "b")))

    @staticmethod
    def write(service, *, field_map, field_index=2):
        feature, layer, field = Mock(), MagicMock(), object()
        layer.fields.return_value.indexFromName.return_value = field_index
        layer.fields.return_value.__getitem__.side_effect = lambda index: field if index == field_index else None
        with patch.object(service, "_field_map", return_value=field_map), patch.object(
            service, "coerce_value_for_field", return_value="coerced"
        ) as coerce:
            service._set_attr_if_present(feature, layer=layer, candidates=("Code",), value="raw")
        return feature, coerce, field

    def test_value_is_coerced_for_the_field_and_written(self) -> None:
        for service in FIELD_WRITE_SERVICES:
            with self.subTest(service=service.__name__):
                feature, coerce, field = self.write(service, field_map={"code": "CODE"})
                feature.setAttribute.assert_called_once_with("CODE", "coerced")
                coerce.assert_called_once_with(field, "raw")

    def test_field_missing_from_the_layer_is_left_alone(self) -> None:
        for service in FIELD_WRITE_SERVICES:
            with self.subTest(service=service.__name__):
                feature, coerce, _field = self.write(service, field_map={})
                feature.setAttribute.assert_not_called()
                coerce.assert_not_called()

    def test_unresolved_field_index_coerces_without_a_field(self) -> None:
        for service in FIELD_WRITE_SERVICES:
            with self.subTest(service=service.__name__):
                feature, coerce, _field = self.write(service, field_map={"code": "CODE"}, field_index=-1)
                coerce.assert_called_once_with(None, "raw")
                feature.setAttribute.assert_called_once_with("CODE", "coerced")


    def test_works_writes_through_its_own_field_map(self) -> None:
        feature = Mock()
        with patch.object(WorksLayerService, "coerce_value_for_field", return_value="coerced") as coerce:
            WorksLayerService._set_attr_via_field_map(
                feature, layer=None, field_map={"code": "CODE"}, field_name="Code", value="raw"
            )
        feature.setAttribute.assert_called_once_with("CODE", "coerced")
        coerce.assert_called_once_with(None, "raw")


class SharedHelpersStayInOnePlaceTest(unittest.TestCase):
    SHARED = ("_configured_layers", "_feature_by_id", "_field_map", "_geometry_in_layer_crs", "_layer_target_label",
              "_point_in_layer_crs", "_refresh_saved_layer", "_resolve_first_field_name", "_set_attr_if_present",
              "backend_geometry_payload_from_geometry", "coerce_optional_int", "current_username",
              "find_feature_at_point", "parse_backend_datetime", "prepare_layer_for_draw", "resolve_main_layer")
    KEPT_ON_PURPOSE = {(EasementLayerService, "_layer_target_label")}

    def test_no_service_carries_its_own_copy(self) -> None:
        for service in ALL_SERVICES:
            for name in self.SHARED:
                if (service, name) in self.KEPT_ON_PURPOSE:
                    continue
                with self.subTest(service=service.__name__, helper=name):
                    self.assertNotIn(name, vars(service))


class CoerceOptionalIntTest(unittest.TestCase):
    def test_values(self) -> None:
        for value, expected in ((None, None), ("", None), ("  ", None), (0, None), ("12", 12), (" 12 ", 12),
                                (12, 12), ("abc", None), (1.5, None)):
            for service in PLAIN_INT_SERVICES:
                with self.subTest(service=service.__name__, value=value):
                    self.assertEqual(service.coerce_optional_int(value), expected)


class RefreshSavedLayerTest(unittest.TestCase):
    @staticmethod
    def layer(*, valid=True, editable=False) -> MagicMock:
        layer = MagicMock(spec=QgsVectorLayer)
        layer.isValid.return_value = valid
        layer.isEditable.return_value = editable
        return layer

    @staticmethod
    def refresh(service, layer, interface) -> None:
        with patch.object(home_of(service._refresh_saved_layer), "iface", interface):
            service._refresh_saved_layer(layer)

    def test_saved_layer_is_reloaded_and_repainted_on_the_canvas(self) -> None:
        for service in REFRESH_SERVICES:
            with self.subTest(service=service.__name__):
                layer, interface = self.layer(), Mock()
                self.refresh(service, layer, interface)
                layer.updateExtents.assert_called_once_with()
                layer.reload.assert_called_once_with()
                layer.triggerRepaint.assert_called_once_with()
                interface.mapCanvas.return_value.refresh.assert_called_once_with()

    def test_layer_in_edit_mode_is_not_reloaded(self) -> None:
        for service in REFRESH_SERVICES:
            with self.subTest(service=service.__name__):
                layer = self.layer(editable=True)
                self.refresh(service, layer, Mock())
                layer.reload.assert_not_called()
                layer.triggerRepaint.assert_called_once_with()

    def test_invalid_or_foreign_layer_is_ignored(self) -> None:
        for service in REFRESH_SERVICES:
            for layer in (None, object(), self.layer(valid=False)):
                with self.subTest(service=service.__name__, layer=layer):
                    interface = Mock()
                    self.refresh(service, layer, interface)
                    interface.mapCanvas.assert_not_called()

    def test_one_failing_step_does_not_stop_the_next(self) -> None:
        for service in REFRESH_SERVICES:
            with self.subTest(service=service.__name__):
                layer, interface = self.layer(), Mock()
                layer.updateExtents.side_effect = RuntimeError("extent")
                layer.reload.side_effect = RuntimeError("reload")
                layer.triggerRepaint.side_effect = RuntimeError("repaint")
                self.refresh(service, layer, interface)
                layer.triggerRepaint.assert_called_once_with()
                interface.mapCanvas.return_value.refresh.assert_called_once_with()

    def test_without_a_qgis_window_the_layer_is_still_refreshed(self) -> None:
        for service in REFRESH_SERVICES:
            with self.subTest(service=service.__name__):
                layer = self.layer()
                self.refresh(service, layer, None)
                layer.triggerRepaint.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()
