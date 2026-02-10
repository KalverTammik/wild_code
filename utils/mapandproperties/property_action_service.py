from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from ...constants.cadastral_fields import Katastriyksus
from ...Logs.python_fail_logger import PythonFailLogger
from ...modules.Property.FlowControllers.BackendPropertyActions import BackendPropertyActions
from ...utils.MapTools.MapHelpers import FeatureActions
from ...utils.url_manager import Module


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
