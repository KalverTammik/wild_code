from __future__ import annotations

from .MainAddProperties import BackendPropertyVerifier
from .UpdatePropertyData import UpdatePropertyData
from .MainDeleteProperties import deleteProperty
from ....utils.TagsEngines import TagsHelpers
from ....Logs.python_fail_logger import PythonFailLogger


class BackendPropertyActions:
    @staticmethod
    def archive_properties_by_tunnused(
        tunnused: list[str],
        *,
        archive_tag_name: str,
        module_name: str,
    ) -> dict:
        summary = {"total": len(tunnused or []), "succeeded": 0, "skipped": 0, "failed": 0}
        if not tunnused:
            return summary

        tag_id = TagsHelpers.check_if_tag_exists(tag_name=archive_tag_name, module=module_name)

        for tunnus in tunnused:
            backend_info = BackendPropertyVerifier.verify_properties_by_cadastral_number(tunnus)
            if not isinstance(backend_info, dict) or backend_info.get("exists") is None:
                summary["failed"] += 1
                continue

            if not backend_info.get("exists"):
                summary["skipped"] += 1
                continue

            active_count = backend_info.get("active_count")
            if isinstance(active_count, int) and active_count > 1:
                summary["failed"] += 1
                continue

            prop = backend_info.get("property") if isinstance(backend_info.get("property"), dict) else None
            prop_id = (prop.get("id") if isinstance(prop, dict) else None) if prop else None
            if not prop_id:
                summary["failed"] += 1
                continue

            ok = UpdatePropertyData._archive_a_propertie(item_id=str(prop_id), archive_tag=tag_id)
            if ok:
                summary["succeeded"] += 1
            else:
                summary["failed"] += 1
        return summary

    @staticmethod
    def unarchive_properties_by_tunnused(tunnused: list[str]) -> dict:
        summary = {"total": len(tunnused or []), "succeeded": 0, "skipped": 0, "failed": 0}
        if not tunnused:
            return summary

        for tunnus in tunnused:
            backend_info = BackendPropertyVerifier.verify_properties_by_cadastral_number(tunnus)
            if not isinstance(backend_info, dict) or backend_info.get("exists") is None:
                summary["failed"] += 1
                continue

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
                continue

            prop_id = archived_ids[0]
            ok = UpdatePropertyData._unarchive_property_data(item_id=prop_id)
            if ok:
                summary["succeeded"] += 1
            else:
                summary["failed"] += 1
        return summary

    @staticmethod
    def delete_properties_by_tunnused(tunnused: list[str]) -> None:
        if not tunnused:
            return

        for tunnus in tunnused:
            backend_info = BackendPropertyVerifier.verify_properties_by_cadastral_number(tunnus)
            if not isinstance(backend_info, dict) or backend_info.get("exists") is None:
                print({"delete_backend": {"tunnus": tunnus, "ok": False, "reason": "backend_lookup_failed", "backend_info": backend_info}})
                continue

            property_ids: list[str] = []

            if backend_info.get("exists"):
                active_count = backend_info.get("active_count")
                if isinstance(active_count, int) and active_count > 1:
                    print({"delete_backend": {"tunnus": tunnus, "ok": False, "reason": "multiple_active_backend_matches", "active_count": active_count}})
                    continue

                prop = backend_info.get("property") if isinstance(backend_info.get("property"), dict) else None
                prop_id = (prop.get("id") if isinstance(prop, dict) else None) if prop else None
                if not prop_id:
                    print({"delete_backend": {"tunnus": tunnus, "ok": False, "reason": "missing_property_id"}})
                    continue
                property_ids = [str(prop_id)]
            else:
                # Allow delete when there is exactly one archived match and no active.
                active_count = backend_info.get("active_count")
                try:
                    if int(active_count or 0) > 0:
                        print({"delete_backend": {"tunnus": tunnus, "ok": False, "reason": "active_backend_exists"}})
                        continue
                except Exception as exc:
                    PythonFailLogger.log_exception(
                        exc,
                        module="property",
                        event="backend_active_count_parse_failed",
                        extra={"tunnus": tunnus, "active_count": active_count},
                    )

                archived_ids = backend_info.get("archived_ids") or []
                if isinstance(archived_ids, list):
                    archived_ids = [str(i).strip() for i in archived_ids if i]
                else:
                    archived_ids = []

                if len(archived_ids) == 0:
                    print({"delete_backend": {"tunnus": tunnus, "ok": False, "reason": "no_backend_match"}})
                    continue
                if len(archived_ids) > 1:
                    print({"delete_backend": {"tunnus": tunnus, "ok": False, "reason": "multiple_archived_backend_matches", "archived_ids": archived_ids}})
                    continue
                property_ids = [archived_ids[0]]

            for prop_id in property_ids:
                ok, message = deleteProperty.delete_single_item(str(prop_id))
                print({"delete_backend": {"tunnus": tunnus, "property_id": str(prop_id), "ok": bool(ok), "message": message}})
