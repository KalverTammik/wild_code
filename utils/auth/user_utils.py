from ..url_manager import Module

from typing import Any, Dict, List, Set, Tuple


class UserUtils:
    @staticmethod
    def fetch_user_payload(query_loader, api_client, *, query_file: str = "me.graphql") -> Dict[str, Any]:
        name = Module.USER.value
        query = query_loader.load_query_by_module(name, query_file)
        data = api_client.send_query(query)
        return data.get("me", {}) or {}

    @staticmethod
    def abilities_to_subjects(abilities: List[Dict[str, Any]]) -> Set[str]:
        subjects = set()
        for ab in abilities:
            subj = ab.get('subject')
            if isinstance(subj, list) and subj:
                subjects.add(str(subj[0]))
            elif isinstance(subj, str):
                subjects.add(subj)
        return subjects

    @staticmethod
    def parse_abilities(abilities_raw: Any) -> List[Dict[str, Any]]:
        import json
        from ...Logs.python_fail_logger import PythonFailLogger

        if not isinstance(abilities_raw, str):
            return []

        try:
            parsed = json.loads(abilities_raw)
            if isinstance(parsed, (list, tuple)):
                return list(parsed)
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module=Module.USER.value,
                event="settings_parse_abilities_failed",
            )
        return []

    @staticmethod
    def get_roles_list(roles_data: Any) -> List[str]:
        roles = roles_data or []
        if isinstance(roles, str):
            roles = []
        names: List[str] = []
        for r in roles:
            name = r.get('displayName') or r.get('name') or str(r.get('id') or '')
            if name:
                names.append(name)
        return names

    @staticmethod
    def extract_user_header(user_data: Dict[str, Any], dash: str) -> Dict[str, str]:
        full_name = f"{user_data.get('firstName', '')} {user_data.get('lastName', '')}".strip() or dash
        email = user_data.get("email", dash)
        return {
            "full_name": full_name,
            "email": email,
        }

    @staticmethod
    def has_property_rights(user_payload: Dict[str, Any]) -> Tuple[bool, bool]:
        abilities_raw = user_payload.get("abilities") if isinstance(user_payload, dict) else None
        abilities = UserUtils.parse_abilities(abilities_raw)

        has_qgis_access = any(
            a.get("action") == "access" and a.get("subject") == "QGIS"
            for a in abilities
        )

        can_create_property = any(
            a.get("action") == "create" and (
                a.get("subject") == "Property"
                or (isinstance(a.get("subject"), list) and "Property" in a["subject"])
            )
            for a in abilities
        )
        return has_qgis_access, can_create_property
