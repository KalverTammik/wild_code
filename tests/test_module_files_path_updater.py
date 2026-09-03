import unittest
from pathlib import Path

from python.module_files_path_updater import ModuleFilesPathUpdater


class FakeQueryLoader:
    def __init__(self) -> None:
        self.calls = []

    def load_query_by_module(self, module, query_filename):
        self.calls.append((module, query_filename))
        return "project-files-path-mutation"


class FakeApiClient:
    def __init__(self, response) -> None:
        self.response = response
        self.calls = []

    def send_query(self, query, variables=None, **kwargs):
        self.calls.append((query, variables, kwargs))
        return self.response


class ModuleFilesPathUpdaterTest(unittest.TestCase):
    def _updater(self, response):
        loader = FakeQueryLoader()
        client = FakeApiClient(response)
        return ModuleFilesPathUpdater(query_loader=loader, api_client=client), loader, client

    def test_project_path_update_uses_dedicated_mutation_and_validates_response(self) -> None:
        item_id = "project-42"
        files_path = r"C:\GIS\Projects\Project-42"
        response = {
            "data": {
                "updateProject": {
                    "id": item_id,
                    "filesPath": files_path,
                }
            }
        }
        updater, loader, client = self._updater(response)

        updated = updater.update("project", item_id, files_path)

        self.assertEqual(updated, response["data"]["updateProject"])
        self.assertEqual(
            loader.calls,
            [("project", "updateProjectFilesPath.graphql")],
        )
        self.assertEqual(
            client.calls,
            [
                (
                    "project-files-path-mutation",
                    {
                        "input": {
                            "id": item_id,
                            "filesPath": files_path,
                        }
                    },
                    {"return_raw": True},
                )
            ],
        )

    def test_different_returned_id_is_rejected(self) -> None:
        updater, _, _ = self._updater(
            {
                "data": {
                    "updateProject": {
                        "id": "another-project",
                        "filesPath": r"C:\GIS\Project-42",
                    }
                }
            }
        )

        with self.assertRaisesRegex(RuntimeError, "different module item ID"):
            updater.update("project", "project-42", r"C:\GIS\Project-42")

    def test_different_returned_path_is_rejected(self) -> None:
        updater, _, _ = self._updater(
            {
                "data": {
                    "updateProject": {
                        "id": "project-42",
                        "filesPath": r"C:\GIS\Another-Project",
                    }
                }
            }
        )

        with self.assertRaisesRegex(RuntimeError, "requested path"):
            updater.update("project", "project-42", r"C:\GIS\Project-42")

    def test_missing_mutation_payload_is_rejected(self) -> None:
        updater, _, _ = self._updater({"data": {}})

        with self.assertRaisesRegex(RuntimeError, "did not return updateProject"):
            updater.update("project", "project-42", r"C:\GIS\Project-42")

    def test_unsupported_module_and_empty_values_are_rejected(self) -> None:
        updater, _, _ = self._updater({})

        with self.assertRaisesRegex(ValueError, "not configured"):
            updater.update("contract", "contract-42", r"C:\GIS\Contract-42")
        with self.assertRaisesRegex(ValueError, "item ID"):
            updater.update("project", "", r"C:\GIS\Project-42")
        with self.assertRaisesRegex(ValueError, "non-empty filesPath"):
            updater.update("project", "project-42", "")

    def test_project_graphql_document_is_minimal_and_returns_verified_fields(self) -> None:
        query_path = (
            Path(__file__).resolve().parents[1]
            / "python"
            / "queries"
            / "graphql"
            / "projects"
            / "updateProjectFilesPath.graphql"
        )
        query = query_path.read_text(encoding="utf-8")

        self.assertIn("mutation UpdateProjectFilesPath", query)
        self.assertIn("updateProject(input: $input)", query)
        self.assertIn("filesPath", query)
        self.assertNotIn("properties", query)


if __name__ == "__main__":
    unittest.main()
