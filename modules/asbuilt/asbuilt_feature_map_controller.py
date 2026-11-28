from __future__ import annotations

from typing import Optional

from qgis.core import QgsVectorLayer

from ...Logs.python_fail_logger import PythonFailLogger
from ...languages.language_manager import LanguageManager
from ...languages.translation_keys import TranslationKeys
from ...python.api_actions import APIModuleActions
from ...utils.layers.module_layer_service_base import FieldValueProblem
from ...ui.map_tools.module_feature_controllers import (
    FeatureLinkResult,
    ModuleFeatureAttachMessages,
    ModuleFeatureDrawMessages,
    ModuleFeatureEditMessages,
    ModuleFeatureWorkflow,
    ModuleFeatureWorkflowConfig,
    ask_existing_feature_mode,
)
from ...ui.messages_helper import ModernMessageDialog
from .asbuilt_geometry_form_dialog import AsBuiltGeometryFormDialog
from .asbuilt_layer_service import AsBuiltLayerService


class AsBuiltFeatureMapController:
    def __init__(self) -> None:
        self._lang = LanguageManager()
        self._workflow = ModuleFeatureWorkflow(self._build_workflow_config())

    def start_draw(self, *, item_data: Optional[dict]) -> bool:
        item_payload = dict(item_data or {})
        item_id = str(item_payload.get("id") or "").strip()
        if not item_id:
            return False
        layer, _message = AsBuiltLayerService.prepare_layer_for_draw(dialogs=ModernMessageDialog)
        if layer is None:
            return False
        mode = ask_existing_feature_mode(
            AsBuiltLayerService, layer, item_id, lang=self._lang,
            question_key=TranslationKeys.ASBUILT_FEATURE_EXISTS_QUESTION,
            replace_only_key=TranslationKeys.ASBUILT_FEATURE_EXISTS_REPLACE_ONLY,
        )
        if mode is None:
            return False
        if mode:
            item_payload["_existing_feature_mode"] = mode
        return self._workflow.start_draw(item_data=item_payload)

    def _build_workflow_config(self) -> ModuleFeatureWorkflowConfig:
        return ModuleFeatureWorkflowConfig(
            log_module="asbuilt",
            resolve_layer=lambda: AsBuiltLayerService.resolve_main_layer(dialogs=ModernMessageDialog),
            find_feature_at_point=lambda point, layer: AsBuiltLayerService.find_feature_at_point(point, layer=layer),
            attach_handler=self._attach_asbuilt_feature_and_sync_geometry,
            find_feature_for_item=lambda layer, current_item: AsBuiltLayerService.find_feature(
                layer,
                item_id=str((current_item or {}).get("id") or "").strip(),
                item_name=str((current_item or {}).get("name") or (current_item or {}).get("title") or "").strip(),
            ),
            attach_messages=ModuleFeatureAttachMessages(
                start_failed=self._lang.translate(TranslationKeys.ASBUILT_DRAW_NEW_START_FAILED),
                feature_not_found="",
                save_failed_template=self._lang.translate(TranslationKeys.ASBUILT_DRAW_NEW_SAVE_FAILED).format(
                    item_id="{item_id}",
                    error="{error}",
                ),
                success=self._lang.translate(TranslationKeys.ASBUILT_DRAW_NEW_SUCCESS).format(item_id="{item_id}"),
                title_error=self._lang.translate(TranslationKeys.ERROR),
                title_warning=self._lang.translate(TranslationKeys.WARNING),
                title_success=self._lang.translate(TranslationKeys.SUCCESS),
            ),
            draw_messages=ModuleFeatureDrawMessages(
                start_failed=self._lang.translate(TranslationKeys.ASBUILT_DRAW_NEW_START_FAILED),
                layer_save_failed_template=self._lang.translate(TranslationKeys.ASBUILT_DRAW_NEW_LAYER_SAVE_FAILED).format(
                    item_id="{item_id}",
                    error="{error}",
                ),
                sync_failed_template=self._lang.translate(TranslationKeys.ASBUILT_DRAW_NEW_SAVE_FAILED).format(
                    item_id="{item_id}",
                    error="{error}",
                ),
                success=self._lang.translate(TranslationKeys.ASBUILT_DRAW_NEW_SUCCESS).format(item_id="{item_id}"),
                title_error=self._lang.translate(TranslationKeys.ERROR),
                title_success=self._lang.translate(TranslationKeys.SUCCESS),
            ),
            edit_messages=ModuleFeatureEditMessages(
                not_found="",
                start_failed=self._lang.translate(TranslationKeys.ASBUILT_DRAW_NEW_START_FAILED),
                ready=self._lang.translate(TranslationKeys.ASBUILT_DRAW_NEW_SUCCESS).format(item_id="{item_id}"),
                title_error=self._lang.translate(TranslationKeys.ERROR),
                title_success=self._lang.translate(TranslationKeys.SUCCESS),
            ),
        )

    @staticmethod
    def _attach_asbuilt_feature_and_sync_geometry(
        layer: QgsVectorLayer,
        feature_id: int,
        current_item: dict,
    ) -> FeatureLinkResult:
        item_payload = current_item if isinstance(current_item, dict) else {}
        item_id = str(item_payload.get("id") or "").strip()
        form_values = AsBuiltGeometryFormDialog.prompt(item_data=item_payload, layer=layer)
        if form_values is None:
            return FeatureLinkResult(
                False, LanguageManager().translate(TranslationKeys.ASBUILT_FORM_CANCELLED), cancelled=True)

        item_payload["_asbuilt_geometry_form"] = form_values
        item_payload["_asbuilt_feature_id"] = int(feature_id)
        value_problems: list[FieldValueProblem] = []
        success, message = AsBuiltLayerService.attach_backend_item_to_feature(
            layer=layer,
            feature_id=feature_id,
            item_id=item_id,
            item_data=item_payload,
            value_problems=value_problems,
        )
        if not success:
            return FeatureLinkResult(False, message)

        mode = str(item_payload.get("_existing_feature_mode") or "")
        if mode:
            folded, fold_error = AsBuiltLayerService.fold_existing_areas(
                layer, keep_feature_id=feature_id, item_id=item_id, mode=mode
            )
            if not folded:
                return FeatureLinkResult(False, fold_error)

        # Read now: a drawn feature changes its id when the layer is committed.
        geometry_payload = AsBuiltFeatureMapController._geometry_payload_for_item(layer, item_payload)
        if geometry_payload is None:
            PythonFailLogger.log(
                "asbuilt_geometry_backend_sync_skipped_no_geometry",
                module="asbuilt",
                extra={"item_id": item_id, "feature_id": int(feature_id)},
            )
            return FeatureLinkResult(False, LanguageManager().translate(TranslationKeys.KAVITRO_GEOMETRY_NOT_FOUND))

        def sync_to_kavitro() -> tuple[bool, str]:
            if APIModuleActions.update_task_geometry(item_id, geometry_payload):
                PythonFailLogger.log(
                    "asbuilt_geometry_backend_sync_success",
                    module="asbuilt",
                    extra={"item_id": item_id, "feature_id": int(feature_id), "geometry_type": str(geometry_payload.get("type") or "")},
                )
                return True, message

            PythonFailLogger.log_exception(
                RuntimeError("Could not update As-built task geometry in Kavitro"),
                module="asbuilt",
                event="asbuilt_geometry_backend_update_failed",
                extra={"item_id": item_id, "feature_id": int(feature_id)},
            )
            return False, LanguageManager().translate(TranslationKeys.KAVITRO_GEOMETRY_SYNC_FAILED)

        return FeatureLinkResult(True, message, sync_to_kavitro, tuple(value_problems))

    @staticmethod
    def _geometry_payload_for_item(layer: QgsVectorLayer, item_payload: dict) -> Optional[dict[str, object]]:
        try:
            feature = None
            feature_id = item_payload.get("_asbuilt_feature_id")
            if feature_id is not None:
                feature = AsBuiltLayerService._feature_by_id(layer, int(feature_id))
            if feature is None:
                feature = AsBuiltLayerService.find_feature(
                    layer,
                    item_id=str((item_payload or {}).get("id") or "").strip(),
                    item_name=str((item_payload or {}).get("name") or (item_payload or {}).get("title") or "").strip(),
                )
            if feature is None:
                PythonFailLogger.log(
                    "asbuilt_geometry_payload_feature_not_found",
                    module="asbuilt",
                    extra={
                        "item_id": str((item_payload or {}).get("id") or "").strip(),
                        "feature_id": item_payload.get("_asbuilt_feature_id"),
                    },
                )
                return None
            geometry = feature.geometry()
            return AsBuiltLayerService.backend_geometry_payload_from_geometry(geometry, layer)
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module="asbuilt",
                event="asbuilt_geometry_payload_from_item_failed",
                extra={"item_id": str((item_payload or {}).get("id") or "").strip()},
            )
            return None
