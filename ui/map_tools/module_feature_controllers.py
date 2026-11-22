from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Optional

from PyQt5.QtCore import QTimer
from qgis.core import QgsEditFormConfig, QgsFeature, QgsVectorLayer, QgsWkbTypes
from qgis.utils import iface

from ...Logs.python_fail_logger import PythonFailLogger
from ..window_state.dialog_helpers import DialogHelpers
from ...utils.layers.field_value_problems import show_saved, with_field_value_problems
from ...utils.layers.module_layer_service_base import FieldValueProblem
from ..messages_helper import ModernMessageDialog
from ...utils.MapTools.canvas_click_tool import SingleClickMapTool
from ...utils.MapTools.MapHelpers import MapHelpers

LayerResolver = Callable[[], Optional[QgsVectorLayer]]
FeatureAtPointResolver = Callable[[object, QgsVectorLayer], Optional[QgsFeature]]
FeatureLookupResolver = Callable[[QgsVectorLayer, dict], Optional[QgsFeature]]
BeforeAttachHandler = Callable[[QgsVectorLayer, QgsFeature, dict], bool]
KavitroSync = Callable[[], tuple[bool, str]]


@dataclass(frozen=True)
class FeatureLinkResult:
    """Outcome of writing a Kavitro item onto a layer feature.

    The Kavitro update is returned, not run, so the draw flow can send it only
    after the layer commit: otherwise Kavitro gets a geometry the layer never saved.
    `value_problems` are fields left empty because their value did not fit; the user hears of them
    only when the feature was really saved.
    """

    success: bool
    message: str = ""
    sync_to_kavitro: Optional[KavitroSync] = None
    value_problems: tuple[FieldValueProblem, ...] = ()


AttachHandler = Callable[[QgsVectorLayer, int, dict], FeatureLinkResult]


@dataclass(frozen=True)
class ModuleFeatureAttachMessages:
    start_failed: str
    feature_not_found: str
    save_failed_template: str
    success: str
    title_error: str
    title_warning: str
    title_success: str


@dataclass(frozen=True)
class ModuleFeatureDrawMessages:
    start_failed: str
    # Nothing was saved: the drawn feature is gone and Kavitro was not changed.
    layer_save_failed_template: str
    # The feature is on the layer with the Kavitro link, but Kavitro did not get its geometry.
    sync_failed_template: str
    success: str
    title_error: str
    title_success: str


@dataclass(frozen=True)
class ModuleFeatureEditMessages:
    not_found: str
    start_failed: str
    ready: str
    title_error: str
    title_success: str


@dataclass(frozen=True)
class ModuleFeatureWorkflowConfig:
    log_module: str
    resolve_layer: LayerResolver
    find_feature_at_point: FeatureAtPointResolver
    attach_handler: AttachHandler
    find_feature_for_item: FeatureLookupResolver
    attach_messages: ModuleFeatureAttachMessages
    draw_messages: ModuleFeatureDrawMessages
    edit_messages: ModuleFeatureEditMessages
    before_attach: Optional[BeforeAttachHandler] = None


class ModuleFeatureAttachController:
    def __init__(self) -> None:
        self._capture_tool: Optional[SingleClickMapTool] = None
        self._parent_window = None
        self._layer: Optional[QgsVectorLayer] = None
        self._item_data: dict = {}
        self._find_feature_at_point: Optional[FeatureAtPointResolver] = None
        self._attach_handler: Optional[AttachHandler] = None
        self._before_attach: Optional[BeforeAttachHandler] = None
        self._item_id: str = ""

    def start_attach(
        self,
        *,
        item_data: Optional[dict],
        parent_window=None,
        resolve_layer: LayerResolver,
        find_feature_at_point: FeatureAtPointResolver,
        attach_handler: AttachHandler,
        before_attach: Optional[BeforeAttachHandler] = None,
        start_failed_message: str,
        feature_not_found_message: str,
        save_failed_message: str,
        success_message: str,
        title_error: str,
        title_warning: str,
        title_success: str,
        log_module: str,
    ) -> bool:
        layer = resolve_layer()
        if layer is None:
            return False

        canvas = iface.mapCanvas() if iface is not None else None
        if canvas is None:
            ModernMessageDialog.show_warning(title_error, start_failed_message)
            return False

        self.cancel(bring_front=False, log_module=log_module)
        self._parent_window = parent_window
        self._layer = layer
        self._item_data = dict(item_data or {})
        self._item_id = str(self._item_data.get("id") or "").strip()
        self._find_feature_at_point = find_feature_at_point
        self._attach_handler = attach_handler
        self._before_attach = before_attach

        try:
            layer.removeSelection()
        except RuntimeError:  # layer deleted
            pass

        DialogHelpers.enter_map_selection_mode(
            iface_obj=iface,
            parent_window=self._parent_window,
        )

        def _on_selected(point) -> None:
            self._handle_point_selected(
                point,
                feature_not_found_message=feature_not_found_message,
                save_failed_message=save_failed_message,
                success_message=success_message,
                title_error=title_error,
                title_warning=title_warning,
                title_success=title_success,
                log_module=log_module,
            )

        self._capture_tool = SingleClickMapTool(
            canvas,
            on_selected=_on_selected,
            on_cancel=lambda: self.cancel(log_module=log_module),
        )
        canvas.setMapTool(self._capture_tool)
        return True

    def cancel(self, *, bring_front: bool = True, log_module: str = "general") -> None:
        self._clear_capture_tool(bring_front=bring_front, log_module=log_module)

    def _handle_point_selected(
        self,
        point,
        *,
        feature_not_found_message: str,
        save_failed_message: str,
        success_message: str,
        title_error: str,
        title_warning: str,
        title_success: str,
        log_module: str,
    ) -> None:
        layer = self._layer
        if not isinstance(layer, QgsVectorLayer) or not layer.isValid() or self._find_feature_at_point is None or self._attach_handler is None:
            self._clear_capture_tool(bring_front=True, log_module=log_module)
            return

        feature = self._find_feature_at_point(point, layer)
        if feature is None:
            ModernMessageDialog.show_warning(title_warning, feature_not_found_message)
            return

        if callable(self._before_attach) and not self._before_attach(layer, feature, self._item_data):
            self._clear_capture_tool(bring_front=True, log_module=log_module)
            return

        try:
            MapHelpers.select_features_by_ids(layer, [int(feature.id())], zoom=True)
        except Exception as exc:  # canvas click callback: nothing may escape; the attach below goes on
            PythonFailLogger.log_exception(
                exc,
                module=log_module,
                event="module_feature_attach_select_failed",
                extra={"item_id": self._item_id},
            )

        link = self._attach_handler(layer, int(feature.id()), self._item_data)
        success, message = link.success, link.message
        if success and link.sync_to_kavitro is not None:
            success, message = link.sync_to_kavitro()
        # Read before the clear below empties it: the messages used to name item "-".
        item_id = self._item_id or "-"
        self._clear_capture_tool(bring_front=True, log_module=log_module)

        if not link.success:
            ModernMessageDialog.show_warning(
                title_error,
                save_failed_message.format(item_id=item_id, error=message or title_error),
            )
            return

        # The handler has saved the feature; only the Kavitro update can still have failed.
        if not success:
            ModernMessageDialog.show_warning(
                title_error,
                with_field_value_problems(
                    save_failed_message.format(item_id=item_id, error=message or title_error),
                    link.value_problems,
                ),
            )
            return

        show_saved(
            ModernMessageDialog,
            title=title_success,
            message=success_message.format(item_id=item_id),
            problems=link.value_problems,
        )

    def _clear_capture_tool(self, *, bring_front: bool, log_module: str) -> None:
        canvas = iface.mapCanvas() if iface is not None else None
        if canvas is not None and self._capture_tool is not None:
            try:
                if canvas.mapTool() is self._capture_tool:
                    canvas.unsetMapTool(self._capture_tool)
            except Exception as exc:
                PythonFailLogger.log_exception(exc, module=log_module, event="module_feature_attach_capture_unset_failed")

        try:
            if iface is not None:
                iface.actionPan().trigger()
        except Exception as exc:
            PythonFailLogger.log_exception(exc, module=log_module, event="module_feature_attach_pan_restore_failed")

        try:
            if isinstance(self._layer, QgsVectorLayer):
                self._layer.removeSelection()
        except Exception as exc:
            PythonFailLogger.log_exception(exc, module=log_module, event="module_feature_attach_selection_clear_failed")

        DialogHelpers.exit_map_selection_mode(
            iface_obj=iface,
            parent_window=self._parent_window,
            bring_front=bring_front,
        )

        self._capture_tool = None
        self._layer = None
        self._item_data = {}
        self._item_id = ""
        self._find_feature_at_point = None
        self._attach_handler = None
        self._before_attach = None


class ModuleFeatureDrawController:
    def __init__(self) -> None:
        self._layer: Optional[QgsVectorLayer] = None
        self._item_data: dict = {}
        self._on_feature_created: Optional[AttachHandler] = None
        self._title_error = ""
        self._title_success = ""
        self._layer_save_failed_message = ""
        self._sync_failed_message = ""
        self._success_message = ""
        self._log_module = "general"
        self._item_id: str = ""
        self._pending_feature_ids: set[int] = set()
        self._started_edit_session = False
        self._original_form_suppress = None

    def start_draw(
        self,
        *,
        item_data: Optional[dict],
        resolve_layer: LayerResolver,
        on_feature_created: AttachHandler,
        start_failed_message: str,
        layer_save_failed_message: str,
        sync_failed_message: str,
        success_message: str,
        title_error: str,
        title_success: str,
        log_module: str,
    ) -> bool:
        layer = resolve_layer()
        if layer is None:
            return False

        self.cancel(log_module=log_module)
        self._layer = layer
        self._item_data = dict(item_data or {})
        self._item_id = str(self._item_data.get("id") or "").strip()
        self._on_feature_created = on_feature_created
        self._title_error = title_error
        self._title_success = title_success
        self._layer_save_failed_message = layer_save_failed_message
        self._sync_failed_message = sync_failed_message
        self._success_message = success_message
        self._log_module = log_module
        self._started_edit_session = False

        try:
            MapHelpers.ensure_layer_visible(layer, make_active=True)
            self._suppress_attribute_form(layer)
            if not layer.isEditable():
                if not layer.startEditing():
                    ModernMessageDialog.show_warning(title_error, start_failed_message)
                    self.cancel(log_module=log_module)
                    return False
                self._started_edit_session = True
            layer.featureAdded.connect(self._handle_feature_added)
        except Exception as exc:
            PythonFailLogger.log_exception(exc, module=log_module, event="module_feature_draw_prepare_failed")
            ModernMessageDialog.show_warning(title_error, start_failed_message)
            self.cancel(log_module=log_module)
            return False

        if not self._trigger_iface_action("actionAddFeature"):
            ModernMessageDialog.show_warning(title_error, start_failed_message)
            self.cancel(log_module=log_module)
            return False
        return True

    def cancel(self, *, log_module: str = "general") -> None:
        if isinstance(self._layer, QgsVectorLayer):
            self._restore_attribute_form(self._layer)
        self._disconnect_feature_added()
        self._pending_feature_ids.clear()
        self._layer = None
        self._item_data = {}
        self._on_feature_created = None
        self._title_error = ""
        self._title_success = ""
        self._layer_save_failed_message = ""
        self._sync_failed_message = ""
        self._success_message = ""
        self._log_module = log_module
        self._item_id = ""
        self._started_edit_session = False
        self._original_form_suppress = None

    def _disconnect_feature_added(self) -> None:
        if isinstance(self._layer, QgsVectorLayer):
            try:
                self._layer.featureAdded.disconnect(self._handle_feature_added)
            except (TypeError, RuntimeError):  # not connected, or the layer was deleted
                pass

    def _handle_feature_added(self, feature_id: int) -> None:
        try:
            normalized_feature_id = int(feature_id)
        except (TypeError, ValueError, OverflowError):
            normalized_feature_id = None

        # QGIS can assign temporary negative feature ids while a new feature
        # still lives in the edit buffer. Those ids are valid for immediate
        # post-create attribute updates and commit handling.
        if normalized_feature_id is None:
            self.cancel(log_module=self._log_module)
            return

        if normalized_feature_id in self._pending_feature_ids:
            return

        # One draw links one feature. Committing it emits featureAdded again with the
        # permanent id, which must not open the form a second time.
        self._disconnect_feature_added()
        self._pending_feature_ids.add(normalized_feature_id)
        QTimer.singleShot(0, lambda fid=normalized_feature_id: self._finalize_feature_added(fid))

    def _finalize_feature_added(self, feature_id: int) -> None:
        self._pending_feature_ids.discard(int(feature_id))
        layer = self._layer
        handler = self._on_feature_created
        started_edit_session = bool(self._started_edit_session)
        if not isinstance(layer, QgsVectorLayer) or handler is None:
            self.cancel(log_module=self._log_module)
            return

        try:
            MapHelpers.select_features_by_ids(layer, [int(feature_id)], zoom=True)
        except Exception as exc:  # timer callback: nothing may escape; saving goes on
            PythonFailLogger.log_exception(
                exc,
                module=self._log_module,
                event="module_feature_draw_select_failed",
                extra={"feature_id": int(feature_id), "item_id": self._item_id},
            )

        try:
            link = handler(layer, int(feature_id), self._item_data)
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module=self._log_module,
                event="module_feature_draw_finalize_failed",
                extra={"feature_id": int(feature_id), "item_id": self._item_id},
            )
            link = FeatureLinkResult(False, str(exc))

        saved_to_layer, message = link.success, link.message
        if saved_to_layer and started_edit_session:
            saved_to_layer, message = self._commit_drawn_feature(layer, feature_id)
        if not saved_to_layer:
            self._discard_drawn_feature(layer, feature_id, started_edit_session)

        synced, sync_detail = True, ""
        if saved_to_layer and link.sync_to_kavitro is not None:
            synced, sync_detail = self._run_kavitro_sync(link.sync_to_kavitro, feature_id)

        if saved_to_layer:
            try:
                layer.triggerRepaint()
            except RuntimeError:  # layer deleted
                pass
            try:
                MapHelpers.ensure_layer_visible(layer, make_active=True)
                MapHelpers.select_features_by_ids(layer, [int(feature_id)], zoom=True)
            except Exception as exc:
                PythonFailLogger.log_exception(
                    exc,
                    module=self._log_module,
                    event="module_feature_draw_postsave_focus_failed",
                    extra={"feature_id": int(feature_id), "item_id": self._item_id},
                )

        title_error = self._title_error
        title_success = self._title_success
        layer_save_failed_message = self._layer_save_failed_message
        sync_failed_message = self._sync_failed_message
        success_message = self._success_message
        item_id = self._item_id
        log_module = self._log_module

        self.cancel(log_module=log_module)

        try:
            if iface is not None:
                iface.actionPan().trigger()
        except (AttributeError, RuntimeError):  # no pan action, or it was deleted
            pass

        if not saved_to_layer:
            ModernMessageDialog.show_warning(
                title_error,
                layer_save_failed_message.format(item_id=item_id or "-", error=message or title_error),
            )
            return

        # Past this point the feature is on the layer, so the fields left empty are worth correcting.
        if not synced:
            ModernMessageDialog.show_warning(
                title_error,
                with_field_value_problems(
                    sync_failed_message.format(item_id=item_id or "-", error=sync_detail or title_error),
                    link.value_problems,
                ),
            )
            return

        show_saved(
            ModernMessageDialog,
            title=title_success,
            message=success_message.format(item_id=item_id or "-"),
            problems=link.value_problems,
        )

    def _commit_drawn_feature(self, layer: QgsVectorLayer, feature_id: int) -> tuple[bool, str]:
        try:
            if layer.commitChanges():
                return True, ""
            return False, "; ".join(layer.commitErrors() or []) or "Could not commit layer changes after drawing"
        except Exception as exc:  # timer callback: nothing may escape; the feature is discarded next
            PythonFailLogger.log_exception(
                exc,
                module=self._log_module,
                event="module_feature_draw_commit_failed",
                extra={"feature_id": int(feature_id), "item_id": self._item_id},
            )
            return False, str(exc)

    def _discard_drawn_feature(self, layer: QgsVectorLayer, feature_id: int, started_edit_session: bool) -> None:
        # No half-saved feature may stay behind: our own session is rolled back whole,
        # a session the user opened earlier loses only the feature drawn here.
        try:
            if not layer.isEditable():
                return
            if started_edit_session:
                layer.rollBack()
            else:
                layer.deleteFeature(int(feature_id))
        except Exception as exc:  # a failed rollBack leaves the layer in edit mode
            PythonFailLogger.log_exception(
                exc,
                module=self._log_module,
                event="module_feature_draw_rollback_failed",
                extra={"feature_id": int(feature_id), "item_id": self._item_id},
            )

    def _run_kavitro_sync(self, sync: KavitroSync, feature_id: int) -> tuple[bool, str]:
        try:
            synced, detail = sync()
        except Exception as exc:  # timer callback: nothing may escape; the layer save stands
            PythonFailLogger.log_exception(
                exc,
                module=self._log_module,
                event="module_feature_draw_kavitro_sync_failed",
                extra={"feature_id": int(feature_id), "item_id": self._item_id},
            )
            return False, str(exc)
        return bool(synced), detail

    @staticmethod
    def _trigger_iface_action(*action_names: str) -> bool:
        for action_name in action_names:
            target = getattr(iface, action_name, None)
            if target is None:
                continue
            try:
                action = target() if callable(target) else target
                if action is not None:
                    action.trigger()
                    return True
            except (AttributeError, RuntimeError, TypeError):  # candidate action missing or unusable: try the next
                continue
        return False

    def _suppress_attribute_form(self, layer: QgsVectorLayer) -> None:
        try:
            config = layer.editFormConfig()
            self._original_form_suppress = config.suppress()
            suppress_on = getattr(QgsEditFormConfig, "SuppressOn", None)
            if suppress_on is None:
                return
            config.setSuppress(suppress_on)
            layer.setEditFormConfig(config)
        except Exception as exc:
            self._original_form_suppress = None
            PythonFailLogger.log_exception(
                exc,
                module=self._log_module,
                event="module_feature_draw_form_suppress_failed",
            )

    def _restore_attribute_form(self, layer: QgsVectorLayer) -> None:
        if self._original_form_suppress is None:
            return
        try:
            config = layer.editFormConfig()
            config.setSuppress(self._original_form_suppress)
            layer.setEditFormConfig(config)
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module=self._log_module,
                event="module_feature_draw_form_restore_failed",
            )


class ModuleFeatureEditController:
    def start_edit(
        self,
        *,
        item_data: Optional[dict],
        resolve_layer: LayerResolver,
        find_feature_for_item: FeatureLookupResolver,
        not_found_message: str,
        start_failed_message: str,
        ready_message: str,
        title_error: str,
        title_success: str,
        log_module: str,
    ) -> bool:
        layer = resolve_layer()
        if layer is None:
            return False

        item_payload = dict(item_data or {})
        item_id = str(item_payload.get("id") or "").strip()
        feature = find_feature_for_item(layer, item_payload)
        if feature is None:
            ModernMessageDialog.show_warning(
                title_error,
                not_found_message.format(item_id=item_id or "-"),
            )
            return False

        try:
            MapHelpers.ensure_layer_visible(layer, make_active=True)
            if not layer.isEditable() and not layer.startEditing():
                ModernMessageDialog.show_warning(title_error, start_failed_message.format(item_id=item_id or "-"))
                return False

            MapHelpers.select_features_by_ids(layer, [int(feature.id())], zoom=True)
            if not self._trigger_edit_action(layer):
                ModernMessageDialog.show_warning(title_error, start_failed_message.format(item_id=item_id or "-"))
                return False
        except Exception as exc:
            PythonFailLogger.log_exception(exc, module=log_module, event="module_feature_edit_start_failed")
            ModernMessageDialog.show_warning(title_error, start_failed_message.format(item_id=item_id or "-"))
            return False

        ModernMessageDialog.show_info(title_success, ready_message.format(item_id=item_id or "-"))
        return True

    @staticmethod
    def _trigger_edit_action(layer: QgsVectorLayer) -> bool:
        geometry_type = None
        try:
            geometry_type = layer.geometryType()
        except RuntimeError:  # layer deleted
            geometry_type = None

        preferred_actions = []
        if geometry_type == QgsWkbTypes.PointGeometry:
            preferred_actions.extend(["actionMoveFeature", "actionVertexToolActiveLayer", "actionVertexTool"])
        else:
            preferred_actions.extend(["actionVertexToolActiveLayer", "actionVertexTool", "actionMoveFeature"])

        for action_name in preferred_actions:
            target = getattr(iface, action_name, None)
            if target is None:
                continue
            try:
                action = target() if callable(target) else target
                if action is not None:
                    action.trigger()
                    return True
            except (AttributeError, RuntimeError, TypeError):  # candidate action missing or unusable: try the next
                continue
        return False


class ModuleFeatureWorkflow:
    """Reusable facade for module map-feature workflows.

    A module only needs to provide a `ModuleFeatureWorkflowConfig` and can then
    reuse the same attach, draw and edit actions without rewriting controller glue.
    """

    def __init__(self, config: ModuleFeatureWorkflowConfig) -> None:
        self._config = config
        self._attach_controller = ModuleFeatureAttachController()
        self._draw_controller = ModuleFeatureDrawController()
        self._edit_controller = ModuleFeatureEditController()

    def start_attach(self, *, item_data: Optional[dict], parent_window=None) -> bool:
        messages = self._config.attach_messages
        return self._attach_controller.start_attach(
            item_data=item_data,
            parent_window=parent_window,
            resolve_layer=self._config.resolve_layer,
            find_feature_at_point=self._config.find_feature_at_point,
            attach_handler=self._config.attach_handler,
            before_attach=self._config.before_attach,
            start_failed_message=messages.start_failed,
            feature_not_found_message=messages.feature_not_found,
            save_failed_message=messages.save_failed_template,
            success_message=messages.success,
            title_error=messages.title_error,
            title_warning=messages.title_warning,
            title_success=messages.title_success,
            log_module=self._config.log_module,
        )

    def start_draw(self, *, item_data: Optional[dict]) -> bool:
        messages = self._config.draw_messages
        return self._draw_controller.start_draw(
            item_data=item_data,
            resolve_layer=self._config.resolve_layer,
            on_feature_created=self._config.attach_handler,
            start_failed_message=messages.start_failed,
            layer_save_failed_message=messages.layer_save_failed_template,
            sync_failed_message=messages.sync_failed_template,
            success_message=messages.success,
            title_error=messages.title_error,
            title_success=messages.title_success,
            log_module=self._config.log_module,
        )

    def start_edit(self, *, item_data: Optional[dict]) -> bool:
        messages = self._config.edit_messages
        return self._edit_controller.start_edit(
            item_data=item_data,
            resolve_layer=self._config.resolve_layer,
            find_feature_for_item=self._config.find_feature_for_item,
            not_found_message=messages.not_found,
            start_failed_message=messages.start_failed,
            ready_message=messages.ready,
            title_error=messages.title_error,
            title_success=messages.title_success,
            log_module=self._config.log_module,
        )
