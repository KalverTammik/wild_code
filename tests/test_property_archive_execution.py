from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path
from unittest.mock import Mock, patch


os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from Kavitro_dev.modules.Property.FlowControllers import MainAddProperties as flow_module
from Kavitro_dev.modules.Property.FlowControllers.MainAddProperties import MainAddPropertiesFlow
from Kavitro_dev.modules.Property.FlowControllers.UpdatePropertyData import UpdatePropertyData
from Kavitro_dev.utils.mapandproperties import property_action_service as action_service_module
from Kavitro_dev.utils.mapandproperties.property_action_service import PropertyActionService


class _Feature:
    def __init__(self, feature_id: int):
        self._feature_id = feature_id

    def id(self) -> int:
        return self._feature_id


class _Layer:
    def __init__(self, *, commit_ok: bool = True, editable: bool = False):
        self._editable = editable
        self._commit_ok = commit_ok
        self.start_calls = 0
        self.commit_calls = 0
        self.rollback_calls = 0
        self.delete_calls: list[list[int]] = []

    def isEditable(self) -> bool:
        return self._editable

    def startEditing(self) -> bool:
        self.start_calls += 1
        self._editable = True
        return True

    def commitChanges(self) -> bool:
        self.commit_calls += 1
        if self._commit_ok:
            self._editable = False
        return self._commit_ok

    def commitErrors(self) -> list[str]:
        return ["test commit failure"] if not self._commit_ok else []

    def rollBack(self) -> bool:
        self.rollback_calls += 1
        self._editable = False
        return True

    def deleteFeatures(self, feature_ids) -> bool:
        self.delete_calls.append(list(feature_ids))
        return True


class PropertyArchiveExecutionTest(unittest.TestCase):
    def _run(self, target, archive, *, backend_allowed=None, backend_result=None):
        backend_info = backend_result or {
            "exists": True,
            "active_ids": ["backend-1"],
        }
        with (
            patch.object(
                MainAddPropertiesFlow,
                "_prepare_layers",
                return_value=(object(), target, archive),
            ),
            patch.object(
                flow_module.MapHelpers,
                "find_features_by_fields_and_values",
                return_value=[_Feature(41)],
            ),
            patch.object(
                flow_module.FeatureActions,
                "copy_feature_to_layer",
                return_value=(True, ""),
            ),
            patch.object(
                flow_module.BackendPropertyVerifier,
                "verify_properties_by_cadastral_number",
                return_value=backend_info,
            ) as verify,
            patch.object(
                flow_module.UpdatePropertyData,
                "_archive_a_propertie",
                return_value=True,
            ) as archive_backend,
        ):
            result = MainAddPropertiesFlow.archive_missing_from_import(
                ["T1"],
                backend_allowed=backend_allowed,
            )
        return result, verify, archive_backend

    def test_archive_commit_failure_never_deletes_from_main(self) -> None:
        target = _Layer()
        archive = _Layer(commit_ok=False)

        result, verify, archive_backend = self._run(
            target,
            archive,
            backend_allowed={"T1"},
        )

        self.assertEqual(target.start_calls, 0)
        self.assertEqual(target.delete_calls, [])
        self.assertEqual(result["moved_map"], 0)
        self.assertTrue(result["errors"])
        verify.assert_not_called()
        archive_backend.assert_not_called()

    def test_backend_failure_is_not_counted_as_success(self) -> None:
        target = _Layer()
        archive = _Layer()

        with patch.object(
            flow_module.UpdatePropertyData,
            "_archive_a_propertie",
            return_value=False,
        ):
            with (
                patch.object(
                    MainAddPropertiesFlow,
                    "_prepare_layers",
                    return_value=(object(), target, archive),
                ),
                patch.object(
                    flow_module.MapHelpers,
                    "find_features_by_fields_and_values",
                    return_value=[_Feature(41)],
                ),
                patch.object(
                    flow_module.FeatureActions,
                    "copy_feature_to_layer",
                    return_value=(True, ""),
                ),
                patch.object(
                    flow_module.BackendPropertyVerifier,
                    "verify_properties_by_cadastral_number",
                    return_value={"exists": True, "active_ids": ["backend-1"]},
                ),
            ):
                result = MainAddPropertiesFlow.archive_missing_from_import(
                    ["T1"],
                    backend_allowed={"T1"},
                )

        self.assertEqual(result["moved_map"], 1)
        self.assertEqual(result["archived_backend"], 0)
        self.assertEqual(result["backend_failed"], 1)
        self.assertTrue(result["errors"])

    def test_backend_action_not_in_confirmed_plan_is_skipped(self) -> None:
        target = _Layer()
        archive = _Layer()

        result, verify, archive_backend = self._run(
            target,
            archive,
            backend_allowed=set(),
        )

        self.assertEqual(result["moved_map"], 1)
        self.assertEqual(result["backend_skipped"], 1)
        verify.assert_not_called()
        archive_backend.assert_not_called()

    def test_existing_edit_buffer_blocks_the_archive_plan(self) -> None:
        target = _Layer(editable=True)
        archive = _Layer()

        result, verify, archive_backend = self._run(
            target,
            archive,
            backend_allowed={"T1"},
        )

        self.assertEqual(target.delete_calls, [])
        self.assertEqual(archive.start_calls, 0)
        self.assertTrue(result["errors"])
        verify.assert_not_called()
        archive_backend.assert_not_called()

    def test_backend_status_failure_makes_archive_fail_before_metadata_changes(self) -> None:
        with (
            patch.object(
                UpdatePropertyData,
                "_set_backend_property_status",
                return_value=False,
            ),
            patch.object(UpdatePropertyData, "_update_property_tags") as update_tags,
        ):
            result = UpdatePropertyData._archive_a_propertie("backend-1", archive_tag="tag-1")

        self.assertFalse(result)
        update_tags.assert_not_called()

    def test_property_action_service_reports_backend_failures(self) -> None:
        with patch.object(
            action_service_module.BackendPropertyActions,
            "archive_properties_by_tunnused",
            return_value={"total": 2, "succeeded": 1, "skipped": 0, "failed": 1},
        ):
            result = PropertyActionService.run_action("archive", ["T1", "T2"])

        self.assertFalse(result.ok)
        self.assertIn("failed: 1", result.message)
        self.assertIsNotNone(result.error)


if __name__ == "__main__":
    unittest.main()
