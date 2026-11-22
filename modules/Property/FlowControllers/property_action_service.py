from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from ....constants.cadastral_fields import Katastriyksus
from ....Logs.python_fail_logger import PythonFailLogger
from ....utils.api_error_handling import user_message
from .backend_property_actions import BackendPropertyActions
from ....utils.MapTools.MapHelpers import FeatureActions
from ....constants.module_names import Module
from ....languages.translation_keys import TranslationKeys
from ....languages.language_manager import LanguageManager


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
        lang = LanguageManager()
        normalized_action = (action or "").strip().lower()
        if not normalized_action:
            return PropertyActionResult(
                ok=False,
                title=lang.translate(TranslationKeys.PROPERTY_ACTION_UNKNOWN_TITLE),
                message=lang.translate(TranslationKeys.PROPERTY_ACTION_MISSING_MESSAGE),
                action=normalized_action,
            )

        if not tunnused:
            return PropertyActionResult(
                ok=False,
                title=lang.translate(TranslationKeys.PROPERTY_ACTION_MISSING_TUNNUS_TITLE),
                message=lang.translate(TranslationKeys.PROPERTY_ACTION_MISSING_TUNNUS_MESSAGE),
                action=normalized_action,
            )

        try:
            if normalized_action == "archive":
                summary = BackendPropertyActions.archive_properties_by_tunnused(
                    list(tunnused),
                    archive_tag_name=archive_tag_name,
                    module_name=module_name,
                )
                succeeded = int(summary.get("succeeded") or 0)
                skipped = int(summary.get("skipped") or 0)
                failed = int(summary.get("failed") or 0)
                return PropertyActionResult(
                    ok=bool(succeeded > 0 and failed == 0),
                    title=lang.translate(
                        TranslationKeys.PROPERTY_ACTION_ARCHIVE_TITLE if failed == 0 else TranslationKeys.PROPERTY_ACTION_ARCHIVE_PARTIAL_TITLE
                    ),
                    message=(
                        lang.translate(TranslationKeys.PROPERTY_ACTION_ARCHIVE_SUMMARY).format(succeeded=succeeded, skipped=skipped, failed=failed)
                        + "\n" + lang.translate(TranslationKeys.PROPERTY_BACKEND_PENDING).format(tunnused=", ".join(summary.get("pending") or []))
                    ),
                    action=normalized_action,
                    error=(f"{failed} backend archive operations failed" if failed else None),
                )

            if normalized_action == "unarchive":
                summary = BackendPropertyActions.unarchive_properties_by_tunnused(list(tunnused))
                succeeded = int(summary.get("succeeded") or 0)
                skipped = int(summary.get("skipped") or 0)
                failed = int(summary.get("failed") or 0)
                return PropertyActionResult(
                    ok=bool(succeeded > 0 and failed == 0),
                    title=lang.translate(
                        TranslationKeys.PROPERTY_ACTION_UNARCHIVE_TITLE if failed == 0 else TranslationKeys.PROPERTY_ACTION_UNARCHIVE_PARTIAL_TITLE
                    ),
                    message=(
                        lang.translate(TranslationKeys.PROPERTY_ACTION_UNARCHIVE_SUMMARY).format(succeeded=succeeded, skipped=skipped, failed=failed)
                        + "\n" + lang.translate(TranslationKeys.PROPERTY_BACKEND_PENDING).format(tunnused=", ".join(summary.get("pending") or []))
                    ),
                    action=normalized_action,
                    error=(f"{failed} backend unarchive operations failed" if failed else None),
                )

            if normalized_action == "delete":
                BackendPropertyActions.delete_properties_by_tunnused(list(tunnused))
                if main_layer is None:
                    return PropertyActionResult(
                        ok=True,
                        title=lang.translate(TranslationKeys.PROPERTY_ACTION_DELETE_TITLE),
                        message=lang.translate(TranslationKeys.PROPERTY_ACTION_DELETE_ATTEMPTED).format(count=len(tunnused)),
                        action=normalized_action,
                    )

                ok_commit, feature_ids, err = FeatureActions.delete_features_by_field_values(
                    main_layer,
                    Katastriyksus.tunnus,
                    list(tunnused),
                )

                lines = [
                    lang.translate(TranslationKeys.PROPERTY_ACTION_DELETE_ATTEMPTED).format(count=len(tunnused)),
                    lang.translate(TranslationKeys.PROPERTY_ACTION_DELETE_MATCHED).format(count=len(feature_ids or [])),
                    lang.translate(TranslationKeys.PROPERTY_ACTION_DELETE_DELETED).format(count=len(feature_ids or []) if ok_commit else 0),
                ]
                if err:
                    lines.append(lang.translate(TranslationKeys.ERROR_DETAILS).format(error=err))

                title = lang.translate(
                    TranslationKeys.PROPERTY_ACTION_DELETE_TITLE if ok_commit else TranslationKeys.PROPERTY_ACTION_DELETE_PARTIAL_TITLE
                )
                return PropertyActionResult(
                    ok=bool(ok_commit),
                    title=title,
                    message="\n".join(lines),
                    action=normalized_action,
                    error=err,
                )

            return PropertyActionResult(
                ok=False,
                title=lang.translate(TranslationKeys.PROPERTY_ACTION_UNKNOWN_TITLE),
                message=lang.translate(TranslationKeys.PROPERTY_ACTION_UNSUPPORTED_MESSAGE).format(action=action),
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
                title=lang.translate(TranslationKeys.PROPERTY_ACTION_FAILED_TITLE),
                message=user_message(exc),
                action=normalized_action,
                error=str(exc),
            )

