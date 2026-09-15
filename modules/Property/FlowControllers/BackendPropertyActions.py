from __future__ import annotations

from .MainAddProperties import BackendPropertyVerifier
from .UpdatePropertyData import UpdatePropertyData
from .MainDeleteProperties import deleteProperty
from ....utils.TagsEngines import TagsHelpers
from ....languages.language_manager import LanguageManager
from ....languages.translation_keys import TranslationKeys


class BackendPropertyActions:
    @staticmethod
    def archive_properties_by_tunnused(
        tunnused: list[str],
        *,
        archive_tag_name: str,
        module_name: str,
    ) -> dict:
        summary = {"total": len(tunnused or []), "succeeded": 0, "skipped": 0, "failed": 0, "pending": []}
        if not tunnused:
            return summary

        tag_id = TagsHelpers.check_if_tag_exists(tag_name=archive_tag_name, module=module_name)

        for index, tunnus in enumerate(tunnused):
            summary["pending"] = list(tunnused[index + 1:])
            backend_info = BackendPropertyVerifier.verify_properties_by_cadastral_number(tunnus)
            if not isinstance(backend_info, dict) or backend_info.get("exists") is None:
                summary["failed"] += 1
                break

            if not backend_info.get("exists"):
                summary["skipped"] += 1
                continue

            active_count = backend_info.get("active_count")
            if isinstance(active_count, int) and active_count > 1:
                summary["failed"] += 1
                break

            prop = backend_info.get("property") if isinstance(backend_info.get("property"), dict) else None
            prop_id = (prop.get("id") if isinstance(prop, dict) else None) if prop else None
            if not prop_id:
                summary["failed"] += 1
                break

            ok = UpdatePropertyData._archive_a_propertie(item_id=str(prop_id), archive_tag=tag_id)
            if ok:
                summary["succeeded"] += 1
            else:
                summary["failed"] += 1
                break
        return summary

    @staticmethod
    def unarchive_properties_by_tunnused(tunnused: list[str]) -> dict:
        summary = {"total": len(tunnused or []), "succeeded": 0, "skipped": 0, "failed": 0, "pending": []}
        if not tunnused:
            return summary

        for index, tunnus in enumerate(tunnused):
            summary["pending"] = list(tunnused[index + 1:])
            backend_info = BackendPropertyVerifier.verify_properties_by_cadastral_number(tunnus)
            if not isinstance(backend_info, dict) or backend_info.get("exists") is None:
                summary["failed"] += 1
                break

            archived_ids = backend_info.get("archived_ids") or []
            if isinstance(archived_ids, list):
                archived_ids = [str(i).strip() for i in archived_ids if i]
            else:
                archived_ids = []

            if len(archived_ids) == 0:
                summary["skipped"] += 1
                continue
            if len(archived_ids) > 1:
                summary["failed"] += 1
                break

            prop_id = archived_ids[0]
            ok = UpdatePropertyData._unarchive_property_data(item_id=prop_id)
            if ok:
                summary["succeeded"] += 1
            else:
                summary["failed"] += 1
                break
        return summary

    @staticmethod
    def delete_properties_by_tunnused(tunnused: list[str]) -> None:
        # A failed/uncertain delete must stop before callers touch the main layer.
        for index, tunnus in enumerate(tunnused or []):
            try:
                info = BackendPropertyVerifier.verify_properties_by_cadastral_number(tunnus)
                if not isinstance(info, dict) or info.get("exists") is None:
                    raise RuntimeError(LanguageManager().translate(TranslationKeys.PROPERTY_ADD_LOOKUP_FAILED))
                if info.get("exists"):
                    if int(info.get("active_count") or 0) > 1:
                        raise RuntimeError(LanguageManager().translate(TranslationKeys.PROPERTY_ADD_AMBIGUOUS))
                    property_id = (info.get("property") or {}).get("id")
                    if not property_id:
                        raise RuntimeError(LanguageManager().translate(TranslationKeys.PROPERTY_ADD_LOOKUP_FAILED))
                else:
                    ids = info.get("archived_ids") or []
                    if int(info.get("active_count") or 0) > 0 or len(ids) > 1:
                        raise RuntimeError(LanguageManager().translate(TranslationKeys.PROPERTY_ADD_AMBIGUOUS))
                    if not ids:
                        continue  # Confirmed absent; no backend deletion is needed.
                    property_id = ids[0]
                ok, message = deleteProperty.delete_single_item(str(property_id))
                if not ok:
                    raise RuntimeError(message or LanguageManager().translate(TranslationKeys.PROPERTY_ADD_WRITE_FAILED))
            except Exception as exc:
                raise RuntimeError(LanguageManager().translate(TranslationKeys.PROPERTY_DELETE_STOPPED).format(
                    tunnus=tunnus, pending=", ".join(tunnused[index + 1:]), error=str(exc))) from exc
