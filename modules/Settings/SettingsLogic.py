from typing import List, Dict, Optional, Set

from ...constants.module_names import PROJECTS_MODULE, CONTRACT_MODULE, PROPERTY_MODULE
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
        # Property layer tracking
        self._original_property_layer_id: Optional[str] = None
        self._pending_property_layer_id: Optional[str] = None

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
        api = APIClient(SessionManager(), ConfigPaths.CONFIG)
        query = ql.load_query("USER", "me.graphql")
        data = api.send_query(query)
        user_data = data.get("me", {}) or {}
        #print("=== USER ABILITIES FROM 'me' QUERY ===")
        #print(user_data)
        
        # Debug: Show abilities parsing
        abilities_raw = user_data.get("abilities", [])
        if abilities_raw:
            subjects = self.abilities_to_subjects(abilities_raw)
            #print(f"DEBUG: User has {len(subjects)} subjects: {sorted(subjects)}")
            if "Property" in subjects:
                print("✅ User has Property access!")
            else:
                print("❌ User does NOT have Property access")
        
        return user_data

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
                # Translate role names
                translated_name = self._translate_role_name(name)
                names.append(translated_name)
        return names

    def _translate_role_name(self, role_name: str) -> str:
        """Translate role names to Estonian."""
        role_translations = {
            "Admins": "Admin",
            "Administrators": "Administraatorid",
            "Project Managers": "Projektijuhid",
            "Users": "Kasutajad",
            "Managers": "Juhid",
            "Editors": "Toimetajad",
            "Viewers": "Vaatajad",
            "Guests": "Külalised"
        }
        return role_translations.get(role_name, role_name)

    def abilities_to_subjects(self, abilities_raw) -> Set[str]:
        import json
        abilities = abilities_raw or []
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

    def get_module_access_from_abilities(self, abilities_raw) -> Dict[str, bool]:
        subjects = self.abilities_to_subjects(abilities_raw)
        subject_to_module = {
            'Project': PROJECTS_MODULE,
            'Contract': CONTRACT_MODULE,
            'Property': PROPERTY_MODULE,
        }
        # Return access for all modules, including Property for UserCard preferred selection
        access: Dict[str, bool] = {}
        #print(f"DEBUG: Available modules: {self._available_modules}")
        #print(f"DEBUG: Subjects from abilities: {subjects}")
        for subj, mod in subject_to_module.items():
            # Include Property even if not in available modules (for UserCard preferred selection)
            if mod == PROPERTY_MODULE:
                access[mod] = subj in subjects
            elif self._available_modules and mod not in self._available_modules:
                continue
            else:
                access[mod] = subj in subjects
            #print(f"DEBUG: {mod} access: {access[mod]} (subject '{subj}' in subjects: {subj in subjects})")
        #print(f"DEBUG: Final access map: {access}")
        return access

    def get_module_update_permissions(self, abilities_raw) -> Dict[str, bool]:
        """Check if user has update permissions for specific modules"""
        import json
        abilities = abilities_raw or []
        if isinstance(abilities, str):
            try:
                abilities = json.loads(abilities)
            except Exception:
                abilities = []
        
        update_permissions = {}
        
        for ab in abilities:
            action = ab.get('action')
            subj = ab.get('subject')
            
            # Handle both string and array subjects
            if isinstance(subj, list) and subj:
                subject_name = str(subj[0])
            elif isinstance(subj, str):
                subject_name = subj
            else:
                continue
                
            # Check for update actions
            if action in ['update', 'manage'] and subject_name in ['Property', 'Project', 'Contract']:
                subject_to_module = {
                    'Project': PROJECTS_MODULE,
                    'Contract': CONTRACT_MODULE,
                    'Property': PROPERTY_MODULE,
                }
                module_name = subject_to_module.get(subject_name)
                if module_name:
                    update_permissions[module_name] = True
        
        return update_permissions

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

        # Load property layer
        try:
            layer_id = s.value("wild_code/main_property_layer_id", "") or None
        except Exception:
            layer_id = None
        self._original_property_layer_id = layer_id
        # Reset pending to original when loading
        self._pending_property_layer_id = layer_id

    def get_original_preferred(self) -> Optional[str]:
        return self._original_preferred

    def set_pending_preferred(self, module_name: Optional[str]):
        # None means user prefers Welcome page
        self._pending_preferred = module_name or None

    def get_pending_preferred(self) -> Optional[str]:
        return self._pending_preferred

    def has_unsaved_changes(self) -> bool:
        # Track change even if moving to None (welcome)
        preferred_changed = (self._pending_preferred or None) != (self._original_preferred or None)
        layer_changed = (self._pending_property_layer_id or None) != (self._original_property_layer_id or None)
        return preferred_changed or layer_changed

    def apply_pending_changes(self):
        try:
            from qgis.core import QgsSettings
            s = QgsSettings()
            if self._pending_preferred:
                s.setValue("wild_code/preferred_module", self._pending_preferred)
            else:
                # None -> remove setting to show Welcome
                s.remove("wild_code/preferred_module")
            self._original_preferred = self._pending_preferred

            # Apply property layer changes
            if self._pending_property_layer_id:
                s.setValue("wild_code/main_property_layer_id", self._pending_property_layer_id)
            else:
                # None -> remove setting
                s.remove("wild_code/main_property_layer_id")
            self._original_property_layer_id = self._pending_property_layer_id

        except Exception:
            # leave dirty state so user can retry
            pass

    def revert_pending_changes(self):
        # Reset pending selection back to the original
        self._pending_preferred = self._original_preferred
        self._pending_property_layer_id = self._original_property_layer_id

    # --- Property layer settings ---
    def get_original_property_layer_id(self) -> Optional[str]:
        return self._original_property_layer_id

    def get_pending_property_layer_id(self) -> Optional[str]:
        return self._pending_property_layer_id

    def set_pending_property_layer_id(self, layer_id: Optional[str]):
        # None means no layer selected
        self._pending_property_layer_id = layer_id or None
