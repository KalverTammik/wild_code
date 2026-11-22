"""Geometry actions: the geometry input value, the input errors create_task retries on, and the geometry updates."""
import json
import re

from ..api_client import APIClient
from ..GraphQLQueryLoader import GraphQLQueryLoader
from ...Logs.python_fail_logger import PythonFailLogger
from ...constants.module_names import Module


class GeometryActions:
    """Static geometry actions; APIModuleActions inherits them so callers keep one entry point."""

    @staticmethod
    def _geometry_input_value(geometry: dict) -> str:
        return json.dumps(geometry, ensure_ascii=False, separators=(",", ":"))

    @staticmethod
    def _is_unknown_input_field_error(message: str, field_name: str) -> bool:
        text = str(message or "").lower()
        field_text = str(field_name or "").strip().lower()
        # The whole name only: "status" must not match "statusId".
        if not field_text or not re.search(rf"(?<!\w){re.escape(field_text)}(?!\w)", text):
            return False

        unknown_field_markers = (
            "unknown field",
            "not defined",
            "undefined field",
            "field is not defined",
            "does not exist on type",
            "did you mean",
        )
        return any(marker in text for marker in unknown_field_markers)

    @staticmethod
    def _is_unknown_geometry_input_error(message: str) -> bool:
        return GeometryActions._is_unknown_input_field_error(message, "geometry")

    @staticmethod
    def _is_geometry_retryable_create_error(message: str) -> bool:
        text = str(message or "").lower()
        if GeometryActions._is_unknown_geometry_input_error(message):
            return True

        # Only errors the server returns in its answer; HTTP status errors leave the create's outcome unknown.
        retryable_markers = (
            "internal server error",
            "geojson",
            "json",
            "icon",
            "iconcolor",
        )
        return any(marker in text for marker in retryable_markers)

    @staticmethod
    def _update_module_geometry(
        *,
        item_id: str,
        geometry: dict,
        module: str,
        query_filename: str,
        response_key: str,
        failure_event: str,
        empty_event: str,
    ) -> bool:
        resolved_id = str(item_id or "").strip()
        if not resolved_id or not isinstance(geometry, dict):
            return False

        variables = {
            "input": {
                "id": resolved_id,
                "geometry": GeometryActions._geometry_input_value(geometry),
            }
        }

        loader = GraphQLQueryLoader()
        client = APIClient()
        try:
            query = loader.load_query_by_module(module, query_filename)
            data = client.send_query(query, variables=variables) or {}
            updated = (data.get(response_key) or {}) if isinstance(data, dict) else {}
            if updated.get("id"):
                return True
            PythonFailLogger.log_exception(
                RuntimeError(f"{response_key} geometry update returned no id"),
                module=module,
                event=empty_event,
                extra={
                    "item_id": resolved_id,
                    "geometry_type": str(geometry.get("type") or ""),
                },
            )
            return False
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module=module,
                event=failure_event,
                extra={"item_id": resolved_id},
            )
            return False

    @staticmethod
    def update_task_geometry(item_id: str, geometry: dict) -> bool:
        """Update the task geometry field in the backend."""

        return GeometryActions._update_module_geometry(
            item_id=item_id,
            geometry=geometry,
            module=Module.TASK.value,
            query_filename="updateTaskGeometry.graphql",
            response_key="updateTask",
            failure_event="task_update_geometry_failed",
            empty_event="task_update_geometry_empty_response",
        )

    @staticmethod
    def update_project_geometry(item_id: str, geometry: dict) -> bool:
        """Update the project geometry field in the backend."""

        return GeometryActions._update_module_geometry(
            item_id=item_id,
            geometry=geometry,
            module=Module.PROJECT.value,
            query_filename="updateProjectGeometry.graphql",
            response_key="updateProject",
            failure_event="project_update_geometry_failed",
            empty_event="project_update_geometry_empty_response",
        )

    @staticmethod
    def update_easement_geometry(item_id: str, geometry: dict) -> bool:
        """Update the easement geometry field in the backend."""

        return GeometryActions._update_module_geometry(
            item_id=item_id,
            geometry=geometry,
            module=Module.EASEMENT.value,
            query_filename="updateEasementGeometry.graphql",
            response_key="updateEasement",
            failure_event="easement_update_geometry_failed",
            empty_event="easement_update_geometry_empty_response",
        )
