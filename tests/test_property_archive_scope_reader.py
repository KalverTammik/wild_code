"""Headless reads behind the add-property dialog's archive plan.

These were dialog methods; they now take the layers, scope and translator as arguments,
so they are tested on real memory layers without a dialog.
"""
from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
PLUGIN_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLUGIN_ROOT.parent))
if os.environ.get("QGIS_PREFIX_PATH"):
    sys.path.append(str(Path(os.environ["QGIS_PREFIX_PATH"]) / "python" / "plugins"))

from qgis.core import QgsApplication, QgsFeature, QgsVectorLayer

from Kavitro_dev.constants.cadastral_fields import Katastriyksus
from Kavitro_dev.languages.translation_keys import TranslationKeys
from Kavitro_dev.modules.Property.FlowControllers.property_archive_plan import PropertyArchiveScope
from Kavitro_dev.modules.Property.FlowControllers.property_archive_scope_reader import (
    archive_candidate_row,
    find_import_tunnused,
    layer_identity,
    read_scope_features,
)
from Kavitro_dev.modules.Property.FlowControllers.property_check_run import main_check_batch_params
from Kavitro_dev.modules.Property.dialogs.add_property import archive_plan_mixin
from Kavitro_dev.modules.Property.dialogs.add_property.archive_plan_mixin import PropertyArchivePlanMixin

_APP = QgsApplication.instance() or QgsApplication([], False)
if QgsApplication.instance() is _APP:
    QgsApplication.initQgis()

FIELDS = (Katastriyksus.tunnus, Katastriyksus.mk_nimi, Katastriyksus.ov_nimi, Katastriyksus.ay_nimi)


def _layer(rows, fields=FIELDS):
    spec = "&".join(f"field={name}:string" for name in fields)
    layer = QgsVectorLayer(f"None?{spec}", "scope_test", "memory")
    features = []
    for row in rows:
        feature = QgsFeature(layer.fields())
        feature.setAttributes(list(row))
        features.append(feature)
    layer.dataProvider().addFeatures(features)
    return layer


def _scope(settlements=("Küla A",)):
    return PropertyArchiveScope.create(
        county="Harju maakond",
        municipality="Saue vald",
        settlements=settlements,
        import_tunnused={"1"},
        import_layer_id="id",
        import_layer_source="src",
        load_succeeded=True,
    )


ROWS = [
    ("1", "Harju maakond", "Saue vald", "Küla A"),
    ("2", "Harju maakond", "Saue vald", "Küla A"),
    ("2", "Harju maakond", "Saue vald", "Küla A"),  # duplicate tunnus: first one wins
    ("3", "Harju maakond", "Saue vald", "Küla B"),
    ("4", "Tartu maakond", "Tartu vald", "Küla A"),
    ("", "Harju maakond", "Saue vald", "Küla A"),
]


class ReadScopeFeaturesTest(unittest.TestCase):
    def test_returns_features_inside_the_scope_by_tunnus(self):
        result = read_scope_features(_layer(ROWS), _scope())

        self.assertEqual(sorted(result), ["1", "2"])
        layer_ids = sorted(f.id() for f in _layer(ROWS).getFeatures() if f.attribute(Katastriyksus.tunnus) == "2")
        self.assertEqual(result["2"].id(), layer_ids[0])

    def test_several_settlements(self):
        result = read_scope_features(_layer(ROWS), _scope(settlements=("Küla A", "Küla B")))

        self.assertEqual(sorted(result), ["1", "2", "3"])

    def test_missing_or_invalid_layer_raises(self):
        with self.assertRaises(RuntimeError):
            read_scope_features(None, _scope())
        invalid = Mock()
        invalid.isValid.return_value = False
        with self.assertRaises(RuntimeError):
            read_scope_features(invalid, _scope())

    def test_missing_field_raises_and_names_it(self):
        layer = _layer([("1", "Harju maakond", "Saue vald")], fields=FIELDS[:3])
        with self.assertRaisesRegex(RuntimeError, Katastriyksus.ay_nimi):
            read_scope_features(layer, _scope())


class FindImportTunnusedTest(unittest.TestCase):
    def test_finds_the_asked_tunnused_anywhere_in_the_layer(self):
        found = find_import_tunnused(_layer(ROWS), {"3", "4", "9"})

        self.assertEqual(found, {"3", "4"})

    def test_rows_the_filter_let_through_are_still_checked(self):
        rows = [SimpleNamespace(attribute=lambda name, t=t: t) for t in ("3", "8")]
        layer = Mock()
        layer.isValid.return_value = True
        layer.fields.return_value.lookupField.return_value = 0
        layer.getFeatures.return_value = rows

        self.assertEqual(find_import_tunnused(layer, {"3"}), {"3"})

    def test_nothing_asked_reads_nothing(self):
        self.assertEqual(find_import_tunnused(None, set()), set())

    def test_missing_layer_or_field_raises(self):
        with self.assertRaises(RuntimeError):
            find_import_tunnused(None, {"1"})
        layer = _layer([("x",)], fields=(Katastriyksus.mk_nimi,))
        with self.assertRaisesRegex(RuntimeError, Katastriyksus.tunnus):
            find_import_tunnused(layer, {"1"})


class LayerIdentityTest(unittest.TestCase):
    def test_real_layer(self):
        layer = _layer([])
        self.assertEqual(layer_identity(layer), (layer.id(), layer.source()))

    def test_deleted_or_missing(self):
        deleted = SimpleNamespace(id=Mock(side_effect=RuntimeError("deleted")), source=lambda: "memory://x")
        self.assertEqual(layer_identity(deleted), ("", "memory://x"))
        self.assertEqual(layer_identity(None), ("", ""))
        self.assertEqual(layer_identity(object()), ("", ""))


def _translate(key):
    return f"<{key}>"


class ArchiveCandidateRowTest(unittest.TestCase):
    def _row(self, backend_info):
        return archive_candidate_row("7", backend_info, settlement="Küla A", translate=_translate)

    def test_one_active_match_may_be_archived(self):
        row = self._row({"exists": True, "active_ids": ["55"], "active_count": 1})

        self.assertEqual(row, {
            "tunnus": "7",
            "settlement": "Küla A",
            "backend_allowed": True,
            "backend_label": f"<{TranslationKeys.PROPERTY_ARCHIVE_PLAN_BACKEND_ARCHIVE}>",
            "note": "",
        })

    def test_several_active_matches_are_not_archived(self):
        for info in ({"exists": True, "active_ids": ["1", "2"]},
                     {"exists": True, "active_ids": ["1"], "active_count": 2}):
            row = self._row(info)
            self.assertFalse(row["backend_allowed"])
            self.assertEqual(row["backend_label"], f"<{TranslationKeys.PROPERTY_ARCHIVE_PLAN_BACKEND_MULTIPLE}>")

    def test_no_active_match(self):
        row = self._row({"exists": False, "active_ids": [" ", ""]})

        self.assertFalse(row["backend_allowed"])
        self.assertEqual(row["backend_label"], f"<{TranslationKeys.PROPERTY_ARCHIVE_PLAN_BACKEND_MISSING}>")
        self.assertEqual(row["note"], "")

    def test_failed_lookup_is_noted(self):
        failed = f"<{TranslationKeys.PROPERTY_ARCHIVE_PLAN_BACKEND_FAILED}>"
        for info in (None, "error", {"exists": None}):
            row = self._row(info)
            self.assertFalse(row["backend_allowed"])
            self.assertEqual((row["backend_label"], row["note"]), (failed, failed))


IMPORT_ROWS = [
    ("1", "Harju maakond", "Saue vald", "Küla A"),
    ("3", "Harju maakond", "Saue vald", "Küla B"),  # moved out of the scope
]
MAIN_ROWS = [
    ("1", "Harju maakond", "Saue vald", "Küla A"),
    ("2", "Harju maakond", "Saue vald", "Küla A"),
    ("3", "Harju maakond", "Saue vald", "Küla A"),
]


class _Host(PropertyArchivePlanMixin):
    """The dialog state the archive mixin reads, without a dialog."""

    def __init__(self, scope, main_layer):
        self._archive_scope_snapshot = scope
        self._archive_scope_blocked_reason = ""
        self._archive_preliminary_missing = set()
        self._archive_moved_elsewhere = set()
        self._archive_candidate_settlement = {}
        self._main_layer = main_layer
        self.lang_manager = SimpleNamespace(translate=_translate)

    def _plan_main_layer(self):
        return self._main_layer

    def _current_location_scope(self):
        return self._archive_scope_snapshot.key


class ArchivePlanMixinTest(unittest.TestCase):
    def setUp(self):
        self.import_layer = _layer(IMPORT_ROWS)
        self.main_layer = _layer(MAIN_ROWS)
        self.scope = PropertyArchiveScope.create(
            county="Harju maakond", municipality="Saue vald", settlements=("Küla A",),
            import_tunnused={"1"}, import_layer_id=self.import_layer.id(),
            import_layer_source=self.import_layer.source(), load_succeeded=True,
        )
        self.host = _Host(self.scope, self.main_layer)
        tag_patch = patch.object(archive_plan_mixin.MapHelpers, "get_layer_by_tag",
                                 side_effect=lambda _tag: self.import_layer)
        tag_patch.start()
        self.addCleanup(tag_patch.stop)

    def test_plan_reads_the_main_layer_and_skips_properties_moved_elsewhere(self):
        self.assertEqual(self.host._compute_scoped_archive_plan(), {"2"})
        self.assertEqual(self.host._archive_moved_elsewhere, {"3"})
        self.assertEqual(self.host._archive_preliminary_missing, {"2", "3"})
        self.assertEqual(self.host._archive_candidate_settlement, {"2": "Küla A"})

    def test_plan_is_current_for_the_same_import_layer(self):
        self.host._compute_scoped_archive_plan()

        self.assertTrue(self.host._archive_scope_is_current())

    def test_plan_is_stale_when_another_layer_has_the_tag(self):
        self.host._compute_scoped_archive_plan()
        self.import_layer = _layer(IMPORT_ROWS)  # same rows, a different layer

        self.assertFalse(self.host._archive_scope_is_current())

    def test_plan_is_stale_when_a_moved_property_comes_back(self):
        self.host._compute_scoped_archive_plan()
        self.import_layer.dataProvider().deleteFeatures(
            [f.id() for f in self.import_layer.getFeatures() if f.attribute(Katastriyksus.tunnus) == "3"])

        self.assertFalse(self.host._archive_scope_is_current())

    def test_candidate_row_carries_the_settlement(self):
        self.host._compute_scoped_archive_plan()
        row = self.host._archive_candidate_row("2", {"exists": True, "active_ids": ["9"]})

        self.assertEqual(row["settlement"], "Küla A")
        self.assertTrue(row["backend_allowed"])


class MainCheckBatchParamsTest(unittest.TestCase):
    def test_batch_size_and_pause_by_row_count(self):
        self.assertEqual(main_check_batch_params(0), (30, 0))
        self.assertEqual(main_check_batch_params(49), (30, 0))
        self.assertEqual(main_check_batch_params(50), (50, 0))
        self.assertEqual(main_check_batch_params(199), (50, 0))
        self.assertEqual(main_check_batch_params(200), (50, 5))


if __name__ == "__main__":
    unittest.main()
