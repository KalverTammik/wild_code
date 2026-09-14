from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "utils"
    / "mapandproperties"
    / "property_archive_plan.py"
)
SPEC = importlib.util.spec_from_file_location("property_archive_plan_under_test", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)
PropertyArchiveScope = MODULE.PropertyArchiveScope
classify_archive_candidates = MODULE.classify_archive_candidates


class PropertyArchivePlanTest(unittest.TestCase):
    def _scope(self, import_tunnused=("A1", "A2")) -> PropertyArchiveScope:
        return PropertyArchiveScope.create(
            county="Tartu maakond",
            municipality="Elva vald",
            settlements=["Rannu alevik"],
            import_tunnused=import_tunnused,
            import_layer_id="import-1",
            import_layer_source="test.gpkg",
            load_succeeded=True,
        )

    def test_only_missing_tunnused_inside_the_selected_scope_become_candidates(self) -> None:
        result = classify_archive_candidates(
            scope=self._scope(),
            main_scope_tunnused=["A1", "A2", "A3"],
            import_tunnused_found_elsewhere=[],
        )

        self.assertEqual(result.candidates, frozenset({"A3"}))
        self.assertEqual(result.moved_elsewhere, frozenset())
        self.assertFalse(result.blocked)

    def test_tunnus_found_elsewhere_in_import_is_not_archived(self) -> None:
        result = classify_archive_candidates(
            scope=self._scope(),
            main_scope_tunnused=["A1", "A2", "A3"],
            import_tunnused_found_elsewhere=["A3"],
        )

        self.assertEqual(result.candidates, frozenset())
        self.assertEqual(result.moved_elsewhere, frozenset({"A3"}))

    def test_other_settlement_never_enters_the_comparison_input(self) -> None:
        # B1 exists on the wider main layer, but the caller supplies only the
        # features already limited to the selected settlement.
        result = classify_archive_candidates(
            scope=self._scope(),
            main_scope_tunnused=["A1", "A2"],
            import_tunnused_found_elsewhere=[],
        )

        self.assertEqual(result.candidates, frozenset())

    def test_empty_import_scope_blocks_missing_based_archiving(self) -> None:
        scope = self._scope(import_tunnused=[])
        result = classify_archive_candidates(
            scope=scope,
            main_scope_tunnused=["A1"],
            import_tunnused_found_elsewhere=[],
        )

        self.assertTrue(result.blocked)
        self.assertEqual(result.blocked_reason, "empty_import_scope")
        self.assertEqual(result.candidates, frozenset())

    def test_explicit_settlement_is_required(self) -> None:
        scope = PropertyArchiveScope.create(
            county="Tartu maakond",
            municipality="Elva vald",
            settlements=[],
            import_tunnused=["A1"],
            load_succeeded=True,
        )

        self.assertFalse(scope.complete)
        self.assertEqual(scope.blocked_reason, "explicit_settlements_required")

    def test_scope_identity_is_independent_of_table_order(self) -> None:
        first = self._scope(import_tunnused=["A2", "A1"])
        second = self._scope(import_tunnused=["A1", "A2"])

        self.assertEqual(first.identity, second.identity)


if __name__ == "__main__":
    unittest.main()
