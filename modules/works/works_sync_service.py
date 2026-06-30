from __future__ import annotations

from datetime import datetime
from typing import Optional

from qgis.core import QgsFeatureRequest, QgsGeometry, QgsVectorLayer

from ...Logs.python_fail_logger import PythonFailLogger
from ...languages.language_manager import LanguageManager
from ...python.api_actions import APIModuleActions
from ...utils.url_manager import Module
from .works_layer_service import WorksLayerService


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
        if not isinstance(layer, QgsVectorLayer) or not layer.isValid():
            return
        if self._is_layer_editable(layer, event="works_sync_skipped_layer_editable"):
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

        feature_ids_by_task_id = self._feature_ids_by_task_id(features, task_id_field)
        if not feature_ids_by_task_id:
            return

        self._log_duplicate_task_ids(feature_ids_by_task_id)

        task_ids = list(feature_ids_by_task_id.keys())
        if not task_ids:
            return

        tasks_by_id = APIModuleActions.get_tasks_by_ids(task_ids)
        self._log_missing_backend_tasks(task_ids, tasks_by_id)
        if not tasks_by_id:
            return

        pending_updates: list[tuple[int, dict[str, object], object]] = []

        for feature in features:
            task_id = str(feature.attribute(task_id_field) or "").strip()
            if not task_id:
                continue

            task = tasks_by_id.get(task_id)
            if not isinstance(task, dict):
                continue

            updates = self._build_layer_updates(task)
            geometry = WorksLayerService.geometry_from_payload(task.get("geometry"))
            if isinstance(geometry, QgsGeometry):
                updates["__geometry"] = geometry

            if updates:
                pending_updates.append((feature.id(), updates, feature))

        if not pending_updates:
            return

        self._apply_pending_updates(layer=layer, pending_updates=pending_updates)

    def sync_task_from_backend(self, task_id: str, *, task: Optional[dict] = None) -> None:
        if self._syncing_from_backend:
            return

        task_id_text = str(task_id or "").strip()
        if not task_id_text:
            return

        layer = self.attach()
        if not isinstance(layer, QgsVectorLayer) or not layer.isValid():
            return
        if self._is_layer_editable(layer, event="works_sync_task_skipped_layer_editable", extra={"task_id": task_id_text}):
            return

        feature = WorksLayerService.find_feature_by_task_id(layer, task_id_text)
        if feature is None:
            return

        task_payload = task if isinstance(task, dict) else APIModuleActions.get_task_data(task_id_text)
        if not isinstance(task_payload, dict):
            return

        updates = self._build_layer_updates(task_payload)
        geometry = WorksLayerService.geometry_from_payload(task_payload.get("geometry"))
        if isinstance(geometry, QgsGeometry):
            updates["__geometry"] = geometry

        if not updates:
            return

        self._apply_pending_updates(layer=layer, pending_updates=[(feature.id(), updates, feature)])

    def _apply_pending_updates(
        self,
        *,
        layer: QgsVectorLayer,
        pending_updates: list[tuple[int, dict[str, object], object]],
    ) -> None:
        if not pending_updates:
            return

        if self._is_layer_editable(layer, event="works_sync_apply_skipped_layer_editable"):
            return

        self._syncing_from_backend = True
        started_edit = False
        try:
            field_indices = {field.name().lower(): index for index, field in enumerate(layer.fields())}

            started_edit = bool(layer.startEditing())
            if not started_edit:
                return

            changed = False
            for feature_id, updates, feature in pending_updates:
                geometry_update = updates.pop("__geometry", None)
                if isinstance(geometry_update, QgsGeometry):
                    current_geometry = feature.geometry() if hasattr(feature, "geometry") else None
                    if not self._geometries_equal(current_geometry, geometry_update):
                        if layer.changeGeometry(feature_id, geometry_update):
                            changed = True

                for canonical_name, new_value in updates.items():
                    field_index = field_indices.get(str(canonical_name).lower())
                    if field_index is None:
                        continue

                    field = layer.fields()[field_index]
                    coerced_value = WorksLayerService.coerce_value_for_field(field, new_value)
                    current_value = feature.attribute(field_index)
                    if self._values_equal(current_value, coerced_value):
                        continue

                    if layer.changeAttributeValue(feature_id, field_index, coerced_value):
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
        if self._syncing_from_backend or self._syncing_geometry or not isinstance(changed_geometries, dict) or not changed_geometries:
            return

        layer = self._layer
        if not isinstance(layer, QgsVectorLayer) or not layer.isValid():
            return

        task_id_field = WorksLayerService.resolve_task_id_field_name(layer)
        if not task_id_field:
            return

        self._syncing_geometry = True
        try:
            changed_feature_ids: list[int] = []
            for feature_id, geometry in changed_geometries.items():
                current_feature_id = int(feature_id)
                changed_feature_ids.append(current_feature_id)
                self._sync_feature_geometry_to_backend(
                    layer=layer,
                    feature_id=current_feature_id,
                    geometry=geometry,
                    task_id_field=task_id_field,
                )
            self._stamp_geometry_audit_fields(layer=layer, feature_ids=changed_feature_ids)
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

        task = APIModuleActions.get_task_data(task_id)
        status_color = WorksLayerService.status_color_from_task(task)

        geometry_payload = WorksLayerService.backend_geometry_payload_from_geometry(geometry or feature.geometry())
        geometry_payload = WorksLayerService.styled_backend_geometry_payload(
            geometry_payload,
            color=status_color,
        )
        if geometry_payload is not None:
            try:
                APIModuleActions.update_task_geometry(task_id, geometry_payload)
            except Exception as exc:
                PythonFailLogger.log_exception(
                    exc,
                    module=Module.WORKS.value,
                    event="works_sync_update_geometry_failed",
                    extra={"task_id": task_id},
                )

    @staticmethod
    def _build_layer_updates(task: dict) -> dict[str, object]:
        title = str(task.get("name") or task.get("title") or "").strip()
        created_at = WorksLayerService.created_date_from_task(task)
        updated_at = WorksLayerService.updated_date_from_task(task)

        updates = {
            WorksLayerService.FIELD_EXT_SYSTEM: WorksLayerService.EXT_SYSTEM_NAME,
            WorksLayerService.FIELD_EXT_JOB_NAME: title,
            WorksLayerService.FIELD_EXT_JOB_TYPE: WorksLayerService.type_id_from_task(task),
            WorksLayerService.FIELD_EXT_JOB_STATE: WorksLayerService.status_id_from_task(task),
            WorksLayerService.FIELD_ACTIVE: WorksLayerService.active_from_task(task),
            WorksLayerService.FIELD_DETAILED: WorksLayerService.detailed_from_task(task),
            WorksLayerService.FIELD_BEGIN_DATE: WorksLayerService.begin_date_from_task(task),
            WorksLayerService.FIELD_END_DATE: WorksLayerService.end_date_from_task(task),
        }

        if created_at is not None:
            updates[WorksLayerService.FIELD_ADDED_DATE] = created_at
        if updated_at is not None:
            updates[WorksLayerService.FIELD_UPDATE_DATE] = updated_at

        return updates

    @staticmethod
    def _feature_ids_by_task_id(features: list, task_id_field: str) -> dict[str, list[int]]:
        feature_ids_by_task_id: dict[str, list[int]] = {}
        for feature in features:
            try:
                task_id = str(feature.attribute(task_id_field) or "").strip()
            except Exception:
                continue
            if not task_id:
                continue
            try:
                feature_id = int(feature.id())
            except Exception:
                continue
            feature_ids_by_task_id.setdefault(task_id, []).append(feature_id)
        return feature_ids_by_task_id

    @staticmethod
    def _layer_name(layer: QgsVectorLayer) -> str:
        try:
            return str(layer.name() or "").strip()
        except Exception:
            return ""

    def _is_layer_editable(self, layer: QgsVectorLayer, *, event: str, extra: Optional[dict] = None) -> bool:
        try:
            editable = bool(layer.isEditable())
        except Exception:
            return False
        if not editable:
            return False
        payload = {
            "layer": self._layer_name(layer),
        }
        if extra:
            payload.update(extra)
        PythonFailLogger.log(
            event,
            module=Module.WORKS.value,
            extra=payload,
        )
        return True

    def _log_duplicate_task_ids(self, feature_ids_by_task_id: dict[str, list[int]]) -> None:
        duplicates = {
            task_id: feature_ids
            for task_id, feature_ids in feature_ids_by_task_id.items()
            if len(feature_ids) > 1
        }
        if not duplicates:
            return
        for task_id, feature_ids in list(duplicates.items())[:20]:
            PythonFailLogger.log(
                "works_sync_duplicate_task_ids",
                module=Module.WORKS.value,
                extra={
                    "task_id": task_id,
                    "feature_ids": ",".join(str(feature_id) for feature_id in feature_ids[:20]),
                    "count": len(feature_ids),
                },
            )
        if len(duplicates) > 20:
            PythonFailLogger.log(
                "works_sync_duplicate_task_ids_truncated",
                module=Module.WORKS.value,
                extra={"count": len(duplicates)},
            )

    @staticmethod
    def _log_missing_backend_tasks(task_ids: list[str], tasks_by_id: dict[str, dict]) -> None:
        returned_ids = {str(task_id).strip() for task_id in (tasks_by_id or {}).keys() if str(task_id).strip()}
        missing_ids = [str(task_id) for task_id in task_ids if str(task_id) not in returned_ids]
        if not missing_ids:
            return
        PythonFailLogger.log(
            "works_sync_missing_backend_tasks",
            module=Module.WORKS.value,
            extra={
                "count": len(missing_ids),
                "sample": ",".join(missing_ids[:20]),
                "requested": len(task_ids),
                "returned": len(returned_ids),
            },
        )

    def _stamp_geometry_audit_fields(self, *, layer: QgsVectorLayer, feature_ids: list[int]) -> None:
        if not feature_ids:
            return

        try:
            field_indices = {field.name().lower(): index for index, field in enumerate(layer.fields())}
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module=Module.WORKS.value,
                event="works_sync_geometry_audit_field_map_failed",
            )
            return

        updated_by_index = field_indices.get(WorksLayerService.FIELD_UPDATED_BY.lower())
        update_date_index = field_indices.get(WorksLayerService.FIELD_UPDATE_DATE.lower())
        if updated_by_index is None and update_date_index is None:
            return

        started_edit = False
        changed = False
        username = WorksLayerService.current_username()
        timestamp = datetime.now()

        try:
            if not layer.isEditable():
                started_edit = bool(layer.startEditing())
                if not started_edit:
                    return

            for feature_id in feature_ids:
                if updated_by_index is not None and layer.changeAttributeValue(int(feature_id), updated_by_index, username):
                    changed = True
                if update_date_index is not None:
                    coerced_timestamp = WorksLayerService.coerce_value_for_field(layer.fields()[update_date_index], timestamp)
                    if layer.changeAttributeValue(int(feature_id), update_date_index, coerced_timestamp):
                        changed = True

            if not started_edit:
                return

            if not changed:
                layer.rollBack()
                return

            if not layer.commitChanges():
                errors = "; ".join(layer.commitErrors() or [])
                layer.rollBack()
                raise RuntimeError(errors or "Could not commit works geometry audit changes")

            layer.triggerRepaint()
        except Exception as exc:
            if started_edit and layer.isEditable():
                try:
                    layer.rollBack()
                except Exception as rollback_exc:
                    PythonFailLogger.log_exception(
                        rollback_exc,
                        module=Module.WORKS.value,
                        event="works_sync_geometry_audit_rollback_failed",
                    )

            PythonFailLogger.log_exception(
                exc,
                module=Module.WORKS.value,
                event="works_sync_geometry_audit_failed",
            )

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
        current_dt = WorksSyncService._normalize_datetime_value(current_value)
        new_dt = WorksSyncService._normalize_datetime_value(new_value)
        if current_dt is not None or new_dt is not None:
            return current_dt == new_dt

        if isinstance(new_value, bool):
            if isinstance(current_value, bool):
                return current_value is new_value
            current_text = str(current_value or "").strip().lower()
            return (current_text in {"1", "true", "yes"}) is new_value

        if isinstance(new_value, int) and not isinstance(new_value, bool):
            return WorksLayerService.coerce_optional_int(current_value) == new_value

        current_text = "" if current_value is None else str(current_value).strip()
        new_text = "" if new_value is None else str(new_value).strip()
        return current_text == new_text

    @staticmethod
    def _normalize_datetime_value(value) -> Optional[datetime]:
        if value is None:
            return None

        if isinstance(value, datetime):
            return value.replace(microsecond=0, tzinfo=None)

        to_py_datetime = getattr(value, "toPyDateTime", None)
        if callable(to_py_datetime):
            try:
                parsed = to_py_datetime()
            except Exception:
                parsed = None
            if isinstance(parsed, datetime):
                return parsed.replace(microsecond=0, tzinfo=None)

        parsed = WorksLayerService.parse_backend_datetime(value)
        if isinstance(parsed, datetime):
            return parsed.replace(microsecond=0, tzinfo=None)
        return None

    @staticmethod
    def _geometries_equal(existing_geometry: Optional[QgsGeometry], new_geometry: QgsGeometry) -> bool:
        if not isinstance(existing_geometry, QgsGeometry) or existing_geometry.isEmpty():
            return False
        if not isinstance(new_geometry, QgsGeometry) or new_geometry.isEmpty():
            return False
        try:
            return existing_geometry.equals(new_geometry)
        except Exception:
            return False

    @staticmethod
    def _geometry_point(geometry: Optional[QgsGeometry]):
        if not isinstance(geometry, QgsGeometry) or geometry.isEmpty():
            return None
        try:
            return geometry.vertexAt(0)
        except Exception:
            return None
