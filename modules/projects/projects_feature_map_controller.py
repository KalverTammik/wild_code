from __future__ import annotations

from typing import Optional

from ...languages.language_manager import LanguageManager
from ...languages.translation_keys import TranslationKeys
from ...utils.MapTools.module_feature_controllers import (
    ModuleFeatureAttachMessages,
    ModuleFeatureDrawMessages,
    ModuleFeatureEditMessages,
    ModuleFeatureWorkflow,
    ModuleFeatureWorkflowConfig,
)
from .projects_layer_service import ProjectsLayerService


class ProjectsFeatureMapController:
    def __init__(self, *, lang_manager=None) -> None:
        self._lang = lang_manager or LanguageManager()
        self._workflow = ModuleFeatureWorkflow(self._build_workflow_config())

    def start_draw(self, *, item_data: Optional[dict]) -> bool:
        item_payload = dict(item_data or {})
        item_id = str(item_payload.get("id") or "").strip()
        if not item_id:
            return False
        layer, _message = ProjectsLayerService.prepare_layer_for_draw(lang_manager=self._lang, silent=False)
        if layer is None:
            return False
        return self._workflow.start_draw(item_data=item_payload)

    def _build_workflow_config(self) -> ModuleFeatureWorkflowConfig:
        return ModuleFeatureWorkflowConfig(
            log_module="project",
            resolve_layer=lambda: ProjectsLayerService.resolve_main_layer(lang_manager=self._lang, silent=False),
            find_feature_at_point=lambda point, layer: ProjectsLayerService.find_feature_at_point(point, layer=layer),
            attach_handler=lambda layer, feature_id, current_item: ProjectsLayerService.attach_backend_item_to_feature(
                layer=layer,
                feature_id=feature_id,
                item_id=str((current_item or {}).get("id") or "").strip(),
                item_data=current_item,
            ),
            find_feature_for_item=lambda layer, current_item: ProjectsLayerService.find_feature(
                layer,
                item_id=str((current_item or {}).get("id") or "").strip(),
                item_number=str((current_item or {}).get("projectNumber") or (current_item or {}).get("number") or "").strip(),
                item_name=str((current_item or {}).get("name") or (current_item or {}).get("title") or "").strip(),
            ),
            attach_messages=ModuleFeatureAttachMessages(
                start_failed=self._lang.translate(TranslationKeys.PROJECT_DRAW_NEW_START_FAILED),
                feature_not_found="",
                save_failed_template=self._lang.translate(TranslationKeys.PROJECT_DRAW_NEW_SAVE_FAILED).format(
                    item_id="{item_id}",
                    error="{error}",
                ),
                success=self._lang.translate(TranslationKeys.PROJECT_DRAW_NEW_SUCCESS).format(item_id="{item_id}"),
                title_error=self._lang.translate(TranslationKeys.ERROR),
                title_warning=self._lang.translate(TranslationKeys.WARNING),
                title_success=self._lang.translate(TranslationKeys.SUCCESS),
            ),
            draw_messages=ModuleFeatureDrawMessages(
                start_failed=self._lang.translate(TranslationKeys.PROJECT_DRAW_NEW_START_FAILED),
                save_failed_template=self._lang.translate(TranslationKeys.PROJECT_DRAW_NEW_SAVE_FAILED).format(
                    item_id="{item_id}",
                    error="{error}",
                ),
                success=self._lang.translate(TranslationKeys.PROJECT_DRAW_NEW_SUCCESS).format(item_id="{item_id}"),
                title_error=self._lang.translate(TranslationKeys.ERROR),
                title_success=self._lang.translate(TranslationKeys.SUCCESS),
            ),
            edit_messages=ModuleFeatureEditMessages(
                not_found="",
                start_failed=self._lang.translate(TranslationKeys.PROJECT_DRAW_NEW_START_FAILED),
                ready=self._lang.translate(TranslationKeys.PROJECT_DRAW_NEW_SUCCESS).format(item_id="{item_id}"),
                title_error=self._lang.translate(TranslationKeys.ERROR),
                title_success=self._lang.translate(TranslationKeys.SUCCESS),
            ),
            commit_edit_session_after_draw=True,
        )