from typing import Callable

from ....languages.translation_keys import TranslationKeys
from ....constants.module_names import Module

from ....ui.messages_helper import ModernMessageDialog
from ....utils.MapTools.MapSelectionOrchestrator import MapSelectionOrchestrator
from ....utils.property.property_row_builder import PropertyRowBuilder
from .property_prompt_helpers import PropertyPromptHelpers
from .property_action_service import PropertyActionService


class PropertySelectionActionService:
    @staticmethod
    def start_settings_remove_flow(
        *,
        parent,
        main_layer,
        translate: Callable[[str], str],
        prompt_title: str,
        on_restore_ui: Callable[[], None],
        on_minimize_ui: Callable[[], None],
        on_flow_finished: Callable[[], None],
    ):
        ModernMessageDialog.Info_messages_modern(
            translate(TranslationKeys.SELECT_PROPERTIES),
            translate(TranslationKeys.SELECT_PROPERTIES_MAP_INSTRUCTION),
        )

        def _on_selected(_layer, features):
            try:
                on_restore_ui()

                feats = list(features or [])
                if not feats:
                    ModernMessageDialog.Info_messages_modern(
                        translate(TranslationKeys.NO_SELECTION),
                        translate(TranslationKeys.MAP_SELECTION_NONE),
                    )
                    return

                rows = PropertyRowBuilder.rows_from_features(feats, log_prefix="PropertyManagementUI")
                tunnused = PropertyRowBuilder.extract_tunnused(rows, key="cadastral_id")

                action = PropertyPromptHelpers.prompt_backend_action(
                    parent,
                    rows,
                    title=prompt_title,
                )
                if not action:
                    return

                tunnused_u = PropertyRowBuilder.dedupe_values(tunnused)

                if not tunnused_u:
                    ModernMessageDialog.Warning_messages_modern(
                        translate(TranslationKeys.MISSING_TUNNUS_TITLE),
                        translate(TranslationKeys.MISSING_TUNNUS_MESSAGE),
                    )
                    return

                result = PropertyActionService.run_action(
                    action,
                    tunnused_u,
                    main_layer=main_layer,
                    module_name=Module.PROPERTY.name,
                )

                if result.ok:
                    ModernMessageDialog.Info_messages_modern(result.title, result.message)
                else:
                    ModernMessageDialog.Warning_messages_modern(result.title, result.message)
            finally:
                on_flow_finished()

        orchestrator = MapSelectionOrchestrator(parent=parent)
        started = orchestrator.start_selection_for_layer(
            main_layer,
            on_selected=_on_selected,
            selection_tool="rectangle",
            restore_pan=True,
            min_selected=1,
            max_selected=None,
            clear_filter=False,
        )

        if not started:
            on_flow_finished()
            ModernMessageDialog.Warning_messages_modern(
                translate(TranslationKeys.SELECTION_FAILED_TITLE),
                translate(TranslationKeys.MAP_SELECTION_START_FAILED),
            )
            return None

        on_minimize_ui()
        return orchestrator
