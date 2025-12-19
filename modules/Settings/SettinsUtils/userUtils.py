from ....constants.file_paths import ConfigPaths
from ....python.GraphQLQueryLoader import GraphQLQueryLoader
from ....utils.SessionManager import SessionManager
from ....python.api_client import APIClient
from ....utils.url_manager import Module


from PyQt5.QtWidgets import QLabel


from typing import Dict, List, Set, Union


class userUtils:
    @staticmethod
    def load_user(lbl_name: QLabel, lbl_email: QLabel, lbl_roles: QLabel, lang_manager) -> Dict:

        user_data = userUtils.fetch_user_payload()
        userUtils.extract_and_set_user_labels(lbl_name, lbl_email, user_data)

        roles = userUtils.get_roles_list(user_data.get("roles"))
        userUtils.set_roles(lbl_roles, roles)
        abilities = user_data.get("abilities", [])
        return abilities

    @staticmethod
    def fetch_user_payload() -> Dict:

        name = Module.USER.value
        query_file = "me.graphql"

        ql = GraphQLQueryLoader()
        api = APIClient(SessionManager(), ConfigPaths.CONFIG)
        query = ql.load_query_by_module(name, query_file)
        data = api.send_query(query)
        return data.get("me", {}) or {}

    @staticmethod
    def abilities_to_subjects(abilities) -> Set[str]:

        #print("DEBUG: Converting abilities to subjects...")
        #print(f"DEBUG: Raw abilities input: {abilities}")
        subjects = set()
        #print(f"DEBUG: Parsed abilities: {abilities}")
        for ab in abilities:
            subj = ab.get('subject')
            if isinstance(subj, list) and subj:
                subjects.add(str(subj[0]))
            elif isinstance(subj, str):
                subjects.add(subj)
        return subjects

    @staticmethod
    def extract_and_set_user_labels(lbl_name: QLabel, lbl_email: QLabel, user: dict):

        full_name = f"{user.get('firstName', '')} {user.get('lastName', '')}".strip() or "—"
        #print(f"[userUtils] Full name extracted: {full_name}")
        email = user.get("email", "—")

        lbl_name.setText(f"{full_name}")
        lbl_email.setText(f"{email}")

    @staticmethod
    def get_roles_list(roles_data) -> List[str]:
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
    def set_roles(lbl_roles: QLabel, roles: list):
        # IMPROVED: Display roles on separate line below label
        if roles:
            roles_text = ", ".join(roles)
            lbl_roles.setText(roles_text)
        else:
            lbl_roles.setText("—")

    @staticmethod
    def has_property_rights(user_payload) -> Union[bool, bool]:
        import json
        abilities = json.loads(user_payload["abilities"])

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