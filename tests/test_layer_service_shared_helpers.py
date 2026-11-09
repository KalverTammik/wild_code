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

from qgis.core import QgsVectorLayer

from Kavitro_dev.modules.asbuilt.asbuilt_layer_service import AsBuiltLayerService
from Kavitro_dev.modules.easements.easement_layer_service import EasementLayerService
from Kavitro_dev.modules.projects.projects_layer_service import ProjectsLayerService
from Kavitro_dev.modules.works.works_layer_service import WorksLayerService

ALL_SERVICES = (AsBuiltLayerService, EasementLayerService, ProjectsLayerService, WorksLayerService)
LAYER_LOOKUP_SERVICES = (AsBuiltLayerService, EasementLayerService, ProjectsLayerService)
FIELD_WRITE_SERVICES = (AsBuiltLayerService, EasementLayerService, ProjectsLayerService)
PLAIN_INT_SERVICES = (AsBuiltLayerService, EasementLayerService)
REFRESH_SERVICES = (EasementLayerService, ProjectsLayerService)
NAME_LABEL_SERVICES = (AsBuiltLayerService, ProjectsLayerService)


def home_of(function):
    """The module whose names a helper resolves, wherever the helper is defined."""
    return sys.modules[function.__module__]


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
        for service in LAYER_LOOKUP_SERVICES:
            for identifier in (None, "", "   "):
                with self.subTest(service=service.__name__, identifier=identifier):
                    found, helpers = self.lookup(service, identifier, layers=[self.named("")])
                    self.assertEqual(found, [])
                    helpers.find_layer_by_id.assert_not_called()

    def test_layer_id_wins_over_names(self) -> None:
        direct = self.named("id match")
        for service in LAYER_LOOKUP_SERVICES:
            with self.subTest(service=service.__name__):
                found, helpers = self.lookup(service, "  abc ", direct=direct, layers=[self.named("abc")])
                self.assertEqual(found, [direct])
                helpers.find_layer_by_id.assert_called_once_with("abc")

    def test_names_match_without_case_and_surrounding_spaces(self) -> None:
        first, second, other = self.named("Tööd"), self.named("  TÖÖD "), self.named("Muu")
        for service in LAYER_LOOKUP_SERVICES:
            with self.subTest(service=service.__name__):
                found, _helpers = self.lookup(service, " TööD ", layers=[first, other, second])
                self.assertEqual(found, [first, second])

    def test_layer_that_cannot_report_its_name_is_skipped(self) -> None:
        broken, good = Mock(), self.named("Tööd")
        broken.name.side_effect = RuntimeError("deleted")
        for service in LAYER_LOOKUP_SERVICES:
            with self.subTest(service=service.__name__):
                found, _helpers = self.lookup(service, "tööd", layers=[broken, good])
                self.assertEqual(found, [good])

    def test_without_a_project_nothing_is_found(self) -> None:
        for service in LAYER_LOOKUP_SERVICES:
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
    SHARED = ("_configured_layers", "_layer_target_label", "_refresh_saved_layer", "_resolve_first_field_name",
              "_set_attr_if_present", "coerce_optional_int", "parse_backend_datetime")
    KEPT_ON_PURPOSE = {(EasementLayerService, "_layer_target_label"), (WorksLayerService, "coerce_optional_int")}

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
