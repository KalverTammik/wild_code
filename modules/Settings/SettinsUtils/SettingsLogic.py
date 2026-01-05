
from typing import Dict, Iterable, Optional

from ....constants.module_icons import IconNames
from ....widgets.theme_manager import ThemeManager
from ....utils.messagesHelper import ModernMessageDialog

from ....utils.url_manager import Module, ModuleSupports
from ....module_manager import MODULES_LIST_BY_NAME
from ....constants.settings_keys import SettingsService



SUBJECT_TO_MODULE = {
    Module.PROJECT.value.capitalize(): Module.PROJECT.value.capitalize(),
    Module.CONTRACT.value.capitalize(): Module.CONTRACT.value.capitalize(),
    Module.PROPERTY.value.capitalize(): Module.PROPERTY.value.capitalize(),
    Module.COORDINATION.value.capitalize(): Module.COORDINATION.value.capitalize(),
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

    # --- Module-layer helpers -------------------------------------------------
    def get_module_layer_ids(self, module_key: str, *, include_archive: bool = False) -> Dict[str, str]:
        """Return the persisted layer identifiers for the given module."""
        element = self._service.module_main_layer_name(module_key) or ""
        archive = ""
        if include_archive:
            archive = self._service.module_archive_layer_name(module_key) or ""
        return {"element": element, "archive": archive}

    def set_module_layer_id(self, module_key: str, *, kind: str, layer_name: Optional[str]) -> None:
        """Persist (or clear) a module's layer mapping via a single entry point."""
        normalized = (layer_name or "").strip()
        try:
            if kind == "archive":
                if normalized:
                    self._service.module_archive_layer_name(module_key, value=normalized)
                else:
                    self._service.module_archive_layer_name(module_key, clear=True)
            else:
                if normalized:
                    self._service.module_main_layer_name(module_key, value=normalized)
                else:
                    self._service.module_main_layer_name(module_key, clear=True)
        except Exception:
            pass

    # --- Module preference helpers -------------------------------------------
    def load_module_preference_ids(self, module_key: str, *, support_key: str) -> Iterable[str]:
        """Fetch stored preference identifiers for the requested capability."""
        values = SettingsService.load_preferred_ids_by_key(support_key, module_key) or []
        return values

    def save_module_preference_ids(self, module_key: str, *, support_key: str, ids: Iterable[str]) -> None:
        """Persist tag/status/type selections for a module via the centralized service."""
        SettingsService.save_preferred_ids_by_key(support_key, module_key, ids)

    def clear_module_preference_ids(self, module_key: str, *, support_key: str) -> None:
        """Ensure preference storage is cleared for the given capability."""
        if support_key == ModuleSupports.TAGS.value:
            self._service.module_preferred_tags(module_key, clear=True)
        elif support_key == ModuleSupports.TYPES.value:
            self._service.module_preferred_types(module_key, clear=True)
        else:
            self._service.module_preferred_statuses(module_key, clear=True)

    # --- Module label helpers ----------------------------------------------

    def load_module_label_value(self, module_key: str, label_key) -> str:
        # Ensure label_key is a string
        key = getattr(label_key, 'value', label_key)
        value = self._service.module_label_value(module_key, key) or ""

        return value

    def save_module_label_value(self, module_key: str, label_key, value: str) -> None:
        try:
            key = getattr(label_key, 'value', label_key)
            if value is None:
                self._service.module_label_value(module_key, key, clear=True)
            else:
                self._service.module_label_value(module_key, key, value=value)
        except Exception:
            pass

    def clear_module_label_value(self, module_key: str, label_key) -> None:
        try:
            key = getattr(label_key, 'value', label_key)
            self._service.module_label_value(module_key, key, clear=True)
        except Exception:
            pass

    def confirm_navigation_away(self) -> bool:
        """Handle unsaved changes prompt when navigating away from Settings.
        
        Args:
            parent_dialog: Parent dialog for the prompt
            
        Returns:
            True if navigation may proceed, False to cancel
        """
        if not self.has_unsaved_changes():
            return True
            
        try:
            title = self.tr("Unsaved changes")
            text = self.tr("You have unsaved Settings changes.")
            detail = self.tr("Do you want to save your changes or discard them?")
            save_label = self.tr("Save")
            discard_label = self.tr("Discard")
            cancel_label = self.tr("Cancel")

            choice = ModernMessageDialog.ask_choice_modern(
                title,
                f"{text}\n\n{detail}",
                buttons=[save_label, discard_label, cancel_label],
                default=save_label,
                cancel=cancel_label,
                icon_name=IconNames.WARNING,
            )

            if choice == save_label:
                self.apply_pending_changes()
                return True
            if choice == discard_label:
                self.revert_pending_changes()
                return True
            return False
        except Exception as e:
            print(f"Settings navigation prompt failed: {e}", "error")
            return True

class SettingsHelpers:
    @staticmethod
    def _confirm_unsaved_settings(active_name) -> bool:
        """Check for unsaved changes in Settings and prompt the user.
        Returns True if navigation may proceed, False to cancel.
        """
        if active_name == Module.SETTINGS.name:
            return SettingsLogic.confirm_navigation_away()
        
        return True