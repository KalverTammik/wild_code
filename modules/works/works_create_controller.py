from __future__ import annotations

from datetime import datetime, timedelta
from typing import Callable, Iterable, Optional

from qgis.core import QgsPointXY
from qgis.utils import iface

from ...languages.language_manager import LanguageManager
from ...languages.translation_keys import TranslationKeys
from ...python.api_actions import APIModuleActions
from ...ui.window_state.dialog_helpers import DialogHelpers
from ...utils.layers.field_value_problems import show_saved, with_field_value_problems
from ...utils.layers.module_layer_service_base import FieldValueProblem
from ...ui.messages_helper import ModernMessageDialog
from ...constants.module_names import Module
from ...Logs.python_fail_logger import PythonFailLogger
from .works_create_dialog import (
    WorksCreateDialog,
)
from .works_layer_service import WorksDescriptionService, WorksLayerService
from .works_create_map_widgets import WorksPointCaptureTool
from .works_create_options import WorksCreateOptionsMixin
from .works_pending_gis_review import WorksPendingGisReviewMixin


class WorksCreateController(WorksCreateOptionsMixin, WorksPendingGisReviewMixin):
    """Adds works from the map: a new work from a click, an existing task placed on the map,
    or a pending GIS feature turned into a work (listed by WorksPendingGisReviewMixin)."""

    def __init__(self) -> None:
        self._lang = LanguageManager()
        self._capture_tool: Optional[WorksPointCaptureTool] = None
        self._parent_window = None
        self._allowed_type_ids: list[str] = []
        self._on_created: Optional[Callable[[str], None]] = None
        self._existing_task_id: str = ""
        self._existing_task_payload: dict[str, object] = {}
        self._preload_worker = None
        self._preload_thread = None
        self._preload_request_id = 0
        self._cached_type_options: list[dict[str, str]] = []
        self._cached_assignable_users: list[dict[str, str]] = []
        self._cached_status_options: list[dict[str, object]] = []
        self._cached_priority_options: list[dict[str, str]] = []
        self._cached_default_responsible_id = ""
        self._cached_default_status_id = ""
        self._cached_default_status_color = ""
        self._load_failures: set[str] = set()

    def start_capture(
        self,
        *,
        parent_window=None,
        allowed_type_ids: Optional[Iterable[str]] = None,
        on_created: Optional[Callable[[str], None]] = None,
    ) -> bool:
        works_layer = WorksLayerService.resolve_main_layer(dialogs=ModernMessageDialog)
        if works_layer is None:
            return False

        self.cancel(bring_front=False)

        self._parent_window = parent_window
        self._allowed_type_ids = [str(item_id) for item_id in (allowed_type_ids or []) if item_id]
        self._on_created = on_created
        self._existing_task_id = ""
        self._existing_task_payload = {}
        self.preload_dialog_data()

        return self._start_point_capture(
            start_failed_key=TranslationKeys.WORKS_CREATE_START_FAILED,
        )

    def start_add_existing_to_map(
        self,
        *,
        task_id: str,
        task_payload: Optional[dict] = None,
        parent_window=None,
        on_created: Optional[Callable[[str], None]] = None,
    ) -> bool:
        works_layer = WorksLayerService.resolve_main_layer(dialogs=ModernMessageDialog)
        if works_layer is None:
            return False

        task_id_text = str(task_id or "").strip()
        if not task_id_text:
            return False

        existing_feature = WorksLayerService.find_feature_by_task_id(works_layer, task_id_text)
        if existing_feature is not None:
            WorksLayerService.focus_feature_by_task_id(works_layer, task_id_text)
            ModernMessageDialog.show_info(
                self._lang.translate(TranslationKeys.INFO),
                self._lang.translate(TranslationKeys.WORKS_ADD_EXISTING_ON_MAP_ALREADY_LINKED).format(
                    task_id=task_id_text,
                ),
            )
            return False

        self.cancel(bring_front=False)

        self._parent_window = parent_window
        self._allowed_type_ids = []
        self._on_created = on_created
        self._existing_task_id = task_id_text
        self._existing_task_payload = dict(task_payload or {})

        return self._start_point_capture(
            start_failed_key=TranslationKeys.WORKS_ADD_EXISTING_ON_MAP_START_FAILED,
        )

    def _start_point_capture(self, *, start_failed_key: str) -> bool:

        canvas = iface.mapCanvas() if iface is not None else None
        if canvas is None:
            ModernMessageDialog.show_warning(
                self._lang.translate(TranslationKeys.ERROR),
                self._lang.translate(start_failed_key),
            )
            return False

        DialogHelpers.enter_map_selection_mode(
            iface_obj=iface,
            parent_window=self._parent_window,
        )

        self._capture_tool = WorksPointCaptureTool(
            canvas,
            on_selected=self._handle_point_selected,
            on_cancel=self.cancel,
        )
        canvas.setMapTool(self._capture_tool)
        return True

    def cancel(self, *, bring_front: bool = True) -> None:
        self._clear_capture_tool(bring_front=bring_front)

    def _handle_point_selected(self, point: QgsPointXY) -> None:
        if self._existing_task_id:
            self._handle_existing_task_point_selected(point)
            return

        parent_window = self._parent_window
        self._clear_capture_tool(bring_front=True)

        property_feature = WorksLayerService.find_property_feature_at_point(point)
        dialog = WorksCreateDialog(
            point=point,
            property_feature=property_feature,
            allowed_type_ids=self._allowed_type_ids,
            **self._resolve_dialog_options(),
            parent=parent_window,
        )
        if dialog.exec_() != dialog.Accepted:
            return

        now = datetime.now()
        works_layer = WorksLayerService.resolve_main_layer(dialogs=None)
        property_ids, property_link_failed = self._resolve_property_ids(
            property_feature, event="works_property_link_failed")
        task_result = self._create_backend_task_from_dialog(
            point=point,
            works_layer=works_layer,
            dialog=dialog,
            now=now,
            property_ids=property_ids,
        )
        if task_result is None:
            return

        task_id, created_task = task_result

        map_saved = False
        map_error = ""
        value_problems: list[FieldValueProblem] = []
        if works_layer is not None:
            map_saved, map_error = WorksLayerService.insert_work_feature(
                layer=works_layer,
                point=point,
                task_id=task_id,
                **self._feature_values_from_form(created_task, dialog, now),
                value_problems=value_problems,
            )

        property_link_failed = self._link_missing_properties(
            task_id, created_task, property_ids, property_link_failed,
            property_feature=property_feature, event="works_property_link_failed")
        cadastral_number = WorksLayerService.property_cadastral_number(property_feature)
        self._notify_created(task_id, event="works_post_create_callback_failed")

        if not map_saved:
            ModernMessageDialog.show_warning(
                self._lang.translate(TranslationKeys.WARNING),
                self._lang.translate(TranslationKeys.WORKS_CREATE_MAP_SAVE_FAILED).format(
                    task_id=task_id,
                    error=map_error or self._lang.translate(TranslationKeys.ERROR),
                ),
            )
            return

        if property_link_failed:
            ModernMessageDialog.show_warning(
                self._lang.translate(TranslationKeys.WARNING),
                with_field_value_problems(
                    self._lang.translate(TranslationKeys.WORKS_CREATE_PROPERTY_LINK_FAILED).format(
                        task_id=task_id,
                        cadastral=cadastral_number,
                    ),
                    value_problems,
                ),
            )
            return

        show_saved(
            ModernMessageDialog,
            title=self._lang.translate(TranslationKeys.SUCCESS),
            message=self._lang.translate(TranslationKeys.WORKS_CREATE_SUCCESS).format(task_id=task_id),
            problems=value_problems,
        )

    def _open_pending_gis_feature(
        self,
        works_layer,
        feature_id: int,
        *,
        parent_window=None,
    ) -> bool:
        feature = WorksLayerService.feature_by_id(works_layer, feature_id)
        if feature is None:
            ModernMessageDialog.show_warning(
                self._lang.translate(TranslationKeys.ERROR),
                self._lang.translate(TranslationKeys.WORKS_PENDING_GIS_FEATURE_MISSING),
                parent=parent_window,
            )
            return False

        pending_payload = WorksLayerService.pending_gis_payload_from_feature(works_layer, feature)
        if not pending_payload:
            ModernMessageDialog.show_warning(
                self._lang.translate(TranslationKeys.ERROR),
                self._lang.translate(TranslationKeys.WORKS_PENDING_GIS_FEATURE_MISSING),
                parent=parent_window,
            )
            return False

        WorksLayerService.focus_feature_by_id(works_layer, feature_id)
        point = WorksLayerService.feature_point_in_canvas_crs(works_layer, feature)
        if point is None:
            ModernMessageDialog.show_warning(
                self._lang.translate(TranslationKeys.ERROR),
                self._lang.translate(TranslationKeys.WORKS_PENDING_GIS_FEATURE_MISSING),
                parent=parent_window,
            )
            return False

        property_feature = WorksLayerService.find_property_feature_at_point(point)
        dialog = WorksCreateDialog(
            point=point,
            property_feature=property_feature,
            allowed_type_ids=self._allowed_type_ids,
            **self._resolve_dialog_options(),
            initial_title=str(pending_payload.get("title") or ""),
            initial_type_id=str(pending_payload.get("type_id") or ""),
            initial_status_id=str(pending_payload.get("status_id") or ""),
            parent=parent_window,
        )
        if dialog.exec_() != dialog.Accepted:
            return False

        now = datetime.now()
        property_ids, property_link_failed = self._resolve_property_ids(
            property_feature, event="works_pending_gis_property_link_failed")
        task_result = self._create_backend_task_from_dialog(
            point=point,
            works_layer=works_layer,
            dialog=dialog,
            now=now,
            property_ids=property_ids,
        )
        if task_result is None:
            return False

        task_id, created_task = task_result
        value_problems: list[FieldValueProblem] = []
        map_saved, map_error = WorksLayerService.update_existing_work_feature(
            layer=works_layer,
            feature_id=feature_id,
            task_id=task_id,
            **self._feature_values_from_form(created_task, dialog, now),
            value_problems=value_problems,
        )

        property_link_failed = self._link_missing_properties(
            task_id, created_task, property_ids, property_link_failed,
            property_feature=property_feature, event="works_pending_gis_property_link_failed")
        cadastral_number = WorksLayerService.property_cadastral_number(property_feature)
        self._notify_created(task_id, event="works_pending_gis_post_create_callback_failed")

        if not map_saved:
            ModernMessageDialog.show_warning(
                self._lang.translate(TranslationKeys.WARNING),
                self._lang.translate(TranslationKeys.WORKS_CREATE_MAP_SAVE_FAILED).format(
                    task_id=task_id,
                    error=map_error or self._lang.translate(TranslationKeys.ERROR),
                ),
                parent=parent_window,
            )
            return False

        if property_link_failed:
            ModernMessageDialog.show_warning(
                self._lang.translate(TranslationKeys.WARNING),
                with_field_value_problems(
                    self._lang.translate(TranslationKeys.WORKS_CREATE_PROPERTY_LINK_FAILED).format(
                        task_id=task_id,
                        cadastral=cadastral_number,
                    ),
                    value_problems,
                ),
                parent=parent_window,
            )
            return True

        show_saved(
            ModernMessageDialog,
            title=self._lang.translate(TranslationKeys.SUCCESS),
            message=self._lang.translate(TranslationKeys.WORKS_CREATE_SUCCESS).format(task_id=task_id),
            problems=value_problems,
        )
        return True

    def _create_backend_task_from_dialog(
        self,
        *,
        point: QgsPointXY,
        works_layer,
        dialog: WorksCreateDialog,
        now: datetime,
        property_ids: Optional[list[str]] = None,
    ) -> Optional[tuple[str, dict]]:
        backend_description = WorksDescriptionService.build_task_description(dialog.description_text())

        task_id = None
        selected_status_id = dialog.selected_status_id()
        selected_status_color = dialog.selected_status_color()
        initial_status_color = selected_status_color or self._resolve_default_status_color()
        geometry_payload = self._backend_point_geometry_payload(
            point,
            works_layer,
            status_color=initial_status_color,
        )
        try:
            task_id = APIModuleActions.create_task(
                title=dialog.title_text(),
                type_id=dialog.selected_type_id(),
                description=backend_description,
                priority=dialog.priority_value(),
                start_at=now.strftime("%Y-%m-%d"),
                due_at=(now + timedelta(days=7)).strftime("%Y-%m-%d"),
                responsible_id=dialog.selected_responsible_id(),
                status_id=selected_status_id,
                geometry=geometry_payload,
                property_ids=property_ids or None,
            )
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module=Module.WORKS.value,
                event="works_task_create_failed",
            )
            task_id = None

        if not task_id:
            ModernMessageDialog.show_warning(
                self._lang.translate(TranslationKeys.ERROR),
                self._lang.translate(TranslationKeys.WORKS_CREATE_FAILED),
            )
            return None

        created_task = APIModuleActions.get_task_data(task_id) or {}
        created_status_id = self._task_status_id_text(created_task)
        if selected_status_id and created_status_id != selected_status_id:
            updated_status_task = APIModuleActions.update_item_status(Module.WORKS.value, task_id, selected_status_id)
            if updated_status_task:
                created_task = APIModuleActions.get_task_data(task_id) or created_task
            else:
                PythonFailLogger.log_exception(
                    RuntimeError("Could not update works task status after creation"),
                    module=Module.WORKS.value,
                    event="works_task_status_update_failed",
                    extra={"task_id": task_id, "status_id": selected_status_id},
                )

        created_status_color = WorksLayerService.status_color_from_task(
            created_task,
            fallback=initial_status_color,
        )
        if created_status_color != WorksLayerService.normalize_backend_color(initial_status_color):
            try:
                APIModuleActions.update_task_geometry(
                    task_id,
                    self._backend_point_geometry_payload(
                        point,
                        works_layer,
                        status_color=created_status_color,
                    ),
                )
            except Exception as exc:
                PythonFailLogger.log_exception(
                    exc,
                    module=Module.WORKS.value,
                    event="works_task_geometry_style_update_failed",
                    extra={"task_id": task_id},
                )

        return str(task_id), created_task

    def _resolve_property_ids(self, property_feature, *, event: str, task_id: str = "") -> tuple[list[str], bool]:
        """Kavitro ids of the property under the point, and whether linking it already failed.

        Resolved before the task mutation, so the link can travel with it."""
        cadastral_number = WorksLayerService.property_cadastral_number(property_feature)
        if not cadastral_number:
            return [], False
        try:
            property_ids, _missing = APIModuleActions.resolve_property_ids_by_cadastral([cadastral_number])
        except Exception as exc:
            extra = {"task_id": task_id, "cadastral": cadastral_number} if task_id else {"cadastral": cadastral_number}
            PythonFailLogger.log_exception(exc, module=Module.WORKS.value, event=event, extra=extra)
            return [], True
        property_ids = [str(value) for value in (property_ids or []) if str(value or "").strip()]
        return property_ids, not property_ids

    @staticmethod
    def _task_has_properties(task: Optional[dict], property_ids: list[str]) -> bool:
        properties = task.get("properties") if isinstance(task, dict) else None
        edges = properties.get("edges") if isinstance(properties, dict) else None
        linked = {
            str(((edge or {}).get("node") or {}).get("id") or "")
            for edge in (edges or [])
            if isinstance(edge, dict)
        }
        return all(property_id in linked for property_id in property_ids)

    def _link_missing_properties(
        self, task_id: str, task: Optional[dict], property_ids: list[str], failed: bool, *, property_feature, event: str,
    ) -> bool:
        """Link the properties the create could not carry; returns whether linking failed."""
        if failed or not property_ids or self._task_has_properties(task, property_ids):
            return failed
        return self._link_property_to_task(task_id, property_ids, property_feature=property_feature, event=event)

    def _link_property_to_task(self, task_id: str, property_ids: list[str], *, property_feature, event: str) -> bool:
        """Link the properties in a mutation of their own; returns whether it failed."""
        try:
            APIModuleActions.associate_properties(Module.TASK.value, task_id, property_ids)
            return False
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module=Module.WORKS.value,
                event=event,
                extra={"task_id": task_id, "cadastral": WorksLayerService.property_cadastral_number(property_feature)},
            )
            return True

    def _notify_created(self, task_id: str, *, event: str) -> None:
        if not callable(self._on_created):
            return
        try:
            self._on_created(task_id)
        except Exception as exc:
            PythonFailLogger.log_exception(exc, module=Module.WORKS.value, event=event)

    @classmethod
    def _feature_values_from_form(cls, created_task: dict, dialog: WorksCreateDialog, now: datetime) -> dict:
        """Layer values of a task just created from the form; the form fills what the task lacks."""
        return cls._work_feature_values(
            created_task,
            title=str(created_task.get("name") or dialog.title_text() or "").strip(),
            type_id=WorksLayerService.type_id_from_task(created_task) or dialog.selected_type_id(),
            responsible_name=cls._responsible_display_name(
                created_task,
                fallback=dialog.selected_responsible_label() or WorksLayerService.current_username(),
            ),
            now=now,
        )

    @staticmethod
    def _work_feature_values(task: dict, *, title: str, type_id, responsible_name: str, now: datetime) -> dict:
        """The works layer values of a task, for insert_work_feature and update_existing_work_feature."""
        created_at = WorksLayerService.created_date_from_task(task) or now
        updated_at = WorksLayerService.updated_date_from_task(task) or created_at
        return {
            "title": title,
            "type_id": type_id,
            "status_id": WorksLayerService.status_id_from_task(task),
            "active": WorksLayerService.active_from_task(task),
            "detailed": WorksLayerService.detailed_from_task(task),
            "begin_date": WorksLayerService.begin_date_from_task(task) or created_at,
            "end_date": WorksLayerService.end_date_from_task(task),
            "added_by": responsible_name,
            "added_date": created_at,
            "updated_by": responsible_name,
            "update_date": updated_at,
        }

    def _handle_existing_task_point_selected(self, point: QgsPointXY) -> None:
        parent_window = self._parent_window
        self._clear_capture_tool(bring_front=True)

        task_id = str(self._existing_task_id or "").strip()
        cached_payload = dict(self._existing_task_payload or {})
        self._existing_task_id = ""
        self._existing_task_payload = {}

        if not task_id:
            return

        task_payload = APIModuleActions.get_task_data(task_id)
        if not isinstance(task_payload, dict):
            task_payload = cached_payload
        if not isinstance(task_payload, dict) or not task_payload:
            ModernMessageDialog.show_warning(
                self._lang.translate(TranslationKeys.ERROR),
                self._lang.translate(TranslationKeys.WORKS_ADD_EXISTING_ON_MAP_TASK_LOAD_FAILED).format(
                    task_id=task_id,
                ),
            )
            return

        works_layer = WorksLayerService.resolve_main_layer(dialogs=None)
        if works_layer is None:
            ModernMessageDialog.show_warning(
                self._lang.translate(TranslationKeys.ERROR),
                self._lang.translate(TranslationKeys.WORKS_LAYER_MISSING),
                parent=parent_window,
            )
            return

        existing_feature = WorksLayerService.find_feature_by_task_id(works_layer, task_id)
        if existing_feature is not None:
            WorksLayerService.focus_feature_by_task_id(works_layer, task_id)
            ModernMessageDialog.show_info(
                self._lang.translate(TranslationKeys.INFO),
                self._lang.translate(TranslationKeys.WORKS_ADD_EXISTING_ON_MAP_ALREADY_LINKED).format(
                    task_id=task_id,
                ),
            )
            return

        property_feature = WorksLayerService.find_property_feature_at_point(point)
        value_problems: list[FieldValueProblem] = []
        map_saved, map_error = WorksLayerService.insert_work_feature(
            layer=works_layer,
            point=point,
            task_id=task_id,
            **self._work_feature_values(
                task_payload,
                title=str(task_payload.get("name") or "").strip() or task_id,
                type_id=WorksLayerService.type_id_from_task(task_payload),
                responsible_name=self._responsible_display_name(
                    task_payload,
                    fallback=WorksLayerService.current_username(),
                ),
                now=datetime.now(),
            ),
            value_problems=value_problems,
        )

        if not map_saved:
            ModernMessageDialog.show_warning(
                self._lang.translate(TranslationKeys.WARNING),
                self._lang.translate(TranslationKeys.WORKS_ADD_EXISTING_ON_MAP_SAVE_FAILED).format(
                    task_id=task_id,
                    error=map_error or self._lang.translate(TranslationKeys.ERROR),
                ),
            )
            return

        property_ids, property_link_failed = self._resolve_property_ids(
            property_feature, event="works_existing_property_link_failed", task_id=task_id)
        geometry_payload = self._backend_point_geometry_payload(
            point,
            works_layer,
            status_color=WorksLayerService.status_color_from_task(task_payload),
        )
        # One mutation for the place and the property: a second one waits for the pacing.
        linked = False
        location_saved = False
        try:
            if APIModuleActions.update_task_geometry(task_id, geometry_payload, property_ids=property_ids or None):
                linked = bool(property_ids)
                location_saved = True
            elif property_ids:
                # The server may have refused the pair for the property alone: send the place by itself.
                location_saved = bool(APIModuleActions.update_task_geometry(task_id, geometry_payload))
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module=Module.WORKS.value,
                event="works_existing_task_geometry_update_failed",
                extra={"task_id": task_id},
            )

        if property_ids and not linked:
            property_link_failed = self._link_property_to_task(
                task_id, property_ids, property_feature=property_feature, event="works_existing_property_link_failed")
        cadastral_number = WorksLayerService.property_cadastral_number(property_feature)
        self._notify_created(task_id, event="works_post_add_existing_callback_failed")

        # The point is on the layer either way; what did not reach Kavitro is named.
        problems = []
        if not location_saved:
            problems.append(self._lang.translate(TranslationKeys.WORKS_ADD_EXISTING_ON_MAP_LOCATION_SYNC_FAILED).format(
                task_id=task_id))
        if property_link_failed:
            problems.append(self._lang.translate(TranslationKeys.WORKS_ADD_EXISTING_ON_MAP_PROPERTY_LINK_FAILED).format(
                task_id=task_id,
                cadastral=cadastral_number,
            ))
        if problems:
            ModernMessageDialog.show_warning(
                self._lang.translate(TranslationKeys.WARNING),
                with_field_value_problems("\n\n".join(problems), value_problems),
            )
            return

        show_saved(
            ModernMessageDialog,
            title=self._lang.translate(TranslationKeys.SUCCESS),
            message=self._lang.translate(TranslationKeys.WORKS_ADD_EXISTING_ON_MAP_SUCCESS).format(task_id=task_id),
            problems=value_problems,
        )

    @staticmethod
    def _backend_point_geometry_payload(point: QgsPointXY, layer=None, *, status_color: object = None) -> dict[str, object]:
        backend_point = point
        if layer is not None:
            backend_point = WorksLayerService._point_in_layer_crs(point, layer)
        payload = {
            "type": "Point",
            "coordinates": [backend_point.x(), backend_point.y()],
        }
        payload = WorksLayerService.styled_backend_geometry_payload(payload, color=status_color) or payload
        return payload

    @staticmethod
    def _responsible_display_name(task_data: Optional[dict], *, fallback: str = "") -> str:
        task_payload = task_data if isinstance(task_data, dict) else {}
        edges = ((task_payload.get("members") or {}).get("edges") or [])
        for edge in edges:
            edge_payload = edge if isinstance(edge, dict) else {}
            if not edge_payload.get("responsible"):
                continue

            node = edge_payload.get("node") or {}
            if not isinstance(node, dict):
                continue

            display_name = str(node.get("displayName") or "").strip()
            if display_name:
                return display_name

        return str(fallback or "").strip()

    @staticmethod
    def _task_status_id_text(task_data: Optional[dict]) -> str:
        task_payload = task_data if isinstance(task_data, dict) else {}
        status_payload = task_payload.get("status") or {}
        if not isinstance(status_payload, dict):
            return ""
        return str(status_payload.get("id") or "").strip()

    # An empty cache (preload still running, failed or empty) is retried here on the GUI thread.
    def _clear_capture_tool(self, *, bring_front: bool) -> None:
        canvas = iface.mapCanvas() if iface is not None else None
        if canvas is not None and self._capture_tool is not None:
            try:
                if canvas.mapTool() is self._capture_tool:
                    canvas.unsetMapTool(self._capture_tool)
            except Exception as exc:
                PythonFailLogger.log_exception(
                    exc,
                    module=Module.WORKS.value,
                    event="works_capture_unset_failed",
                )

        try:
            if iface is not None:
                iface.actionPan().trigger()
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module=Module.WORKS.value,
                event="works_capture_pan_restore_failed",
            )

        DialogHelpers.exit_map_selection_mode(
            iface_obj=iface,
            parent_window=self._parent_window,
            bring_front=bring_front,
        )
        self._capture_tool = None
