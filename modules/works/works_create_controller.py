from __future__ import annotations

from datetime import datetime, timedelta
from typing import Callable, Iterable, Optional

from PyQt5.QtCore import Qt
from qgis.core import QgsPointXY
from qgis.gui import QgsMapTool
from qgis.utils import iface

from ...languages.language_manager import LanguageManager
from ...languages.translation_keys import TranslationKeys
from ...python.api_actions import APIModuleActions
from ...python.workers import FunctionWorker, start_worker
from ...ui.window_state.dialog_helpers import DialogHelpers
from ...utils.FilterHelpers.FilterHelper import FilterHelper
from ...utils.messagesHelper import ModernMessageDialog
from ...utils.url_manager import Module, ModuleSupports
from ...Logs.python_fail_logger import PythonFailLogger
from .works_create_dialog import WorksCreateDialog
from .works_layer_service import WorksDescriptionService, WorksLayerService


class _WorksPointCaptureTool(QgsMapTool):
    def __init__(self, canvas, on_selected: Callable[[QgsPointXY], None], on_cancel: Callable[[], None]):
        super().__init__(canvas)
        self.canvas = canvas
        self._on_selected = on_selected
        self._on_cancel = on_cancel
        self.setCursor(Qt.CrossCursor)

    def canvasReleaseEvent(self, event) -> None:  # noqa: N802
        if event.button() == Qt.LeftButton:
            point = self.canvas.getCoordinateTransform().toMapCoordinates(event.pos())
            self._on_selected(point)
            return
        if event.button() == Qt.RightButton:
            self._on_cancel()

    def keyPressEvent(self, event) -> None:  # noqa: N802
        if event.key() == Qt.Key_Escape:
            self._on_cancel()


class WorksCreateController:
    def __init__(self, *, lang_manager=None) -> None:
        self._lang = lang_manager or LanguageManager()
        self._capture_tool: Optional[_WorksPointCaptureTool] = None
        self._parent_window = None
        self._allowed_type_ids: list[str] = []
        self._on_created: Optional[Callable[[str], None]] = None
        self._preload_worker = None
        self._preload_thread = None
        self._preload_request_id = 0
        self._cached_type_options: list[dict[str, str]] = []
        self._cached_assignable_users: list[dict[str, str]] = []
        self._cached_priority_options: list[dict[str, str]] = []
        self._cached_default_responsible_id = ""

    def start_capture(
        self,
        *,
        parent_window=None,
        allowed_type_ids: Optional[Iterable[str]] = None,
        on_created: Optional[Callable[[str], None]] = None,
    ) -> bool:
        works_layer = WorksLayerService.resolve_main_layer(lang_manager=self._lang, silent=False)
        if works_layer is None:
            return False

        self.cancel(bring_front=False)

        self._parent_window = parent_window
        self._allowed_type_ids = [str(item_id) for item_id in (allowed_type_ids or []) if item_id]
        self._on_created = on_created
        self.preload_dialog_data()

        canvas = iface.mapCanvas() if iface is not None else None
        if canvas is None:
            ModernMessageDialog.show_warning(
                self._lang.translate(TranslationKeys.ERROR),
                self._lang.translate(TranslationKeys.WORKS_CREATE_START_FAILED),
            )
            return False

        DialogHelpers.enter_map_selection_mode(
            iface_obj=iface,
            parent_window=self._parent_window,
        )

        self._capture_tool = _WorksPointCaptureTool(
            canvas,
            on_selected=self._handle_point_selected,
            on_cancel=self.cancel,
        )
        canvas.setMapTool(self._capture_tool)
        return True

    def cancel(self, *, bring_front: bool = True) -> None:
        self._clear_capture_tool(bring_front=bring_front)

    def preload_dialog_data(self, *, force: bool = False) -> None:
        if self._preload_thread is not None and not force:
            return

        self._preload_request_id += 1
        request_id = self._preload_request_id

        worker = FunctionWorker(self._fetch_preload_payload)
        worker.finished.connect(
            lambda payload, req=request_id: self._handle_preload_success(payload, req)
        )
        worker.error.connect(
            lambda message, req=request_id: self._handle_preload_error(message, req)
        )
        self._preload_worker = worker
        self._preload_thread = start_worker(worker, on_thread_finished=self._cleanup_preload_worker)

    def _handle_point_selected(self, point: QgsPointXY) -> None:
        parent_window = self._parent_window
        self._clear_capture_tool(bring_front=True)

        property_feature = WorksLayerService.find_property_feature_at_point(point)
        assignable_users = self._resolve_assignable_users()
        priority_options = self._resolve_priority_options()
        default_responsible_id = self._resolve_default_responsible_id()
        type_options = self._resolve_type_options()
        dialog = WorksCreateDialog(
            point=point,
            property_feature=property_feature,
            allowed_type_ids=self._allowed_type_ids,
            type_options=type_options,
            assignable_users=assignable_users,
            priority_options=priority_options,
            default_responsible_id=default_responsible_id,
            lang_manager=self._lang,
            parent=parent_window,
        )
        if dialog.exec_() != dialog.Accepted:
            return

        now = datetime.now()
        works_layer = WorksLayerService.resolve_main_layer(lang_manager=self._lang, silent=True)
        backend_description = WorksDescriptionService.build_task_description(
            layer=works_layer,
            point=point,
            description_text=dialog.description_text(),
            property_feature=property_feature,
            lang_manager=self._lang,
        )

        task_id = None
        try:
            task_id = APIModuleActions.create_task(
                title=dialog.title_text(),
                type_id=dialog.selected_type_id(),
                description=backend_description,
                priority=dialog.priority_value(),
                start_at=now.strftime("%Y-%m-%d"),
                due_at=(now + timedelta(days=7)).strftime("%Y-%m-%d"),
                responsible_id=dialog.selected_responsible_id(),
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
            return

        created_task = APIModuleActions.get_task_data(task_id) or {}

        final_backend_description = WorksDescriptionService.build_task_description(
            layer=works_layer,
            point=point,
            description_text=dialog.description_text(),
            property_feature=property_feature,
            task_id=task_id,
            lang_manager=self._lang,
        )
        if final_backend_description and final_backend_description != backend_description:
            try:
                updated = APIModuleActions.update_task_description(task_id, final_backend_description)
            except Exception as exc:
                PythonFailLogger.log_exception(
                    exc,
                    module=Module.WORKS.value,
                    event="works_task_metadata_update_failed",
                    extra={"task_id": task_id},
                )
            else:
                if not updated:
                    PythonFailLogger.log_exception(
                        RuntimeError("Could not update works task metadata description"),
                        module=Module.WORKS.value,
                        event="works_task_metadata_update_failed",
                        extra={"task_id": task_id},
                    )

        map_saved = False
        map_error = ""
        if works_layer is not None:
            created_at = WorksLayerService.created_date_from_task(created_task) or now
            updated_at = WorksLayerService.updated_date_from_task(created_task) or created_at
            responsible_name = self._responsible_display_name(
                created_task,
                fallback=dialog.selected_responsible_label() or WorksLayerService.current_username(),
            )
            created_title = str(created_task.get("name") or dialog.title_text() or "").strip()
            created_type = str(((created_task.get("type") or {}).get("name") or dialog.selected_type_label() or "")).strip()
            map_saved, map_error = WorksLayerService.insert_work_feature(
                layer=works_layer,
                point=point,
                task_id=task_id,
                title=created_title,
                type_label=created_type,
                status_id=WorksLayerService.status_id_from_task(created_task),
                active=WorksLayerService.active_from_task(created_task),
                detailed=WorksLayerService.detailed_from_task(created_task),
                begin_date=WorksLayerService.begin_date_from_task(created_task) or created_at,
                end_date=WorksLayerService.end_date_from_task(created_task),
                added_by=responsible_name,
                added_date=created_at,
                updated_by=responsible_name,
                update_date=updated_at,
            )

        property_link_failed = False
        cadastral_number = WorksLayerService.property_cadastral_number(property_feature)
        if cadastral_number:
            try:
                property_ids, _missing = APIModuleActions.resolve_property_ids_by_cadastral([cadastral_number])
                if property_ids:
                    APIModuleActions.associate_properties(Module.TASK.value, task_id, property_ids)
                else:
                    property_link_failed = True
            except Exception as exc:
                PythonFailLogger.log_exception(
                    exc,
                    module=Module.WORKS.value,
                    event="works_property_link_failed",
                    extra={"task_id": task_id, "cadastral": cadastral_number},
                )
                property_link_failed = True

        if callable(self._on_created):
            try:
                self._on_created(task_id)
            except Exception as exc:
                PythonFailLogger.log_exception(
                    exc,
                    module=Module.WORKS.value,
                    event="works_post_create_callback_failed",
                )

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
                self._lang.translate(TranslationKeys.WORKS_CREATE_PROPERTY_LINK_FAILED).format(
                    task_id=task_id,
                    cadastral=cadastral_number,
                ),
            )
            return

        ModernMessageDialog.show_info(
            self._lang.translate(TranslationKeys.SUCCESS),
            self._lang.translate(TranslationKeys.WORKS_CREATE_SUCCESS).format(task_id=task_id),
        )

    @staticmethod
    def _responsible_display_name(task_data: Optional[dict], *, fallback: str = "") -> str:
        task_payload = task_data if isinstance(task_data, dict) else {}
        edges = ((task_payload.get("members") or {}).get("edges") or [])
        for edge in edges:
            edge_payload = edge if isinstance(edge, dict) else {}
            if not edge_payload.get("isResponsible"):
                continue

            node = edge_payload.get("node") or {}
            if not isinstance(node, dict):
                continue

            display_name = str(node.get("displayName") or "").strip()
            if display_name:
                return display_name

        return str(fallback or "").strip()

    def _fetch_preload_payload(self) -> dict[str, object]:
        try:
            raw_types = FilterHelper.get_filter_edges_by_key_and_module(
                ModuleSupports.TYPES.value,
                Module.WORKS.value,
            )
        except Exception:
            raw_types = []

        try:
            assignable_users = APIModuleActions.get_assignable_users()
        except Exception:
            assignable_users = []

        try:
            default_responsible_id = APIModuleActions.get_current_user_id()
        except Exception:
            default_responsible_id = ""

        try:
            APIModuleActions.get_task_priority_values()
        except Exception:
            pass

        return {
            "type_options": self._normalize_type_options(raw_types),
            "assignable_users": list(assignable_users or []),
            "default_responsible_id": str(default_responsible_id or "").strip(),
        }

    def _handle_preload_success(self, payload: object, request_id: int) -> None:
        if request_id != self._preload_request_id or not isinstance(payload, dict):
            return

        self._cached_type_options = self._normalize_type_options(payload.get("type_options") or [])
        self._cached_assignable_users = self._normalize_assignable_users(payload.get("assignable_users") or [])
        self._cached_default_responsible_id = str(payload.get("default_responsible_id") or "").strip()
        self._cached_priority_options = APIModuleActions.get_task_priority_options(
            lang_manager=self._lang,
            include_empty=True,
        )

    def _handle_preload_error(self, message: str, request_id: int) -> None:
        if request_id != self._preload_request_id:
            return
        PythonFailLogger.log_exception(
            RuntimeError(message or "Works create dialog preload failed"),
            module=Module.WORKS.value,
            event="works_create_dialog_preload_failed",
        )

    def _cleanup_preload_worker(self) -> None:
        self._preload_worker = None
        self._preload_thread = None

    def _resolve_assignable_users(self) -> list[dict[str, str]]:
        if self._cached_assignable_users:
            return list(self._cached_assignable_users)
        return self._normalize_assignable_users(APIModuleActions.get_assignable_users())

    def _resolve_priority_options(self) -> list[dict[str, str]]:
        if self._cached_priority_options:
            return list(self._cached_priority_options)
        return APIModuleActions.get_task_priority_options(lang_manager=self._lang, include_empty=True)

    def _resolve_default_responsible_id(self) -> str:
        if self._cached_default_responsible_id:
            return self._cached_default_responsible_id
        return APIModuleActions.get_current_user_id()

    def _resolve_type_options(self) -> list[dict[str, str]]:
        if self._cached_type_options:
            return list(self._cached_type_options)
        try:
            raw_types = FilterHelper.get_filter_edges_by_key_and_module(
                ModuleSupports.TYPES.value,
                Module.WORKS.value,
            )
        except Exception:
            raw_types = []
        return self._normalize_type_options(raw_types)

    @staticmethod
    def _normalize_assignable_users(users: object) -> list[dict[str, str]]:
        normalized: list[dict[str, str]] = []
        for user in users or []:
            if not isinstance(user, dict):
                continue
            user_id = str(user.get("id") or "").strip()
            display_name = str(user.get("displayName") or user.get("name") or "").strip()
            if not user_id or not display_name:
                continue
            normalized.append({"id": user_id, "displayName": display_name})
        return normalized

    @staticmethod
    def _normalize_type_options(entries: object) -> list[dict[str, str]]:
        normalized: list[dict[str, str]] = []
        for entry in entries or []:
            if isinstance(entry, dict):
                type_id = str(entry.get("id") or "").strip()
                label = str(entry.get("label") or "").strip()
            elif isinstance(entry, (list, tuple)) and len(entry) >= 2:
                label = str(entry[0] or "").strip()
                type_id = str(entry[1] or "").strip()
            else:
                continue
            if not type_id or not label:
                continue
            normalized.append({"id": type_id, "label": label})
        return normalized

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