
from qgis.core import QgsSettings
from typing import Dict, Optional
import json

from ...utils.url_manager import Module
from ...modules.Settings.cards.UserCard import userUtils
from ...module_manager import MODULES_LIST_BY_NAME


SUBJECT_TO_MODULE = {
    Module.PROJECT.value.capitalize(): Module.PROJECT.value.capitalize(),
    Module.CONTRACT.value.capitalize(): Module.CONTRACT.value.capitalize(),
    Module.PROPERTY.value.capitalize(): Module.PROPERTY.value.capitalize(),
}

class SettingsLogic:
    def __init__(self):
        # Change tracking
        self._original_preferred: Optional[str] = None
        self._pending_preferred: Optional[str] = None
        
        self._original_property_layer_id: Optional[str] = None
        self._pending_property_layer_id: Optional[str] = None
        self._has_property_rights: bool = False
        self._has_pending_status: bool = False
        self._pending_statuses: Dict[str, list] = {}
        self._pending_types: Dict[str, list] = {}



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
        try:
            pref = QgsSettings().value("wild_code/preferred_module", "") or None
        except Exception:
            pref = None
        self._original_preferred = pref
        # Reset pending to original when loading
        self._pending_preferred = pref
        layer_id = QgsSettings().value("wild_code/main_property_layer_id", "") or None
        layer_id = None
        self._original_property_layer_id = layer_id
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
        statuses_changed = bool(self._pending_statuses)
        types_changed = bool(self._pending_types)
        return preferred_changed or layer_changed or statuses_changed or types_changed

    def apply_pending_changes(self):
        try:
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

            self.apply_pending_statuses()
            self.apply_pending_types()  

        except Exception:
            # leave dirty state so user can retry
            pass

    def revert_pending_changes(self):
        # Reset pending selection back to the original
        self._pending_preferred = self._original_preferred
        self._pending_property_layer_id = self._original_property_layer_id
        self._pending_statuses.clear()
        self._pending_types.clear()

    # --- Property layer settings ---
    def get_original_property_layer_id(self) -> Optional[str]:
        return self._original_property_layer_id

    def get_pending_property_layer_id(self) -> Optional[str]:
        return self._pending_property_layer_id

    def set_pending_property_layer_id(self, layer_id: Optional[str]):
        # None means no layer selected
        self._pending_property_layer_id = layer_id

    def set_pending_statuses(self, module_name, status_ids):
        self._pending_statuses[module_name] = status_ids

    def get_pending_statuses(self, module_name):
        return self._pending_statuses.get(module_name, [])

    def apply_pending_statuses(self):
        for module, statuses in self._pending_statuses.items():
            key = f"wild_code/modules/{module}/preferred_statuses"
            from qgis.core import QgsSettings
            s = QgsSettings()
            s.setValue(key, ",".join(statuses))
        self._pending_statuses.clear()

    def revert_pending_statuses(self):
        self._pending_statuses.clear() or None

    def set_pending_types(self, module_name, type_ids):
        self._pending_types[module_name] = type_ids

    def get_pending_types(self, module_name):
        return self._pending_types.get(module_name, [])

    def apply_pending_types(self):
        for module, types in self._pending_types.items():
            key = f"wild_code/modules/{module}/preferred_types"
            from qgis.core import QgsSettings
            s = QgsSettings()
            s.setValue(key, ",".join(types))
        self._pending_types.clear()

    def revert_pending_types(self):
        self._pending_types.clear()