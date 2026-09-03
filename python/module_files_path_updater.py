"""Validated module-specific updates for the common ``filesPath`` field."""

from __future__ import annotations

from typing import Any


_MODULE_MUTATIONS = {
    "project": {
        "query_filename": "updateProjectFilesPath.graphql",
        "mutation_root": "updateProject",
    },
}


class ModuleFilesPathUpdater:
    """Update and verify a module item's ``filesPath`` value.

    A module is enabled only after its dedicated GraphQL document and response
    shape have been verified. Adding another module requires one mapping entry
    and one small mutation document in that module's query directory.
    """

    def __init__(self, *, query_loader=None, api_client=None) -> None:
        self._query_loader = query_loader
        self._api_client = api_client

    @staticmethod
    def _module_key(module: Any) -> str:
        value = getattr(module, "value", module)
        return str(value or "").strip().lower()

    def _loader(self):
        if self._query_loader is None:
            from .GraphQLQueryLoader import GraphQLQueryLoader

            self._query_loader = GraphQLQueryLoader()
        return self._query_loader

    def _client(self):
        if self._api_client is None:
            from .api_client import APIClient

            self._api_client = APIClient()
        return self._api_client

    def update(self, module: Any, item_id: object, files_path: object) -> dict[str, Any]:
        module_key = self._module_key(module)
        spec = _MODULE_MUTATIONS.get(module_key)
        if not spec:
            raise ValueError(f"filesPath updates are not configured for module: {module_key or '-'}")

        resolved_id = str(item_id or "").strip()
        resolved_path = str(files_path or "").strip()
        if not resolved_id:
            raise ValueError("A module item ID is required for a filesPath update")
        if not resolved_path:
            raise ValueError("A non-empty filesPath value is required")

        query = self._loader().load_query_by_module(
            module_key,
            spec["query_filename"],
        )
        variables = {
            "input": {
                "id": resolved_id,
                "filesPath": resolved_path,
            }
        }
        response = self._client().send_query(
            query,
            variables=variables,
            return_raw=True,
        )

        if not isinstance(response, dict):
            raise RuntimeError("filesPath update returned an invalid response")
        if response.get("errors"):
            raise RuntimeError("filesPath update returned GraphQL errors")

        data = response.get("data") or {}
        updated = data.get(spec["mutation_root"]) if isinstance(data, dict) else None
        if not isinstance(updated, dict):
            raise RuntimeError(f"filesPath update did not return {spec['mutation_root']}")

        returned_id = str(updated.get("id") or "").strip()
        returned_path = str(updated.get("filesPath") or "").strip()
        if returned_id != resolved_id:
            raise RuntimeError("filesPath update returned a different module item ID")
        if returned_path != resolved_path:
            raise RuntimeError("filesPath update did not return the requested path")

        return updated
