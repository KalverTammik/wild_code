
from typing import Dict, Optional

from ....utils.url_manager import Module
from ....module_manager import MODULES_LIST_BY_NAME
from ....constants.settings_keys import SettingsService


SUBJECT_TO_MODULE = {
    Module.PROJECT.value.capitalize(): Module.PROJECT.value.capitalize(),
    Module.CONTRACT.value.capitalize(): Module.CONTRACT.value.capitalize(),
    Module.PROPERTY.value.capitalize(): Module.PROPERTY.value.capitalize(),
}

class SettingsLogic:
    def __init__(self):
        # Change tracking
        self._service = SettingsService()
        self._original_preferred: Optional[str] = None
        self._pending_preferred_module: Optional[str] = None
        


    def get_module_access_from_abilities(self, subjects) -> Dict[str, bool]:
        #print(f"[SettingsLogic.get_module_access_from_abilities] abilities_raw: {abilities_raw}")
        
        # Return access for all modules, including Property for UserCard preferred selection
        access: Dict[str, bool] = {}

        for subj, mod in SUBJECT_TO_MODULE.items():
            if mod == Module.PROPERTY.value.capitalize():
                access[mod] = subj in subjects
            elif MODULES_LIST_BY_NAME and mod not in MODULES_LIST_BY_NAME:
                continue
            else:
                access[mod] = subj in subjects
        #print(f"[SettingsLogic.get_module_access_from_abilities] computed access: {access}")
        return access

    @staticmethod
    def get_module_update_permissions(update_subjects) -> Dict[str, bool]:
        """Check if user has update permissions for specific modules"""
        update_permissions = {}
        
        for subj in update_subjects:
            subject_name = subj[0] if isinstance(subj, list) and subj else subj if isinstance(subj, str) else None
            if subject_name and subject_name in SUBJECT_TO_MODULE:
                update_permissions[SUBJECT_TO_MODULE[subject_name]] = True
        
        return update_permissions

    def load_original_settings(self):
        #Load preferred module
        pref = self._service.preferred_module() or None
        self._original_preferred = pref
        self._pending_preferred_module = pref

    def get_original_preferred(self) -> Optional[str]:
        return self._original_preferred

    def set_user_preferred_module(self, module_name: Optional[str]):
        # None means user prefers Welcome page
        self._pending_preferred_module = module_name or None


    def has_unsaved_changes(self) -> bool:
        # Track change even if moving to None (welcome)
        has_preferred_module_changes = (self._pending_preferred_module or None) != (self._original_preferred or None)
        return has_preferred_module_changes

    def apply_pending_changes(self):

        if self._pending_preferred_module:
            self._service.preferred_module(value=self._pending_preferred_module)
        else:
            self._service.preferred_module(clear=True)
        self._original_preferred = self._pending_preferred_module

        # Property layer persistence is handled via module cards

    def revert_pending_changes(self):
        # Reset pending selection back to the original
        self._pending_preferred_module = self._original_preferred
        # Property layer pending state managed by module cards

