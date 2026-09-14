from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path


os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
PLUGIN_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLUGIN_ROOT.parent))

from Kavitro_dev.modules.works.works_create_controller import WorksCreateController
from Kavitro_dev.python.api_actions import APIModuleActions
from Kavitro_dev.python.responses import DataDisplayExtractors


MEMBER_EDGE_QUERIES = (
    "python/queries/graphql/connectedData/connected_contracts.graphql",
    "python/queries/graphql/connectedData/connected_coordinations.graphql",
    "python/queries/graphql/connectedData/connected_projects.graphql",
    "python/queries/graphql/connectedData/connected_specifications.graphql",
    "python/queries/graphql/connectedData/connected_submissions.graphql",
    "python/queries/graphql/connectedData/connected_tasks.graphql",
    "python/queries/graphql/contracts/ListFilteredContracts.graphql",
    "python/queries/graphql/contracts/w_contracts_module_data_by_item_id.graphql",
    "python/queries/graphql/coordinations/ListFilteredCoordinations.graphql",
    "python/queries/graphql/coordinations/W_coordination_id.graphql",
    "python/queries/graphql/projects/ListFilteredProjects.graphql",
    "python/queries/graphql/projects/w_projects_module_data_by_item_id.graphql",
    "python/queries/graphql/tasks/ListFilteredTasks.graphql",
    "python/queries/graphql/tasks/w_tasks_module_data_by_item_id.graphql",
)


class DeprecatedGraphqlFieldsTest(unittest.TestCase):
    def test_member_edge_queries_use_responsible(self) -> None:
        for relative_path in MEMBER_EDGE_QUERIES:
            with self.subTest(query=relative_path):
                query = (PLUGIN_ROOT / relative_path).read_text(encoding="utf-8")
                self.assertIn("responsible", query)
                self.assertNotIn("isResponsible", query)

    def test_shared_member_extractor_reads_responsible_edge_flag(self) -> None:
        responsible = {"id": "user-1", "displayName": "Vastutaja"}
        participant = {"id": "user-2", "displayName": "Osaleja"}
        item = {
            "members": {
                "edges": [
                    {"node": responsible, "responsible": True},
                    {"node": participant, "responsible": False},
                ]
            }
        }

        responsible_nodes, participant_nodes = DataDisplayExtractors.extract_members(item)

        self.assertEqual(responsible_nodes, [responsible])
        self.assertEqual(participant_nodes, [participant])

    def test_works_responsible_name_reads_responsible_edge_flag(self) -> None:
        task = {
            "members": {
                "edges": [
                    {
                        "node": {"id": "user-1", "displayName": "Vastutaja"},
                        "responsible": True,
                    }
                ]
            }
        }

        self.assertEqual(
            WorksCreateController._responsible_display_name(task),
            "Vastutaja",
        )

    def test_task_member_input_uses_responsible_pivot_key(self) -> None:
        payload = APIModuleActions._build_task_member_associate_payload(
            ["user-1", "user-2"],
            responsible_id="user-2",
        )

        self.assertEqual(
            payload,
            [
                {"id": "user-1", "responsible": False},
                {"id": "user-2", "responsible": True},
            ],
        )


if __name__ == "__main__":
    unittest.main()
