"""The temporary GeoPackage layer helpers of the works and project modules."""
from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
if os.environ.get("QGIS_PREFIX_PATH"):
    sys.path.append(str(Path(os.environ["QGIS_PREFIX_PATH"]) / "python" / "plugins"))

from qgis.PyQt.QtCore import QVariant
from qgis.core import QgsVectorLayer, QgsWkbTypes

from Kavitro_dev.modules.projects.projects_temp_layer_helper import ProjectsTempLayerHelper
from Kavitro_dev.modules.works.works_temp_layer_helper import WorksTempLayerHelper

HELPERS = (ProjectsTempLayerHelper, WorksTempLayerHelper)
# log module, log event prefix, geometry of a new layer
SPECS = {
    ProjectsTempLayerHelper: ("project", "projects", QgsWkbTypes.Polygon),
    WorksTempLayerHelper: ("works", "works", QgsWkbTypes.Point),
}
GPKG = os.path.join(os.path.abspath(os.sep), "kihid", "ajutine.gpkg")


def home_of(function):
    """The module whose names a helper resolves, wherever the helper is defined."""
    return sys.modules[function.__module__]


def gpkg_layer(path: str = GPKG, *, valid: bool = True) -> MagicMock:
    layer = MagicMock(spec=QgsVectorLayer)
    layer.isValid.return_value = valid
    layer.dataProvider.return_value.dataSourceUri.return_value = f"{path}|layername=tööd"
    layer.id.return_value = f"id-{path}"
    return layer


def assert_logged(test: unittest.TestCase, logger, helper, suffix: str) -> None:
    module, prefix, _geometry = SPECS[helper]
    logger.log_exception.assert_called_once()
    arguments = logger.log_exception.call_args.kwargs
    test.assertEqual(arguments["module"], module)
    test.assertEqual(arguments["event"], f"{prefix}_{suffix}")


class StandalonePathTest(unittest.TestCase):
    def test_file_goes_beside_the_reference_layer(self) -> None:
        for helper in HELPERS:
            with self.subTest(helper=helper.__name__):
                self.assertEqual(helper.default_standalone_gpkg_path(gpkg_layer(), "Uus kiht"),
                                 os.path.join(os.path.dirname(GPKG), "Uus kiht.gpkg"))

    def test_without_a_reference_file_goes_home(self) -> None:
        for helper in HELPERS:
            with self.subTest(helper=helper.__name__):
                self.assertEqual(helper.default_standalone_gpkg_path(None, "Uus"),
                                 os.path.join(os.path.expanduser("~"), "Uus.gpkg"))

    def test_unsafe_characters_are_replaced(self) -> None:
        for helper in HELPERS:
            with self.subTest(helper=helper.__name__):
                path = helper.default_standalone_gpkg_path(None, ' a/b:c*d?"e ')
                self.assertEqual(os.path.basename(path), "a_b_c_d__e.gpkg")

    def test_empty_name_uses_the_default_layer_name(self) -> None:
        for helper in HELPERS:
            for name in ("", None, " ._ "):
                with self.subTest(helper=helper.__name__, name=name):
                    path = helper.default_standalone_gpkg_path(None, name)
                    self.assertEqual(os.path.basename(path), f"{helper.DEFAULT_LAYER_NAME}.gpkg")


class PathTest(unittest.TestCase):
    def test_blank_path_stays_blank(self) -> None:
        for helper in HELPERS:
            for path in ("", None, "   "):
                with self.subTest(helper=helper.__name__, path=path):
                    self.assertEqual(helper._normalize_gpkg_path(path), "")

    def test_extension_is_added_and_path_made_absolute(self) -> None:
        for helper in HELPERS:
            with self.subTest(helper=helper.__name__):
                self.assertEqual(helper._normalize_gpkg_path("kaust/nimi"),
                                 os.path.normcase(os.path.abspath("kaust/nimi.gpkg")))

    def test_existing_extension_is_kept_whatever_its_case(self) -> None:
        for helper in HELPERS:
            with self.subTest(helper=helper.__name__):
                self.assertEqual(helper._normalize_gpkg_path("nimi.GPKG"),
                                 os.path.normcase(os.path.abspath("nimi.GPKG")))

    def test_layer_path_is_the_file_part_of_its_source(self) -> None:
        for helper in HELPERS:
            with self.subTest(helper=helper.__name__):
                self.assertEqual(helper.gpkg_path_for_layer(gpkg_layer()), GPKG)

    def test_invalid_or_non_geopackage_layer_has_no_path(self) -> None:
        for helper in HELPERS:
            for layer in (None, object(), gpkg_layer(valid=False), gpkg_layer("C:/kihid/andmed.shp")):
                with self.subTest(helper=helper.__name__, layer=layer):
                    self.assertEqual(helper.gpkg_path_for_layer(layer), "")

    def test_unreadable_source_is_logged_and_gives_no_path(self) -> None:
        layer = gpkg_layer()
        layer.dataProvider.side_effect = RuntimeError("deleted")
        for helper in HELPERS:
            with self.subTest(helper=helper.__name__), patch.object(
                home_of(helper.gpkg_path_for_layer), "PythonFailLogger"
            ) as logger:
                self.assertEqual(helper.gpkg_path_for_layer(layer), "")
                assert_logged(self, logger, helper, "temp_reference_uri_failed")


class LoadedLayersTest(unittest.TestCase):
    @staticmethod
    def project(helper, layers):
        return patch.object(home_of(helper._find_loaded_layer), "QgsProject", **{
            "instance.return_value.mapLayersByName.return_value": layers,
            "instance.return_value.mapLayers.return_value": {index: layer for index, layer in enumerate(layers)},
        })

    def test_loaded_layer_of_that_file_is_found(self) -> None:
        other, wanted = gpkg_layer(os.path.join(os.sep, "mujal.gpkg")), gpkg_layer()
        for helper in HELPERS:
            with self.subTest(helper=helper.__name__), self.project(helper, [other, wanted]) as project:
                self.assertIs(helper._find_loaded_layer("tööd", GPKG), wanted)
                project.instance.return_value.mapLayersByName.assert_called_once_with("tööd")

    def test_invalid_or_other_layers_are_not_found(self) -> None:
        layers = [object(), gpkg_layer(valid=False), gpkg_layer(os.path.join(os.sep, "mujal.gpkg"))]
        for helper in HELPERS:
            with self.subTest(helper=helper.__name__), self.project(helper, layers):
                self.assertIsNone(helper._find_loaded_layer("tööd", GPKG))

    def test_blank_path_finds_nothing(self) -> None:
        for helper in HELPERS:
            with self.subTest(helper=helper.__name__), self.project(helper, [gpkg_layer("C:/kihid/andmed.shp"), gpkg_layer()]):
                self.assertIsNone(helper._find_loaded_layer("tööd", ""))

    def test_only_layers_of_that_file_are_removed(self) -> None:
        wanted, other = gpkg_layer(), gpkg_layer(os.path.join(os.sep, "mujal.gpkg"))
        for helper in HELPERS:
            with self.subTest(helper=helper.__name__), self.project(helper, [other, object(), wanted]) as project:
                helper._remove_loaded_layers_for_gpkg(GPKG)
                project.instance.return_value.removeMapLayer.assert_called_once_with(wanted.id())

    def test_blank_path_removes_nothing(self) -> None:
        for helper in HELPERS:
            with self.subTest(helper=helper.__name__), self.project(helper, [gpkg_layer("C:/kihid/andmed.shp"), gpkg_layer()]) as project:
                helper._remove_loaded_layers_for_gpkg("")
                project.instance.return_value.removeMapLayer.assert_not_called()


class ReferenceLayerTest(unittest.TestCase):
    @staticmethod
    def resolve(helper, preferred=None, *, stored=None, error=None):
        home = home_of(helper.resolve_reference_layer)
        with patch.object(home, "SettingsService") as settings, patch.object(home, "MapHelpers") as helpers, patch.object(
            home, "PythonFailLogger"
        ) as logger:
            settings.return_value.module_main_layer_name.return_value = "kinnistud"
            helpers.resolve_layer.return_value = stored
            helpers.resolve_layer.side_effect = error
            return helper.resolve_reference_layer(preferred), settings, helpers, logger

    def test_preferred_geopackage_layer_wins_without_looking_further(self) -> None:
        preferred = gpkg_layer()
        for helper in HELPERS:
            with self.subTest(helper=helper.__name__):
                result, _settings, helpers, _logger = self.resolve(helper, preferred, stored=gpkg_layer())
                self.assertIs(result, preferred)
                helpers.resolve_layer.assert_not_called()

    def test_property_layer_is_used_next(self) -> None:
        stored, preferred = gpkg_layer(), gpkg_layer("C:/a.shp")
        for helper in HELPERS:
            with self.subTest(helper=helper.__name__):
                result, settings, helpers, _logger = self.resolve(helper, preferred, stored=stored)
                self.assertIs(result, stored)
                settings.return_value.module_main_layer_name.assert_called_once_with("property")
                helpers.resolve_layer.assert_called_once_with("kinnistud")

    def test_without_a_geopackage_the_preferred_layer_stays(self) -> None:
        preferred = gpkg_layer("C:/a.shp")
        for helper in HELPERS:
            with self.subTest(helper=helper.__name__):
                self.assertIs(self.resolve(helper, preferred, stored=gpkg_layer("C:/b.shp"))[0], preferred)

    def test_without_a_preferred_layer_the_stored_one_is_returned(self) -> None:
        stored = gpkg_layer("C:/b.shp")
        for helper in HELPERS:
            with self.subTest(helper=helper.__name__):
                self.assertIs(self.resolve(helper, None, stored=stored)[0], stored)

    def test_invalid_preferred_layer_is_not_returned(self) -> None:
        for helper in HELPERS:
            with self.subTest(helper=helper.__name__):
                self.assertIsNone(self.resolve(helper, gpkg_layer(valid=False))[0])

    def test_failed_lookup_is_logged(self) -> None:
        for helper in HELPERS:
            with self.subTest(helper=helper.__name__):
                result, _settings, _helpers, logger = self.resolve(helper, error=RuntimeError("settings"))
                self.assertIsNone(result)
                assert_logged(self, logger, helper, "temp_reference_layer_failed")


class CreateOrLoadTest(unittest.TestCase):
    def setUp(self) -> None:
        self.reference = gpkg_layer()
        self.loaded = gpkg_layer()

    def run_helper(self, helper, *, name="Uus", reference="default", found=None, exists=False, layer_exists=False,
                   created=True, load=("default",), error=None, **options):
        home = home_of(helper.create_or_load_layer)
        reference = self.reference if reference == "default" else reference
        load_value = self.loaded if load == ("default",) else load
        with patch.object(home, "GPKGHelpers") as gpkg, patch.object(home, "PythonFailLogger") as logger, patch.object(
            helper, "_find_loaded_layer", return_value=found
        ) as find, patch.object(helper, "_remove_loaded_layers_for_gpkg") as remove, patch.object(
            os, "makedirs"
        ) as makedirs, patch.object(os, "remove") as delete, patch.object(os.path, "exists", return_value=exists):
            gpkg.gpkg_layer_exists.return_value = layer_exists
            gpkg.create_empty_gpkg_layer.return_value = created
            gpkg.create_empty_gpkg_layer.side_effect = error
            gpkg.load_layer_from_gpkg.return_value = load_value
            result = helper.create_or_load_layer(reference, name, **options)
            return result, Mock(gpkg=gpkg, logger=logger, find=find, remove=remove, makedirs=makedirs, delete=delete)

    def expected_path(self) -> str:
        return os.path.normcase(os.path.abspath(GPKG))

    def test_bad_input_gives_its_message(self) -> None:
        for helper in HELPERS:
            with self.subTest(helper=helper.__name__):
                self.assertEqual(self.run_helper(helper, name="  ")[0], (None, "Layer name is empty"))
                self.assertEqual(self.run_helper(helper, reference=None)[0], (None, "Reference layer is invalid"))
                no_gpkg = gpkg_layer("C:/a.shp")
                self.assertEqual(self.run_helper(helper, reference=no_gpkg)[0], (None, "GeoPackage path is empty"))

    def test_loaded_layer_is_reused(self) -> None:
        found = gpkg_layer()
        for helper in HELPERS:
            with self.subTest(helper=helper.__name__):
                result, calls = self.run_helper(helper, found=found)
                self.assertEqual(result, (found, ""))
                calls.find.assert_called_once_with("Uus", self.expected_path())
                calls.gpkg.create_empty_gpkg_layer.assert_not_called()

    def test_existing_layer_in_the_file_is_loaded(self) -> None:
        for helper in HELPERS:
            with self.subTest(helper=helper.__name__):
                result, calls = self.run_helper(helper, layer_exists=True, group_name="Rühm")
                self.assertEqual(result, (self.loaded, ""))
                calls.gpkg.load_layer_from_gpkg.assert_called_once_with(self.expected_path(), "Uus", group_name="Rühm")
                calls.gpkg.create_empty_gpkg_layer.assert_not_called()

    def test_unloadable_existing_layer_gives_its_message(self) -> None:
        for helper in HELPERS:
            with self.subTest(helper=helper.__name__):
                result, _calls = self.run_helper(helper, layer_exists=True, load=None)
                self.assertEqual(result, (None, "Could not load the existing layer from the GeoPackage"))

    def test_new_layer_has_the_module_geometry_and_fields(self) -> None:
        for helper in HELPERS:
            with self.subTest(helper=helper.__name__):
                result, calls = self.run_helper(helper)
                self.assertEqual(result, (self.loaded, ""))
                arguments = calls.gpkg.create_empty_gpkg_layer.call_args.kwargs
                self.assertEqual(arguments["gpkg_path"], self.expected_path())
                self.assertEqual(arguments["layer_name"], "Uus")
                self.assertEqual(arguments["geometry_type"], SPECS[helper][2])
                self.assertIs(arguments["crs"], self.reference.crs.return_value)
                self.assertEqual([f.name() for f in arguments["fields"]], [f.name() for f in helper._build_fields()])
                self.assertFalse(arguments["overwrite"])
                calls.makedirs.assert_called_once_with(os.path.dirname(self.expected_path()), exist_ok=True)

    def test_given_path_is_used_instead_of_the_reference_file(self) -> None:
        target = os.path.join(os.path.abspath(os.sep), "mujal", "uus")
        for helper in HELPERS:
            with self.subTest(helper=helper.__name__):
                _result, calls = self.run_helper(helper, gpkg_path=target)
                self.assertEqual(calls.gpkg.create_empty_gpkg_layer.call_args.kwargs["gpkg_path"],
                                 os.path.normcase(f"{target}.gpkg"))

    def test_failed_creation_and_failed_load_give_their_messages(self) -> None:
        for helper in HELPERS:
            with self.subTest(helper=helper.__name__):
                self.assertEqual(self.run_helper(helper, created=False)[0], (None, "Could not create the layer inside the GeoPackage"))
                self.assertEqual(self.run_helper(helper, load=None)[0], (None, "Layer was created but could not be loaded into the project"))
                self.assertEqual(self.run_helper(helper, load=gpkg_layer(valid=False))[0], (None, "Layer was created but could not be loaded into the project"))

    def test_overwrite_replaces_the_file_even_when_loaded(self) -> None:
        found = gpkg_layer()
        for helper in HELPERS:
            with self.subTest(helper=helper.__name__):
                result, calls = self.run_helper(helper, found=found, exists=True, layer_exists=True, overwrite_file=True)
                self.assertEqual(result, (self.loaded, ""))
                calls.remove.assert_called_once_with(self.expected_path())
                calls.delete.assert_called_once_with(self.expected_path())
                calls.gpkg.create_empty_gpkg_layer.assert_called_once()

    def test_overwrite_of_a_missing_file_deletes_nothing(self) -> None:
        for helper in HELPERS:
            with self.subTest(helper=helper.__name__):
                _result, calls = self.run_helper(helper, exists=False, overwrite_file=True)
                calls.delete.assert_not_called()
                calls.remove.assert_not_called()

    def test_failure_is_logged_and_its_text_returned(self) -> None:
        for helper in HELPERS:
            with self.subTest(helper=helper.__name__):
                result, calls = self.run_helper(helper, error=RuntimeError("ketas täis"))
                self.assertEqual(result, (None, "ketas täis"))
                assert_logged(self, calls.logger, helper, "temp_layer_create_failed")
                self.assertEqual(calls.logger.log_exception.call_args.kwargs["extra"], {"layer": "Uus"})


class FieldsTest(unittest.TestCase):
    @staticmethod
    def schema(helper) -> list:
        return [(field.name(), field.type()) for field in helper._build_fields()]

    def test_project_fields(self) -> None:
        self.assertEqual(self.schema(ProjectsTempLayerHelper), [
            ("ext_project_id", QVariant.String), ("ext_system", QVariant.String), ("ext_project_name", QVariant.String),
            ("ext_project_number", QVariant.String), ("detailed", QVariant.String), ("active", QVariant.Bool),
            ("added_by", QVariant.String), ("added_date", QVariant.DateTime), ("updated_by", QVariant.String),
            ("update_date", QVariant.DateTime),
        ])

    def test_works_fields(self) -> None:
        self.assertEqual(self.schema(WorksTempLayerHelper), [
            ("ext_job_id", QVariant.LongLong), ("ext_job_name", QVariant.String), ("ext_job_type", QVariant.LongLong),
            ("ext_job_state", QVariant.LongLong), ("detailed", QVariant.String), ("active", QVariant.Bool),
            ("begin_date", QVariant.DateTime), ("end_date", QVariant.DateTime), ("added_by", QVariant.String),
            ("added_date", QVariant.DateTime), ("updated_by", QVariant.String), ("update_date", QVariant.DateTime),
        ])

    def test_default_layer_names(self) -> None:
        self.assertEqual(WorksTempLayerHelper.DEFAULT_LAYER_NAME, "Works_Temp")
        self.assertTrue(ProjectsTempLayerHelper.DEFAULT_LAYER_NAME)


if __name__ == "__main__":
    unittest.main()
