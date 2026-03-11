from __future__ import annotations

from datetime import datetime
from typing import Optional

from qgis.core import QgsFeatureRequest, QgsGeometry, QgsVectorLayer

from ...Logs.python_fail_logger import PythonFailLogger
from ...languages.language_manager import LanguageManager
from ...python.api_actions import APIModuleActions
from ...utils.url_manager import Module
from .works_layer_service import WorksDescriptionService, WorksLayerService


class WorksSyncService:
    def __init__(self, *, lang_manager=None) -> None:
        self._lang = lang_manager or LanguageManager()
        self._layer: Optional[QgsVectorLayer] = None
        self._syncing_from_backend = False
        self._syncing_geometry = False

    def attach(self) -> Optional[QgsVectorLayer]:
        layer = WorksLayerService.resolve_main_layer(lang_manager=self._lang, silent=True)
        if layer is self._layer:
            return layer

        self.detach()
        if not isinstance(layer, QgsVectorLayer) or not layer.isValid():
            return None

        try:
            layer.committedGeometriesChanges.connect(self._on_committed_geometries_changes)
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module=Module.WORKS.value,
                event="works_sync_attach_failed",
            )
            return None

        self._layer = layer
        return layer

    def detach(self) -> None:
        layer = self._layer
        self._layer = None
        if not isinstance(layer, QgsVectorLayer):
            return
        try:
            layer.committedGeometriesChanges.disconnect(self._on_committed_geometries_changes)
        except Exception:
            return

    def sync_from_backend(self) -> None:
        if self._syncing_from_backend:
            return

        layer = self.attach()
        if not isinstance(layer, QgsVectorLayer) or not layer.isValid() or layer.isEditable():
            return

        task_id_field = WorksLayerService.resolve_task_id_field_name(layer)
        if not task_id_field:
            return

        try:
            features = list(layer.getFeatures())
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module=Module.WORKS.value,
                event="works_sync_layer_read_failed",
            )
            return

        if not features:
            return

        task_ids = [
            str(feature.attribute(task_id_field) or "").strip()
            for feature in features
            if str(feature.attribute(task_id_field) or "").strip()
        ]
        if not task_ids:
            return

        tasks_by_id = APIModuleActions.get_tasks_by_ids(task_ids)
        if not tasks_by_id:
            return

        field_indices = {field.name().lower(): index for index, field in enumerate(layer.fields())}
        pending_updates: list[tuple[int, dict[str, object], object]] = []

        for feature in features:
            task_id = str(feature.attribute(task_id_field) or "").strip()
            if not task_id:
                continue

            task = tasks_by_id.get(task_id)
            if not isinstance(task, dict):
                continue

            updates = self._build_layer_updates(task)
            if updates:
                pending_updates.append((feature.id(), updates, feature))

        if not pending_updates:
            return

        self._syncing_from_backend = True
        started_edit = False
        try:
            if not layer.isEditable():
                started_edit = bool(layer.startEditing())
                if not started_edit:
                    return

            changed = False
            for feature_id, updates, feature in pending_updates:
                for canonical_name, new_value in updates.items():
                    field_index = field_indices.get(str(canonical_name).lower())
                    if field_index is None:
                        continue

                    current_value = feature.attribute(field_index)
                    if self._values_equal(current_value, new_value):
                        continue

                    if layer.changeAttributeValue(feature_id, field_index, new_value):
                        changed = True

            if not started_edit:
                return

            if not changed:
                layer.rollBack()
                return

            if not layer.commitChanges():
                errors = "; ".join(layer.commitErrors() or [])
                layer.rollBack()
                raise RuntimeError(errors or "Could not commit Works sync changes")

            layer.triggerRepaint()
        except Exception as exc:
            if started_edit and layer.isEditable():
                try:
                    layer.rollBack()
                except Exception as rollback_exc:
                    PythonFailLogger.log_exception(
                        rollback_exc,
                        module=Module.WORKS.value,
                        event="works_sync_rollback_failed",
                    )
            PythonFailLogger.log_exception(
                exc,
                module=Module.WORKS.value,
                event="works_sync_from_backend_failed",
            )
        finally:
            self._syncing_from_backend = False

    def _on_committed_geometries_changes(self, _layer_id: str, changed_geometries: dict) -> None:
        if self._syncing_geometry or not isinstance(changed_geometries, dict) or not changed_geometries:
            return

        layer = self._layer
        if not isinstance(layer, QgsVectorLayer) or not layer.isValid():
            return

        task_id_field = WorksLayerService.resolve_task_id_field_name(layer)
        if not task_id_field:
            return

        self._syncing_geometry = True
        try:
            for feature_id, geometry in changed_geometries.items():
                self._sync_feature_geometry_to_backend(
                    layer=layer,
                    feature_id=int(feature_id),
                    geometry=geometry,
                    task_id_field=task_id_field,
                )
        finally:
            self._syncing_geometry = False

    def _sync_feature_geometry_to_backend(
        self,
        *,
        layer: QgsVectorLayer,
        feature_id: int,
        geometry: QgsGeometry,
        task_id_field: str,
    ) -> None:
        feature = next(layer.getFeatures(QgsFeatureRequest(feature_id)), None)
        if feature is None:
            return

        task_id = str(feature.attribute(task_id_field) or "").strip()
        if not task_id:
            return

        point = self._geometry_point(geometry or feature.geometry())
        if point is None:
            return

        task = APIModuleActions.get_task_data(task_id)
        if not isinstance(task, dict):
            return

        current_description = str(task.get("description") or "")
        updated_description = WorksDescriptionService.merge_metadata_into_description(
            existing_html=current_description,
            layer=layer,
            point=point,
            lang_manager=self._lang,
            point_in_layer_crs=True,
        )
        if updated_description == current_description:
            return

        try:
            updated = APIModuleActions.update_task_description(task_id, updated_description)
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module=Module.WORKS.value,
                event="works_sync_geometry_push_failed",
                extra={"task_id": task_id},
            )
            return

        if not updated:
            PythonFailLogger.log_exception(
                RuntimeError("Could not update works task description after geometry change"),
                module=Module.WORKS.value,
                event="works_sync_geometry_push_failed",
                extra={"task_id": task_id},
            )

    @staticmethod
    def _build_layer_updates(task: dict) -> dict[str, object]:
        updates: dict[str, object] = {}

        title = str(task.get("name") or task.get("title") or "").strip()
        if title:
            updates["title"] = title

        description = WorksDescriptionService.extract_user_description(task.get("description"))
        updates["description"] = description

        type_name = str(((task.get("type") or {}).get("name") or "")).strip()
        if type_name:
            updates["type"] = type_name

        updates["priority"] = str(task.get("priority") or "").strip()

        status_type = str(((task.get("status") or {}).get("type") or "")).strip().upper()
        if status_type:
            is_active = status_type != "CLOSED"
            updates["status"] = is_active
            updates["active"] = is_active

        created_at = str(task.get("createdAt") or "").strip()
        updated_at = str(task.get("updatedAt") or "").strip()
        if created_at:
            updates["created_at"] = created_at
        if updated_at:
            updates["updated_at"] = updated_at

        display_timestamp = WorksSyncService._format_display_datetime(created_at or updated_at)
        if display_timestamp:
            updates["datetime"] = display_timestamp

        return updates

    @staticmethod
    def _format_display_datetime(value: str) -> str:
        text = str(value or "").strip()
        if not text:
            return ""

        normalized = text.replace("Z", "+00:00")
        try:
            parsed = datetime.fromisoformat(normalized)
            return parsed.strftime("%Y-%m-%d %H:%M")
        except Exception:
            if "T" in text:
                return text.replace("T", " ")[:16]
            return text[:16]

    @staticmethod
    def _values_equal(current_value, new_value) -> bool:
        if isinstance(new_value, bool):
            if isinstance(current_value, bool):
                return current_value is new_value
            current_text = str(current_value or "").strip().lower()
            return (current_text in {"1", "true", "yes"}) is new_value

        current_text = "" if current_value is None else str(current_value).strip()
        new_text = "" if new_value is None else str(new_value).strip()
        return current_text == new_text

    @staticmethod
    def _geometry_point(geometry: Optional[QgsGeometry]):
        if not isinstance(geometry, QgsGeometry) or geometry.isEmpty():
            return None
        try:
            return geometry.vertexAt(0)
        except Exception:
            return None