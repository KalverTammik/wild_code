from __future__ import annotations

from ...languages.language_manager import LanguageManager
from ...languages.translation_keys import TranslationKeys
from ...utils.messagesHelper import ModernMessageDialog
from ...utils.MapTools.module_feature_controllers import (
    ModuleFeatureAttachMessages,
    ModuleFeatureDrawMessages,
    ModuleFeatureEditMessages,
    ModuleFeatureWorkflow,
    ModuleFeatureWorkflowConfig,
)
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
            attach_handler=lambda layer, feature_id, current_item: EasementLayerService.attach_backend_item_to_feature(
                layer=layer,
                feature_id=feature_id,
                item_id=str((current_item or {}).get("id") or "").strip(),
                item_data=current_item,
            ),
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