from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Sequence

from ...constants.cadastral_fields import Katastriyksus
from ...Logs.python_fail_logger import PythonFailLogger
from ...modules.Property.FlowControllers.BackendPropertyActions import BackendPropertyActions
from ...utils.MapTools.MapSelectionOrchestrator import MapSelectionOrchestrator
from ...utils.MapTools.MapHelpers import FeatureActions
from ...utils.messagesHelper import ModernMessageDialog
from ...utils.url_manager import Module
from ...languages.translation_keys import TranslationKeys
from .property_prompt_helpers import PropertyPromptHelpers
from .property_row_builder import PropertyRowBuilder


@dataclass(frozen=True)
class PropertyActionResult:
    ok: bool
    title: str
    message: str
    action: str
    error: str | None = None


class PropertyActionService:
    @staticmethod
    def run_action(
        action: str,
        tunnused: Sequence[str],
        *,
        main_layer=None,
        module_name: str = Module.PROPERTY.name,
        archive_tag_name: str = "Arhiveeritud",
    ) -> PropertyActionResult:
        normalized_action = (action or "").strip().lower()
        if not normalized_action:
            return PropertyActionResult(
                ok=False,
                title="Unknown action",
                message="Action was not provided.",
                action=normalized_action,
            )

        if not tunnused:
            return PropertyActionResult(
                ok=False,
                title="Missing tunnus",
                message="Selected features do not contain cadastral tunnus.",
                action=normalized_action,
            )

        try:
            if normalized_action == "archive":
                BackendPropertyActions.archive_properties_by_tunnused(
                    list(tunnused),
                    archive_tag_name=archive_tag_name,
                    module_name=module_name,
                )
                return PropertyActionResult(
                    ok=True,
                    title="Backend action",
                    message=f"Archived in backend: {len(tunnused)}",
                    action=normalized_action,
                )

            if normalized_action == "unarchive":
                BackendPropertyActions.unarchive_properties_by_tunnused(list(tunnused))
                return PropertyActionResult(
                    ok=True,
                    title="Backend action",
                    message=f"Unarchived in backend: {len(tunnused)}",
                    action=normalized_action,
                )

            if normalized_action == "delete":
                BackendPropertyActions.delete_properties_by_tunnused(list(tunnused))
                if main_layer is None:
                    return PropertyActionResult(
                        ok=True,
                        title="Delete",
                        message=f"Backend delete attempted: {len(tunnused)}",
                        action=normalized_action,
                    )

                ok_commit, feature_ids, err = FeatureActions.delete_features_by_field_values(
                    main_layer,
                    Katastriyksus.tunnus,
                    list(tunnused),
                )

                lines = [
                    f"Backend delete attempted: {len(tunnused)}",
                    f"MAIN matched: {len(feature_ids or [])}",
                    f"MAIN deleted: {len(feature_ids or []) if ok_commit else 0}",
                ]
                if err:
                    lines.append(f"Error: {err}")

                title = "Delete" if ok_commit else "Delete (partial)"
                return PropertyActionResult(
                    ok=bool(ok_commit),
                    title=title,
                    message="\n".join(lines),
                    action=normalized_action,
                    error=err,
                )

            return PropertyActionResult(
                ok=False,
                title="Unknown action",
                message=f"Action '{action}' is not supported.",
                action=normalized_action,
            )
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module=Module.PROPERTY.value,
                event="property_action_failed",
            )
            return PropertyActionResult(
                ok=False,
                title="Backend action failed",
                message=str(exc),
                action=normalized_action,
                error=str(exc),
            )


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
