from typing import List, Dict, Optional, Set

from ...constants.module_names import PROJECTS_MODULE, CONTRACT_MODULE
from ...utils.GraphQLQueryLoader import GraphQLQueryLoader
from ...utils.api_client import APIClient
from ...constants.file_paths import ConfigPaths
from ...utils.SessionManager import SessionManager


class SettingsLogic:
    def __init__(self):
        # Which module cards to show
        self._available_modules: List[str] = []
        # Change tracking
        self._original_preferred: Optional[str] = None
        self._pending_preferred: Optional[str] = None

    # --- Available modules management ---
    def set_available_modules(self, module_names: List[str]):
        seen = set()
        ordered = []
        for n in module_names or []:
            if n not in seen:
                seen.add(n)
                ordered.append(n)
        self._available_modules = ordered

    def get_available_modules(self) -> List[str]:
        return list(self._available_modules)

    # --- Data loading ---
    def load_user(self, lang_manager) -> Dict:
        ql = GraphQLQueryLoader(lang_manager)
        api = APIClient(lang_manager, SessionManager(), ConfigPaths.CONFIG)
        query = ql.load_query("USER", "me.graphql")
        data = api.send_query(query)
        return data.get("me", {}) or {}

    # --- Parsing helpers ---
    def parse_roles(self, roles_raw) -> List[str]:
        import json
        roles = roles_raw or []
        if isinstance(roles, str):
            try:
                roles = json.loads(roles)
            except Exception:
                roles = []
        names: List[str] = []
        for r in roles:
            name = r.get('displayName') or r.get('name') or str(r.get('id') or '')
            if name:
                names.append(name)
        return names

    def abilities_to_subjects(self, abilities_raw) -> Set[str]:
        import json
        abilities = abilities_raw or []
        if isinstance(abilities, str):
            try:
                abilities = json.loads(abilities)
            except Exception:
                abilities = []
        subjects = set()
        for ab in abilities:
            subj = ab.get('subject')
            if isinstance(subj, list) and subj:
                subjects.add(str(subj[0]))
            elif isinstance(subj, str):
                subjects.add(subj)
        return subjects

    def get_module_access_from_abilities(self, abilities_raw) -> Dict[str, bool]:
        subjects = self.abilities_to_subjects(abilities_raw)
        subject_to_module = {
            'Project': PROJECTS_MODULE,
            'Contract': CONTRACT_MODULE,
        }
        # Only return access for modules that are available (in sidebar)
        access: Dict[str, bool] = {}
        for subj, mod in subject_to_module.items():
            if self._available_modules and mod not in self._available_modules:
                continue
            access[mod] = subj in subjects
        return access

    # --- Preferred module settings ---
    def load_original_settings(self):
        try:
            from qgis.core import QgsSettings
            s = QgsSettings()
            pref = s.value("wild_code/preferred_module", "") or None
        except Exception:
            pref = None
        self._original_preferred = pref
        # Reset pending to original when loading
        self._pending_preferred = pref

    def get_original_preferred(self) -> Optional[str]:
        return self._original_preferred

    def set_pending_preferred(self, module_name: Optional[str]):
        self._pending_preferred = module_name or None

    def get_pending_preferred(self) -> Optional[str]:
        return self._pending_preferred

    def has_unsaved_changes(self) -> bool:
        return (self._pending_preferred or None) != (self._original_preferred or None)

    def apply_pending_changes(self):
        try:
            from qgis.core import QgsSettings
            s = QgsSettings()
            if self._pending_preferred:
                s.setValue("wild_code/preferred_module", self._pending_preferred)
            else:
                s.remove("wild_code/preferred_module")
            self._original_preferred = self._pending_preferred
        except Exception:
            # leave dirty state so user can retry
            pass

    def revert_pending_changes(self):
        # Reset pending selection back to the original
        self._pending_preferred = self._original_preferred
