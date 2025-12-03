from ....constants.file_paths import ConfigPaths
from ....python.GraphQLQueryLoader import GraphQLQueryLoader
from ....utils.SessionManager import SessionManager
from ....python.api_client import APIClient
from ....utils.url_manager import Module


from PyQt5.QtWidgets import QLabel


import json
from typing import Dict, List, Set


class userUtils:
    @staticmethod
    def load_user(lbl_name: QLabel, lbl_email: QLabel, lbl_roles: QLabel, lang_manager) -> Dict:

        user_data = userUtils.fetch_user_payload(lang_manager)
        userUtils.extract_and_set_user_labels(lbl_name, lbl_email, user_data)

        roles = userUtils.get_roles_list(user_data.get("roles"))
        userUtils.set_roles(lbl_roles, roles)
        abilities = user_data.get("abilities", [])
        return abilities

    @staticmethod
    def fetch_user_payload(lang_manager) -> Dict:

        name = Module.USER.value
        query_file = "me.graphql"

        ql = GraphQLQueryLoader()
        api = APIClient(SessionManager(), ConfigPaths.CONFIG)
        query = ql.load_query_by_module(name, query_file)
        data = api.send_query(query)
        return data.get("me", {}) or {}

    @staticmethod
    def abilities_to_subjects(abilities) -> Set[str]:

        import json
        abilities = abilities or []
        if isinstance(abilities, str):
            try:
                abilities = json.loads(abilities)
            except Exception:
                abilities = []
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