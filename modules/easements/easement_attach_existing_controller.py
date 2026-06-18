from __future__ import annotations

from typing import Optional

from ...languages.language_manager import LanguageManager
from ...languages.translation_keys import TranslationKeys
from ...Logs.python_fail_logger import PythonFailLogger
from ...python.api_actions import APIModuleActions
from ...utils.messagesHelper import ModernMessageDialog
from ...utils.MapTools.module_feature_controllers import (
    ModuleFeatureAttachMessages,
    ModuleFeatureDrawMessages,
    ModuleFeatureEditMessages,
    ModuleFeatureWorkflow,
    ModuleFeatureWorkflowConfig,
)
from .easement_geometry_form_dialog import EasementGeometryFormDialog
from .easement_layer_service import EasementLayerService


class EasementAttachExistingController:
    def __init__(self, *, lang_manager=None) -> None:
        self._lang = lang_manager or LanguageManager()
        self._workflow = ModuleFeatureWorkflow(self._build_workflow_config())

    def start_attach(self, *, item_data: Optional[dict], parent_window=None) -> bool:
        item_payload = dict(item_data or {})
        item_id = str(item_payload.get("id") or "").strip()
        if not item_id:
            return False

        return self._workflow.start_attach(item_data=item_payload, parent_window=parent_window)

    def start_draw(self, *, item_data: Optional[dict]) -> bool:
        item_payload = dict(item_data or {})
        item_id = str(item_payload.get("id") or "").strip()
        if not item_id:
            return False
        return self._workflow.start_draw(item_data=item_payload)

    def start_edit(self, *, item_data: Optional[dict]) -> bool:
        item_payload = dict(item_data or {})
        item_id = str(item_payload.get("id") or "").strip()
        if not item_id:
            return False
        return self._workflow.start_edit(item_data=item_payload)

    def _build_workflow_config(self) -> ModuleFeatureWorkflowConfig:
        return ModuleFeatureWorkflowConfig(
            log_module="easement",
            resolve_layer=lambda: EasementLayerService.resolve_main_layer(lang_manager=self._lang, silent=False),
            find_feature_at_point=lambda point, layer: EasementLayerService.find_feature_at_point(point, layer=layer),
            attach_handler=self._attach_easement_feature_with_form,
            find_feature_for_item=lambda layer, current_item: EasementLayerService.find_feature(
                layer,
                item_id=str((current_item or {}).get("id") or "").strip(),
                item_number=str((current_item or {}).get("number") or "").strip(),
            ),
            attach_messages=ModuleFeatureAttachMessages(
                start_failed=self._lang.translate(TranslationKeys.EASEMENT_ATTACH_EXISTING_START_FAILED),
                feature_not_found=self._lang.translate(TranslationKeys.EASEMENT_ATTACH_EXISTING_FEATURE_NOT_FOUND),
                save_failed_template=self._lang.translate(TranslationKeys.EASEMENT_ATTACH_EXISTING_SAVE_FAILED).format(
                    item_id="{item_id}",
                    error="{error}",
                ),
                success=self._lang.translate(TranslationKeys.EASEMENT_ATTACH_EXISTING_SUCCESS).format(item_id="{item_id}"),
                title_error=self._lang.translate(TranslationKeys.ERROR),
                title_warning=self._lang.translate(TranslationKeys.WARNING),
                title_success=self._lang.translate(TranslationKeys.SUCCESS),
            ),
            draw_messages=ModuleFeatureDrawMessages(
                start_failed=self._lang.translate(TranslationKeys.EASEMENT_DRAW_NEW_START_FAILED),
                save_failed_template=self._lang.translate(TranslationKeys.EASEMENT_DRAW_NEW_SAVE_FAILED).format(
                    item_id="{item_id}",
                    error="{error}",
                ),
                success=self._lang.translate(TranslationKeys.EASEMENT_DRAW_NEW_SUCCESS).format(item_id="{item_id}"),
                title_error=self._lang.translate(TranslationKeys.ERROR),
                title_success=self._lang.translate(TranslationKeys.SUCCESS),
            ),
            edit_messages=ModuleFeatureEditMessages(
                not_found=self._lang.translate(TranslationKeys.EASEMENT_EDIT_GEOMETRY_NOT_FOUND).format(item_id="{item_id}"),
                start_failed=self._lang.translate(TranslationKeys.EASEMENT_EDIT_GEOMETRY_START_FAILED),
                ready=self._lang.translate(TranslationKeys.EASEMENT_EDIT_GEOMETRY_READY).format(item_id="{item_id}"),
                title_error=self._lang.translate(TranslationKeys.ERROR),
                title_success=self._lang.translate(TranslationKeys.SUCCESS),
            ),
            before_attach=self._handle_attach_conflict,
            commit_edit_session_after_draw=True,
        )

    def _attach_easement_feature_with_form(self, layer, feature_id: int, current_item: Optional[dict]) -> tuple[bool, str]:
        item_payload = dict(current_item or {})
        item_id = str(item_payload.get("id") or "").strip()
        form_values = EasementGeometryFormDialog.prompt(item_data=item_payload)
        if form_values is None:
            return False, "Servituudi ala andmete sisestamine katkestati"

        item_payload["_easement_geometry_form"] = form_values
        item_payload["_easement_feature_id"] = int(feature_id)
        return self._attach_and_sync_easement_geometry(
            layer=layer,
            feature_id=feature_id,
            item_id=item_id,
            item_payload=item_payload,
        )

    @staticmethod
    def _attach_and_sync_easement_geometry(
        *,
        layer,
        feature_id: int,
        item_id: str,
        item_payload: dict,
    ) -> tuple[bool, str]:
        success, message = EasementLayerService.attach_backend_item_to_feature(
            layer=layer,
            feature_id=feature_id,
            item_id=item_id,
            item_data=item_payload,
        )
        if not success:
            return success, message

        geometry_payload = EasementAttachExistingController._geometry_payload_for_item(layer, item_payload)
        if geometry_payload is None:
            PythonFailLogger.log(
                "easement_geometry_backend_sync_skipped_no_geometry",
                module="easement",
                extra={"item_id": item_id, "feature_id": int(feature_id)},
            )
            return success, message

        if APIModuleActions.update_easement_geometry(item_id, geometry_payload):
            PythonFailLogger.log(
                "easement_geometry_backend_sync_success",
                module="easement",
                extra={"item_id": item_id, "feature_id": int(feature_id), "geometry_type": str(geometry_payload.get("type") or "")},
            )
            return success, message

        PythonFailLogger.log_exception(
            RuntimeError("Could not update easement geometry in backend"),
            module="easement",
            event="easement_geometry_backend_update_failed",
            extra={"item_id": item_id, "feature_id": int(feature_id)},
        )
        return False, "Servituudi geomeetria saatmine backendisse ebaõnnestus"

    @staticmethod
    def _geometry_payload_for_item(layer, item_payload: dict):
        try:
            feature = None
            feature_id = item_payload.get("_easement_feature_id")
            if feature_id is not None:
                feature = EasementLayerService._feature_by_id(layer, int(feature_id))
            if feature is None:
                feature = EasementLayerService.find_feature(
                    layer,
                    item_id=str((item_payload or {}).get("id") or "").strip(),
                    item_number=str((item_payload or {}).get("number") or "").strip(),
                )
            geometry = feature.geometry() if feature is not None else None
            return EasementLayerService.backend_geometry_payload_from_geometry(geometry)
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module="easement",
                event="easement_geometry_payload_from_item_failed",
                extra={"item_id": str((item_payload or {}).get("id") or "").strip()},
            )
            return None

    def _handle_attach_conflict(self, layer, feature, item_data: dict) -> bool:
        item_id = str((item_data or {}).get("id") or "").strip()
        existing_backend_id = EasementLayerService.linked_backend_id_for_feature(layer, feature)
        if not existing_backend_id or existing_backend_id == item_id:
            return True

        choice = ModernMessageDialog.ask_choice_modern(
            self._lang.translate(TranslationKeys.WARNING),
            self._lang.translate(TranslationKeys.EASEMENT_ATTACH_EXISTING_CONFLICT_MESSAGE).format(
                current_id=existing_backend_id,
                new_id=item_id,
            ),
            buttons=[
                self._lang.translate(TranslationKeys.EASEMENT_ATTACH_EXISTING_DELETE_OPTION),
                self._lang.translate(TranslationKeys.EASEMENT_ATTACH_EXISTING_ARCHIVE_OPTION),
                self._lang.translate(TranslationKeys.EASEMENT_ATTACH_EXISTING_CANCEL_OPTION),
            ],
            default=self._lang.translate(TranslationKeys.EASEMENT_ATTACH_EXISTING_CANCEL_OPTION),
            cancel=self._lang.translate(TranslationKeys.EASEMENT_ATTACH_EXISTING_CANCEL_OPTION),
        )

        if choice == self._lang.translate(TranslationKeys.EASEMENT_ATTACH_EXISTING_DELETE_OPTION):
            success, message = EasementLayerService.delete_feature_by_id(
                layer=layer,
                feature_id=int(feature.id()),
            )
            if success:
                ModernMessageDialog.show_info(
                    self._lang.translate(TranslationKeys.SUCCESS),
                    self._lang.translate(TranslationKeys.EASEMENT_ATTACH_EXISTING_DELETE_SUCCESS).format(item_id=existing_backend_id),
                )
            else:
                ModernMessageDialog.show_warning(
                    self._lang.translate(TranslationKeys.ERROR),
                    self._lang.translate(TranslationKeys.EASEMENT_ATTACH_EXISTING_DELETE_FAILED).format(
                        item_id=existing_backend_id,
                        error=message or self._lang.translate(TranslationKeys.ERROR),
                    ),
                )
            return False

        if choice == self._lang.translate(TranslationKeys.EASEMENT_ATTACH_EXISTING_ARCHIVE_OPTION):
            success, message = EasementLayerService.archive_feature_by_id(
                layer=layer,
                feature_id=int(feature.id()),
            )
            if success:
                ModernMessageDialog.show_info(
                    self._lang.translate(TranslationKeys.SUCCESS),
                    self._lang.translate(TranslationKeys.EASEMENT_ATTACH_EXISTING_ARCHIVE_SUCCESS).format(item_id=existing_backend_id),
                )
            else:
                ModernMessageDialog.show_warning(
                    self._lang.translate(TranslationKeys.ERROR),
                    self._lang.translate(TranslationKeys.EASEMENT_ATTACH_EXISTING_ARCHIVE_FAILED).format(
                        item_id=existing_backend_id,
                        error=message or self._lang.translate(TranslationKeys.ERROR),
                    ),
                )
            return False

        return False
