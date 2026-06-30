from __future__ import annotations

from datetime import datetime, timedelta
from typing import Callable, Iterable, Optional

from PyQt5.QtCore import QPoint, Qt
from PyQt5.QtWidgets import QApplication, QFrame, QHBoxLayout, QLabel, QProgressBar, QProgressDialog
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
from .works_pending_gis_dialog import WorksPendingGisDialog


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


class _MapButtonProgressBubble(QFrame):
    WIDTH = 286
    HEIGHT = 44
    GAP = 8

    def __init__(self, *, text: str, anchor, parent=None) -> None:
        super().__init__(parent, Qt.ToolTip | Qt.FramelessWindowHint)
        self._anchor = anchor
        self.setObjectName("MapButtonProgressBubble")
        self.setFixedSize(self.WIDTH, self.HEIGHT)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setStyleSheet(
            """
            QFrame#MapButtonProgressBubble {
                background: rgba(248, 252, 255, 220);
                border: 1px solid rgba(30, 126, 180, 150);
                border-radius: 8px;
            }
            QLabel#MapButtonProgressLabel {
                color: #12394a;
                font-weight: 600;
            }
            QProgressBar#MapButtonProgressBar {
                min-width: 74px;
                max-width: 74px;
                height: 8px;
                border: 1px solid rgba(22, 111, 151, 90);
                border-radius: 4px;
                background: rgba(255, 255, 255, 120);
                text-align: center;
            }
            QProgressBar#MapButtonProgressBar::chunk {
                border-radius: 3px;
                background: rgba(15, 118, 110, 160);
            }
            """
        )

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(10)

        label = QLabel(text, self)
        label.setObjectName("MapButtonProgressLabel")
        label.setWordWrap(False)
        layout.addWidget(label, 1)

        progress = QProgressBar(self)
        progress.setObjectName("MapButtonProgressBar")
        progress.setRange(0, 0)
        progress.setTextVisible(False)
        layout.addWidget(progress)

    def show_near_anchor(self) -> None:
        anchor = self._anchor
        if anchor is not None:
            try:
                top_left = anchor.mapToGlobal(QPoint(0, 0))
                y_pos = top_left.y() + max(0, (anchor.height() - self.HEIGHT) // 2)
                self.move(max(0, top_left.x() - self.WIDTH - self.GAP), max(0, y_pos))
            except Exception:
                pass
        self.show()
        self.raise_()


class WorksCreateController:
    def __init__(self, *, lang_manager=None) -> None:
        self._lang = lang_manager or LanguageManager()
        self._capture_tool: Optional[_WorksPointCaptureTool] = None
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
        works_layer = WorksLayerService.resolve_main_layer(lang_manager=self._lang, silent=False)
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

    def review_pending_gis_features(
        self,
        *,
        parent_window=None,
        allowed_type_ids: Optional[Iterable[str]] = None,
        on_created: Optional[Callable[[str], None]] = None,
        progress_anchor=None,
    ) -> bool:
        works_layer = WorksLayerService.resolve_main_layer(lang_manager=self._lang, silent=False)
        if works_layer is None:
            return False

        self.cancel(bring_front=False)

        self._parent_window = parent_window
        self._allowed_type_ids = [str(item_id) for item_id in (allowed_type_ids or []) if item_id]
        self._on_created = on_created
        self._existing_task_id = ""
        self._existing_task_payload = {}
        self.preload_dialog_data()

        pending_rows = self._scan_pending_gis_features_with_feedback(
            works_layer,
            parent_window=parent_window,
            progress_anchor=progress_anchor,
        )
        if not pending_rows:
            ModernMessageDialog.show_info(
                self._lang.translate(TranslationKeys.INFO),
                self._lang.translate(TranslationKeys.WORKS_PENDING_GIS_NONE),
            )
            return False
        pending_rows = self._decorate_pending_gis_rows(pending_rows)

        dialog = WorksPendingGisDialog(
            rows=pending_rows,
            on_open=lambda feature_id, owner: self._open_pending_gis_feature(
                works_layer,
                feature_id,
                parent_window=owner,
            ),
            lang_manager=self._lang,
            parent=parent_window,
        )
        dialog.exec_()
        return True

    def _scan_pending_gis_features_with_feedback(
        self,
        works_layer,
        *,
        parent_window=None,
        progress_anchor=None,
    ) -> list[dict[str, object]]:
        progress = self._make_scan_progress_widget(
            parent_window=parent_window,
            progress_anchor=progress_anchor,
        )
        if hasattr(progress, "show_near_anchor"):
            progress.show_near_anchor()
        else:
            progress.show()
        QApplication.setOverrideCursor(Qt.WaitCursor)
        QApplication.processEvents()

        try:
            return WorksLayerService.pending_gis_work_features(works_layer)
        finally:
            QApplication.restoreOverrideCursor()
            progress.close()
            progress.deleteLater()
            QApplication.processEvents()

    def _make_scan_progress_widget(self, *, parent_window=None, progress_anchor=None):
        text = self._lang.translate(TranslationKeys.WORKS_PENDING_GIS_CHECKING)
        if progress_anchor is not None:
            return _MapButtonProgressBubble(text=text, anchor=progress_anchor)

        progress = QProgressDialog(text, "", 0, 0, parent_window)
        progress.setWindowTitle(self._lang.translate(TranslationKeys.WORKS_PENDING_GIS_DIALOG_TITLE))
        progress.setWindowModality(Qt.ApplicationModal)
        progress.setMinimumDuration(0)
        progress.setCancelButton(None)
        return progress

    def _decorate_pending_gis_rows(self, rows: list[dict[str, object]]) -> list[dict[str, object]]:
        type_labels = {
            str(option.get("id") or "").strip(): str(option.get("label") or "").strip()
            for option in self._resolve_type_options()
            if isinstance(option, dict) and str(option.get("id") or "").strip()
        }
        status_labels = {
            str(option.get("id") or "").strip(): str(option.get("name") or option.get("label") or "").strip()
            for option in self._resolve_status_options()
            if isinstance(option, dict) and str(option.get("id") or "").strip()
        }

        decorated: list[dict[str, object]] = []
        for row in rows:
            payload = dict(row or {})
            type_id = str(payload.get("type_id") or "").strip()
            status_id = str(payload.get("status_id") or "").strip()
            payload["type_label"] = type_labels.get(type_id) or type_id
            payload["status_label"] = status_labels.get(status_id) or status_id
            decorated.append(payload)
        return decorated

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
        if self._existing_task_id:
            self._handle_existing_task_point_selected(point)
            return

        parent_window = self._parent_window
        self._clear_capture_tool(bring_front=True)

        property_feature = WorksLayerService.find_property_feature_at_point(point)
        assignable_users = self._resolve_assignable_users()
        priority_options = self._resolve_priority_options()
        default_responsible_id = self._resolve_default_responsible_id()
        status_options = self._resolve_status_options()
        default_status_id = self._resolve_default_status_id(status_options)
        type_options = self._resolve_type_options()
        dialog = WorksCreateDialog(
            point=point,
            property_feature=property_feature,
            allowed_type_ids=self._allowed_type_ids,
            type_options=type_options,
            assignable_users=assignable_users,
            status_options=status_options,
            priority_options=priority_options,
            default_responsible_id=default_responsible_id,
            default_status_id=default_status_id,
            lang_manager=self._lang,
            parent=parent_window,
        )
        if dialog.exec_() != dialog.Accepted:
            return

        now = datetime.now()
        works_layer = WorksLayerService.resolve_main_layer(lang_manager=self._lang, silent=True)
        task_result = self._create_backend_task_from_dialog(
            point=point,
            works_layer=works_layer,
            property_feature=property_feature,
            dialog=dialog,
            now=now,
        )
        if task_result is None:
            return

        task_id, created_task = task_result

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
            map_saved, map_error = WorksLayerService.insert_work_feature(
                layer=works_layer,
                point=point,
                task_id=task_id,
                title=created_title,
                type_id=WorksLayerService.type_id_from_task(created_task) or dialog.selected_type_id(),
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
        assignable_users = self._resolve_assignable_users()
        priority_options = self._resolve_priority_options()
        default_responsible_id = self._resolve_default_responsible_id()
        status_options = self._resolve_status_options()
        default_status_id = self._resolve_default_status_id(status_options)
        type_options = self._resolve_type_options()

        dialog = WorksCreateDialog(
            point=point,
            property_feature=property_feature,
            allowed_type_ids=self._allowed_type_ids,
            type_options=type_options,
            assignable_users=assignable_users,
            status_options=status_options,
            priority_options=priority_options,
            default_responsible_id=default_responsible_id,
            default_status_id=default_status_id,
            initial_title=str(pending_payload.get("title") or ""),
            initial_type_id=str(pending_payload.get("type_id") or ""),
            initial_status_id=str(pending_payload.get("status_id") or ""),
            lang_manager=self._lang,
            parent=parent_window,
        )
        if dialog.exec_() != dialog.Accepted:
            return False

        now = datetime.now()
        task_result = self._create_backend_task_from_dialog(
            point=point,
            works_layer=works_layer,
            property_feature=property_feature,
            dialog=dialog,
            now=now,
        )
        if task_result is None:
            return False

        task_id, created_task = task_result
        created_at = WorksLayerService.created_date_from_task(created_task) or now
        updated_at = WorksLayerService.updated_date_from_task(created_task) or created_at
        responsible_name = self._responsible_display_name(
            created_task,
            fallback=dialog.selected_responsible_label() or WorksLayerService.current_username(),
        )
        created_title = str(created_task.get("name") or dialog.title_text() or "").strip()
        map_saved, map_error = WorksLayerService.update_existing_work_feature(
            layer=works_layer,
            feature_id=feature_id,
            task_id=task_id,
            title=created_title,
            type_id=WorksLayerService.type_id_from_task(created_task) or dialog.selected_type_id(),
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

        property_link_failed = self._link_property_to_task(
            task_id,
            property_feature,
            event="works_pending_gis_property_link_failed",
        )
        cadastral_number = WorksLayerService.property_cadastral_number(property_feature)

        if callable(self._on_created):
            try:
                self._on_created(task_id)
            except Exception as exc:
                PythonFailLogger.log_exception(
                    exc,
                    module=Module.WORKS.value,
                    event="works_pending_gis_post_create_callback_failed",
                )

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
                self._lang.translate(TranslationKeys.WORKS_CREATE_PROPERTY_LINK_FAILED).format(
                    task_id=task_id,
                    cadastral=cadastral_number,
                ),
                parent=parent_window,
            )
            return True

        ModernMessageDialog.show_info(
            self._lang.translate(TranslationKeys.SUCCESS),
            self._lang.translate(TranslationKeys.WORKS_CREATE_SUCCESS).format(task_id=task_id),
        )
        return True

    def _create_backend_task_from_dialog(
        self,
        *,
        point: QgsPointXY,
        works_layer,
        property_feature,
        dialog: WorksCreateDialog,
        now: datetime,
    ) -> Optional[tuple[str, dict]]:
        backend_description = WorksDescriptionService.build_task_description(
            layer=works_layer,
            point=point,
            description_text=dialog.description_text(),
            property_feature=property_feature,
            lang_manager=self._lang,
        )

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
            updated_status_task = APIModuleActions.update_task_status(task_id, selected_status_id)
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

    def _link_property_to_task(self, task_id: str, property_feature, *, event: str) -> bool:
        cadastral_number = WorksLayerService.property_cadastral_number(property_feature)
        if not cadastral_number:
            return False

        try:
            property_ids, _missing = APIModuleActions.resolve_property_ids_by_cadastral([cadastral_number])
            if property_ids:
                APIModuleActions.associate_properties(Module.TASK.value, task_id, property_ids)
                return False
            return True
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module=Module.WORKS.value,
                event=event,
                extra={"task_id": task_id, "cadastral": cadastral_number},
            )
            return True

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

        works_layer = WorksLayerService.resolve_main_layer(lang_manager=self._lang, silent=True)
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
        created_at = WorksLayerService.created_date_from_task(task_payload) or datetime.now()
        updated_at = WorksLayerService.updated_date_from_task(task_payload) or created_at
        responsible_name = self._responsible_display_name(
            task_payload,
            fallback=WorksLayerService.current_username(),
        )
        title = str(task_payload.get("name") or "").strip() or task_id

        map_saved, map_error = WorksLayerService.insert_work_feature(
            layer=works_layer,
            point=point,
            task_id=task_id,
            title=title,
            type_id=WorksLayerService.type_id_from_task(task_payload),
            status_id=WorksLayerService.status_id_from_task(task_payload),
            active=WorksLayerService.active_from_task(task_payload),
            detailed=WorksLayerService.detailed_from_task(task_payload),
            begin_date=WorksLayerService.begin_date_from_task(task_payload) or created_at,
            end_date=WorksLayerService.end_date_from_task(task_payload),
            added_by=responsible_name,
            added_date=created_at,
            updated_by=responsible_name,
            update_date=updated_at,
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

        geometry_payload = self._backend_point_geometry_payload(
            point,
            works_layer,
            status_color=WorksLayerService.status_color_from_task(task_payload),
        )
        try:
            APIModuleActions.update_task_geometry(task_id, geometry_payload)
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module=Module.WORKS.value,
                event="works_existing_task_geometry_update_failed",
                extra={"task_id": task_id},
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
                    event="works_existing_property_link_failed",
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
                    event="works_post_add_existing_callback_failed",
                )

        if property_link_failed:
            ModernMessageDialog.show_warning(
                self._lang.translate(TranslationKeys.WARNING),
                self._lang.translate(TranslationKeys.WORKS_ADD_EXISTING_ON_MAP_PROPERTY_LINK_FAILED).format(
                    task_id=task_id,
                    cadastral=cadastral_number,
                ),
            )
            return

        ModernMessageDialog.show_info(
            self._lang.translate(TranslationKeys.SUCCESS),
            self._lang.translate(TranslationKeys.WORKS_ADD_EXISTING_ON_MAP_SUCCESS).format(task_id=task_id),
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
            if not edge_payload.get("isResponsible"):
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
            status_options = self._normalize_status_options(
                APIModuleActions.get_module_status_options(Module.WORKS.value)
            )
        except Exception:
            status_options = []

        default_status_id = self._default_status_id_from_options(status_options)
        default_status_color = self._status_color_from_options(default_status_id, status_options)

        try:
            APIModuleActions.get_task_priority_values()
        except Exception:
            pass

        return {
            "type_options": self._normalize_type_options(raw_types),
            "assignable_users": list(assignable_users or []),
            "default_responsible_id": str(default_responsible_id or "").strip(),
            "status_options": status_options,
            "default_status_id": str(default_status_id or "").strip(),
            "default_status_color": str(default_status_color or "").strip(),
        }

    def _handle_preload_success(self, payload: object, request_id: int) -> None:
        if request_id != self._preload_request_id or not isinstance(payload, dict):
            return

        self._cached_type_options = self._normalize_type_options(payload.get("type_options") or [])
        self._cached_assignable_users = self._normalize_assignable_users(payload.get("assignable_users") or [])
        self._cached_default_responsible_id = str(payload.get("default_responsible_id") or "").strip()
        self._cached_status_options = self._normalize_status_options(payload.get("status_options") or [])
        self._cached_default_status_id = (
            str(payload.get("default_status_id") or "").strip()
            or self._default_status_id_from_options(self._cached_status_options)
        )
        self._cached_default_status_color = (
            str(payload.get("default_status_color") or "").strip()
            or self._status_color_from_options(self._cached_default_status_id, self._cached_status_options)
        )
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

    def _resolve_status_options(self) -> list[dict[str, object]]:
        if self._cached_status_options:
            return list(self._cached_status_options)
        try:
            self._cached_status_options = self._normalize_status_options(
                APIModuleActions.get_module_status_options(Module.WORKS.value)
            )
        except Exception:
            self._cached_status_options = []
        return list(self._cached_status_options)

    def _resolve_default_status_id(self, status_options: Optional[list[dict[str, object]]] = None) -> str:
        if self._cached_default_status_id:
            return self._cached_default_status_id

        options = status_options if status_options is not None else self._resolve_status_options()
        self._cached_default_status_id = self._default_status_id_from_options(options)
        return self._cached_default_status_id

    def _resolve_default_status_color(self) -> str:
        if self._cached_default_status_color:
            return WorksLayerService.normalize_backend_color(self._cached_default_status_color)
        options = self._resolve_status_options()
        default_status_id = self._resolve_default_status_id(options)
        self._cached_default_status_color = self._status_color_from_options(default_status_id, options)
        return WorksLayerService.normalize_backend_color(self._cached_default_status_color)

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

    @staticmethod
    def _normalize_status_options(options: object) -> list[dict[str, object]]:
        normalized: list[dict[str, object]] = []
        for option in options or []:
            if not isinstance(option, dict):
                continue

            status_id = str(option.get("id") or "").strip()
            label = str(option.get("name") or option.get("label") or "").strip()
            if not status_id or not label:
                continue

            normalized.append(
                {
                    "id": status_id,
                    "name": label,
                    "label": label,
                    "color": WorksLayerService.normalize_backend_color(option.get("color")),
                    "type": str(option.get("type") or "").strip().upper(),
                    "description": str(option.get("description") or "").strip(),
                    "isDefault": bool(option.get("isDefault")),
                    "sortOrder": option.get("sortOrder"),
                }
            )
        return normalized

    @staticmethod
    def _default_status_id_from_options(options: object) -> str:
        first_status_id = ""
        for option in options or []:
            if not isinstance(option, dict):
                continue

            status_id = str(option.get("id") or "").strip()
            if status_id and not first_status_id:
                first_status_id = status_id
            if status_id and option.get("isDefault"):
                return status_id
        return first_status_id

    @staticmethod
    def _status_color_from_options(status_id: object, options: object) -> str:
        status_id_text = str(status_id or "").strip()
        first_color = ""
        for option in options or []:
            if not isinstance(option, dict):
                continue

            color = str(option.get("color") or "").strip()
            if color and not first_color:
                first_color = color
            if status_id_text and str(option.get("id") or "").strip() == status_id_text and color:
                return WorksLayerService.normalize_backend_color(color)
        return WorksLayerService.normalize_backend_color(first_color)

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
