
from .constants.module_icons import ModuleIconPaths
from .languages.language_manager import LanguageManager
from .constants.module_names import SETTINGS_MODULE,  PROJECTS_MODULE, CONTRACT_MODULE, PROPERTY_MODULE
from .utils.url_manager import Module




# Use class names as translation keys for all modules
MODULE_NAMES = {
    SETTINGS_MODULE: "SettingsModule",
    PROPERTY_MODULE: "PropertyModule",
    PROJECTS_MODULE: "ProjectsModule",
    CONTRACT_MODULE: "ContractsModule",
    Module.HOME: "HomeModule",
}


class ModuleManager:
    def __init__(self, lang_manager=None):
        self.modules = {}  # Dictionary to store modules by name
        self.activeModule = None  # Reference to the currently active module
        self.lang_manager = lang_manager or LanguageManager()

    def registerModule(self, module):
        print(f"[ModuleManager] Registering module: {module.name}")
        """Register a new module with its icon, human-readable name, and internal name."""
        self.modules[module.name] = {
            "module": module,
            "name": module.name,  # Store the internal name for reference
            "icon": ModuleIconPaths.get_module_icon(module.name),
            "display_name": self.get_module_name(module.name),  # Human-readable name (for language handling)
        }
    def getModuleIcon(self, moduleName):
        """Retrieve the icon for a registered module."""
        module_info = self.modules.get(moduleName, None)
        if module_info:
            return module_info.get("icon", None)
        return None


    def get_module_name(self, module_name):
        """Retrieve the human-readable name for a given module, using the injected language manager (must be LanguageManager_NEW)."""
        if not self.lang_manager or not hasattr(self.lang_manager, 'sidebar_button'):
            raise RuntimeError("lang_manager must be LanguageManager_NEW with sidebar_button method.")
        return self.lang_manager.sidebar_button(module_name)
    def activateModule(self, moduleName):
        # Debug print removed
        if moduleName in self.modules:
            # Debug print removed
            if self.activeModule:
                # Debug print removed
                self.activeModule["module"].deactivate()  # Deactivate the current module
            self.activeModule = self.modules[moduleName]
            # Debug print removed
            self.activeModule["module"].activate()  # Activate the new module
        else:
            # Debug print removed
            raise ValueError(f"Module '{moduleName}' not found.")

    def getActiveModule(self):
        """Return the currently active module."""
        return self.activeModule
