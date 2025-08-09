
from .constants.module_icons import ModuleIconPaths
from .languages.language_manager import LanguageManager
from .constants.module_names import SETTINGS_MODULE, GPT_ASSISTANT_MODULE, PROJECTS_MODULE, CONTRACT_MODULE




# Use class names as translation keys for all modules
MODULE_NAMES = {
    SETTINGS_MODULE: "SettingsModule",

    GPT_ASSISTANT_MODULE: "GptAssistant",
    PROJECTS_MODULE: "ProjectsModule",
    CONTRACT_MODULE: "ContractModule",
}


class ModuleManager:
    def __init__(self, lang_manager=None):
        self.modules = {}  # Dictionary to store modules by name
        self.activeModule = None  # Reference to the currently active module
        self.lang_manager = lang_manager or LanguageManager()

    def registerModule(self, module):
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
        """Activate a module by name."""
        if moduleName in self.modules:
            if self.activeModule:
                self.activeModule["module"].deactivate()  # Deactivate the current module
            self.activeModule = self.modules[moduleName]
            self.activeModule["module"].activate()  # Activate the new module
        else:
            raise ValueError(f"Module '{moduleName}' not found.")

    def getActiveModule(self):
        """Return the currently active module."""
        return self.activeModule
