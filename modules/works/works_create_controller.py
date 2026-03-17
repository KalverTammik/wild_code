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
from ...ui.window_state.dialog_helpers import DialogHelpers
from ...utils.messagesHelper import ModernMessageDialog
from ...utils.url_manager import Module
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

    def _handle_point_selected(self, point: QgsPointXY) -> None:
        parent_window = self._parent_window
        self._clear_capture_tool(bring_front=True)

        property_feature = WorksLayerService.find_property_feature_at_point(point)
        assignable_users = APIModuleActions.get_assignable_users()
        priority_options = APIModuleActions.get_task_priority_options(lang_manager=self._lang, include_empty=True)
        default_responsible_id = APIModuleActions.get_current_user_id()
        dialog = WorksCreateDialog(
            point=point,
            property_feature=property_feature,
            allowed_type_ids=self._allowed_type_ids,
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
                begin_date=WorksLayerService.begin_date_from_task(created_task) or now,
                end_date=WorksLayerService.end_date_from_task(created_task),
                added_by=responsible_name,
                added_date=now,
                updated_by=responsible_name,
                update_date=now,
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