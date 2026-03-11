from __future__ import annotations

from typing import Callable, Optional

from PyQt5.QtCore import Qt
from qgis.core import QgsGeometry, QgsPointXY, QgsVectorLayer
from qgis.gui import QgsMapTool
from qgis.utils import iface

from ...Logs.python_fail_logger import PythonFailLogger
from ...languages.language_manager import LanguageManager
from ...languages.translation_keys import TranslationKeys
from ...ui.window_state.dialog_helpers import DialogHelpers
from ...utils.messagesHelper import ModernMessageDialog
from ...utils.url_manager import Module
from .works_layer_service import WorksLayerService


class _WorksRepositionCaptureTool(QgsMapTool):
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


class WorksRepositionController:
    def __init__(self, *, lang_manager=None) -> None:
        self._lang = lang_manager or LanguageManager()
        self._capture_tool: Optional[_WorksRepositionCaptureTool] = None
        self._parent_window = None
        self._layer: Optional[QgsVectorLayer] = None
        self._feature_id: Optional[int] = None
        self._task_id: str = ""
        self._on_repositioned: Optional[Callable[[str], None]] = None

    def start_reposition(
        self,
        *,
        task_id: str,
        parent_window=None,
        on_repositioned: Optional[Callable[[str], None]] = None,
    ) -> bool:
        layer = WorksLayerService.resolve_main_layer(lang_manager=self._lang, silent=False)
        if layer is None:
            return False

        task_id_text = str(task_id or "").strip()
        if not task_id_text:
            return False

        feature = WorksLayerService.find_feature_by_task_id(layer, task_id_text)
        if feature is None:
            ModernMessageDialog.show_warning(
                self._lang.translate(TranslationKeys.ERROR),
                self._lang.translate(TranslationKeys.WORKS_REPOSITION_FEATURE_NOT_FOUND).format(task_id=task_id_text),
            )
            return False

        canvas = iface.mapCanvas() if iface is not None else None
        if canvas is None:
            ModernMessageDialog.show_warning(
                self._lang.translate(TranslationKeys.ERROR),
                self._lang.translate(TranslationKeys.WORKS_REPOSITION_START_FAILED),
            )
            return False

        self.cancel(bring_front=False)

        self._parent_window = parent_window
        self._layer = layer
        self._feature_id = int(feature.id())
        self._task_id = task_id_text
        self._on_repositioned = on_repositioned

        WorksLayerService.focus_feature_by_task_id(layer, task_id_text)

        DialogHelpers.enter_map_selection_mode(
            iface_obj=iface,
            parent_window=self._parent_window,
        )

        self._capture_tool = _WorksRepositionCaptureTool(
            canvas,
            on_selected=self._handle_point_selected,
            on_cancel=self.cancel,
        )
        canvas.setMapTool(self._capture_tool)
        return True

    def cancel(self, *, bring_front: bool = True) -> None:
        self._clear_capture_tool(bring_front=bring_front)

    def _handle_point_selected(self, point: QgsPointXY) -> None:
        layer = self._layer
        feature_id = self._feature_id
        task_id = self._task_id

        success, error = self._apply_new_geometry(point)
        self._clear_capture_tool(bring_front=True)

        if not success:
            ModernMessageDialog.show_warning(
                self._lang.translate(TranslationKeys.ERROR),
                self._lang.translate(TranslationKeys.WORKS_REPOSITION_SAVE_FAILED).format(
                    task_id=task_id,
                    error=error or self._lang.translate(TranslationKeys.ERROR),
                ),
            )
            return

        if callable(self._on_repositioned):
            try:
                self._on_repositioned(task_id)
            except Exception as exc:
                PythonFailLogger.log_exception(
                    exc,
                    module=Module.WORKS.value,
                    event="works_reposition_callback_failed",
                    extra={"task_id": task_id},
                )

        ModernMessageDialog.show_info(
            self._lang.translate(TranslationKeys.SUCCESS),
            self._lang.translate(TranslationKeys.WORKS_REPOSITION_SUCCESS).format(task_id=task_id),
        )

    def _apply_new_geometry(self, point: QgsPointXY) -> tuple[bool, str]:
        layer = self._layer
        feature_id = self._feature_id
        task_id = self._task_id

        if not isinstance(layer, QgsVectorLayer) or not layer.isValid() or feature_id is None:
            return False, "Invalid works layer"

        layer_point = WorksLayerService._point_in_layer_crs(point, layer)
        new_geometry = QgsGeometry.fromPointXY(layer_point)
        started_edit = False

        try:
            if not layer.isEditable():
                started_edit = bool(layer.startEditing())
                if not started_edit:
                    return False, "Could not start editing works layer"

            if not layer.changeGeometry(int(feature_id), new_geometry):
                if started_edit and layer.isEditable():
                    layer.rollBack()
                return False, "Could not update work geometry"

            if not layer.commitChanges():
                errors = "; ".join(layer.commitErrors() or [])
                if started_edit and layer.isEditable():
                    layer.rollBack()
                return False, errors or "Could not commit works layer changes"

            layer.triggerRepaint()
            return True, ""
        except Exception as exc:
            try:
                if started_edit and layer.isEditable():
                    layer.rollBack()
            except Exception as rollback_exc:
                PythonFailLogger.log_exception(
                    rollback_exc,
                    module=Module.WORKS.value,
                    event="works_reposition_rollback_failed",
                    extra={"task_id": task_id},
                )

            PythonFailLogger.log_exception(
                exc,
                module=Module.WORKS.value,
                event="works_reposition_save_failed",
                extra={"task_id": task_id},
            )
            return False, str(exc)

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
                    event="works_reposition_capture_unset_failed",
                )

        try:
            if iface is not None:
                iface.actionPan().trigger()
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module=Module.WORKS.value,
                event="works_reposition_pan_restore_failed",
            )

        try:
            if isinstance(self._layer, QgsVectorLayer):
                self._layer.removeSelection()
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module=Module.WORKS.value,
                event="works_reposition_selection_clear_failed",
            )

        DialogHelpers.exit_map_selection_mode(
            iface_obj=iface,
            parent_window=self._parent_window,
            bring_front=bring_front,
        )

        self._capture_tool = None
        self._layer = None
        self._feature_id = None
        self._task_id = ""
        self._on_repositioned = None